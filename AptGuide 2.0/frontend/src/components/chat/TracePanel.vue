<script setup lang="ts">
import { useChatStore } from "../../stores/chat";

const chat = useChatStore();
</script>

<template>
  <aside v-if="chat.latestResponse" class="trace-panel">
    <h3>Trace</h3>
    <p><strong>Task:</strong> {{ chat.latestResponse.task }}</p>
    <p><strong>Phase:</strong> {{ chat.latestResponse.phase }}</p>
    <p><strong>Request ID:</strong> {{ chat.latestResponse.request_id }}</p>
    <p><strong>Trace ID:</strong> {{ chat.latestResponse.trace_id }}</p>
    <p><strong>Session ID:</strong> {{ chat.latestResponse.session_id }}</p>
    <pre>{{ JSON.stringify(chat.latestResponse.metadata, null, 2) }}</pre>
  </aside>
</template>
