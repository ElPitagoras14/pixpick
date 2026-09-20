import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
	type AlbumSummary,
	albumsQueryOptions,
	remainingTimeLabel,
} from "@/features/albums/api";
import { accountUsageQueryOptions, formatBytes } from "@/features/quota/api";
import { cn } from "@/lib/utils";

const ALBUM_GROUPS = ["own", "shared"] as const;
type AlbumGroup = (typeof ALBUM_GROUPS)[number];

// A closed set with a default, the same pattern the gallery's own filter
// uses: an unrecognized group falls back to "own" instead of producing an
// error.
const albumsSearchSchema = z.object({
	group: z.enum(ALBUM_GROUPS).catch("own"),
});

export const Route = createFileRoute("/_app/albums/")({
	validateSearch: albumsSearchSchema,
	loader: ({ context }) =>
		Promise.all([
			context.queryClient.ensureQueryData(albumsQueryOptions()),
			context.queryClient.ensureQueryData(accountUsageQueryOptions()),
		]),
	component: AlbumsList,
});

const GROUP_LABEL: Record<AlbumGroup, string> = {
	own: "My albums",
	shared: "Shared with me",
};

const EMPTY_GROUP_MESSAGE: Record<AlbumGroup, string> = {
	own: "You don't have any albums yet.",
	shared: "No one has shared an album with you yet.",
};

function AlbumsList() {
	const { data: albums } = useSuspenseQuery(albumsQueryOptions());
	// The same breakdown the home's own total is sliced from, so what each
	// card shows always adds up to what the home shows. Only the albums this
	// person owns appear in it -- what a shared album occupies is its owner's
	// space, and not this viewer's to see.
	const { data: usage } = useSuspenseQuery(accountUsageQueryOptions());
	const usedByAlbumId = new Map(
		usage.albums.map((entry) => [entry.albumId, entry.usedBytes]),
	);
	const { group } = Route.useSearch();

	// Split here, not with a second request: the list the server already
	// returned distinguishes owned from shared, so grouping and counting each
	// group are two array filters over data already in hand, and the backend
	// is untouched.
	const groups: Record<AlbumGroup, AlbumSummary[]> = {
		own: albums.filter((album) => album.isOwner),
		shared: albums.filter((album) => !album.isOwner),
	};
	const visible = groups[group];

	return (
		<div className="mx-auto max-w-3xl p-6">
			<div className="mb-6 flex items-center justify-between">
				<h1 className="text-xl font-bold">Albums</h1>
				<Button asChild size="sm">
					<Link to="/albums/new">New album</Link>
				</Button>
			</div>

			<div className="mb-6 flex gap-1">
				{ALBUM_GROUPS.map((candidate) => (
					<Link
						key={candidate}
						to="/albums"
						search={{ group: candidate }}
						className={cn(
							"rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
							group === candidate
								? "bg-primary text-primary-foreground"
								: "text-muted-foreground hover:bg-muted",
						)}
					>
						{GROUP_LABEL[candidate]}{" "}
						<span className={group === candidate ? "opacity-80" : "opacity-60"}>
							{groups[candidate].length}
						</span>
					</Link>
				))}
			</div>

			{visible.length === 0 ? (
				// Says what would appear here, so an empty group never reads like a
				// list still loading -- the suspense boundary above already handles
				// that state on its own.
				<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
					<p className="text-muted-foreground text-sm">
						{EMPTY_GROUP_MESSAGE[group]}
					</p>
					{group === "own" && (
						<Button asChild size="sm">
							<Link to="/albums/new">Create your first album</Link>
						</Button>
					)}
				</div>
			) : (
				<ul className="grid grid-cols-2 gap-4 sm:grid-cols-3">
					{visible.map((album) => (
						<li key={album.id}>
							<Link
								to="/albums/$albumId"
								params={{ albumId: album.id }}
								search={{ filter: "all" }}
								// `flex h-full flex-col`: a grid row already stretches
								// each `<li>` to the tallest one, but the link itself
								// still sized to its own content -- a card with the
								// "to rate" line and one without would otherwise show
								// different heights inside the same, equally tall row.
								className="group flex h-full flex-col overflow-hidden rounded-xl border"
							>
								<div className="bg-muted aspect-square w-full overflow-hidden">
									{album.coverUrl ? (
										<img
											src={album.coverUrl}
											alt=""
											className="size-full object-cover transition-transform group-hover:scale-105"
										/>
									) : (
										<div className="text-muted-foreground flex size-full items-center justify-center text-xs">
											No photos yet
										</div>
									)}
								</div>
								<div className="flex flex-1 flex-col justify-center gap-0.5 p-2">
									<p className="truncate text-sm font-medium">{album.title}</p>
									<p className="text-muted-foreground text-xs">
										{album.photoCount} photo
										{album.photoCount === 1 ? "" : "s"}
										{usedByAlbumId.has(album.id) &&
											` · ${formatBytes(usedByAlbumId.get(album.id) ?? 0)}`}
									</p>
									{album.pendingCount > 0 && (
										<p className="text-xs font-medium text-primary">
											{album.pendingCount} to rate
										</p>
									)}
									<p className="text-muted-foreground text-xs">
										{remainingTimeLabel(album.expiresAt)}
									</p>
								</div>
							</Link>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}
