import { forwardRef } from "react";
import TerminalCard from "../../../widgets/TerminalCard";
import { Message } from "../types";

interface MessageDisplayProps {
  messages: Message[];
  isLoading: boolean;
}

export const MessageDisplay = forwardRef<HTMLDivElement, MessageDisplayProps>(
  ({ messages, isLoading }, ref) => {
    return (
      <div className="flex-1 overflow-hidden">
        <TerminalCard className="h-full flex flex-col" statusIndicator={true}>
          <div className="flex-1 overflow-y-auto font-mono text-sm space-y-3 pr-2 max-h-full message-container">
            <div className="min-h-full flex flex-col justify-end">
              <div className="space-y-3">
                {messages.map((message, index) => (
                  <MessageItem key={index} message={message} />
                ))}
                {isLoading && <LoadingIndicator />}
              </div>
              <div ref={ref} />
            </div>
          </div>
        </TerminalCard>
      </div>
    );
  }
);

MessageDisplay.displayName = "MessageDisplay";

interface MessageItemProps {
  message: Message;
}

const MessageItem = ({ message }: MessageItemProps) => {
  const getMessageClassName = () => {
    switch (message.role) {
      case "system":
        return "msg-system";
      case "user":
        return "msg-user";
      case "assistant":
        return "msg-assistant";
      default:
        return "";
    }
  };

  const renderMessageContent = () => {
    switch (message.role) {
      case "system":
        return (
          <div className="text-center py-2">
            ═══════════════════════════════════════
            <div className="mt-1">{message.content}</div>
            ═══════════════════════════════════════
          </div>
        );
      case "user":
        return (
          <div className="bg-emerald-400/5 border-l-2 border-emerald-400/30 pl-3 py-2">
            <span className="text-emerald-200 font-bold">&gt; USER:</span>
            <div className="ml-4 mt-1 text-emerald-100">{message.content}</div>
          </div>
        );
      case "assistant":
        return (
          <div className="bg-gray-800/30 border-l-2 border-emerald-400 pl-3 py-2">
            <span className="text-emerald-400 font-bold">&gt; DATACOM-7:</span>
            <div className="ml-4 mt-1 text-emerald-300/90 whitespace-pre-wrap">
              {message.content}
            </div>
          </div>
        );
      default:
        return <div>{message.content}</div>;
    }
  };

  return <div className={getMessageClassName()}>{renderMessageContent()}</div>;
};

const LoadingIndicator = () => (
  <div className="text-emerald-400/60 text-xs">[PROCESSING... PLEASE WAIT]</div>
);
