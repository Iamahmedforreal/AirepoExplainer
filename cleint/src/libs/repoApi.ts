import api from "./api";

export type Phase =
  | "pending"
  | "queued"
  | "cloning"
  | "parsing"
  | "embedding"
  | "indexing"
  | "indexed"
  | "failed";

export interface Repo {
  id: string;
  githubUrl: string;
  repoOwner: string;
  repoName: string;
  defaultBranch: string | null;
  language: string | null;
  description: string | null;
  topics: string[];
  isPrivate: boolean;
  status: string | null;
  sourceFileCount: number | null;
  chunkCount: number | null;
  connectionCount: number | null;
  indexedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  phase?: Phase;
}

export interface SubmitRepoResponse {
  status: string;
  repoId: string;
  jobId: string | null;
  repo: Repo;
}

/** Normalise loose repo input into a canonical https GitHub URL, or null. */
export function normalizeRepoUrl(raw: string): string | null {
  let s = raw.trim();
  if (!s) return null;
  s = s.replace(/\.git$/, "").replace(/\/+$/, "");

  // bare "owner/repo"
  if (/^[\w.-]+\/[\w.-]+$/.test(s)) return `https://github.com/${s}`;
  // "github.com/owner/repo" without scheme
  if (/^(www\.)?github\.com\//i.test(s)) s = `https://${s.replace(/^www\./i, "")}`;

  try {
    const u = new URL(s);
    if (u.hostname !== "github.com" && u.hostname !== "www.github.com") return null;
    const parts = u.pathname.split("/").filter(Boolean);
    if (parts.length < 2) return null;
    return `https://github.com/${parts[0]}/${parts[1]}`;
  } catch {
    return null;
  }
}

export async function submitRepo(url: string): Promise<SubmitRepoResponse> {
  const { data } = await api.post<SubmitRepoResponse>("/api/repos", { url });
  return data;
}

export async function listRepos(): Promise<Repo[]> {
  const { data } = await api.get<{ repos: Repo[] }>("/api/repos");
  return data.repos;
}

export async function getRepo(repoId: string): Promise<Repo> {
  const { data } = await api.get<Repo>(`/api/repos/${repoId}`);
  return data;
}
