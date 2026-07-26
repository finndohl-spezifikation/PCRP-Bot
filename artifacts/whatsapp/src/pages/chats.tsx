import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { useGetSession, useListChats } from "@workspace/api-client-react";
import { AppContainer } from "@/components/layout/AppContainer";
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { EmptyChat } from "@/components/chat/EmptyChat";

export default function Chats() {
  const [, setLocation] = useLocation();
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  const { data: session, isLoading: sessionLoading, isError: sessionError } = useGetSession({
    query: { retry: false }
  });

  useEffect(() => {
    if (sessionError) setLocation("/");
  }, [sessionError, setLocation]);

  const { data: chats = [] } = useListChats({
    query: {
      refetchInterval: 2000,
      enabled: !!session
    }
  });

  if (sessionLoading) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-[#f5f0eb]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-[#CC5500] border-t-transparent rounded-full animate-spin" />
          <p className="text-[#666] text-sm">Verbinde...</p>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const showSidebar = !activeChatId;
  const showChat = !!activeChatId;

  return (
    <AppContainer>
      {/* On mobile: show either sidebar OR chat. On desktop: show both. */}
      <div className={`${showSidebar ? "flex" : "hidden"} md:flex w-full md:w-auto md:min-w-0`}>
        <Sidebar
          session={session}
          chats={chats}
          activeChatId={activeChatId}
          onSelectChat={setActiveChatId}
        />
      </div>

      {showChat ? (
        <ChatPanel
          chatId={activeChatId}
          session={session}
          chatSummary={chats.find(c => c.id === activeChatId)}
          onBack={() => setActiveChatId(null)}
        />
      ) : (
        <EmptyChat />
      )}
    </AppContainer>
  );
}
