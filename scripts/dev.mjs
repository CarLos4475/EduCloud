import { spawn } from "node:child_process";
import { join } from "node:path";
import { existsSync } from "node:fs";

if (existsSync(".env") && !process.env.CAMPUS_ENV_PRELOADED)
  process.loadEnvFile(".env");

// Spawn through the package manager entry point on Windows without a shell.
const pnpm = process.env.npm_execpath;
if (!pnpm) {
  console.error("Ejecuta este script mediante pnpm dev.");
  process.exit(1);
}
const pnpmCommand = pnpm.toLowerCase().endsWith(".exe")
  ? pnpm
  : process.execPath;
const pnpmPrefix = pnpmCommand === pnpm ? [] : [pnpm];
const services = [
  [pnpmCommand, [...pnpmPrefix, "--filter", "@campus/web", "dev"]],
  [pnpmCommand, [...pnpmPrefix, "--filter", "@campus/renderer", "dev"]],
  [
    join(
      "backend",
      ".venv",
      process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
    ),
    [
      "-m",
      "uvicorn",
      "campus.api.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      "8000",
      "--reload",
      "--reload-dir",
      "backend/src",
    ],
  ],
];
const children = services.map(([cmd, args]) =>
  spawn(cmd, args, { stdio: "inherit" }),
);
let stopping = false;
function stop(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (!child.pid) continue;
    if (process.platform === "win32")
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], {
        stdio: "ignore",
      });
    else child.kill("SIGTERM");
  }
  setTimeout(() => process.exit(code), 500).unref();
}
for (const child of children) {
  child.on("error", (e) => {
    console.error(e.message);
    stop(1);
  });
  child.on("exit", (code) => {
    if (!stopping) stop(code || 1);
  });
}
process.on("SIGINT", () => stop(0));
process.on("SIGTERM", () => stop(0));
