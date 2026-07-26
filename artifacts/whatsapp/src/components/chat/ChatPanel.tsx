import { useEffect, useRef, useState } from "react";
import {
  ChatSummary, SessionUser,
  useGetChatMessages, useSendMessage, useMarkChatRead,
  getGetChatMessagesQueryKey, getListChatsQueryKey
} from "@workspace/api-client-react";
import { Avatar } from "@/components/ui/avatar";
import { ArrowLeft, MoreVertical, Search, Smile, Send, Check, CheckCheck, Users } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";

interface ChatPanelProps {
  chatId: string;
  session: SessionUser;
  chatSummary?: ChatSummary;
  onBack: () => void;
}

export function ChatPanel({ chatId, session, chatSummary, onBack }: ChatPanelProps) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: messages = [] } = useGetChatMessages(chatId, {
    query: {
      enabled: !!chatId,
      queryKey: getGetChatMessagesQueryKey(chatId),
      refetchInterval: 2000,
    }
  });

  const markRead = useMarkChatRead();
  const markReadFnRef = useRef(markRead.mutate);
  markReadFnRef.current = markRead.mutate;

  useEffect(() => {
    if (chatId) {
      markReadFnRef.current({ chatId });
      queryClient.invalidateQueries({ queryKey: getListChatsQueryKey() });
    }
  }, [chatId, messages.length, queryClient]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMsg = useSendMessage();

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) return;
    setContent("");
    sendMsg.mutate(
      { chatId, data: { content: trimmed, senderId: session.id } },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: getGetChatMessagesQueryKey(chatId) });
          queryClient.invalidateQueries({ queryKey: getListChatsQueryKey() });
          inputRef.current?.focus();
        },
        onError: () => setContent(trimmed),
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const otherParticipant = chatSummary?.participants.find(p => p.id !== session.id);
  const name = chatSummary?.isGroup ? chatSummary.name : otherParticipant?.name || "Unbekannt";
  const avatarColor = chatSummary?.isGroup ? "#CC5500" : otherParticipant?.color;
  const avatarFallback = name.charAt(0).toUpperCase();

  let currentDate = "";

  return (
    <div className="flex-1 flex flex-col h-full bg-[#efeae2] relative pcrp-bg-pattern min-w-0">

      {/* Header */}
      <div className="h-[59px] bg-[#f5f0eb] flex items-center justify-between px-3 z-10 border-l border-[#e0d5cc] shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          {/* Back button — always visible, essential on mobile */}
          <button
            onClick={onBack}
            className="p-1.5 rounded-full hover:bg-[#e9ddd5] transition-colors text-[#54656f] shrink-0 md:hidden"
            aria-label="Zurück"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div className="cursor-pointer flex items-center gap-3 min-w-0">
            <Avatar fallback={avatarFallback} bgColor={avatarColor} />
            <div className="min-w-0">
              <h2 className="text-[#1a1a1a] font-semibold text-[15px] leading-tight truncate">{name}</h2>
              <p className="text-[#888] text-[12px] truncate max-w-[200px] md:max-w-[400px]">
                {chatSummary?.isGroup
                  ? <span className="flex items-center gap-1"><Users className="w-3 h-3" />{chatSummary.participants.map(p => p.name).join(", ")}</span>
                  : "Tippe für mehr Infos"}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 text-[#54656f] shrink-0">
          <Search className="w-5 h-5 cursor-pointer hover:text-[#CC5500] transition-colors" />
          <MoreVertical className="w-5 h-5 cursor-pointer hover:text-[#CC5500] transition-colors" />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-[4%] py-4 z-10 custom-scrollbar">
        <div className="flex flex-col gap-0.5 max-w-[900px] mx-auto">
          {messages.map((msg, index) => {
            const msgDate = new Date(msg.createdAt).toLocaleDateString("de-DE");
            const showDate = currentDate !== msgDate;
            currentDate = msgDate;

            const isMine = msg.senderId === session.id;
            const prevMsg = index > 0 ? messages[index - 1] : null;
            const groupBreak = !prevMsg || prevMsg.senderId !== msg.senderId;

            return (
              <div key={msg.id} className="flex flex-col">
                {showDate && (
                  <div className="flex justify-center my-4">
                    <span className="bg-white/90 text-[#777] text-xs px-3 py-1.5 rounded-lg shadow-sm font-medium">
                      {new Date(msg.createdAt).toLocaleDateString("de-DE", {
                        day: "numeric", month: "long", year: "numeric"
                      })}
                    </span>
                  </div>
                )}

                <div className={cn(
                  "flex max-w-[85%] md:max-w-[65%]",
                  isMine ? "self-end" : "self-start",
                  groupBreak ? "mt-2" : "mt-[2px]"
                )}>
                  <div className={cn(
                    "px-[9px] py-[6px] rounded-lg shadow-sm relative text-[14.2px] leading-[19px] text-[#1a1a1a]",
                    isMine
                      ? "bg-[#ffe8d6] rounded-tr-none"
                      : "bg-white rounded-tl-none"
                  )}>
                    {/* Sender name in group */}
                    {!isMine && chatSummary?.isGroup && (
                      <div
                        className="text-[12px] font-semibold mb-0.5"
                        style={{ color: msg.senderColor || "#CC5500" }}
                      >
                        {msg.senderName}
                      </div>
                    )}

                    <span className="break-words mr-14 block min-h-[20px] whitespace-pre-wrap">
                      {msg.content}
                    </span>

                    {/* Timestamp + read receipts */}
                    <div className="absolute bottom-[5px] right-[7px] flex items-center gap-0.5 h-[14px]">
                      <span className="text-[10.5px] text-[#888] leading-none whitespace-nowrap">
                        {new Date(msg.createdAt).toLocaleTimeString("de-DE", {
                          hour: "2-digit", minute: "2-digit"
                        })}
                      </span>
                      {isMine && (
                        msg.readBy.length > 1
                          ? <CheckCheck className="w-[14px] h-[14px] text-[#CC5500]" />
                          : <Check className="w-[14px] h-[14px] text-[#aaa]" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="min-h-[62px] bg-[#f5f0eb] px-3 py-2.5 flex items-end gap-3 z-10 shrink-0 border-t border-[#e0d5cc]">
        <div className="flex gap-3 mb-2 text-[#888] shrink-0">
          <Smile className="w-[26px] h-[26px] cursor-pointer hover:text-[#CC5500] transition-colors" />
        </div>

        <form onSubmit={handleSend} className="flex-1 flex min-h-[42px]">
          <input
            ref={inputRef}
            type="text"
            placeholder="Nachricht schreiben"
            className="w-full bg-white rounded-xl px-4 outline-none text-[#1a1a1a] placeholder:text-[#aaa] text-[15px] border border-[#e0d5cc] focus:border-[#CC5500] transition-colors"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </form>

        <div className="mb-2 shrink-0">
          <button
            onClick={() => handleSend()}
            className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center transition-all",
              content.trim()
                ? "bg-[#CC5500] text-white hover:bg-[#a34400] shadow-md"
                : "text-[#aaa] cursor-default"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
