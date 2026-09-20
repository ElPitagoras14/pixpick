import { useGesture } from "@use-gesture/react";
import { ChevronLeftIcon, ChevronRightIcon, XIcon } from "lucide-react";
import {
	useCallback,
	useEffect,
	useLayoutEffect,
	useRef,
	useState,
} from "react";

import { cn } from "@/lib/utils";

/** What the viewer needs of a photo, and nothing else: the address of the
 * largest variant. Both screens that open it already carry this on the
 * photos they were listing, so the viewer never asks for anything of its
 * own. */
export interface ViewerPhoto {
	id: string;
	viewerUrl: string;
}

interface PhotoViewerProps {
	/** The set to move through, in the order it is being looked at: the
	 * gallery's filtered list, or the rating sequence. The viewer moves
	 * inside whatever it was handed and knows nothing about filters. */
	photos: ViewerPhoto[];
	openPhotoId: string;
	/** Opens another photo of the set -- the caller writes it to the
	 * address, the same way it wrote the one that opened the viewer. */
	onOpenPhoto: (photoId: string) => void;
	onClose: () => void;
}

// What the zoom is capped at until the image reports its real size.
// Deliberately conservative: letting it open wide for the first second
// and then snapping back is worse than starting tight.
const FALLBACK_MAX_SCALE = 2;
const DOUBLE_TAP_MS = 300;
// How much of the wheel's travel a doubling of the scale takes.
const WHEEL_SCALE_DIVISOR = 500;

interface Transform {
	scale: number;
	x: number;
	y: number;
}

const IDENTITY: Transform = { scale: 1, x: 0, y: 0 };

/** Where a gesture's originating event landed. The gesture library types
 * its event as any of the four input kinds and only the pointer-shaped
 * ones carry a position; without one, the zoom falls back to the frame's
 * own center. */
function pointOf(event: Event): [number | undefined, number | undefined] {
	if ("clientX" in event && "clientY" in event) {
		return [event.clientX as number, event.clientY as number];
	}
	return [undefined, undefined];
}

/** Looking at one photo in detail: it shows the largest variant -- never
 * the original, which this product does not serve -- fitted whole inside
 * the screen whatever its shape, zoomable and pannable up to the point
 * where that variant runs out of pixels of its own, and steppable through
 * the set it was given.
 *
 * Zoom and pan are written straight onto the element, not held in React
 * state: the image has to track the fingers with no interpolation, and a
 * re-render per frame reads as lag -- the same reasoning the rating card's
 * drag already follows. */
