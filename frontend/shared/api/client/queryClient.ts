import { QueryClient } from "@tanstack/react-query";
import { APIError } from "./httpClient";

/**
 * Creates a configured QueryClient instance with default options for:
 * - Query caching and stale time settings
 * - Retry logic for failed requests
 * - Error handling for mutations
 */
export const createQueryClient = (): QueryClient => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,
        gcTime: 10 * 60 * 1000,

        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        refetchOnMount: true,

        retry: (failureCount: number, error: unknown) => {
          if (
            error instanceof APIError &&
            error.status >= 400 &&
            error.status < 500
          ) {
            return false;
          }

          return failureCount < 3;
        },

        retryDelay: (attemptIndex: number) => {
          return Math.min(1000 * 2 ** attemptIndex, 30000);
        },
      },

      mutations: {
        retry: (failureCount: number, error: unknown) => {
          if (error instanceof APIError) {
            return error.status >= 500 && failureCount < 2;
          }

          return failureCount < 1;
        },

        onError: (error: unknown) => {
          console.error("Mutation error:", error);

          if (process.env.NODE_ENV === "production") {
            // reportError(error);
          }
        },
      },
    },
  });
};

/**
 * Handles different types of query errors with appropriate logging and actions:
 * - 401: Unauthorized access
 * - 403: Forbidden access
 * - 404: Resource not found
 * - 500: Server errors
 * - Network and other errors
 */
export const handleQueryError = (error: unknown): void => {
  console.error("Query error:", error);

  if (error instanceof APIError) {
    switch (error.status) {
      case 401:
        console.warn("Unauthorized access - redirecting to login");
        // window.location.href = '/login';
        break;

      case 403:
        console.warn("Forbidden access");
        break;

      case 404:
        console.warn("Resource not found");
        break;

      case 500:
        console.error("Server error occurred");
        break;

      default:
        console.error("Unexpected API error:", error.message);
    }
  } else {
    console.error("Network or unknown error:", error);
  }

  if (process.env.NODE_ENV === "production") {
    // reportError(error);
  }
};

/**
 * Default query client instance
 * Use this for most cases, or create a new one with createQueryClient()
 */
export const queryClient = createQueryClient();
