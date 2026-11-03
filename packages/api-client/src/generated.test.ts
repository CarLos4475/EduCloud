import { describe, expect, it } from "vitest";

import type { ApiError, SourceRef } from "./generated";
import fixtures from "../../../tests/fixtures/contracts/valid-contracts.json";

describe("generated API contracts", () => {
  it("uses the same camelCase public names as the backend schema", () => {
    const source: SourceRef = fixtures.sourceRef;
    const error: ApiError = fixtures.apiError;

    expect(source.materialId).toBe("material-1");
    expect(error.requestId).toBe("request-1");
  });
});
