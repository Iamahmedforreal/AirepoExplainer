import Section from "./Section";

const extracted = [
  { k: "functions", d: "Every function & method, with signatures and scope." },
  { k: "classes", d: "Types, classes and their members across the repo." },
  { k: "imports", d: "Module dependencies and resolution paths." },
  { k: "call relationships", d: "Who calls what — a complete call graph." },
];

const questions = [
  "Where is this function used?",
  "Why does this module break?",
  "How does auth flow work?",
];

export default function WhatIs() {
  return (
    <Section
      id="what"
      label="What is CodeGrok"
      title="Understand your own codebase."
      intro="CodeGrok is a tool that helps you understand your code. Give it a repository URL and it reads the source, then turns it into a clear map of how everything connects."
    >
      <div className="grid gap-6 lg:grid-cols-2">
        {/* extracted structured data */}
        <div className="rounded-2xl border border-line bg-paper p-7 transition-colors hover:border-ink-soft">
          <div className="mono-label mb-6">Extracts structured data</div>
          <ul className="divide-y divide-line">
            {extracted.map((item) => (
              <li
                key={item.k}
                className="group flex items-baseline gap-4 py-3.5 first:pt-0 last:pb-0"
              >
                <span className="min-w-[8.5rem] font-mono text-sm text-ink">
                  {item.k}
                </span>
                <span className="text-sm text-muted">{item.d}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* ask questions */}
        <div className="accent-panel relative overflow-hidden rounded-2xl border border-ink bg-ink p-7 text-paper">
          <div className="mono-label !text-paper/60 mb-6">Then answer questions like</div>
          <ul className="space-y-3">
            {questions.map((q) => (
              <li
                key={q}
                className="flex items-center gap-3 rounded-xl border border-paper/15 bg-paper/5 px-4 py-3.5 text-sm transition-colors hover:border-paper/40"
              >
                <span className="font-mono text-paper/50">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm text-paper/60">
            Answers are grounded in the symbol graph — not guesses.
          </p>
        </div>
      </div>
    </Section>
  );
}
