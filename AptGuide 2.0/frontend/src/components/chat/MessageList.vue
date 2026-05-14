<script setup lang="ts">
import { useChatStore } from "../../stores/chat";
import CardRenderer from "./CardRenderer.vue";
import ActionBar from "./ActionBar.vue";

const chat = useChatStore();
</script>

<template>
  <div class="message-list">
    <div v-for="(msg, i) in chat.messages" :key="i" :class="['message', msg.role]">
      <div>{{ msg.content }}</div>
      <CardRenderer v-for="(card, j) in msg.cards" :key="j" :card="card" />
      <ActionBar v-if="msg.actions?.length" :actions="msg.actions" />
    </div>
    <div v-if="chat.loading" class="message assistant">思考中...</div>
  </div>
</template>
