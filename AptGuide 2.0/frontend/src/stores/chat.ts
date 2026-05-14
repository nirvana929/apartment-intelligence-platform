import { defineStore } from "pinia";
import { sendChat } from "../api/chat";
import { useAuthStore } from "./auth";
import type { ChatAction, ChatCard, ChatResponse, PendingAction } from "../types/chat";

type Message = {
  role: "user" | "assistant";
  content: string;
  cards?: ChatCard[];
  actions?: ChatAction[];
};

export const useChatStore = defineStore("chat", {
  state: () => ({
    sessionId: undefined as string | undefined,
    messages: [] as Message[],
    pendingAction: null as PendingAction | null,
    latestResponse: null as ChatResponse | null,
    loading: false,
    error: null as string | null,
    lastDraft: "",
    lastAction: undefined as Record<string, unknown> | undefined
  }),
  actions: {
    async send(message: string, action?: Record<string, unknown>) {
      if (this.loading) return;
      const auth = useAuthStore();
      this.error = null;
      this.lastDraft = message;
      this.lastAction = action;
      this.loading = true;
      this.messages.push({ role: "user", content: message });
      try {
        const response = await sendChat({
          message,
          session_id: this.sessionId,
          user_id: auth.mode === "dev" ? auth.devUserId : undefined,
          action,
          client_context: { frontend: "standalone" }
        });
        this.sessionId = response.session_id || this.sessionId;
        this.pendingAction = response.pending_action;
        this.latestResponse = response;
        this.messages.push({
          role: "assistant",
          content: response.message,
          cards: response.cards,
          actions: response.actions
        });
      } catch (err) {
        this.error = err instanceof Error ? err.message : "请求失败，请稍后重试";
      } finally {
        this.loading = false;
      }
    },
    async retryLast() {
      if (!this.lastDraft) return;
      await this.send(this.lastDraft, this.lastAction);
    }
  }
});
