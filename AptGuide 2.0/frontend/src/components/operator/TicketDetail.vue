<script setup lang="ts">
import { useOperatorStore } from "../../stores/operator";
import OperatorReplyBox from "./OperatorReplyBox.vue";

const store = useOperatorStore();
</script>

<template>
  <div v-if="store.selectedTicket" class="ticket-detail">
    <h3>工单详情: {{ store.selectedTicket.ticket_id }}</h3>
    <p>用户: {{ store.selectedTicket.user_id }}</p>
    <p>会话: {{ store.selectedTicket.session_id }}</p>
    <p>状态: {{ store.selectedTicket.status }}</p>

    <h4>消息记录</h4>
    <div v-for="(msg, i) in store.selectedTicket.messages" :key="i" class="message">
      <strong>{{ msg.sender }}:</strong> {{ msg.content }}
    </div>

    <OperatorReplyBox v-if="store.selectedTicket.status === 'open'" />
    <button v-if="store.selectedTicket.status === 'open'" @click="store.close()">关闭工单</button>
  </div>
</template>

<style scoped>
.message {
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}
button {
  margin-top: 12px;
  padding: 8px 16px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
