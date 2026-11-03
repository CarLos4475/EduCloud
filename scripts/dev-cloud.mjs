import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { firebaseConfig, operatorToken } from "./google-session.mjs";
if (existsSync(".env")) process.loadEnvFile(".env");
let config, token;
try {
  config = firebaseConfig();
  token = operatorToken();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
const environment = {
  ...process.env,
  CAMPUS_ENV_PRELOADED: "1",
  CAMPUS_ENV: "production",
  GOOGLE_CLOUD_PROJECT: config.projectId,
  CAMPUS_LOCAL_ACCESS_TOKEN: token,
  VITE_USE_EMULATORS: "false",
  VITE_FIREBASE_PROJECT_ID: config.projectId,
  VITE_FIREBASE_API_KEY: config.apiKey,
  VITE_FIREBASE_AUTH_DOMAIN: config.authDomain,
};
delete environment.FIREBASE_AUTH_EMULATOR_HOST;
delete environment.FIRESTORE_EMULATOR_HOST;
console.log(
  "Desarrollo local conectado a Firebase/Firestore reales. La sesión del operador es temporal; reinicia este comando cuando expire.",
);
const child = spawn(process.execPath, ["scripts/dev.mjs"], {
  stdio: "inherit",
  env: environment,
});
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
