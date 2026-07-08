import { useEffect, useRef, useState } from "react";
import { UserButton, useUser } from "@clerk/react";
import type { Conversation } from "./types";
import { groupConversations } from "./utils";
import { Check, Close, Pencil, Plus, Trash } from "../components/icons";

function ConversationItem({
  conversation,
  active,
  onSelect,
  onRename,
  onDelete,
}: {
  conversation: Conversation;
  active: boolean;
  onSelect: () => void;
  onRename: (title: string) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(conversation.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  const commit = () => {
    onRename(draft);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex items-center gap-1 rounded-lg border border-white/25 bg-white/[0.04] px-2 py-1.5">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") {
              setDraft(conversation.title);
              setEditing(false);
            }
          }}
          className="min-w-0 flex-1 bg-transparent text-sm text-ink focus:outline-none"
        />
        <button
          onClick={commit}
          aria-label="Save title"
          className="shrink-0 rounded p-1 text-muted hover:text-ink"
        >
          <Check className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => {
            setDraft(conversation.title);
            setEditing(false);
          }}
          aria-label="Cancel"
          className="shrink-0 rounded p-1 text-muted hover:text-ink"
        >
          <Close className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div
      className={`group/item relative flex items-center rounded-lg transition-colors ${
        active ? "bg-white/[0.07]" : "hover:bg-white/[0.04]"
      }`}
    >
      <button
        onClick={onSelect}
        className="flex-1 truncate py-2 pl-3 pr-2 text-left text-sm text-ink-soft"
        title={conversation.title}
      >
        <span className="truncate">{conversation.title}</span>
      </button>
      <div
        className={`absolute right-1 flex items-center gap-0.5 pl-4 ${
          active ? "opacity-100" : "opacity-0 group-hover/item:opacity-100"
        } bg-gradient-to-l from-[#0c0d14] via-[#0c0d14] to-transparent transition-opacity`}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
          aria-label="Rename conversation"
          className="rounded p-1.5 text-faint hover:text-ink"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          aria-label="Delete conversation"
          className="rounded p-1.5 text-faint hover:text-red-400"
        >
          <Trash className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({
  conversations,
  activeId,
  onNewChat,
  onSelect,
  onRename,
  onDelete,
}: {
  conversations: Conversation[];
  activeId: string;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}) {
  const { user } = useUser();
  const groups = groupConversations(conversations);

  return (
    <div className="flex h-full flex-col bg-mist">
      {/* Brand + new chat */}
      <div className="flex flex-col gap-3 p-3">
        <div className="flex items-center gap-2 px-1 pt-1 font-display text-base font-bold tracking-tight">
          CodeGrok
        </div>
        <button
          onClick={onNewChat}
          className="glass group flex w-full items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-medium text-ink transition-all hover:border-white/30 hover:bg-white/[0.06]"
        >
          <Plus className="h-4 w-4 transition-transform group-hover:rotate-90" />
          New chat
        </button>
      </div>

      {/* Conversation list */}
      <nav className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        {conversations.length === 0 && (
          <p className="px-3 py-6 text-center text-sm text-faint">No conversations yet.</p>
        )}
        {groups.map(({ group, items }) => (
          <div key={group} className="mb-4">
            <p className="mono-label px-3 pb-1.5 pt-2 text-[0.62rem]">{group}</p>
            <div className="flex flex-col gap-0.5">
              {items.map((c) => (
                <ConversationItem
                  key={c.id}
                  conversation={c}
                  active={c.id === activeId}
                  onSelect={() => onSelect(c.id)}
                  onRename={(title) => onRename(c.id, title)}
                  onDelete={() => onDelete(c.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User / settings pinned at bottom */}
      <div className="border-t border-white/[0.06] p-3">
        <div className="glass flex items-center gap-3 rounded-xl px-3 py-2">
          <UserButton
            appearance={{ elements: { avatarBox: "h-7 w-7" } }}
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">
              {user?.fullName ?? user?.username ?? "Your account"}
            </p>
            <p className="truncate text-xs text-faint">
              {user?.primaryEmailAddress?.emailAddress ?? "Manage settings"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
