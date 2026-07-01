import { Github, LogoMark } from "./icons";

const cols = [
  {
    title: "Product",
    links: [
      { label: "What it does", href: "#features" },
      { label: "Architecture graph", href: "#graph" },
      { label: "How it works", href: "#how" },
      { label: "Why CodeGrok", href: "#why" },
    ],
  },
  {
    title: "Explore",
    links: [
      { label: "Who it's for", href: "#who" },
      { label: "Analyze a repo", href: "#top" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-white/8 px-6 py-16 sm:px-10">
      {/* the tagline the whole product is built around */}
      <div className="mx-auto mb-14 w-full max-w-6xl">
        <p className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          Paste repo URL
          <span className="text-faint"> &rarr; </span>
          understand codebase.
        </p>
      </div>

      <div className="mx-auto grid w-full max-w-6xl gap-12 md:grid-cols-[1.4fr_2fr]">
        <div>
          <a
            href="#top"
            className="flex items-center gap-2 font-display text-xl font-bold tracking-tight"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-md border border-white/15">
              <LogoMark className="h-3.5 w-3.5" />
            </span>
            CodeGrok<span className="text-faint">/</span>
          </a>
          <p className="mt-5 max-w-xs text-sm leading-relaxed text-muted">
            Sign in, paste a GitHub URL, generate an architecture graph, and chat
            with your code — understand any repository in minutes.
          </p>
          <a
            href="#top"
            className="glass mt-6 inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm text-ink transition-colors hover:border-white/35"
          >
            <Github className="h-4 w-4" />
            <span className="font-mono text-xs">star on github</span>
          </a>
        </div>

        <div className="grid grid-cols-2 gap-8">
          {cols.map((col) => (
            <div key={col.title}>
              <h3 className="mono-label mb-4">{col.title}</h3>
              <ul className="space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-muted transition-colors hover:text-ink"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="mx-auto mt-14 flex w-full max-w-6xl flex-col items-center justify-between gap-4 border-t border-white/8 pt-8 sm:flex-row">
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
          <span className="mono-label">Made for the night sky</span>
        </div>
      </div>
    </footer>
  );
}
