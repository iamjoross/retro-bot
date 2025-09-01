import { ReactNode } from "react";

interface RetroLayoutProps {
  children: ReactNode;
}

export default function RetroLayout({ children }: RetroLayoutProps) {
  return (
    <div className="retro-container">
      {/* Subtle CRT effect overlay */}
      <div className="crt-scanlines" />

      {/* Main content */}
      <div className="relative">{children}</div>

      {/* Optional footer with system status */}
      <div className="fixed bottom-0 left-0 right-0 p-2 text-center bg-gray-900/50 backdrop-blur-sm z-40">
        <span className="terminal-text-muted">
          DATACOM-7 SYSTEM • 1978 MAINFRAME • SESSION ACTIVE
        </span>
      </div>
    </div>
  );
}
