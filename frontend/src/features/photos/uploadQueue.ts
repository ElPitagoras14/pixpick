import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useCallback, useState } from "react";

import { albumQueryOptions, albumsQueryOptions } from "@/features/albums/api";
import { galleryQueryKeyPrefix } from "@/features/gallery/api";
import {
	type ConfirmationStatus,
	confirmPhotoBatch,
	type GrantFileInput,
	grantPhotoBatch,
	type PhotoDenial,
	type PhotoGrant,
	photosQueryOptions,
} from "@/features/photos/api";
import {
	accountUsageQueryOptions,
	albumUsageQueryOptions,
	formatBytes,
} from "@/features/quota/api";

// Mirrors the server's own constants (photo-upload spec): fixed, not
// configurable, because they're the product's own contract and not
// something that should vary between environments. Validating here lets
// an inadmissible file be reported immediately, with no request spent
// (D3, task 7.1) -- the server validates the same two things again at
// the border, and that duplication is deliberate (D3 in this change's
// design), not a redundancy to remove.
const ALLOWED_CONTENT_TYPES = new Set([
	"image/jpeg",
	"image/png",
	"image/webp",
]);
const MAX_FILE_SIZE = 20 * 1024 * 1024;

// The batch ceiling (D13): a selection larger than this is the client's
// own job to split into successive batches, sent in order and never in
// parallel, so the positions they claim land in the order they were
// picked.
const BATCH_SIZE = 50;

// How many uploads this client keeps in flight at once (D5) -- bounded
// so a large selection doesn't open dozens of simultaneous connections.
const MAX_CONCURRENT_UPLOADS = 3;

export type UploadItemStatus =
	| "queued"
	| "uploading"
	| "confirming"
	| ConfirmationStatus
	// Asked for and not granted (D4): a state of its own, not a failure.
	// Nothing went wrong -- there was no room -- so it reads differently
	// and, unlike a failure, the way out is to free space, not to retry
	// the same thing hoping for a different answer.
	| "denied"
	// The instance couldn't take this request right now -- nginx's own
	// rate limit, or the backend's connection pool (request-throttling
	// spec, task 4.8) -- a state of its own, not a failure: nothing about
	// this file was wrong, and the way out is to wait and retry the same
	// thing, unlike "failed" below.
	| "busy"
	| "failed";

export interface UploadItem {
	id: string;
	file: File;
	status: UploadItemStatus;
	progress: number;
	error?: string;
	photoId?: string;
}

function validateFile(file: File): string | null {
	if (!ALLOWED_CONTENT_TYPES.has(file.type)) {
		return "This file type isn't supported.";
	}
	if (file.size > MAX_FILE_SIZE) {
		return "This file is too large.";
	}
	return null;
}

/** Why one file didn't get a grant, in the words the person can act on
 * (D4, modified by add-instance-quota): the three limits are never
 * collapsed into one message, because an album that's full is fixed by
 * creating another album, an account without space by deleting
 * something -- and an instance without space isn't fixed by whoever is
 * asking at all, so this SHALL NOT tell them to delete their own photos
 * (upload-feedback spec). */
function denialMessage(denial: PhotoDenial): string {
	if (denial.reason === "album_full") {
		return "Album full";
	}
	if (denial.reason === "instance_full") {
		return "The instance is full — this isn't your space to free. Try again once someone else deletes photos.";
	}
	return `No space (${formatBytes(denial.remainingBytes ?? 0)} left)`;
}

function errorMessage(error: unknown): string {
	if (axios.isAxiosError(error)) {
		const message = error.response?.data?.error?.message;
		if (typeof message === "string") return message;
	}
	return "Something went wrong.";
}

/** How long to wait before retrying, only ever set on a rejection caused
 * by a lack of capacity (api-conventions spec, task 4.8) -- `null` for
 * every other kind of error, including one with no response at all. */
function capacityRetryAfter(error: unknown): number | null {
	if (!axios.isAxiosError(error)) return null;
	const seconds = error.response?.data?.error?.retryAfterSeconds;
	return typeof seconds === "number" ? seconds : null;
}

