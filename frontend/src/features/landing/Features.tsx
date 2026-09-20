import {
	LinkIcon,
	type LucideIcon,
	TrendingUpIcon,
	UploadCloudIcon,
	ZoomInIcon,
} from "lucide-react";

interface Feature {
	icon: LucideIcon;
	title: string;
	description: string;
}

// The four characteristics worth coming in for: sharing, upload feedback,
// stats and the viewer. The retention window is deliberately left out --
// an operational limit, not a reason to come in.
const FEATURES: Feature[] = [
	{
		icon: LinkIcon,
		title: "Join with just a link",
		description:
			"Anyone with the link can sign in and start swiping -- no invite or approval needed.",
	},
	{
		icon: UploadCloudIcon,
		title: "Live upload progress",
		description:
			"Watch each photo land as it uploads, with no guessing whether it went through.",
	},
	{
		icon: TrendingUpIcon,
		title: "Results for the owner",
		description: "See how the group voted on every photo, all in one place.",
	},
	{
		icon: ZoomInIcon,
		title: "Zoom into any shot",
		description:
			"Open a photo full-screen to check the detail before deciding.",
	},
];

export function Features() {
	return (
		<section id="features" className="bg-muted/40 px-6 py-16">
			<h2 className="text-center text-2xl font-bold sm:text-3xl">
				What you get
			</h2>
			<ul className="mx-auto mt-10 grid max-w-4xl grid-cols-1 gap-8 sm:grid-cols-2">
				{FEATURES.map((feature) => (
					<li key={feature.title} className="flex items-start gap-4">
						<span className="bg-background flex size-10 shrink-0 items-center justify-center rounded-full">
							<feature.icon className="size-5" aria-hidden="true" />
						</span>
						<div className="min-w-0">
							<h3 className="font-semibold">{feature.title}</h3>
							<p className="text-muted-foreground text-sm">
								{feature.description}
							</p>
						</div>
					</li>
				))}
			</ul>
		</section>
	);
}
