import Markdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

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
        {text.slice(0, 12000)}
      </Markdown>
    </div>
  );
}
