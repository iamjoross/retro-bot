export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  created_at?: string;
}

export interface Conversation {
  id?: string;
  _id?: string;
  title?: string | null;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  id?: string;
  _id?: string;
  title?: string | null;
  message_count: number;
  last_message_preview?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationListParams {
  skip?: number;
  limit?: number;
  include_messages?: boolean;
}

export interface ConversationUpdateRequest {
  title?: string;
}

export interface ConversationStatsResponse {
  total_conversations: number;
  total_messages: number;
  average_messages_per_conversation: number;
  oldest_conversation_date?: string | null;
  newest_conversation_date?: string | null;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  timestamp: string;
}