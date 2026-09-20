import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { ImagePlusIcon } from "lucide-react";
import { type ChangeEvent, useRef } from "react";

import { Button } from "@/components/ui/button";
import {
	UploadItemCard,
	uploadOutcomeOf,
} from "@/features/photos/UploadItemCard";
import { type UploadItem, useUploadQueue } from "@/features/photos/uploadQueue";
import { accountUsageQueryOptions, formatBytes } from "@/features/quota/api";

export const Route = createFileRoute("/_app/albums/$albumId/upload")({
	loader: ({ context }) =>
		context.queryClient.ensureQueryData(accountUsageQueryOptions()),
	component: UploadView,
});

/** How the batch went, without having to count it. It sits above the list
 * and the list itself never moves: the order photos were picked in is what
 * lets someone find one among fifty, and reordering under the eyes of
 * whoever is watching costs more than a scroll. */
function summarize(items: UploadItem[]) {
	let done = 0;
	let failed = 0;
	let running = 0;
	for (const item of items) {
		const outcome = uploadOutcomeOf(item.status);
		if (outcome === "done") done += 1;
		else if (outcome === "failed") failed += 1;
		else running += 1;
	}
	return { done, failed, running };
}

function UploadView() {
	const { albumId } = Route.useParams();
	const { items, addFiles, retry } = useUploadQueue(albumId);
	const { data: usage } = useSuspenseQuery(accountUsageQueryOptions());
	const inputRef = useRef<HTMLInputElement>(null);
	const remaining = Math.max(usage.limitBytes - usage.usedBytes, 0);
	const summary = summarize(items);

	function handleFilesSelected(event: ChangeEvent<HTMLInputElement>) {
		const files = event.target.files;
		if (files && files.length > 0) {
			addFiles(Array.from(files));
		}
		// Lets picking the exact same file again fire another change event.
		event.target.value = "";
	}

	return (
		<div>
			<input
				ref={inputRef}
				type="file"
				accept="image/jpeg,image/png,image/webp"
				multiple
				className="hidden"
				onChange={handleFilesSelected}
			/>
			{/* The one thing this page exists to do, so it gets the visual
			weight: a dashed empty-state card matching the rest of the app's
			own idiom, not a plain default-sized button among others. */}
			<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
				<p className="text-muted-foreground text-sm">
					Pick one or more photos to add to this album.
				</p>
				{/* Before choosing, not after the server turns some away: the limit
				 * stops being something discovered by hitting it and becomes something
				 * seen while deciding. */}
				<p
					className={
						remaining === 0
							? "text-destructive text-sm font-medium"
							: "text-muted-foreground text-sm"
					}
				>
					{remaining === 0
						? "No space left. Delete some photos to make room."
						: `${formatBytes(remaining)} of ${formatBytes(usage.limitBytes)} free`}
				</p>
				<Button size="lg" onClick={() => inputRef.current?.click()}>
					<ImagePlusIcon />
					Choose photos
				</Button>
			</div>

			{items.length > 0 && (
				<>
					<div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
						<span className="font-medium">
							{items.length} file{items.length === 1 ? "" : "s"}
						</span>
						<span className="text-muted-foreground">
							{summary.done} uploaded
						</span>
						<span
							className={
								summary.failed > 0
									? "text-destructive"
									: "text-muted-foreground"
							}
						>
							{summary.failed} didn't finish
						</span>
						{summary.running > 0 && (
							<span className="text-muted-foreground">
								{summary.running} in progress
							</span>
						)}
					</div>
					<ul className="mt-2 flex flex-col gap-2">
						{items.map((item) => (
							<UploadItemCard
								key={item.id}
								item={item}
								onRetry={() => retry(item.id)}
							/>
						))}
					</ul>
				</>
			)}
		</div>
	);
}
