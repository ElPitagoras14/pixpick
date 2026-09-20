import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import {
	createFileRoute,
	Link,
	Outlet,
	useMatchRoute,
} from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { AlbumHeader } from "@/features/albums/AlbumHeader";
import { albumQueryOptions } from "@/features/albums/api";
import { albumStatsQueryOptions } from "@/features/gallery/api";
import { ShareDialog } from "@/features/shares/ShareDialog";

// The album is loaded once, here: the grid, the upload view, and the two
// views a later change adds all read it from this layout's own context
// instead of asking for it again.
export const Route = createFileRoute("/_app/albums/$albumId")({
	loader: ({ context, params }) =>
		context.queryClient.ensureQueryData(albumQueryOptions(params.albumId)),
	component: AlbumLayout,
});

function AlbumLayout() {
	const { albumId } = Route.useParams();
	const { data: album } = useSuspenseQuery(albumQueryOptions(albumId));
	const matchRoute = useMatchRoute();
	// The album's own view goes back to the list; every subview beneath it
	// (upload, swipe) goes back to this album: the destination depends on
	// which screen this is, not on how it was reached, so it can't fork by
	// viewport either.
	const isAlbumView = !!matchRoute({ to: "/albums/$albumId" });
	// The upload view is its own flow, not a place to jump to Share or to
	// "Upload photos" again. What that changes about the back link is where it
	// points, not whether it exists: it is drawn here for every subview, above
	// the title, the way it is on every other screen -- so there can never be
	// two of them, or one below the title.
	const isUploadView = !!matchRoute({ to: "/albums/$albumId/upload" });
	// Its own query, mounted here rather than lifted from the gallery:
	// react-query resolves both consumers against the same cache entry.
	// `enabled` only stops the request (owner-only); whether the summary is
	// shown is decided by `isAlbumView` below, not by whether it happens to
	// already be in cache from a prior visit.
	const { data: stats } = useQuery({
		...albumStatsQueryOptions(albumId),
		enabled: album.isOwner && isAlbumView,
	});

	return (
		<div className="mx-auto max-w-3xl p-6">
			<div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
				<div>
					{isAlbumView ? (
						<Link
							to="/albums"
							search={{ group: "own" }}
							className="hidden text-muted-foreground text-xs md:block"
						>
							← Albums
						</Link>
					) : (
						<Link
							to="/albums/$albumId"
							params={{ albumId }}
							search={{ filter: "all" }}
							className="hidden text-muted-foreground text-xs md:block"
						>
							← Back to album
						</Link>
					)}
					<AlbumHeader album={album} stats={isAlbumView ? stats : undefined} />
				</div>
				{!isUploadView && (
					<div className="flex items-center gap-2">
						{album.isOwner && (
							<>
								<ShareDialog albumId={albumId} />
								<Button asChild className="h-11 md:h-7" size="sm">
									<Link to="/albums/$albumId/upload" params={{ albumId }}>
										Upload photos
									</Link>
								</Button>
							</>
						)}
						{album.pendingCount > 0 && (
							<Button
								asChild
								className="h-11 md:h-7"
								size="sm"
								variant="secondary"
							>
								<Link to="/albums/$albumId/swipe" params={{ albumId }}>
									Rate {album.pendingCount} photo
									{album.pendingCount === 1 ? "" : "s"}
								</Link>
							</Button>
						)}
					</div>
				)}
			</div>
			<Outlet />
		</div>
	);
}
