import { useEffect, useRef, useState } from "react";
import { Send, Stop } from "../components/icons";

const MAX_HEIGHT = 200;

export default function ChatInput({
  onSend,
  onStop,
  isStreaming,
}: {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-expand the textarea up to a max height.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value]);

  const submit = () => {
    const text = value.trim();
    if (!text || isStreaming) return;
    onSend(text);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const canSend = value.trim().length > 0 && !isStreaming;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-4 sm:px-6 sm:pb-6">
      <div className="glass-strong flex items-end gap-2 rounded-2xl p-2 pl-4 transition-colors focus-within:border-white/30">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask anything about your codebase…"
          className="max-h-[200px] flex-1 resize-none bg-transparent py-2.5 text-[0.95rem] leading-relaxed text-ink placeholder:text-faint focus:outline-none"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop generating"
            className="mb-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/15 bg-white/[0.06] text-ink transition-colors hover:bg-white/[0.12]"
          >
            <Stop className="h-3.5 w-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send message"
            className="mb-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-[#050609] transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:translate-y-0"
          >
            <Send className="h-4 w-4" />
          </button>
        )}
      </div>
      <p className="mt-2 text-center text-xs text-faint">
        CodeGrok can make mistakes. Verify important details.
      </p>
    </div>
  );
}
