import { Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import type { CurrentUser } from "@/features/auth/api";
import { SwipeMock } from "@/features/landing/SwipeMock";

interface LandingAccessButtonProps {
	session: CurrentUser | null;
	size?: "default" | "lg";
	// The signed-out label varies by where the button sits (a marketing
	// CTA in the hero/final CTA reads differently than a nav bar's login
	// link); the session check and the destinations themselves don't.
	loggedOutLabel?: string;
}

// The one place this ternary is written: Cta.tsx and Navbar.tsx import this
// same component instead of repeating `session ?...:...` on their own.
export function LandingAccessButton({
	session,
	size = "lg",
	loggedOutLabel = "Log in",
}: LandingAccessButtonProps) {
	return (
		<Button
			asChild
			size={size}
			// The big touch-target width only makes sense for the hero/CTA's
			// large button, not the compact navbar one -- there it would
			// force the whole header wider than a "Log in"/"Enter" label
			// needs.
			className={size === "lg" ? "min-h-11 min-w-40" : undefined}
		>
			{session ? (
				<Link to="/home">Enter pixpick</Link>
			) : (
				<Link to="/login" search={{}}>
					{loggedOutLabel}
				</Link>
			)}
		</Button>
	);
}

interface HeroProps {
	session: CurrentUser | null;
}

export function Hero({ session }: HeroProps) {
	return (
		<section className="mx-auto grid w-full max-w-5xl grid-cols-1 items-center gap-10 px-6 pt-16 pb-12 lg:grid-cols-2 lg:gap-16 lg:pt-24">
			{/* `grid-cols-1` on the section is load-bearing (not decorative):
			without it this implicit single-column grid sizes its track to
			its widest child's max-content instead of the viewport, and the
			paragraph below overflows past the edge on anything narrower
			than its own `max-w-md`. `grid-cols-1` uses `minmax(0, 1fr)`,
			which actually shrinks to the available width. */}
			<div className="flex w-full flex-col items-center gap-4 text-center lg:items-start lg:text-left">
				<h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
					The best shots, chosen together.
				</h1>
				<p className="text-muted-foreground mx-auto w-full max-w-md text-base sm:text-lg lg:mx-0">
					Share the album from the trip or the get-together, and let everyone
					who was there swipe through it to pick the shots worth keeping.
				</p>
				<LandingAccessButton session={session} loggedOutLabel="Start picking" />
			</div>
			<SwipeMock />
		</section>
	);
}
