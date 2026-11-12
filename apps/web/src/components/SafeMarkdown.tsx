import Markdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

/** Models sometimes write math as \( ... \) or \[ ... \]; the renderer expects $ delimiters. */
export function normalizeMath(text: string) {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, math) => `$$${math}$$`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, math) => `$${math}$`);
}

export function SafeMarkdown({ text }: { text: string }) {
  return (
    <div className="safe-markdown">
      <Markdown
        skipHtml
        remarkPlugins={[remarkMath]}
        rehypePlugins={[
          [
            rehypeKatex,
            { trust: false, strict: "ignore", maxExpand: 1000, maxSize: 20 },
          ],
        ]}
        disallowedElements={[
          "img",
          "iframe",
          "script",
          "style",
          "form",
          "input",
        ]}
        components={{ a: ({ children }) => <span>{children}</span> }}
      >
        {normalizeMath(text.slice(0, 12000))}
      </Markdown>
    </div>
  );
}
