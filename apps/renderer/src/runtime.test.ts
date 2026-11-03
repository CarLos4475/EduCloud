import { describe, expect, it } from "vitest";
import { runScript } from "./runtime";

describe("isolated resource VM", () => {
  it("computes data without browser APIs", async () => {
    const commands = await runScript(
      'ui.patch("result", {text: String(6*7)}); ui.patch("access",{text:[typeof window,typeof document,typeof fetch,typeof WebSocket].join(",")});',
    );
    expect(commands[0]).toEqual({
      type: "patch",
      id: "result",
      value: { text: "42" },
    });
    expect(commands[1].value.text).toBe(
      "undefined,undefined,undefined,undefined",
    );
  });
  it("interrupts infinite loops and rejects excessive commands", async () => {
    await expect(runScript("while(true) {}")).rejects.toThrow();
    await expect(
      runScript('for(let i=0;i<2000;i++) ui.patch("x",{text:"x"});'),
    ).rejects.toThrow();
  });
});
