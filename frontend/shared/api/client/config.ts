export const API_CONFIG = {
  BASE_URL:
    process.env.NODE_ENV === "production"
      ? "/api/v1"
      : "http://localhost:8000/api/v1",

  ENDPOINTS: {
    // Chat endpoints
    CHAT: "/chat",

    // Conversation management endpoints
    CONVERSATIONS: "/conversations",
    CONVERSATION_BY_ID: (id: string) => `/conversations/${id}`,
    CONVERSATION_STATS: "/conversations-stats",
  },

  // Request timeouts (in milliseconds)
  TIMEOUTS: {
    DEFAULT: 30000,
    CHAT: 60000, // Longer timeout for chat responses
    UPLOAD: 120000,
  },

  // Retry configuration
  RETRY: {
    ATTEMPTS: 3,
    DELAY: 1000,
    EXPONENTIAL_BACKOFF: true,
  },
} as const;

export type APIEndpoint = typeof API_CONFIG.ENDPOINTS;
