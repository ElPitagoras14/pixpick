import { HeartIcon, Trash2Icon, XIcon } from "lucide-react";

import type { GalleryPhoto, PhotoStats } from "@/features/gallery/api";
import { cn } from "@/lib/utils";

interface GalleryPhotoCardProps {
	photo: GalleryPhoto;
	onSetRating: (approved: boolean) => void;
	stats?: PhotoStats;
	onDelete?: () => void;
}

/** One photo of the gallery grid (rating-gallery spec): the thumbnail, a
 * rating indicator in one corner, and -- only when the caller passes
 * `stats` (the owner) -- the aggregate counts as a compact strip below
 * the image, never sharing a corner with the indicator above (Risks:
 * the two would otherwise compete for the same corner).
 */
export function GalleryPhotoCard({
	photo,
	onSetRating,
	stats,
	onDelete,
}: GalleryPhotoCardProps) {
	return (
		<li className="flex flex-col gap-1">
			<div className="group relative">
				<div
					className="bg-muted overflow-hidden rounded-lg"
					style={{
						aspectRatio:
							photo.width && photo.height
								? `${photo.width} / ${photo.height}`
								: "1 / 1",
					}}
				>
					<img
						src={photo.thumbnailUrl}
						alt=""
						loading="lazy"
						className="size-full object-cover"
					/>
				</div>

				{/* The rating indicator (task 3.3): one small widget in a
				corner with three visible states -- neither button lit up is
				"not rated yet", and it never reads like a rejection. Tapping
				either button is how a rating changes from here (D6). */}
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

			{stats && (
				<p className="text-muted-foreground flex justify-center gap-3 text-xs">
					<span>{stats.approvedCount} approved</span>
					<span>{stats.rejectedCount} rejected</span>
				</p>
			)}
		</li>
	);
}
