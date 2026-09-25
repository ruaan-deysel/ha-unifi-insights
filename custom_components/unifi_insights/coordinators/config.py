"""Config coordinator for UniFi Insights - handles slow-changing configuration data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from custom_components.unifi_insights.api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiNotFoundError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.const import CONF_SITE_IDS, SCAN_INTERVAL_CONFIG
from custom_components.unifi_insights.topology_contract import normalize_mac

from .base import UnifiBaseCoordinator

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from custom_components.unifi_insights.api.network import UniFiNetworkClient
    from custom_components.unifi_insights.api.protect import UniFiProtectClient

_LOGGER = logging.getLogger(__name__)


class UnifiConfigCoordinator(UnifiBaseCoordinator):
    """
    Coordinator for slow-changing configuration data (5 minute updates).

    Handles:
    - Sites configuration
    - WiFi networks configuration
    - Firewall policy configuration
    - Policy-based routes (traffic routes) configuration
    - Network info
    """

    def __init__(
        self,
        hass: HomeAssistant,
        network_client: UniFiNetworkClient,
        protect_client: UniFiProtectClient | None,
        entry: ConfigEntry,
        *,
        network_available: bool = True,
        innerspace_available: bool = False,
    ) -> None:
        """Initialize the config coordinator."""
        super().__init__(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=entry,
            name="config",
            update_interval=SCAN_INTERVAL_CONFIG,
        )
        self._network_available = network_available
        self._innerspace_available = innerspace_available
        self.data: dict[str, Any] = {
            "sites": {},
            "wifi": {},
            "firewall_rules": {},
            "policy_based_routes": {},
            "vpn_clients": {},
            "site_vpns": {},
            "network_info": {},
            "client_links": {},
        }
        # Every site the console reports (id -> display name), before the
        # site filter is applied, so the options flow can offer all of them.
        self.available_sites: dict[str, str] = {}
        self._warned_no_selected_sites = False
        # (section, site_id) pairs for optional sections (WiFi, firewall)
        # whose last fetch failed. They keep their previous data but report
        # unavailable, without failing the whole refresh.
        self._failed_sections: set[tuple[str, str]] = set()

    def wifi_available(self, site_id: str) -> bool:
        """Return True if the last refresh fetched WiFi networks for a site."""
        return self.last_update_success and ("wifi", site_id) not in (
            self._failed_sections
        )

    def firewall_available(self, site_id: str) -> bool:
        """Return True if the last refresh fetched firewall rules for a site."""
        return self.last_update_success and ("firewall_rules", site_id) not in (
            self._failed_sections
        )

    async def _fetch_optional_section(
        self,
        section: str,
        site_id: str,
        fetch: Callable[[], Awaitable[list[Any]]],
    ) -> list[Any] | None:
        """
        Fetch an optional per-site section (WiFi networks, firewall rules).

        Returns the models, an empty list when the console or API key does
        not offer the feature, or None when the fetch failed. A failure used
        to be reported as an empty section with a successful refresh, which
        blanked those entities; the caller now keeps the previous data and
        marks the section unavailable instead. It deliberately does not fail
        the whole refresh: at setup that would block every other platform
        (including Protect) on one optional endpoint. A 401 still raises so
        reauth starts.
        """
        try:
            return await fetch()
        except UniFiAuthenticationError as err:
            if not self._is_unsupported_response(err):
                raise
            unsupported: Exception = err
        except Exception as err:
            if not self._is_unsupported_response(err):
                log = (
                    _LOGGER.debug
                    if (section, site_id) in self._failed_sections
                    else _LOGGER.warning
                )
                log(
                    "Config coordinator: Unable to fetch %s for site %s, keeping "
                    "the last known data: %s",
                    section,
                    site_id,
                    err,
                )
                return None
            unsupported = err
        _LOGGER.debug(
            "Config coordinator: %s not available for site %s: %s",
            section,
            site_id,
            unsupported,
        )
        return []

    @staticmethod
    def _map_legacy_site_names(
        integration_sites: dict[str, dict[str, Any]],
        legacy_sites: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Map integration site IDs to classic ("legacy") site names."""

        def _norm(value: Any) -> str | None:
            if not isinstance(value, str):
                return None
            stripped = value.strip().lower()
            return stripped or None

        legacy: list[tuple[str, set[str]]] = []
        for site in legacy_sites:
            name = site.get("name")
            if not isinstance(name, str) or not name:
                continue
            candidates = {
                c
                for c in (
                    _norm(name),
                    _norm(site.get("desc")),
                    _norm(site.get("description")),
                )
                if c is not None
            }
            legacy.append((name, candidates))

        mappings: dict[str, str] = {}
        for site_id, site_data in integration_sites.items():
            candidates = {
                c
                for c in (
                    _norm(site_id),
                    _norm(site_data.get("name")),
                    _norm(site_data.get("description")),
                    _norm(site_data.get("desc")),
                )
                if c is not None
            }
            for legacy_name, legacy_candidates in legacy:
                if candidates & legacy_candidates:
                    mappings[site_id] = legacy_name
                    break
            if site_id not in mappings and len(legacy) == 1:
                mappings[site_id] = legacy[0][0]
        return mappings

    @staticmethod
    def _wifi_qr_payload(
        ssid: str,
        passphrase: str | None,
        security: str | None,
        *,
        hidden: bool,
    ) -> str:
        """
        Build a standard ``WIFI:`` QR payload string.

        Follows the de-facto WiFi network config QR format consumed by phone
        cameras: ``WIFI:T:<auth>;S:<ssid>;P:<password>;H:<hidden>;;``.
        """

        def _escape(value: str) -> str:
            for char in ("\\", ";", ",", ":", '"'):
                value = value.replace(char, f"\\{char}")
            return value

        security_lower = (security or "").lower()
        if not passphrase or security_lower in ("", "open", "none"):
            auth = "nopass"
        elif "wep" in security_lower:
            auth = "WEP"
        else:
            auth = "WPA"

        parts = [f"T:{auth}", f"S:{_escape(ssid)}"]
        if auth != "nopass" and passphrase:
            parts.append(f"P:{_escape(passphrase)}")
        if hidden:
            parts.append("H:true")
        return "WIFI:" + ";".join(parts) + ";;"

    @staticmethod
    def _enrich_wifi(
        wifi_dict: dict[str, dict[str, Any]],
        legacy_configs: list[dict[str, Any]],
        active_clients: list[dict[str, Any]],
    ) -> None:
        """
        Add secrets, per-SSID client counts, and QR payloads to WiFi data.

        Secrets come from the classic ``/rest/wlanconf`` data (the official API
        redacts them); per-SSID counts are derived from active clients' essid.
        """
        configs_by_name = {
            config.get("name"): config
            for config in legacy_configs
            if config.get("name")
        }

        counts: dict[str, int] = {}
        for client in active_clients:
            if client.get("is_wired"):
                continue
            essid = client.get("essid")
            if essid:
                counts[essid] = counts.get(essid, 0) + 1

        for wifi in wifi_dict.values():
            ssid = wifi.get("name") or wifi.get("ssid")
            if not ssid:
                continue

            wifi["num_connected_clients"] = counts.get(ssid, 0)

            config = configs_by_name.get(ssid)
            if config is None:
                continue

            passphrase = config.get("x_passphrase")
            security = config.get("security")
            hidden = bool(config.get("hide_ssid"))
            wifi["ssid"] = ssid
            wifi["passphrase"] = passphrase
            wifi["security"] = security
            wifi["wpa_mode"] = config.get("wpa_mode")
            wifi["hide_ssid"] = hidden
            wifi["is_guest"] = config.get("is_guest", wifi.get("isGuest", False))
            wifi["qr_code"] = UnifiConfigCoordinator._wifi_qr_payload(
                ssid, passphrase, security, hidden=hidden
            )

    @staticmethod
    def _client_links(active_clients: list[Any]) -> dict[str, dict[str, Any]]:
        """
        Extract each active client's switch port, AP, VLAN and network name.

        The v1 clients endpoint leaves swMac/swPort/apMac/vlan/networkId null
        on current firmware; the classic /stat/sta response (already fetched
        for per-SSID counts) carries them. Keyed by normalised client MAC so
        the topology builder can join it to v1 clients.
        """
        links: dict[str, dict[str, Any]] = {}
        for client in active_clients:
            if not isinstance(client, dict):
                continue
            client_mac = normalize_mac(client.get("mac"))
            if client_mac is None:
                continue
            link: dict[str, Any] = {}
            for key in ("sw_mac", "ap_mac"):
                mac = normalize_mac(client.get(key))
                if mac is not None:
                    link[key] = mac
            sw_port = client.get("sw_port")
            if isinstance(sw_port, int) and not isinstance(sw_port, bool):
                link["sw_port"] = sw_port
            # VLAN 0 is an 802.1Q priority tag, not a real VLAN; untagged
            # (the default network) reports no vlan key at all on real
            # hardware, so only a VLAN id of 1 or higher is kept.
            vlan = client.get("vlan")
            if isinstance(vlan, int) and not isinstance(vlan, bool) and vlan >= 1:
                link["vlan"] = vlan
            network_name = client.get("network")
            if isinstance(network_name, str) and network_name:
                link["network_name"] = network_name
            links[client_mac] = link
        return links

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch configuration data from API."""
        try:
            # Get all sites
            _LOGGER.debug("Config coordinator: Fetching sites")
            sites_models = []
            if self._network_available:
                other_app_available = (
                    self.protect_client is not None or self._innerspace_available
                )
                try:
                    sites_models = await self.network_client.sites.get_all()
                except (UniFiNotFoundError, UniFiAuthenticationError) as err:
                    if other_app_available:
                        self._network_available = False
                        _LOGGER.debug(
                            "Config coordinator: Network API not available on "
                            "console: %s",
                            err,
                        )
                    else:
                        raise
                except UniFiResponseError as err:
                    if not other_app_available or err.status_code != HTTPStatus.OK:
                        raise
                    self._network_available = False
                    _LOGGER.debug(
                        "Config coordinator: sites endpoint returned a non-JSON "
                        "body (status %s) - console has no Network application",
                        err.status_code,
                    )

            site_list = [self._model_to_dict(s) for s in sites_models]
            all_sites: dict[str, dict[str, Any]] = {
                site["id"]: site for site in site_list if site.get("id")
            }
            self.available_sites = {
                site_id: str(
                    site.get("name") or site.get("internalReference") or site_id
                )
                for site_id, site in all_sites.items()
            }
            sites = self._filter_selected_sites(all_sites)
            self.data["sites"] = sites

            _LOGGER.debug(
                "Config coordinator: Found %d sites",
                len(sites),
            )

            if not sites:
                self.data["sites"] = sites
                self.data["wifi"] = {}
                self.data["firewall_rules"] = {}
                self.data["policy_based_routes"] = {}
                self.data["vpn_clients"] = {}
                self.data["site_vpns"] = {}
                self.data["network_info"] = {}
                self.data["client_links"] = {}
                self._available = True
                self.data["last_update"] = datetime.now(tz=UTC)
                return self.data

            # Per-site maps are updated in place below, so drop any site that
            # is no longer polled (removed from the console, or deselected)
            # rather than keep serving its last values.
            for key in (
                "wifi",
                "firewall_rules",
                "policy_based_routes",
                "vpn_clients",
                "site_vpns",
            ):
                self.data[key] = {
                    site_id: value
                    for site_id, value in self.data[key].items()
                    if site_id in self.data["sites"]
                }

            # Resolve classic site names so we can enrich WiFi data with secrets
            # and per-SSID client counts that the official API does not expose.
            legacy_site_names: dict[str, str] = {}
            legacy_mapping_failed = False
            try:
                legacy_sites = await self.network_client.sites.get_legacy_all()
                legacy_site_names = self._map_legacy_site_names(sites, legacy_sites)
            except Exception as err:
                legacy_mapping_failed = True
                _LOGGER.debug(
                    "Config coordinator: Unable to fetch legacy site mapping: %s",
                    err,
                )

            # Everything below is collected into fresh dicts and only
            # published once every site has refreshed. An error that fails
            # the refresh (e.g. a 401) part-way through therefore leaves the
            # previous snapshot intact rather than a half-updated one.
            wifi_by_site: dict[str, dict[str, Any]] = {}
            firewall_by_site: dict[str, dict[str, Any]] = {}
            failed_sections: set[tuple[str, str]] = set()
            routes_by_site: dict[str, dict[str, Any]] = {}
            vpn_clients_by_site: dict[str, dict[str, Any]] = {}
            site_vpns_by_site: dict[str, dict[str, Any]] = {}
            client_links_by_site: dict[str, dict[str, Any]] = {}

            for site_id in sites:
                _LOGGER.debug(
                    "Config coordinator: Fetching WiFi networks for site %s",
                    site_id,
                )
                wifi_models = await self._fetch_optional_section(
                    "wifi", site_id, partial(self.network_client.wifi.get_all, site_id)
                )
                if wifi_models is None:
                    failed_sections.add(("wifi", site_id))
                    wifi_by_site[site_id] = self.data["wifi"].get(site_id, {})
                wifi_dict = {}
                for wifi_model in wifi_models or []:
                    wifi = self._model_to_dict(wifi_model)
                    wifi_id = wifi.get("id")
                    if wifi_id:
                        wifi_dict[wifi_id] = wifi
                # One classic /stat/sta call per site feeds both the topology
                # client links and the per-SSID Wi-Fi counts. It runs even
                # when the Wi-Fi section failed, so topology keeps its links.
                legacy_name = legacy_site_names.get(site_id)
                active_clients: list[Any] | None = None
                if legacy_name:
                    try:
                        active_clients = (
                            await self.network_client.clients.get_active_legacy(
                                legacy_name
                            )
                        )
                    except Exception as err:
                        _LOGGER.debug(
                            "Config coordinator: Unable to fetch active clients "
                            "for site %s: %s",
                            site_id,
                            err,
                        )
                client_links_by_site[site_id] = (
                    self._client_links(active_clients)
                    if active_clients is not None
                    else self.data["client_links"].get(site_id, {})
                )

                # Enrich with classic data (secrets, per-SSID counts, QR).
                if (
                    wifi_models is not None
                    and legacy_name
                    and active_clients is not None
                ):
                    try:
                        legacy_configs = (
                            await self.network_client.wifi.get_legacy_configs(
                                legacy_name
                            )
                        )
                        self._enrich_wifi(wifi_dict, legacy_configs, active_clients)
                    except Exception as err:
                        _LOGGER.debug(
                            "Config coordinator: Unable to enrich WiFi data "
                            "for site %s: %s",
                            site_id,
                            err,
                        )

                if wifi_models is not None:
                    wifi_by_site[site_id] = wifi_dict
                    _LOGGER.debug(
                        "Config coordinator: Successfully fetched %d WiFi networks "
                        "for site %s",
                        len(wifi_dict),
                        site_id,
                    )

                _LOGGER.debug(
                    "Config coordinator: Fetching firewall rules for site %s",
                    site_id,
                )
                firewall_models = await self._fetch_optional_section(
                    "firewall_rules",
                    site_id,
                    partial(self.network_client.firewall.list_rules, site_id),
                )
                firewall_rules_dict = {}
                for firewall_model in firewall_models or []:
                    firewall_rule = self._model_to_dict(firewall_model)
                    firewall_rule_id = firewall_rule.get("id")
                    if firewall_rule_id:
                        firewall_rules_dict[firewall_rule_id] = firewall_rule
                if firewall_models is None:
                    failed_sections.add(("firewall_rules", site_id))
                    firewall_by_site[site_id] = self.data["firewall_rules"].get(
                        site_id, {}
                    )
                else:
                    firewall_by_site[site_id] = firewall_rules_dict
                    _LOGGER.debug(
                        "Config coordinator: Successfully fetched %d firewall rules "
                        "for site %s",
                        len(firewall_rules_dict),
                        site_id,
                    )

                # Fetch policy-based routes (traffic routes) via legacy v2 endpoint
                legacy_name = legacy_site_names.get(site_id)
                if legacy_name:
                    try:
                        _LOGGER.debug(
                            "Config coordinator: Fetching policy-based routes "
                            "for site %s (%s)",
                            site_id,
                            legacy_name,
                        )
                        route_models = await self.network_client.routes.list_routes(
                            legacy_name
                        )
                        routes_dict: dict[str, Any] = {}
                        for route_model in route_models:
                            route = self._model_to_dict(route_model)
                            route_id = route.get("id") or route.get("_id")
                            if route_id:
                                routes_dict[route_id] = route
                        routes_by_site[site_id] = routes_dict
                        _LOGGER.debug(
                            "Config coordinator: Successfully fetched %d "
                            "policy-based routes for site %s",
                            len(routes_dict),
                            site_id,
                        )
                    except UniFiAuthenticationError:
                        raise
                    except Exception as err:
                        _LOGGER.debug(
                            "Config coordinator: Policy-based routes unavailable "
                            "for site %s: %s",
                            site_id,
                            err,
                        )
                        routes_by_site[site_id] = {}
                else:
                    routes_by_site[site_id] = {}

                # Fetch VPN clients via classic networkconf endpoint
                if legacy_name:
                    try:
                        _LOGGER.debug(
                            "Config coordinator: Fetching VPN clients for site %s (%s)",
                            site_id,
                            legacy_name,
                        )
                        vpn_client_models = (
                            await self.network_client.vpn_clients.list_vpn_clients(
                                legacy_name
                            )
                        )
                        vpn_clients_dict: dict[str, Any] = {}
                        for vpn_client_model in vpn_client_models:
                            vpn_client = self._model_to_dict(vpn_client_model)
                            vpn_client_id = vpn_client.get("id") or vpn_client.get(
                                "_id"
                            )
                            if vpn_client_id:
                                vpn_clients_dict[vpn_client_id] = vpn_client
                        vpn_clients_by_site[site_id] = vpn_clients_dict
                        _LOGGER.debug(
                            "Config coordinator: Successfully fetched %d "
                            "VPN clients for site %s",
                            len(vpn_clients_dict),
                            site_id,
                        )
                    except UniFiAuthenticationError:
                        raise
                    except Exception as err:
                        _LOGGER.debug(
                            "Config coordinator: VPN clients unavailable "
                            "for site %s: %s",
                            site_id,
                            err,
                        )
                        vpn_clients_by_site[site_id] = {}
                else:
                    vpn_clients_by_site[site_id] = {}

                # Site-to-site VPN tunnels (names/types for per-tunnel entities;
                # their live state comes from the device coordinator).
                if legacy_name:
                    try:
                        vpn_endpoint = self.network_client.vpn_clients
                        tunnels = await vpn_endpoint.list_site_to_site_vpns(legacy_name)
                        site_vpns_by_site[site_id] = {
                            tunnel["id"]: tunnel for tunnel in tunnels
                        }
                    except UniFiAuthenticationError:
                        raise
                    except Exception as err:
                        _LOGGER.debug(
                            "Config coordinator: Site-to-site VPNs unavailable "
                            "for site %s: %s",
                            site_id,
                            err,
                        )
                        # Keep the last known tunnels: their sensors would
                        # otherwise all go unavailable until the next poll.
                        site_vpns_by_site[site_id] = self.data.get("site_vpns", {}).get(
                            site_id, {}
                        )
                elif legacy_mapping_failed:
                    # Same reason: the tunnels were not re-read, not deleted.
                    site_vpns_by_site[site_id] = self.data.get("site_vpns", {}).get(
                        site_id, {}
                    )
                else:
                    site_vpns_by_site[site_id] = {}

            self.data["sites"] = sites
            self.data["wifi"] = wifi_by_site
            self.data["firewall_rules"] = firewall_by_site
            self.data["policy_based_routes"] = routes_by_site
            self.data["vpn_clients"] = vpn_clients_by_site
            self.data["site_vpns"] = site_vpns_by_site
            self.data["client_links"] = client_links_by_site
            for section, site_id in self._failed_sections - failed_sections:
                _LOGGER.info(
                    "Config coordinator: %s fetch for site %s recovered",
                    section,
                    site_id,
                )
            self._failed_sections = failed_sections
            self._available = True
            _LOGGER.debug(
                "Config coordinator: Update complete - %d sites, %d WiFi configs, "
                "%d firewall rules, %d policy-based routes, %d VPN clients",
                len(self.data["sites"]),
                sum(len(w) for w in self.data["wifi"].values()),
                sum(len(rules) for rules in self.data["firewall_rules"].values()),
                sum(
                    len(routes) for routes in self.data["policy_based_routes"].values()
                ),
                sum(len(clients) for clients in self.data["vpn_clients"].values()),
            )

            return self.data

        except UniFiAuthenticationError as err:
            self._handle_auth_error(err)
        except UniFiConnectionError as err:
            self._handle_connection_error(err)
        except UniFiTimeoutError as err:
            self._handle_timeout_error(err)
        except UniFiResponseError as err:
            self._handle_response_error(err)
        except Exception as err:
            self._handle_generic_error(err)

        # Should never reach here due to raises above
        return self.data  # pragma: no cover

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        """Get site data by site ID."""
        sites = self.data.get("sites", {})
        result = sites.get(site_id)
        return result if isinstance(result, dict) else None

    def _filter_selected_sites(
        self, sites: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Narrow sites to the ones selected in options.

        Both coordinators fan out per site from ``self.data["sites"]``, so
        filtering here is what keeps unselected sites off the API entirely.
        """
        selected = self.config_entry.options.get(CONF_SITE_IDS)
        if not selected or not sites:
            return sites

        filtered = {
            site_id: site for site_id, site in sites.items() if site_id in selected
        }
        if filtered:
            self._warned_no_selected_sites = False
        elif not self._warned_no_selected_sites:
            # Warn once rather than on every poll until the user acts.
            self._warned_no_selected_sites = True
            _LOGGER.warning(
                "Config coordinator: none of the selected sites (%s) exist on "
                "the console any more; re-select sites in the integration options",
                ", ".join(selected),
            )
        return filtered

    def get_site_ids(self) -> list[str]:
        """Get all site IDs."""
        return list(self.data.get("sites", {}).keys())

    def get_wifi_networks(self, site_id: str) -> dict[str, Any]:
        """Get WiFi networks for a site."""
        result: dict[str, Any] = self.data.get("wifi", {}).get(site_id, {})
        return result

    def get_firewall_rules(self, site_id: str) -> dict[str, Any]:
        """Get firewall rules for a site."""
        result: dict[str, Any] = self.data.get("firewall_rules", {}).get(site_id, {})
        return result

    def get_policy_based_routes(self, site_id: str) -> dict[str, Any]:
        """Get policy-based routes for a site."""
        result: dict[str, Any] = self.data.get("policy_based_routes", {}).get(
            site_id, {}
        )
        return result

    def get_vpn_clients(self, site_id: str) -> dict[str, Any]:
        """Get VPN clients for a site."""
        result: dict[str, Any] = self.data.get("vpn_clients", {}).get(site_id, {})
        return result
