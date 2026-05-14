import { http } from "./client";
import type { ChatRequest, ChatResponse } from "../types/chat";

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await http.post<ChatResponse>("/chat", request);
  return response.data;
}
