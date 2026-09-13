import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { albumsQueryOptions } from "@/features/albums/api";

export const Route = createFileRoute("/_app/albums/")({
	loader: ({ context }) =>
		context.queryClient.ensureQueryData(albumsQueryOptions()),
	component: AlbumsList,
});

function AlbumsList() {
	const { data: albums } = useSuspenseQuery(albumsQueryOptions());

	return (
		<div className="mx-auto max-w-3xl p-6">
			<div className="mb-6 flex items-center justify-between">
				<h1 className="text-xl font-bold">Albums</h1>
				<Button asChild size="sm">
					<Link to="/albums/new">New album</Link>
				</Button>
			</div>

			{albums.length === 0 ? (
				<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
					<p className="text-muted-foreground text-sm">
						You don't have any albums yet.
					</p>
					<Button asChild size="sm">
						<Link to="/albums/new">Create your first album</Link>
					</Button>
				</div>
			) : (
				<ul className="grid grid-cols-2 gap-4 sm:grid-cols-3">
					{albums.map((album) => (
						<li key={album.id}>
							<Link
								to="/albums/$albumId"
								params={{ albumId: album.id }}
								className="group block overflow-hidden rounded-xl border"
							>
								<div className="bg-muted aspect-square w-full overflow-hidden">
									{album.coverUrl ? (
										<img
											src={album.coverUrl}
											alt=""
											className="size-full object-cover transition-transform group-hover:scale-105"
										/>
									) : (
										<div className="text-muted-foreground flex size-full items-center justify-center text-xs">
											No photos yet
										</div>
									)}
								</div>
								<div className="p-2">
									<p className="truncate text-sm font-medium">{album.title}</p>
									<p className="text-muted-foreground text-xs">
										{album.photoCount} photo{album.photoCount === 1 ? "" : "s"}
									</p>
								</div>
							</Link>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}
