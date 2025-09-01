import { useEffect, useState } from "react";
import { useAutoScrollOnChange } from "../hooks/useAutoScroll";
import { useConversationState } from "../hooks/useConversationState";
import { ConversationHeader } from "./ConversationHeader";
import { ConversationList } from "./ConversationList";
import { MessageDisplay } from "./MessageDisplay";
import { MessageInput } from "./MessageInput";

export const ConversationContainer = () => {
  const {
    activeConversation,
    conversationList,
    actions,
    isLoading,
    loadMoreConversations,
    hasNextPage,
    isFetchingNextPage,
  } = useConversationState();

  const [showConversationList, setShowConversationList] = useState(true);

  const { scrollRef } = useAutoScrollOnChange(activeConversation?.messages);

  // Show conversation list by default when no active conversation
  useEffect(() => {
    if (!activeConversation && !isLoading) {
      setShowConversationList(true);
    }
  }, [activeConversation, isLoading]);

  const handleToggleConversationList = () => {
    setShowConversationList(!showConversationList);
  };

  const handleSwitchConversation = (id: string) => {
    actions.switchToConversation(id);
    setShowConversationList(false);
  };

  const handleCloseConversationList = () => {
    setShowConversationList(false);
  };

  const handleCreateNewConversation = () => {
    actions.createNewConversation();
    setShowConversationList(false);
  };

  return (
    <div className="flex flex-col h-screen px-4 pb-12 pt-4">
      <div className="max-w-4xl w-full mx-auto flex flex-col h-full">
        <ConversationHeader
          activeConversation={activeConversation}
          conversationCount={conversationList.length}
          onNewConversation={actions.createNewConversation}
          onToggleConversationList={handleToggleConversationList}
        />

        {showConversationList && (
          <ConversationList
            conversations={conversationList}
            activeConversationId={activeConversation?.id || null}
            onSwitchConversation={handleSwitchConversation}
            onDeleteConversation={actions.deleteConversation}
            onClose={handleCloseConversationList}
            onCreateNew={handleCreateNewConversation}
            isLoading={isLoading}
            onLoadMore={loadMoreConversations}
            hasNextPage={hasNextPage}
            isFetchingNextPage={isFetchingNextPage}
          />
        )}

        <MessageDisplay
          messages={activeConversation?.messages || []}
          isLoading={isLoading}
          ref={scrollRef}
        />

        <MessageInput
          onSendMessage={actions.sendMessage}
          isLoading={isLoading}
          disabled={!activeConversation}
        />
      </div>
    </div>
  );
};
