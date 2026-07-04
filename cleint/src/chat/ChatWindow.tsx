import { useEffect, useRef } from "react";
import type { Conversation } from "./types";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import { LogoMark, PanelLeft, PenSquare } from "../components/icons";

const SUGGESTIONS = [
  "Explain the architecture of this repo",
  "Where does request handling start?",
  "Summarize the data model",
  "How is authentication wired up?",
];

function EmptyState({ onSend }: { onSend: (t: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <span className="emblem-glow badge-stars mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 text-ink">
        <LogoMark className="h-7 w-7" />
      </span>
      <h2 className="text-gradient font-display text-3xl font-bold tracking-tight">
        How can I help?
      </h2>
      <p className="mt-3 max-w-md text-muted">
        Ask about any part of your codebase — architecture, data flow, or a
        specific function.
      </p>
      <div className="mt-8 grid w-full max-w-xl grid-cols-1 gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSend(s)}
            className="glass rounded-xl px-4 py-3 text-left text-sm text-ink-soft transition-all hover:-translate-y-0.5 hover:border-white/30 hover:bg-white/[0.06]"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ChatWindow({
  conversation,
  isStreaming,
  streamingId,
  onSend,
  onStop,
  onNewChat,
  onToggleSidebar,
}: {
  conversation: Conversation | null;
  isStreaming: boolean;
  streamingId: string | null;
  onSend: (text: string) => void;
  onStop: () => void;
  onNewChat: () => void;
  onToggleSidebar: () => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const messages = conversation?.messages ?? [];
  const lastContent = messages[messages.length - 1]?.content ?? "";
  const isThisStreaming = isStreaming && streamingId === conversation?.id;

  // Auto-scroll to bottom as messages arrive / stream.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, lastContent]);

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-full min-w-0 flex-col">
      {/* Top bar */}
      <header className="flex h-14 shrink-0 items-center gap-2 border-b border-white/[0.06] px-3 sm:px-4">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-white/[0.06] hover:text-ink"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
        <h1 className="min-w-0 flex-1 truncate text-sm font-medium text-ink">
          {hasMessages ? conversation?.title : "New chat"}
        </h1>
        <button
          onClick={onNewChat}
          aria-label="New chat"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-white/[0.06] hover:text-ink"
        >
          <PenSquare className="h-5 w-5" />
        </button>
      </header>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {hasMessages ? (
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6">
            {messages.map((m) => (
              <div key={m.id} className="reveal" style={{ animationDuration: "0.4s" }}>
                <MessageBubble
                  message={m}
                  streaming={
                    isThisStreaming && m.id === messages[messages.length - 1].id
                  }
                />
              </div>
            ))}
            <div ref={bottomRef} className="h-px" />
          </div>
        ) : (
          <EmptyState onSend={onSend} />
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} onStop={onStop} isStreaming={isStreaming} />
    </div>
  );
}
