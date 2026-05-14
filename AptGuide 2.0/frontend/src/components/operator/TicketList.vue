<script setup lang="ts">
import { useOperatorStore } from "../../stores/operator";

const store = useOperatorStore();
</script>

<template>
  <div class="ticket-list">
    <h3>工单列表</h3>
    <div class="filter-bar">
      <button
        :class="{ active: store.statusFilter === 'open' }"
        @click="store.setStatusFilter('open')"
      >未处理</button>
      <button
        :class="{ active: store.statusFilter === 'closed' }"
        @click="store.setStatusFilter('closed')"
      >已关闭</button>
      <button
        :class="{ active: store.statusFilter === 'all' }"
        @click="store.setStatusFilter('all')"
      >全部</button>
    </div>
    <div v-if="store.loading">加载中...</div>
    <div v-else-if="store.tickets.length === 0">暂无工单</div>
    <div v-for="ticket in store.tickets" :key="ticket.ticket_id"
         :class="['ticket-item', { selected: store.selectedTicket?.ticket_id === ticket.ticket_id }]"
         @click="store.select(ticket.ticket_id)">
      <p><strong>{{ ticket.ticket_id }}</strong></p>
      <p>用户: {{ ticket.user_id }}</p>
      <p>状态: {{ ticket.status }}</p>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.filter-bar button {
  flex: 1;
  padding: 6px 0;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.filter-bar button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
.ticket-item {
  padding: 8px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}
.ticket-item:hover {
  background: #f5f5f5;
}
.ticket-item.selected {
  background: #e3f2fd;
}
</style>
