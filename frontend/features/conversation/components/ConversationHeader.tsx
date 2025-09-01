import { useRouter } from "next/router";
import TerminalCard from "../../../widgets/TerminalCard";
import { Conversation } from "../types";

interface ConversationHeaderProps {
  activeConversation: Conversation | null;
  conversationCount: number;
  onNewConversation: () => void;
  onToggleConversationList: () => void;
}

export const ConversationHeader = ({
  activeConversation,
  conversationCount,
  onNewConversation,
  onToggleConversationList,
}: ConversationHeaderProps) => {
  const router = useRouter();

  return (
    <div className="mb-4">
      <TerminalCard className="p-4">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h1 className="terminal-subheading">
              DATACOM-7 COMMUNICATION TERMINAL
            </h1>
            <p className="terminal-text-muted mt-1">
              Session: {activeConversation?.title || "No Session"} • ID:{" "}
              {activeConversation?.id?.slice(-8).toUpperCase() || "NONE"}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onNewConversation}
              className="btn-terminal-small"
              title="Start new conversation"
            >
              [NEW]
            </button>
            <button
              onClick={onToggleConversationList}
              className="btn-terminal-small"
              title="Switch conversation"
            >
              [CONV({conversationCount})]
            </button>
            <button
              onClick={() => router.push("/")}
              className="btn-terminal-small"
            >
              [EXIT]
            </button>
          </div>
        </div>
      </TerminalCard>
    </div>
  );
};
