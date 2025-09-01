/**
 * Conversation Mutations
 * TanStack Query mutations for conversation data modification
 */

import {
  useMutation,
  useQueryClient,
  UseMutationOptions,
} from "@tanstack/react-query";
import { httpClient, APIError } from "../client/httpClient";
import { API_CONFIG } from "../client/config";
import { conversationKeys } from "../queries/queryKeys";
import {
  Conversation,
  ConversationUpdateRequest,
  ChatRequest,
  ChatResponse,
} from "../types/conversation";

/**
 * Create a new conversation with cache management:
 * - Invalidates conversation lists and stats
 * - Adds new conversation to cache
 */
export const useCreateConversationMutation = (
  options?: UseMutationOptions<Conversation, APIError, void>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<Conversation> => {
      return httpClient.post<Conversation>(API_CONFIG.ENDPOINTS.CONVERSATIONS);
    },
    onSuccess: (newConversation) => {
      queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });

      queryClient.setQueryData(
        conversationKeys.detail(newConversation.id),
        newConversation
      );

      queryClient.invalidateQueries({
        queryKey: conversationKeys.stats(),
      });
    },
    onError: (error) => {
      console.error("Failed to create conversation:", error);
    },
    ...options,
  });
};

/**
 * Update conversation (currently supports title updates) with cache synchronization:
 * - Updates specific conversation in cache
 * - Refreshes conversation lists
 */
export const useUpdateConversationMutation = (
  options?: UseMutationOptions<
    Conversation,
    APIError,
    { conversationId: string; updates: ConversationUpdateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ conversationId, updates }): Promise<Conversation> => {
      return httpClient.patch<Conversation>(
        API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(conversationId),
        updates
      );
    },
    onSuccess: (updatedConversation, { conversationId }) => {
      queryClient.setQueryData(
        conversationKeys.detail(conversationId),
        updatedConversation
      );

      queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });
    },
    onError: (error) => {
      console.error("Failed to update conversation:", error);
    },
    ...options,
  });
};

/**
 * Delete a conversation with complete cache cleanup:
 * - Removes conversation from cache
 * - Updates conversation lists and stats
 */
export const useDeleteConversationMutation = (
  options?: UseMutationOptions<{ message: string }, APIError, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      conversationId: string
    ): Promise<{ message: string }> => {
      return httpClient.delete<{ message: string }>(
        API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(conversationId)
      );
    },
    onSuccess: (_, conversationId) => {
      queryClient.removeQueries({
        queryKey: conversationKeys.detail(conversationId),
      });

      queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });

      queryClient.invalidateQueries({
        queryKey: conversationKeys.stats(),
      });
    },
    onError: (error) => {
      console.error("Failed to delete conversation:", error);
    },
    ...options,
  });
};

/**
 * Send a chat message with conversation updates:
 * - Refetches conversation with new messages
 * - Updates conversation list activity
 */
export const useSendChatMessageMutation = (
  options?: UseMutationOptions<ChatResponse, APIError, ChatRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chatRequest: ChatRequest): Promise<ChatResponse> => {
      return httpClient.post<ChatResponse>(
        API_CONFIG.ENDPOINTS.CHAT,
        chatRequest,
        { timeout: API_CONFIG.TIMEOUTS.CHAT }
      );
    },
    onSuccess: (_, request) => {
      queryClient.invalidateQueries({
        queryKey: conversationKeys.detail(request.conversation_id!),
      });

      queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });
    },
    onError: (error) => {
      console.error("Failed to send chat message:", error);
    },
    ...options,
  });
};

/**
 * Optimistic update for chat messages providing immediate UI feedback:
 * - Shows user message instantly before API response
 * - Handles rollback on errors
 * - Ensures data consistency with refetching
 */
export const useSendChatMessageOptimisticMutation = (
  options?: UseMutationOptions<ChatResponse, APIError, ChatRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (chatRequest: ChatRequest): Promise<ChatResponse> => {
      return httpClient.post<ChatResponse>(
        API_CONFIG.ENDPOINTS.CHAT,
        chatRequest,
        { timeout: API_CONFIG.TIMEOUTS.CHAT }
      );
    },
    onMutate: async (chatRequest) => {
      const conversationId = chatRequest.conversation_id;
      if (!conversationId) return { previousConversation: undefined };

      await queryClient.cancelQueries({
        queryKey: conversationKeys.detail(conversationId),
      });

      const previousConversation = queryClient.getQueryData<Conversation>(
        conversationKeys.detail(conversationId)
      );

      if (previousConversation) {
        const optimisticConversation: Conversation = {
          ...previousConversation,
          messages: [
            ...previousConversation.messages,
            {
              role: "user",
              content: chatRequest.message,
              timestamp: new Date().toISOString(),
            },
          ],
          updated_at: new Date().toISOString(),
        };

        queryClient.setQueryData(
          conversationKeys.detail(conversationId),
          optimisticConversation
        );
      }

      return { previousConversation };
    },
    onError: (error, chatRequest, context) => {
      const conversationId = chatRequest.conversation_id;
      if (context?.previousConversation && conversationId) {
        queryClient.setQueryData(
          conversationKeys.detail(conversationId),
          context.previousConversation
        );
      }
      console.error("Failed to send chat message:", error);
    },
    onSettled: (_, __, chatRequest) => {
      const conversationId = chatRequest.conversation_id;
      if (conversationId) {
        queryClient.invalidateQueries({
          queryKey: conversationKeys.detail(conversationId),
        });
      }
    },
    ...options,
  });
};
