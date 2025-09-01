import type { Message as APIMessage } from "../../../shared/api";

export type { ChatRequest, ChatResponse } from "../../../shared/api";

export type Message = APIMessage;

// Extended Conversation type with local UI state
export interface Conversation {
  id: string;
  _id?: string; // MongoDB _id field for compatibility
  title?: string | null;
  messages: Message[];
  created_at: string;
  updated_at: string;
  // Local UI state
  lastActivity: Date;
  isActive: boolean;
}

export interface ConversationState {
  conversations: Map<string, Conversation>;
  activeConversationId: string | null;
}

export interface ConversationActions {
  createNewConversation: () => string;
  switchToConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  sendMessage: (message: string) => Promise<void>;
}
