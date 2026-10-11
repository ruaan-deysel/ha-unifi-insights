// Entry point of the topology card bundle, served by the integration (frontend.py).
import { CARD_TAG, EDITOR_TAG } from "./config";
import { defineOnce } from "./define";
import "./internet-activity-card";
import { makeLocalize } from "./localize";
import "./performance-card";
import "./protect-status-card";
import "./site-health-card";
import "./timeline-card";
import { UnifiInsightsTopologyCard } from "./topology-card";
import { UnifiInsightsTopologyCardEditor } from "./topology-card-editor";

defineOnce(CARD_TAG, UnifiInsightsTopologyCard);
defineOnce(EDITOR_TAG, UnifiInsightsTopologyCardEditor);

const localize = makeLocalize("en");
window.customCards ??= [];
if (!window.customCards.some((card) => card.type === CARD_TAG)) {
    window.customCards.push({
        type: CARD_TAG,
        name: localize("card.name"),
        description: localize("card.description"),
        preview: true,
        documentationURL:
            "https://github.com/tinkerologie/ha-unifi-insights#network-topology-card",
    });
}
