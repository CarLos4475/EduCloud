import { defineConfig } from "vite";

export default defineConfig({
  envDir: "../..",
  build: {
    rollupOptions: { input: { app: "index.html", laboratorio: "h0.html" } },
  },
});
