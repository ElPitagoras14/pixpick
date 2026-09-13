import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { albumQueryOptions, useDeleteAlbum } from "@/features/albums/api";
import {
	albumStatsQueryOptions,
	GALLERY_FILTERS,
	type GalleryFilter,
	type GalleryPhoto,
	galleryQueryOptions,
	useSetRating,
} from "@/features/gallery/api";
import { GalleryPhotoCard } from "@/features/gallery/GalleryPhotoCard";
import { GalleryTabs } from "@/features/gallery/GalleryTabs";
import { useDeletePhoto } from "@/features/photos/api";

// A closed set of four values with a default (D9, rating-gallery spec):
// `.catch` is what turns an unrecognized filter into "all" instead of a
// validation error, so an old or hand-edited link never breaks.
const gallerySearchSchema = z.object({
	filter: z.enum(GALLERY_FILTERS).catch("all"),
});

export const Route = createFileRoute("/_app/albums/$albumId/")({
	validateSearch: gallerySearchSchema,
	loaderDeps: ({ search }) => ({ filter: search.filter }),
	loader: ({ context, params, deps }) =>
		context.queryClient.ensureQueryData(
			galleryQueryOptions(params.albumId, deps.filter),
		),
	component: AlbumGallery,
});

const EMPTY_MESSAGE: Record<GalleryFilter, string> = {
	all: "No photos yet.",
	approved: "Nothing approved yet.",
	rejected: "Nothing rejected yet.",
	unrated: "Nothing left to rate.",
};

function AlbumGallery() {
	const { albumId } = Route.useParams();
	const { filter } = Route.useSearch();
	const navigate = useNavigate();
	// Already loaded by the layout's own loader (D11): reading it here
	// again is a cache hit, never a second request.
	const { data: album } = useSuspenseQuery(albumQueryOptions(albumId));
	const { data: gallery } = useSuspenseQuery(
		galleryQueryOptions(albumId, filter),
	);
	// Requested alongside the gallery and never awaited before it (D5):
	// the grid renders as soon as the gallery arrives, and the owner's
	// counts appear on top of it once the stats arrive separately. Only
	// mounted for the owner -- for anyone else this resource is forbidden
	// (album-stats spec), so there is nothing to ask for.
	const { data: stats } = useQuery({
		...albumStatsQueryOptions(albumId),
		enabled: album.isOwner,
	});
	const statsByPhotoId = new Map(
		stats?.photos.map((photo) => [photo.photoId, photo]) ?? [],
	);

	const setRating = useSetRating(albumId);
	const deleteAlbum = useDeleteAlbum();
	const [confirmingDeleteAlbum, setConfirmingDeleteAlbum] = useState(false);
	const [photoPendingDelete, setPhotoPendingDelete] =
		useState<GalleryPhoto | null>(null);

	return (
		<div>
			<div className="mb-4 flex flex-wrap items-center justify-between gap-3">
				<div className="flex flex-col gap-1">
					<GalleryTabs
						albumId={albumId}
						active={filter}
						counts={gallery.counts}
					/>
					{/* Only exists for the owner (task 4.3, D8): never shown
					empty to anyone else, since for them this isn't a zone
					that failed to load -- it simply isn't there. */}
					{album.isOwner && stats && (
						<p className="text-muted-foreground text-xs">
							{stats.participantCount} participant
							{stats.participantCount === 1 ? "" : "s"} · {stats.ratingCount}{" "}
							rating
							{stats.ratingCount === 1 ? "" : "s"}
						</p>
					)}
				</div>
				{album.isOwner && (
					<Button
						variant="destructive"
						size="sm"
						onClick={() => setConfirmingDeleteAlbum(true)}
					>
						Delete album
					</Button>
				)}
			</div>

			{gallery.photos.length === 0 ? (
				<p className="text-muted-foreground py-12 text-center text-sm">
					{EMPTY_MESSAGE[filter]}
				</p>
			) : (
				<ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
					{gallery.photos.map((photo) => (
						<GalleryPhotoCard
							key={photo.id}
							photo={photo}
							stats={album.isOwner ? statsByPhotoId.get(photo.id) : undefined}
							onSetRating={(approved) =>
								setRating.mutate({ photoId: photo.id, approved })
							}
							onDelete={
								album.isOwner ? () => setPhotoPendingDelete(photo) : undefined
							}
						/>
					))}
				</ul>
			)}

			<Dialog
				open={confirmingDeleteAlbum}
				onOpenChange={setConfirmingDeleteAlbum}
			>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Delete this album?</DialogTitle>
						<DialogDescription>
							This deletes the album and every photo in it. This can't be
							undone.
						</DialogDescription>
					</DialogHeader>
					<DialogFooter showCloseButton>
						<Button
							variant="destructive"
							disabled={deleteAlbum.isPending}
							onClick={() =>
								deleteAlbum.mutate(albumId, {
									onSuccess: () =>
										navigate({ to: "/albums", search: { group: "own" } }),
								})
							}
						>
							Delete
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			<DeletePhotoDialog
				albumId={albumId}
				photo={photoPendingDelete}
				onOpenChange={(open) => !open && setPhotoPendingDelete(null)}
			/>
		</div>
	);
}

function DeletePhotoDialog({
	albumId,
	photo,
	onOpenChange,
}: {
	albumId: string;
	photo: GalleryPhoto | null;
	onOpenChange: (open: boolean) => void;
}) {
	const deletePhoto = useDeletePhoto(albumId);

	return (
		<Dialog open={photo !== null} onOpenChange={onOpenChange}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Delete this photo?</DialogTitle>
					<DialogDescription>This can't be undone.</DialogDescription>
				</DialogHeader>
				<DialogFooter showCloseButton>
					<Button
						variant="destructive"
						disabled={deletePhoto.isPending}
						onClick={() => {
							if (!photo) return;
							deletePhoto.mutate(
								{ albumId, photoId: photo.id },
								{ onSuccess: () => onOpenChange(false) },
							);
						}}
					>
						Delete
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