function busyMessage(retryAfterSeconds: number): string {
	return `Server is busy — retry in ${retryAfterSeconds}s`;
}

async function readImageDimensions(
	file: File,
): Promise<{ width?: number; height?: number }> {
	// A presentation hint only (photo-upload spec): if this can't be read
	// for any reason, the upload proceeds without it rather than fail.
	try {
		const bitmap = await createImageBitmap(file);
		const dimensions = { width: bitmap.width, height: bitmap.height };
		bitmap.close();
		return dimensions;
	} catch {
		return {};
	}
}

function toGrantInput(
	file: File,
	dimensions: { width?: number; height?: number },
): GrantFileInput {
	return {
		contentType: file.type,
		size: file.size,
		width: dimensions.width,
		height: dimensions.height,
	};
}

async function uploadToStorage(
	grant: PhotoGrant,
	file: File,
	onProgress: (percent: number) => void,
): Promise<void> {
	// Not this app's own `api` client: this goes straight to the storage
	// provider's own origin, with none of the API's credentials or base
	// URL (object-storage spec -- the API never sees these bytes). A PUT
	// with the file itself as the body (D9 in add-cloud-media-adapters):
	// `uploadHeaders` has to travel exactly as given, since it's signed
	// into `uploadUrl` -- a missing or altered header invalidates it.
	await axios.put(grant.uploadUrl, file, {
		headers: grant.uploadHeaders,
		onUploadProgress: (event) => {
			if (event.total) {
				onProgress(Math.round((event.loaded / event.total) * 100));
			}
		},
	});
}

async function runWithConcurrency(
	tasks: Array<() => Promise<void>>,
	limit: number,
): Promise<void> {
	const queue = [...tasks];
	async function worker(): Promise<void> {
		for (let task = queue.shift(); task; task = queue.shift()) {
			await task();
		}
	}
	await Promise.all(
		Array.from({ length: Math.min(limit, tasks.length) }, worker),
	);
}

type UpdateItem = (id: string, patch: Partial<UploadItem>) => void;

async function processBatch(
	albumId: string,
	items: UploadItem[],
	update: UpdateItem,
): Promise<void> {
	items.forEach((item) => {
		update(item.id, { status: "uploading", progress: 0, error: undefined });
	});

	const dimensions = await Promise.all(
		items.map((item) => readImageDimensions(item.file)),
	);

	let granted: PhotoGrant[];
	let denied: PhotoDenial[];
	try {
		const result = await grantPhotoBatch(
			albumId,
			items.map((item, index) => toGrantInput(item.file, dimensions[index])),
		);
		granted = result.granted;
		denied = result.denied;
	} catch (error) {
		const retryAfterSeconds = capacityRetryAfter(error);
		items.forEach((item) => {
			update(
				item.id,
				retryAfterSeconds != null
					? { status: "busy", error: busyMessage(retryAfterSeconds) }
					: { status: "failed", error: errorMessage(error) },
			);
		});
		return;
	}

	// Every file of the batch is in exactly one of the two lists, and each
	// entry names which file it is by its index in the request (D4) -- the
	// request carries no filename, so there is nothing else to match on,
	// and matching by order stopped working the moment fewer grants than
	// files could come back.
	denied.forEach((denial) => {
		update(items[denial.index].id, {
			status: "denied",
			progress: 0,
			error: denialMessage(denial),
		});
	});

	const uploaded: Array<{ item: UploadItem; grant: PhotoGrant }> = [];
	await runWithConcurrency(
		granted.map((grant) => async () => {
			const item = items[grant.index];
			update(item.id, { photoId: grant.photoId });
			try {
				await uploadToStorage(grant, item.file, (progress) =>
					update(item.id, { progress }),
				);
				update(item.id, { progress: 100 });
				uploaded.push({ item, grant });
			} catch (error) {
				const retryAfterSeconds = capacityRetryAfter(error);
				update(
					item.id,
					retryAfterSeconds != null
						? { status: "busy", error: busyMessage(retryAfterSeconds) }
						: { status: "failed", error: errorMessage(error) },
				);
			}
		}),
		MAX_CONCURRENT_UPLOADS,
	);

	// Confirmed only for the ones that actually made it (task 7.4): an
	// interrupted upload stays exactly where confirming would leave it
	// pending, never mistaken for confirmed.
	if (uploaded.length === 0) return;

	uploaded.forEach(({ item }) => {
		update(item.id, { status: "confirming" });
	});
	try {
		const results = await confirmPhotoBatch(
			albumId,
			uploaded.map(({ grant }) => grant.photoId),
		);
		const statusByPhotoId = new Map(
			results.map((result) => [result.photoId, result.status]),
		);
		uploaded.forEach(({ item, grant }) => {
			update(item.id, {
				status: statusByPhotoId.get(grant.photoId) ?? "pending",
			});
		});
	} catch (error) {
		const retryAfterSeconds = capacityRetryAfter(error);
		uploaded.forEach(({ item }) => {
			update(
				item.id,
				retryAfterSeconds != null
					? { status: "busy", error: busyMessage(retryAfterSeconds) }
					: { status: "failed", error: errorMessage(error) },
			);
		});
	}
}

