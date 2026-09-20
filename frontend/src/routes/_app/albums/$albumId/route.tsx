import { useSuspenseQuery } from "@tanstack/react-query";
import {
	createFileRoute,
	Link,
	Outlet,
	useMatchRoute,
} from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { albumQueryOptions, remainingTimeLabel } from "@/features/albums/api";
import { ShareDialog } from "@/features/shares/ShareDialog";

// The album is loaded once, here (D11): the grid, the upload view, and
// the two views a later change adds all read it from this layout's own
// context instead of asking for it again.
export const Route = createFileRoute("/_app/albums/$albumId")({
	loader: ({ context, params }) =>
		context.queryClient.ensureQueryData(albumQueryOptions(params.albumId)),
	component: AlbumLayout,
});

function AlbumLayout() {
	const { albumId } = Route.useParams();
	const { data: album } = useSuspenseQuery(albumQueryOptions(albumId));
	const matchRoute = useMatchRoute();
	// The album's own view goes back to the list; every subview beneath
	// it (upload, swipe) goes back to this album (app-navigation spec:
	// the destination depends on which screen this is, not on how it was
	// reached, so it can't fork by viewport either -- see design.md).
	const isAlbumView = !!matchRoute({ to: "/albums/$albumId" });
	// The upload view is its own flow, not a place to jump to Share or to
	// "Upload photos" again. What that changes about the back link is
	// where it points, not whether it exists (D1): it is drawn here for
	// every subview, above the title, the way it is on every other screen
	// -- so there can never be two of them, or one below the title.
	const isUploadView = !!matchRoute({ to: "/albums/$albumId/upload" });

	return (
		<div className="mx-auto max-w-3xl p-6">
			<div className="mb-6 flex items-center justify-between gap-4">
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
					<h1 className="text-xl font-bold">{album.title}</h1>
					{album.description && (
						<p className="text-muted-foreground text-sm">{album.description}</p>
					)}
					<p className="text-muted-foreground text-xs">
						{remainingTimeLabel(album.expiresAt)}
					</p>
				</div>
				{!isUploadView && (
					<div className="flex items-center gap-2">
						{album.isOwner && (
							<>
								<ShareDialog albumId={albumId} />
								<Button asChild size="sm">
									<Link to="/albums/$albumId/upload" params={{ albumId }}>
										Upload photos
									</Link>
								</Button>
							</>
						)}
						{album.pendingCount > 0 && (
							<Button asChild size="sm" variant="secondary">
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
