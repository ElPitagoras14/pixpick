import { Link } from "@tanstack/react-router";

import {
	GALLERY_FILTERS,
	type GalleryCounts,
	type GalleryFilter,
} from "@/features/gallery/api";
import { cn } from "@/lib/utils";

const LABELS: Record<GalleryFilter, string> = {
	all: "All",
	approved: "Approved",
	rejected: "Rejected",
	unrated: "To rate",
};

function countFor(filter: GalleryFilter, counts: GalleryCounts): number {
	return filter === "all" ? counts.total : counts[filter];
}

interface GalleryTabsProps {
	albumId: string;
	active: GalleryFilter;
	counts: GalleryCounts;
}

/** The gallery's four filters (rating-gallery spec), each carrying its
 * own count straight from the response that already came with the grid
 * (D2, task 3.2) -- switching tabs never fires a request just to learn
 * how many photos are in it. The filter lives in the address (D9), so
 * this is a set of links, not buttons that call `setState`.
 */
export function GalleryTabs({ albumId, active, counts }: GalleryTabsProps) {
	return (
		<div className="flex gap-1 overflow-x-auto">
			{GALLERY_FILTERS.map((filter) => (
				<Link
					key={filter}
					to="/albums/$albumId"
					params={{ albumId }}
					search={{ filter }}
					className={cn(
						"shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
						active === filter
							? "bg-primary text-primary-foreground"
							: "text-muted-foreground hover:bg-muted",
					)}
				>
					{LABELS[filter]}{" "}
					<span className={active === filter ? "opacity-80" : "opacity-60"}>
						{countFor(filter, counts)}
					</span>
				</Link>
			))}
		</div>
	);
}
