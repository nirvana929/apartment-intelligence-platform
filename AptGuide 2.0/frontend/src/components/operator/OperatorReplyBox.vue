<script setup lang="ts">
import { ref } from "vue";
import { useOperatorStore } from "../../stores/operator";

const store = useOperatorStore();
const text = ref("");

async function send() {
  if (!text.value.trim()) return;
  await store.reply(text.value.trim());
  text.value = "";
}
</script>

<template>
  <div class="reply-box">
    <input v-model="text" placeholder="输入回复..." @keyup.enter="send" />
    <button :disabled="!text.trim() || store.loading" @click="send">发送</button>
  </div>
</template>

<style scoped>
.reply-box {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:disabled {
  background: #ccc;
}
</style>
