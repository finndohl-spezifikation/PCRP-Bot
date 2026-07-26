import { ChatSummary } from "@workspace/api-client-react";
import { Avatar } from "@/components/ui/avatar";
import { formatTime, cn } from "@/lib/utils";
import { Check, CheckCheck, Users } from "lucide-react";

interface ChatListProps {
  chats: ChatSummary[];
  currentUserId: string;
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
}

export function ChatList({ chats, currentUserId, activeChatId, onSelectChat }: ChatListProps) {
  if (chats.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[#999] text-sm py-16 gap-3">
        <div className="w-12 h-12 rounded-full bg-[#f5f0eb] flex items-center justify-center">
          <Users className="w-6 h-6 text-[#CC5500] opacity-60" />
        </div>
        <p>Noch keine Chats vorhanden.</p>
        <p className="text-xs text-[#bbb]">Erstelle einen neuen Chat oben rechts.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {chats.map(chat => {
        const otherParticipant = chat.participants.find(p => p.id !== currentUserId);
        const name = chat.isGroup ? chat.name : otherParticipant?.name || "Unbekannt";
        const avatarColor = chat.isGroup ? "#CC5500" : otherParticipant?.color;
        const avatarFallback = chat.isGroup ? name.charAt(0).toUpperCase() : name.charAt(0).toUpperCase();

        const isUnread = chat.unreadCount > 0;
        const isActive = activeChatId === chat.id;

        return (
          <div
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={cn(
              "flex items-center px-3 cursor-pointer hover:bg-[#faf5f0] transition-colors active:bg-[#f5ece4]",
              isActive && "bg-[#f5f0eb] hover:bg-[#f5f0eb]"
            )}
          >
            <Avatar
              fallback={avatarFallback}
              bgColor={avatarColor}
              className="mr-3 w-[49px] h-[49px] shrink-0"
            />

            <div className="flex-1 flex flex-col justify-center border-b border-[#f0ecE8] py-3 pr-2 min-w-0 h-[72px]">
              <div className="flex justify-between items-center mb-0.5">
                <span className="text-[16px] text-[#1a1a1a] truncate font-medium">{name}</span>
                {chat.lastMessage && (
                  <span className={cn(
                    "text-[12px] whitespace-nowrap ml-2 shrink-0",
                    isUnread ? "text-[#CC5500] font-semibold" : "text-[#999]"
                  )}>
                    {formatTime(chat.lastMessage.createdAt)}
                  </span>
                )}
              </div>

              <div className="flex justify-between items-center">
                <div className="flex items-center text-sm text-[#999] truncate pr-2 min-w-0">
                  {chat.lastMessage?.senderId === currentUserId && (
                    <span className="mr-1 shrink-0">
                      {chat.lastMessage.readBy.length > 1
                        ? <CheckCheck className="w-[16px] h-[16px] text-[#CC5500]" />
                        : <Check className="w-[16px] h-[16px] text-[#aaa]" />
                      }
                    </span>
                  )}
                  <span className="truncate text-[13px]">
                    {chat.lastMessage
                      ? (chat.isGroup && chat.lastMessage.senderId !== currentUserId
                          ? `${chat.lastMessage.senderName}: ${chat.lastMessage.content}`
                          : chat.lastMessage.content)
                      : "Noch keine Nachrichten"}
                  </span>
                </div>

                {isUnread && (
                  <div className="bg-[#CC5500] text-white text-[11px] font-bold rounded-full min-w-[20px] h-[20px] flex items-center justify-center px-1 shrink-0">
                    {chat.unreadCount > 99 ? "99+" : chat.unreadCount}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
