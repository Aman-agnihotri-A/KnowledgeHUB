import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,

    proxy: {
      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/conversations": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/rag": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },

      "/documents": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/tenants": {
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
    },
    },
  },

  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/testSetup.js",
  },
});