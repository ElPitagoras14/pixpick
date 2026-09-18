import { z } from "zod";

/** Which photo is open in the viewer travels in the address, not in
 * component state (D1): the back button closes the viewer with nothing
 * to intercept, an open photo is a link, and a reload lands where it
 * left off. It is a search param on the screen's own route rather than a
 * child route (D2), so the grid or the deck underneath stays mounted.
 *
 * Two screens open the viewer, so the name is declared here once and
 * neither of them spells it out (Risks: the convention is what's
 * duplicated, and it's the one thing worth centralizing).
 */
export const VIEWER_SEARCH_PARAM = "photo";

/** The param's shape, spread into each screen's own search schema.
 * `.catch` keeps an id that no longer exists -- a stale link, a deleted
 * photo -- from turning the whole address into a validation error; the
 * viewer simply finds nothing to open and stays closed, the same
 * leniency the gallery's filter already applies (D9 in rating-gallery).
 */
export const viewerSearchSchema = {
	[VIEWER_SEARCH_PARAM]: z.string().optional().catch(undefined),
};
