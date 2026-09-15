import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";

import { type ApiEnvelope, api, unwrapApiError } from "@/api";
import { albumsQueryOptions } from "@/features/albums/api";
import {
	albumStatsQueryOptions,
	galleryQueryKeyPrefix,
} from "@/features/gallery/api";
import {
	accountUsageQueryOptions,
	albumUsageQueryOptions,
} from "@/features/quota/api";

export interface Photo {
	id: string;
	position: number;
	width: number | null;
	height: number | null;
	thumbnailUrl: string;
}

export interface PhotoGrant {
	// The position the file had in the request (D4): with a batch that
	// can be granted only in part, the response is no longer as long as
	// the request, so order alone no longer says which file this is for.
	index: number;
	photoId: string;
	position: number;
	uploadUrl: string;
	uploadHeaders: Record<string, string>;
}

// Which of the two capacity limits stopped a file (photo-upload spec).
// They are not resolved the same way: an album that's full is resolved
// by creating another album, an account without space by deleting
// something -- so they are never collapsed into one message.
export type DenialReason = "album_full" | "account_full";

export interface PhotoDenial {
	index: number;
	reason: DenialReason;
	remainingPhotos: number | null;
	remainingBytes: number | null;
}

export interface GrantBatchResult {
	granted: PhotoGrant[];
	denied: PhotoDenial[];
}

export type ConfirmationStatus = "available" | "rejected" | "pending";

export interface ConfirmationResult {
	photoId: string;
	status: ConfirmationStatus;
}

export interface GrantFileInput {
	contentType: string;
	size: number;
	width?: number;
	height?: number;
}

async function fetchPhotos(albumId: string): Promise<Photo[]> {
	const response = await api.get<ApiEnvelope<Photo[]>>(
		`/albums/${albumId}/photos`,
	);
	return response.data.data ?? [];
}

// The one place this query is defined (D9): the grid and the upload
// view both invalidate it once their own work changes what it returns,
// instead of each keeping its own copy.
export function photosQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId, "photos"] as const,
		queryFn: () => fetchPhotos(albumId),
	});
}

// Not a `useMutation` hook like the rest of this feature's writes: the
// upload queue (`uploadQueue.ts`) drives many of these itself, batched
// and in a specific order (D13), so it calls this function directly
// instead of going through a component's own mutation lifecycle.
export async function grantPhotoBatch(
	albumId: string,
	files: GrantFileInput[],
): Promise<GrantBatchResult> {
	try {
		const response = await api.post<ApiEnvelope<GrantBatchResult>>(
			`/albums/${albumId}/photos/grants`,
			{ files },
		);
		return response.data.data ?? { granted: [], denied: [] };
	} catch (error) {
		unwrapApiError(error);
	}
}

export async function confirmPhotoBatch(
	albumId: string,
	photoIds: string[],
): Promise<ConfirmationResult[]> {
	try {
		const response = await api.post<ApiEnvelope<ConfirmationResult[]>>(
			`/albums/${albumId}/photos/confirm`,
			{ photoIds },
		);
		return response.data.data ?? [];
	} catch (error) {
		unwrapApiError(error);
	}
}

async function deletePhoto({
	albumId,
	photoId,
}: {
	albumId: string;
	photoId: string;
}): Promise<void> {
	try {
		await api.delete(`/albums/${albumId}/photos/${photoId}`);
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useDeletePhoto(albumId: string) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: deletePhoto,
		onSuccess: () => {
			// Freeing space is what re-enables adding (account-quota spec),
			// so the meters that show how much is left are stale the moment
			// a photo goes.
			queryClient.invalidateQueries({
				queryKey: accountUsageQueryOptions().queryKey,
			});
			queryClient.invalidateQueries({
				queryKey: albumUsageQueryOptions(albumId).queryKey,
			});
			// A deleted photo can change the album's cover and count too
			// (album-management spec), not only its own grid -- and, now
			// that the grid is the gallery (rating-gallery spec), every one
			// of its filters and their counts.
			queryClient.invalidateQueries({
				queryKey: photosQueryOptions(albumId).queryKey,
			});
			queryClient.invalidateQueries({
				queryKey: galleryQueryKeyPrefix(albumId),
			});
			queryClient.invalidateQueries({
				queryKey: albumStatsQueryOptions(albumId).queryKey,
			});
			queryClient.invalidateQueries({
				queryKey: albumsQueryOptions().queryKey,
			});
		},
	});
}
