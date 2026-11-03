import { defineConfig } from "vite";

export default defineConfig({
  envDir: "../..",
  server: {
    fs: {
      deny: [
        "**/.env*",
        "**/*.{crt,pem,key,p12,pfx}",
        "**/.git/**",
        "**/.data/**",
        "**/.superpowers/**",
        "**/.tools/**",
        "**/.codex/**",
        "**/.agents/**",
        "**/.aws/**",
        "**/.gcloud/**",
        "**/credentials.json",
        "**/*firebase-adminsdk*.json",
        "**/service-account*.json",
      ],
    },
    headers: {
      "X-Frame-Options": "DENY",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
    },
  },
  build: {
    rollupOptions: { input: { app: "index.html", laboratorio: "h0.html" } },
  },
});
