import { useState } from "react";
import { ChatSummary, SessionUser } from "@workspace/api-client-react";
import { Avatar } from "@/components/ui/avatar";
import { MessageSquarePlus, MoreVertical, Search, LogOut } from "lucide-react";
import { ChatList } from "./ChatList";
import { NewChatDialog } from "./NewChatDialog";
import { useLocation } from "wouter";

interface SidebarProps {
  session: SessionUser;
  chats: ChatSummary[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
}

export function Sidebar({ session, chats, activeChatId, onSelectChat }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);
  const [, setLocation] = useLocation();

  const filteredChats = chats.filter(chat => {
    if (!searchQuery) return true;
    const name = chat.isGroup
      ? chat.name
      : chat.participants.find(p => p.id !== session.id)?.name || "";
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleLogout = async () => {
    try {
      await fetch(`${import.meta.env.BASE_URL}api/session`, { method: "DELETE" });
    } catch {}
    setLocation("/");
    window.location.reload();
  };

  return (
    <div className="w-full md:w-[360px] md:min-w-[300px] md:max-w-[400px] h-full flex flex-col border-r border-[#e9edef] bg-white shrink-0">
      {/* Header */}
      <div className="h-[59px] bg-[#f5f0eb] flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <Avatar
            fallback={session.name.charAt(0).toUpperCase()}
            bgColor={session.color}
          />
          <span className="text-[#1a1a1a] text-sm font-medium truncate max-w-[120px]">
            {session.name}
          </span>
        </div>
        <div className="flex items-center gap-1 text-[#54656f]">
          <button
            title="Neuer Chat"
            className="p-2 rounded-full hover:bg-[#e9ddd5] transition-colors"
            onClick={() => setIsNewChatOpen(true)}
          >
            <MessageSquarePlus className="w-5 h-5" />
          </button>
          <div className="relative group">
            <button className="p-2 rounded-full hover:bg-[#e9ddd5] transition-colors">
              <MoreVertical className="w-5 h-5" />
            </button>
            <div className="absolute right-0 top-full mt-1 bg-white shadow-lg rounded-md py-1 min-w-[140px] z-50 hidden group-focus-within:block group-hover:block">
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-[#333] hover:bg-[#f5f0eb] transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Abmelden
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="p-2 bg-white border-b border-[#e9edef]">
        <div className="bg-[#f5f0eb] rounded-lg flex items-center px-3 h-[35px]">
          <Search className="w-4 h-4 text-[#888] mr-2 shrink-0" />
          <input
            type="text"
            placeholder="Suche oder neuer Chat"
            className="bg-transparent border-none outline-none w-full text-sm placeholder:text-[#888]"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto bg-white custom-scrollbar">
        <ChatList
          chats={filteredChats}
          currentUserId={session.id}
          activeChatId={activeChatId}
          onSelectChat={onSelectChat}
        />
      </div>

      {isNewChatOpen && (
        <NewChatDialog
          session={session}
          onClose={() => setIsNewChatOpen(false)}
          onChatCreated={(chatId) => {
            setIsNewChatOpen(false);
            onSelectChat(chatId);
          }}
        />
      )}
    </div>
  );
}
