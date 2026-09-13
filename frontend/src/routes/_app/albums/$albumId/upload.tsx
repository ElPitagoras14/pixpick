import { createFileRoute, Link } from "@tanstack/react-router";
import { type ChangeEvent, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
	type UploadItemStatus,
	useUploadQueue,
} from "@/features/photos/uploadQueue";

export const Route = createFileRoute("/_app/albums/$albumId/upload")({
	component: UploadView,
});

const STATUS_LABEL: Record<UploadItemStatus, string> = {
	queued: "Waiting…",
	uploading: "Uploading…",
	confirming: "Confirming…",
	available: "Uploaded",
	pending: "Waiting for upload to finish",
	rejected: "Rejected",
	failed: "Failed",
};

function UploadView() {
	const { albumId } = Route.useParams();
	const { items, addFiles, retry } = useUploadQueue(albumId);
	const inputRef = useRef<HTMLInputElement>(null);

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
			<Link
				to="/albums/$albumId"
				params={{ albumId }}
				className="text-muted-foreground mb-4 inline-block text-xs"
			>
				← Back to album
			</Link>
			<input
				ref={inputRef}
				type="file"
				accept="image/jpeg,image/png,image/webp"
				multiple
				className="hidden"
				onChange={handleFilesSelected}
			/>
			<div>
				<Button onClick={() => inputRef.current?.click()}>Choose photos</Button>
			</div>

			{items.length > 0 && (
				<ul className="mt-6 flex flex-col gap-3">
					{items.map((item) => (
						<li key={item.id} className="flex items-center gap-3">
							<span className="flex-1 truncate text-sm">{item.file.name}</span>
							<span className="text-muted-foreground w-40 shrink-0 text-xs">
								{item.status === "uploading" ? (
									<Progress value={item.progress} />
								) : (
									(item.error ?? STATUS_LABEL[item.status])
								)}
							</span>
							{item.status === "failed" && (
								<Button
									size="sm"
									variant="outline"
									onClick={() => retry(item.id)}
								>
									Retry
								</Button>
							)}
						</li>
					))}
				</ul>
			)}
		</div>
	);
}
