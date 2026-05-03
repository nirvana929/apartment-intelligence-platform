<script setup lang="ts">
import { ref, nextTick } from "vue";
import { chatWithAi } from "@/api/ai";
import ChatMessage from "./ChatMessage.vue";

interface Message {
  role: "user" | "assistant";
  content: string;
  cards?: any[];
}

const isOpen = ref(false);
const inputText = ref("");
const isLoading = ref(false);
const sessionId = ref<string | undefined>(undefined);
const messages = ref<Message[]>([
  {
    role: "assistant",
    content: "你好！我是尚庭公寓AI助手，可以帮你找房、预约看房、咨询租约问题。请问有什么可以帮您？"
  }
]);
const messageListRef = ref<HTMLElement | null>(null);

function togglePanel() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    nextTick(() => scrollToBottom());
  }
}

function closePanel() {
  isOpen.value = false;
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || isLoading.value) return;

  messages.value.push({ role: "user", content: text });
  inputText.value = "";
  isLoading.value = true;
  nextTick(() => scrollToBottom());

  try {
    const res = await chatWithAi({
      message: text,
      sessionId: sessionId.value
    });
    const data = (res as any).data ?? res;
    sessionId.value = data.sessionId;
    messages.value.push({
      role: "assistant",
      content: data.reply || "抱歉，我没有理解您的问题。",
      cards: data.cards
    });
  } catch {
    messages.value.push({
      role: "assistant",
      content: "网络异常，请稍后再试。"
    });
  } finally {
    isLoading.value = false;
    nextTick(() => scrollToBottom());
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}
</script>

<template>
  <div class="ai-assistant">
    <!-- Floating button -->
    <div class="fab" @click="togglePanel">
      <span class="fab-icon">AI</span>
    </div>

    <!-- Chat panel -->
    <Transition name="slide-up">
      <div v-if="isOpen" class="chat-panel">
        <div class="panel-header">
          <span class="panel-title">AI 助手</span>
          <span class="panel-close" @click="closePanel">&times;</span>
        </div>

        <div ref="messageListRef" class="message-list">
          <ChatMessage
            v-for="(msg, index) in messages"
            :key="index"
            :role="msg.role"
            :content="msg.content"
            :cards="msg.cards"
          />
          <div v-if="isLoading" class="typing">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>

        <div class="input-area">
          <input
            v-model="inputText"
            class="chat-input"
            placeholder="输入你的问题..."
            :disabled="isLoading"
            @keydown="handleKeydown"
          />
          <button
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="sendMessage"
          >
            发送
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style lang="less" scoped>
.ai-assistant {
  position: fixed;
  bottom: 80px;
  right: 16px;
  z-index: 9999;
}

.fab {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1989fa, #0066ff);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.4);
  cursor: pointer;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.9);
  }
}

.fab-icon {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1px;
}

.chat-panel {
  position: absolute;
  bottom: 56px;
  right: 0;
  width: 340px;
  height: 500px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #1989fa;
  color: #fff;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
}

.panel-close {
  font-size: 24px;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
  -webkit-overflow-scrolling: touch;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 8px 20px;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ccc;
    animation: bounce 1.4s infinite ease-in-out;

    &:nth-child(1) {
      animation-delay: 0s;
    }
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-area {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-top: 1px solid #eee;
  gap: 8px;
}

.chat-input {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: #1989fa;
  }

  &:disabled {
    background: #f5f5f5;
  }
}

.send-btn {
  background: #1989fa;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;

  &:disabled {
    background: #a0cfff;
    cursor: not-allowed;
  }

  &:active:not(:disabled) {
    background: #0066ff;
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>
