import { AuthCluster } from "./AuthButtons";
import { LogoMark } from "./icons";

const links = [
  { label: "What", href: "#what" },
  { label: "How it works", href: "#how" },
  { label: "Agent", href: "#agent" },
  { label: "Why", href: "#why" },
];

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-paper/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6 sm:px-10">
        <a href="#top" className="group flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-ink bg-ink text-paper transition-transform duration-200 group-hover:rotate-[-6deg]">
            <LogoMark className="h-5 w-5" />
          </span>
          <span className="font-display text-lg font-bold tracking-tight">
            CodeGrok
          </span>
        </a>

        <div className="hidden items-center gap-9 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="relative text-sm text-muted transition-colors hover:text-ink after:absolute after:-bottom-1.5 after:left-0 after:h-px after:w-0 after:bg-ink after:transition-all after:duration-300 hover:after:w-full"
            >
              {l.label}
            </a>
          ))}
        </div>

        <AuthCluster />
      </nav>
    </header>
  );
}
