import { Lock } from "lucide-react";

export function EmptyChat() {
  return (
    <div className="flex-1 flex-col h-full bg-[#f5f0eb] items-center justify-center border-l border-[#e0d5cc] relative hidden md:flex">
      <div className="max-w-[440px] text-center flex flex-col items-center px-6">
        {/* PCRP Chat Logo */}
        <div className="w-36 h-36 rounded-full bg-white shadow-inner border border-[#e8ddd5] flex items-center justify-center mb-8 opacity-80">
          <svg viewBox="0 0 96 96" fill="none" className="w-20 h-20">
            <circle cx="48" cy="48" r="48" fill="#fff3ec"/>
            <path d="M48 12C28.12 12 12 28.12 12 48c0 6.3 1.73 12.19 4.73 17.24L12 84l19.22-4.67A35.78 35.78 0 0048 84c19.88 0 36-16.12 36-36S67.88 12 48 12z" fill="#CC5500" opacity=".15"/>
            <path d="M48 20C30.33 20 16 34.33 16 52c0 5.5 1.51 10.66 4.14 15.06L16 76l9.28-2.26A31.83 31.83 0 0048 84c17.67 0 32-14.33 32-32S65.67 20 48 20z" fill="#CC5500" opacity=".35"/>
            <path d="M33 40h30a3 3 0 013 3v12a3 3 0 01-3 3H42l-7 7V58h-2a3 3 0 01-3-3V43a3 3 0 013-3z" fill="#CC5500"/>
          </svg>
        </div>

        <h1 className="text-[28px] font-light text-[#4a3728] mb-3">PCRP Chat</h1>
        <p className="text-[#888] text-[14px] leading-relaxed mb-8">
          Wähle links einen Chat aus oder starte einen neuen Gespräch.<br />
          Alle Nachrichten werden in Echtzeit synchronisiert.
        </p>
      </div>

      <div className="absolute bottom-8 flex items-center text-[#aaa] text-xs gap-1.5">
        <Lock className="w-3 h-3" />
        Paradise City Roleplay — PCRP Chat
      </div>
    </div>
  );
}
