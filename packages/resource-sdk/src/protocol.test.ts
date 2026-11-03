import { describe, expect, it } from "vitest";

import { parseHostMessage } from "./protocol";

describe("resource protocol", () => {
  it("accepts a correctly versioned load command", () => {
    expect(
      parseHostMessage({
        protocolVersion: 1,
        channelId: "channel-1",
        sequence: 1,
        type: "load",
        payload: { resourceVersionId: "resource-version-1" },
      }),
    ).toMatchObject({ type: "load", sequence: 1 });
  });

  it("rejects unknown message types and prototype-bearing payloads", () => {
    expect(() =>
      parseHostMessage({
        protocolVersion: 1,
        channelId: "channel-1",
        sequence: 1,
        type: "networkRequest",
        payload: {},
      }),
    ).toThrow("Unsupported resource message type");
    expect(() => parseHostMessage(Object.create({ type: "load" }))).toThrow(
      "plain object",
    );
  });
});
