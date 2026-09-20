import { HeartIcon, Trash2Icon, XIcon } from "lucide-react";

import type { GalleryPhoto, PhotoStats } from "@/features/gallery/api";
import { formatBytes } from "@/features/quota/api";
import { cn } from "@/lib/utils";

interface GalleryPhotoCardProps {
	photo: GalleryPhoto;
	onSetRating: (approved: boolean) => void;
	/** Opens this photo in the viewer. The rating controls sit on top of the
	 * image and stop the tap themselves, so rating from the grid never opens
	 * anything. */
	onOpen: () => void;
	stats?: PhotoStats;
	sizeBytes?: number;
	onDelete?: () => void;
}

/** One photo of the gallery grid: the thumbnail, a rating indicator in one
 * corner, and -- only when the caller passes `stats` (the owner) -- the
 * aggregate counts as a compact strip below the image, never sharing a
 * corner with the indicator above, which the two would otherwise compete
 * for.
 *
 * What the photo occupies joins that same strip rather than starting one
 * of its own: it is owner-only for the same reason the counts are, and it
 * arrives from its own resource, so it is present or absent independently
 * of them. */
export function GalleryPhotoCard({
	photo,
	onSetRating,
	onOpen,
	stats,
	sizeBytes,
	onDelete,
}: GalleryPhotoCardProps) {
	return (
		<li className="flex flex-col gap-1">
			<div className="group relative">
				{/* Square, never the photo's own ratio: the thumbnail the backend
				 * serves is already a deliberate square crop, and a container of any
				 * other shape cropped that square a second time. With both square the
				 * fill crop has nothing left to remove, and the grid comes out even.
				 * Seeing a photo uncropped is what the viewer is for. */}
				<button
					type="button"
					onClick={onOpen}
					aria-label="Open this photo"
					className="bg-muted aspect-square w-full overflow-hidden rounded-lg"
				>
					<img
						src={photo.thumbnailUrl}
						alt=""
						loading="lazy"
						className="size-full object-cover"
					/>
				</button>

				{/* The rating indicator: one small widget in a corner with three
				 * visible states -- neither button lit up is "not rated yet", and it
				 * never reads like a rejection. Tapping either button is how a rating
				 * changes from here. */}
				<div className="bg-background/80 absolute top-1.5 right-1.5 flex gap-0.5 rounded-full p-0.5">
					<button
						type="button"
						aria-label="Reject this photo"
						aria-pressed={photo.rating === "rejected"}
						onClick={() => onSetRating(false)}
						className={cn(
							"flex size-6 items-center justify-center rounded-full transition-colors",
							photo.rating === "rejected"
								? "bg-destructive text-destructive-foreground"
								: "text-muted-foreground hover:bg-muted",
						)}
					>
						<XIcon className="size-3.5" />
					</button>
					<button
						type="button"
						aria-label="Approve this photo"
						aria-pressed={photo.rating === "approved"}
						onClick={() => onSetRating(true)}
						className={cn(
							"flex size-6 items-center justify-center rounded-full transition-colors",
							photo.rating === "approved"
								? "bg-primary text-primary-foreground"
								: "text-muted-foreground hover:bg-muted",
						)}
					>
						<HeartIcon className="size-3.5" />
					</button>
				</div>

				{onDelete && (
					<button
						type="button"
						onClick={onDelete}
						className="bg-background/80 absolute top-1.5 left-1.5 rounded-md p-1 opacity-0 transition-opacity group-hover:opacity-100"
					>
						<Trash2Icon className="size-4" />
						<span className="sr-only">Delete photo</span>
					</button>
				)}
			</div>

			{(stats || sizeBytes !== undefined) && (
				<p className="text-muted-foreground flex justify-center gap-3 text-xs">
					{stats && <span>{stats.approvedCount} approved</span>}
					{stats && <span>{stats.rejectedCount} rejected</span>}
					{sizeBytes !== undefined && <span>{formatBytes(sizeBytes)}</span>}
				</p>
			)}
		</li>
	);
}
