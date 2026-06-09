import { SignIn, SignUp } from "./AuthButtons";
import { Graph } from "./icons";

export default function Hero() {
  return (
    <section
      id="top"
      className="grain relative overflow-hidden border-b border-line"
    >
      {/* layered grayscale backdrop */}
      <div className="bg-dotgrid pointer-events-none absolute inset-0 opacity-60" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-line" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, rgba(255,255,255,0) 0%, rgba(255,255,255,0.85) 70%, #ffffff 100%)",
        }}
      />

      <div className="relative mx-auto flex w-full max-w-4xl flex-col items-center px-6 pb-24 pt-20 text-center sm:px-10 md:pt-28">
        <div
          className="reveal mb-8 inline-flex items-center gap-2.5 rounded-full border border-line bg-mist px-4 py-1.5"
          style={{ animationDelay: "0ms" }}
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ink opacity-30" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-ink" />
          </span>
          <span className="mono-label !text-ink">AI code understanding agent</span>
        </div>

        <h1
          className="reveal text-balance text-6xl leading-[0.95] sm:text-7xl md:text-[7.5rem]"
          style={{ animationDelay: "80ms" }}
        >
          CodeGrok
        </h1>

        <p
          className="reveal mt-7 max-w-2xl text-balance text-lg leading-relaxed text-muted sm:text-xl"
          style={{ animationDelay: "160ms" }}
        >
          Understand any codebase. Ask questions. Get instant AI-powered
          explanations of how your system works.
        </p>

        <div
          className="reveal mt-10 flex flex-col items-center gap-3 sm:flex-row"
          style={{ animationDelay: "240ms" }}
        >
          <SignUp variant="primary" size="lg" withArrow />
          <SignIn variant="secondary" size="lg" />
        </div>

        <p
          className="reveal mono-label mt-6"
          style={{ animationDelay: "300ms" }}
        >
          No card required · Frontend demo
        </p>

        {/* code-aware preview card */}
        <div
          className="reveal mt-16 w-full max-w-3xl"
          style={{ animationDelay: "380ms" }}
        >
          <QueryPreview />
        </div>
      </div>
    </section>
  );
}

function QueryPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-line-strong bg-paper text-left shadow-[0_40px_80px_-40px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between border-b border-line bg-mist px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full border border-line-strong" />
          <span className="h-3 w-3 rounded-full border border-line-strong" />
          <span className="h-3 w-3 rounded-full border border-line-strong" />
        </div>
        <span className="font-mono text-xs text-faint">codegrok ~ auth-service</span>
        <Graph className="h-4 w-4 text-faint" />
      </div>

      <div className="space-y-4 p-5 font-mono text-[0.8rem] leading-relaxed sm:p-6 sm:text-sm">
        <div className="flex items-start gap-3">
          <span className="select-none text-faint">$</span>
          <p className="text-ink">
            How does authentication work in this project?
          </p>
        </div>

        <div className="rounded-xl border border-line bg-mist/60 p-4">
          <p className="text-muted">
            <span className="text-ink">Auth flow</span> starts in{" "}
            <span className="rounded bg-ink px-1.5 py-0.5 text-paper">
              login()
            </span>{" "}
            →{" "}
            <span className="rounded bg-ink px-1.5 py-0.5 text-paper">
              verifyToken()
            </span>{" "}
            →{" "}
            <span className="rounded bg-ink px-1.5 py-0.5 text-paper">
              createSession()
            </span>
            .
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-faint">
            <span># 3 symbols traced</span>
            <span># 2 imports</span>
            <span># call-graph depth 4</span>
            <span className="text-ink">
              answered<span className="caret" />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
