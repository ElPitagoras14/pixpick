import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";

import { type ApiEnvelope, api } from "@/api";
import { albumQueryOptions, albumsQueryOptions } from "@/features/albums/api";
import { ratePhoto } from "@/features/swipe/api";

export const GALLERY_FILTERS = [
	"all",
	"approved",
	"rejected",
	"unrated",
] as const;
export type GalleryFilter = (typeof GALLERY_FILTERS)[number];

export interface GalleryPhoto {
	id: string;
	position: number;
	width: number | null;
	height: number | null;
	thumbnailUrl: string;
	// The largest variant, carried next to the thumbnail and requested only
	// when a photo is actually opened: drawing the grid costs exactly what it
	// cost before.
	viewerUrl: string;
	rating: "approved" | "rejected" | null;
}

export interface GalleryCounts {
	total: number;
	approved: number;
	rejected: number;
	unrated: number;
}

export interface Gallery {
	photos: GalleryPhoto[];
	counts: GalleryCounts;
}

const EMPTY_COUNTS: GalleryCounts = {
	total: 0,
	approved: 0,
	rejected: 0,
	unrated: 0,
};

async function fetchGallery(
	albumId: string,
	filter: GalleryFilter,
): Promise<Gallery> {
	const response = await api.get<ApiEnvelope<Gallery>>(
		`/albums/${albumId}/photos/gallery`,
		{ params: { filter } },
	);
	return response.data.data ?? { photos: [], counts: EMPTY_COUNTS };
}

// Every filter's own cache lives under this one prefix: setting a rating
// invalidates all four together, rather than working out which ones the
// change actually moved the photo into or out of. Exported so that
// uploading and deleting a photo (`features/photos`) can invalidate every
// filter too, without importing each one's own query options.
export function galleryQueryKeyPrefix(albumId: string) {
	return ["albums", albumId, "gallery"] as const;
}

export function galleryQueryOptions(albumId: string, filter: GalleryFilter) {
	return queryOptions({
		queryKey: [...galleryQueryKeyPrefix(albumId), filter] as const,
		queryFn: () => fetchGallery(albumId, filter),
	});
}

/** Changes a rating from the gallery: the same `ratePhoto` operation the
 * swipe sequence uses, but through a plain optimistic mutation instead of
 * the swipe's own retrying queue -- the queue exists for a burst of
 * decisions in a row, and here it's one tap at a time. */
export function useSetRating(albumId: string) {
	const queryClient = useQueryClient();
	const prefix = galleryQueryKeyPrefix(albumId);

	return useMutation({
		mutationFn: ({
			photoId,
			approved,
		}: {
			photoId: string;
			approved: boolean;
		}) => ratePhoto(albumId, photoId, approved),
		// This only ever patches the `rating` field of the matching entry, in
		// every filter's own cached list -- it never removes an entry, even from
		// a list it no longer belongs in. That's what keeps the grid from jumping
		// under whoever just tapped it.
		onMutate: async ({ photoId, approved }) => {
			await queryClient.cancelQueries({ queryKey: prefix });
			const previous = queryClient.getQueriesData<Gallery>({
				queryKey: prefix,
			});
			queryClient.setQueriesData<Gallery>({ queryKey: prefix }, (data) =>
				data
					? {
							...data,
							photos: data.photos.map((photo) =>
								photo.id === photoId
									? { ...photo, rating: approved ? "approved" : "rejected" }
									: photo,
							),
						}
					: data,
			);
			return { previous };
		},
		onError: (_error, _variables, context) => {
			context?.previous.forEach(([key, data]) => {
				queryClient.setQueryData(key, data);
			});
		},
		onSettled: () => {
			// Marked stale, not force-refetched (`refetchType: "none"`): the filter
			// being looked at right now keeps its optimistic value until it's asked
			// for again -- a background refetch here would remove the photo the
			// instant the request resolves, which is exactly the jump to avoid.
			queryClient.invalidateQueries({ queryKey: prefix, refetchType: "none" });
			queryClient.invalidateQueries({
				queryKey: albumQueryOptions(albumId).queryKey,
			});
			queryClient.invalidateQueries({
				queryKey: albumsQueryOptions().queryKey,
			});
		},
	});
}

export interface PhotoStats {
	photoId: string;
	approvedCount: number;
	rejectedCount: number;
}

export interface AlbumStats {
	photos: PhotoStats[];
	participantCount: number;
	ratingCount: number;
}

async function fetchAlbumStats(albumId: string): Promise<AlbumStats> {
	const response = await api.get<ApiEnvelope<AlbumStats>>(
		`/albums/${albumId}/stats`,
	);
	return (
		response.data.data ?? { photos: [], participantCount: 0, ratingCount: 0 }
	);
}

// Owner-only on the server; this project's own router never even mounts a
// route that would call this for anyone else.
export function albumStatsQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId, "stats"] as const,
		queryFn: () => fetchAlbumStats(albumId),
	});
}
