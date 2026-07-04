import { Github, LogoMark } from "./icons";

export default function Footer() {
  return (
    <footer className="relative border-t border-white/8 px-6 py-16 sm:px-10">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center text-center">
        <a
          href="#top"
          className="flex items-center gap-2 font-display text-xl font-bold tracking-tight"
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-md border border-white/15">
            <LogoMark className="h-3.5 w-3.5" />
          </span>
          CodeGrok<span className="text-faint">/</span>
        </a>

        <p className="mt-5 max-w-md text-sm leading-relaxed text-muted">
          Sign in, paste a GitHub URL, generate an architecture graph, and chat
          with your code — understand any repository in minutes.
        </p>

        <a
          href="#top"
          className="glass mt-7 inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm text-ink transition-colors hover:border-white/35"
        >
          <Github className="h-4 w-4" />
          <span className="font-mono text-xs">star on github</span>
        </a>
      </div>

      <div className="mx-auto mt-14 flex w-full max-w-3xl flex-col items-center justify-between gap-4 border-t border-white/8 pt-8 sm:flex-row">
        <p className="font-mono text-xs text-faint">
          © {new Date().getFullYear()} CodeGrok — built for developers.
        </p>
        <div className="flex items-center gap-6">
          <a
            href="#top"
            className="text-xs text-faint transition-colors hover:text-ink"
          >
            Privacy
          </a>
          <a
            href="#top"
            className="text-xs text-faint transition-colors hover:text-ink"
          >
            Terms
          </a>
        </div>
      </div>
    </footer>
  );
}
