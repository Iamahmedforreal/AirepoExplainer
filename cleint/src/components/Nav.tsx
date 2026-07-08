import { AuthCluster } from "./AuthButtons";

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-[#050609]/70 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6 sm:px-10">
        <a
          href="#top"
          className="group flex items-center gap-2 font-display text-lg font-bold tracking-tight"
        >
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
