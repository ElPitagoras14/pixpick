import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

import { ApiRequestError } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateAlbum } from "@/features/albums/api";

export const Route = createFileRoute("/_app/albums/new")({
	component: NewAlbum,
});

function NewAlbum() {
	const navigate = useNavigate();
	const createAlbum = useCreateAlbum();
	const [title, setTitle] = useState("");
	const [description, setDescription] = useState("");
	const [titleError, setTitleError] = useState<string | null>(null);

	function handleSubmit(event: FormEvent) {
		event.preventDefault();
		setTitleError(null);
		createAlbum.mutate(
			{ title, description: description || undefined },
			{
				onSuccess: (album) => {
					navigate({
						to: "/albums/$albumId",
						params: { albumId: album.id },
						search: { filter: "all" },
					});
				},
				onError: (error) => {
					// The field the server names lands on the field itself
					// (api-conventions spec), not as a generic banner.
					if (
						error instanceof ApiRequestError &&
						error.error.field === "title"
					) {
						setTitleError(error.error.message);
					}
				},
			},
		);
	}

	return (
		<div className="mx-auto max-w-sm p-6">
			{/* The header button covers mobile; desktop had no way out of
			this screen at all (design.md D on albums/new.tsx). */}
			<Link
				to="/albums"
				search={{ group: "own" }}
				className="hidden text-muted-foreground text-xs md:block"
			>
				← Albums
			</Link>
			<h1 className="mb-6 text-xl font-bold">New album</h1>
			<form onSubmit={handleSubmit} className="flex flex-col gap-4">
				<div className="flex flex-col gap-1.5">
					<Label htmlFor="title">Title</Label>
					<Input
						id="title"
						value={title}
						onChange={(event) => setTitle(event.target.value)}
						aria-invalid={titleError ? true : undefined}
						autoFocus
					/>
					{titleError && (
						<p className="text-destructive text-xs">{titleError}</p>
					)}
				</div>
				<div className="flex flex-col gap-1.5">
					<Label htmlFor="description">Description (optional)</Label>
					<Input
						id="description"
						value={description}
						onChange={(event) => setDescription(event.target.value)}
					/>
				</div>
				<Button type="submit" disabled={createAlbum.isPending}>
					{createAlbum.isPending ? "Creating…" : "Create album"}
				</Button>
			</form>
		</div>
	);
}
