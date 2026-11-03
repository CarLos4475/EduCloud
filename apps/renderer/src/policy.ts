import DOMPurify from "dompurify";
import * as css from "css-tree";

export const tags = [
  "div",
  "span",
  "p",
  "section",
  "h2",
  "h3",
  "h4",
  "label",
  "input",
  "button",
  "select",
  "option",
  "output",
  "ul",
  "ol",
  "li",
  "strong",
  "em",
  "table",
  "thead",
  "tbody",
  "tr",
  "td",
  "th",
  "canvas",
  "br",
];
const attrs = [
  "id",
  "class",
  "type",
  "value",
  "min",
  "max",
  "step",
  "for",
  "width",
  "height",
  "role",
  "aria-label",
  "aria-live",
  "disabled",
  "selected",
];

export function safeMarkup(markup: string): string {
  const clean = DOMPurify.sanitize(markup, {
    ALLOWED_TAGS: tags,
    ALLOWED_ATTR: attrs,
    ALLOW_DATA_ATTR: false,
    FORBID_ATTR: ["style"],
    SANITIZE_NAMED_PROPS: false,
  });
  const template = document.createElement("template");
  template.innerHTML = clean;
  if (template.content.querySelectorAll("*").length > 1000)
    throw new Error("Too many nodes");
  for (const input of template.content.querySelectorAll("input")) {
    if (!["range", "number", "text", "checkbox", "radio"].includes(input.type))
      input.type = "text";
  }
  for (const canvas of template.content.querySelectorAll("canvas")) {
    canvas.width = Math.min(Math.max(canvas.width, 1), 800);
    canvas.height = Math.min(Math.max(canvas.height, 1), 600);
  }
  return template.innerHTML;
}

export function safeCss(source: string): string {
  if (source.length > 64000) throw new Error("CSS limit exceeded");
  const ast = css.parse(source);
  css.walk(ast, (node) => {
    if (node.type === "Atrule" || node.type === "Url" || node.type === "Raw")
      throw new Error("Unsupported CSS construct");
    if (
      node.type === "Declaration" &&
      !/^(color|background-color|border(-[a-z]+)?|padding(-[a-z]+)?|margin(-[a-z]+)?|font-(size|weight|family)|text-align|display|gap|grid-template-columns|flex(-[a-z]+)?|width|height|max-width|min-height|opacity)$/.test(
        node.property,
      )
    )
      throw new Error("Unsupported CSS property");
    if (
      (node.type === "Dimension" ||
        node.type === "Number" ||
        node.type === "Percentage") &&
      (!Number.isFinite(Number(node.value)) ||
        Math.abs(Number(node.value)) > 2000)
    )
      throw new Error("CSS size limit");
  });
  css.walk(ast, (node) => {
    if (node.type === "Rule" && node.prelude.type === "SelectorList") {
      node.prelude.children.forEach((selector) => {
        if (selector.type === "Selector") {
          selector.children.prependData({ type: "Combinator", name: " " });
          selector.children.prependData({
            type: "IdSelector",
            name: "resource",
          });
        }
      });
    }
  });
  return css.generate(ast);
}

export function plainJson(value: unknown, max = 50000): unknown {
  const text = JSON.stringify(value);
  if (!text || text.length > max) throw new Error("JSON limit exceeded");
  return JSON.parse(text, (key, value) => {
    if (["__proto__", "constructor", "prototype"].includes(key))
      throw new Error("Forbidden key");
    return value;
  });
}
