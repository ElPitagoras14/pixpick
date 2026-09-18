import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({ component: Landing });

// The public way in (app-entry spec): says what this is to someone who
// has never seen it, and offers a way in whatever the session state is.
// Outside the `_app` layout, so it carries no guard and never redirects.
function Landing() {
	// The session the root route already resolved and threads down (D3):
	// no query of its own, and the page stays public either way -- whoever
	// isn't signed in gets this same screen with the other button.
	const { session } = Route.useRouteContext();

	return (
		<div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
			<h1 className="text-3xl font-bold">pixpick</h1>
			<p className="text-muted-foreground max-w-sm text-sm">
				Share a photo album with the people who were there, and let everyone
				swipe through it to pick the shots worth keeping.
			</p>
			{/* One access, two cases (app-entry spec): signed in it goes
			straight inside, signed out it goes to log in -- never absent. */}
			<Button asChild size="lg" className="min-h-11 min-w-40">
				{session ? (
					<Link to="/home">Enter pixpick</Link>
				) : (
					<Link to="/login" search={{}}>
						Log in
					</Link>
				)}
			</Button>
		</div>
	);
}
