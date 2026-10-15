import { afterEach, describe, expect, it } from "vitest";
import {
  NODE_KINDS,
  type SiteTopology,
  type TopologyEdge,
  type TopologyNode,
} from "../src/contract";
import { makeLocalize } from "../src/localize";
import { buildModel } from "../src/model/graph-model";
import { CULL_THRESHOLD, layoutModel } from "../src/model/layout";
import type { UitGraphView } from "../src/views/graph-view";
import "../src/views/graph-view";
import { cleanup, fixtureSnapshot, mount } from "./helpers";

afterEach(cleanup);

/** A gateway, a core switch, 18 access switches/APs and 500 clients spread across them. */
function bigSnapshot(): SiteTopology {
  const nodes: TopologyNode[] = [
    { id: "dev:gw", kind: "gateway", name: "Gateway", state: "online" },
    { id: "dev:core", kind: "switch", name: "Core", state: "online" },
  ];
  const edges: TopologyEdge[] = [
    {
      source: "dev:core",
      target: "dev:gw",
      medium: "wired",
      parent_port: 1,
      speed_mbps: 10000,
    },
  ];
  for (let i = 0; i < 18; i++) {
    nodes.push({
      id: `dev:d${i}`,
      kind: i % 3 === 0 ? "access_point" : "switch",
      name: `Device ${i}`,
      state: "online",
    });
    edges.push({
      source: `dev:d${i}`,
      target: "dev:core",
      medium: "wired",
      parent_port: i + 2,
      speed_mbps: 1000,
    });
  }
  for (let i = 0; i < 500; i++) {
    const parent = `dev:d${i % 18}`;
    nodes.push({
      id: `cli:c${i}`,
      kind: "client",
      name: `Client ${i}`,
      state: "online",
      connection: i % 2 ? "wired" : "wireless",
    });
    edges.push({
      source: `cli:c${i}`,
      target: parent,
      medium: i % 2 ? "wired" : "wireless",
    });
  }
  return fixtureSnapshot({ nodes, edges, truncation: null });
}

const ui = {
  kinds: new Set(NODE_KINDS),
  clients: "expanded" as const,
  toggledGroups: new Set<string>(),
};

describe("large site (20 devices, 500 clients, fully expanded)", () => {
  it("builds and lays out within budget", () => {
    const snapshot = bigSnapshot();
    const start = performance.now();
    const model = buildModel(snapshot, ui);
    const layout = layoutModel(model, "comfortable", "vertical");
    const ms = performance.now() - start;
    console.info(
      `[benchmark] model + layout for ${layout.positions.size} nodes: ${ms.toFixed(1)} ms`,
    );
    expect(layout.positions.size).toBe(20 + 18 + 500); // devices + one group per access device + clients
    expect(ms).toBeLessThan(500); // generous for CI runners; typical is far lower
  });

  it("renders only the nodes near the viewport", async () => {
    const model = buildModel(bigSnapshot(), ui);
    expect(model.visuals.size).toBeGreaterThan(CULL_THRESHOLD);
    const el = await mount<UitGraphView>("uit-graph-view", {
      model,
      localize: makeLocalize("en"),
      siteName: "Big",
      reducedMotion: true,
    });
    el.setViewportSize(800, 600);
    await el.updateComplete;
    const rendered = el.shadowRoot!.querySelectorAll("g.nodes g.node").length;
    console.info(
      `[benchmark] rendered ${rendered} of ${model.visuals.size} nodes`,
    );
    expect(rendered).toBeGreaterThan(0);
    expect(rendered).toBeLessThan(model.visuals.size);
  });
});

describe("large site in the tiered layout", () => {
  it("builds and lays out within budget", () => {
    const model = buildModel(bigSnapshot(), ui);
    const start = performance.now();
    const layout = layoutModel(model, "comfortable", "vertical", "tiered");
    const ms = performance.now() - start;
    console.info(
      `[benchmark] tiered layout for ${layout.positions.size} nodes: ${ms.toFixed(1)} ms`,
    );
    expect(layout.positions.size).toBe(20 + 18 + 500);
    expect(ms).toBeLessThan(500);
    // All 500 clients share one row, below their 18 groups.
    const clientRows = new Set(
      [...model.visuals.values()]
        .filter((v) => v.type === "client")
        .map((v) => layout.positions.get(v.id)!.y),
    );
    expect(clientRows.size).toBe(1);
    const groupY = layout.positions.get("group:dev:d0")!.y;
    expect([...clientRows][0]).toBeGreaterThan(groupY);
  });

  it("renders only the nodes near the viewport", async () => {
    const model = buildModel(bigSnapshot(), ui);
    const el = await mount<UitGraphView>("uit-graph-view", {
      model,
      layoutMode: "tiered",
      localize: makeLocalize("en"),
      siteName: "Big",
      reducedMotion: true,
    });
    el.setViewportSize(800, 600);
    await el.updateComplete;
    const rendered = el.shadowRoot!.querySelectorAll("g.nodes g.node").length;
    console.info(
      `[benchmark] tiered rendered ${rendered} of ${model.visuals.size} nodes`,
    );
    expect(rendered).toBeGreaterThan(0);
    expect(rendered).toBeLessThan(model.visuals.size);
  });
});
