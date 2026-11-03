import { spawnSync } from "node:child_process";
import { join } from "node:path";

const action = process.argv[2];
if (action !== "generate" && action !== "check") {
  console.error("Usage: node scripts/contracts.mjs <generate|check>");
  process.exit(1);
}

const python = join(
  "backend",
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const result = spawnSync(
  python,
  [
    "backend/scripts/generate_contracts.py",
    ...(action === "check" ? ["--check"] : []),
  ],
  {
    stdio: "inherit",
  },
);
if (result.error) {
  console.error(`No se pudo generar contratos: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
