import { AuthCluster } from "./AuthButtons";
import { LogoMark } from "./icons";

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-[#050609]/70 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6 sm:px-10">
        <a
          href="#top"
          className="group flex items-center gap-2 font-display text-lg font-bold tracking-tight"
        >
          <span className="emblem-glow flex h-7 w-7 items-center justify-center rounded-lg border border-white/15 text-ink">
            <LogoMark className="h-4 w-4" />
          </span>
          CodeGrok
          <span className="text-faint transition-colors group-hover:text-ink">
            /
          </span>
        </a>

        <div className="flex items-center gap-3">
          <AuthCluster />
        </div>
      </nav>
    </header>
  );
}
