import { describe, expect, it, vi } from "vitest";
import { WS_NODE_DETAILS, type NodeDetails } from "../src/contract";
import { NodeDetailsFetcher, nodeActions } from "../src/data/node-details";
import { isAdmin, type HomeAssistant } from "../src/ha-types";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const hassFor = (isAdminUser: boolean | undefined, callWS = vi.fn()) =>
  ({
    callWS,
    user: isAdminUser === undefined ? undefined : { is_admin: isAdminUser },
  }) as unknown as HomeAssistant;

const KEY = { entry_id: "entry-1", site_id: "site-1", node_id: "dev:a" };
const DETAILS: NodeDetails = {
  kind: "switch",
  ip_address: "192.0.2.10",
  mac_address: "aa:bb:cc:dd:ee:ff",
  device_id: "reg-a",
  entity_id: "sensor.a",
};

/** Let promise callbacks (the fetcher's then/catch) run. */
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("isAdmin", () => {
  it("is true only for an explicit administrator", () => {
    expect(isAdmin(hassFor(true))).toBe(true);
    expect(isAdmin(hassFor(false))).toBe(false);
    expect(isAdmin(hassFor(undefined))).toBe(false);
    expect(isAdmin(undefined)).toBe(false);
    expect(isAdmin({ user: {} } as unknown as HomeAssistant)).toBe(false);
  });
});

