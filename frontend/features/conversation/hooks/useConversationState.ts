import { useCallback, useEffect, useMemo, useState } from "react";
import { InfiniteData } from "@tanstack/react-query";
import {
  API_CONFIG,
  ConversationSummary,
  httpClient,
  useCreateConversationMutation,
  useDeleteConversationMutation,
  useInfiniteConversationsQuery,
  useSendChatMessageOptimisticMutation,
} from "../../../shared/api";
import { Conversation, ConversationActions, Message } from "../types";
import {
  createErrorMessage,
  generateConversationTitle,
  mapAPIConversationSummaryToLocal,
  mapAPIConversationToLocal,
  sortConversationsByActivity,
} from "../utils/conversationUtils";

interface UseConversationStateResult {
  activeConversation: Conversation | null;
  conversationList: Conversation[];
  actions: ConversationActions;
  isLoading: boolean;
  loadMoreConversations: () => void;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
}

export const useConversationState = (): UseConversationStateResult => {
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [localConversations, setLocalConversations] = useState<
    Map<string, Conversation>
  >(new Map());

  // Fetch conversations from API with infinite scroll
  const conversationsQuery = useInfiniteConversationsQuery({});

  // Update local conversations when API data changes
  useEffect(() => {
    const infiniteData = conversationsQuery.data as InfiniteData<ConversationSummary[], number> | undefined;
    if (infiniteData?.pages) {
      const conversationMap = new Map<string, Conversation>();

      infiniteData.pages.forEach((page: ConversationSummary[]) => {
        page.forEach((apiSummary: ConversationSummary) => {
          const localConv = mapAPIConversationSummaryToLocal(apiSummary);
          if (localConv.id) {
            conversationMap.set(localConv.id, localConv);
          }
        });
      });
      setLocalConversations(conversationMap);
    }
  }, [conversationsQuery.data]);

  // Use shared API mutations
  const createConversationMutation = useCreateConversationMutation({
    onSuccess: (apiConversation) => {
      const localConversation = mapAPIConversationToLocal(apiConversation);
      localConversation.isActive = true;
      const conversationId = apiConversation.id || apiConversation._id;
      if (conversationId) {
        setLocalConversations((prev) =>
          new Map(prev).set(conversationId, localConversation)
        );
        setActiveConversationId(conversationId);
      }
      // Invalidate conversations query to refetch the list
      conversationsQuery.refetch();
    },
  });

  const deleteConversationMutation = useDeleteConversationMutation({
    onSuccess: (_, deletedId) => {
      if (deletedId === activeConversationId) {
        setActiveConversationId(null);
      }
      // Invalidate conversations query to refetch the list
      conversationsQuery.refetch();
    },
  });

  const sendMessageMutation = useSendChatMessageOptimisticMutation();

  const activeConversation = useMemo(() => {
    return activeConversationId
      ? localConversations.get(activeConversationId) || null
      : null;
  }, [activeConversationId, localConversations]);

  const conversationList = useMemo(() => {
    const conversations = Array.from(localConversations.values());
    return sortConversationsByActivity(conversations);
  }, [localConversations]);

  const createNewConversationAction = useCallback((): string => {
    const tempId = `temp_${Date.now()}`;

    createConversationMutation.mutate();

    return tempId;
  }, [createConversationMutation]);

  const switchToConversation = useCallback(async (conversationId: string) => {
    setActiveConversationId(conversationId);

    try {
      // Fetch full conversation details from API
      const fullConversation = await httpClient.get<
        import("../../../shared/api").Conversation
      >(API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(conversationId));

      const localConv = mapAPIConversationToLocal(fullConversation);
      localConv.isActive = true;
      localConv.lastActivity = new Date();

      setLocalConversations((prev) => {
        const updated = new Map(prev);
        const existingConv = updated.get(conversationId);

        // Preserve any existing messages if the API didn't return them
        if (
          existingConv &&
          localConv.messages.length === 0 &&
          existingConv.messages.length > 0
        ) {
          localConv.messages = existingConv.messages;
        }

        updated.set(conversationId, localConv);

        updated.forEach((conv, id) => {
          if (id !== conversationId) {
            conv.isActive = false;
          }
        });

        return updated;
      });
    } catch (error) {
      console.error("Failed to fetch conversation details:", error);

      setLocalConversations((prev) => {
        const updated = new Map(prev);
        const conversation = updated.get(conversationId);
        if (conversation) {
          conversation.isActive = true;
          conversation.lastActivity = new Date();

          updated.forEach((conv, id) => {
            if (id !== conversationId) {
              conv.isActive = false;
            }
          });
        }
        return updated;
      });
    }
  }, []);

  const deleteConversation = useCallback(
    (conversationId: string) => {
      deleteConversationMutation.mutate(conversationId, {
        onSuccess: () => {
          setLocalConversations((prev) => {
            const updated = new Map(prev);
            updated.delete(conversationId);

            // If we're deleting the active conversation, find a new one
            if (conversationId === activeConversationId) {
              const remaining = Array.from(updated.values());
              const sorted = sortConversationsByActivity(remaining);
              setActiveConversationId(sorted.length > 0 ? sorted[0].id : null);
            }

            return updated;
          });
        },
      });
    },
    [deleteConversationMutation, activeConversationId]
  );

  const updateConversationMessages = useCallback(
    (
      conversationId: string,
      messageOrUpdater: Message | Message[] | ((prev: Message[]) => Message[])
    ) => {
      setLocalConversations((prev) => {
        const updated = new Map(prev);
        const conversation = updated.get(conversationId);

        if (conversation) {
          if (typeof messageOrUpdater === "function") {
            conversation.messages = messageOrUpdater(conversation.messages);
          } else if (Array.isArray(messageOrUpdater)) {
            conversation.messages = messageOrUpdater;
          } else {
            conversation.messages = [
              ...conversation.messages,
              messageOrUpdater,
            ];
          }

          conversation.lastActivity = new Date();

          // Update title if it's still "New Session"
          if (conversation.title === "New Session" || !conversation.title) {
            conversation.title = generateConversationTitle(
              conversation.messages
            );
          }
        }

        return updated;
      });
    },
    []
  );

  const sendMessage = useCallback(
    async (message: string) => {
      if (!activeConversation || !message.trim()) return;

      const chatRequest = {
        message,
        conversation_id: activeConversation.id || activeConversation._id,
      };

      sendMessageMutation.mutate(chatRequest, {
        onSuccess: (response) => {
          console.log("Message sent successfully:", response);

          // Manually update the conversation with both user message and AI response
          const conversationId =
            activeConversation.id || activeConversation._id;
          if (conversationId) {
            updateConversationMessages(conversationId, (prevMessages) => [
              ...prevMessages,
              {
                role: "user" as const,
                content: message,
                timestamp: new Date().toISOString(),
              },
              {
                role: "assistant" as const,
                content: response.message,
                timestamp: response.timestamp,
              },
            ]);
          }
        },
        onError: (error) => {
          console.error("Failed to send message:", error);
          // Add error message to conversation
          const errorMessage = createErrorMessage(
            "COMMUNICATION FAILURE. PLEASE RETRY."
          );
          const conversationId =
            activeConversation.id || activeConversation._id;
          if (conversationId) {
            updateConversationMessages(conversationId, errorMessage);
          }
        },
      });
    },
    [activeConversation, sendMessageMutation, updateConversationMessages]
  );

  const actions: ConversationActions = useMemo(
    () => ({
      createNewConversation: createNewConversationAction,
      switchToConversation,
      deleteConversation,
      sendMessage,
    }),
    [
      createNewConversationAction,
      switchToConversation,
      deleteConversation,
      sendMessage,
    ]
  );

  const isLoading =
    conversationsQuery.isLoading ||
    createConversationMutation.isPending ||
    deleteConversationMutation.isPending ||
    sendMessageMutation.isPending;

  const loadMoreConversations = useCallback(() => {
    if (
      conversationsQuery.hasNextPage &&
      !conversationsQuery.isFetchingNextPage
    ) {
      conversationsQuery.fetchNextPage();
    }
  }, [conversationsQuery]);

  return {
    activeConversation,
    conversationList,
    actions,
    isLoading,
    loadMoreConversations,
    hasNextPage: conversationsQuery.hasNextPage ?? false,
    isFetchingNextPage: conversationsQuery.isFetchingNextPage,
  };
};
