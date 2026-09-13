import { queryOptions } from "@tanstack/react-query";

import { type ApiEnvelope, api } from "@/api";

export interface PendingPhoto {
	id: string;
	position: number;
	width: number | null;
	height: number | null;
	ratingUrl: string;
}

async function fetchPending(albumId: string): Promise<PendingPhoto[]> {
	const response = await api.get<ApiEnvelope<PendingPhoto[]>>(
		`/albums/${albumId}/pending`,
	);
	return response.data.data ?? [];
}

// Not paginated (D11): the deck is bounded by the album's own maximum, so
// this brings every pending photo in one reply.
export function pendingQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId, "pending"] as const,
		queryFn: () => fetchPending(albumId),
	});
}

// Not wrapped with `unwrapApiError` like the rest of this project's
// mutations: the rating queue (`ratingQueue.ts`) is what decides how to
// react to a failure here -- retry, then surface it -- so it needs the
// raw rejection, not this project's `ApiRequestError`.
export async function ratePhoto(
	albumId: string,
	photoId: string,
	approved: boolean,
): Promise<void> {
	await api.post(`/albums/${albumId}/photos/${photoId}/rating`, { approved });
}
