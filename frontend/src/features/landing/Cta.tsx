import type { CurrentUser } from "@/features/auth/api";
import { LandingAccessButton } from "@/features/landing/Hero";

interface CtaProps {
	session: CurrentUser | null;
}

export function Cta({ session }: CtaProps) {
	return (
		<section className="flex flex-col items-center gap-4 px-6 py-20 text-center">
			<h2 className="text-2xl font-bold sm:text-3xl">
				Ready to pick the keepers?
			</h2>
			<p className="text-muted-foreground w-full max-w-md text-sm sm:text-base">
				Start an album for your next trip or get-together, and let everyone who
				was there help choose.
			</p>
			<LandingAccessButton session={session} loggedOutLabel="Start picking" />
		</section>
	);
}
