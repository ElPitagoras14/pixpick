import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { type AlbumSummary, albumsQueryOptions } from "@/features/albums/api";
import {
	accountUsageQueryOptions,
	instanceUsageQueryOptions,
} from "@/features/quota/api";
import { StorageMeter } from "@/features/quota/StorageMeter";

// Where signing in lands (identity-provider spec's DEFAULT_RETURN_TO), so
// it answers "what now?" rather than "you're in" (app-entry spec): how
// much room is left, what's waiting to be rated, and where to start
// something new. The album list stays the "what do I have?" screen.
export const Route = createFileRoute("/_app/home")({
	// Only the albums are awaited, and under the list's own key (D1), so
	// this is the same single request either screen already makes -- never
	// a second one, in either direction.
	loader: ({ context }) =>
		context.queryClient.ensureQueryData(albumsQueryOptions()),
	component: Home,
});

function Home() {
	const { data: albums } = useSuspenseQuery(albumsQueryOptions());
	// Requested alongside the albums and never awaited before drawing
	// (D2), the same way the album view asks for its owner stats: if this
	// one fails or is still in flight, everything below still renders --
	// not seeing the meter can't stand between anyone and what they have
	// left to rate. The instance's own usage travels the same way and for
	// the same reason (task 4.2 in add-instance-quota).
	const { data: usage } = useQuery(accountUsageQueryOptions());
	const { data: instanceUsage } = useQuery(instanceUsageQueryOptions());

	return (
		<div className="mx-auto flex max-w-3xl flex-col gap-8 p-6">
			{(usage || instanceUsage) && (
				<div className="flex flex-col gap-4 sm:flex-row sm:gap-8">
					{usage && (
						<div className="flex-1">
							<StorageMeter usage={usage} />
						</div>
					)}
					{instanceUsage && (
						<div className="flex-1">
							{/* A different label and a different full-space
							message (D5, app-entry spec's "se distingue cuál es
							cuál"): this one isn't the viewer's own space, so it
							never tells them to delete anything of theirs. */}
							<StorageMeter
								usage={instanceUsage}
								label="Instance storage"
								fullMessage="The instance is full. This isn't your storage — space frees up once someone deletes photos."
							/>
						</div>
					)}
				</div>
			)}

			<section className="flex flex-col gap-3">
				<div className="flex flex-wrap items-center justify-between gap-3">
					<h1 className="text-xl font-bold">To rate</h1>
					<Button asChild size="sm">
						<Link to="/albums/new">New album</Link>
					</Button>
				</div>
				<ToRate albums={albums} />
			</section>
		</div>
	);
}

/** The three states kept apart (D4): no albums at all, albums with
 * nothing left to rate, and albums with photos waiting. The first two
 * both come out as a section with no rows and mean the opposite of each
 * other -- one is "start here", the other is "you're done" -- so they are
 * three branches here and never a test on a list's length. */
function ToRate({ albums }: { albums: AlbumSummary[] }) {
	if (albums.length === 0) {
		return (
			<EmptyState message="You don't have any albums yet. Create one, add photos, and share it to start collecting ratings.">
				<Button asChild size="sm">
					<Link to="/albums/new">Create your first album</Link>
				</Button>
			</EmptyState>
		);
	}

	// Filtered in memory off the list's own response (D1): the count shown
	// next to an album here is literally the number that album reports,
	// read twice, not a second source that could drift from it. Shared
	// albums included -- what waits for this viewer's rating doesn't
	// depend on who owns it.
	const pending = albums.filter((album) => album.pendingCount > 0);

	if (pending.length === 0) {
		return (
			<EmptyState message="Nothing left to rate. Every photo you can see already has your rating.">
				<Button asChild size="sm" variant="outline">
					<Link to="/albums" search={{ group: "own" }}>
						Go to your albums
					</Link>
				</Button>
			</EmptyState>
		);
	}

	return (
		<ul className="flex flex-col gap-2">
			{pending.map((album) => (
				<li key={album.id}>
					{/* Straight into the deck, not into the album: from here
					the next thing to do is rate (app-entry spec), and going
					through the album is what the list is for. */}
					<Link
						to="/albums/$albumId/swipe"
						params={{ albumId: album.id }}
						className="hover:bg-muted flex min-h-14 items-center justify-between gap-3 rounded-xl border p-4 transition-colors"
					>
						<span className="min-w-0 flex-1 truncate text-sm font-medium">
							{album.title}
						</span>
						<span className="text-primary shrink-0 text-xs font-medium">
							{album.pendingCount} to rate
						</span>
					</Link>
				</li>
			))}
		</ul>
	);
}

function EmptyState({
	message,
	children,
}: {
	message: string;
	children: ReactNode;
}) {
	return (
		<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
			<p className="text-muted-foreground text-sm">{message}</p>
			{children}
		</div>
	);
}
