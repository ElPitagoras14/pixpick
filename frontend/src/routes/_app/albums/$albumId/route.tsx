import { useSuspenseQuery } from "@tanstack/react-query";
import {
	createFileRoute,
	Link,
	Outlet,
	useMatchRoute,
} from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { albumQueryOptions } from "@/features/albums/api";
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
	// The upload view is its own flow, not a place to jump to Share or to
	// "Upload photos" again: its own "← Back to album" link is the one
	// back link that belongs there, replacing this layout's "← Albums"
	// rather than sitting above it.
	const isUploadView = !!matchRoute({ to: "/albums/$albumId/upload" });

	return (
		<div className="mx-auto max-w-3xl p-6">
			<div className="mb-6 flex items-center justify-between gap-4">
				<div>
					{!isUploadView && (
						<Link
							to="/albums"
							search={{ group: "own" }}
							className="text-muted-foreground text-xs"
						>
							← Albums
						</Link>
					)}
					<h1 className="text-xl font-bold">{album.title}</h1>
					{album.description && (
						<p className="text-muted-foreground text-sm">{album.description}</p>
					)}
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
