import {
    mdiArrowDownBold,
    mdiArrowUpBold,
    mdiEarth,
    mdiSpeedometer,
} from "@mdi/js";
import { html, nothing, type TemplateResult } from "lit";

import { WS_SOURCES } from "./contract";
import {
    BaseDashboardCard,
    GenericEditor,
    INTERNET_ACTIVITY_CARD_TAG,
    INTERNET_ACTIVITY_EDITOR_TAG,
    formatBps,
    formatBytesCompact,
} from "./dashboard-cards-base";
import { iconTemplate } from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnifiInsightsInternetActivityCard extends BaseDashboardCard {
    static override editorTag = INTERNET_ACTIVITY_EDITOR_TAG;

    static override properties = {
        ...BaseDashboardCard.properties,
        selectedWindow: { state: true },
    };

    declare selectedWindow: string;

    constructor() {
        super();
        this.selectedWindow = "1d";
    }

    protected get cardType(): string {
        return `custom:${INTERNET_ACTIVITY_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return WS_SOURCES;
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/internet_activity/subscribe";
    }

    protected get defaultTitle(): string {
        return "Internet Activity";
    }

    protected get headerIcon(): string {
        return mdiSpeedometer;
    }

    private resolveActiveWindow(windows: Record<string, unknown>): {
        keys: string[];
        activeWindow: string;
    } {
        const keys = ["1h", "1d", "1w", "1m"].filter((k) => k in windows);
        const activeWindow =
            this.selectedWindow in windows
                ? this.selectedWindow
                : (keys[0] ?? "1d");
        return { keys, activeWindow };
    }

    protected override renderHeaderBadge(): TemplateResult | typeof nothing {
        const windows = (this.snapshot?.windows ?? {}) as Record<string, unknown>;
        const { keys, activeWindow } = this.resolveActiveWindow(windows);
        if (keys.length <= 1) {
            return nothing;
        }
        return html`
            <div class="pill-tabs" role="group" aria-label="Time window">
                ${keys.map(
                    (w) => html`
                        <button
                            type="button"
                            class="pill-tab"
                            aria-pressed=${String(activeWindow === w)}
                            @click=${() => {
                                this.selectedWindow = w;
                            }}
                        >
                            ${w}
                        </button>
                    `,
                )}
            </div>
        `;
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">No data</div>`;
        }
        const windows = (snapshot.windows ?? {}) as Record<string, unknown>;
        const { activeWindow } = this.resolveActiveWindow(windows);
        const selected = (windows[activeWindow] ??
            windows["1d"] ??
            windows["1h"] ??
            {}) as Record<string, unknown>;
        const down = Number(selected.download_bytes ?? 0);
        const up = Number(selected.upload_bytes ?? 0);
        const total = down + up;
        const downMb = `${Math.round(down / 1_000_000)} MB`;
        const upMb = `${Math.round(up / 1_000_000)} MB`;
        const totalMb = `${Math.round(total / 1_000_000)} MB`;
        const downPct = total > 0 ? Math.round((down / total) * 100) : 50;
        const upPct = total > 0 ? 100 - downPct : 50;

        const throughput = (snapshot.throughput ?? {}) as Record<string, unknown>;
        const rxRate = formatBps(throughput.rx_bps);
        const txRate = formatBps(throughput.tx_bps);
        const entityIds = (snapshot.entity_ids ?? {}) as Record<string, string>;
        const downEntity = entityIds[`download_${activeWindow}`];
        const upEntity = entityIds[`upload_${activeWindow}`];

        return html`
            ${rxRate || txRate
                ? html`<div class="hero-banner">
                      <div class="hero-left">
                          ${iconTemplate(mdiEarth)}
                          <div>
                              <div class="hero-title">Live Throughput</div>
                              <div class="hero-meta">
                                  ↓ ${rxRate ?? "0 bps"} · ↑ ${txRate ?? "0 bps"}
                              </div>
                          </div>
                      </div>
                      <span class="chip ok">
                          <span class="status-dot"></span>Live
                      </span>
                  </div>`
                : nothing}

            <div class="kpi-grid">
                <button
                    type="button"
                    class="kpi-tile ${downEntity ? "clickable" : ""}"
                    ?disabled=${!downEntity}
                    @click=${downEntity
                        ? () => this.openMoreInfo(downEntity)
                        : nothing}
                >
                    <div class="kpi-top">
                        <span>Download</span>
                        ${iconTemplate(mdiArrowDownBold)}
                    </div>
                    <div class="kpi-value">${formatBytesCompact(down)}</div>
                    <div class="kpi-sub">${downMb} · ${downPct}%</div>
                </button>

                <button
                    type="button"
                    class="kpi-tile ${upEntity ? "clickable" : ""}"
                    ?disabled=${!upEntity}
                    @click=${upEntity
                        ? () => this.openMoreInfo(upEntity)
                        : nothing}
                >
                    <div class="kpi-top">
                        <span>Upload</span>
                        ${iconTemplate(mdiArrowUpBold)}
                    </div>
                    <div class="kpi-value">${formatBytesCompact(up)}</div>
                    <div class="kpi-sub">${upMb} · ${upPct}%</div>
                </button>
            </div>

            <div class="kpi-tile">
                <div class="item-top">
                    <span class="kpi-top">Total Traffic (${activeWindow})</span>
                    <span class="item-value">
                        ${formatBytesCompact(total)} (${totalMb})
                    </span>
                </div>
                <div class="bar-track" aria-hidden="true">
                    <div
                        class="bar-fill"
                        style=${`width: ${downPct}%`}
                    ></div>
                    <div
                        class="bar-fill secondary"
                        style=${`width: ${upPct}%`}
                    ></div>
                </div>
            </div>
        `;
    }
}

export class UnifiInsightsInternetActivityCardEditor extends GenericEditor {
    constructor() {
        super(INTERNET_ACTIVITY_CARD_TAG, WS_SOURCES);
    }
}

registerDashboardCard({
    tag: INTERNET_ACTIVITY_CARD_TAG,
    editorTag: INTERNET_ACTIVITY_EDITOR_TAG,
    card: UnifiInsightsInternetActivityCard,
    editor: UnifiInsightsInternetActivityCardEditor,
    name: "UniFi Internet Activity",
    description: "Historical WAN download/upload activity and live gateway throughput.",
});

export { INTERNET_ACTIVITY_CARD_TAG, INTERNET_ACTIVITY_EDITOR_TAG };
