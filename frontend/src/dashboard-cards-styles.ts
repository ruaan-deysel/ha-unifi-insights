import { css } from "lit";

import { themeTokens } from "./styles";

export const dashboardCardStyles = [
    themeTokens,
    css`
        :host {
            display: block;
            height: 100%;
        }
        ha-card {
            height: 100%;
            box-sizing: border-box;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow: hidden;
        }
        .icon {
            width: 20px;
            height: 20px;
            fill: currentColor;
            flex: none;
        }
        .header,
        .header-main,
        .header-actions,
        .hero-banner,
        .hero-left,
        .kpi-top,
        .item-card,
        .item-top,
        .item-meta,
        .ring-card {
            display: flex;
            align-items: center;
        }
        .header,
        .hero-banner,
        .kpi-top,
        .item-top {
            justify-content: space-between;
            gap: 10px;
        }
        .header-main,
        .hero-left,
        .item-card,
        .ring-card {
            gap: 10px;
            min-width: 0;
        }
        .header-icon,
        .item-icon,
        .ring-gauge,
        .empty-hero .icon-badge {
            display: grid;
            place-items: center;
            flex: none;
        }
        .header-icon {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: color-mix(
                in srgb,
                var(--card-accent, var(--primary-color)) 15%,
                transparent
            );
            color: var(--card-accent, var(--primary-color));
        }
        .header-titles {
            min-width: 0;
        }
        .header-title,
        .hero-title,
        .item-name,
        .kpi-sub {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .header-title,
        .hero-title,
        .item-name,
        .empty-title,
        .chip,
        .kpi-top,
        .pill-tab,
        button.link {
            font-weight: 600;
        }
        .header-title {
            font-size: 1.02rem;
            line-height: 1.25;
        }
        .header-subtitle,
        .hero-meta,
        .kpi-sub,
        .item-meta,
        .empty-sub {
            font-size: 0.75rem;
            color: var(--secondary-text-color);
        }
        .header-actions,
        .kpi-top,
        .item-meta,
        .empty-hero,
        .chip {
            gap: 6px;
        }
        .state {
            color: var(--secondary-text-color);
            font-size: 0.88rem;
            padding: 12px;
            border-radius: 12px;
            background: color-mix(
                in srgb,
                var(--primary-text-color) 4%,
                transparent
            );
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .error,
        .chip.critical,
        .chip.offline,
        .item-icon.offline {
            color: var(--uit-offline);
            background: color-mix(in srgb, var(--uit-offline) 14%, transparent);
        }
        .pulse-dot,
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            display: inline-block;
            flex: none;
        }
        .chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.74rem;
            text-transform: capitalize;
            background: color-mix(
                in srgb,
                var(--primary-text-color) 8%,
                transparent
            );
            color: var(--primary-text-color);
        }
        .chip.ok,
        .chip.healthy,
        .chip.online,
        .item-icon.online,
        .empty-hero .icon-badge {
            background: color-mix(in srgb, var(--uit-online) 16%, transparent);
            color: var(--uit-online);
        }
        .chip.warning,
        .chip.degraded,
        .chip.partial {
            background: color-mix(in srgb, var(--uit-warning) 18%, transparent);
            color: var(--uit-warning);
        }
        .hero-banner {
            padding: 10px 12px;
            border-radius: 12px;
            background: color-mix(
                in srgb,
                var(--card-accent, var(--primary-color)) 8%,
                transparent
            );
            border: 1px solid
                color-mix(
                    in srgb,
                    var(--card-accent, var(--primary-color)) 20%,
                    transparent
                );
        }
        .hero-left .icon {
            color: var(--card-accent, var(--primary-color));
        }
        .hero-title {
            font-size: 0.9rem;
        }
        .kpi-grid,
        .ring-strip,
        .list {
            display: grid;
            gap: 8px;
        }
        .kpi-grid {
            grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
        }
        .ring-strip {
            grid-template-columns: repeat(2, 1fr);
        }
        .kpi-tile,
        .ring-card,
        .item-card {
            border-radius: 12px;
            background: color-mix(
                in srgb,
                var(--primary-text-color) 4%,
                transparent
            );
            border: 1px solid var(--uit-line);
        }
        .kpi-tile {
            appearance: none;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 0;
            text-align: left;
            font: inherit;
            color: inherit;
        }
        .kpi-tile:disabled {
            cursor: default;
            opacity: 1;
        }
        .kpi-tile.clickable {
            cursor: pointer;
            transition: background 150ms ease;
        }
        .kpi-tile.clickable:hover {
            background: color-mix(
                in srgb,
                var(--primary-color) 10%,
                transparent
            );
        }
        .kpi-top {
            font-size: 0.73rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            color: var(--secondary-text-color);
        }
        .kpi-value {
            font-size: 1.18rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            line-height: 1.2;
            text-transform: capitalize;
        }
        .bar-track {
            width: 100%;
            height: 6px;
            border-radius: 999px;
            background: color-mix(
                in srgb,
                var(--primary-text-color) 10%,
                transparent
            );
            overflow: hidden;
            display: flex;
        }
        .bar-fill {
            height: 100%;
            border-radius: 999px;
            background: var(--primary-color);
            transition: width 250ms ease;
        }
        .bar-fill.ok {
            background: var(--uit-online);
        }
        .bar-fill.warning {
            background: var(--uit-warning);
        }
        .bar-fill.critical {
            background: var(--uit-offline);
        }
        .bar-fill.secondary {
            background: #8b5cf6;
        }
        .ring-card,
        .item-card {
            padding: 8px 10px;
        }
        .ring-gauge {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: conic-gradient(
                var(--ring-color, var(--uit-online)) calc(var(--pct, 0) * 1%),
                color-mix(in srgb, var(--primary-text-color) 10%, transparent) 0
            );
            position: relative;
        }
        .ring-gauge::before {
            content: "";
            position: absolute;
            inset: 5px;
            border-radius: 50%;
            background: var(--card-background-color, #fff);
        }
        .ring-gauge span {
            position: relative;
            font-size: 0.7rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }
        .item-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: color-mix(
                in srgb,
                var(--primary-color) 12%,
                transparent
            );
            color: var(--primary-color);
        }
        .item-body {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .item-name {
            font-size: 0.88rem;
        }
        .item-value {
            font-size: 0.85rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            flex-shrink: 0;
        }
        .pill-tabs {
            display: inline-flex;
            background: color-mix(
                in srgb,
                var(--primary-text-color) 6%,
                transparent
            );
            border-radius: 999px;
            padding: 2px;
            gap: 2px;
        }
        .pill-tab {
            border: 0;
            background: transparent;
            color: var(--secondary-text-color);
            font: inherit;
            font-size: 0.7rem;
            padding: 3px 8px;
            border-radius: 999px;
            cursor: pointer;
            text-transform: uppercase;
        }
        .pill-tab[aria-pressed="true"] {
            background: var(--primary-color);
            color: var(--text-primary-color, #fff);
        }
        .empty-hero {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 18px 12px;
            border-radius: 14px;
            background: color-mix(in srgb, var(--uit-online) 7%, transparent);
            border: 1px dashed
                color-mix(in srgb, var(--uit-online) 30%, transparent);
        }
        .empty-hero .icon-badge {
            width: 42px;
            height: 42px;
            border-radius: 50%;
        }
        .empty-title {
            font-size: 0.92rem;
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
        button.link:hover {
            text-decoration: underline;
        }
    `,
];
