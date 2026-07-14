import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const apiProxyTarget = process.env.VITE_DEV_PROXY_TARGET?.trim() || "http://localhost:8000";
const apiProxy = {
  "/api": {
    target: apiProxyTarget,
    changeOrigin: true,
    configure: (proxy) => {
      // Avoid stale keep-alive sockets after the API container is recreated.
      proxy.on("proxyReq", (proxyReq) => {
        proxyReq.setHeader("Connection", "close");
      });
    },
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: apiProxy,
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: apiProxy,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
    exclude: ["**/node_modules/**", "**/dist/**", "**/e2e/**"],
  },
});
