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
import type { CurrentUser } from "@/features/auth/api";
import { sessionQueryOptions } from "@/features/auth/api";
import {
	BackButton,
	type BackDestination,
} from "@/features/navigation/BackButton";
import { BottomNav } from "@/features/navigation/BottomNav";

export const Route = createFileRoute("/_app")({
	beforeLoad: ({ context, location }) => {
		// The guard's own job: enter without a session and land back here
		// exactly, once signed in. Whatever happens *while* a page from this
		// layout is already open is the HTTP client's job (see api.ts's
		// onUnauthorized), not this one's.
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
	// useMatchRoute call here instead of BottomNav recomputing its own
	// matches, which is what a third tab would otherwise multiply.
	const isHome = !!matchRoute({ to: "/home" });
	const isAlbums = !!matchRoute({ to: "/albums", fuzzy: true });
	const activeTab = isHome ? "home" : isAlbums ? "albums" : null;

	// Static before dynamic, most specific before least (D on ordering):
	// "/albums/new" can never be mistaken for an albumId, and the two
	// subviews of an album resolve before the album view itself.
	const isNewAlbum = matchRoute({ to: "/albums/new" });
	const albumUploadMatch = matchRoute({ to: "/albums/$albumId/upload" });
	const albumSwipeMatch = matchRoute({ to: "/albums/$albumId/swipe" });
	const albumViewMatch = matchRoute({ to: "/albums/$albumId" });
	const isSwipeDeck = !!albumSwipeMatch;

	const albumsListDestination: BackDestination = {
		to: "/albums",
		search: { group: "own" },
	};
	const backDestination: BackDestination = isNewAlbum
		? albumsListDestination
		: albumUploadMatch
			? {
					to: "/albums/$albumId",
					params: { albumId: albumUploadMatch.albumId },
					search: { filter: "all" },
				}
			: albumSwipeMatch
				? {
						to: "/albums/$albumId",
						params: { albumId: albumSwipeMatch.albumId },
						search: { filter: "all" },
					}
				: albumViewMatch
					? albumsListDestination
					: null;

	return (
		<div className="flex min-h-dvh flex-col">
			<header className="flex items-center justify-between gap-4 border-b px-4 py-2">
				<div className="flex items-center gap-4">
					{/* Below md, this is the one thing on the leading edge: who's
					signed in on a main screen, or the way out of a subview --
					never both, so it never ends up floating in the middle of an
					otherwise-empty side the way a same-width avatar and back
					slot did before. Fixed at the button's own 44px footprint
					(not the avatar's smaller one) so the header doesn't grow
					or shrink when the two swap. */}
					<div className="flex size-11 items-center justify-center md:hidden">
						{backDestination ? (
							<BackButton destination={backDestination} />
						) : (
							<UserAvatar session={session} />
						)}
					</div>
					<nav className="hidden items-center gap-4 md:flex">
						{/* The way back in from anywhere: one more link beside the one
						 * already here, with the same active treatment -- two links don't
						 * make a navigation component. */}
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
				</div>
				<div className="flex items-center gap-4">
					<div className="hidden items-center gap-2 md:flex">
						<UserAvatar session={session} />
						<span className="text-sm font-medium">
							{session?.name ?? session?.email ?? "Signed in"}
						</span>
					</div>
					<Button variant="outline" size="sm" onClick={() => logout.mutate()}>
						Log out
					</Button>
				</div>
			</header>
			<main className="flex-1 pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-0">
				<Outlet />
			</main>
			{!isSwipeDeck && <BottomNav activeTab={activeTab} />}
		</div>
	);
}

function UserAvatar({ session }: { session: CurrentUser | null }) {
	return (
		<Avatar>
			{/* The provider's own address, used as-is: not copied, not proxied
			 * through this system. */}
			<AvatarImage
				src={session?.avatarUrl ?? undefined}
				alt=""
				referrerPolicy="no-referrer"
			/>
			<AvatarFallback>
				{(session?.name ?? session?.email ?? "?").charAt(0).toUpperCase()}
			</AvatarFallback>
		</Avatar>
	);
}
