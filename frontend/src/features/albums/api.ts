import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";

import { type ApiEnvelope, api, unwrapApiError } from "@/api";
import { accountUsageQueryOptions } from "@/features/quota/api";

export interface AlbumSummary {
	id: string;
	title: string;
	description: string | null;
	isOwner: boolean;
	photoCount: number;
	coverUrl: string | null;
	pendingCount: number;
	// The instant the album stops existing, as an ISO timestamp: the backend
	// sends the instant itself, never a rendered string or a day count, and
	// turning it into either one is this client's job -- see
	// `remainingTimeLabel`.
	expiresAt: string;
}

export interface Album {
	id: string;
	title: string;
	description: string | null;
	isOwner: boolean;
	pendingCount: number;
	expiresAt: string;
}

const DAY_IN_MS = 24 * 60 * 60 * 1000;

// Turns the backend's raw instant into what someone reads: the day it falls
// into from *now*, not a rounded duration -- something confirmed a minute
// ago reads "today", not "in 0 days". Shown to the owner and to anyone with
// a shared link alike: both need to know how long the album -- and their
// chance to finish rating it -- has left.
export function remainingTimeLabel(expiresAt: string): string {
	const daysRemaining = Math.ceil(
		(new Date(expiresAt).getTime() - Date.now()) / DAY_IN_MS,
	);
	if (daysRemaining <= 0) return "Expires today";
	if (daysRemaining === 1) return "Expires tomorrow";
	return `Expires in ${daysRemaining} days`;
}

async function fetchAlbums(): Promise<AlbumSummary[]> {
	const response = await api.get<ApiEnvelope<AlbumSummary[]>>("/albums");
	return response.data.data ?? [];
}

async function fetchAlbum(albumId: string): Promise<Album> {
	const response = await api.get<ApiEnvelope<Album>>(`/albums/${albumId}`);
	return response.data.data as Album;
}

// The one place each of these queries is defined: the list route, the album
// layout, and the grid all consume these, and none keeps a second copy of
// the same data.
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

// What create/rename return: the album's own descriptive fields, never
// `isOwner`/`pendingCount` -- those depend on who's asking and what they've
// rated, which only the detail endpoint (`fetchAlbum`) resolves.
export interface AlbumEditResult {
	id: string;
	title: string;
	description: string | null;
}

async function createAlbum(input: AlbumInput): Promise<AlbumEditResult> {
	try {
		const response = await api.post<ApiEnvelope<AlbumEditResult>>(
			"/albums",
			input,
		);
		return response.data.data as AlbumEditResult;
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
}: AlbumInput & { albumId: string }): Promise<AlbumEditResult> {
	try {
		const response = await api.patch<ApiEnvelope<AlbumEditResult>>(
			`/albums/${albumId}`,
			body,
		);
		return response.data.data as AlbumEditResult;
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
			// Not `setQueryData`: the rename response doesn't carry
			// `isOwner`/`pendingCount`, so caching it verbatim would erase
			// them from whatever the detail query already held.
			queryClient.invalidateQueries({
				queryKey: albumQueryOptions(album.id).queryKey,
			});
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
			// An album takes its photos with it, so what it occupied stops counting
			// against its owner's limit.
			queryClient.invalidateQueries({
				queryKey: accountUsageQueryOptions().queryKey,
			});
		},
	});
}
