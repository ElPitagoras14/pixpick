import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { albumQueryOptions } from "@/features/albums/api";
import { ratePhoto } from "@/features/swipe/api";

// Spaced retries, not exponential from zero (D6): a rating that fails
// once almost always fails because of a momentary blip, so the first
// retry comes quickly; only a rating that keeps failing waits longer.
const RETRY_DELAYS_MS = [500, 2000, 5000];

export interface FailedRating {
	photoId: string;
	approved: boolean;
}

interface QueueItem extends FailedRating {
	attempt: number;
}

function wait(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Sends ratings one at a time, in the order they were decided, retrying
 * a failure a few times before giving up on that one item (D6): never in
 * a batch, so closing the tab loses at most the single request in
 * flight, not everything queued behind it. A rating that exhausts its
 * retries is reported through `failed` -- its own decided value included,
 * never silently dropped -- while the queue moves on to what's next.
 */
export function useRatingQueue(albumId: string) {
	const [failed, setFailed] = useState<FailedRating[]>([]);
	const queueRef = useRef<QueueItem[]>([]);
	const processingRef = useRef(false);
	const queryClient = useQueryClient();

	const processNext = useCallback(async () => {
		if (processingRef.current) return;
		processingRef.current = true;
		try {
			for (
				let item = queueRef.current.shift();
				item;
				item = queueRef.current.shift()
			) {
				try {
					await ratePhoto(albumId, item.photoId, item.approved);
					// Only once the server actually recorded it -- invalidating
					// any earlier would just refetch the count this same
					// rating hasn't reached yet, showing a stale one instead.
					queryClient.invalidateQueries({
						queryKey: albumQueryOptions(albumId).queryKey,
					});
					queryClient.invalidateQueries({ queryKey: ["albums"] });
				} catch {
					if (item.attempt < RETRY_DELAYS_MS.length) {
						await wait(RETRY_DELAYS_MS[item.attempt]);
						queueRef.current.unshift({ ...item, attempt: item.attempt + 1 });
					} else {
						setFailed((prev) => [
							...prev,
							{ photoId: item.photoId, approved: item.approved },
						]);
					}
				}
			}
		} finally {
			processingRef.current = false;
		}
	}, [albumId, queryClient]);

	const enqueue = useCallback(
		(photoId: string, approved: boolean) => {
			queueRef.current.push({ photoId, approved, attempt: 0 });
			void processNext();
		},
		[processNext],
	);

	const dismissFailure = useCallback((photoId: string) => {
		setFailed((prev) => prev.filter((item) => item.photoId !== photoId));
	}, []);

	const retryFailure = useCallback(
		(photoId: string) => {
			const item = failed.find((candidate) => candidate.photoId === photoId);
			if (!item) return;
			dismissFailure(photoId);
			enqueue(item.photoId, item.approved);
		},
		[failed, dismissFailure, enqueue],
	);

	return { enqueue, failed, dismissFailure, retryFailure };
}
