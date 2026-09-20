import {
	BarChart3Icon,
	FolderPlusIcon,
	HandIcon,
	type LucideIcon,
	Share2Icon,
} from "lucide-react";

interface Step {
	icon: LucideIcon;
	title: string;
	description: string;
}

// The four steps of the real flow: create an album, share it, have it
// rated, read the result.
const STEPS: Step[] = [
	{
		icon: FolderPlusIcon,
		title: "Create an album",
		description: "Start one for the trip or the get-together in a few seconds.",
	},
	{
		icon: Share2Icon,
		title: "Share the link",
		description:
			"Send it to whoever was there -- opening it and signing in is all it takes to join.",
	},
	{
		icon: HandIcon,
		title: "Everyone swipes",
		description:
			"Each person goes through the photos and picks the ones they like.",
	},
	{
		icon: BarChart3Icon,
		title: "The owner sees the result",
		description: "The shots everyone agreed on rise to the top, ready to keep.",
	},
];

export function HowItWorks() {
	return (
		<section id="how-it-works" className="px-6 py-16">
			<h2 className="text-center text-2xl font-bold sm:text-3xl">
				How it works
			</h2>
			<ol className="mx-auto mt-10 grid max-w-4xl grid-cols-1 gap-8 sm:grid-cols-2 sm:gap-10 lg:grid-cols-4">
				{STEPS.map((step, index) => (
					<li
						key={step.title}
						className="flex w-full flex-col items-center gap-3 text-center"
					>
						<span className="bg-muted flex size-12 items-center justify-center rounded-full">
							<step.icon className="size-6" aria-hidden="true" />
						</span>
						<span className="text-muted-foreground text-xs font-medium">
							Step {index + 1}
						</span>
						<h3 className="w-full font-semibold">{step.title}</h3>
						<p className="text-muted-foreground w-full text-sm">
							{step.description}
						</p>
					</li>
				))}
			</ol>
		</section>
	);
}
