<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card memory">
    <h4>记忆</h4>
    <pre>{{ JSON.stringify(card.profile || card, null, 2) }}</pre>
  </div>
</template>