export function PhotoViewer({
	photos,
	openPhotoId,
	onOpenPhoto,
	onClose,
}: PhotoViewerProps) {
	const index = photos.findIndex((photo) => photo.id === openPhotoId);
	const photo = index === -1 ? undefined : photos[index];

	const frameRef = useRef<HTMLDivElement>(null);
	const imageRef = useRef<HTMLImageElement>(null);
	const transformRef = useRef<Transform>(IDENTITY);
	const maxScaleRef = useRef(FALLBACK_MAX_SCALE);
	const lastTapRef = useRef(0);
	// Which photo the transform above currently belongs to: a re-render
	// for any other reason must not throw away a zoom halfway through a
	// gesture, only an actual change of photo does.
	const shownPhotoRef = useRef<string | null>(null);
	// Mirrors only whether the photo is currently magnified, which is the
	// one thing the rest of the UI reacts to -- not the scale itself,
	// which changes every frame.
	const [zoomed, setZoomed] = useState(false);

	const previous = index > 0 ? photos[index - 1] : undefined;
	const next =
		index >= 0 && index < photos.length - 1 ? photos[index + 1] : undefined;

	const paint = useCallback(() => {
		const image = imageRef.current;
		if (!image) return;
		const { scale, x, y } = transformRef.current;
		image.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
	}, []);

	/** Keeps the photo's own edges from leaving the frame: at a given
	 * scale it can travel exactly as far as it overflows, and no
	 * further. At scale 1 there is no overflow, so it stays centered. */
	const clamp = useCallback((next: Transform): Transform => {
		const image = imageRef.current;
		const frame = frameRef.current;
		if (!image || !frame) return next;
		// `offsetWidth` is the laid-out size, which the transform above
		// does not affect -- so this stays the untransformed baseline.
		const overflowX = Math.max(
			0,
			(image.offsetWidth * next.scale - frame.clientWidth) / 2,
		);
		const overflowY = Math.max(
			0,
			(image.offsetHeight * next.scale - frame.clientHeight) / 2,
		);
		return {
			scale: next.scale,
			x: Math.min(overflowX, Math.max(-overflowX, next.x)),
			y: Math.min(overflowY, Math.max(-overflowY, next.y)),
		};
	}, []);

	const applyTransform = useCallback(
		(next: Transform) => {
			transformRef.current = clamp(next);
			paint();
			setZoomed(transformRef.current.scale > 1.01);
		},
		[clamp, paint],
	);

	const reset = useCallback(() => {
		applyTransform(IDENTITY);
	}, [applyTransform]);

	/** Scales around a point, so what is under the fingers -- or under
	 * the pointer -- stays under them instead of sliding away. */
	const zoomAround = useCallback(
		(nextScale: number, clientX?: number, clientY?: number) => {
			const frame = frameRef.current;
			if (!frame) return;
			const current = transformRef.current;
			const bounded = Math.min(maxScaleRef.current, Math.max(1, nextScale));
			const rect = frame.getBoundingClientRect();
			const centerX = rect.left + rect.width / 2;
			const centerY = rect.top + rect.height / 2;
			const anchorX = (clientX ?? centerX) - centerX;
			const anchorY = (clientY ?? centerY) - centerY;
			const ratio = bounded / current.scale;
			applyTransform({
				scale: bounded,
				x: anchorX - ratio * (anchorX - current.x),
				y: anchorY - ratio * (anchorY - current.y),
			});
		},
		[applyTransform],
	);

	/** The ceiling, derived rather than written down: the variant's own pixels
	 * against the size it is being shown at. Recomputed whenever either side
	 * of that comparison can have changed -- a new photo, or a resized window
	 * -- so it never has to be kept in sync by hand. */
	const measureMaxScale = useCallback(() => {
		const image = imageRef.current;
		if (!image?.naturalWidth || !image.offsetWidth) return;
		maxScaleRef.current = Math.max(1, image.naturalWidth / image.offsetWidth);
		if (transformRef.current.scale > maxScaleRef.current) {
			applyTransform({ ...transformRef.current, scale: maxScaleRef.current });
		} else {
			// The window may have shrunk under a panned photo, which moves
			// where its edges are allowed to be.
			applyTransform(transformRef.current);
		}
	}, [applyTransform]);

	// Back to the whole photo on every change of photo: the next one must not
	// arrive magnified on a region nobody chose. Runs before paint, so it is
	// never briefly visible zoomed.
	useLayoutEffect(() => {
		if (shownPhotoRef.current === openPhotoId) return;
		shownPhotoRef.current = openPhotoId;
		transformRef.current = IDENTITY;
		maxScaleRef.current = FALLBACK_MAX_SCALE;
		setZoomed(false);
		paint();
	}, [openPhotoId, paint]);

	useEffect(() => {
		function onResize() {
			measureMaxScale();
		}
		window.addEventListener("resize", onResize);
		return () => window.removeEventListener("resize", onResize);
	}, [measureMaxScale]);

	// Nothing here locks the page's own scroll. Hiding the body's overflow is
	// the usual way to keep what is underneath still, and it throws the scroll
	// position away -- which is exactly what closing has to give back. The
	// overlay covers the screen and takes the touches itself (`touch-none`
	// below), so there is nothing left for the page behind to react to.

	const goTo = useCallback(
		(target: ViewerPhoto | undefined) => {
			if (target) onOpenPhoto(target.id);
		},
		[onOpenPhoto],
	);

	useEffect(() => {
		function onKeyDown(event: KeyboardEvent) {
			if (event.key === "Escape") onClose();
			if (event.key === "ArrowLeft") goTo(previous);
			if (event.key === "ArrowRight") goTo(next);
		}
		window.addEventListener("keydown", onKeyDown);
		return () => window.removeEventListener("keydown", onKeyDown);
	}, [onClose, goTo, previous, next]);

	// One gesture object for the three ways of zooming and the pan, all from
	// the library the rating card already uses -- no new dependency, and no
	// second mechanism listening to the same finger.
	useGesture(
		{
			onDrag: ({ down, movement: [mx, my], memo, tap, event }) => {
				if (tap) {
					const now = Date.now();
					// Double tap is the one-step toggle: out to the whole photo, or in to
					// the ceiling, never a gradual climb back. Detected off the same
					// gesture that already tells a tap from a drag, so there is one
					// criterion and not two.
					if (now - lastTapRef.current < DOUBLE_TAP_MS) {
						lastTapRef.current = 0;
						if (transformRef.current.scale > 1.01) reset();
						else {
							const [pointX, pointY] = pointOf(event);
							zoomAround(maxScaleRef.current, pointX, pointY);
						}
					} else {
						lastTapRef.current = now;
					}
					return memo;
				}
				// Panning only means something once the photo is bigger than
				// the frame; below that there is nowhere to go.
				if (transformRef.current.scale <= 1.01) return memo;
				const origin = (memo as { x: number; y: number } | undefined) ?? {
					x: transformRef.current.x,
					y: transformRef.current.y,
				};
				applyTransform({
					scale: transformRef.current.scale,
					x: origin.x + mx,
					y: origin.y + my,
				});
				return down ? origin : undefined;
			},
			onPinch: ({ offset: [scale], origin: [originX, originY] }) => {
				zoomAround(scale, originX, originY);
			},
			onWheel: ({ delta: [, dy], event }) => {
				// The wheel zooms the photo and nothing else: without this the same
				// turn would also scroll whatever is behind the overlay.
				event.preventDefault();
				const factor = 2 ** (-dy / WHEEL_SCALE_DIVISOR);
				zoomAround(
					transformRef.current.scale * factor,
					event.clientX,
					event.clientY,
				);
			},
		},
		{
			// Bound to the frame itself rather than spread as props, which
			// is the only way `passive: false` below actually reaches the
			// listener: React registers `wheel` passively at the root of
			// the app, and a passive listener's `preventDefault()` does
			// nothing but log a warning -- the turn of the wheel would zoom
			// the photo and scroll the grid behind the overlay at once.
			// Bound this way the library attaches natively, on an effect
			// that runs after every render, so the frame is picked up
			// whenever it mounts.
			target: frameRef,
			drag: { filterTaps: true, threshold: 5 },
			// Starts from where the photo already is, so a second pinch
			// continues instead of jumping back to 1.
			pinch: {
				from: () => [transformRef.current.scale, 0],
				pinchOnWheel: false,
			},
			eventOptions: { passive: false },
		},
	);

	if (!photo) return null;

	return (
		<div
			// `touch-none` over the whole overlay, not just the photo: a pinch or a
			// drag anywhere on it is the viewer's, so the page underneath neither
			// scrolls nor zooms. Taps still reach the buttons -- this only takes the
			// browser's own scroll and zoom gestures away.
			className="bg-background fixed inset-0 z-50 flex touch-none flex-col"
			style={{ touchAction: "none" }}
			role="dialog"
			aria-modal="true"
			aria-label="Photo viewer"
		>
			<div className="flex items-center justify-between gap-2 p-3">
				<span className="text-muted-foreground text-xs tabular-nums">
					{index + 1} / {photos.length}
				</span>
				<div className="flex items-center gap-2">
					{zoomed && (
						<button
							type="button"
							onClick={reset}
							className="text-muted-foreground hover:text-foreground rounded-md px-2 py-1 text-xs"
						>
							Fit to screen
						</button>
					)}
					<button
						type="button"
						onClick={onClose}
						aria-label="Close viewer"
						className="hover:bg-muted rounded-md p-1.5"
					>
						<XIcon className="size-5" />
					</button>
				</div>
			</div>

			<div
				ref={frameRef}
				// `touch-none` is what keeps a pinch on the photo from zooming the page
				// behind it instead: the browser hands the gesture over rather than
				// claiming it.
				className="relative flex flex-1 touch-none items-center justify-center overflow-hidden"
				style={{ touchAction: "none" }}
			>
				<img
					ref={imageRef}
					// The largest variant of the catalog, never the file as it was
					// uploaded.
					src={photo.viewerUrl}
					alt=""
					draggable={false}
					onLoad={measureMaxScale}
					// `max-*` with no width of its own: the element's own box
					// ends up exactly the size of the photo drawn inside it,
					// which is what makes the pan bounds above the photo's
					// real edges -- and what shows it whole, undistorted,
					// whatever its shape.
					className="max-h-full max-w-full origin-center object-contain select-none"
				/>
			</div>

			<div className="flex items-center justify-center gap-8 p-4">
				<button
					type="button"
					onClick={() => goTo(previous)}
					disabled={!previous}
					aria-label="Previous photo"
					className={cn(
						"hover:bg-muted rounded-full p-2",
						!previous && "pointer-events-none opacity-30",
					)}
				>
					<ChevronLeftIcon className="size-6" />
				</button>
				<button
					type="button"
					onClick={() => goTo(next)}
					disabled={!next}
					aria-label="Next photo"
					className={cn(
						"hover:bg-muted rounded-full p-2",
						!next && "pointer-events-none opacity-30",
					)}
				>
					<ChevronRightIcon className="size-6" />
				</button>
			</div>
		</div>
	);
}
