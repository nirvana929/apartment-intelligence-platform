<script setup lang="ts">
import { onMounted } from "vue";
import { useOperatorStore } from "../../stores/operator";
import TicketDetail from "./TicketDetail.vue";
import TicketList from "./TicketList.vue";

const store = useOperatorStore();
onMounted(() => store.refresh());
</script>

<template>
  <main class="operator-layout">
    <div v-if="store.error" class="error-banner">
      <span>{{ store.error }}</span>
      <button @click="store.refresh()">重试</button>
    </div>
    <div v-if="store.loading && store.tickets.length === 0" class="loading-indicator">
      加载中...
    </div>
    <div v-else-if="!store.loading && !store.error && store.tickets.length === 0" class="empty-state">
      暂无工单
    </div>
    <TicketList v-else />
    <TicketDetail v-if="store.selectedTicket" />
  </main>
</template>

<style scoped>
.error-banner {
  background: #ffebee;
  color: #c62828;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 4px;
  margin-bottom: 8px;
}
.error-banner button {
  background: #c62828;
  color: white;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.loading-indicator,
.empty-state {
  padding: 24px;
  text-align: center;
  color: #888;
}
</style>
