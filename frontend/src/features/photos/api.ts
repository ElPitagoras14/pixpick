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

export interface Photo {
	id: string;
	position: number;
	width: number | null;
	height: number | null;
	thumbnailUrl: string;
}

export interface PhotoGrant {
	photoId: string;
	position: number;
	uploadUrl: string;
	uploadFields: Record<string, string>;
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
): Promise<PhotoGrant[]> {
	try {
		const response = await api.post<ApiEnvelope<PhotoGrant[]>>(
			`/albums/${albumId}/photos/grants`,
			{ files },
		);
		return response.data.data ?? [];
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
