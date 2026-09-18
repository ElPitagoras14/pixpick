import { useDrag } from "@use-gesture/react";
import { animate } from "motion/mini";
import { forwardRef, useCallback, useImperativeHandle, useRef } from "react";
import type { PendingPhoto } from "@/features/swipe/api";
import { isSwipeAccepted } from "@/features/swipe/swipeThreshold";
import { cn } from "@/lib/utils";

export interface SwipeCardHandle {
	/** Plays the same exit a successful drag would, then reports the
	 * decision -- the button and keyboard paths call this so every path
	 * converges on one mechanism, not three (task 6.8). */
	exit: (direction: 1 | -1) => void;
}

interface SwipeCardProps {
	photo: PendingPhoto;
	/** Only the top card of the stack binds the gesture and accepts
	 * `exit()`; the ones behind it are purely decorative. */
	active: boolean;
	onDecide: (approved: boolean) => void;
	/** Opens this photo in the viewer (photo-viewer spec). Fired from the
	 * drag gesture's own tap, never from a click handler of its own
	 * (D4): two mechanisms listening to the same finger would each have
	 * their own idea of where a tap ends and a drag begins, and an
	 * eight-pixel movement would be settled by whichever reacted first. */
	onOpen: () => void;
}

// Not `type: "spring"`: the mini engine runs entirely on the browser's
// own Web Animations API and only accepts a generator *function* for
// `type`, never the string shorthand the full package understands --
// pulling in the real spring generator would drag the physics runtime
// back in, defeating the point of the reduced variant (D7). An
// easeOutBack-style cubic bezier gets the same slight overshoot on the
// rebound (D8) from a plain WAAPI-native curve instead.
const OVERSHOOT_EASE = [0.34, 1.56, 0.64, 1] as const;
const RETURN_ANIMATION = { duration: 0.35, easing: OVERSHOOT_EASE } as const;
const EXIT_ANIMATION = { duration: 0.3, easing: "ease-out" } as const;

export const SwipeCard = forwardRef<SwipeCardHandle, SwipeCardProps>(
	function SwipeCard({ photo, active, onDecide, onOpen }, ref) {
		const cardRef = useRef<HTMLDivElement>(null);

		const playExit = useCallback(
			(direction: 1 | -1) => {
				const card = cardRef.current;
				if (!card) {
					onDecide(direction > 0);
					return;
				}
				const width = card.offsetWidth || 320;
				void animate(
					card,
					{ x: direction * width * 1.6, rotate: direction * 18, opacity: 0 },
					EXIT_ANIMATION,
				).then(() => onDecide(direction > 0));
			},
			[onDecide],
		);

		useImperativeHandle(ref, () => ({ exit: playExit }), [playExit]);

		// D7: the gesture library owns detection -- direction, distance and
		// velocity, and the non-passive listener that keeps the drag from
		// also scrolling the page. While the finger moves, the transform is
		// written straight onto the element below, with no React state and
		// no animation library in between: the card has to track the finger
		// with zero interpolation, and anything in the middle reads as lag.
		const bind = useDrag(
			({ down, movement: [mx, my], velocity: [vx], last, tap }) => {
				const card = cardRef.current;
				if (!card || !active) return;
				// The same gesture already separates the two (D4): `tap` is
				// only ever true for a press that stayed inside the 5px
				// threshold below, so opening and rating can't both happen.
				if (tap) {
					onOpen();
					return;
				}
				if (down) {
					card.style.transform = `translateX(${mx}px) rotate(${mx / 18}deg)`;
					return;
				}
				if (!last) return;
				const width = card.offsetWidth || 320;
				const accepted = isSwipeAccepted({
					dx: mx,
					dy: my,
					velocityX: vx,
					cardWidth: width,
				});
				if (accepted) {
					playExit(mx > 0 ? 1 : -1);
				} else {
					void animate(card, { x: 0, rotate: 0 }, RETURN_ANIMATION);
				}
			},
			{ filterTaps: true, threshold: 5, eventOptions: { passive: false } },
		);

		return (
			<div
				ref={cardRef}
				{...(active ? bind() : {})}
				className={cn(
					// `bg-muted` is what the bands left by the fit are made of:
					// without it the card would be transparent wherever the
					// photo's shape doesn't reach its own.
					"bg-muted absolute touch-none overflow-hidden rounded-2xl shadow-xl select-none",
					// Tucked in on three sides and extended past the bottom edge
					// (task 6.7): a `scale()` centered inside the very same
					// `inset-0` box the active card fills would never actually
					// stick out past it, so nothing would read as "underneath"
					// until the top card had already moved. Insets instead of a
					// transform make the peek show up at rest, not only once it
					// starts leaving.
					active ? "inset-0" : "inset-x-3 top-3 -bottom-3 opacity-80",
				)}
				style={{ touchAction: "none" }}
			>
				{/* Fits, never fills (D7, photo-rating spec): what is being
				judged is the whole photo, so a landscape one sits inside
				the card with bands above and below rather than losing its
				sides. The card keeps its fixed 3:4 shape, which is what
				makes the drag feel the same on every photo. */}
				<img
					src={photo.ratingUrl}
					alt=""
					draggable={false}
					className="size-full object-contain"
				/>
			</div>
		);
	},
);
