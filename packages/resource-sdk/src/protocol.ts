export type ResourceMessageType =
  "load" | "reset" | "saveState" | "requestPractice";

export type ResourceMessage = {
  protocolVersion: 1;
  channelId: string;
  sequence: number;
  type: ResourceMessageType;
  payload: Record<string, unknown>;
};

const messageTypes = new Set<ResourceMessageType>([
  "load",
  "reset",
  "saveState",
  "requestPractice",
]);

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function requireNonEmptyString(value: unknown, name: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${name} must be a non-empty string`);
  }
  return value;
}

function parseLoadPayload(
  payload: Record<string, unknown>,
): Record<string, unknown> {
  requireNonEmptyString(payload.resourceVersionId, "payload.resourceVersionId");
  return payload;
}

export function parseHostMessage(value: unknown): ResourceMessage {
  if (!isPlainObject(value))
    throw new Error("Resource message must be a plain object");
  if (value.protocolVersion !== 1)
    throw new Error("Unsupported resource protocol version");
  const type = value.type;
  if (
    typeof type !== "string" ||
    !messageTypes.has(type as ResourceMessageType)
  ) {
    throw new Error("Unsupported resource message type");
  }
  const payload = value.payload;
  if (!isPlainObject(payload))
    throw new Error("Resource message payload must be a plain object");
  requireNonEmptyString(value.channelId, "channelId");
  if (!Number.isSafeInteger(value.sequence) || (value.sequence as number) < 1) {
    throw new Error("sequence must be a positive safe integer");
  }
  if (type === "load") parseLoadPayload(payload);
  return {
    protocolVersion: 1,
    channelId: value.channelId as string,
    sequence: value.sequence as number,
    type: type as ResourceMessageType,
    payload,
  };
}
