import { SignUp } from "./AuthButtons";
import { Arrow } from "./icons";

export default function Hero() {
  return (
    <section
      id="top"
      className="grain relative overflow-hidden border-b border-line"
    >
      {/* layered grayscale backdrop */}
      <div className="bg-dotgrid pointer-events-none absolute inset-0 opacity-60 dark:opacity-20" />
      {/* night-sky stars (dark mode only) */}
      <div className="starfield pointer-events-none absolute inset-0" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-line" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, transparent 0%, var(--color-paper) 82%)",
        }}
      />

      <div className="relative mx-auto flex w-full max-w-3xl flex-col items-center px-6 pb-24 pt-24 text-center sm:px-10 md:pt-32">
        <h1
          className="text-gradient reveal font-display text-6xl font-extrabold leading-[0.95] tracking-tight sm:text-7xl md:text-[7rem]"
          style={{ animationDelay: "80ms" }}
        >
          CodeGrok
        </h1>

        <p
          className="reveal mt-5 font-mono text-xs font-semibold uppercase tracking-[0.28em] text-ink sm:text-sm"
          style={{ animationDelay: "150ms" }}
        >
          Understand any codebase in minutes
        </p>

        <p
          className="reveal mt-7 max-w-2xl text-balance text-lg leading-relaxed text-muted sm:text-xl"
          style={{ animationDelay: "220ms" }}
        >
          CodeGrok analyzes repositories, generates architecture graphs, maps
          dependencies, and lets you chat with your codebase using AI.
        </p>

        <div
          className="reveal mt-10 flex flex-col items-center gap-3 sm:flex-row"
          style={{ animationDelay: "300ms" }}
        >
          <SignUp variant="primary" size="lg" withArrow>
            Analyze Repository
          </SignUp>
          <a
            href="#how"
            className="group inline-flex h-12 items-center justify-center gap-2 rounded-full border border-ink bg-paper px-7 text-[0.95rem] font-medium tracking-tight text-ink transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink hover:text-paper"
          >
            View Demo
            <Arrow className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </a>
        </div>

        <p
          className="reveal mono-label mt-6"
          style={{ animationDelay: "360ms" }}
        >
          No card required · Paste a GitHub URL to start
        </p>
      </div>
    </section>
  );
}
