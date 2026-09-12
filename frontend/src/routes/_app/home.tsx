import { createFileRoute } from "@tanstack/react-router";

// The `_app` layout's first real child (deferred from add-local-environment:
// a pathless layout with no children resolves to the same route as the
// top-level index). Nothing to show yet -- that arrives with albums.
export const Route = createFileRoute("/_app/home")({ component: Home });

function Home() {
	return (
		<div className="p-6 text-center">
			<p className="text-muted-foreground text-sm">
				You're signed in. Nothing here yet.
			</p>
		</div>
	);
}
