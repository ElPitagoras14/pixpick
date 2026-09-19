import { Link } from "@tanstack/react-router";
import { Home, Images, Plus } from "lucide-react";

import { cn } from "@/lib/utils";

type ActiveTab = "home" | "albums" | null;

// Active-tab detection lives in AppLayout (single useMatchRoute call for the
// whole layout), not here, so a future third tab doesn't need its own copy.
export function BottomNav({ activeTab }: { activeTab: ActiveTab }) {
	return (
		<nav className="fixed inset-x-0 bottom-0 z-10 flex h-16 items-center justify-around border-t bg-background md:hidden">
			<Link
				to="/home"
				className={cn(
					"flex flex-col items-center gap-0.5 text-xs font-medium",
					activeTab === "home" ? "text-foreground" : "text-muted-foreground",
				)}
			>
				<Home className="size-5" />
				Home
			</Link>
			<Link
				to="/albums/new"
				className="-translate-y-4 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg"
				aria-label="Create album"
			>
				<Plus className="size-6" />
			</Link>
			<Link
				to="/albums"
				search={{ group: "own" }}
				className={cn(
					"flex flex-col items-center gap-0.5 text-xs font-medium",
					activeTab === "albums" ? "text-foreground" : "text-muted-foreground",
				)}
			>
				<Images className="size-5" />
				Albums
			</Link>
		</nav>
	);
}
