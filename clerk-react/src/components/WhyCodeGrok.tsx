import Section from "./Section";
import { Check } from "./icons";

const benefits = [
  "Understand large codebases faster",
  "Reduce onboarding time",
  "Improve architecture visibility",
  "Navigate repositories effortlessly",
  "Discover hidden dependencies",
  "Accelerate development",
];

export default function WhyCodeGrok() {
  return (
    <Section
      id="why"
      label="Why developers love CodeGrok"
      title="Stop searching. Start understanding."
      intro="The fastest way to build a real mental model of any repository — and keep it as the code changes."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {benefits.map((b, i) => (
          <div
            key={b}
            className="glass group flex items-center gap-4 rounded-2xl p-7 transition-all duration-300 hover:-translate-y-1 hover:border-white/25 hover:bg-white/[0.05]"
          >
            <span className="font-mono text-xs text-faint">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/12 text-ink transition-colors group-hover:border-white group-hover:bg-white group-hover:text-[#050609]">
              <Check className="h-4 w-4" />
            </span>
            <p className="text-base font-medium tracking-tight">{b}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
