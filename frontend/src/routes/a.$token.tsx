import { createFileRoute, notFound, redirect } from "@tanstack/react-router";

import { albumQueryOptions } from "@/features/albums/api";
import { enterShare } from "@/features/shares/api";

// A flat route, deliberately outside `/_app`: opening it is a plain
// navigation -- the read half of the flow -- and only the write this loader
// fires next is what actually grants membership. The guard below mirrors
// `_app`'s own, since this route isn't nested under it and inherits none of
// its behavior.
export const Route = createFileRoute("/a/$token")({
	beforeLoad: ({ context, location }) => {
		if (!context.session) {
			throw redirect({ to: "/login", search: { returnTo: location.href } });
		}
	},
	loader: async ({ params, context }) => {
		let albumId: string;
		try {
			({ albumId } = await enterShare(params.token));
		} catch {
			// An unknown, revoked, or foreign token all land here the same way --
			// the API already made the three indistinguishable, and this route
			// doesn't try to un-collapse them either.
			throw notFound();
		}
		const album = await context.queryClient.ensureQueryData(
			albumQueryOptions(albumId),
		);
		throw redirect({
			to:
				album.pendingCount > 0 ? "/albums/$albumId/swipe" : "/albums/$albumId",
			params: { albumId },
		});
	},
	notFoundComponent: InvalidLink,
});

function InvalidLink() {
	return (
		<div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
			<h1 className="text-2xl font-bold">This link doesn't work</h1>
			<p className="text-muted-foreground max-w-xs text-sm">
				It may have been revoked, or it never existed.
			</p>
		</div>
	);
}
