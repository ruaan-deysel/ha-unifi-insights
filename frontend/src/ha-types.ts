/**
 * The slice of Home Assistant's frontend API this card uses. Declared locally
 * because custom-card-helpers is unmaintained.
 */

export interface MessageBase {
  type: string;
  [key: string]: unknown;
}

export type UnsubscribeFunc = () => Promise<void>;

/** Socket lifecycle events a card cares about. */
export type ConnectionEvent = "ready" | "disconnected";
export type ConnectionListener = (connection: Connection) => void;

export interface Connection {
  addEventListener(event: ConnectionEvent, listener: ConnectionListener): void;
  removeEventListener(
    event: ConnectionEvent,
    listener: ConnectionListener,
  ): void;
  subscribeMessage<T>(
    callback: (message: T) => void,
    message: MessageBase,
    options?: { resubscribe?: boolean },
  ): Promise<UnsubscribeFunc>;
}

export interface HomeAssistant {
  connection: Connection;
  callWS<T>(message: MessageBase): Promise<T>;
  language?: string;
  locale?: { language: string };
  user?: { is_admin: boolean };
}

/** Whether the signed-in user is an administrator; anything unknown counts as no. */
export function isAdmin(hass: HomeAssistant | undefined): boolean {
  return hass?.user?.is_admin === true;
}

/** Rejection shape of home-assistant-js-websocket commands. */
export interface WsError {
  code: string;
  message: string;
}

export function isWsError(value: unknown): value is WsError {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as WsError).code === "string"
  );
}

export function toWsError(value: unknown): WsError {
  if (isWsError(value))
    return {
      code: value.code,
      message: typeof value.message === "string" ? value.message : "",
    };
  return { code: "unknown_error", message: String(value) };
}

export function fireEvent(
  node: EventTarget,
  type: string,
  detail?: unknown,
): void {
  node.dispatchEvent(
    new CustomEvent(type, { detail, bubbles: true, composed: true }),
  );
}

/** Ask Home Assistant to open the more-info dialog of an entity. */
export function fireMoreInfo(node: EventTarget, entityId: string): void {
  fireEvent(node, "hass-more-info", { entityId });
}

/** Navigate inside the HA frontend without a page load. */
export function navigate(path: string): void {
  history.pushState(null, "", path);
  fireEvent(window, "location-changed", { replace: false });
}

export interface CardHelpers {
  createCardElement(config: {
    type: string;
    [key: string]: unknown;
  }): HTMLElement;
}

declare global {
  interface Window {
    customCards?: {
      type: string;
      name: string;
      description: string;
      preview?: boolean;
      documentationURL?: string;
    }[];
    loadCardHelpers?: () => Promise<CardHelpers>;
  }
}
