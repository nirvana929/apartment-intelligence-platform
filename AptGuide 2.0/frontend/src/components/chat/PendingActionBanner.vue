<script setup lang="ts">
import { useChatStore } from "../../stores/chat";

const chat = useChatStore();
</script>

<template>
  <div v-if="chat.pendingAction" class="pending-banner">
    待确认: {{ chat.pendingAction.type }} ({{ chat.pendingAction.confirmation_id }})
  </div>
</template>
