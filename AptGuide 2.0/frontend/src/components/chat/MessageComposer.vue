<script setup lang="ts">
import { ref } from "vue";
import { useChatStore } from "../../stores/chat";

const chat = useChatStore();
const text = ref("");

async function send() {
  if (!text.value.trim() || chat.loading) return;
  const msg = text.value.trim();
  text.value = "";
  await chat.send(msg);
}
</script>

<template>
  <div class="message-composer">
    <input v-model="text" placeholder="输入消息..." @keyup.enter="send" />
    <button :disabled="!text.trim() || chat.loading" @click="send">发送</button>
  </div>
</template>
