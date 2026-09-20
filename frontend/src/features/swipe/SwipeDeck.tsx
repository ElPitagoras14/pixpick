import { Link } from "@tanstack/react-router";
import { HeartIcon, XIcon } from "lucide-react";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import type { PendingPhoto } from "@/features/swipe/api";
import { SwipeCard, type SwipeCardHandle } from "@/features/swipe/SwipeCard";
import { useSwipeDeck } from "@/features/swipe/useSwipeDeck";
import { PhotoViewer } from "@/features/viewer/PhotoViewer";

interface SwipeDeckProps {
	albumId: string;
	initialPhotos: PendingPhoto[];
	/** Which photo the viewer has open, straight off the address -- absent
	 * means it is closed. */
	openPhotoId?: string;
	onOpenPhoto: (photoId: string) => void;
	onShowPhoto: (photoId: string) => void;
	onCloseViewer: () => void;
}

export function SwipeDeck({
	albumId,
	initialPhotos,
	openPhotoId,
	onOpenPhoto,
	onShowPhoto,
	onCloseViewer,
}: SwipeDeckProps) {
	const {
		remaining,
		current,
		next,
		finished,
		decide,
		failed,
		dismissFailure,
		retryFailure,
	} = useSwipeDeck(albumId, initialPhotos);
	const activeCardRef = useRef<SwipeCardHandle>(null);
	const viewerOpen = openPhotoId !== undefined;

	// The keyboard is a full path, not an afterthought: a whole sequence has
	// to be completable without ever touching the gesture or the pointer.
	//
	// Silent while the viewer is open: there the arrows step between photos,
	// and a key that both moved the viewer and rated the photo underneath
	// would rate one nobody decided on.
	useEffect(() => {
		if (finished || viewerOpen) return;
		function onKeyDown(event: KeyboardEvent) {
			if (event.key === "ArrowRight") activeCardRef.current?.exit(1);
			if (event.key === "ArrowLeft") activeCardRef.current?.exit(-1);
		}
		window.addEventListener("keydown", onKeyDown);
		return () => window.removeEventListener("keydown", onKeyDown);
	}, [finished, viewerOpen]);

	if (finished) {
		return (
			<div className="flex min-h-[70vh] flex-col items-center justify-center gap-4 p-6 text-center">
				<h2 className="text-xl font-bold">All caught up</h2>
				<p className="text-muted-foreground max-w-xs text-sm">
					There's nothing left for you to rate in this album right now.
				</p>
				<Button asChild size="sm">
					<Link
						to="/albums/$albumId"
						params={{ albumId }}
						search={{ filter: "all" }}
					>
						View album
					</Link>
				</Button>
			</div>
		);
	}

	return (
		<div className="mx-auto flex max-w-sm flex-col items-center gap-6 p-6">
			<div className="relative aspect-3/4 w-full">
				{next && (
					<SwipeCard
						key={next.id}
						photo={next}
						active={false}
						onDecide={() => {}}
						onOpen={() => {}}
					/>
				)}
				{current && (
					<SwipeCard
						key={current.id}
						ref={activeCardRef}
						photo={current}
						active
						onDecide={decide}
						onOpen={() => onOpenPhoto(current.id)}
					/>
				)}
			</div>

			<div className="flex items-center gap-6">
				<Button
					variant="outline"
					size="icon-lg"
					onClick={() => activeCardRef.current?.exit(-1)}
					aria-label="Reject this photo"
				>
					<XIcon />
				</Button>
				<Button
					size="icon-lg"
					onClick={() => activeCardRef.current?.exit(1)}
					aria-label="Approve this photo"
				>
					<HeartIcon />
				</Button>
			</div>

			{failed.length > 0 && (
				<div className="flex w-full flex-col gap-2">
					{failed.map((item) => (
						<div
							key={item.photoId}
							className="border-destructive/30 bg-destructive/10 flex items-center justify-between gap-3 rounded-lg border p-2 text-sm"
						>
							<span>
								Couldn't save {item.approved ? "an approval" : "a rejection"}.
							</span>
							<div className="flex gap-2">
								<Button
									size="xs"
									variant="outline"
									onClick={() => retryFailure(item.photoId)}
								>
									Retry
								</Button>
								<Button
									size="xs"
									variant="ghost"
									onClick={() => dismissFailure(item.photoId)}
								>
									Dismiss
								</Button>
							</div>
						</div>
					))}
				</div>
			)}

			{/* The set it moves through is what is left of the sequence, in its own
			 * order. Closing leaves the deck exactly as it was: nothing here was
			 * unmounted, and no decision was emitted. */}
			{openPhotoId && (
				<PhotoViewer
					photos={remaining}
					openPhotoId={openPhotoId}
					onOpenPhoto={onShowPhoto}
					onClose={onCloseViewer}
				/>
			)}
		</div>
	);
}
