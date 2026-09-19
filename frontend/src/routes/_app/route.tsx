import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
	createFileRoute,
	Link,
	Outlet,
	redirect,
	useMatchRoute,
	useRouter,
} from "@tanstack/react-router";

import { api } from "@/api";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { sessionQueryOptions } from "@/features/auth/api";
import { BottomNav } from "@/features/navigation/BottomNav";

export const Route = createFileRoute("/_app")({
	beforeLoad: ({ context, location }) => {
		// The guard's own job: enter without a session and land back here
		// exactly, once signed in (D9, identity-provider spec). Whatever
		// happens *while* a page from this layout is already open is the
		// HTTP client's job (see api.ts's onUnauthorized), not this one's.
		if (!context.session) {
			throw redirect({ to: "/login", search: { returnTo: location.href } });
		}
	},
	component: AppLayout,
});

function useLogout() {
	const queryClient = useQueryClient();
	const router = useRouter();

	return useMutation({
		mutationFn: async () => {
			await api.post("/auth/logout");
		},
		onSuccess: () => {
			queryClient.setQueryData(sessionQueryOptions().queryKey, null);
			router.navigate({ to: "/login" });
		},
	});
}

function AppLayout() {
	const { session } = Route.useRouteContext();
	const logout = useLogout();
	const matchRoute = useMatchRoute();

	// Same pattern as isUploadView in albums/$albumId/route.tsx: one
	// useMatchRoute call here, centralized, instead of BottomNav
	// recomputing its own matches (design.md's mitigation for a future
	// third tab).
	const isHome = !!matchRoute({ to: "/home" });
	const isAlbums = !!matchRoute({ to: "/albums", fuzzy: true });
	const isSwipeDeck = !!matchRoute({ to: "/albums/$albumId/swipe" });
	const activeTab = isHome ? "home" : isAlbums ? "albums" : null;

	return (
		<div className="flex min-h-dvh flex-col">
			<header className="flex items-center justify-between gap-4 border-b p-4">
				<nav className="hidden items-center gap-4 md:flex">
					{/* The way back in from anywhere (app-entry spec): one more
					link beside the one already here, with the same active
					treatment -- two links don't make a navigation component
					(D5). */}
					<Link
						to="/home"
						className="text-sm font-semibold"
						activeProps={{ className: "underline" }}
					>
						Home
					</Link>
					<Link
						to="/albums"
						search={{ group: "own" }}
						className="text-sm font-semibold"
						activeProps={{ className: "underline" }}
					>
						Albums
					</Link>
				</nav>
				<div className="flex items-center gap-2">
					<Avatar>
						{/* The provider's own address, used as-is (D10): not
						copied, not proxied through this system. */}
						<AvatarImage
							src={session?.avatarUrl ?? undefined}
							alt=""
							referrerPolicy="no-referrer"
						/>
						<AvatarFallback>
							{(session?.name ?? session?.email ?? "?").charAt(0).toUpperCase()}
						</AvatarFallback>
					</Avatar>
					<span className="text-sm font-medium">
						{session?.name ?? session?.email ?? "Signed in"}
					</span>
				</div>
				<Button variant="outline" size="sm" onClick={() => logout.mutate()}>
					Log out
				</Button>
			</header>
			<main className="flex-1 pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-0">
				<Outlet />
			</main>
			{!isSwipeDeck && <BottomNav activeTab={activeTab} />}
		</div>
	);
}