describe("NodeDetailsFetcher", () => {
  function setup() {
    const onChange = vi.fn();
    const fetcher = new NodeDetailsFetcher(onChange);
    const calls: ReturnType<typeof deferred<NodeDetails>>[] = [];
    const callWS = vi.fn(() => {
      const call = deferred<NodeDetails>();
      calls.push(call);
      return call.promise;
    });
    return { fetcher, onChange, calls, callWS };
  }

  it("never calls the websocket for a non-administrator", () => {
    const { fetcher, onChange, callWS } = setup();
    for (const hass of [
      hassFor(false, callWS),
      hassFor(undefined, callWS),
      undefined,
    ]) {
      fetcher.select(hass, KEY);
      expect(fetcher.state).toEqual({ status: "idle" });
    }
    expect(callWS).not.toHaveBeenCalled();
    expect(onChange).not.toHaveBeenCalled();
  });

  it("sends the exact command and publishes the result", async () => {
    const { fetcher, onChange, calls, callWS } = setup();
    fetcher.select(hassFor(true, callWS), KEY);
    expect(fetcher.state).toEqual({ status: "loading" });
    expect(callWS).toHaveBeenCalledOnce();
    expect(callWS).toHaveBeenCalledWith({
      type: WS_NODE_DETAILS,
      entry_id: "entry-1",
      site_id: "site-1",
      node_id: "dev:a",
    });
    expect(WS_NODE_DETAILS).toBe("unifi_insights/topology/node_details");

    calls[0]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "ready", details: DETAILS });
    expect(onChange).toHaveBeenCalledOnce();
  });

  it("does not ask again for the same selection", () => {
    const { fetcher, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    fetcher.select(hassFor(true, callWS), { ...KEY });
    expect(callWS).toHaveBeenCalledOnce();
  });

  it("ignores a stale response after another node was selected", async () => {
    const { fetcher, onChange, calls, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    fetcher.select(hass, { ...KEY, node_id: "dev:b" });
    expect(callWS).toHaveBeenCalledTimes(2);

    // The first node's answer arrives last and must not touch node B.
    calls[1]!.resolve({ kind: "switch", ip_address: "192.0.2.20" });
    await flush();
    calls[0]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({
      status: "ready",
      details: { kind: "switch", ip_address: "192.0.2.20" },
    });
    expect(onChange).toHaveBeenCalledOnce();
  });

  it("ignores a stale answer that arrives while the next node still loads", async () => {
    const { fetcher, onChange, calls, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    fetcher.select(hass, { ...KEY, node_id: "dev:b" });
    calls[0]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "loading" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("ignores a stale failure of the previous selection", async () => {
    const { fetcher, onChange, calls, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    fetcher.select(hass, { ...KEY, node_id: "dev:b" });
    calls[0]!.reject({ code: "node_not_found", message: "" });
    await flush();
    expect(fetcher.state).toEqual({ status: "loading" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("clears the cached details when the selection changes or ends", async () => {
    const { fetcher, calls, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    calls[0]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state.status).toBe("ready");

    fetcher.select(hass, { ...KEY, node_id: "dev:b" });
    expect(fetcher.state).toEqual({ status: "loading" });

    fetcher.select(hass, undefined);
    expect(fetcher.state).toEqual({ status: "idle" });
    // A late answer for the ended selection is dropped.
    calls[1]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
  });

  it("asks again when the same node is selected after the selection ended", async () => {
    const { fetcher, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    fetcher.select(hass, undefined);
    fetcher.select(hass, KEY);
    expect(callWS).toHaveBeenCalledTimes(2);
  });

  it("clears the cached details when the site changes", async () => {
    const { fetcher, onChange, calls, callWS } = setup();
    const hass = hassFor(true, callWS);
    fetcher.select(hass, KEY);
    calls[0]!.resolve(DETAILS);
    await flush();
    onChange.mockClear();

    // Same node id, other site: a different selection.
    fetcher.select(hass, { ...KEY, site_id: "site-2" });
    expect(fetcher.state).toEqual({ status: "loading" });
    expect(callWS).toHaveBeenLastCalledWith(
      expect.objectContaining({ site_id: "site-2", node_id: "dev:a" }),
    );
    calls[1]!.resolve(DETAILS);
    await flush();
    // The answer for site-2 is dropped once the selection moved on.
    fetcher.select(hass, KEY);
    calls[2]!.resolve(DETAILS);
    await flush();
    onChange.mockClear();
    expect(fetcher.state.status).toBe("ready");

    // Same site and node ids under another entry: yet another selection.
    fetcher.select(hass, { ...KEY, entry_id: "entry-2" });
    expect(fetcher.state).toEqual({ status: "loading" });
    expect(callWS).toHaveBeenLastCalledWith(
      expect.objectContaining({ entry_id: "entry-2" }),
    );
    expect(onChange).not.toHaveBeenCalled();
  });

  it("goes idle and drops the answer when the user stops being an administrator", async () => {
    const { fetcher, calls, callWS } = setup();
    fetcher.select(hassFor(true, callWS), KEY);
    fetcher.select(hassFor(false, callWS), KEY);
    expect(fetcher.state).toEqual({ status: "idle" });
    calls[0]!.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
  });

  it.each([
    [{ code: "unauthorized", message: "Unauthorized" }],
    [{ code: "node_not_found", message: "" }],
    [{ code: "entry_not_loaded", message: "later" }],
  ])("returns no details for a rejection %j", async (rejection) => {
    const { fetcher, onChange, calls, callWS } = setup();
    fetcher.select(hassFor(true, callWS), KEY);
    calls[0]!.reject(rejection);
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
    expect(onChange).toHaveBeenCalledOnce();
  });

  it("discards a rejection that is not a websocket error", async () => {
    const { fetcher, calls, callWS } = setup();
    fetcher.select(hassFor(true, callWS), KEY);
    calls[0]!.reject(new Error("boom"));
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
  });
});

describe("nodeActions", () => {
  it("offers all details in order only for administrators", () => {
    expect(nodeActions(DETAILS, true)).toEqual([
      "copy_ip",
      "copy_mac",
      "open_device",
      "open_entity",
    ]);
    expect(nodeActions(DETAILS, false)).toEqual([]);
    expect(nodeActions(undefined, true)).toEqual([]);
    expect(nodeActions({ kind: "client" }, true)).toEqual([]);
    expect(
      nodeActions(
        {
          kind: "client",
          ip_address: "",
          mac_address: "",
          device_id: "",
          entity_id: "",
        },
        true,
      ),
    ).toEqual([]);
  });
  it.each([
    ["ip_address", "copy_ip"],
    ["mac_address", "copy_mac"],
    ["device_id", "open_device"],
    ["entity_id", "open_entity"],
  ] as const)("offers only %s when present", (field, action) => {
    expect(nodeActions({ kind: "client", [field]: "value" }, true)).toEqual([
      action,
    ]);
  });
});

describe("plan v3 fetcher lifecycle", () => {
  it("does not request group ids", () => {
    const callWS = vi.fn();
    const fetcher = new NodeDetailsFetcher(vi.fn());
    fetcher.select(hassFor(true, callWS), {
      ...KEY,
      node_id: "group:dev:a",
    });
    expect(callWS).not.toHaveBeenCalled();
    expect(fetcher.state).toEqual({ status: "idle" });
  });

  it("clears the cache and drops responses on connection changes", async () => {
    const stale = deferred<NodeDetails>();
    const fresh = deferred<NodeDetails>();
    const callWS = vi
      .fn()
      .mockImplementationOnce(() => stale.promise)
      .mockImplementation(() => fresh.promise);
    const fetcher = new NodeDetailsFetcher(vi.fn());
    const first = {
      ...hassFor(true, callWS),
      connection: {},
    } as HomeAssistant;
    fetcher.select(first, KEY);
    const next = { ...first, connection: {} } as HomeAssistant;
    fetcher.select(next, KEY);
    expect(callWS).toHaveBeenCalledTimes(2);
    stale.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "loading" });
    fresh.resolve({ ...DETAILS, ip_address: "192.0.2.20" });
    await flush();
    expect(fetcher.state).toEqual({
      status: "ready",
      details: { ...DETAILS, ip_address: "192.0.2.20" },
    });
    fetcher.select({ ...next, connection: {} } as HomeAssistant, KEY);
    expect(fetcher.state).toEqual({ status: "loading" });
  });

  it("ignores a response after teardown", async () => {
    const pending = deferred<NodeDetails>();
    const changed = vi.fn();
    const fetcher = new NodeDetailsFetcher(changed);
    fetcher.select(
      hassFor(
        true,
        vi.fn(() => pending.promise),
      ),
      KEY,
    );
    fetcher.stop();
    pending.resolve(DETAILS);
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
    expect(changed).not.toHaveBeenCalled();
  });

  it("returns no details on errors and does not retry the same key", async () => {
    const callWS = vi.fn(async () => {
      throw { code: "node_not_found" };
    });
    const hass = hassFor(true, callWS);
    const fetcher = new NodeDetailsFetcher(vi.fn());
    fetcher.select(hass, KEY);
    await flush();
    expect(fetcher.state).toEqual({ status: "idle" });
    fetcher.select(hass, KEY);
    expect(callWS).toHaveBeenCalledOnce();
  });
});
