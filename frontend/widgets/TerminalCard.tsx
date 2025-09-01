import { ReactNode } from "react";

interface TerminalCardProps {
  children: ReactNode;
  title?: string;
  statusIndicator?: boolean;
  className?: string;
}

export default function TerminalCard({
  children,
  title,
  statusIndicator = false,
  className = "",
}: TerminalCardProps) {
  return (
    <div className={`terminal-card ${className}`}>
      {(title || statusIndicator) && (
        <div className="px-6 py-3 border-b border-emerald-400/20">
          <div className="flex items-center justify-between">
            {title && <h2 className="terminal-text">{title}</h2>}
            {statusIndicator && (
              <div className="status-online">
                <span className="status-indicator"></span>
                System Online
              </div>
            )}
          </div>
        </div>
      )}
      <div className="p-6 overflow-auto">{children}</div>
    </div>
  );
}
