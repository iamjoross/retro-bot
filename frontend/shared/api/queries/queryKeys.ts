import { ConversationListParams } from "../types/conversation";

/**
 * Hierarchical query keys for conversation-related queries:
 * - all: Base key for all conversation queries
 * - lists/list: Conversation list queries with optional parameters
 * - details/detail: Individual conversation queries by ID
 * - stats: Conversation statistics queries
 * - chat/chatHistory: Chat-related queries with conversation context
 */
export const conversationKeys = {
  all: ["conversations"] as const,

  lists: () => [...conversationKeys.all, "list"] as const,
  list: (params: ConversationListParams) =>
    [...conversationKeys.lists(), params] as const,

  details: () => [...conversationKeys.all, "detail"] as const,
  detail: (id: string) => [...conversationKeys.details(), id] as const,

  stats: () => [...conversationKeys.all, "stats"] as const,

  chat: () => ["chat"] as const,
  chatHistory: (conversationId: string) =>
    [...conversationKeys.chat(), "history", conversationId] as const,
} as const;

/**
 * Main query keys registry for the entire application:
 * - conversations: All conversation-related query keys
 * - Future expansion for other feature areas
 */
export const queryKeys = {
  conversations: conversationKeys,
} as const;

/**
 * Type helpers for better IntelliSense and type safety
 */
export type ConversationQueryKey =
  | typeof conversationKeys.all
  | ReturnType<typeof conversationKeys.lists>
  | ReturnType<typeof conversationKeys.list>
  | ReturnType<typeof conversationKeys.details>
  | ReturnType<typeof conversationKeys.detail>
  | ReturnType<typeof conversationKeys.stats>
  | ReturnType<typeof conversationKeys.chat>
  | ReturnType<typeof conversationKeys.chatHistory>;

export type QueryKey = ConversationQueryKey;
