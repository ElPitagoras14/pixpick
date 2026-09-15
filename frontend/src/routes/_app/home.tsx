import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { accountUsageQueryOptions } from "@/features/quota/api";
import { StorageMeter } from "@/features/quota/StorageMeter";

// The `_app` layout's first real child (deferred from add-local-environment:
// a pathless layout with no children resolves to the same route as the
// top-level index). What it shows so far is how much of the account's
// storage is taken (account-quota spec) -- the one number a person needs
// before deciding whether to add more or free some.
export const Route = createFileRoute("/_app/home")({
	loader: ({ context }) =>
		context.queryClient.ensureQueryData(accountUsageQueryOptions()),
	component: Home,
});

function Home() {
	const { data: usage } = useSuspenseQuery(accountUsageQueryOptions());

	return (
		<div className="mx-auto max-w-3xl p-6">
			<StorageMeter usage={usage} />
		</div>
	);
}
