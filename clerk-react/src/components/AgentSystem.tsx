import Section from "./Section";
import { Layers, Graph, Check } from "./icons";
// Canonical agent config — source of truth lives in /.agents
import skillRaw from "../../../.agents/skills/codegrok-agent/skill.md?raw";

const principles = [
  {
    Icon: Layers,
    title: "Config-driven",
    desc: "An internal skill.md defines the agent's capabilities and guardrails.",
  },
  {
    Icon: Graph,
    title: "Graph-grounded",
    desc: "Reasoning always runs over structured code data, never vibes.",
  },
  {
    Icon: Check,
    title: "Precise by rule",
    desc: "Prefers call-graph analysis over guessing. Technical but simple.",
  },
];

export default function AgentSystem() {
  return (
    <Section
      id="agent"
      label="Agent system"
      title={
        <>
          Powered by an internal{" "}
          <span className="font-mono text-[0.85em]">skill.md</span>
        </>
      }
      intro="CodeGrok runs on an agent configuration file. It declares exactly how the agent thinks, what it can do, and the rules it must follow."
    >
      <div className="grid items-start gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <SkillFile content={skillRaw} />

        <div className="space-y-4">
          {principles.map((p) => (
            <div
              key={p.title}
              className="group flex gap-4 rounded-2xl border border-line bg-paper p-5 transition-colors hover:border-ink-soft"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-line text-ink transition-colors group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
                <p.Icon className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-base font-bold tracking-tight">{p.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  {p.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

function SkillFile({ content }: { content: string }) {
  const lines = content.replace(/\r\n/g, "\n").trimEnd().split("\n");

  return (
    <div className="overflow-hidden rounded-2xl border border-ink bg-ink text-paper shadow-[0_40px_80px_-50px_rgba(0,0,0,0.7)]">
      <div className="flex items-center justify-between border-b border-paper/15 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-paper/30" />
          <span className="h-2.5 w-2.5 rounded-full bg-paper/20" />
          <span className="h-2.5 w-2.5 rounded-full bg-paper/10" />
        </div>
        <span className="font-mono text-xs text-paper/50">
          /agent/skill.md
        </span>
      </div>

      <pre className="overflow-x-auto p-5 font-mono text-[0.82rem] leading-7 sm:p-6">
        <code className="block">
          {lines.map((line, i) => (
            <span key={i} className="grid grid-cols-[2.2rem_1fr] gap-2">
              <span className="select-none text-right text-paper/25">
                {i + 1}
              </span>
              <span>{renderLine(line)}</span>
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}

function renderLine(line: string) {
  if (line.trim() === "") return <span>&nbsp;</span>;
  // markdown heading
  if (line.startsWith("#")) {
    return <span className="font-semibold text-paper">{line}</span>;
  }
  // section headers like "Capabilities:" / "Rules:"
  if (/^[A-Za-z].*:\s*$/.test(line)) {
    return <span className="font-semibold text-paper">{line}</span>;
  }
  // bullet list items
  if (line.trimStart().startsWith("- ")) {
    const indent = line.length - line.trimStart().length;
    return (
      <span style={{ paddingLeft: `${indent * 0.5}rem` }}>
        <span className="text-paper/40">- </span>
        <span className="text-paper/85">{line.trimStart().slice(2)}</span>
      </span>
    );
  }
  return <span className="text-paper/70">{line}</span>;
}
