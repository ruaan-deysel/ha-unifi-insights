import {
    mdiAlertCircleOutline,
    mdiBellRingOutline,
    mdiCctv,
    mdiDoorbellVideo,
} from "@mdi/js";
import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";

import { allSites, resolveBinding, type SiteBinding } from "./config";
import { type TopologySource } from "./contract";
import {
    fireEvent,
    toWsError,
    type HomeAssistant,
    type MessageBase,
    type UnsubscribeFunc,
    type WsError,
} from "./ha-types";
import {
    iconTemplate,
    mdiAccessPoint,
    mdiDevices,
    mdiRouterNetwork,
    mdiSwitch,
} from "./icons";
import { themeTokens } from "./styles";

export const SITE_HEALTH_CARD_TAG = "unifi-insights-site-health-card";
export const SITE_HEALTH_EDITOR_TAG = "unifi-insights-site-health-card-editor";
export const INTERNET_ACTIVITY_CARD_TAG = "unifi-insights-internet-activity-card";
export const INTERNET_ACTIVITY_EDITOR_TAG = "unifi-insights-internet-activity-card-editor";
export const PERFORMANCE_CARD_TAG = "unifi-insights-performance-card";
export const PERFORMANCE_EDITOR_TAG = "unifi-insights-performance-card-editor";
export const PROTECT_CARD_TAG = "unifi-insights-protect-status-card";
export const PROTECT_EDITOR_TAG = "unifi-insights-protect-status-card-editor";
export const TIMELINE_CARD_TAG = "unifi-insights-timeline-card";
export const TIMELINE_EDITOR_TAG = "unifi-insights-timeline-card-editor";

export interface DashboardCardConfig {
    type: string;
    title?: string;
    entry_id?: string;
    site_id?: string;
    show_site_selector?: boolean;
    [key: string]: unknown;
}

export interface ProtectSource {
    entry_id: string;
    title: string;
    camera_count: number;
    sites: { id: string; name: string }[];
}

interface SnapshotIssue {
    code?: string;
}

export function formatBytesCompact(bytes: number): string {
    const mb = Math.round(bytes / 1_000_000);
    if (bytes >= 1_000_000_000) {
        return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
    }
    return `${mb} MB`;
}

export function formatBps(bps: unknown): string | undefined {
    if (typeof bps !== "number" || !Number.isFinite(bps) || bps < 0) return undefined;
    if (bps >= 1_000_000_000) return `${(bps / 1_000_000_000).toFixed(1)} Gbps`;
    if (bps >= 1_000_000) return `${(bps / 1_000_000).toFixed(1)} Mbps`;
    if (bps >= 1_000) return `${Math.round(bps / 1_000)} Kbps`;
    return `${Math.round(bps)} bps`;
}

export function formatUptime(seconds: unknown): string | undefined {
    if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) {
        return undefined;
    }
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    if (days > 0) return `${days}d ${hours}h`;
    const mins = Math.max(1, Math.floor((seconds % 3600) / 60));
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

