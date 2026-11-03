import {
  samples,
  InteractivePackage,
} from "../../../packages/resource-sdk/src/fixtures";
import "./styles/main.css";
const root = document.getElementById("root")!;
root.innerHTML =
  '<main style="max-width:1000px;margin:30px auto;padding:20px"><span class="eyebrow">MI CAMPUS · PRUEBA H0</span><h1>Explora una idea.</h1><p>Tres experiencias de referencia con composición libre y un SDK de capacidades limitadas.</p><div id="choices" class="button-row"></div><p id="status" role="status"></p><iframe title="Laboratorio interactivo" style="width:100%;height:690px;border:2px solid #122245;margin-top:20px" sandbox="allow-scripts allow-same-origin" src="http://127.0.0.1:5174"></iframe><button id="reset" class="secondary">Reiniciar experiencia</button></main>';
const frame = root.querySelector("iframe")!;
let sequence = 0;
let channel = crypto.randomUUID();
let current = samples[0];
let saved: Record<string, unknown> = {};
function load(pkg: InteractivePackage) {
  current = pkg;
  frame.contentWindow?.postMessage(
    {
      protocolVersion: 1,
      channelId: channel,
      sequence: ++sequence,
      type: "load",
      payload: { package: pkg, state: saved[pkg.title] || pkg.initialState },
    },
    "http://127.0.0.1:5174",
  );
}
samples.forEach((sample) => {
  const button = document.createElement("button");
  button.className = "secondary";
  button.textContent = sample.title;
  button.onclick = () => load(sample);
  document.getElementById("choices")!.append(button);
});
fetch("/h0-generated.json")
  .then((response) => (response.ok ? response.json() : null))
  .then((pkg) => {
    if (!pkg) return;
    const button = document.createElement("button");
    button.className = "primary";
    button.textContent = "Recurso creado por DeepSeek";
    button.onclick = () => load(pkg);
    document.getElementById("choices")!.append(button);
  })
  .catch(() => {});
frame.addEventListener("load", () => {
  channel = crypto.randomUUID();
  sequence = 0;
  load(current);
});
document.getElementById("reset")!.onclick = () => {
  delete saved[current.title];
  frame.contentWindow?.postMessage(
    {
      protocolVersion: 1,
      channelId: channel,
      sequence: ++sequence,
      type: "reset",
      payload: {},
    },
    "http://127.0.0.1:5174",
  );
};
window.addEventListener("message", (event) => {
  if (
    event.origin !== "http://127.0.0.1:5174" ||
    event.source !== frame.contentWindow ||
    event.data.channelId !== channel
  )
    return;
  if (event.data.type === "state") {
    saved[current.title] = event.data.payload;
    document.getElementById("status")!.textContent =
      "Parámetros conservados durante esta sesión.";
  }
});
