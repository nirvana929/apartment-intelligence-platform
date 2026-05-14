<script setup lang="ts">
defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <div class="card room">
    <h4>房间 #{{ card.room_id }}</h4>
    <p v-if="card.rent">租金: ¥{{ card.rent }}/月</p>
    <p v-if="card.district">区域: {{ card.district }}</p>
    <p v-if="card.recommendation_reason">{{ card.recommendation_reason }}</p>
  </div>
</template>
