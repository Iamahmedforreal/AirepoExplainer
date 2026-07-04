import { useEffect, useState, type ReactElement } from "react";
import { UserButton } from "@clerk/react";
import type { Phase, Repo } from "../libs/repoApi";
import {
  Arrow,
  Brain,
  Check,
  Close,
  Github,
  Index,
  LogoMark,
  Parse,
} from "../components/icons";

interface Step {
  key: string;
  label: string;
  hint: string;
  Icon: (p: { className?: string }) => ReactElement;
}

const STEPS: Step[] = [
  { key: "queued", label: "Queued", hint: "Waiting for a worker", Icon: Index },
  { key: "cloning", label: "Cloning", hint: "Fetching source from GitHub", Icon: Github },
  { key: "parsing", label: "Parsing", hint: "Extracting symbols & structure", Icon: Parse },
  { key: "embedding", label: "Embedding", hint: "Vectorising code chunks", Icon: Brain },
];

function activeIndex(phase: Phase): number {
  switch (phase) {
    case "pending":
    case "queued":
      return 0;
    case "cloning":
      return 1;
    case "parsing":
      return 2;
    case "embedding":
    case "indexing":
      return 3;
    case "indexed":
      return STEPS.length; // all complete
    default:
      return 0;
  }
}

function useElapsed(active: boolean) {
  const [start] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [active]);
  const s = Math.max(0, Math.floor((now - start) / 1000));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

