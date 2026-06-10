import Section from "./Section";
import { Quote, Arrow } from "./icons";

const questions = [
  {
    q: "How does authentication work in this project?",
    tag: "flow tracing",
  },
  {
    q: "What breaks if I change this function?",
    tag: "impact analysis",
  },
  {
    q: "Where is this API used?",
    tag: "usage lookup",
  },
  {
    q: "Explain this module step by step",
    tag: "walkthrough",
  },
];

const marquee = [
  "find unused exports",
  "trace this error",
  "map the data flow",
  "list all callers",
  "summarize this package",
  "why is this slow?",
  "what depends on utils?",
  "explain the build step",
];

export default function ExampleQuestions() {
  return (
    <Section
      id="examples"
      label="Example questions"
      title="Ask in plain English. Get engineering answers."
      className="accent-panel bg-ink text-paper [&_h2]:text-paper [&_.mono-label]:!text-paper/50"
    >
      <div className="grid gap-px overflow-hidden rounded-2xl border border-paper/15 bg-paper/15 sm:grid-cols-2">
        {questions.map((item) => (
          <div
            key={item.q}
            className="group flex items-start justify-between gap-4 bg-ink p-7 transition-colors hover:bg-ink-soft"
          >
            <div className="flex gap-4">
              <Quote className="mt-0.5 h-5 w-5 shrink-0 text-paper/40" />
              <div>
                <p className="text-lg font-medium tracking-tight text-paper">
                  {item.q}
                </p>
                <span className="mono-label !text-paper/40 mt-2 inline-block">
                  {item.tag}
                </span>
              </div>
            </div>
            <Arrow className="mt-1 h-5 w-5 shrink-0 text-paper/30 transition-all duration-200 group-hover:translate-x-1 group-hover:text-paper" />
          </div>
        ))}
      </div>

      {/* scrolling strip of more prompts */}
      <div className="relative mt-6 overflow-hidden rounded-xl border border-paper/15 py-4 [mask-image:linear-gradient(to_right,transparent,#000_12%,#000_88%,transparent)]">
        <div className="flex w-max animate-marquee gap-3 pr-3">
          {[...marquee, ...marquee].map((m, i) => (
            <span
              key={i}
              className="whitespace-nowrap rounded-full border border-paper/15 px-4 py-1.5 font-mono text-xs text-paper/60"
            >
              {m}
            </span>
          ))}
        </div>
      </div>
    </Section>
  );
}
