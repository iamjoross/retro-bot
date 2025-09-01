import {
  useQuery,
  UseQueryOptions,
  useInfiniteQuery,
  UseInfiniteQueryOptions,
} from "@tanstack/react-query";
import { httpClient, APIError } from "../client/httpClient";
import { API_CONFIG } from "../client/config";
import { conversationKeys } from "./queryKeys";
import {
  Conversation,
  ConversationSummary,
  ConversationListParams,
  ConversationStatsResponse,
} from "../types/conversation";

/**
 * Fetch conversations list with pagination and filtering support:
 * - Builds query string from parameters
 * - Configures caching and retry logic
 * - Avoids retrying on client errors (4xx)
 */
export const useConversationsQuery = (
  params: ConversationListParams = {},
  options?: UseQueryOptions<ConversationSummary[], APIError>
) => {
  return useQuery({
    queryKey: conversationKeys.list(params),
    queryFn: async (): Promise<ConversationSummary[]> => {
      const searchParams = new URLSearchParams();

      if (params.skip !== undefined)
        searchParams.set("skip", params.skip.toString());
      if (params.limit !== undefined)
        searchParams.set("limit", params.limit.toString());
      if (params.include_messages !== undefined) {
        searchParams.set(
          "include_messages",
          params.include_messages.toString()
        );
      }

      const queryString = searchParams.toString();
      const url = `${API_CONFIG.ENDPOINTS.CONVERSATIONS}${queryString ? `?${queryString}` : ""}`;

      return httpClient.get<ConversationSummary[]>(url);
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      if (
        error instanceof APIError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        return false;
      }
      return failureCount < 3;
    },
    ...options,
  });
};

/**
 * Fetch a specific conversation by ID:
 * - Only executes when conversationId is provided
 * - Shorter cache time for more current data
 * - Avoids retrying on 404 and client errors
 */
export const useConversationQuery = (
  conversationId: string,
  options?: UseQueryOptions<Conversation, APIError>
) => {
  return useQuery({
    queryKey: conversationKeys.detail(conversationId),
    queryFn: async (): Promise<Conversation> => {
      return httpClient.get<Conversation>(
        API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(conversationId)
      );
    },
    enabled: !!conversationId,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (
        error instanceof APIError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        return false;
      }
      return failureCount < 3;
    },
    ...options,
  });
};

/**
 * Fetch conversation statistics with extended caching:
 * - Long cache times since stats change infrequently
 * - Disabled window focus refetch for better UX
 */
export const useConversationStatsQuery = (
  options?: UseQueryOptions<ConversationStatsResponse, APIError>
) => {
  return useQuery({
    queryKey: conversationKeys.stats(),
    queryFn: async (): Promise<ConversationStatsResponse> => {
      return httpClient.get<ConversationStatsResponse>(
        API_CONFIG.ENDPOINTS.CONVERSATION_STATS
      );
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    ...options,
  });
};

/**
 * Infinite scroll conversations query with pagination:
 * - Fixed page size of 20 items
 * - Automatic next page detection based on response length
 * - Calculates skip values for pagination
 */
export const useInfiniteConversationsQuery = (
  baseParams: Omit<ConversationListParams, "skip"> = {},
  options?: UseInfiniteQueryOptions<ConversationSummary[], APIError>
) => {
  const PAGE_SIZE = 20;

  return useInfiniteQuery({
    queryKey: conversationKeys.list({ ...baseParams, limit: PAGE_SIZE }),
    queryFn: async ({ pageParam = 0 }): Promise<ConversationSummary[]> => {
      const searchParams = new URLSearchParams();

      searchParams.set("skip", (pageParam as number).toString());
      searchParams.set("limit", PAGE_SIZE.toString());
      if (baseParams.include_messages !== undefined) {
        searchParams.set(
          "include_messages",
          baseParams.include_messages.toString()
        );
      }

      const queryString = searchParams.toString();
      const url = `${API_CONFIG.ENDPOINTS.CONVERSATIONS}?${queryString}`;

      return httpClient.get<ConversationSummary[]>(url);
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < PAGE_SIZE) {
        return undefined;
      }
      return allPages.length * PAGE_SIZE;
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      if (
        error instanceof APIError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        return false;
      }
      return failureCount < 3;
    },
    ...options,
  });
};

/**
 * Prefetch conversations list for better UX:
 * - Returns query configuration for manual prefetching
 * - Reuses same query building logic as main hook
 * - Useful for preloading data on user interactions
 */
export const usePrefetchConversations = () => {
  return {
    prefetchList: (params: ConversationListParams = {}) => {
      return {
        queryKey: conversationKeys.list(params),
        queryFn: async () => {
          const searchParams = new URLSearchParams();

          if (params.skip !== undefined)
            searchParams.set("skip", params.skip.toString());
          if (params.limit !== undefined)
            searchParams.set("limit", params.limit.toString());
          if (params.include_messages !== undefined) {
            searchParams.set(
              "include_messages",
              params.include_messages.toString()
            );
          }

          const queryString = searchParams.toString();
          const url = `${API_CONFIG.ENDPOINTS.CONVERSATIONS}${queryString ? `?${queryString}` : ""}`;

          return httpClient.get<ConversationSummary[]>(url);
        },
      };
    },
  };
};
