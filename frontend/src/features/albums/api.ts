import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";

import { type ApiEnvelope, api, unwrapApiError } from "@/api";

export interface AlbumSummary {
	id: string;
	title: string;
	description: string | null;
	photoCount: number;
	coverUrl: string | null;
}

export interface Album {
	id: string;
	title: string;
	description: string | null;
}

async function fetchAlbums(): Promise<AlbumSummary[]> {
	const response = await api.get<ApiEnvelope<AlbumSummary[]>>("/albums");
	return response.data.data ?? [];
}

async function fetchAlbum(albumId: string): Promise<Album> {
	const response = await api.get<ApiEnvelope<Album>>(`/albums/${albumId}`);
	return response.data.data as Album;
}

// The one place each of these queries is defined (D9): the list route,
// the album layout, and the grid all consume these, and none keeps a
// second copy of the same data.
export function albumsQueryOptions() {
	return queryOptions({
		queryKey: ["albums"] as const,
		queryFn: fetchAlbums,
	});
}

export function albumQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId] as const,
		queryFn: () => fetchAlbum(albumId),
	});
}

export interface AlbumInput {
	title: string;
	description?: string;
}

async function createAlbum(input: AlbumInput): Promise<Album> {
	try {
		const response = await api.post<ApiEnvelope<Album>>("/albums", input);
		return response.data.data as Album;
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useCreateAlbum() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: createAlbum,
		onSuccess: () => {
			queryClient.invalidateQueries({
				queryKey: albumsQueryOptions().queryKey,
			});
		},
	});
}

async function renameAlbum({
	albumId,
	...body
}: AlbumInput & { albumId: string }): Promise<Album> {
	try {
		const response = await api.patch<ApiEnvelope<Album>>(
			`/albums/${albumId}`,
			body,
		);
		return response.data.data as Album;
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useRenameAlbum() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: renameAlbum,
		onSuccess: (album) => {
			queryClient.invalidateQueries({
				queryKey: albumsQueryOptions().queryKey,
			});
			queryClient.setQueryData(albumQueryOptions(album.id).queryKey, album);
		},
	});
}

async function deleteAlbum(albumId: string): Promise<void> {
	try {
		await api.delete(`/albums/${albumId}`);
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useDeleteAlbum() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: deleteAlbum,
		onSuccess: () => {
			queryClient.invalidateQueries({
				queryKey: albumsQueryOptions().queryKey,
			});
		},
	});
}
