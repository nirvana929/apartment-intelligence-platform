import { createRouter, createWebHistory } from "vue-router";

import ChatShell from "./components/chat/ChatShell.vue";
import OperatorConsole from "./components/operator/OperatorConsole.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: ChatShell },
    { path: "/operator", component: OperatorConsole }
  ]
});
