import Section from "./Section";
import { Brain, Graph, Trace, Quote, Parse, Bolt } from "./icons";
import type { ComponentType, SVGProps } from "react";

type Feature = {
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  title: string;
  desc: string;
};

const features: Feature[] = [
  {
    Icon: Brain,
    title: "Repository intelligence",
    desc: "AI-generated understanding of every file, module, and service.",
  },
  {
    Icon: Graph,
    title: "Architecture graph",
    desc: "Visualize how your code connects across the entire repository.",
  },
  {
    Icon: Trace,
    title: "Dependency mapping",
    desc: "Track imports, function calls, and service interactions.",
  },
  {
    Icon: Quote,
    title: "AI code chat",
    desc: "Ask questions about any repository in plain English.",
  },
  {
    Icon: Parse,
    title: "Smart summaries",
    desc: "Generate explanations for files, classes, and functions.",
  },
  {
    Icon: Bolt,
    title: "Faster onboarding",
    desc: "Help new developers become productive immediately.",
  },
];

export default function Features() {
  return (
    <Section
      id="features"
      label="What it does"
      title="Everything you need to read a codebase fast."
      intro="CodeGrok turns raw source into structured, queryable intelligence — so you spend minutes understanding what used to take days."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f, i) => {
          const highlight = i === 0;
          return (
            <div
              key={f.title}
              className={`group flex flex-col items-center rounded-2xl border bg-paper p-8 text-center transition-all duration-300 hover:-translate-y-1 ${
                highlight
                  ? "card-highlight border-ink bg-mist"
                  : "border-line hover:border-ink-soft hover:bg-mist"
              }`}
            >
              <span className="text-ink transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:scale-110">
                <f.Icon className="h-7 w-7" />
              </span>
              <h3 className="mt-5 text-lg font-bold tracking-tight">
                {f.title}
              </h3>
              <p className="mt-2.5 max-w-xs text-sm leading-relaxed text-muted">
                {f.desc}
              </p>
            </div>
          );
        })}
      </div>
    </Section>
  );
}
