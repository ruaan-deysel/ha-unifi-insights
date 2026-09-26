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

from .base import UnifiBaseCoordinator
from .config_sections import (
    async_fetch_site_routes,
    async_fetch_site_vpn_clients,
    async_fetch_site_vpns,
    client_links,
    enrich_wifi,
    map_legacy_site_names,
    resolve_report_site_name,
    wifi_qr_payload,
)
from .internet_activity import (
    WINDOW_1D_MS,
    WINDOW_1H_MS,
    WINDOW_1M_MS,
    WINDOW_1W_MS,
    aggregate_internet_activity_windows,
    async_call_site_report,
    async_fetch_site_internet_activity,
)

__all__ = [
    "WINDOW_1D_MS",
    "WINDOW_1H_MS",
    "WINDOW_1M_MS",
    "WINDOW_1W_MS",
    "UnifiConfigCoordinator",
    "aggregate_internet_activity_windows",
]

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
    - Internet activity rolling-window traffic statistics
    - Network info
    """

    _map_legacy_site_names = staticmethod(map_legacy_site_names)
    _wifi_qr_payload = staticmethod(wifi_qr_payload)
    _enrich_wifi = staticmethod(enrich_wifi)
    _client_links = staticmethod(client_links)

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
            "internet_activity": {},
            "internet_activity_unavailable": set(),
        }
        self.available_sites: dict[str, str] = {}
        self._warned_no_selected_sites = False
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

    def internet_activity_available(self, site_id: str) -> bool:
        """Return True if the last refresh fetched internet activity for a site."""
        return self.last_update_success and ("internet_activity", site_id) not in (
            self._failed_sections
        )

    async def _fetch_optional_section(
        self,
        section: str,
        site_id: str,
        fetch: Callable[[], Awaitable[list[Any]]],
    ) -> list[Any] | None:
        """Fetch an optional per-site section (WiFi, firewall, or site reports)."""
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

    async def _call_site_report(
        self,
        site_name: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
    ) -> list[Any]:
        """Invoke the Network client site report method for one interval."""
        return await async_call_site_report(
            self.network_client,
            site_name,
            interval,
            start_ms=start_ms,
            end_ms=end_ms,
        )

    async def _fetch_site_internet_activity(
        self,
        *,
        site_id: str,
        site_name: str,
        now_ms: int,
    ) -> dict[str, dict[str, int]] | None:
        """Fetch ``5minutes``, ``hourly``, and ``daily`` site reports and aggregate."""
        return await async_fetch_site_internet_activity(
            self._fetch_optional_section,
            self._call_site_report,
            site_id=site_id,
            site_name=site_name,
            now_ms=now_ms,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch configuration data from API."""
        try:
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

            if not sites:
                for key in (
                    "wifi",
                    "firewall_rules",
                    "policy_based_routes",
                    "vpn_clients",
                    "site_vpns",
                    "network_info",
                    "client_links",
                    "internet_activity",
                ):
                    self.data[key] = {}
                self.data["internet_activity_unavailable"] = set()
                self._available = True
                self.data["last_update"] = datetime.now(tz=UTC)
                return self.data

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

            wifi_by_site: dict[str, dict[str, Any]] = {}
            firewall_by_site: dict[str, dict[str, Any]] = {}
            internet_activity_by_site: dict[str, dict[str, dict[str, int]]] = {}
            failed_sections: set[tuple[str, str]] = set()
            routes_by_site: dict[str, dict[str, Any]] = {}
            vpn_clients_by_site: dict[str, dict[str, Any]] = {}
            site_vpns_by_site: dict[str, dict[str, Any]] = {}
            client_links_by_site: dict[str, dict[str, Any]] = {}
            now_ms = int(datetime.now(tz=UTC).timestamp() * 1000)

            for site_id in sites:
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

                report_site_name = resolve_report_site_name(
                    site_id, sites.get(site_id), legacy_name
                )
                site_activity = await self._fetch_site_internet_activity(
                    site_id=site_id,
                    site_name=report_site_name,
                    now_ms=now_ms,
                )
                if site_activity is None:
                    failed_sections.add(("internet_activity", site_id))
                    prior_activity = self.data.get("internet_activity", {}).get(site_id)
                    if isinstance(prior_activity, dict) and prior_activity:
                        internet_activity_by_site[site_id] = prior_activity
                elif site_activity:
                    internet_activity_by_site[site_id] = site_activity

                routes_by_site[site_id] = await async_fetch_site_routes(
                    self.network_client, self._model_to_dict, site_id, legacy_name
                )
                vpn_clients_by_site[site_id] = await async_fetch_site_vpn_clients(
                    self.network_client, self._model_to_dict, site_id, legacy_name
                )
                site_vpns_by_site[site_id] = await async_fetch_site_vpns(
                    self.network_client,
                    site_id,
                    legacy_name,
                    legacy_mapping_failed=legacy_mapping_failed,
                    prior_site_vpns=self.data.get("site_vpns", {}).get(site_id, {}),
                )

            self.data["sites"] = sites
            self.data["wifi"] = wifi_by_site
            self.data["firewall_rules"] = firewall_by_site
            self.data["internet_activity"] = internet_activity_by_site
            self.data["internet_activity_unavailable"] = {
                site_id
                for section, site_id in failed_sections
                if section == "internet_activity"
            }
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

        return self.data  # pragma: no cover

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        """Get site data by site ID."""
        sites = self.data.get("sites", {})
        result = sites.get(site_id)
        return result if isinstance(result, dict) else None

    def _filter_selected_sites(
        self, sites: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Narrow sites to the ones selected in options."""
        selected = self.config_entry.options.get(CONF_SITE_IDS)
        if not selected or not sites:
            return sites

        filtered = {
            site_id: site for site_id, site in sites.items() if site_id in selected
        }
        if filtered:
            self._warned_no_selected_sites = False
        elif not self._warned_no_selected_sites:
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
