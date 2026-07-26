import { useState } from "react";
import { useListUsers, useCreateChat, SessionUser, User, getListChatsQueryKey } from "@workspace/api-client-react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, Search, Users, ArrowRight, Check } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { useQueryClient } from "@tanstack/react-query";

export function NewChatDialog({
  session,
  onClose,
  onChatCreated,
}: {
  session: SessionUser;
  onClose: () => void;
  onChatCreated: (chatId: string) => void;
}) {
  const queryClient = useQueryClient();
  const { data: users = [] } = useListUsers();
  const createChat = useCreateChat();

  const [search, setSearch] = useState("");
  const [isGroupMode, setIsGroupMode] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);

  const availableUsers = users.filter(
    u => u.id !== session.id && u.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleUserClick = (user: User) => {
    if (isGroupMode) {
      setSelectedUsers(prev =>
        prev.some(u => u.id === user.id)
          ? prev.filter(u => u.id !== user.id)
          : [...prev, user]
      );
    } else {
      startChat([user.id], false);
    }
  };

  const startChat = (participantIds: string[], isGroup: boolean) => {
    createChat.mutate(
      { data: { participantIds, isGroup, name: isGroup ? groupName : undefined } },
      {
        onSuccess: (chat) => {
          queryClient.invalidateQueries({ queryKey: getListChatsQueryKey() });
          onChatCreated(chat.id);
        },
      }
    );
  };

  const handleCreateGroup = () => {
    if (selectedUsers.length > 0 && groupName.trim()) {
      startChat(selectedUsers.map(u => u.id), true);
    }
  };

  return (
    <Dialog.Root open={true} onOpenChange={open => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] w-[calc(100vw-2rem)] max-w-[400px] h-[80vh] max-h-[600px] bg-white rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden animate-in fade-in zoom-in-95">

          {/* Dialog header */}
          <div className="bg-[#CC5500] text-white flex items-center h-[60px] px-4 shrink-0">
            <button onClick={onClose} className="mr-4 hover:bg-white/10 p-1.5 rounded-full transition-colors">
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-[16px] font-semibold">
              {isGroupMode ? "Gruppenmitglieder wählen" : "Neuer Chat"}
            </h2>
          </div>

          {/* Group name input */}
          {isGroupMode && (
            <div className="p-4 border-b border-[#e9edef] bg-[#f5f0eb]">
              <input
                type="text"
                placeholder="Gruppenname eingeben"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="w-full bg-white px-3 py-2 border-b-2 border-[#CC5500] outline-none text-[15px] rounded-t-sm"
                autoFocus
              />
              {selectedUsers.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {selectedUsers.map(u => (
                    <div key={u.id} className="bg-[#ffe8d6] rounded-full flex items-center px-2 py-1 text-xs border border-[#CC5500]/20">
                      <Avatar fallback={u.name.charAt(0)} bgColor={u.color} className="w-5 h-5 mr-1.5" />
                      <span className="text-[#4a3728]">{u.name}</span>
                      <X className="w-3 h-3 ml-1.5 cursor-pointer text-[#CC5500]" onClick={() => handleUserClick(u)} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Search (direct chat mode) */}
          {!isGroupMode && (
            <div className="p-2 border-b border-[#e9edef]">
              <div className="bg-[#f5f0eb] rounded-lg flex items-center px-3 h-[35px]">
                <Search className="w-4 h-4 text-[#888] mr-2" />
                <input
                  type="text"
                  placeholder="Spieler suchen"
                  className="bg-transparent border-none outline-none w-full text-sm placeholder:text-[#888]"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  autoFocus
                />
              </div>
            </div>
          )}

          {/* User list */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {!isGroupMode && search === "" && (
              <div
                className="flex items-center px-4 py-3 cursor-pointer hover:bg-[#faf5f0] transition-colors"
                onClick={() => setIsGroupMode(true)}
              >
                <div className="bg-[#CC5500] w-[49px] h-[49px] rounded-full flex items-center justify-center mr-3 text-white shadow-sm shrink-0">
                  <Users className="w-6 h-6" />
                </div>
                <span className="text-[16px] text-[#1a1a1a]">Neue Gruppe erstellen</span>
              </div>
            )}

            <div className="px-4 py-2 text-[#CC5500] text-xs font-semibold uppercase tracking-wide">
              PCRP Spieler
            </div>

            {availableUsers.map(user => {
              const isSelected = selectedUsers.some(u => u.id === user.id);
              return (
                <div
                  key={user.id}
                  className="flex items-center px-4 py-3 cursor-pointer hover:bg-[#faf5f0] transition-colors active:bg-[#f5ece4]"
                  onClick={() => handleUserClick(user)}
                >
                  <div className="relative mr-3 shrink-0">
                    <Avatar fallback={user.name.charAt(0).toUpperCase()} bgColor={user.color} className="w-[49px] h-[49px]" />
                    {isGroupMode && isSelected && (
                      <div className="absolute -bottom-1 -right-1 bg-[#CC5500] text-white rounded-full p-0.5 border-2 border-white">
                        <Check className="w-3 h-3" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 border-b border-[#f0ece8] py-3 -my-3 h-[72px] flex items-center min-w-0">
                    <span className="text-[16px] text-[#1a1a1a] truncate">{user.name}</span>
                  </div>
                </div>
              );
            })}

            {availableUsers.length === 0 && (
              <div className="p-8 text-center text-[#aaa] text-sm">
                {search ? `Kein Spieler gefunden für "${search}".` : "Keine weiteren Spieler verfügbar."}
              </div>
            )}
          </div>

          {/* Group create button */}
          {isGroupMode && (
            <div className="bg-[#f5f0eb] p-4 flex justify-center shrink-0 border-t border-[#e0d5cc]">
              <button
                onClick={handleCreateGroup}
                disabled={selectedUsers.length === 0 || !groupName.trim() || createChat.isPending}
                className="bg-[#CC5500] text-white rounded-full p-4 hover:bg-[#a34400] transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
              >
                <ArrowRight className="w-6 h-6" />
              </button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
