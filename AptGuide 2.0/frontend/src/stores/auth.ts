import { defineStore } from "pinia";
import { setBearerToken } from "../api/client";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    mode: "dev" as "dev" | "lease_token",
    devUserId: "dev-user-001",
    token: ""
  }),
  actions: {
    setDevUser(userId: string) {
      this.mode = "dev";
      this.devUserId = userId;
      setBearerToken(null);
    },
    setToken(token: string) {
      this.mode = "lease_token";
      this.token = token;
      setBearerToken(token);
    }
  }
});
