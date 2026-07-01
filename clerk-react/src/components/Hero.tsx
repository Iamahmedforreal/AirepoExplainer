import { SignUpButton } from "@clerk/react";
import { SignIn } from "./AuthButtons";
import { Arrow, Github, LogoMark } from "./icons";

export default function Hero() {
  return (
    <section
      id="top"
      className="grain relative overflow-hidden"
    >
      {/* extra local starlight so the hero reads as the brightest patch of sky */}
      <div className="starfield pointer-events-none absolute inset-0" />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-64"
        style={{
          background:
            "radial-gradient(60% 100% at 50% 0%, rgba(255,255,255,0.06), transparent 70%)",
        }}
      />

      <div className="relative mx-auto flex w-full max-w-3xl flex-col items-center px-6 pb-20 pt-20 text-center sm:px-10 md:pt-28">
        <span
          className="badge-stars reveal emblem-glow relative mb-8 inline-flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 text-ink"
          style={{ animationDelay: "40ms" }}
        >
          <LogoMark className="h-7 w-7" />
        </span>

        <p
          className="reveal mono-label mb-6"
          style={{ animationDelay: "120ms" }}
        >
          Understand any codebase in minutes
        </p>

        <h1
          className="text-gradient reveal font-display text-5xl font-extrabold leading-[0.98] tracking-tight sm:text-6xl md:text-7xl"
          style={{ animationDelay: "180ms" }}
        >
          Read code like
          <br />
          you wrote it.
        </h1>

        <p
          className="reveal mt-7 max-w-xl text-balance text-lg leading-relaxed text-muted"
          style={{ animationDelay: "260ms" }}
        >
          Sign in, paste a GitHub URL, and CodeGrok maps the whole repository into
          an architecture graph you can chat with — services, calls, imports, and
          dependencies, explained in plain English.
        </p>

        {/* the "product" itself: a repo-url input that starts the sign-up flow */}
        <RepoUrlPanel />

        <div
          className="reveal mt-6 flex flex-col items-center gap-3 sm:flex-row"
          style={{ animationDelay: "420ms" }}
        >
          <span className="text-sm text-faint">Already have an account?</span>
          <SignIn variant="ghost">Sign in</SignIn>
        </div>

        <p
          className="reveal mono-label mt-8 flex items-center gap-2"
          style={{ animationDelay: "480ms" }}
        >
          <Github className="h-3.5 w-3.5" />
          No card required · works with any public repo
        </p>
      </div>
    </section>
  );
}

function RepoUrlPanel() {
  return (
    <div
      className="reveal mt-11 w-full max-w-xl"
      style={{ animationDelay: "340ms" }}
    >
      <SignUpButton mode="modal">
        <button
          type="button"
          className="glass-strong group flex w-full flex-col gap-3 rounded-2xl p-3 text-left transition-all duration-200 hover:border-white/30 hover:shadow-[0_24px_70px_-32px_rgba(255,255,255,0.35)] sm:flex-row sm:items-center"
        >
          <span className="flex flex-1 items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
            <Github className="h-5 w-5 shrink-0 text-faint" />
            <span className="truncate font-mono text-sm text-muted">
              github.com/your-org/your-repo
            </span>
          </span>
          <span className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-6 text-sm font-semibold tracking-tight text-[#050609] transition-transform duration-200 group-hover:-translate-y-0.5">
            Understand codebase
            <Arrow className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </span>
        </button>
      </SignUpButton>
      <p className="mt-3 font-mono text-xs text-faint">
        Sign up to connect a repository — it&apos;s the only setup.
      </p>
    </div>
  );
}
