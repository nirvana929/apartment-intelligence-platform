<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card handoff">
    <h4>人工客服</h4>
    <p>工单号: {{ card.ticket_id }}</p>
    <p>状态: {{ card.status }}</p>
  </div>
</template>
