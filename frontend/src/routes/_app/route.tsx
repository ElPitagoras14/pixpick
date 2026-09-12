import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
	createFileRoute,
	Outlet,
	redirect,
	useRouter,
} from "@tanstack/react-router";

import { api } from "@/api";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { sessionQueryOptions } from "@/features/auth/api";

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

	return (
		<div className="flex min-h-dvh flex-col">
			<header className="flex items-center justify-between gap-4 border-b p-4">
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
			<main className="flex-1">
				<Outlet />
			</main>
		</div>
	);
}
