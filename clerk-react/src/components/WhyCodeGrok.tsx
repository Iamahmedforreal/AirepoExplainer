import Section from "./Section";
import { Bolt, Search, Trace, Layers } from "./icons";
import type { ComponentType, SVGProps } from "react";

type Reason = {
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  title: string;
  desc: string;
};

const reasons: Reason[] = [
  {
    Icon: Bolt,
    title: "Understand large codebases instantly",
    desc: "Onboard to unfamiliar repos in minutes instead of days. Ask, don't dig.",
  },
  {
    Icon: Search,
    title: "Replace manual code searching",
    desc: "Stop grepping across files. Get direct, contextual answers from the graph.",
  },
  {
    Icon: Trace,
    title: "AI-powered dependency tracing",
    desc: "Follow imports and call chains automatically to see real impact.",
  },
  {
    Icon: Layers,
    title: "Built for solo developers",
    desc: "Understand any project you work on by yourself — from a small script to a large app.",
  },
];

export default function WhyCodeGrok() {
  return (
    <Section
      id="why"
      label="Why CodeGrok"
      title="Stop searching. Start understanding."
      intro="CodeGrok turns your codebase into a structured knowledge graph so you can understand architecture, flows, and dependencies faster."
    >
      <div className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2">
        {reasons.map((r, i) => (
          <div
            key={r.title}
            className="group relative bg-paper p-8 transition-colors hover:bg-mist"
          >
            <span className="absolute right-7 top-7 font-mono text-xs text-faint">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-line text-ink transition-all duration-300 group-hover:-translate-y-1 group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
              <r.Icon className="h-6 w-6" />
            </span>
            <h3 className="mt-6 text-xl font-bold tracking-tight">{r.title}</h3>
            <p className="mt-2.5 max-w-md text-sm leading-relaxed text-muted">
              {r.desc}
            </p>
          </div>
        ))}
      </div>
    </Section>
  );
}
