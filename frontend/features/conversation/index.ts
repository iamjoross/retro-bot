// Components
export { ConversationContainer } from "./components/ConversationContainer";
export { ConversationHeader } from "./components/ConversationHeader";
export { ConversationList } from "./components/ConversationList";
export { MessageDisplay } from "./components/MessageDisplay";
export { MessageInput } from "./components/MessageInput";

// Hooks
export { useConversationState } from "./hooks/useConversationState";
export { useAutoScroll, useAutoScrollOnChange } from "./hooks/useAutoScroll";

// Services
export { chatService } from "./services/chatService";

// Types
export type {
  Message,
  Conversation,
  ConversationState,
  ChatRequest,
  ChatResponse,
  ConversationActions,
} from "./types";

// Utils
export {
  SYSTEM_MESSAGE,
  generateConversationId,
  generateConversationTitle,
  sortConversationsByActivity,
  createNewConversation,
  createErrorMessage,
} from "./utils/conversationUtils";
