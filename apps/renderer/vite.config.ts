import { defineConfig } from "vite";
export default defineConfig({
  worker: { format: "es" },
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
      "Content-Security-Policy":
        "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://127.0.0.1:5174; worker-src 'self' blob:; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors http://127.0.0.1:5173 http://localhost:5173",
      "Referrer-Policy": "no-referrer",
      "X-Content-Type-Options": "nosniff",
    },
  },
});
