import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { pendingQueryOptions } from "@/features/swipe/api";
import { SwipeDeck } from "@/features/swipe/SwipeDeck";

export const Route = createFileRoute("/_app/albums/$albumId/swipe")({
	loader: ({ context, params }) =>
		context.queryClient.ensureQueryData(pendingQueryOptions(params.albumId)),
	component: SwipePage,
});

function SwipePage() {
	const { albumId } = Route.useParams();
	const { data: photos } = useSuspenseQuery(pendingQueryOptions(albumId));

	return <SwipeDeck albumId={albumId} initialPhotos={photos} />;
}
