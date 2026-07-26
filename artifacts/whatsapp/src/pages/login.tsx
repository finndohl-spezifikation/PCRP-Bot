import { useState } from "react";
import { useLocation } from "wouter";
import { AppContainer } from "@/components/layout/AppContainer";
import { useCreateSession } from "@workspace/api-client-react";
import { toast } from "sonner";

export default function Login() {
  const [name, setName] = useState("");
  const [, setLocation] = useLocation();

  const createSession = useCreateSession();

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    createSession.mutate(
      { data: { name: name.trim() } },
      {
        onSuccess: () => setLocation("/chats"),
        onError: () => toast.error("Verbindung fehlgeschlagen. Bitte erneut versuchen."),
      }
    );
  };

  return (
    <AppContainer>
      <div className="flex-1 flex flex-col items-center justify-center bg-[#f5f0eb] w-full px-4">
        {/* Logo */}
        <div className="mb-10 flex flex-col items-center gap-3">
          <div className="w-20 h-20 rounded-full bg-[#CC5500] flex items-center justify-center shadow-lg">
            <svg viewBox="0 0 48 48" fill="none" className="w-11 h-11">
              <path d="M24 4C12.95 4 4 12.95 4 24c0 3.73 1.02 7.22 2.8 10.22L4 44l10.1-2.74A19.88 19.88 0 0024 44c11.05 0 20-8.95 20-20S35.05 4 24 4z" fill="white"/>
              <path d="M17 15h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-4 4v-4h-5a2 2 0 01-2-2v-8a2 2 0 012-2z" fill="#CC5500"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[#1a1a1a] tracking-tight">PCRP Chat</h1>
          <p className="text-sm text-[#666] text-center">Paradise City Roleplay</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm w-full max-w-[380px] border border-[#e8ddd5]">
          <h2 className="text-lg text-[#1a1a1a] font-semibold mb-1 text-center">Willkommen!</h2>
          <p className="text-sm text-[#666] text-center mb-6">Gib deinen Ingame-Namen ein um fortzufahren.</p>

          <form onSubmit={handleJoin} className="flex flex-col gap-4">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="z.B. Max Müller"
              className="w-full border-b-2 border-[#CC5500] bg-[#faf7f4] px-4 py-3 outline-none rounded-t-md text-[15px] placeholder:text-[#aaa] focus:bg-[#f5f0eb] transition-colors"
              autoFocus
              maxLength={32}
            />

            <button
              type="submit"
              disabled={createSession.isPending || !name.trim()}
              className="bg-[#CC5500] hover:bg-[#a34400] text-white font-semibold py-3 rounded-full transition-colors disabled:opacity-50 text-[15px] mt-2 shadow-sm"
            >
              {createSession.isPending ? "Verbinde..." : "Chat beitreten"}
            </button>
          </form>
        </div>

        <p className="text-xs text-[#999] mt-6 text-center max-w-[300px]">
          Durch das Beitreten stimmst du den Server-Regeln von PCRP zu.
        </p>
      </div>
    </AppContainer>
  );
}
