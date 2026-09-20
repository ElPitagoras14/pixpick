import { useCallback, useEffect, useState } from "react";

import type { PendingPhoto } from "@/features/swipe/api";
import { useRatingQueue } from "@/features/swipe/ratingQueue";

// A handful ahead, never the whole album: enough that advancing never has
// to wait on the network, without competing for bandwidth with the photo
// actually on screen.
const PRELOAD_AHEAD = 2;

/** Drives one rating sequence: what's left to show is plain client state
 * seeded from the server's own pending list, decided against locally and
 * never re-fetched mid-sequence -- the server side of each decision is the
 * rating queue's job, not this hook's. */
export function useSwipeDeck(albumId: string, initialPhotos: PendingPhoto[]) {
	const [remaining, setRemaining] = useState(initialPhotos);
	const { enqueue, failed, dismissFailure, retryFailure } =
		useRatingQueue(albumId);

	useEffect(() => {
		// Reuses the exact addresses the sequence already returned -- never a new
		// one built for the occasion -- so the preload warms the very same cache
		// entry the next card's `<img>` requests.
		for (const photo of remaining.slice(0, PRELOAD_AHEAD)) {
			const image = new Image();
			image.src = photo.ratingUrl;
		}
	}, [remaining]);

	const decide = useCallback(
		(approved: boolean) => {
			setRemaining((prev) => {
				const [current, ...rest] = prev;
				if (!current) return prev;
				enqueue(current.id, approved);
				return rest;
			});
		},
		[enqueue],
	);

	return {
		// What is left of the sequence, in its own order: the set the viewer
		// moves through when a photo is opened from the card.
		remaining,
		current: remaining[0] ?? null,
		next: remaining[1] ?? null,
		finished: remaining.length === 0,
		decide,
		failed,
		dismissFailure,
		retryFailure,
	};
}
