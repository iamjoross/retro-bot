import { useState, KeyboardEvent } from "react";
import TerminalCard from "../../../widgets/TerminalCard";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const MessageInput = ({
  onSendMessage,
  isLoading,
  disabled = false,
}: MessageInputProps) => {
  const [inputMessage, setInputMessage] = useState("");

  const handleSendMessage = () => {
    if (!inputMessage.trim() || isLoading || disabled) return;

    onSendMessage(inputMessage);
    setInputMessage("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  const isDisabled = isLoading || disabled;
  const placeholder = disabled ? "No active session" : "Enter command...";

  return (
    <div className="mt-4">
      <TerminalCard className="p-4">
        <div className="flex gap-3 items-stretch">
          <div className="flex-1 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-400/60">
              &gt;
            </span>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="input-terminal h-12"
              disabled={isDisabled}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={isDisabled || !inputMessage.trim()}
            className="btn-terminal px-6 h-12"
          >
            {isLoading ? "[WAIT]" : "[SEND]"}
          </button>
        </div>
      </TerminalCard>
    </div>
  );
};
