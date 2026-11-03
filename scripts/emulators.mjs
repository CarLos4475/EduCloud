import { spawn } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
const environment = { ...process.env };
if (existsSync(".tools/java21")) {
  const directory = readdirSync(".tools/java21").find((name) =>
    existsSync(join(".tools/java21", name, "bin", "java.exe")),
  );
  if (directory) {
    environment.JAVA_HOME = resolve(".tools/java21", directory);
    environment.PATH =
      join(environment.JAVA_HOME, "bin") + ";" + environment.PATH;
  }
}
const args = [
  "node_modules/firebase-tools/lib/bin/firebase.js",
  "emulators:start",
  "--only",
  "auth,firestore",
  "--project",
  "demo-campus",
  "--export-on-exit=.firebase/data",
];
if (existsSync(".firebase/data/firebase-export-metadata.json"))
  args.push("--import=.firebase/data");
const child = spawn(process.execPath, args, {
  stdio: "inherit",
  env: environment,
});
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
