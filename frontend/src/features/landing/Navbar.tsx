import type { CurrentUser } from "@/features/auth/api";
import { LandingAccessButton } from "@/features/landing/Hero";

interface NavbarProps {
	session: CurrentUser | null;
}

// Anchors into the sections below, kept in one place instead of hardcoded
// again wherever a section needs the id this points at.
const SECTION_LINKS = [
	{ href: "#how-it-works", label: "How it works" },
	{ href: "#features", label: "What you get" },
] as const;

export function Navbar({ session }: NavbarProps) {
	return (
		<header className="bg-background sticky top-0 z-10 flex items-center justify-between gap-4 border-b px-6 py-4">
			<span className="text-lg font-bold">Pixpick</span>
			<div className="flex items-center gap-6">
				<nav className="hidden items-center gap-6 sm:flex">
					{SECTION_LINKS.map((link) => (
						<a
							key={link.href}
							href={link.href}
							className="text-muted-foreground hover:text-foreground text-sm font-medium"
						>
							{link.label}
						</a>
					))}
				</nav>
				<LandingAccessButton session={session} size="default" />
			</div>
		</header>
	);
}
