import { useCallback, useState } from "react";
import Sidebar from "./Sidebar";
import ChatWindow from "./ChatWindow";
import { useConversations } from "./useConversations";

const isDesktop = () =>
  typeof window !== "undefined" && window.matchMedia("(min-width: 768px)").matches;

export default function ChatPage() {
  const chat = useConversations();
  // Open by default on desktop, closed (drawer) on mobile.
  const [sidebarOpen, setSidebarOpen] = useState(isDesktop);

  const closeOnMobile = useCallback(() => {
    if (!isDesktop()) setSidebarOpen(false);
  }, []);

  const handleSelect = useCallback(
    (id: string) => {
      chat.selectConversation(id);
      closeOnMobile();
    },
    [chat, closeOnMobile],
  );

  const handleNewChat = useCallback(() => {
    chat.newChat();
    closeOnMobile();
  }, [chat, closeOnMobile]);

  return (
    <div className="flex h-screen overflow-hidden text-ink">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar: drawer on mobile, collapsible column on desktop */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[280px] overflow-hidden border-r border-white/[0.06] transition-transform duration-300 ease-out md:relative md:z-auto md:translate-x-0 md:transition-[width] ${
          sidebarOpen
            ? "translate-x-0 md:w-[280px]"
            : "-translate-x-full md:w-0"
        }`}
      >
        <div className="h-full w-[280px]">
          <Sidebar
            conversations={chat.conversations}
            activeId={chat.activeId}
            onNewChat={handleNewChat}
            onSelect={handleSelect}
            onRename={chat.renameConversation}
            onDelete={chat.deleteConversation}
          />
        </div>
      </aside>

      {/* Main chat area */}
      <main className="min-w-0 flex-1">
        <ChatWindow
          conversation={chat.activeConversation}
          isStreaming={chat.isStreaming}
          streamingId={chat.streamingId}
          onSend={chat.sendMessage}
          onStop={chat.stopStreaming}
          onNewChat={handleNewChat}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
        />
      </main>
    </div>
  );
}
