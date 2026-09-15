import type { AccountUsage } from "@/features/quota/api";
import { formatBytes } from "@/features/quota/api";
import { cn } from "@/lib/utils";

/** How much of the account's storage is taken (account-quota spec). The
 * bar carries the state at a glance and the numbers carry the detail, so
 * an empty account and a full one never read the same even before the
 * caption is read. Not built on the shared `Progress` primitive: this one
 * changes color when there's no room left, which that primitive's
 * indicator doesn't expose.
 */
export function StorageMeter({ usage }: { usage: AccountUsage }) {
	const remaining = Math.max(usage.limitBytes - usage.usedBytes, 0);
	const percent =
		usage.limitBytes === 0
			? 0
			: Math.min(Math.round((usage.usedBytes / usage.limitBytes) * 100), 100);
	const full = remaining === 0;

	return (
		<div className="flex flex-col gap-1.5">
			<div className="flex items-baseline justify-between gap-3">
				<span className="text-sm font-medium">Storage</span>
				<span className="text-muted-foreground text-xs">
					{formatBytes(usage.usedBytes)} of {formatBytes(usage.limitBytes)}
				</span>
			</div>
			<div
				className="bg-muted h-2 w-full overflow-hidden rounded-full"
				role="progressbar"
				aria-label="Storage used"
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
			<p
				className={cn(
					"text-xs",
					full ? "text-destructive font-medium" : "text-muted-foreground",
				)}
			>
				{full
					? "No space left. Delete photos to make room."
					: `${formatBytes(remaining)} free`}
			</p>
		</div>
	);
}
