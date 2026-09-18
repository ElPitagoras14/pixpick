import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

import { pendingQueryOptions } from "@/features/swipe/api";
import { SwipeDeck } from "@/features/swipe/SwipeDeck";
import {
	VIEWER_SEARCH_PARAM,
	viewerSearchSchema,
} from "@/features/viewer/searchParam";
import { useViewerNavigation } from "@/features/viewer/useViewerNavigation";

// The same param the gallery carries, on this screen's own address (D1,
// D2): the deck stays mounted underneath and the back button closes the
// viewer. The name comes from one place, not from two spellings that
// have to agree.
const swipeSearchSchema = z.object(viewerSearchSchema);

export const Route = createFileRoute("/_app/albums/$albumId/swipe")({
	validateSearch: swipeSearchSchema,
	loader: ({ context, params }) =>
		context.queryClient.ensureQueryData(pendingQueryOptions(params.albumId)),
	component: SwipePage,
});

function SwipePage() {
	const { albumId } = Route.useParams();
	const { [VIEWER_SEARCH_PARAM]: openPhotoId } = Route.useSearch();
	const { openPhoto, showPhoto, closeViewer } = useViewerNavigation();
	const { data: photos } = useSuspenseQuery(pendingQueryOptions(albumId));

	return (
		<SwipeDeck
			albumId={albumId}
			initialPhotos={photos}
			openPhotoId={openPhotoId}
			onOpenPhoto={openPhoto}
			onShowPhoto={showPhoto}
			onCloseViewer={closeViewer}
		/>
	);
}
