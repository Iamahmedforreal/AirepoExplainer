import Section from "./Section";
import { Bolt, Trace, Layers, Github, Brain, Index } from "./icons";
import type { ComponentType, SVGProps } from "react";

type Persona = {
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  who: string;
  desc: string;
};

const personas: Persona[] = [
  {
    Icon: Bolt,
    who: "New team members",
    desc: "Understand an unfamiliar codebase quickly.",
  },
  {
    Icon: Trace,
    who: "Software engineers",
    desc: "Trace how features work across multiple services and files.",
  },
  {
    Icon: Layers,
    who: "Engineering managers",
    desc: "Get high-level architectural understanding without reading code.",
  },
  {
    Icon: Github,
    who: "Open source contributors",
    desc: "Learn large repositories before making contributions.",
  },
  {
    Icon: Brain,
    who: "AI engineers",
    desc: "Generate a structured knowledge graph for better repository reasoning.",
  },
  {
    Icon: Index,
    who: "Students",
    desc: "Learn how real-world software systems are organized.",
  },
];

export default function Audience() {
  return (
    <Section
      id="who"
      label="Who is it for"
      title="Built for anyone who needs to read code, not just write it."
    >
      <div className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
        {personas.map((p) => (
          <div
            key={p.who}
            className="group flex flex-col bg-paper p-7 transition-colors hover:bg-mist"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-line text-ink transition-colors group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
                <p.Icon className="h-5 w-5" />
              </span>
              <h3 className="text-base font-bold tracking-tight">{p.who}</h3>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">{p.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
