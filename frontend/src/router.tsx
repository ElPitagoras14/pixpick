import { QueryClient } from "@tanstack/react-query";
import { createRouter as createTanStackRouter } from "@tanstack/react-router";

import { onUnauthorized } from "@/api";
import { sessionQueryOptions } from "@/features/auth/api";

import { routeTree } from "@/routeTree.gen";

export function getRouter() {
	const queryClient = new QueryClient();

	// Injected into the router's own context (not just React context) so route
	// loaders can reach it via `beforeLoad`/`loader`, not only components via
	// hooks.
	const router = createTanStackRouter({
		routeTree,
		context: { queryClient },
		scrollRestoration: true,
		defaultPreload: "intent",
		defaultPreloadStaleTime: 0,
	});

	// The HTTP client's own concern is only "this request came back
	// unauthorized" -- whether that means a live session just died, as opposed
	// to the unremarkable shape of an anonymous request, is decided here by
	// checking what the app currently believes.
	onUnauthorized(() => {
		const sessionQueryKey = sessionQueryOptions().queryKey;
		if (queryClient.getQueryData(sessionQueryKey)) {
			queryClient.setQueryData(sessionQueryKey, null);
			router.navigate({ to: "/login" });
		}
	});

	return router;
}

declare module "@tanstack/react-router" {
	interface Register {
		router: ReturnType<typeof getRouter>;
	}
}
