import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/login")({ component: Login });

function Login() {
	return (
		<div className="flex min-h-dvh flex-col items-center justify-center gap-2 p-6 text-center">
			<h1 className="text-2xl font-bold">Log in</h1>
			<p className="text-muted-foreground text-sm">
				Sign-in is not implemented yet.
			</p>
		</div>
	);
}
