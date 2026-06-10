import Section from "./Section";
import { Link, Parse, Graph, Index, Brain } from "./icons";
import type { ComponentType, SVGProps } from "react";

type Step = {
  n: string;
  title: string;
  desc: string;
  items?: string[];
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
};

const steps: Step[] = [
  {
    n: "01",
    title: "Connect repository",
    desc: "Paste a GitHub URL — that's the only setup.",
    Icon: Link,
  },
  {
    n: "02",
    title: "Analyze",
    desc: "CodeGrok parses every file and extracts:",
    items: [
      "Classes",
      "Functions",
      "Methods",
      "Imports",
      "Call relationships",
      "Dependencies",
    ],
    Icon: Parse,
  },
  {
    n: "03",
    title: "Build architecture graph",
    desc: "Generate an interactive graph showing:",
    items: [
      "Service-to-service relationships",
      "Function calls",
      "Import chains",
      "File dependencies",
    ],
    Icon: Graph,
  },
  {
    n: "04",
    title: "Generate knowledge base",
    desc: "Create summaries and embeddings for the entire repository.",
    Icon: Index,
  },
  {
    n: "05",
    title: "Chat with your code",
    desc: "Ask questions in plain English and get answers grounded in real code.",
    Icon: Brain,
  },
];

export default function HowItWorks() {
  return (
    <Section
      id="how"
      label="How it works"
      title="From raw repository to answers, in five steps."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s, i) => (
          <div
            key={s.n}
            className={`group flex flex-col rounded-2xl border bg-paper p-7 transition-all duration-300 hover:-translate-y-1 ${
              i === 0
                ? "card-highlight border-ink bg-mist"
                : "border-line hover:border-ink-soft hover:bg-mist"
            }`}
          >
            <div className="mb-6 flex items-center justify-between">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-line bg-paper text-ink transition-all duration-300 group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
                <s.Icon className="h-5 w-5" />
              </span>
              <span className="font-mono text-xs text-faint">{s.n}</span>
            </div>
            <h3 className="text-lg font-bold tracking-tight">{s.title}</h3>
            <p className="mt-2.5 text-sm leading-relaxed text-muted">{s.desc}</p>
            {s.items && (
              <ul className="mt-4 flex flex-wrap gap-2">
                {s.items.map((item) => (
                  <li
                    key={item}
                    className="rounded-full border border-line bg-mist px-3 py-1 font-mono text-xs text-ink"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}
