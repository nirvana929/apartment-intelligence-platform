<script setup lang="ts">
import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();
const users = [
  { id: "dev-user-001", name: "测试用户 1" },
  { id: "dev-user-002", name: "测试用户 2" }
];
</script>

<template>
  <select :value="auth.devUserId" @change="auth.setDevUser(($event.target as HTMLSelectElement).value)">
    <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
  </select>
</template>
