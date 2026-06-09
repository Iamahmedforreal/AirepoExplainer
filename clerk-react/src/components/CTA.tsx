import { SignUp } from "./AuthButtons";
import { Arrow, LogoMark } from "./icons";

export default function CTA() {
  return (
    <section className="grain relative overflow-hidden border-t border-line px-6 py-28 sm:px-10 md:py-36">
      <div className="bg-dotgrid pointer-events-none absolute inset-0 opacity-50" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(70% 60% at 50% 50%, rgba(255,255,255,0) 0%, #ffffff 75%)",
        }}
      />

      <div className="relative mx-auto flex max-w-3xl flex-col items-center text-center">
        <span className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl border border-ink bg-ink text-paper">
          <LogoMark className="h-6 w-6" />
        </span>

        <h2 className="text-balance text-4xl sm:text-5xl md:text-6xl">
          Stop reading code.
          <br />
          Start understanding it.
        </h2>

        <p className="mt-6 max-w-xl text-balance text-lg text-muted">
          Turn your repository into a structured knowledge graph and chat with it
          like an AI engineer.
        </p>

        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          <SignUp variant="primary" size="lg" withArrow />
          <a
            href="#top"
            className="group inline-flex h-12 items-center justify-center gap-2 rounded-full border border-ink bg-paper px-7 text-[0.95rem] font-medium tracking-tight text-ink transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink hover:text-paper"
          >
            Try Demo
            <Arrow className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </a>
          <a
            href="#agent"
            className="inline-flex h-12 items-center justify-center rounded-full border border-line bg-transparent px-7 text-[0.95rem] font-medium tracking-tight text-ink transition-all duration-200 hover:-translate-y-0.5 hover:border-ink"
          >
            View Docs
          </a>
        </div>
      </div>
    </section>
  );
}
