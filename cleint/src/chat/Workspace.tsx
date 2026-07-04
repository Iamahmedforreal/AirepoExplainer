import { useCallback, useEffect, useRef, useState } from "react";
import ChatPage from "./ChatPage";
import ConnectRepo from "./ConnectRepo";
import IndexingProgress from "./IndexingProgress";
import { getRepo, listRepos, submitRepo, type Repo } from "../libs/repoApi";

type View = "loading" | "connect" | "indexing" | "chat";

const ACTIVE_REPO_KEY = "codegrok.activeRepoId";
const POLL_MS = 1500;

function errorMessage(e: unknown, fallback: string): string {
  const err = e as {
    response?: { data?: { detail?: string }; status?: number };
    message?: string;
  };
  return err?.response?.data?.detail ?? err?.message ?? fallback;
}
function statusOf(e: unknown): number | undefined {
  return (e as { response?: { status?: number } })?.response?.status;
}

export default function Workspace() {
  const [view, setView] = useState<View>("loading");
  const [repos, setRepos] = useState<Repo[]>([]);
  const [currentRepo, setCurrentRepo] = useState<Repo | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const openRepo = useCallback((repo: Repo) => {
    setCurrentRepo(repo);
    localStorage.setItem(ACTIVE_REPO_KEY, repo.id);
    setError(null);
    setView(repo.phase === "indexed" ? "chat" : "indexing");
  }, []);

  const goConnect = useCallback(() => {
    localStorage.removeItem(ACTIVE_REPO_KEY);
    setCurrentRepo(null);
    setError(null);
    setView("connect");
    listRepos().then(setRepos).catch(() => {});
  }, []);

  // Initial load: restore an active repo or show the connect screen.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const stored = localStorage.getItem(ACTIVE_REPO_KEY);
      let repoList: Repo[] = [];
      try {
        repoList = await listRepos();
      } catch {
        /* backend may be unreachable */
      }
      if (cancelled) return;
      setRepos(repoList);

      if (stored) {
        try {
          const repo = await getRepo(stored);
          if (cancelled) return;
          setCurrentRepo(repo);
          setView(repo.phase === "indexed" ? "chat" : "indexing");
          return;
        } catch {
          localStorage.removeItem(ACTIVE_REPO_KEY);
        }
      }
      if (!cancelled) setView("connect");
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Poll repo status while indexing.
  useEffect(() => {
    if (view !== "indexing" || !currentRepo) return;
    const repoId = currentRepo.id;

    const stop = () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };

    const tick = async () => {
      try {
        const repo = await getRepo(repoId);
        setCurrentRepo(repo);
        if (repo.phase === "indexed") {
          stop();
          // Let the "Index complete" screen breathe before entering chat.
          setTimeout(() => setView("chat"), 2400);
        } else if (repo.phase === "failed") {
          stop();
        }
      } catch {
        /* transient; keep polling */
      }
    };

    pollRef.current = window.setInterval(tick, POLL_MS);
    tick();
    return stop;
  }, [view, currentRepo?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = useCallback(
    async (url: string) => {
      setSubmitting(true);
      setError(null);
      try {
        const res = await submitRepo(url);
        openRepo({ ...res.repo, phase: res.repo.phase ?? "queued" });
      } catch (e) {
        if (statusOf(e) === 409) {
          // Already submitted — jump to the existing repo.
          try {
            const list = await listRepos();
            setRepos(list);
            const existing = list.find((r) => r.githubUrl === url);
            if (existing) {
              openRepo(existing);
              return;
            }
          } catch {
            /* fall through to error */
          }
          setError("You have already connected this repository.");
        } else {
          setError(errorMessage(e, "Could not start indexing. Is the API running?"));
        }
      } finally {
        setSubmitting(false);
      }
    },
    [openRepo],
  );

  const handleRetry = useCallback(() => {
    if (currentRepo) handleSubmit(currentRepo.githubUrl);
  }, [currentRepo, handleSubmit]);

  if (view === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-white/15 border-t-white/70" />
      </div>
    );
  }

  if (view === "chat") return <ChatPage />;

  if (view === "indexing" && currentRepo) {
    return (
      <IndexingProgress
        repo={currentRepo}
        onEnter={() => setView("chat")}
        onRetry={handleRetry}
        onBack={goConnect}
      />
    );
  }

  return (
    <ConnectRepo
      onSubmit={handleSubmit}
      submitting={submitting}
      error={error}
      repos={repos}
      onOpenRepo={openRepo}
    />
  );
}