/** Client-side state for the whole upload flow (D5): every file has its
 * own status and progress, a bounded number upload at once, and a retry
 * only ever repeats the one file that failed (task 7.2) -- each file's
 * own pipeline (grant, upload, confirm) is independent of every other's.
 */
export function useUploadQueue(albumId: string) {
	const [items, setItems] = useState<UploadItem[]>([]);
	const queryClient = useQueryClient();

	const update = useCallback<UpdateItem>((id, patch) => {
		setItems((prev) =>
			prev.map((item) => (item.id === id ? { ...item, ...patch } : item)),
		);
	}, []);

	const runItems = useCallback(
		async (toRun: UploadItem[]) => {
			// A selection bigger than the ceiling is split into successive
			// batches, sent in order and never in parallel (D13): concurrent
			// batches would still assign non-overlapping positions, but
			// could interleave them, losing the order the photos were
			// picked in.
			for (let start = 0; start < toRun.length; start += BATCH_SIZE) {
				await processBatch(
					albumId,
					toRun.slice(start, start + BATCH_SIZE),
					update,
				);
				queryClient.invalidateQueries({
					queryKey: photosQueryOptions(albumId).queryKey,
				});
				// The grid the uploader actually watches is the gallery now
				// (rating-gallery spec): every one of its filters, since a
				// newly available photo always belongs to "all" and "unrated".
				queryClient.invalidateQueries({
					queryKey: galleryQueryKeyPrefix(albumId),
				});
				queryClient.invalidateQueries({
					queryKey: albumsQueryOptions().queryKey,
				});
				// A photo becoming available restarts the album's plazo
				// (album-retention spec, task 5.3): the detail query is what
				// the header's remaining-time label reads, so it's stale the
				// moment a batch confirms.
				queryClient.invalidateQueries({
					queryKey: albumQueryOptions(albumId).queryKey,
				});
				// What was just uploaded is what the space meters now have to
				// account for -- the account's own, and this album's.
				queryClient.invalidateQueries({
					queryKey: accountUsageQueryOptions().queryKey,
				});
				queryClient.invalidateQueries({
					queryKey: albumUsageQueryOptions(albumId).queryKey,
				});
			}
		},
		[albumId, update, queryClient],
	);

	const addFiles = useCallback(
		(files: File[]) => {
			const newItems: UploadItem[] = files.map((file) => {
				const error = validateFile(file);
				return {
					id: crypto.randomUUID(),
					file,
					status: error ? "failed" : "queued",
					progress: 0,
					error: error ?? undefined,
				};
			});
			setItems((prev) => [...prev, ...newItems]);
			const runnable = newItems.filter((item) => item.status === "queued");
			if (runnable.length > 0) {
				void runItems(runnable);
			}
		},
		[runItems],
	);

	const retry = useCallback(
		(itemId: string) => {
			const item = items.find((candidate) => candidate.id === itemId);
			if (!item) return;
			update(itemId, { status: "queued", error: undefined, progress: 0 });
			void runItems([
				{ ...item, status: "queued", error: undefined, progress: 0 },
			]);
		},
		[items, runItems, update],
	);

	return { items, addFiles, retry };
}
