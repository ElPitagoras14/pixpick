import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { config } from "@/config";

const loginSearchSchema = z.object({
	returnTo: z.string().optional(),
});

export const Route = createFileRoute("/login")({
	validateSearch: loginSearchSchema,
	component: Login,
});

function Login() {
	const { returnTo } = Route.useSearch();

	// A real, full-page navigation (not a fetch): the backend answers with a
	// redirect into the active provider's own cycle, which this SPA has no
	// part in.
	const loginUrl = new URL(
		`${config.apiBaseUrl}/auth/login`,
		window.location.origin,
	);
	if (returnTo) {
		loginUrl.searchParams.set("return_to", returnTo);
	}

	return (
		<div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
			<h1 className="text-2xl font-bold">Log in</h1>
			<p className="text-muted-foreground max-w-xs text-sm">
				Sign in to see your albums and rate photos.
			</p>
			<Button asChild size="lg" className="min-h-11 min-w-40">
				<a href={loginUrl.toString()}>Continue</a>
			</Button>
		</div>
	);
}
