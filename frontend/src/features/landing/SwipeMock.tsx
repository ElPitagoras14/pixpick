// Decorative only (design.md): a plain CSS @keyframes loop, not the real
// gesture engine (`@use-gesture` + `motion/mini` in features/swipe). No
// pointer listener is attached anywhere in this tree, so nothing here can
// be mistaken for a control that responds to a drag.
export function SwipeMock() {
	return (
		<div
			aria-hidden="true"
			className="relative mx-auto aspect-3/4 w-48 sm:w-56"
		>
			<div className="bg-muted absolute inset-x-3 top-3 -bottom-3 rounded-2xl opacity-60" />
			<div
				className="bg-primary/15 border-primary/20 animate-swipe-mock motion-reduce:animate-none pointer-events-none absolute inset-0 rounded-2xl border"
				style={{ willChange: "transform, opacity" }}
			/>
		</div>
	);
}
