/**
 * Shared API Layer
 * Central export point for all API-related functionality
 */

// Types
export type {
  Message,
  Conversation,
  ConversationSummary,
  ConversationListParams,
  ConversationUpdateRequest,
  ConversationStatsResponse,
  ChatRequest,
  ChatResponse,
} from "./types/conversation";

// Client
export { httpClient, APIError } from "./client/httpClient";
export { API_CONFIG } from "./client/config";
export {
  queryClient,
  createQueryClient,
  handleQueryError,
} from "./client/queryClient";
export type { RequestOptions } from "./client/httpClient";

// Query Keys
export { queryKeys, conversationKeys } from "./queries/queryKeys";
export type { ConversationQueryKey, QueryKey } from "./queries/queryKeys";

// Queries
export {
  useConversationsQuery,
  useInfiniteConversationsQuery,
  useConversationQuery,
  useConversationStatsQuery,
  usePrefetchConversations,
} from "./queries/conversationQueries";

// Mutations
export {
  useCreateConversationMutation,
  useUpdateConversationMutation,
  useDeleteConversationMutation,
  useSendChatMessageMutation,
  useSendChatMessageOptimisticMutation,
} from "./mutations/conversationMutations";
