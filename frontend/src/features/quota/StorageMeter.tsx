import { formatBytes } from "@/features/quota/api";
import { cn } from "@/lib/utils";

/** The account's own scope: a total against a limit, in bytes. */
export interface BytesUsage {
	usedBytes: number;
	limitBytes: number;
}

/** The instance's own scope: only the percentage occupied -- the
 * installation's real capacity never reaches the frontend, so there is no
 * total or limit here to show. */
export interface PercentUsage {
	usedPercent: number;
}

function isPercentUsage(
	usage: BytesUsage | PercentUsage,
): usage is PercentUsage {
	return "usedPercent" in usage;
}

interface StorageMeterProps {
	usage: BytesUsage | PercentUsage;
	/** What this meter names: the account's own meter and the instance's share
	 * the same bar and full-color change, and this is the one thing that
	 * tells them apart without reading the numbers. */
	label?: string;
	/** What to say when there's no room left. The account's own default points
	 * at what the person can do about it; the instance's is not this
	 * component's to assume, since what's missing there may not be this
	 * person's to free. */
	fullMessage?: string;
}

/** How much of a storage scope is taken -- one account's, or the whole
 * instance's. The bar carries the state at a glance, so an empty scope and
 * a full one never read the same even before any caption is read. Not built
 * on the shared `Progress` primitive: this one changes color when there's no
 * room left, which that primitive's indicator doesn't expose.
 *
 * The account's own usage shows the real numbers ("120 of 150 MB", "30 MB
 * free"); the instance's shows only the percentage the backend already
 * reduced it to -- there are no bytes here to fall back to. */
export function StorageMeter({
	usage,
	label = "Storage",
	fullMessage = "No space left. Delete photos to make room.",
}: StorageMeterProps) {
	const percentOnly = isPercentUsage(usage);
	const percent = percentOnly
		? Math.min(Math.max(Math.round(usage.usedPercent), 0), 100)
		: usage.limitBytes === 0
			? 0
			: Math.min(Math.round((usage.usedBytes / usage.limitBytes) * 100), 100);
	const full = percentOnly
		? percent >= 100
		: usage.limitBytes - usage.usedBytes <= 0;
	// No line at all when there's room left and all there is to say is a
	// percentage already shown above: the account's own usage always has
	// something to add -- how much is free -- that the instance's bytes-free
	// reduced-to-a-percentage never carries.
	const belowText = full
		? fullMessage
		: percentOnly
			? null
			: `${formatBytes(usage.limitBytes - usage.usedBytes)} free`;

	return (
		<div className="flex flex-col gap-1.5">
			<div className="flex items-baseline justify-between gap-3">
				<span className="text-sm font-medium">{label}</span>
				<span className="text-muted-foreground text-xs">
					{percentOnly
						? `${percent}%`
						: `${formatBytes(usage.usedBytes)} of ${formatBytes(usage.limitBytes)}`}
				</span>
			</div>
			<div
				className="bg-muted h-2 w-full overflow-hidden rounded-full"
				role="progressbar"
				aria-label={`${label} used`}
				aria-valuenow={percent}
				aria-valuemin={0}
				aria-valuemax={100}
			>
				<div
					className={cn(
						"h-full transition-all",
						full ? "bg-destructive" : "bg-primary",
					)}
					style={{ width: `${percent}%` }}
				/>
			</div>
			{belowText !== null && (
				<p
					className={cn(
						"text-xs",
						full ? "text-destructive font-medium" : "text-muted-foreground",
					)}
				>
					{belowText}
				</p>
			)}
		</div>
	);
}
