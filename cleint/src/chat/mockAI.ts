/**
 * Mock streaming assistant. Produces a markdown reply and yields it in small
 * chunks so the UI can render a live "typing" stream.
 *
 * Swap `streamAssistantReply` for a real backend call (e.g. a fetch to
 * `/api/chat` reading a ReadableStream) and the rest of the UI stays the same.
 */

const REPLIES: ((q: string) => string)[] = [
  (q) => `Great question about **${short(q)}**. Here's how I'd approach it:

1. Start by mapping the **entry points** and how data flows through them.
2. Identify the core modules and their responsibilities.
3. Trace one request end-to-end to ground your mental model.

A quick example in TypeScript:

\`\`\`ts
async function trace(repoId: string) {
  const graph = await buildGraph(repoId);
  return graph.nodes.filter((n) => n.kind === "service");
}
\`\`\`

Let me know if you'd like me to go deeper on any step.`,
  (q) => `Sure — thinking about *${short(q)}*, a few things stand out:

- The architecture favors **small, composable units**.
- Side effects are isolated so the core stays testable.
- Naming is consistent, which makes navigation predictable.

> Tip: follow the imports outward from \`main\` to see the shape of the system.

Want me to sketch the dependency graph next?`,
  (q) => `Here's a concise breakdown for **${short(q)}**:

| Layer | Responsibility |
| --- | --- |
| Router | Accepts requests, validates input |
| Service | Business logic |
| Store | Persistence + queries |

And the minimal handler looks like:

\`\`\`python
def handle(request):
    data = validate(request.json)
    return service.process(data)
\`\`\`

Happy to expand any row into detail.`,
];

const short = (q: string) => {
  const clean = q.trim().replace(/\s+/g, " ");
  return clean.length > 40 ? `${clean.slice(0, 40)}…` : clean || "that";
};

function pickReply(question: string): string {
  const idx = Math.abs(hash(question)) % REPLIES.length;
  return REPLIES[idx](question);
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i);
  return h;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Streams an assistant reply chunk-by-chunk.
 * @param onChunk called with the full accumulated text each tick
 * @param signal optional AbortSignal to stop streaming early
 */
export async function streamAssistantReply(
  question: string,
  onChunk: (fullText: string) => void,
  signal?: AbortSignal,
): Promise<string> {
  const full = pickReply(question);
  // Tokenize keeping whitespace so markdown structure is preserved.
  const tokens = full.match(/\S+\s*|\s+/g) ?? [full];
  let acc = "";
  await sleep(280); // initial "thinking" delay
  for (const tok of tokens) {
    if (signal?.aborted) break;
    acc += tok;
    onChunk(acc);
    await sleep(14 + Math.random() * 34);
  }
  return acc;
}
