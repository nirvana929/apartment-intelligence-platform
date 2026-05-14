<script setup lang="ts">
import DevUserSelector from "../auth/DevUserSelector.vue";
import MessageComposer from "./MessageComposer.vue";
import MessageList from "./MessageList.vue";
import PendingActionBanner from "./PendingActionBanner.vue";
import TracePanel from "./TracePanel.vue";
import { useChatStore } from "../../stores/chat";

const chat = useChatStore();
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <h1>AptGuide 2.0</h1>
        <p>独立租房 Agent 应用</p>
      </div>
      <DevUserSelector />
    </header>
    <section class="chat-layout">
      <div class="chat-main">
        <PendingActionBanner />
        <div v-if="chat.error" class="error-banner">
          <span>{{ chat.error }}</span>
          <button @click="chat.retryLast()">重试</button>
        </div>
        <MessageList />
        <MessageComposer />
      </div>
      <TracePanel />
    </section>
  </main>
</template>
