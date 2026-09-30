import { LitElement, css, html, nothing, type PropertyValues } from "lit";

import { allSites, resolveBinding, type SiteBinding } from "./config";
import { WS_SOURCES, type TopologySource } from "./contract";
import {
    fireEvent,
    navigate,
    toWsError,
    type HomeAssistant,
    type MessageBase,
    type UnsubscribeFunc,
    type WsError,
} from "./ha-types";
import { makeLocalize } from "./localize";
import { ensureHaForm } from "./topology-card-editor";

export const SITE_HEALTH_CARD_TAG = "unifi-insights-site-health-card";
export const SITE_HEALTH_EDITOR_TAG = "unifi-insights-site-health-card-editor";
export const INTERNET_ACTIVITY_CARD_TAG =
    "unifi-insights-internet-activity-card";
export const INTERNET_ACTIVITY_EDITOR_TAG =
    "unifi-insights-internet-activity-card-editor";
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

interface ProtectSource {
    entry_id: string;
    title: string;
    camera_count: number;
    sites: { id: string; name: string }[];
}

interface SnapshotIssue {
    code?: string;
}

abstract class BaseDashboardCard extends LitElement {
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
    protected abstract renderContent(): unknown;

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
            hassChanged &&
            previousHass?.connection !== this.hass?.connection;
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

    getGridOptions(): {
        columns: number;
        rows: number;
        min_columns: number;
        min_rows: number;
    } {
        return { columns: 6, rows: 4, min_columns: 3, min_rows: 3 };
    }

    protected getBinding(): SiteBinding | undefined {
        if (this.config.entry_id && this.config.site_id) {
            return {
                entry_id: this.config.entry_id,
                site_id: this.config.site_id,
            };
        }
        if (this.sourceCommand !== WS_SOURCES) {
            if (this.config.entry_id && this.config.site_id) {
                return {
                    entry_id: this.config.entry_id,
                    site_id: this.config.site_id,
                };
            }
            const options = (this.sources as ProtectSource[]).flatMap((source) =>
                source.sites.map((site) => ({
                    entry_id: source.entry_id,
                    site_id: site.id,
                })),
            );
            if (options.length === 1) {
                return options[0];
            }
            return undefined;
        }
        return resolveBinding(
            {
                entry_id: this.config.entry_id,
                site_id: this.config.site_id,
                title: this.config.title,
                view: "graph",
                show_site_selector: false,
                clients: "collapsed",
                kinds: [
                    "gateway",
                    "switch",
                    "access_point",
                    "client",
                    "other",
                ],
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
        if (!this.hass) {
            return;
        }
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

        if (
            key !== undefined &&
            key === this.failedBindingKey &&
            Date.now() < this.retryAfterMs
        ) {
            this.loading = false;
            return;
        }

        const message: MessageBase = {
            type: this.subscribeCommand,
            entry_id: binding.entry_id,
        };
        if (this.includeSiteInSubscribeMessage) {
            message.site_id = binding.site_id;
        }

        try {
            const unsubscribe = await this.hass.connection.subscribeMessage(
                (message: unknown) => {
                    if (generation !== this.syncGeneration || !this.isConnected) {
                        return;
                    }
                    const issues = Array.isArray(
                        (message as Record<string, unknown>).issues,
                    )
                        ? ((message as Record<string, unknown>)
                              .issues as SnapshotIssue[])
                        : [];
                    if (issues.some((issue) => issue?.code === "entry_unloaded")) {
                        this.unsubscribe?.().catch(() => undefined);
                        this.unsubscribe = undefined;
                        this.bindingKey = undefined;
                        if (this.retryTimer) {
                            clearTimeout(this.retryTimer);
                        }
                        this.retryTimer = setTimeout(() => {
                            if (
                                generation === this.syncGeneration &&
                                this.isConnected
                            ) {
                                void this.sync();
                            }
                        }, 1000);
                        return;
                    }
                    this.failedBindingKey = undefined;
                    this.retryAfterMs = 0;
                    this.error = undefined;
                    this.snapshot = message as Record<string, unknown>;
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
                if (generation === this.syncGeneration && this.isConnected) {
                    void this.sync();
                }
            }, 5000);
        }
    }

    protected localize(key: string): string {
        const lang = this.hass?.locale?.language ?? this.hass?.language ?? "en";
        const localize = makeLocalize(lang);
        return localize(key as never);
    }

    protected openMoreInfo(entityId: string): void {
        fireEvent(this, "hass-more-info", { entityId });
    }

    protected openDevice(deviceId: string): void {
        navigate(`/config/devices/device/${deviceId}`);
    }

    override render() {
        return html`
            <ha-card>
                <div class="header">${this.config.title ?? this.localize("card.name")}</div>
                ${this.loading ? html`<div class="state">${this.localize("state.loading")}</div>` : nothing}
                ${this.error
                    ? html`<div class="state error">${this.error.code}</div>`
                    : nothing}
                ${!this.loading && !this.error ? this.renderContent() : nothing}
            </ha-card>
        `;
    }

    static override styles = css`
        ha-card {
            padding: 12px;
        }

        .header {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .state {
            color: var(--secondary-text-color);
            font-size: 0.9rem;
        }

        .error {
            color: var(--error-color);
        }

        .row {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            margin-top: 6px;
            font-size: 0.9rem;
        }

        .chip {
            border-radius: 999px;
            padding: 2px 8px;
            background: var(--state-icon-color);
            color: var(--card-background-color);
            font-size: 0.75rem;
        }

        .list {
            display: grid;
            gap: 6px;
            margin-top: 8px;
        }

        button.link {
            border: 0;
            background: transparent;
            color: var(--primary-color);
            cursor: pointer;
            padding: 0;
            text-align: left;
            font: inherit;
        }
    `;
}

class SiteHealthCard extends BaseDashboardCard {
    protected get cardType(): string {
        return `custom:${SITE_HEALTH_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return WS_SOURCES;
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/site_health/subscribe";
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">${this.localize("state.unconfigured")}</div>`;
        }
        const health = (snapshot.health ?? {}) as Record<string, unknown>;
        const gateway = (snapshot.gateway ?? {}) as Record<string, unknown>;
        const clients = (snapshot.clients ?? {}) as Record<string, unknown>;
        return html`
            <div class="row"><span>Health</span><span class="chip">${String(health.level ?? "unknown")}</span></div>
            <div class="row"><span>Internet</span><span>${String(gateway.internet ?? "unknown")}</span></div>
            <div class="row"><span>Clients</span><span>${String(clients.total ?? 0)}</span></div>
        `;
    }
}

class InternetActivityCard extends BaseDashboardCard {
    protected get cardType(): string {
        return `custom:${INTERNET_ACTIVITY_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return WS_SOURCES;
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/internet_activity/subscribe";
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">No data</div>`;
        }
        const windows = (snapshot.windows ?? {}) as Record<string, unknown>;
        const selected = (windows["1d"] ?? windows["1h"] ?? {}) as Record<
            string,
            unknown
        >;
        const down = Number(selected.download_bytes ?? 0);
        const up = Number(selected.upload_bytes ?? 0);
        const total = down + up;
        return html`
            <div class="row"><span>Download</span><span>${Math.round(down / 1_000_000)} MB</span></div>
            <div class="row"><span>Upload</span><span>${Math.round(up / 1_000_000)} MB</span></div>
            <div class="row"><span>Total</span><span>${Math.round(total / 1_000_000)} MB</span></div>
        `;
    }
}

