import { useRef, useCallback, useEffect } from "react";
import TerminalCard from "../../../widgets/TerminalCard";
import { Conversation } from "../types";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSwitchConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onClose: () => void;
  onCreateNew: () => void;
  isLoading?: boolean;
  onLoadMore: () => void;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
}

export const ConversationList = ({
  conversations,
  activeConversationId,
  onSwitchConversation,
  onDeleteConversation,
  onClose,
  onCreateNew,
  isLoading = false,
  onLoadMore,
  hasNextPage,
  isFetchingNextPage,
}: ConversationListProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Handle scroll to detect when to load more
  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;

    // Load more when user scrolls to 90% of the container
    if (scrollPercentage > 0.9 && hasNextPage && !isFetchingNextPage) {
      onLoadMore();
    }
  }, [hasNextPage, isFetchingNextPage, onLoadMore]);

  useEffect(() => {
    const scrollElement = scrollRef.current;
    if (scrollElement) {
      scrollElement.addEventListener("scroll", handleScroll);
      return () => scrollElement.removeEventListener("scroll", handleScroll);
    }
  }, [handleScroll]);
  return (
    <div className="mb-4">
      <TerminalCard className="p-4">
        <div className="space-y-2">
          <div className="terminal-text mb-3">
            &gt; SELECT SESSION OR CREATE NEW ({conversations.length} SESSIONS):
          </div>
          <button
            onClick={onCreateNew}
            className="w-full btn-terminal-small mb-3 text-center"
          >
            [+ CREATE NEW SESSION]
          </button>
          <div ref={scrollRef} className="max-h-60 overflow-y-auto space-y-2">
            {isLoading && conversations.length === 0 ? (
              <div className="terminal-text-muted text-center py-4">
                &gt; LOADING SESSIONS... *WHIRRRR*
              </div>
            ) : conversations.length === 0 ? (
              <div className="terminal-text-muted text-center py-4">
                &gt; NO ACTIVE SESSIONS FOUND
              </div>
            ) : (
              <>
                {conversations.map((conv, index) => (
                  <ConversationListItem
                    key={conv.id || `conversation-${index}`}
                    conversation={conv}
                    isActive={conv.id === activeConversationId}
                    onSelect={() => onSwitchConversation(conv.id)}
                    onDelete={() => onDeleteConversation(conv.id)}
                  />
                ))}
                {isFetchingNextPage && (
                  <div className="terminal-text-muted text-center py-2">
                    &gt; LOADING MORE... *BEEP*
                  </div>
                )}
                {!hasNextPage && conversations.length > 0 && (
                  <div className="terminal-text-muted text-center py-2 text-xs">
                    &gt; END OF SESSIONS
                  </div>
                )}
              </>
            )}
          </div>
          <button onClick={onClose} className="btn-terminal-small mt-3">
            [CLOSE]
          </button>
        </div>
      </TerminalCard>
    </div>
  );
};

interface ConversationListItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

const ConversationListItem = ({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: ConversationListItemProps) => {
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  return (
    <div
      className={`conversation-item ${isActive ? "active" : ""}`}
      onClick={onSelect}
    >
      <div className="flex-1 min-w-0">
        <div className="terminal-text text-sm truncate">
          {conversation.title}
        </div>
        <div className="terminal-text-muted text-xs mt-1">
          {conversation.lastActivity.toLocaleTimeString()} •{" "}
          {Math.max(0, conversation.messages.length - 1)} messages
        </div>
      </div>
      <div className="flex items-center gap-2">
        {isActive && <span className="status-indicator"></span>}
        <button
          onClick={handleDeleteClick}
          className="conversation-delete"
          title="Delete conversation"
        >
          [DEL]
        </button>
      </div>
    </div>
  );
};