export default function IndexingProgress({
  repo,
  onEnter,
  onRetry,
  onBack,
}: {
  repo: Repo;
  onEnter: () => void;
  onRetry: () => void;
  onBack: () => void;
}) {
  const phase = repo.phase ?? "queued";
  const failed = phase === "failed";
  const done = phase === "indexed";
  const active = activeIndex(phase);
  const elapsed = useElapsed(!done && !failed);

  return (
    <div className="relative flex min-h-screen flex-col">
      <style>{`
        @keyframes cg-scan { 0% { transform: translateY(-30%); opacity: 0 } 15%,85% { opacity: .5 } 100% { transform: translateY(2400%); opacity: 0 } }
        @keyframes cg-rail { 0% { background-position: 0 0 } 100% { background-position: 0 -18px } }
      `}</style>
      <div className="starfield pointer-events-none absolute inset-0" aria-hidden="true" />

      <header className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10">
        <div className="flex items-center gap-2 font-display text-base font-bold tracking-tight">
          <span className="emblem-glow flex h-7 w-7 items-center justify-center rounded-lg border border-white/15 text-ink">
            <LogoMark className="h-4 w-4" />
          </span>
          CodeGrok
          <span className="text-faint">/</span>
          <span className="mono-label ml-1 hidden sm:inline">indexing</span>
        </div>
        <UserButton />
      </header>

      {done ? (
        <CompletionHero repo={repo} onEnter={onEnter} />
      ) : (
      <main className="relative z-10 mx-auto grid w-full max-w-3xl flex-1 content-center gap-10 px-6 pb-16 sm:px-10 md:grid-cols-[1.4fr_1fr]">
        {/* left: the pipeline */}
        <section>
          <p className="mono-label mb-3">
            {done ? "Complete" : failed ? "Failed" : "Building index"}
          </p>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink">
            <span className="text-gradient">{repo.repoOwner}/{repo.repoName}</span>
          </h1>
          <p className="mt-2 font-mono text-xs text-faint">
            {repo.githubUrl}
          </p>

          <ol className="mt-8 flex flex-col">
            {STEPS.map((step, i) => {
              const isDone = done || i < active;
              const isActive = !done && !failed && i === active;
              const isFailed = failed && i === active;
              const isPending = !isDone && !isActive && !isFailed;
              const last = i === STEPS.length - 1;
              return (
                <li key={step.key} className="flex gap-4">
                  {/* node + rail */}
                  <div className="flex flex-col items-center">
                    <span
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition-colors ${
                        isDone
                          ? "border-white/25 bg-white/[0.06] text-ink"
                          : isActive
                            ? "border-white/40 bg-white/[0.08] text-ink"
                            : isFailed
                              ? "border-red-500/40 bg-red-500/10 text-red-400"
                              : "border-white/10 bg-transparent text-faint"
                      }`}
                    >
                      {isDone ? (
                        <Check className="h-4 w-4" />
                      ) : isFailed ? (
                        <Close className="h-4 w-4" />
                      ) : isActive ? (
                        <span className="relative flex h-5 w-5 items-center justify-center">
                          <span className="absolute h-5 w-5 animate-spin rounded-full border border-white/20 border-t-white/80" />
                          <step.Icon className="h-3 w-3" />
                        </span>
                      ) : (
                        <step.Icon className="h-4 w-4" />
                      )}
                    </span>
                    {!last && (
                      <span
                        className="my-1 w-px flex-1"
                        style={{
                          minHeight: 26,
                          backgroundImage: isDone
                            ? "linear-gradient(rgba(255,255,255,0.35),rgba(255,255,255,0.35))"
                            : "repeating-linear-gradient(rgba(255,255,255,0.22) 0 3px, transparent 3px 9px)",
                          animation: isActive ? "cg-rail .9s linear infinite" : undefined,
                        }}
                        aria-hidden="true"
                      />
                    )}
                  </div>

                  {/* label */}
                  <div className={`pb-6 pt-1.5 ${isPending ? "opacity-45" : ""}`}>
                    <p
                      className={`text-sm font-medium ${
                        isActive ? "text-ink" : isFailed ? "text-red-400" : "text-ink-soft"
                      }`}
                    >
                      {step.label}
                      {isActive && <span className="caret ml-1 !h-[0.9em]" aria-hidden="true" />}
                    </p>
                    <p className="mt-0.5 font-mono text-xs text-faint">{step.hint}</p>
                  </div>
                </li>
              );
            })}
          </ol>

          {/* terminal states */}
          {failed && (
            <div className="mt-1 flex flex-wrap gap-2.5">
              <button
                onClick={onRetry}
                className="inline-flex h-10 items-center gap-2 rounded-xl bg-white px-5 text-sm font-semibold text-[#050609] transition-all hover:-translate-y-0.5"
              >
                Try again
              </button>
              <button
                onClick={onBack}
                className="glass inline-flex h-10 items-center gap-2 rounded-xl px-5 text-sm text-ink transition-colors hover:border-white/30"
              >
                Choose another repo
              </button>
            </div>
          )}
        </section>

        {/* right: live telemetry */}
        <aside className="relative">
          <div className="glass-strong relative overflow-hidden rounded-2xl p-5">
            {/* scanning sweep */}
            {!done && !failed && (
              <span
                className="pointer-events-none absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-white/10 to-transparent"
                style={{ animation: "cg-scan 2.6s ease-in-out infinite" }}
                aria-hidden="true"
              />
            )}
            <div className="flex items-center justify-between">
              <span className="mono-label">Telemetry</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  failed ? "bg-red-400" : done ? "bg-emerald-400" : "animate-pulse bg-white"
                }`}
                aria-hidden="true"
              />
            </div>

            <dl className="mt-4 flex flex-col divide-y divide-white/[0.06] font-mono text-sm">
              <Row label="status" value={done ? "indexed" : failed ? "failed" : phase} />
              <Row label="elapsed" value={elapsed} />
              <Row label="branch" value={repo.defaultBranch ?? "—"} />
              <Row label="language" value={repo.language ?? "—"} />
              <Row label="files" value={fmt(repo.sourceFileCount)} />
              <Row label="chunks" value={fmt(repo.chunkCount)} />
              <Row label="links" value={fmt(repo.connectionCount)} />
            </dl>
          </div>

          <p className="mt-4 px-1 text-xs leading-relaxed text-faint">
            {done
              ? "Your codebase is mapped. Head into the workspace to start asking questions."
              : failed
                ? "Indexing stopped before it finished. Retry, or point CodeGrok at a different repository."
                : "You can keep this open — indexing continues on the server even if you leave."}
          </p>
        </aside>
      </main>
      )}
    </div>
  );
}

function CompletionHero({
  repo,
  onEnter,
}: {
  repo: Repo;
  onEnter: () => void;
}) {
  return (
    <main className="relative z-10 mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center px-6 pb-16 text-center">
      <span
        className="emblem-glow badge-stars reveal mb-7 flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
        style={{ animationDelay: "20ms" }}
      >
        <Check className="h-8 w-8" />
      </span>
      <p className="reveal mono-label mb-4" style={{ animationDelay: "90ms" }}>
        Index complete
      </p>
      <h1
        className="text-gradient reveal font-display text-4xl font-extrabold tracking-tight sm:text-5xl"
        style={{ animationDelay: "150ms" }}
      >
        {repo.repoOwner}/{repo.repoName}
      </h1>
      <p
        className="reveal mt-4 max-w-sm text-balance leading-relaxed text-muted"
        style={{ animationDelay: "210ms" }}
      >
        The codebase is fully mapped and searchable. Opening your workspace…
      </p>

      <div
        className="reveal mt-8 flex items-center gap-8 font-mono"
        style={{ animationDelay: "270ms" }}
      >
        <Stat label="files" value={fmt(repo.sourceFileCount)} />
        <Stat label="chunks" value={fmt(repo.chunkCount)} />
        <Stat label="links" value={fmt(repo.connectionCount)} />
      </div>

      <button
        onClick={onEnter}
        className="group reveal mt-10 inline-flex h-11 items-center gap-2 rounded-xl bg-white px-6 text-sm font-semibold tracking-tight text-[#050609] transition-all hover:-translate-y-0.5"
        style={{ animationDelay: "330ms" }}
      >
        Enter workspace
        <Arrow className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </button>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-xl font-semibold text-ink">{value}</span>
      <span className="mono-label text-[0.6rem]">{label}</span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <dt className="text-faint">{label}</dt>
      <dd className="text-ink-soft">{value}</dd>
    </div>
  );
}

const fmt = (n: number | null | undefined) =>
  n == null ? "—" : n.toLocaleString("en-US");
