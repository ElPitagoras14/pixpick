import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Trash2Icon } from "lucide-react";
import { useState } from "react";

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
	type Photo,
	photosQueryOptions,
	useDeletePhoto,
} from "@/features/photos/api";

export const Route = createFileRoute("/_app/albums/$albumId/")({
	loader: ({ context, params }) =>
		context.queryClient.ensureQueryData(photosQueryOptions(params.albumId)),
	component: AlbumGrid,
});

function AlbumGrid() {
	const { albumId } = Route.useParams();
	const navigate = useNavigate();
	// Already loaded by the layout's own loader (D11): reading it here again
	// is a cache hit, never a second request.
	const { data: album } = useSuspenseQuery(albumQueryOptions(albumId));
	const { data: photos } = useSuspenseQuery(photosQueryOptions(albumId));
	const deleteAlbum = useDeleteAlbum();
	const [confirmingDeleteAlbum, setConfirmingDeleteAlbum] = useState(false);
	const [photoPendingDelete, setPhotoPendingDelete] = useState<Photo | null>(
		null,
	);

	return (
		<div>
			{album.isOwner && (
				<div className="mb-4 flex justify-end">
					<Button
						variant="destructive"
						size="sm"
						onClick={() => setConfirmingDeleteAlbum(true)}
					>
						Delete album
					</Button>
				</div>
			)}

			{photos.length === 0 ? (
				<p className="text-muted-foreground py-12 text-center text-sm">
					No photos yet.
				</p>
			) : (
				<ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
					{photos.map((photo) => (
						<li key={photo.id} className="group relative">
							{/* The declared dimensions reserve the aspect ratio before
							the thumbnail loads (task 6.4) -- purely a layout hint
							(photo-upload spec), never a decision anything depends on. */}
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
							{album.isOwner && (
								<button
									type="button"
									onClick={() => setPhotoPendingDelete(photo)}
									className="bg-background/80 absolute top-1.5 right-1.5 rounded-md p-1 opacity-0 transition-opacity group-hover:opacity-100"
								>
									<Trash2Icon className="size-4" />
									<span className="sr-only">Delete photo</span>
								</button>
							)}
						</li>
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
									onSuccess: () => navigate({ to: "/albums" }),
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
	photo: Photo | null;
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
