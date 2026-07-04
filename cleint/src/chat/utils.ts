import type { Conversation, DateGroup, Message } from "./types";

export const uid = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;

export function makeMessage(
  role: Message["role"],
  content: string,
): Message {
  return { id: uid(), role, content, createdAt: Date.now() };
}

export function makeConversation(title = "New chat"): Conversation {
  const now = Date.now();
  return { id: uid(), title, messages: [], createdAt: now, updatedAt: now };
}

/** Derive a short title from the first user message. */
export function deriveTitle(text: string): string {
  const clean = text.trim().replace(/\s+/g, " ");
  if (!clean) return "New chat";
  return clean.length > 48 ? `${clean.slice(0, 48)}…` : clean;
}

const startOfDay = (d: number) => {
  const date = new Date(d);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
};

/** Bucket a timestamp into a human date group. */
export function dateGroupFor(ts: number): DateGroup {
  const today = startOfDay(Date.now());
  const day = 86_400_000;
  const t = startOfDay(ts);
  if (t >= today) return "Today";
  if (t >= today - day) return "Yesterday";
  if (t >= today - day * 7) return "Previous 7 Days";
  return "Older";
}

const GROUP_ORDER: DateGroup[] = [
  "Today",
  "Yesterday",
  "Previous 7 Days",
  "Older",
];

/** Group conversations (newest first) into ordered date buckets. */
export function groupConversations(
  conversations: Conversation[],
): { group: DateGroup; items: Conversation[] }[] {
  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt);
  const buckets = new Map<DateGroup, Conversation[]>();
  for (const c of sorted) {
    const g = dateGroupFor(c.updatedAt);
    const arr = buckets.get(g) ?? [];
    arr.push(c);
    buckets.set(g, arr);
  }
  return GROUP_ORDER.filter((g) => buckets.has(g)).map((group) => ({
    group,
    items: buckets.get(group)!,
  }));
}
