import { spawnSync } from "node:child_process";

export function firebaseConfig() {
  const response = spawnSync(
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
  try {
    const config = JSON.parse(response.stdout).result.sdkConfig;
    if (config.projectId !== "educloud-1d5de") throw new Error();
    return config;
  } catch {
    throw new Error("No se pudo obtener la configuración pública de EduCloud.");
  }
}
export function operatorToken() {
  const response = spawnSync(
    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
    [
      "-NoProfile",
      "-Command",
      "& 'C:/Program Files (x86)/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd' auth print-access-token --quiet",
    ],
    { encoding: "utf8" },
  );
  if (response.status !== 0 || !response.stdout.trim())
    throw new Error("Inicia sesión en gcloud antes de continuar.");
  return response.stdout.trim();
}
