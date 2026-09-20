import { useNavigate, useRouter } from "@tanstack/react-router";
import { useCallback, useRef } from "react";

import { VIEWER_SEARCH_PARAM } from "@/features/viewer/searchParam";

/** Moving the viewer's own param around the address it already sits on.
 * Both screens that open the viewer do it identically, so the three moves
 * live here once instead of being spelled out twice.
 *
 * `resetScroll: false` on every one of them: the router sends each
 * navigation back to the top of the page, and none of these is a change of
 * screen -- it is the same grid, or the same deck, with something drawn
 * over it. */
export function useViewerNavigation() {
	const navigate = useNavigate();
	const router = useRouter();
	// Whether this screen is the one that pushed the viewer's entry.
	// Arriving straight at a link with the param already on it pushed
	// nothing, and there is no entry of ours to go back to.
	const pushedHere = useRef(false);

	const setParam = useCallback(
		(photoId: string | undefined, replace: boolean) =>
			navigate({
				to: ".",
				search: (prev: Record<string, unknown>) => ({
					...prev,
					[VIEWER_SEARCH_PARAM]: photoId,
				}),
				replace,
				resetScroll: false,
			}),
		[navigate],
	);

	/** Opening pushes an entry, so the browser's own back button closes the
	 * viewer with nothing to intercept. */
	const openPhoto = useCallback(
		(photoId: string) => {
			pushedHere.current = true;
			void setParam(photoId, false);
		},
		[setParam],
	);

	/** Stepping replaces that one entry rather than stacking one per
	 * photo: otherwise leaving a long visit would mean pressing back once
	 * for every photo that was looked at. */
	const showPhoto = useCallback(
		(photoId: string) => {
			void setParam(photoId, true);
		},
		[setParam],
	);

	/** Closing is a step back in history, not a new address: that is what
	 * hands back the filter and the exact scroll position without this code
	 * saving or restoring either of them. Only a viewer that was opened from
	 * a link, with no entry of ours behind it, closes by dropping the param
	 * instead. */
	const closeViewer = useCallback(() => {
		if (pushedHere.current) {
			pushedHere.current = false;
			router.history.back();
			return;
		}
		void setParam(undefined, true);
	}, [router, setParam]);

	return { openPhoto, showPhoto, closeViewer };
}
