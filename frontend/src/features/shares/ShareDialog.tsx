import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
	shareLinkQueryOptions,
	useRegenerateShareLink,
	useRevokeShareLink,
} from "@/features/shares/api";

// Not itemized in this change's original tasks -- added during
// implementation, because without it there is no way from the interface
// itself to reach the link this whole change exists to open (see
// tasks.md 5.4). Owner-only: a non-owner member never gets this button.
export function ShareDialog({ albumId }: { albumId: string }) {
	const [open, setOpen] = useState(false);

	return (
		<>
			<Button
				className="h-11 md:h-7"
				variant="outline"
				size="sm"
				onClick={() => setOpen(true)}
			>
				Share
			</Button>
			<Dialog open={open} onOpenChange={setOpen}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Share this album</DialogTitle>
						<DialogDescription>
							Anyone with this link can view the album and rate its photos.
						</DialogDescription>
					</DialogHeader>
					{open && (
						<Suspense
							fallback={
								<p className="text-muted-foreground text-sm">Loading link…</p>
							}
						>
							<ShareLinkPanel albumId={albumId} />
						</Suspense>
					)}
					<DialogFooter showCloseButton />
				</DialogContent>
			</Dialog>
		</>
	);
}

function ShareLinkPanel({ albumId }: { albumId: string }) {
	// Idempotent GET (task 2.1, task 5.4): opening this dialog never itself
	// changes what's shared -- it fetches the album's current live link,
	// generating the first one only if it has none yet.
	const { data: link } = useSuspenseQuery(shareLinkQueryOptions(albumId));
	const regenerate = useRegenerateShareLink(albumId);
	const revoke = useRevokeShareLink(albumId);
	const [copied, setCopied] = useState(false);

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(link.url);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch {
			// Clipboard access can be denied or unavailable; the link is
			// still selectable in the input either way.
		}
	}

	return (
		<div className="flex flex-col gap-3">
			<div className="flex gap-2">
				<Input
					readOnly
					value={link.url}
					onFocus={(event) => event.target.select()}
				/>
				<Button type="button" onClick={copyLink}>
					{copied ? "Copied" : "Copy"}
				</Button>
			</div>
			<div className="flex gap-2">
				<Button
					type="button"
					variant="outline"
					size="sm"
					disabled={regenerate.isPending}
					onClick={() => regenerate.mutate()}
				>
					{regenerate.isPending ? "Regenerating…" : "Regenerate link"}
				</Button>
				<Button
					type="button"
					variant="destructive"
					size="sm"
					disabled={revoke.isPending}
					onClick={() => revoke.mutate()}
				>
					Revoke
				</Button>
			</div>
		</div>
	);
}
