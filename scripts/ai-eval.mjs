import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { existsSync } from "node:fs";
if (existsSync(".env")) process.loadEnvFile(".env");
if (!process.env.DEEPSEEK_API_KEY) {
  console.error("Configura DEEPSEEK_API_KEY en .env.");
  process.exit(1);
}
const python = join(
  "backend",
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const script = process.argv.includes("--generate-resource")
  ? "backend/scripts/generate_h0.py"
  : "backend/scripts/eval_h0.py";
const result = spawnSync(python, [script], { stdio: "inherit" });
if (result.error) {
  console.error("No se pudo iniciar la evaluación.");
  process.exit(1);
}
process.exit(result.status ?? 1);
