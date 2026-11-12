import { safeMarkup, safeCss, plainJson } from "./policy";
import type { InteractivePackage } from "../../../packages/resource-sdk/src/fixtures";
import katex from "katex";
import "katex/dist/katex.min.css";
import "./style.css";

const root = document.getElementById("root")!;
root.innerHTML =
  '<header><small>MI CAMPUS · LABORATORIO</small><h1 id="title">Un espacio para explorar.</h1><p id="instructions">Abre un recurso desde tu espacio de estudio.</p></header><p id="status" role="status"></p><section id="resource"></section><p id="alternative"></p>';
const resource = document.getElementById("resource")!;
const status = document.getElementById("status")!;
let worker: Worker | null = null;
let channel = "";
let sequence = 0;
let parentOrigin = "";
let watchdog: ReturnType<typeof setTimeout> | undefined;
let animation: ReturnType<typeof setInterval> | undefined;
let lastPackage: InteractivePackage | null = null;
const style = document.createElement("style");
document.head.append(style);
function stop() {
  worker?.terminate();
  worker = null;
  clearTimeout(watchdog);
  clearInterval(animation);
}
function fail() {
  stop();
  resource.inert = true;
  status.textContent =
    "El recurso se detuvo. Reinícialo para volver a intentar.";
}
function post(type: string, payload: unknown) {
  if (parentOrigin)
    window.parent.postMessage(
      { protocolVersion: 1, channelId: channel, type, payload },
      parentOrigin,
    );
}
// Tell the parent how tall the content is so its frame can fit without inner scrolling.
let reportedHeight = 0;
new ResizeObserver(() => {
  const height = Math.ceil(document.body.getBoundingClientRect().height);
  if (Math.abs(height - reportedHeight) > 4) {
    reportedHeight = height;
    post("size", { height });
  }
}).observe(document.body);
function event(id: string, event: string, value: unknown) {
  if (!worker) return;
  clearTimeout(watchdog);
  watchdog = setTimeout(fail, 1500);
  worker.postMessage({ type: "event", id, event, value });
}
function target(id: unknown): HTMLElement {
  if (typeof id !== "string" || !/^[a-zA-Z][\w-]{0,63}$/.test(id))
    throw new Error("Invalid element ID");
  const found = resource.querySelector<HTMLElement>("#" + CSS.escape(id));
  if (!found) throw new Error("Unknown element");
  return found;
}
function finite(value: unknown): number {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    Math.abs(value) > 100000
  )
    throw new Error("Invalid number");
  return value;
}
function svg(name: string) {
  return document.createElementNS("http://www.w3.org/2000/svg", name);
}
function apply(command: any) {
  if (command.type === "state") {
    post("state", plainJson(command.value));
    return;
  }
  if (command.type === "animate") {
    clearInterval(animation);
    animation = setInterval(
      () => event("animation", "tick", Date.now()),
      1000 / 30,
    );
    return;
  }
  const element = target(command.id);
  if (command.type === "patch") {
    const value = command.value;
    if (!value || typeof value !== "object") throw new Error("Invalid patch");
    for (const key of Object.keys(value))
      if (!["text", "value", "classes", "attributes"].includes(key))
        throw new Error("Unknown patch");
    if (value.text !== undefined)
      element.textContent = String(value.text).slice(0, 10000);
    if (
      value.value !== undefined &&
      (element instanceof HTMLInputElement ||
        element instanceof HTMLSelectElement)
    )
      element.value = String(value.value);
    if (value.classes !== undefined)
      element.className = String(value.classes).slice(0, 200);
    for (const [key, val] of Object.entries(value.attributes || {})) {
      if (
        !["aria-label", "aria-live", "min", "max", "step", "disabled"].includes(
          key,
        )
      )
        throw new Error("Invalid attribute");
      element.setAttribute(key, String(val).slice(0, 500));
    }
  } else if (command.type === "listen") {
    if (!["click", "input", "change"].includes(command.event))
      throw new Error("Invalid event");
    element.addEventListener(command.event, () =>
      event(
        command.id,
        command.event,
        "value" in element ? (element as HTMLInputElement).value : null,
      ),
    );
  } else if (command.type === "math") {
    // Trusted library output only: no raw HTML from the resource reaches the DOM.
    element.innerHTML = katex.renderToString(
      String(command.value).slice(0, 2000),
      {
        throwOnError: false,
        trust: false,
        strict: "ignore",
        maxExpand: 1000,
        maxSize: 20,
        output: "htmlAndMathml",
      },
    );
  } else if (command.type === "plot") {
    const points = command.value?.points;
    if (!Array.isArray(points) || points.length < 2 || points.length > 1000)
      throw new Error("Invalid points");
    const pairs = points.map((p: any) => [finite(p[0]), finite(p[1])]);
    const xs = pairs.map((p) => p[0]),
      ys = pairs.map((p) => p[1]);
    const minX = Math.min(...xs),
      minY = Math.min(...ys),
      dx = Math.max(...xs) - minX || 1,
      dy = Math.max(...ys) - minY || 1;
    const chart = svg("svg");
    chart.setAttribute("viewBox", "0 0 600 300");
    chart.setAttribute("role", "img");
    chart.setAttribute(
      "aria-label",
      String(command.value.label || "Gráfica").slice(0, 500),
    );
    const path = svg("polyline");
    path.setAttribute(
      "points",
      pairs
        .map(
          (p) =>
            `${30 + ((p[0] - minX) / dx) * 540},${270 - ((p[1] - minY) / dy) * 240}`,
        )
        .join(" "),
    );
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#122245");
    path.setAttribute("stroke-width", "3");
    const axis = svg("path");
    axis.setAttribute("d", "M30 20V270H580");
    axis.setAttribute("fill", "none");
    axis.setAttribute("stroke", "#b59957");
    chart.append(axis, path);
    element.replaceChildren(chart);
    const label = document.createElement("p");
    label.textContent = String(command.value.label || "");
    element.append(label);
  } else if (command.type === "draw") {
    if (
      !(element instanceof HTMLCanvasElement) ||
      !Array.isArray(command.value) ||
      command.value.length > 1000
    )
      throw new Error("Invalid canvas command");
    const ctx = element.getContext("2d")!;
    ctx.strokeStyle = "#122245";
    ctx.fillStyle = "#b59957";
    ctx.lineWidth = 3;
    for (const op of command.value) {
      ctx.beginPath();
      if (op.op === "clear") ctx.clearRect(0, 0, element.width, element.height);
      else if (op.op === "line") {
        ctx.moveTo(finite(op.x), finite(op.y));
        ctx.lineTo(finite(op.x2), finite(op.y2));
        ctx.stroke();
      } else if (op.op === "circle") {
        ctx.arc(
          finite(op.x),
          finite(op.y),
          Math.abs(finite(op.r)),
          0,
          Math.PI * 2,
        );
        ctx.fill();
      } else throw new Error("Unknown drawing command");
    }
  } else if (command.type === "mount") {
    // New nodes use a safe tree schema, not raw HTML or host references.
    let count = 0;
    function node(spec: any): HTMLElement {
      if (
        ++count > 1000 ||
        !["div", "span", "p", "button", "label", "input"].includes(spec.tag)
      )
        throw new Error("Invalid node");
      const result = document.createElement(spec.tag);
      if (spec.id && /^[a-zA-Z][\w-]{0,63}$/.test(spec.id)) result.id = spec.id;
      if (spec.text) result.textContent = String(spec.text).slice(0, 10000);
      if (spec.children)
        for (const child of spec.children) result.append(node(child));
      return result;
    }
    if (!Array.isArray(command.value)) throw new Error("Invalid tree");
    element.replaceChildren(...command.value.map(node));
    if (resource.querySelectorAll("*").length > 1000)
      throw new Error("Node limit");
  } else throw new Error("Unknown capability");
}
function load(pkg: InteractivePackage, state?: Record<string, unknown>) {
  stop();
  plainJson(pkg, 300 * 1024);
  if (pkg.schemaVersion !== 1) throw new Error("Unsupported package");
  lastPackage = pkg;
  document.getElementById("title")!.textContent = pkg.title;
  document.getElementById("instructions")!.textContent = pkg.instructions;
  document.getElementById("alternative")!.textContent = pkg.textAlternative;
  resource.innerHTML = safeMarkup(pkg.html);
  resource.inert = true;
  style.textContent = safeCss(pkg.css);
  status.textContent = "Preparando experiencia…";
  worker = new Worker(new URL("./runtime.worker.ts", import.meta.url), {
    type: "module",
  });
  worker.onerror = fail;
  worker.onmessage = (event) => {
    clearTimeout(watchdog);
    if (event.data.type === "error") {
      fail();
      return;
    }
    try {
      for (const command of plainJson(event.data.commands, 200000) as any[])
        apply(command);
      status.textContent = "Listo para explorar.";
      resource.inert = false;
    } catch {
      fail();
    }
  };
  watchdog = setTimeout(fail, 12000);
  worker.postMessage({
    type: "load",
    code: pkg.javascript,
    state: plainJson(state || pkg.initialState),
  });
}
window.addEventListener("message", (event) => {
  const permitted = ["http://127.0.0.1:5173", "http://localhost:5173"];
  if (event.source !== window.parent || !permitted.includes(event.origin))
    return;
  try {
    const msg = plainJson(event.data, 350000) as any;
    if (
      msg.protocolVersion !== 1 ||
      typeof msg.channelId !== "string" ||
      msg.channelId.length < 16 ||
      !Number.isSafeInteger(msg.sequence) ||
      msg.sequence < 1
    )
      return;
    if (channel && (msg.channelId !== channel || msg.sequence <= sequence))
      return;
    channel = msg.channelId;
    parentOrigin = event.origin;
    sequence = msg.sequence;
    if (msg.type === "load") load(msg.payload.package, msg.payload.state);
    else if (msg.type === "reset" && lastPackage) load(lastPackage);
  } catch {
    fail();
  }
});
window.addEventListener("pagehide", stop);
