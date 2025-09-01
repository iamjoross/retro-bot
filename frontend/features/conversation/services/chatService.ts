import { httpClient, API_CONFIG } from "../../../shared/api";
import { ChatRequest, ChatResponse } from "../types";

class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return httpClient.post<ChatResponse>(API_CONFIG.ENDPOINTS.CHAT, request, {
      timeout: API_CONFIG.TIMEOUTS.CHAT,
    });
  }
}

export const chatService = new ChatService();