class PerformanceCard extends BaseDashboardCard {
    protected get cardType(): string {
        return `custom:${PERFORMANCE_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return WS_SOURCES;
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/performance/subscribe";
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">No devices</div>`;
        }
        const devices = Array.isArray(snapshot.devices)
            ? (snapshot.devices as Record<string, unknown>[])
            : [];
        return html`
            <div class="row"><span>Devices</span><span>${devices.length}</span></div>
            <div class="list">
                ${devices.slice(0, 5).map((device) => {
                    const name = String(device.name ?? "Device");
                    const cpu = device.cpu_pct;
                    return html`<div class="row"><span>${name}</span><span>${cpu == null ? "--" : `${Math.round(Number(cpu))}%`}</span></div>`;
                })}
            </div>
        `;
    }
}

class ProtectStatusCard extends BaseDashboardCard {
    protected get cardType(): string {
        return `custom:${PROTECT_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return "unifi_insights/protect/sources";
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/protect/subscribe";
    }

    protected override get includeSiteInSubscribeMessage(): boolean {
        return false;
    }

    protected override getBinding(): SiteBinding | undefined {
        const entryId = this.config.entry_id;
        if (entryId) {
            return { entry_id: entryId, site_id: this.config.site_id ?? "*" };
        }
        const first = this.sources[0] as ProtectSource | undefined;
        if (!first) {
            return undefined;
        }
        return { entry_id: first.entry_id, site_id: this.config.site_id ?? "*" };
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">No Protect data</div>`;
        }
        const devices = Array.isArray(snapshot.devices)
            ? (snapshot.devices as Record<string, unknown>[])
            : [];
        const offline = devices.filter((device) => device.connected === false).length;
        return html`
            <div class="row"><span>Devices</span><span>${devices.length}</span></div>
            <div class="row"><span>Offline</span><span>${offline}</span></div>
            <div class="list">
                ${devices.slice(0, 6).map((device) => {
                    const entityId = typeof device.camera_entity_id === "string" ? device.camera_entity_id : undefined;
                    const label = `${String(device.name ?? "Protect device")} · ${String(device.kind ?? "device")}`;
                    return html`
                        <div class="row">
                            ${entityId
                                ? html`<button class="link" @click=${() => this.openMoreInfo(entityId)}>${label}</button>`
                                : html`<span>${label}</span>`}
                            <span>${device.connected === false ? "offline" : "online"}</span>
                        </div>
                    `;
                })}
            </div>
        `;
    }
}

