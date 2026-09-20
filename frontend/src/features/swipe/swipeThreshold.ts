// The calibrated starting points -- editing these is a constants change,
// never a change of the rule, which only requires that the threshold
// combine distance with velocity, not how much of each.

/** The distance path: the drag alone qualifies once it crosses this
 * fraction of the card's own width. */
export const DISTANCE_THRESHOLD_RATIO = 0.3;

/** The fast path's velocity floor, in pixels per millisecond. */
export const VELOCITY_THRESHOLD = 0.5;

/** The fast path's own distance floor. Without it, a tiny, quick graze
 * would already clear the velocity floor on its own -- velocity alone
 * can't tell a deliberate flick from an accidental brush. */
export const FAST_PATH_MIN_DISTANCE_RATIO = 0.1;

/** Below this many pixels of movement, nothing is a gesture yet -- a tap
 * shouldn't be mistaken for the start of one. */
export const MIN_GESTURE_PIXELS = 8;

export interface SwipeAttempt {
	/** Horizontal movement in pixels; sign gives the direction. */
	dx: number;
	/** Vertical movement in pixels. */
	dy: number;
	/** Horizontal speed at release, in pixels per millisecond, unsigned. */
	velocityX: number;
	/** The card's own width, in pixels -- the threshold is relative to
	 * this, not an absolute pixel count, so the gesture feels the same on
	 * any screen. */
	cardWidth: number;
}

/** Whether a drag counts as a rating gesture: either path accepts, but only
 * when the movement is horizontal, and only past the minimum that
 * separates a gesture from a tap. */
export function isSwipeAccepted(attempt: SwipeAttempt): boolean {
	const { dx, dy, velocityX, cardWidth } = attempt;
	const absDx = Math.abs(dx);
	const absDy = Math.abs(dy);

	if (absDx < MIN_GESTURE_PIXELS && absDy < MIN_GESTURE_PIXELS) return false;
	// Dominance, not "no vertical movement at all": scrolling the page
	// vertically SHALL NOT emit a rating, even if it drifts a little
	// sideways.
	if (absDx <= absDy) return false;

	const passesDistance = absDx >= cardWidth * DISTANCE_THRESHOLD_RATIO;
	const passesFastPath =
		velocityX >= VELOCITY_THRESHOLD &&
		absDx >= cardWidth * FAST_PATH_MIN_DISTANCE_RATIO;
	return passesDistance || passesFastPath;
}
