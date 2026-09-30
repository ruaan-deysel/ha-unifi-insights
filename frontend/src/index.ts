// Entry point of the topology card bundle, served by the integration (frontend.py).
import { CARD_TAG, EDITOR_TAG } from "./config";
import {
    INTERNET_ACTIVITY_CARD_TAG,
    INTERNET_ACTIVITY_EDITOR_TAG,
    PERFORMANCE_CARD_TAG,
    PERFORMANCE_EDITOR_TAG,
    PROTECT_CARD_TAG,
    PROTECT_EDITOR_TAG,
    SITE_HEALTH_CARD_TAG,
    SITE_HEALTH_EDITOR_TAG,
    TIMELINE_CARD_TAG,
    TIMELINE_EDITOR_TAG,
    UnifiInsightsInternetActivityCard,
    UnifiInsightsInternetActivityCardEditor,
    UnifiInsightsPerformanceCard,
    UnifiInsightsPerformanceCardEditor,
    UnifiInsightsProtectStatusCard,
    UnifiInsightsProtectStatusCardEditor,
    UnifiInsightsSiteHealthCard,
    UnifiInsightsSiteHealthCardEditor,
    UnifiInsightsTimelineCard,
    UnifiInsightsTimelineCardEditor,
} from "./dashboard-cards";
import { defineOnce } from "./define";
import { makeLocalize } from "./localize";
import { UnifiInsightsTopologyCard } from "./topology-card";
import { UnifiInsightsTopologyCardEditor } from "./topology-card-editor";

defineOnce(CARD_TAG, UnifiInsightsTopologyCard);
defineOnce(EDITOR_TAG, UnifiInsightsTopologyCardEditor);
defineOnce(SITE_HEALTH_CARD_TAG, UnifiInsightsSiteHealthCard);
defineOnce(SITE_HEALTH_EDITOR_TAG, UnifiInsightsSiteHealthCardEditor);
defineOnce(INTERNET_ACTIVITY_CARD_TAG, UnifiInsightsInternetActivityCard);
defineOnce(INTERNET_ACTIVITY_EDITOR_TAG, UnifiInsightsInternetActivityCardEditor);
defineOnce(PERFORMANCE_CARD_TAG, UnifiInsightsPerformanceCard);
defineOnce(PERFORMANCE_EDITOR_TAG, UnifiInsightsPerformanceCardEditor);
defineOnce(PROTECT_CARD_TAG, UnifiInsightsProtectStatusCard);
defineOnce(PROTECT_EDITOR_TAG, UnifiInsightsProtectStatusCardEditor);
defineOnce(TIMELINE_CARD_TAG, UnifiInsightsTimelineCard);
defineOnce(TIMELINE_EDITOR_TAG, UnifiInsightsTimelineCardEditor);

const localize = makeLocalize("en");
window.customCards ??= [];
if (!window.customCards.some((card) => card.type === CARD_TAG)) {
    window.customCards.push({
        type: CARD_TAG,
        name: localize("card.name"),
        description: localize("card.description"),
        preview: true,
        documentationURL:
            "https://github.com/ruaan-deysel/ha-unifi-insights#network-topology-card",
    });
}

const cardEntries: Array<{ type: string; name: string; description: string }> = [
    {
        type: SITE_HEALTH_CARD_TAG,
        name: "UniFi Insights Site Health",
        description: "",
    },
    {
        type: INTERNET_ACTIVITY_CARD_TAG,
        name: "UniFi Insights Internet Activity",
        description: "",
    },
    {
        type: PERFORMANCE_CARD_TAG,
        name: "UniFi Insights Device Performance",
        description: "",
    },
    {
        type: PROTECT_CARD_TAG,
        name: "UniFi Insights Protect Status",
        description: "",
    },
    {
        type: TIMELINE_CARD_TAG,
        name: "UniFi Insights Event Timeline",
        description: "",
    },
];

for (const entry of cardEntries) {
    if (!window.customCards.some((card) => card.type === entry.type)) {
        window.customCards.push({
            type: entry.type,
            name: entry.name,
            description: entry.description,
            preview: true,
        });
    }
}
