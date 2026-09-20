import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";

export type BackDestination =
	| { to: "/albums"; search: { group: "own" } }
	| {
			to: "/albums/$albumId";
			params: { albumId: string };
			search: { filter: "all" };
	  }
	| null;

// Mirrors BottomNav's activeTab: the match logic lives in AppLayout, this
// component only picks which literal <Link> to render from the single
// destination it is handed, and stays silent when there is none.
export function BackButton({ destination }: { destination: BackDestination }) {
	if (!destination) {
		return null;
	}

	return (
		<Button asChild variant="ghost" size="icon" className="size-11 md:hidden">
			{destination.to === "/albums" ? (
				<Link to="/albums" search={destination.search} aria-label="Back">
					<ArrowLeft />
				</Link>
			) : (
				<Link
					to="/albums/$albumId"
					params={destination.params}
					search={destination.search}
					aria-label="Back"
				>
					<ArrowLeft />
				</Link>
			)}
		</Button>
	);
}
