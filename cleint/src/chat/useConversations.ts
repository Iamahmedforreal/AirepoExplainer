import { useCallback, useEffect, useRef, useState } from "react";
import type { Conversation } from "./types";
import { deriveTitle, makeConversation, makeMessage, uid } from "./utils";
import { streamAssistantReply } from "./mockAI";

const STORAGE_KEY = "codegrok.chat.conversations.v1";

function loadInitial(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Conversation[];
      if (Array.isArray(parsed) && parsed.length) return parsed;
    }
  } catch {
    /* ignore corrupt storage */
  }
  return [makeConversation()];
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(loadInitial);
  const [activeId, setActiveId] = useState<string>(() => "");
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Persist to localStorage.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      /* storage may be full or unavailable */
    }
  }, [conversations]);

  const activeConversation =
    conversations.find((c) => c.id === activeId) ?? conversations[0] ?? null;

  const patchConversation = useCallback(
    (id: string, fn: (c: Conversation) => Conversation) => {
      setConversations((prev) => prev.map((c) => (c.id === id ? fn(c) : c)));
    },
    [],
  );

  const newChat = useCallback(() => {
    // Reuse an existing empty conversation instead of piling up blanks.
    setConversations((prev) => {
      const empty = prev.find((c) => c.messages.length === 0);
      if (empty) {
        setActiveId(empty.id);
        return prev;
      }
      const fresh = makeConversation();
      setActiveId(fresh.id);
      return [fresh, ...prev];
    });
  }, []);

  const selectConversation = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  const renameConversation = useCallback(
    (id: string, title: string) => {
      const clean = title.trim();
      if (!clean) return;
      patchConversation(id, (c) => ({ ...c, title: clean }));
    },
    [patchConversation],
  );

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => {
        const next = prev.filter((c) => c.id !== id);
        const ensured = next.length ? next : [makeConversation()];
        setActiveId((current) =>
          current === id ? ensured[0].id : current,
        );
        return ensured;
      });
    },
    [],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || streamingId) return;

      const targetId = activeConversation?.id ?? uid();
      const userMsg = makeMessage("user", content);
      const assistantMsg = makeMessage("assistant", "");

      // Append user + placeholder assistant message; set title on first turn.
      setConversations((prev) => {
        let list = prev;
        if (!prev.some((c) => c.id === targetId)) {
          list = [makeConversation(), ...prev];
        }
        return list.map((c) => {
          if (c.id !== targetId) return c;
          const isFirst = c.messages.length === 0;
          return {
            ...c,
            title: isFirst ? deriveTitle(content) : c.title,
            messages: [...c.messages, userMsg, assistantMsg],
            updatedAt: Date.now(),
          };
        });
      });

      const controller = new AbortController();
      abortRef.current = controller;
      setStreamingId(targetId);

      try {
        await streamAssistantReply(
          content,
          (full) => {
            patchConversation(targetId, (c) => ({
              ...c,
              messages: c.messages.map((m) =>
                m.id === assistantMsg.id ? { ...m, content: full } : m,
              ),
              updatedAt: Date.now(),
            }));
          },
          controller.signal,
        );
      } finally {
        abortRef.current = null;
        setStreamingId(null);
      }
    },
    [activeConversation, streamingId, patchConversation],
  );

  return {
    conversations,
    activeConversation,
    activeId: activeConversation?.id ?? "",
    streamingId,
    isStreaming: streamingId != null,
    newChat,
    selectConversation,
    renameConversation,
    deleteConversation,
    sendMessage,
    stopStreaming,
  };
}
