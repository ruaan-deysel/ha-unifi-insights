/**
 * Card UI strings. English ships in the bundle; other languages fall back to
 * it. (The integration's translations/ folder is backend-only.)
 */
const en = {
    "card.name": "UniFi Topology",
    "card.description":
        "Interactive network topology of a UniFi site, from UniFi Insights.",
    "header.summary": "{devices} devices · {clients} clients",
    "state.loading": "Loading network topology…",
    "state.no_sources": "No UniFi Insights integration is loaded.",
    "state.unconfigured": "Choose a site to show.",
    "state.empty": "No devices reported for {site}.",
    "state.incompatible":
        "Card and integration versions don't match. Refresh the browser (clear cache) after updating.",
    "state.stale": "Stale",
    "state.reconnecting": "Reconnecting…",
    "state.online": "Online",
    "state.offline": "Offline",
    "state.unknown": "Unknown",
    "issue.site_unavailable":
        "Site data temporarily unavailable; will recover automatically.",
    "issue.devices_unavailable":
        "Device data unavailable; showing last known layout.",
    "issue.legacy_uplink_missing":
        "Uplink details unavailable; device links may be missing.",
    "issue.parents_unresolved":
        "{count} nodes couldn't be placed under a parent.",
    "issue.clients_truncated":
        "Showing {included} of {total} clients (limit {max}).",
    "issue.entry_unloaded": "Integration is reloading.",
    "issue.unknown": "Topology problem: {code}.",
    "error.entry_not_found":
        "The configured site no longer exists or is disabled.",
    "error.site_not_selected":
        "The configured site no longer exists or is disabled.",
    "error.entry_not_loaded": "Integration isn't loaded (retrying).",
    "error.unknown": "Could not load the topology ({code}).",
    "action.integration": "Integration",
    "action.edit": "Edit card",
    "view.graph": "Graph",
    "view.list": "List",
    "toolbar.view": "View",
    "toolbar.filters": "Show",
    "toolbar.zoom": "Zoom",
    "toolbar.options": "Options",
    "toolbar.site": "Site",
    "zoom.in": "Zoom in",
    "zoom.out": "Zoom out",
    "zoom.fit": "Fit to view",
    "zoom.hint": "Use Ctrl + scroll to zoom",
    "kind.gateway": "Gateway",
    "kind.switch": "Switch",
    "kind.access_point": "Access point",
    "kind.client": "Client",
    "kind.other": "Other",
    "medium.wired": "Wired",
    "medium.wireless": "Wireless",
    "medium.unknown": "Unknown",
    "group.clients": "{count} clients",
    "group.client_one": "1 client",
    "group.unconnected": "Unconnected clients",
    "group.root": "Clients",
    "group.summary": "{wireless} wireless, {offline} offline",
    "graph.label": "{site} topology, {devices} devices, {clients} clients",
    "graph.roledescription": "network topology",
    "node.label": "{kind} {name}, {state}",
    "node.clients": "{count} clients",
    "node.client_one": "1 client",
    "node.uplink": "uplink port {port}",
    "node.uplink_speed": "uplink port {port} at {speed}",
    "list.label": "{site} devices and clients",
    "list.search": "Search",
    "list.no_matches": "No matches",
    "detail.close": "Close",
    "detail.kind": "Type",
    "detail.model": "Model",
    "detail.state": "State",
    "detail.parent": "Connected to",
    "detail.port": "Port",
    "detail.speed": "Speed",
    "detail.medium": "Link",
    "detail.poe": "PoE",
    "detail.clients": "Clients",
    "detail.clients_value": "{total} ({wired} wired, {wireless} wireless)",
    "detail.connection": "Connection",
    "detail.vlan": "VLAN",
    "detail.network": "Network",
    "detail.via_hidden": "Via hidden",
    "detail.open_device": "Open device",
    "detail.search_members": "Search clients",
    "announce.updated": "Topology updated.",
    "announce.offline": "{count} devices offline.",
    "editor.site": "Site",
    "editor.site_unavailable": "{site} (unavailable)",
    "editor.title": "Title",
    "editor.view": "Default view",
    "editor.clients": "Clients",
    "editor.kinds": "Show node types",
    "editor.density": "Density",
    "editor.orientation": "Orientation",
    "editor.show_site_selector": "Show site selector",
    "editor.show_labels": "Show labels",
    "editor.max_clients": "Maximum clients",
    "clients.collapsed": "Grouped",
    "clients.expanded": "Expanded",
    "clients.hidden": "Hidden",
    "density.auto": "Automatic",
    "density.comfortable": "Comfortable",
    "density.compact": "Compact",
    "orientation.vertical": "Top to bottom",
    "orientation.horizontal": "Left to right",
} as const;

export type LocalizeKey = keyof typeof en;
export type LocalizeVars = Record<string, string | number>;
export type LocalizeFunc = (key: LocalizeKey, vars?: LocalizeVars) => string;

const TABLES: Record<string, Partial<Record<LocalizeKey, string>>> = { en };

export function makeLocalize(language: string | undefined): LocalizeFunc {
    const lang = (language ?? "en").toLowerCase();
    const table = TABLES[lang] ?? TABLES[lang.split("-")[0] ?? "en"] ?? {};
    return (key, vars) => {
        let text: string = table[key] ?? en[key];
        if (vars)
            for (const [name, value] of Object.entries(vars))
                text = text.replaceAll(`{${name}}`, String(value));
        return text;
    };
}
