import type { Message } from "./types";
import { Markdown } from "./Markdown";

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-1.5" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-muted"
          style={{ animation: `typing-bounce 1.2s ease-in-out ${i * 0.18}s infinite` }}
        />
      ))}
    </span>
  );
}

export default function MessageBubble({
  message,
  streaming,
}: {
  message: Message;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex w-full justify-end">
        <div className="glass max-w-[85%] rounded-2xl rounded-br-md px-4 py-2.5 text-[0.95rem] leading-relaxed whitespace-pre-wrap text-ink sm:max-w-[75%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full gap-3">
      <div className="min-w-0 flex-1 pt-0.5">
        {message.content ? (
          <Markdown content={message.content} />
        ) : streaming ? (
          <TypingDots />
        ) : null}
        {streaming && message.content && (
          <span className="caret ml-0.5 align-middle" aria-hidden="true" />
        )}
      </div>
    </div>
  );
}
