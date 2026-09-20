import type { Album } from "@/features/albums/api";
import { remainingTimeLabel } from "@/features/albums/api";
import type { AlbumStats } from "@/features/gallery/api";

// Identity as a single column (album-management spec, design.md D6):
// title, description, expiry, and the participation summary, in that
// order. Receives everything already resolved (D4, D1) -- it never
// mounts a query of its own and never asks who is looking.
export function AlbumHeader({
	album,
	stats,
}: {
	album: Album;
	stats?: AlbumStats;
}) {
	return (
		<div>
			<h1 className="text-xl font-bold">{album.title}</h1>
			{album.description && (
				<p className="text-muted-foreground text-sm">{album.description}</p>
			)}
			<p className="text-muted-foreground text-xs">
				{remainingTimeLabel(album.expiresAt)}
			</p>
			{stats && (
				<p className="text-muted-foreground text-xs">
					{stats.participantCount} participant
					{stats.participantCount === 1 ? "" : "s"} · {stats.ratingCount} rating
					{stats.ratingCount === 1 ? "" : "s"}
				</p>
			)}
		</div>
	);
}
