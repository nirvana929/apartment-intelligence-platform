<script setup lang="ts">
import { useChatStore } from "../../stores/chat";
import type { ChatAction } from "../../types/chat";

defineProps<{ actions: ChatAction[] }>();
const chat = useChatStore();

function run(action: ChatAction) {
  const label = action.type === "cancel" ? "取消" : "确认";
  chat.send(label, {
    type: action.type,
    confirmation_id: action.confirmation_id,
    payload: action.payload || {}
  });
}
</script>

<template>
  <div class="action-bar">
    <button v-for="action in actions" :key="`${action.type}-${action.confirmation_id}`" @click="run(action)">
      {{ action.label || action.type }}
    </button>
  </div>
</template>