export function formatRelativeTimestamp(iso: unknown): string {
    if (typeof iso !== "string" || !iso) return "";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const diffMinutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
    if (diffMinutes < 1) return "Just now";
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const hours = Math.floor(diffMinutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function kindIcon(kind: unknown): string {
    switch (String(kind ?? "")) {
        case "gateway":
            return mdiRouterNetwork;
        case "switch":
            return mdiSwitch;
        case "access_point":
            return mdiAccessPoint;
        case "camera":
            return mdiCctv;
        case "doorbell":
            return mdiDoorbellVideo;
        case "chime":
        case "ring":
            return mdiBellRingOutline;
        default:
            return mdiDevices;
    }
}

export function metricTone(pct: number): string {
    if (pct >= 85) return "critical";
    if (pct >= 60) return "warning";
    return "ok";
}

export abstract class BaseDashboardCard extends LitElement {
    static editorTag = "";

    static async getConfigElement(this: { editorTag: string }): Promise<HTMLElement> {
        return document.createElement(this.editorTag);
    }

    static override properties = {
        hass: { attribute: false },
        config: { state: true },
        snapshot: { state: true },
        sources: { state: true },
        loading: { state: true },
        error: { state: true },
    };

    declare hass?: HomeAssistant;
    declare config: DashboardCardConfig;
    declare snapshot: Record<string, unknown> | undefined;
    declare sources: TopologySource[] | ProtectSource[];
    declare loading: boolean;
    declare error: WsError | undefined;

    private unsubscribe: UnsubscribeFunc | undefined;
    private bindingKey: string | undefined;
    private syncGeneration = 0;
    private failedBindingKey: string | undefined;
    private retryAfterMs = 0;
    private retryTimer: ReturnType<typeof setTimeout> | undefined;

    constructor() {
        super();
        this.config = { type: "" };
        this.snapshot = undefined;
        this.sources = [];
        this.loading = false;
        this.error = undefined;
    }

    protected abstract get cardType(): string;
    protected abstract get sourceCommand(): string;
    protected abstract get subscribeCommand(): string;
    protected abstract get defaultTitle(): string;
    protected abstract get headerIcon(): string;
    protected abstract renderContent(): unknown;

    protected get headerAccent(): string {
        return "var(--primary-color, #03a9f4)";
    }

    protected renderHeaderBadge(): TemplateResult | typeof nothing {
        return nothing;
    }

    protected get loadingLabel(): string {
        return "Loading";
    }

    protected get includeSiteInSubscribeMessage(): boolean {
        return true;
    }

    override connectedCallback(): void {
        super.connectedCallback();
        void this.sync();
    }

    override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.syncGeneration += 1;
        if (this.retryTimer) {
            clearTimeout(this.retryTimer);
            this.retryTimer = undefined;
        }
        void this.unsubscribe?.();
        this.unsubscribe = undefined;
    }

    protected override willUpdate(changed: PropertyValues<this>): void {
        const hassChanged = changed.has("hass");
        const configChanged = changed.has("config");
        const previousHass = changed.get("hass") as HomeAssistant | undefined;
        const connectionChanged =
            hassChanged && previousHass?.connection !== this.hass?.connection;
        if (configChanged || connectionChanged) {
            void this.sync();
        }
    }

    setConfig(config: DashboardCardConfig): void {
        if (!config || typeof config.type !== "string") {
            throw new Error("Invalid card config");
        }
        this.config = { ...config };
    }

    getCardSize(): number {
        return 4;
    }

    getGridOptions() {
        return { columns: 6, rows: 4, min_columns: 3, min_rows: 3 };
    }

    protected getBinding(): SiteBinding | undefined {
        if (this.config.entry_id && this.config.site_id) {
            return { entry_id: this.config.entry_id, site_id: this.config.site_id };
        }
        return resolveBinding(
            {
                entry_id: this.config.entry_id,
                site_id: this.config.site_id,
                title: this.config.title,
                view: "graph",
                show_site_selector: false,
                clients: "collapsed",
                kinds: ["gateway", "switch", "access_point", "client", "other"],
                density: undefined,
                orientation: "vertical",
                show_labels: true,
                max_clients: 500,
            },
            this.sources as TopologySource[],
        );
    }

    private async sync(): Promise<void> {
        const generation = ++this.syncGeneration;
        if (!this.hass) return;
        this.loading = true;
        try {
            this.sources = (await this.hass.callWS({ type: this.sourceCommand })) as
                | TopologySource[]
                | ProtectSource[];
            if (generation !== this.syncGeneration || !this.isConnected) {
                this.loading = false;
                return;
            }
            this.error = undefined;
        } catch (err) {
            if (generation !== this.syncGeneration || !this.isConnected) {
                this.loading = false;
                return;
            }
            this.error = toWsError(err);
            this.loading = false;
            return;
        }

        const binding = this.getBinding();
        const key = binding ? `${binding.entry_id}:${binding.site_id}` : undefined;
        if (key === this.bindingKey && this.unsubscribe) {
            this.loading = false;
            return;
        }
        this.bindingKey = key;
        if (key !== this.failedBindingKey) {
            this.failedBindingKey = undefined;
            this.retryAfterMs = 0;
        }
        this.snapshot = undefined;
        await this.unsubscribe?.();
        this.unsubscribe = undefined;
        if (!binding) {
            this.loading = false;
            return;
        }

        if (key !== undefined && key === this.failedBindingKey && Date.now() < this.retryAfterMs) {
            this.loading = false;
            if (this.retryTimer) clearTimeout(this.retryTimer);
            this.retryTimer = setTimeout(() => {
                if (generation === this.syncGeneration && this.isConnected) void this.sync();
            }, Math.max(0, this.retryAfterMs - Date.now()));
            return;
        }

        const message: MessageBase = { type: this.subscribeCommand, entry_id: binding.entry_id };
        if (this.includeSiteInSubscribeMessage) message.site_id = binding.site_id;

        try {
            const unsubscribe = await this.hass.connection.subscribeMessage(
                (msg: unknown) => {
                    if (generation !== this.syncGeneration || !this.isConnected) return;
                    const issues = Array.isArray((msg as Record<string, unknown>).issues)
                        ? ((msg as Record<string, unknown>).issues as SnapshotIssue[])
                        : [];
                    if (issues.some((issue) => issue?.code === "entry_unloaded")) {
                        this.unsubscribe?.().catch(() => undefined);
                        this.unsubscribe = undefined;
                        this.bindingKey = undefined;
                        if (this.retryTimer) clearTimeout(this.retryTimer);
                        this.retryTimer = setTimeout(() => {
                            if (generation === this.syncGeneration && this.isConnected) {
                                void this.sync();
                            }
                        }, 1000);
                        return;
                    }
                    this.failedBindingKey = undefined;
                    this.retryAfterMs = 0;
                    this.error = undefined;
                    this.snapshot = msg as Record<string, unknown>;
                    this.loading = false;
                },
                message,
                { resubscribe: false },
            );
            if (generation !== this.syncGeneration || !this.isConnected) {
                await unsubscribe();
                this.loading = false;
                return;
            }
            this.unsubscribe = unsubscribe;
        } catch (err) {
            if (generation !== this.syncGeneration || !this.isConnected) {
                this.loading = false;
                return;
            }
            this.failedBindingKey = key;
            this.retryAfterMs = Date.now() + 5000;
            this.error = toWsError(err);
            this.loading = false;
            this.retryTimer = setTimeout(() => {
                if (generation === this.syncGeneration && this.isConnected) void this.sync();
            }, 5000);
        }
    }

    protected openMoreInfo(entityId: string): void {
        fireEvent(this, "hass-more-info", { entityId });
    }

    override render() {
        const subtitle =
            typeof this.snapshot?.site_name === "string" && this.snapshot.site_name.trim()
                ? this.snapshot.site_name
                : typeof this.snapshot?.entry_title === "string" && this.snapshot.entry_title.trim()
                  ? this.snapshot.entry_title
                  : undefined;
        return html`
            <ha-card style=${`--card-accent: ${this.headerAccent}`}>
                <div class="header">
                    <div class="header-main">
                        <div class="header-icon">${iconTemplate(this.headerIcon)}</div>
                        <div class="header-titles">
                            <div class="header-title">${this.config.title ?? this.defaultTitle}</div>
                            ${subtitle ? html`<div class="header-subtitle">${subtitle}</div>` : nothing}
                        </div>
                    </div>
                    <div class="header-actions">${this.renderHeaderBadge()}</div>
                </div>
                ${this.loading
                    ? html`<div class="state loading-box"><span class="pulse-dot"></span><span>${this.loadingLabel}</span></div>`
                    : nothing}
                ${this.error
                    ? html`<div class="state error">${iconTemplate(mdiAlertCircleOutline)}<span>${this.error.code}</span></div>`
                    : nothing}
                ${!this.loading && !this.error ? this.renderContent() : nothing}
            </ha-card>
        `;
    }

    static override styles = [
        themeTokens,
        css`
            :host { display: block; height: 100%; }
            ha-card { height: 100%; box-sizing: border-box; padding: 16px; display: flex; flex-direction: column; gap: 12px; overflow: hidden; }
            .icon { width: 20px; height: 20px; fill: currentColor; flex: none; }
            .header, .header-main, .header-actions, .hero-banner, .hero-left, .kpi-top, .item-card, .item-top, .item-meta, .ring-card { display: flex; align-items: center; }
            .header, .hero-banner, .kpi-top, .item-top { justify-content: space-between; gap: 10px; }
            .header-main, .hero-left, .item-card, .ring-card { gap: 10px; min-width: 0; }
            .header-icon { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; background: color-mix(in srgb, var(--card-accent, var(--primary-color)) 15%, transparent); color: var(--card-accent, var(--primary-color)); flex: none; }
            .header-titles { min-width: 0; }
            .header-title, .hero-title, .item-name { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .header-title { font-size: 1.02rem; line-height: 1.25; }
            .header-subtitle, .hero-meta, .kpi-sub, .item-meta, .empty-sub { font-size: 0.75rem; color: var(--secondary-text-color); }
            .header-actions { gap: 6px; flex-shrink: 0; }
            .state { color: var(--secondary-text-color); font-size: 0.88rem; padding: 12px; border-radius: 12px; background: color-mix(in srgb, var(--primary-text-color) 4%, transparent); display: flex; align-items: center; gap: 8px; }
            .error { color: var(--uit-offline); background: color-mix(in srgb, var(--uit-offline) 12%, transparent); }
            .pulse-dot, .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; display: inline-block; flex: none; }
            .chip { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 4px 10px; font-size: 0.74rem; font-weight: 600; text-transform: capitalize; background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); color: var(--primary-text-color); }
            .chip.ok, .chip.healthy, .chip.online { background: color-mix(in srgb, var(--uit-online) 16%, transparent); color: var(--uit-online); }
            .chip.warning, .chip.degraded, .chip.partial { background: color-mix(in srgb, var(--uit-warning) 18%, transparent); color: var(--uit-warning); }
            .chip.critical, .chip.offline { background: color-mix(in srgb, var(--uit-offline) 16%, transparent); color: var(--uit-offline); }
            .hero-banner { padding: 10px 12px; border-radius: 12px; background: color-mix(in srgb, var(--card-accent, var(--primary-color)) 8%, transparent); border: 1px solid color-mix(in srgb, var(--card-accent, var(--primary-color)) 20%, transparent); }
            .hero-left .icon { color: var(--card-accent, var(--primary-color)); }
            .hero-title { font-size: 0.9rem; }
            .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(92px, 1fr)); gap: 8px; }
            .kpi-tile { appearance: none; padding: 10px 12px; border-radius: 12px; background: color-mix(in srgb, var(--primary-text-color) 4%, transparent); border: 1px solid var(--uit-line); display: flex; flex-direction: column; gap: 4px; min-width: 0; text-align: left; font: inherit; color: inherit; }
            .kpi-tile:disabled { cursor: default; opacity: 1; }
            .kpi-tile.clickable { cursor: pointer; transition: background 150ms ease; }
            .kpi-tile.clickable:hover { background: color-mix(in srgb, var(--primary-color) 10%, transparent); }
            .kpi-top { gap: 6px; font-size: 0.73rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; color: var(--secondary-text-color); }
            .kpi-value { font-size: 1.18rem; font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1.2; text-transform: capitalize; }
            .kpi-sub { font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .bar-track { width: 100%; height: 6px; border-radius: 999px; background: color-mix(in srgb, var(--primary-text-color) 10%, transparent); overflow: hidden; display: flex; }
            .bar-fill { height: 100%; border-radius: 999px; background: var(--primary-color); transition: width 250ms ease; }
            .bar-fill.ok { background: var(--uit-online); }
            .bar-fill.warning { background: var(--uit-warning); }
            .bar-fill.critical { background: var(--uit-offline); }
            .bar-fill.secondary { background: #8b5cf6; }
            .ring-strip { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
            .ring-card, .item-card { padding: 8px 10px; border-radius: 12px; background: color-mix(in srgb, var(--primary-text-color) 3.5%, transparent); border: 1px solid var(--uit-line); }
            .ring-gauge { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; flex: none; background: conic-gradient(var(--ring-color, var(--uit-online)) calc(var(--pct, 0) * 1%), color-mix(in srgb, var(--primary-text-color) 10%, transparent) 0); position: relative; }
            .ring-gauge::before { content: ""; position: absolute; inset: 5px; border-radius: 50%; background: var(--card-background-color, #fff); }
            .ring-gauge span { position: relative; font-size: 0.7rem; font-weight: 700; font-variant-numeric: tabular-nums; }
            .list { display: grid; gap: 8px; }
            .item-icon { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; background: color-mix(in srgb, var(--primary-color) 12%, transparent); color: var(--primary-color); flex: none; }
            .item-icon.offline { background: color-mix(in srgb, var(--uit-offline) 12%, transparent); color: var(--uit-offline); }
            .item-icon.online { background: color-mix(in srgb, var(--uit-online) 12%, transparent); color: var(--uit-online); }
            .item-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
            .item-name { font-size: 0.88rem; }
            .item-meta { gap: 6px; }
            .item-value { font-size: 0.85rem; font-weight: 700; font-variant-numeric: tabular-nums; flex-shrink: 0; }
            .pill-tabs { display: inline-flex; background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); border-radius: 999px; padding: 2px; gap: 2px; }
            .pill-tab { border: 0; background: transparent; color: var(--secondary-text-color); font: inherit; font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 999px; cursor: pointer; text-transform: uppercase; }
            .pill-tab[aria-pressed="true"] { background: var(--primary-color); color: var(--text-primary-color, #fff); }
            .empty-hero { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 18px 12px; border-radius: 14px; background: color-mix(in srgb, var(--uit-online) 7%, transparent); border: 1px dashed color-mix(in srgb, var(--uit-online) 30%, transparent); gap: 6px; }
            .empty-hero .icon-badge { width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center; background: color-mix(in srgb, var(--uit-online) 16%, transparent); color: var(--uit-online); }
            .empty-title { font-size: 0.92rem; font-weight: 600; }
            button.link { border: 0; background: transparent; color: var(--primary-color); cursor: pointer; padding: 0; text-align: left; font: inherit; font-weight: 600; }
            button.link:hover { text-decoration: underline; }
        `,
    ];
}

export class GenericEditor extends LitElement {
    static override properties = {
        hass: { attribute: false },
        config: { state: true },
    };

    declare hass?: HomeAssistant;
    declare config: DashboardCardConfig;

    protected cardType: string;
    protected sourceCommand: string;
    protected options: Array<{ entryId: string; siteId: string; label: string }>;
    private optionsRequested = false;

    constructor(cardType: string, sourceCommand: string) {
        super();
        this.cardType = cardType;
        this.sourceCommand = sourceCommand;
        this.config = { type: `custom:${cardType}` };
        this.options = [];
    }

    setConfig(config: DashboardCardConfig): void {
        this.config = { ...config };
    }

    protected override willUpdate(): void {
        if (this.hass && !this.optionsRequested) {
            this.optionsRequested = true;
            void this.loadOptions();
        }
    }

    private async loadOptions(): Promise<void> {
        if (!this.hass) return;
        try {
            const payload = await this.hass.callWS({ type: this.sourceCommand });
            this.options =
                this.sourceCommand === "unifi_insights/protect/sources"
                    ? (payload as ProtectSource[]).map((s) => ({
                          entryId: s.entry_id,
                          siteId: "*",
                          label: s.title,
                      }))
                    : allSites(payload as TopologySource[]).map((site) => ({
                          entryId: site.binding.entry_id,
                          siteId: site.binding.site_id,
                          label: site.label,
                      }));
            this.requestUpdate();
        } catch {
            this.options = [];
            this.requestUpdate();
        }
    }

    private applySite(value: string): void {
        const next = { ...this.config, type: this.config.type || `custom:${this.cardType}` };
        if (!value) {
            delete next.entry_id;
            delete next.site_id;
        } else {
            const option = this.options[Number.parseInt(value, 10)];
            if (option) {
                next.entry_id = option.entryId;
                next.site_id = option.siteId;
            }
        }
        this.config = next;
        fireEvent(this, "config-changed", { config: next });
    }

    private applyTitle(value: string): void {
        const next = { ...this.config };
        if (value.trim()) next.title = value.trim();
        else delete next.title;
        this.config = next;
        fireEvent(this, "config-changed", { config: next });
    }

    override render() {
        const selected =
            this.config.entry_id && this.config.site_id
                ? String(
                      this.options.findIndex(
                          (o) =>
                              o.entryId === this.config.entry_id &&
                              o.siteId === this.config.site_id,
                      ),
                  )
                : "";
        return html`
            <div class="editor">
                <label>Site</label>
                <select @change=${(ev: Event) => this.applySite((ev.target as HTMLSelectElement).value)}>
                    <option value="">Auto</option>
                    ${this.options.map((option, index) => {
                        const value = String(index);
                        return html`<option value=${value} ?selected=${value === selected}>${option.label}</option>`;
                    })}
                </select>
                <label>Title</label>
                <input
                    .value=${this.config.title ?? ""}
                    @input=${(ev: Event) => this.applyTitle((ev.target as HTMLInputElement).value)}
                />
            </div>
        `;
    }

    static override styles = css`
        .editor { display: grid; gap: 8px; }
        label { font-size: 0.85rem; color: var(--secondary-text-color); }
        select, input { min-height: 36px; border: 1px solid var(--divider-color); border-radius: 8px; padding: 4px 8px; background: var(--card-background-color); color: var(--primary-text-color); }
    `;
}
