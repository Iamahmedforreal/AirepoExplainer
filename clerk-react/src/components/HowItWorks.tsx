import Section from "./Section";
import { Link, Parse, Index, Brain } from "./icons";
import type { ComponentType, SVGProps } from "react";

type Step = {
  n: string;
  title: string;
  desc: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
};

const steps: Step[] = [
  {
    n: "01",
    title: "Connect repository",
    desc: "Connect or upload your repository. Public, private, or local — CodeGrok ingests it.",
    Icon: Link,
  },
  {
    n: "02",
    title: "Parse to symbol graph",
    desc: "Code is parsed into structured intelligence: an AST-based symbol graph of every entity.",
    Icon: Parse,
  },
  {
    n: "03",
    title: "Index everything",
    desc: "Data is indexed for retrieval with full-text search and semantic embeddings.",
    Icon: Index,
  },
  {
    n: "04",
    title: "Ask the agent",
    desc: "The AI agent answers your questions using real code context from the graph.",
    Icon: Brain,
  },
];

export default function HowItWorks() {
  return (
    <Section
      id="how"
      label="How it works"
      title="From raw repository to answers, in four steps."
      className="bg-mist"
    >
      <ol className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((s, i) => (
          <li
            key={s.n}
            className="group relative flex flex-col bg-paper p-7 transition-colors hover:bg-mist"
          >
            <div className="mb-6 flex items-center justify-between">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-line bg-paper text-ink transition-all duration-300 group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
                <s.Icon className="h-5 w-5" />
              </span>
              <span className="font-mono text-xs text-faint">{s.n}</span>
            </div>
            <h3 className="text-lg font-bold tracking-tight">{s.title}</h3>
            <p className="mt-2.5 text-sm leading-relaxed text-muted">{s.desc}</p>
            {i < steps.length - 1 && (
              <span className="absolute -right-2 top-12 z-10 hidden h-4 w-4 items-center justify-center lg:flex">
                <span className="text-faint">→</span>
              </span>
            )}
          </li>
        ))}
      </ol>
    </Section>
  );
}
