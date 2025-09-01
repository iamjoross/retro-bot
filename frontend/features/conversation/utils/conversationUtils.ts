import { Message, Conversation } from "../types";
import {
  Conversation as APIConversation,
  ConversationSummary,
} from "../../../shared/api";

export const SYSTEM_MESSAGE: Message = {
  role: "system",
  content: "DATACOM-7 ONLINE. Ready for interaction. *BEEP*",
};

export const generateConversationId = (): string => {
  return `conv_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
};

export const generateConversationTitle = (messages: Message[]): string => {
  const firstUserMessage = messages.find((m) => m.role === "user")?.content;
  if (!firstUserMessage) return "New Session";
  return firstUserMessage.length > 30
    ? `${firstUserMessage.slice(0, 30)}...`
    : firstUserMessage;
};

export const sortConversationsByActivity = (
  conversations: Conversation[]
): Conversation[] => {
  return conversations.sort(
    (a, b) => b.lastActivity.getTime() - a.lastActivity.getTime()
  );
};

export const createNewConversation = (id?: string): Conversation => ({
  id: id || generateConversationId(),
  messages: [SYSTEM_MESSAGE],
  title: "New Session",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  lastActivity: new Date(),
  isActive: true,
});

export const createErrorMessage = (error: string): Message => ({
  role: "assistant",
  content: `[ERROR] ${error} *BEEP*`,
});

export const mapAPIConversationToLocal = (
  apiConv: APIConversation
): Conversation => ({
  ...apiConv,
  id: apiConv.id || apiConv._id || "", // Handle MongoDB _id field properly
  lastActivity: new Date(apiConv.updated_at),
  isActive: false,
});

export const mapAPIConversationSummaryToLocal = (
  apiSummary: ConversationSummary
): Conversation => {
  const placeholderMessages: Message[] = [];

  return {
    id: apiSummary.id || apiSummary._id || "", // Handle MongoDB _id field properly
    title: apiSummary.title || "New Session",
    messages: placeholderMessages,
    created_at: apiSummary.created_at,
    updated_at: apiSummary.updated_at,
    lastActivity: new Date(apiSummary.updated_at),
    isActive: false,
  };
};
