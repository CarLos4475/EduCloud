import { spawnSync } from "node:child_process";
import { operatorToken } from "./google-session.mjs";
const environment = {
  ...process.env,
  CAMPUS_SMOKE_ACCESS_TOKEN: operatorToken(),
};
delete environment.FIRESTORE_EMULATOR_HOST;
delete environment.FIREBASE_AUTH_EMULATOR_HOST;
const python =
  process.platform === "win32"
    ? "backend/.venv/Scripts/python.exe"
    : "backend/.venv/bin/python";
const result = spawnSync(
  python,
  ["backend/scripts/smoke_h2_firestore.py", ...process.argv.slice(2)],
  { stdio: "inherit", env: environment },
);
process.exit(result.status ?? 1);
