import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { SafeMarkdown } from "./SafeMarkdown";

describe("academic responses", () => {
  it("renders math and code while rejecting active HTML and links", () => {
    const html = renderToStaticMarkup(
      <SafeMarkdown
        text={
          "<script>alert(1)</script>\n\n[abrir](javascript:alert(1))\n\n![remoto](https://example.test/tracker)\n\n$V=IR$\n\n```python\nprint(1)\n```"
        }
      />,
    );
    expect(html).not.toContain("<script");
    expect(html).not.toContain("<img");
    expect(html).not.toContain("javascript:");
    expect(html).toContain("katex");
    expect(html).toContain("print(1)");
  });
});
