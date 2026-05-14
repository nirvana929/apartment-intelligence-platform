<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card appointment">
    <h4>预约</h4>
    <pre>{{ JSON.stringify(card, null, 2) }}</pre>
  </div>
</template>
