import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/chat": "http://localhost:8100",
      "/health": "http://localhost:8100",
      "/operator": "http://localhost:8100"
    }
  }
});
