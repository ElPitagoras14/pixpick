import { queryOptions } from "@tanstack/react-query";

import { type ApiEnvelope, api } from "@/api";

export interface AlbumUsageEntry {
	albumId: string;
	usedBytes: number;
}

export interface AccountUsage {
	usedBytes: number;
	limitBytes: number;
	albums: AlbumUsageEntry[];
}

/** The instance's own resource (instance-quota spec, D3): only the
 * percentage occupied, rounded -- never the raw total or limit, which
 * describe the installation's real capacity and aren't this resource's
 * to publish to every signed-in session. */
export interface InstanceUsage {
	usedPercent: number;
}

export interface PhotoUsageEntry {
	photoId: string;
	sizeBytes: number;
}

export interface AlbumUsage {
	usedBytes: number;
	photos: PhotoUsageEntry[];
}

const EMPTY_ACCOUNT_USAGE: AccountUsage = {
	usedBytes: 0,
	limitBytes: 0,
	albums: [],
};

const EMPTY_INSTANCE_USAGE: InstanceUsage = { usedPercent: 0 };

async function fetchAccountUsage(): Promise<AccountUsage> {
	const response = await api.get<ApiEnvelope<AccountUsage>>("/account/usage");
	return response.data.data ?? EMPTY_ACCOUNT_USAGE;
}

async function fetchInstanceUsage(): Promise<InstanceUsage> {
	const response = await api.get<ApiEnvelope<InstanceUsage>>("/instance/usage");
	return response.data.data ?? EMPTY_INSTANCE_USAGE;
}

async function fetchAlbumUsage(albumId: string): Promise<AlbumUsage> {
	const response = await api.get<ApiEnvelope<AlbumUsage>>(
		`/albums/${albumId}/usage`,
	);
	return response.data.data ?? { usedBytes: 0, photos: [] };
}

// The one place each of these queries is defined: the home, the album
// list and the upload view all read the account's usage, and none keeps
// a copy of its own. Invalidated wherever something changes what it
// returns -- uploading and deleting, which are the only two.
export function accountUsageQueryOptions() {
	return queryOptions({
		queryKey: ["account", "usage"] as const,
		queryFn: fetchAccountUsage,
	});
}

// No account or album ever invalidates this one on its own (D3 in
// add-instance-quota): what any of them occupies is a slice of the same
// total, but the total belongs to nobody in particular, so it's read
// fresh rather than kept in step with every place that changes it.
export function instanceUsageQueryOptions() {
	return queryOptions({
		queryKey: ["instance", "usage"] as const,
		queryFn: fetchInstanceUsage,
	});
}

// Owner-only on the server (account-quota spec): mounted only for the
// owner, since for anyone else this resource is forbidden.
export function albumUsageQueryOptions(albumId: string) {
	return queryOptions({
		queryKey: ["albums", albumId, "usage"] as const,
		queryFn: () => fetchAlbumUsage(albumId),
	});
}

const UNITS = ["B", "KB", "MB", "GB"] as const;

/** A size a person can read at a glance, in the units storage is usually
 * quoted in. One decimal below 10 and none above, so a column of these
 * stays about the same width and the difference between two of them is
 * still visible where it matters. */
export function formatBytes(bytes: number): string {
	let value = bytes;
	let unit = 0;
	while (value >= 1024 && unit < UNITS.length - 1) {
		value /= 1024;
		unit += 1;
	}
	const decimals = unit === 0 || value >= 10 ? 0 : 1;
	return `${value.toFixed(decimals)} ${UNITS[unit]}`;
}