class TimelineCard extends BaseDashboardCard {
    protected get cardType(): string {
        return `custom:${TIMELINE_CARD_TAG}`;
    }

    protected get sourceCommand(): string {
        return WS_SOURCES;
    }

    protected get subscribeCommand(): string {
        return "unifi_insights/timeline/subscribe";
    }

    protected renderContent() {
        const snapshot = this.snapshot;
        if (!snapshot) {
            return html`<div class="state">No events</div>`;
        }
        const items = Array.isArray(snapshot.items)
            ? (snapshot.items as Record<string, unknown>[])
            : [];
        return html`
            <div class="row"><span>Events</span><span>${items.length}</span></div>
            <div class="list">
                ${items.slice(0, 6).map((item) => {
                    const source = (item.source ?? {}) as Record<string, unknown>;
                    return html`<div class="row"><span>${String(source.name ?? "Source")}</span><span>${String(item.kind ?? "event")}</span></div>`;
                })}
            </div>
        `;
    }
}

class GenericEditor extends LitElement {
    static override properties = {
        hass: { attribute: false },
        config: { state: true },
    };

    declare hass?: HomeAssistant;
    declare config: DashboardCardConfig;

    protected cardType: string;
    protected sourceCommand: string;
    protected options: Array<{ entryId: string; siteId: string; label: string }>;

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

    override connectedCallback(): void {
        super.connectedCallback();
        void ensureHaForm();
        void this.loadOptions();
    }

    private async loadOptions(): Promise<void> {
        if (!this.hass) {
            return;
        }
        try {
            const payload = await this.hass.callWS({ type: this.sourceCommand });
            const options =
                this.sourceCommand === "unifi_insights/protect/sources"
                    ? (payload as ProtectSource[]).map((source) => ({
                          entryId: source.entry_id,
                          siteId: "*",
                          label: source.title,
                      }))
                    : allSites(payload as TopologySource[]).map((site) => ({
                          entryId: site.binding.entry_id,
                          siteId: site.binding.site_id,
                          label: site.label,
                      }));
            this.options = options;
            this.requestUpdate();
        } catch {
            this.options = [];
            this.requestUpdate();
        }
    }

    private applySite(value: string): void {
        const next = {
            ...this.config,
            type: this.config.type || `custom:${this.cardType}`,
        };
        if (!value) {
            delete next.entry_id;
            delete next.site_id;
        } else {
            const index = Number.parseInt(value, 10);
            const option = this.options[index];
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
        if (value.trim()) {
            next.title = value.trim();
        } else {
            delete next.title;
        }
        this.config = next;
        fireEvent(this, "config-changed", { config: next });
    }

    override render() {
        const selected =
            this.config.entry_id && this.config.site_id
                ? String(
                      this.options.findIndex(
                          (option) =>
                              option.entryId === this.config.entry_id &&
                              option.siteId === this.config.site_id,
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
        .editor {
            display: grid;
            gap: 8px;
        }

        label {
            font-size: 0.85rem;
            color: var(--secondary-text-color);
        }

        select,
        input {
            min-height: 36px;
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 4px 8px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
        }
    `;
}

class SiteHealthEditor extends GenericEditor {
    constructor() {
        super(SITE_HEALTH_CARD_TAG, WS_SOURCES);
    }
}

class InternetActivityEditor extends GenericEditor {
    constructor() {
        super(INTERNET_ACTIVITY_CARD_TAG, WS_SOURCES);
    }
}

class PerformanceEditor extends GenericEditor {
    constructor() {
        super(PERFORMANCE_CARD_TAG, WS_SOURCES);
    }
}

class ProtectStatusEditor extends GenericEditor {
    constructor() {
        super(PROTECT_CARD_TAG, "unifi_insights/protect/sources");
    }
}

class TimelineEditor extends GenericEditor {
    constructor() {
        super(TIMELINE_CARD_TAG, WS_SOURCES);
    }
}

export {
    InternetActivityCard as UnifiInsightsInternetActivityCard,
    InternetActivityEditor as UnifiInsightsInternetActivityCardEditor,
    PerformanceCard as UnifiInsightsPerformanceCard,
    PerformanceEditor as UnifiInsightsPerformanceCardEditor,
    ProtectStatusCard as UnifiInsightsProtectStatusCard,
    ProtectStatusEditor as UnifiInsightsProtectStatusCardEditor,
    SiteHealthCard as UnifiInsightsSiteHealthCard,
    SiteHealthEditor as UnifiInsightsSiteHealthCardEditor,
    TimelineCard as UnifiInsightsTimelineCard,
    TimelineEditor as UnifiInsightsTimelineCardEditor,
};
