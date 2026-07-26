import { ReactNode } from "react";

export function AppContainer({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[100dvh] w-full relative overflow-hidden bg-[#b5a99e]">
      {/* PCRP orange top bar — desktop only */}
      <div className="absolute top-0 left-0 right-0 h-[127px] bg-[#CC5500] z-0 hidden md:block" />

      {/* Main app window */}
      <div className="relative z-10 h-[100dvh] w-full md:py-[19px] md:px-[19px] lg:px-0 mx-auto max-w-[1600px]">
        <div className="bg-card w-full h-full shadow-xl md:rounded-sm flex overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
}
