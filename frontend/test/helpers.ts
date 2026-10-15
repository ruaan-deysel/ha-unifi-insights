import fixture from "./fixtures/site-topology.json";
import {
  WS_NODE_DETAILS,
  type NodeDetails,
  type SiteTopology,
  type TopologySource,
} from "../src/contract";

/** A fresh deep copy of the Python-generated snapshot, with optional overrides. */
export function fixtureSnapshot(
  overrides: Partial<SiteTopology> = {},
): SiteTopology {
  const copy = JSON.parse(JSON.stringify(fixture)) as SiteTopology;
  return { ...copy, ...overrides };
}

/** What the backend pushes for entry_unloaded / site_unavailable. */
export function unavailableSnapshot(code: string): SiteTopology {
  return fixtureSnapshot({
    revision: "",
    status: "unavailable",
    issues: [{ code, severity: "error" }],
    nodes: [],
    edges: [],
    unresolved: [],
    truncation: null,
  });
}

export const SOURCES_ONE: TopologySource[] = [
  {
    entry_id: "entry-1",
    title: "Crestwood",
    sites: [{ id: "site-1", name: "Home" }],
  },
];

export const SOURCES_MULTI: TopologySource[] = [
  {
    entry_id: "entry-1",
    title: "Crestwood",
    sites: [
      { id: "site-1", name: "Home" },
      { id: "site-2", name: "Cabin" },
    ],
  },
  {
    entry_id: "entry-2",
    title: "Office",
    sites: [{ id: "default", name: "Default" }],
  },
];

import { NODE_KINDS as ALL_KINDS } from "../src/contract";
import {
  buildModel,
  type GraphModel,
  type UiState,
} from "../src/model/graph-model";

export function fixtureModel(
  ui: Partial<UiState> = {},
  snapshot: SiteTopology = fixtureSnapshot(),
): GraphModel {
  return buildModel(snapshot, {
    kinds: new Set(ALL_KINDS),
    clients: "collapsed",
    toggledGroups: new Set(),
    ...ui,
  });
}

export async function mount<T extends HTMLElement>(
  tag: string,
  props: Record<string, unknown> = {},
): Promise<T> {
  const el = document.createElement(tag) as T & {
    updateComplete: Promise<boolean>;
  };
  Object.assign(el, props);
  document.body.append(el);
  await el.updateComplete;
  return el;
}

export function cleanup(): void {
  document.body.replaceChildren();
  history.replaceState(null, "", "/");
}

import { vi } from "vitest";
import type { HomeAssistant, MessageBase } from "../src/ha-types";

export interface FakeSub {
  message: MessageBase;
  callback: (message: unknown) => void;
  unsubscribe: ReturnType<typeof vi.fn>;
}

/** A hass object whose sources call, subscribe and node details commands are scripted. */
export function fakeHass(
  opts: {
    sources?: TopologySource[];
    sourcesError?: unknown;
    subscribeError?: unknown;
    /** Sets `hass.user.is_admin`; without it the hass has no user at all. */
    admin?: boolean;
    /** Answer to `topology/node_details` by node id: details, or a rejection. */
    details?: Record<string, NodeDetails | { code: string; message: string }>;
  } = {},
) {
  const subs: FakeSub[] = [];
  const listeners = new Map<string, Set<() => void>>();
  const connection = {
    addEventListener: vi.fn((event: string, listener: () => void) => {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event)!.add(listener);
    }),
    removeEventListener: vi.fn((event: string, listener: () => void) => {
      listeners.get(event)?.delete(listener);
    }),
    subscribeMessage: vi.fn(
      (callback: (m: unknown) => void, message: MessageBase) => {
        if (opts.subscribeError !== undefined)
          return Promise.reject(opts.subscribeError);
        const unsubscribe = vi.fn(async () => undefined);
        subs.push({ message, callback, unsubscribe });
        return Promise.resolve(unsubscribe);
      },
    ),
  };
  const hass = {
    connection,
    callWS: vi.fn(async (message?: MessageBase) => {
      if (message?.type === WS_NODE_DETAILS) {
        const answer = opts.details?.[String(message.node_id)];
        if (answer === undefined) throw { code: "node_not_found", message: "" };
        if ("code" in answer) throw answer;
        return answer;
      }
      if (opts.sourcesError !== undefined) throw opts.sourcesError;
      return opts.sources ?? SOURCES_ONE;
    }),
    locale: { language: "en" },
    ...(opts.admin === undefined ? {} : { user: { is_admin: opts.admin } }),
  } as unknown as HomeAssistant;
  return {
    hass,
    subs,
    connection,
    push: (payload: unknown) => subs.at(-1)!.callback(payload),
    emit: (event: "ready" | "disconnected") =>
      listeners.get(event)?.forEach((listener) => listener()),
  };
}

/** Let promise callbacks and Lit updates run to completion. */
export async function settle(el: {
  updateComplete: Promise<boolean>;
}): Promise<void> {
  for (let i = 0; i < 4; i++) {
    await new Promise((resolve) => setTimeout(resolve, 0));
    await el.updateComplete;
  }
}
