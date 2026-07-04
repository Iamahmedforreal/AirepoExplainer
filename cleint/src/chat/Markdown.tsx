import { memo, useState, type ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Check, Copy } from "../components/icons";

function extractText(node: ReactNode): string {
  if (node == null || node === false) return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (typeof node === "object" && "props" in node) {
    return extractText((node as { props: { children?: ReactNode } }).props.children);
  }
  return "";
}

function CodeBlock({ children }: { children?: ReactNode }) {
  const [copied, setCopied] = useState(false);
  // `children` is the <code> element produced by markdown.
  const codeEl = Array.isArray(children) ? children[0] : children;
  const className: string =
    (codeEl as { props?: { className?: string } })?.props?.className ?? "";
  const lang = /language-(\w+)/.exec(className)?.[1] ?? "";
  const raw = extractText(children).replace(/\n$/, "");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(raw);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="group/code my-4 overflow-hidden rounded-xl border border-white/10 bg-black/40">
      <div className="flex items-center justify-between border-b border-white/10 px-3.5 py-2">
        <span className="font-mono text-[0.68rem] uppercase tracking-widest text-faint">
          {lang || "code"}
        </span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 font-mono text-[0.68rem] text-muted transition-colors hover:text-ink"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" /> Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" /> Copy
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto px-4 py-3.5 text-[0.86rem] leading-relaxed">
        {children}
      </pre>
    </div>
  );
}

const components: Components = {
  pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
  code: ({ className, children, ...props }) => {
    const isBlock = /language-/.test(className ?? "");
    if (isBlock) {
      return (
        <code className={`${className ?? ""} font-mono`} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code className="rounded-md border border-white/10 bg-white/[0.06] px-1.5 py-0.5 font-mono text-[0.85em] text-ink-soft">
        {children}
      </code>
    );
  },
  p: ({ children }) => <p className="my-3 leading-relaxed first:mt-0 last:mb-0">{children}</p>,
  h1: ({ children }) => <h1 className="mb-3 mt-5 text-xl font-bold">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2.5 mt-5 text-lg font-bold">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold">{children}</h3>,
  ul: ({ children }) => (
    <ul className="my-3 list-disc space-y-1.5 pl-5 marker:text-faint">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-3 list-decimal space-y-1.5 pl-5 marker:text-faint">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-ink underline decoration-white/30 underline-offset-2 transition-colors hover:decoration-white"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-white/20 pl-4 text-muted italic">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-5 border-white/10" />,
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-xl border border-white/10">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-white/[0.04]">{children}</thead>,
  th: ({ children }) => (
    <th className="border-b border-white/10 px-3.5 py-2 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border-b border-white/[0.06] px-3.5 py-2 align-top">{children}</td>
  ),
};

function MarkdownImpl({ content }: { content: string }) {
  return (
    <div className="text-[0.95rem] text-ink-soft">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export const Markdown = memo(MarkdownImpl);
