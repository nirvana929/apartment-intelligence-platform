import http from "@/utils/http";

export interface ChatRequest {
  message: string;
  sessionId?: string;
}

export interface ChatResponse {
  reply: string;
  cards: any[];
  actions: any[];
  pendingConfirmation: any;
  sources: string[];
  sessionId: string;
}

/**
 * @description 与 AI 助手对话
 * @param data
 */
export function chatWithAi(data: ChatRequest) {
  return http.post<ChatResponse>("/app/ai/chat", data);
}
