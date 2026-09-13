import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";

import { type ApiEnvelope, api, unwrapApiError } from "@/api";

export interface ShareLink {
	url: string;
}

async function fetchShareLink(albumId: string): Promise<ShareLink> {
	const response = await api.get<ApiEnvelope<ShareLink>>(
		`/albums/${albumId}/share`,
	);
	return response.data.data as ShareLink;
}

// Idempotent on the server (album-sharing spec): asking for it is what
// creates the album's first link, and asking again just returns the same
// one -- so this is a query, not a mutation, even though it can write.
export function shareLinkQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId, "share"] as const,
		queryFn: () => fetchShareLink(albumId),
	});
}

async function regenerateShareLink(albumId: string): Promise<ShareLink> {
	try {
		const response = await api.post<ApiEnvelope<ShareLink>>(
			`/albums/${albumId}/share/regenerate`,
		);
		return response.data.data as ShareLink;
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useRegenerateShareLink(albumId: string) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: () => regenerateShareLink(albumId),
		onSuccess: (link) => {
			queryClient.setQueryData(shareLinkQueryOptions(albumId).queryKey, link);
		},
	});
}

async function revokeShareLink(albumId: string): Promise<void> {
	try {
		await api.post(`/albums/${albumId}/share/revoke`);
	} catch (error) {
		unwrapApiError(error);
	}
}

export function useRevokeShareLink(albumId: string) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: () => revokeShareLink(albumId),
		onSuccess: () => {
			queryClient.removeQueries({
				queryKey: shareLinkQueryOptions(albumId).queryKey,
			});
		},
	});
}

export interface EnterShareResult {
	albumId: string;
}

// A write, deliberately (D4, album-sharing spec): entering grants
// membership, and only a same-origin POST -- never a plain navigation --
// is allowed to do that.
export async function enterShare(token: string): Promise<EnterShareResult> {
	try {
		const response = await api.post<ApiEnvelope<EnterShareResult>>(
			`/shares/${token}`,
		);
		return response.data.data as EnterShareResult;
	} catch (error) {
		unwrapApiError(error);
	}
}
