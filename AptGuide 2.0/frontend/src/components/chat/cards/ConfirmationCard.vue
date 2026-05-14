<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card">
    <h4>确认操作</h4>
    <p>请确认是否执行此操作</p>
  </div>
</template>
