import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
if (existsSync(".env")) process.loadEnvFile(".env");
if (!process.env.DEEPSEEK_API_KEY) {
  console.error("Configura DEEPSEEK_API_KEY en .env.");
  process.exit(1);
}
const python =
  process.platform === "win32"
    ? "backend/.venv/Scripts/python.exe"
    : "backend/.venv/bin/python";
const child = spawn(python, ["backend/scripts/eval_h2.py"], {
  stdio: "inherit",
});
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
