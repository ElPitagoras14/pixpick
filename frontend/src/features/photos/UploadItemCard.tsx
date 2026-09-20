import {
	CheckCircle2Icon,
	CircleAlertIcon,
	ClockIcon,
	LoaderCircleIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type {
	UploadItem,
	UploadItemStatus,
} from "@/features/photos/uploadQueue";
import { formatBytes } from "@/features/quota/api";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<UploadItemStatus, string> = {
	queued: "Waiting…",
	uploading: "Uploading…",
	confirming: "Confirming…",
	available: "Uploaded",
	pending: "Waiting for upload to finish",
	rejected: "Rejected",
	denied: "Not enough room",
	busy: "Server busy",
	failed: "Failed",
};

/** The four outcomes a person scans for, which the queue's statuses
 * collapse into. The group is what reads at a glance -- icon and color, no
 * text -- while each status keeps its own wording below it for the detail.
 * "busy" is its own outcome, not "failed": nothing about the file was
 * wrong, the instance just couldn't take it yet, so it reads as transient
 * instead of as a defect -- and, unlike "failed", the same retry is
 * expected to work once the wait is over instead of only maybe helping. */
export type UploadOutcome = "running" | "done" | "busy" | "failed";

const STATUS_OUTCOME: Record<UploadItemStatus, UploadOutcome> = {
	queued: "running",
	uploading: "running",
	confirming: "running",
	available: "done",
	// Confirmed and not there: the upload was interrupted, so this is a
	// file that didn't finish, never one still on its way.
	pending: "failed",
	rejected: "failed",
	denied: "failed",
	busy: "busy",
	failed: "failed",
};

export function uploadOutcomeOf(status: UploadItemStatus): UploadOutcome {
	return STATUS_OUTCOME[status];
}

const OUTCOME_ICON = {
	running: LoaderCircleIcon,
	done: CheckCircle2Icon,
	busy: ClockIcon,
	failed: CircleAlertIcon,
} as const;

const OUTCOME_ICON_CLASS: Record<UploadOutcome, string> = {
	running: "text-muted-foreground animate-spin",
	done: "text-primary",
	busy: "text-amber-600 dark:text-amber-500",
	failed: "text-destructive",
};

const OUTCOME_TEXT_CLASS: Record<UploadOutcome, string> = {
	running: "text-muted-foreground",
	done: "text-muted-foreground",
	busy: "text-amber-600 dark:text-amber-500",
	failed: "text-destructive",
};

// The browser's own truncation eats the end of a name, which is exactly
// where the numbering a camera produces differs -- IMG_4821 from IMG_4822.
// Splitting the name and letting only the head shrink keeps the tail on
// screen at any width, with nothing to measure.
const NAME_TAIL_LENGTH = 8;

function splitName(name: string): { head: string; tail: string } {
	if (name.length <= NAME_TAIL_LENGTH) return { head: name, tail: "" };
	return {
		head: name.slice(0, name.length - NAME_TAIL_LENGTH),
		tail: name.slice(-NAME_TAIL_LENGTH),
	};
}

interface UploadItemCardProps {
	item: UploadItem;
	onRetry: () => void;
}

/** One file of the batch: the card turns a queue item into what is shown,
 * so the route keeps only the file picker and the list and no branch of
 * this lives there -- the same reason the gallery grid and the rating deck
 * each have a card of their own.
 *
 * Its identity sits on the first line and the bar gets the whole width
 * below it, which is what gives the reason for a failure room to be read
 * in full, across two lines if it needs them. */
export function UploadItemCard({ item, onRetry }: UploadItemCardProps) {
	const outcome = STATUS_OUTCOME[item.status];
	const { head, tail } = splitName(item.file.name);
	// A transfer that fell over, a file that wasn't granted room, and one the
	// instance couldn't take yet are the ones a person can do something about
	// by asking again (retrying "busy" is expected to succeed once the wait is
	// over, not just maybe help).
	const canRetry =
		item.status === "failed" ||
		item.status === "denied" ||
		item.status === "busy";
	const Icon = OUTCOME_ICON[outcome];

	return (
		<li className="flex flex-col gap-2 rounded-lg border p-3">
			<div className="flex items-baseline gap-2">
				<p className="flex min-w-0 flex-1 text-sm" title={item.file.name}>
					<span className="truncate">{head}</span>
					<span className="shrink-0">{tail}</span>
				</p>
				<span className="text-muted-foreground shrink-0 text-xs">
					{formatBytes(item.file.size)}
				</span>
			</div>

			{outcome === "running" && <Progress value={item.progress} />}

			<div className="flex items-start gap-2">
				<Icon
					aria-hidden
					className={cn("size-4 shrink-0", OUTCOME_ICON_CLASS[outcome])}
				/>
				{/* Whatever the queue has to say, whole: a reason carrying the
				number someone needs in order to act -- how much room is left
				-- is useless cut in half. */}
				<p className={cn("flex-1 text-xs", OUTCOME_TEXT_CLASS[outcome])}>
					{item.error ?? STATUS_LABEL[item.status]}
				</p>
				{canRetry && (
					<Button
						size="sm"
						variant="outline"
						className="-my-1 shrink-0"
						onClick={onRetry}
					>
						Retry
					</Button>
				)}
			</div>
		</li>
	);
}
