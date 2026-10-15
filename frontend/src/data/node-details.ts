import {
  WS_NODE_DETAILS,
  type NodeDetails,
  type NodeDetailsRequest,
} from "../contract";
import { isAdmin, type Connection, type HomeAssistant } from "../ha-types";

export type NodeDetailsKey = Omit<NodeDetailsRequest, "type">;

export type DetailsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; details: NodeDetails };

const IDLE: DetailsState = { status: "idle" };

/** One selected node's details; a new key, connection or lifecycle invalidates all answers. */
export class NodeDetailsFetcher {
  private current: DetailsState = IDLE;
  private keyId: string | undefined;
  private connection: Connection | undefined;
  private generation = 0;

  constructor(private readonly onChange: () => void) {}

  get state(): DetailsState {
    return this.current;
  }

  /** Point at one selection; unchanged keys share only their current result. */
  select(
    hass: HomeAssistant | undefined,
    key: NodeDetailsKey | undefined,
  ): void {
    const keyId =
      key && isAdmin(hass) && !key.node_id.startsWith("group:")
        ? JSON.stringify([key.entry_id, key.site_id, key.node_id])
        : undefined;
    const connection = hass?.connection;
    if (keyId === this.keyId && connection === this.connection) return;
    this.stop();
    this.keyId = keyId;
    this.connection = connection;
    if (!hass || !key || keyId === undefined) return;
    const generation = this.generation;
    this.current = { status: "loading" };
    const request: NodeDetailsRequest = { type: WS_NODE_DETAILS, ...key };
    // Both synchronous throws and rejected promises mean no details; no retry.
    void this.fetch(hass, request, generation);
  }

  stop(): void {
    this.generation++;
    this.current = IDLE;
    this.keyId = undefined;
    this.connection = undefined;
  }

  private async fetch(
    hass: HomeAssistant,
    request: NodeDetailsRequest,
    generation: number,
  ): Promise<void> {
    let next: DetailsState;
    try {
      const details = await hass.callWS<NodeDetails>(request);
      next = { status: "ready", details };
    } catch {
      next = IDLE;
    }
    if (generation !== this.generation) return;
    this.current = next;
    this.onChange();
  }
}

export type NodeAction = "copy_ip" | "copy_mac" | "open_device" | "open_entity";

const has = (value: string | undefined): value is string =>
  typeof value === "string" && value !== "";

/** Only supplied administrator details provide menu actions, in contract order. */
export function nodeActions(
  details: NodeDetails | undefined,
  admin: boolean,
): NodeAction[] {
  if (!admin || !details) return [];
  const actions: NodeAction[] = [];
  if (has(details.ip_address)) actions.push("copy_ip");
  if (has(details.mac_address)) actions.push("copy_mac");
  if (has(details.device_id)) actions.push("open_device");
  if (has(details.entity_id)) actions.push("open_entity");
  return actions;
}
