import { useState, type FormEvent } from "react";
import { UserButton } from "@clerk/react";
import { normalizeRepoUrl, type Repo } from "../libs/repoApi";
import { Arrow, Github, LogoMark } from "../components/icons";

const PIPELINE = ["Clone", "Parse", "Embed", "Index"];
const EXAMPLES = ["tiangolo/fastapi", "pallets/flask", "psf/requests"];

export default function ConnectRepo({
  onSubmit,
  submitting,
  error,
  repos,
  onOpenRepo,
}: {
  onSubmit: (url: string) => void;
  submitting: boolean;
  error: string | null;
  repos: Repo[];
  onOpenRepo: (repo: Repo) => void;
}) {
  const [value, setValue] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    const url = normalizeRepoUrl(value);
    if (!url) {
      setLocalError("Enter a valid GitHub repository, e.g. owner/repo");
      return;
    }
    setLocalError(null);
    onSubmit(url);
  };

  const shown = error ?? localError;

  return (
    <div className="relative flex min-h-screen flex-col">
      {/* local starlight so this screen reads as its own bright patch of sky */}
      <div className="starfield pointer-events-none absolute inset-0" aria-hidden="true" />

      {/* app chrome */}
      <header className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10">
        <div className="flex items-center gap-2 font-display text-base font-bold tracking-tight">
          <span className="emblem-glow flex h-7 w-7 items-center justify-center rounded-lg border border-white/15 text-ink">
            <LogoMark className="h-4 w-4" />
          </span>
          CodeGrok
          <span className="text-faint">/</span>
          <span className="mono-label ml-1 hidden sm:inline">connect</span>
        </div>
        <UserButton />
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-6 pb-20 sm:px-10">
        <p className="reveal mono-label mb-5" style={{ animationDelay: "40ms" }}>
          New index · Step 01
        </p>
        <h1
          className="text-gradient reveal font-display text-4xl font-extrabold leading-[1.02] tracking-tight sm:text-5xl"
          style={{ animationDelay: "110ms" }}
        >
          Point CodeGrok
          <br />
          at a repository.
        </h1>
        <p
          className="reveal mt-5 max-w-lg text-balance leading-relaxed text-muted"
          style={{ animationDelay: "180ms" }}
        >
          Paste a public GitHub URL. We clone it, parse every symbol, and build a
          searchable map of the codebase — then you can chat with it.
        </p>

        {/* the input */}
        <form
          onSubmit={submit}
          className="reveal mt-9"
          style={{ animationDelay: "250ms" }}
        >
          <div
            className={`glass-strong flex flex-col gap-2 rounded-2xl p-2 transition-colors sm:flex-row sm:items-center sm:gap-2 ${
              shown ? "border-red-500/40" : "focus-within:border-white/30"
            }`}
          >
            <label className="flex flex-1 items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
              <Github className="h-5 w-5 shrink-0 text-faint" />
              <input
                autoFocus
                value={value}
                onChange={(e) => {
                  setValue(e.target.value);
                  if (localError) setLocalError(null);
                }}
                disabled={submitting}
                placeholder="github.com/owner/repo"
                spellCheck={false}
                autoCapitalize="off"
                autoCorrect="off"
                className="min-w-0 flex-1 bg-transparent font-mono text-sm text-ink placeholder:text-faint focus:outline-none disabled:opacity-60"
              />
            </label>
            <button
              type="submit"
              disabled={submitting}
              className="group inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-6 text-sm font-semibold tracking-tight text-[#050609] transition-all duration-200 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
            >
              {submitting ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#050609]/30 border-t-[#050609]" />
                  Indexing
                </>
              ) : (
                <>
                  Index repository
                  <Arrow className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </>
              )}
            </button>
          </div>

          {/* validation / server error */}
          {shown ? (
            <p className="mt-2.5 pl-1 font-mono text-xs text-red-400">{shown}</p>
          ) : (
            <div className="mt-3 flex flex-wrap items-center gap-2 pl-1">
              <span className="mono-label text-[0.62rem]">Try</span>
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setValue(ex)}
                  className="rounded-full border border-white/10 bg-white/[0.02] px-2.5 py-1 font-mono text-xs text-muted transition-colors hover:border-white/25 hover:text-ink"
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </form>

        {/* pipeline preview — sets expectations for the next screen */}
        <div
          className="reveal mt-10 flex items-center gap-1.5"
          style={{ animationDelay: "320ms" }}
        >
          {PIPELINE.map((step, i) => (
            <div key={step} className="flex items-center gap-1.5">
              <span className="mono-label text-[0.62rem] text-faint">
                {String(i + 1).padStart(2, "0")} {step}
              </span>
              {i < PIPELINE.length - 1 && (
                <span className="h-px w-6 bg-line-strong" aria-hidden="true" />
              )}
            </div>
          ))}
        </div>

        {/* returning users: jump back into an existing repo */}
        {repos.length > 0 && (
          <div
            className="reveal mt-12 border-t border-white/[0.06] pt-8"
            style={{ animationDelay: "380ms" }}
          >
            <p className="mono-label mb-3">Your repositories</p>
            <ul className="flex flex-col gap-1.5">
              {repos.slice(0, 6).map((repo) => (
                <li key={repo.id}>
                  <button
                    type="button"
                    onClick={() => onOpenRepo(repo)}
                    className="glass group flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-all hover:border-white/25 hover:bg-white/[0.05]"
                  >
                    <Github className="h-4 w-4 shrink-0 text-faint" />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-mono text-sm text-ink">
                        {repo.repoOwner}/{repo.repoName}
                      </span>
                    </span>
                    <RepoBadge phase={repo.phase} />
                    <Arrow className="h-4 w-4 shrink-0 text-faint transition-transform group-hover:translate-x-1 group-hover:text-ink" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}

function RepoBadge({ phase }: { phase?: string }) {
  const label = phase === "indexed" ? "ready" : phase === "failed" ? "failed" : phase ?? "queued";
  const tone =
    phase === "indexed"
      ? "text-emerald-300/90 border-emerald-400/20"
      : phase === "failed"
        ? "text-red-400 border-red-500/25"
        : "text-faint border-white/10";
  return (
    <span
      className={`shrink-0 rounded-full border px-2 py-0.5 font-mono text-[0.62rem] uppercase tracking-wider ${tone}`}
    >
      {label}
    </span>
  );
}
