<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card lease">
    <h4>租约</h4>
    <pre>{{ JSON.stringify(card, null, 2) }}</pre>
  </div>
</template>
