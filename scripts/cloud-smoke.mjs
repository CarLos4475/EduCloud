import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
if (existsSync(".env")) process.loadEnvFile(".env");
const firebase = spawnSync(
  process.execPath,
  [
    "node_modules/firebase-tools/lib/bin/firebase.js",
    "apps:sdkconfig",
    "WEB",
    "1:91278208482:web:8a211daff5f34739e0ddbb",
    "--project",
    "educloud-1d5de",
    "--json",
  ],
  { encoding: "utf8" },
);
let sdk;
try {
  sdk = JSON.parse(firebase.stdout).result.sdkConfig;
} catch {
  console.error("No se pudo obtener la configuración pública Firebase.");
  process.exit(1);
}
const token = spawnSync(
  "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
  [
    "-NoProfile",
    "-Command",
    "& 'C:/Program Files (x86)/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd' auth print-access-token --quiet",
  ],
  { encoding: "utf8" },
);
if (token.status !== 0 || !token.stdout.trim()) {
  console.error("Inicia sesión en gcloud antes de ejecutar esta prueba.");
  process.exit(1);
}
const result = spawnSync(
  join(
    "backend",
    ".venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  ),
  ["backend/scripts/cloud_smoke.py", ...process.argv.slice(2)],
  {
    stdio: "inherit",
    env: {
      ...process.env,
      CAMPUS_SMOKE_ACCESS_TOKEN: token.stdout.trim(),
      CAMPUS_FIREBASE_WEB_CONFIG: JSON.stringify(sdk),
    },
  },
);
if (result.error) {
  console.error("No se pudo iniciar el smoke cloud.");
  process.exit(1);
}
process.exit(result.status ?? 1);
