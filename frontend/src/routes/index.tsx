import { createFileRoute } from "@tanstack/react-router";

import { Cta } from "@/features/landing/Cta";
import { Features } from "@/features/landing/Features";
import { Hero } from "@/features/landing/Hero";
import { HowItWorks } from "@/features/landing/HowItWorks";
import { Navbar } from "@/features/landing/Navbar";

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
		<div className="flex min-h-dvh flex-col">
			<Navbar session={session} />
			<Hero session={session} />
			<HowItWorks />
			<Features />
			<Cta session={session} />
		</div>
	);
}
