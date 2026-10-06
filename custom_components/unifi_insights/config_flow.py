"""Config flow for UniFi Insights integration."""

from __future__ import annotations

import hashlib
import inspect
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from pydantic import ValidationError

from .api import (
    ApiKeyAuth,
    ConnectionType,
    LocalAuth,
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiNotFoundError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from .api.carrier_fabric.client import UniFiCarrierFabricClient
from .api.network import UniFiNetworkClient
from .api.protect import UniFiProtectClient
from .console_identity import (
    DEFAULT_SITE_ID,
    device_fields,
    first_non_default_site_id,
    normalize_mac,
    resolve_console_identity,
)
from .const import (
    CARRIER_FABRIC_REQUEST_TIMEOUT,
    CONF_CARRIER_ACTIONS,
    CONF_CARRIER_ORG_ID,
    CONF_CLIENT_CONTROL,
    CONF_CONNECTION_TYPE,
    CONF_CONSOLE_ID,
    CONF_CONSOLE_NAME,
    CONF_SITE_IDS,
    CONF_TRACK_CLIENTS,
    CONF_TRACK_SUBSCRIBERS,
    CONF_TRACK_WIFI_CLIENTS,
    CONF_TRACK_WIRED_CLIENTS,
    CONNECTION_TYPE_CARRIER_FABRIC,
    CONNECTION_TYPE_LOCAL,
    CONNECTION_TYPE_REMOTE,
    DEFAULT_API_HOST,
    DEFAULT_CARRIER_ACTIONS,
    DEFAULT_CLIENT_CONTROL,
    DEFAULT_TRACK_CLIENTS,
    DEFAULT_TRACK_SUBSCRIBERS,
    DOMAIN,
)
from .probe import (
    ProbeResult,
    ProbeStatus,
    async_probe_carrier_fabric,
    async_probe_network,
    async_probe_protect,
    async_probe_with_client,
    is_transient_error,
)

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Insights."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._connection_type: str | None = None
        self._remote_api_key: str | None = None
        self._discovered_remote_consoles: dict[str, str] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> UnifiInsightsOptionsFlow:
        """Get the options flow for this handler."""
        return UnifiInsightsOptionsFlow()

    @staticmethod
    def _extract_remote_console_options(hosts: list[dict[str, Any]]) -> dict[str, str]:
        """Build selector labels for accessible remote consoles."""
        console_hosts: list[dict[str, Any]] = []
        network_servers: list[dict[str, Any]] = []

        for host in hosts:
            host_id = host.get("id")
            host_type = host.get("type")
            if (
                not isinstance(host_id, str)
                or not host_id
                or not isinstance(host_type, str)
            ):
                continue

            if host_type == "console":
                console_hosts.append(host)
            elif host_type == "network-server":
                network_servers.append(host)

        candidates = console_hosts or network_servers
        options: dict[str, str] = {}

        for host in sorted(candidates, key=lambda item: str(item.get("id", ""))):
            host_id = str(host["id"])
            reported_state = host.get("reportedState")
            hostname = (
                reported_state.get("hostname")
                if isinstance(reported_state, dict)
                else None
            )
            host_type = str(host.get("type", "console")).replace("-", " ")
            display_name = hostname or host_id
            options[host_id] = f"{display_name} ({host_type})"

        return options

    @staticmethod
    def _normalize_remote_console_id(
        console_id: str,
        discovered_consoles: dict[str, str],
    ) -> str | None:
        """Normalize manual or stored console IDs against discovered host IDs."""
        candidate = console_id.strip()
        if not candidate:
            return None

        lowered_candidate = candidate.lower()
        for discovered_id in discovered_consoles:
            lowered_discovered = discovered_id.lower()
            if lowered_candidate == lowered_discovered:
                return discovered_id

            discovered_prefix = lowered_discovered.split(":", 1)[0]
            if lowered_candidate == discovered_prefix:
                return discovered_id

        return None

    async def _async_discover_remote_consoles(self, api_key: str) -> dict[str, str]:
        """Discover accessible remote consoles for a UI.com API key."""
        auth = ApiKeyAuth(api_key=api_key)
        async with UniFiNetworkClient(
            auth=auth,
            connection_type=ConnectionType.REMOTE,
            timeout=30,
        ) as network_client:
            hosts = await network_client.get_hosts()

        return self._extract_remote_console_options(hosts)

    @staticmethod
    def _flow_error_for_probes(*probes: ProbeResult) -> str:
        """
        Pick the form error for a console where no application was usable.

        A temporary failure wins, so a correct key is never reported as
        invalid while the console is restarting or answering 5xx. Then a
        rejected key, a response that failed to parse, other unexpected
        errors, and a 404 or "NVR not found" (api_unsupported). Anything
        else - no sites, or a web-UI page in place of the API - keeps the
        historical "invalid_auth": the console commonly answers that way for
        a key it does not accept.
        """
        statuses = {probe.status for probe in probes}
        if ProbeStatus.UNREACHABLE in statuses:
            return "cannot_connect"
        if ProbeStatus.AUTH_FAILED in statuses:
            return "invalid_auth"
        errors = [probe.error for probe in probes if probe.status is ProbeStatus.ERROR]
        if any(isinstance(error, ValidationError) for error in errors):
            return "site_parse_error"
        if errors:
            return "unknown"
        # 404 from the integration API, or Protect answering without an NVR
        # record ("NVR not found"), as before this probe refactor.
        if any(
            isinstance(probe.error, UniFiNotFoundError)
            or type(probe.error) is ValueError
            for probe in probes
        ):
            return "api_unsupported"
        return "invalid_auth"

    async def _async_validate_local_connection(
        self,
        host: str,
        api_key: str,
        *,
        verify_ssl: bool = False,
    ) -> tuple[bool, str | None, dict[str, str]]:
        """Validate local connection against Network and/or Protect APIs."""
        auth = LocalAuth(api_key=api_key, verify_ssl=verify_ssl)
        console_info: dict[str, str] = {}

        # 1. Probe Network API
        async def _probe_network_and_extract(
            network_client: UniFiNetworkClient,
        ) -> ProbeResult:
            res = await async_probe_network(network_client)
            if res.status is ProbeStatus.AVAILABLE and res.sites:
                site_ids = [getattr(site, "id", None) for site in res.sites]
                # Sites are scanned in API order and the scan stops at the
                # first console found, so the ordinary single-site console
                # still costs one request. Only a controller whose gateway
                # lives outside the first site pays for more - and that is
                # exactly the case that used to leave the flow with no MAC
                # while setup found one, producing a duplicate entry.
                for site_id in site_ids:
                    # Guarding per site, not around the loop: the client stays
                    # usable after a failed request, and setup would still find
                    # the console in a later site. Abandoning the scan here
                    # would put the two paths back out of step.
                    try:
                        devices = await network_client.devices.get_all(
                            site_id=site_id or DEFAULT_SITE_ID
                        )
                    except Exception:
                        _LOGGER.debug(
                            "Could not inspect devices for site %s",
                            site_id,
                            exc_info=True,
                        )
                        continue
                    mac, name = resolve_console_identity(
                        device_fields(dev) for dev in devices
                    )
                    if name and "name" not in console_info:
                        console_info["name"] = name
                    if mac:
                        console_info["id"] = mac
                        console_info["mac"] = mac
                        break

                if "id" not in console_info:
                    # Same ordering rule setup applies, so both derive the
                    # same identity instead of drifting apart.
                    console_info["id"] = (
                        first_non_default_site_id(site_ids) or host.lower()
                    )
                    site_name = getattr(res.sites[0], "name", None)
                    if type(site_name) is str:
                        console_info["name"] = site_name
            return res

        network = await async_probe_with_client(
            UniFiNetworkClient(
                auth=auth,
                base_url=host,
                connection_type=ConnectionType.LOCAL,
                timeout=30,
            ),
            _probe_network_and_extract,
        )
        if network.status is ProbeStatus.AVAILABLE:
            return True, None, console_info

        # 2. Probe Protect API
        async def _probe_protect_and_extract(
            protect_client: UniFiProtectClient,
        ) -> ProbeResult:
            res = await async_probe_protect(protect_client)
            if res.status is ProbeStatus.AVAILABLE:
                console_info["id"] = host.lower()
                console_info["name"] = "UniFi Protect"
                if hasattr(protect_client, "nvr") and hasattr(
                    protect_client.nvr, "get"
                ):
                    nvr_call = protect_client.nvr.get()
                    if inspect.isawaitable(nvr_call):
                        try:
                            nvr = await nvr_call
                            if nvr:
                                nvr_mac = normalize_mac(getattr(nvr, "mac", None))
                                if nvr_mac:
                                    console_info["id"] = nvr_mac
                                    console_info["mac"] = nvr_mac
                                nvr_name = getattr(nvr, "name", None) or getattr(
                                    nvr, "display_name", None
                                )
                                if type(nvr_name) is str:
                                    console_info["name"] = nvr_name
                        except Exception:
                            _LOGGER.debug(
                                "Could not inspect protect NVR", exc_info=True
                            )
            return res

        protect = await async_probe_with_client(
            UniFiProtectClient(
                auth=auth,
                base_url=host,
                connection_type=ConnectionType.LOCAL,
                timeout=30,
            ),
            _probe_protect_and_extract,
        )
        if protect.status is ProbeStatus.AVAILABLE:
            return True, None, console_info

        return False, self._flow_error_for_probes(network, protect), console_info

    async def _async_validate_remote_console(
        self,
        api_key: str,
        console_id: str,
    ) -> bool:
        """
        Validate remote connectivity for a specific console host ID.

        Returns False when neither application is usable with this key and
        console. A temporary failure (connection, timeout, 5xx, rate limit)
        raises UniFiConnectionError so the step reports cannot_connect
        rather than an invalid console.
        """
        auth = ApiKeyAuth(api_key=api_key)

        network = await async_probe_with_client(
            UniFiNetworkClient(
                auth=auth,
                connection_type=ConnectionType.REMOTE,
                console_id=console_id,
                timeout=30,
            ),
            async_probe_network,
        )
        if network.status is ProbeStatus.AVAILABLE:
            return True

        protect = await async_probe_with_client(
            UniFiProtectClient(
                auth=auth,
                connection_type=ConnectionType.REMOTE,
                console_id=console_id,
                timeout=30,
            ),
            async_probe_protect,
        )
        if protect.status is ProbeStatus.AVAILABLE:
            return True

        for probe in (network, protect):
            if probe.status is ProbeStatus.UNREACHABLE:
                msg = f"Remote console temporarily unavailable: {probe.error}"
                raise UniFiConnectionError(msg) from probe.error
        return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - connection type selection."""
        if user_input is not None:
            self._connection_type = user_input[CONF_CONNECTION_TYPE]
            if self._connection_type == CONNECTION_TYPE_LOCAL:
                return await self.async_step_local()
            if self._connection_type == CONNECTION_TYPE_CARRIER_FABRIC:
                return await self.async_step_carrier_fabric()
            return await self.async_step_remote()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONNECTION_TYPE, default=CONNECTION_TYPE_LOCAL
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=CONNECTION_TYPE_LOCAL,
                                    label="Local (Direct connection)",
                                ),
                                SelectOptionDict(
                                    value=CONNECTION_TYPE_REMOTE,
                                    label="Remote (UniFi Cloud)",
                                ),
                                SelectOptionDict(
                                    value=CONNECTION_TYPE_CARRIER_FABRIC,
                                    label="Carrier Fabric (ISP)",
                                ),
                            ],
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def _async_validate_carrier_fabric_key(
        self, api_key: str
    ) -> tuple[ProbeResult, dict[str, str]]:
        """
        Probe Carrier Fabric with an ISP API key.

        Returns the probe result and the form errors for it (empty when the
        key works). Shared by setup, reauth and reconfigure.
        """
        client = UniFiCarrierFabricClient(
            auth=ApiKeyAuth(api_key=api_key),
            session=async_get_clientsession(self.hass),
            timeout=CARRIER_FABRIC_REQUEST_TIMEOUT,
        )
        probe_res = await async_probe_with_client(client, async_probe_carrier_fabric)

        if probe_res.status in (ProbeStatus.AVAILABLE, ProbeStatus.EMPTY):
            return probe_res, {}
        if probe_res.missing_scope:
            return probe_res, {"base": "carrier_missing_scope"}
        if probe_res.status is ProbeStatus.AUTH_FAILED:
            return probe_res, {CONF_API_KEY: "invalid_auth"}
        if probe_res.status is ProbeStatus.UNREACHABLE:
            return probe_res, {"base": "cannot_connect"}
        return probe_res, {"base": "unknown"}

    @staticmethod
    def _carrier_data_for_new_key(
        entry: ConfigEntry, api_key: str, probe_res: ProbeResult
    ) -> dict[str, Any] | None:
        """
        Return the entry data for a replacement key, or None for another org.

        The key is refused only when both the stored and the probed
        organisation are known and differ. Only the key (and a missing
        organisation id) change: the unique id never does.
        """
        stored_org_id = entry.data.get(CONF_CARRIER_ORG_ID)
        new_org_id = probe_res.org_id
        if (
            stored_org_id is not None
            and new_org_id is not None
            and stored_org_id != new_org_id
        ):
            return None

        new_data = {**entry.data, CONF_API_KEY: api_key}
        if stored_org_id is None and new_org_id is not None:
            new_data[CONF_CARRIER_ORG_ID] = new_org_id
        return new_data

    async def async_step_carrier_fabric(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Carrier Fabric ISP setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            probe_res, errors = await self._async_validate_carrier_fabric_key(api_key)
            if not errors:
                if probe_res.org_id:
                    unique_id = f"carrier_{probe_res.org_id}"
                else:
                    key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
                    unique_id = f"carrier_key_{key_hash}"

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="UniFi Carrier Fabric",
                    data={
                        CONF_CONNECTION_TYPE: CONNECTION_TYPE_CARRIER_FABRIC,
                        CONF_API_KEY: api_key,
                        CONF_CARRIER_ORG_ID: probe_res.org_id,
                    },
                )

        return self.async_show_form(
            step_id="carrier_fabric",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle local connection setup."""
        errors = {}

        if user_input is not None:
            try:
                (
                    is_valid,
                    error_code,
                    console_info,
                ) = await self._async_validate_local_connection(
                    host=user_input[CONF_HOST],
                    api_key=user_input[CONF_API_KEY],
                    verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
                )
                if is_valid:
                    console_id = console_info.get("id") or user_input[CONF_HOST].lower()
                    await self.async_set_unique_id(console_id)
                    self._abort_if_unique_id_configured()

                    entry_data: dict[str, Any] = {
                        CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, False),
                    }
                    if console_info.get("mac"):
                        entry_data[CONF_CONSOLE_ID] = console_info["mac"]
                    if console_info.get("name") and console_info.get("mac"):
                        entry_data[CONF_CONSOLE_NAME] = console_info["name"]

                    return self.async_create_entry(
                        title="UniFi Insights (Local)",
                        data=entry_data,
                    )

                if error_code == "invalid_auth":
                    errors[CONF_API_KEY] = "invalid_auth"
                else:
                    errors["base"] = error_code or "cannot_connect"

            except AbortFlow:
                raise
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_API_HOST): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_VERIFY_SSL, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_remote(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle remote/cloud connection setup."""
        errors = {}

        if user_input is not None:
            try:
                api_key = user_input[CONF_API_KEY].strip()
                discovered_consoles = await self._async_discover_remote_consoles(
                    api_key
                )
                if not discovered_consoles:
                    errors["base"] = "no_remote_consoles"
                else:
                    self._remote_api_key = api_key
                    self._discovered_remote_consoles = discovered_consoles
                    return await self.async_step_select_console()

            except UniFiAuthenticationError:
                errors[CONF_API_KEY] = "invalid_auth"
                self._remote_api_key = None
                self._discovered_remote_consoles = {}
            except UniFiConnectionError:
                errors["base"] = "cannot_connect"
            except UniFiTimeoutError:
                errors["base"] = "cannot_connect"
            except UniFiNotFoundError:
                _LOGGER.exception(
                    "UniFi cloud returned 404 while discovering consoles. "
                    "The Site Manager API may be unavailable for this account."
                )
                errors["base"] = "api_unsupported"
            except UniFiResponseError as err:
                if is_transient_error(err):
                    _LOGGER.warning("UniFi API temporarily unavailable: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.exception("Unexpected UniFi API response")
                    errors["base"] = "unknown"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="remote",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_console(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle remote console selection after API key validation."""
        if not self._remote_api_key or not self._discovered_remote_consoles:
            return await self.async_step_remote()

        errors = {}

        if user_input is not None:
            console_id = user_input[CONF_CONSOLE_ID]

            try:
                sites_found = await self._async_validate_remote_console(
                    self._remote_api_key,
                    console_id,
                )
                if sites_found:
                    await self.async_set_unique_id(console_id)
                    self._abort_if_unique_id_configured()

                    label = self._discovered_remote_consoles.get(console_id, "")
                    console_name = label.rsplit(" (", 1)[0] if " (" in label else label
                    title = (
                        f"UniFi - {console_name}"
                        if console_name and console_name != "Cloud"
                        else "UniFi Insights (Cloud)"
                    )

                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE,
                            CONF_CONSOLE_ID: console_id,
                            CONF_API_KEY: self._remote_api_key,
                        },
                    )

                errors[CONF_CONSOLE_ID] = "invalid_console_id"
            except AbortFlow:
                raise
            except UniFiAuthenticationError:
                errors[CONF_CONSOLE_ID] = "invalid_console_id"
            except UniFiConnectionError:
                errors["base"] = "cannot_connect"
            except UniFiTimeoutError:
                errors["base"] = "cannot_connect"
            except UniFiNotFoundError:
                _LOGGER.exception(
                    "UniFi cloud returned 404 while accessing the selected "
                    "console. The console may not expose the Network "
                    "Integration API."
                )
                errors["base"] = "api_unsupported"
            except ValidationError:
                _LOGGER.exception("Failed to parse site data from remote UniFi console")
                errors["base"] = "site_parse_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during console selection")
                errors["base"] = "unknown"

        options: list[SelectOptionDict] = [
            SelectOptionDict(value=console_id, label=label)
            for console_id, label in self._discovered_remote_consoles.items()
        ]

        return self.async_show_form(
            step_id="select_console",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONSOLE_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthorization if the API key becomes invalid."""
        _ = entry_data
        reauth_entry = self._get_reauth_entry()
        if (
            reauth_entry.data.get(CONF_CONNECTION_TYPE)
            == CONNECTION_TYPE_CARRIER_FABRIC
        ):
            return await self.async_step_reauth_carrier_fabric()
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_carrier_fabric(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that Carrier Fabric reauth is required."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            probe_res, errors = await self._async_validate_carrier_fabric_key(api_key)
            if not errors:
                new_data = self._carrier_data_for_new_key(
                    reauth_entry, api_key, probe_res
                )
                if new_data is None:
                    return self.async_abort(reason="carrier_org_mismatch")
                return self.async_update_reload_and_abort(reauth_entry, data=new_data)

        return self.async_show_form(
            step_id="reauth_carrier_fabric",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors = {}
        reauth_entry = self._get_reauth_entry()
        connection_type = reauth_entry.data.get(
            CONF_CONNECTION_TYPE, CONNECTION_TYPE_LOCAL
        )

        if user_input is not None:
            try:
                if connection_type == CONNECTION_TYPE_LOCAL:
                    (
                        is_valid,
                        error_code,
                        _,
                    ) = await self._async_validate_local_connection(
                        host=reauth_entry.data.get(CONF_HOST, DEFAULT_API_HOST),
                        api_key=user_input[CONF_API_KEY],
                        verify_ssl=reauth_entry.data.get(CONF_VERIFY_SSL, False),
                    )
                    if is_valid:
                        return self.async_update_reload_and_abort(
                            reauth_entry,
                            data={
                                **reauth_entry.data,
                                CONF_API_KEY: user_input[CONF_API_KEY],
                            },
                        )
                    if error_code == "invalid_auth":
                        errors[CONF_API_KEY] = "invalid_auth"
                    else:
                        errors["base"] = error_code or "cannot_connect"
                else:
                    api_key = user_input[CONF_API_KEY].strip()
                    discovered_consoles = await self._async_discover_remote_consoles(
                        api_key
                    )
                    if not discovered_consoles:
                        errors["base"] = "no_remote_consoles"
                    else:
                        console_id = self._normalize_remote_console_id(
                            reauth_entry.data.get(CONF_CONSOLE_ID, ""),
                            discovered_consoles,
                        )
                        if console_id is None:
                            errors["base"] = "invalid_console_id"
                        else:
                            try:
                                sites_found = await self._async_validate_remote_console(
                                    api_key,
                                    console_id,
                                )
                                if sites_found:
                                    return self.async_update_reload_and_abort(
                                        reauth_entry,
                                        data={
                                            **reauth_entry.data,
                                            CONF_API_KEY: api_key,
                                            CONF_CONSOLE_ID: console_id,
                                        },
                                    )
                                errors["base"] = "invalid_console_id"
                            except UniFiAuthenticationError:
                                errors["base"] = "invalid_console_id"

            except UniFiAuthenticationError:
                errors[CONF_API_KEY] = "invalid_auth"
            except UniFiConnectionError:
                errors["base"] = "cannot_connect"
            except UniFiTimeoutError:
                errors["base"] = "cannot_connect"
            except UniFiNotFoundError:
                _LOGGER.exception(
                    "UniFi controller returned 404 during reauth. The "
                    "controller may not expose the Network Integration API."
                )
                errors["base"] = "api_unsupported"
            except UniFiResponseError as err:
                if is_transient_error(err):
                    _LOGGER.warning("UniFi API temporarily unavailable: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.exception("Unexpected UniFi API response")
                    errors["base"] = "unknown"
            except ValidationError:
                _LOGGER.exception("Failed to parse site data during reauth")
                errors["base"] = "site_parse_error"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_reconfigure_carrier_fabric(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Carrier Fabric reconfiguration of the integration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            probe_res, errors = await self._async_validate_carrier_fabric_key(api_key)
            if not errors:
                new_data = self._carrier_data_for_new_key(entry, api_key, probe_res)
                if new_data is None:
                    return self.async_abort(reason="carrier_org_mismatch")
                return self.async_update_reload_and_abort(
                    entry, data=new_data, reason="reconfigure_successful"
                )

        return self.async_show_form(
            step_id="reconfigure_carrier_fabric",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        entry = self._get_reconfigure_entry()
        connection_type = entry.data.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_LOCAL)

        if connection_type == CONNECTION_TYPE_CARRIER_FABRIC:
            return await self.async_step_reconfigure_carrier_fabric(user_input)

        errors = {}

        if user_input is not None:
            try:
                if connection_type == CONNECTION_TYPE_LOCAL:
                    (
                        is_valid,
                        error_code,
                        console_info,
                    ) = await self._async_validate_local_connection(
                        host=user_input[CONF_HOST],
                        api_key=user_input[CONF_API_KEY],
                        verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
                    )
                    if is_valid:
                        current_id = entry.data.get(CONF_CONSOLE_ID) or entry.unique_id
                        # Only a discovered hardware MAC may replace the stored
                        # identity. Device inspection swallows transient errors
                        # and then falls back to a site id or the host, and
                        # that fallback would otherwise overwrite a real MAC
                        # permanently: setup only backfills when console_id is
                        # falsy, and the ":"-based mismatch guard below can
                        # never fire again once the id stops looking like a MAC.
                        new_id = (
                            console_info.get("mac")
                            or current_id
                            or console_info.get("id")
                        )
                        if (
                            new_id
                            and current_id
                            and ":" in new_id
                            and ":" in current_id
                            and new_id != current_id
                        ):
                            return self.async_abort(reason="account_mismatch")

                        # The guard above only fires when both ids look like
                        # MACs, so a legacy entry still keyed on a site id or
                        # host slips past it. Setup and the migration both
                        # check for an existing owner before claiming a
                        # unique_id; async_update_reload_and_abort does not,
                        # and Home Assistant will happily let two entries
                        # share one.
                        if new_id and new_id != entry.unique_id:
                            entries = self.hass.config_entries
                            owner = entries.async_entry_for_domain_unique_id(
                                DOMAIN, new_id
                            )
                            if owner and owner.entry_id != entry.entry_id:
                                return self.async_abort(reason="already_configured")

                        new_data = {
                            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_API_KEY: user_input[CONF_API_KEY],
                            CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, False),
                        }
                        if new_id:
                            new_data[CONF_CONSOLE_ID] = new_id

                        return self.async_update_reload_and_abort(
                            entry,
                            data=new_data,
                            unique_id=new_id or entry.unique_id,
                            reason="reconfigure_successful",
                        )
                    if error_code == "invalid_auth":
                        errors[CONF_API_KEY] = "invalid_auth"
                    else:
                        errors["base"] = error_code or "cannot_connect"
                else:
                    api_key = user_input[CONF_API_KEY].strip()
                    discovered_consoles = await self._async_discover_remote_consoles(
                        api_key
                    )
                    if not discovered_consoles:
                        errors["base"] = "no_remote_consoles"
                    else:
                        console_id = self._normalize_remote_console_id(
                            user_input[CONF_CONSOLE_ID],
                            discovered_consoles,
                        )
                        if console_id is None:
                            errors[CONF_CONSOLE_ID] = "invalid_console_id"
                        else:
                            try:
                                sites_found = await self._async_validate_remote_console(
                                    api_key,
                                    console_id,
                                )
                                if sites_found:
                                    if (
                                        console_id != entry.data.get(CONF_CONSOLE_ID)
                                        and entry.unique_id
                                        != entry.data.get(CONF_API_KEY)
                                        and entry.unique_id != console_id
                                    ):
                                        return self.async_abort(
                                            reason="account_mismatch"
                                        )

                                    new_data = {
                                        CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE,
                                        CONF_CONSOLE_ID: console_id,
                                        CONF_API_KEY: api_key,
                                    }
                                    return self.async_update_reload_and_abort(
                                        entry,
                                        data=new_data,
                                        unique_id=console_id,
                                        reason="reconfigure_successful",
                                    )
                                errors[CONF_CONSOLE_ID] = "invalid_console_id"
                            except UniFiAuthenticationError:
                                errors[CONF_CONSOLE_ID] = "invalid_console_id"

            except UniFiAuthenticationError:
                errors[CONF_API_KEY] = "invalid_auth"
            except UniFiConnectionError:
                errors["base"] = "cannot_connect"
            except UniFiTimeoutError:
                errors["base"] = "cannot_connect"
            except UniFiNotFoundError:
                _LOGGER.exception(
                    "UniFi controller returned 404 during reconfiguration. "
                    "The controller may not expose the Network Integration "
                    "API."
                )
                errors["base"] = "api_unsupported"
            except UniFiResponseError as err:
                if is_transient_error(err):
                    _LOGGER.warning("UniFi API temporarily unavailable: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.exception("Unexpected UniFi API response")
                    errors["base"] = "unknown"
            except ValidationError:
                _LOGGER.exception("Failed to parse site data during reconfiguration")
                errors["base"] = "site_parse_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reconfiguration")
                errors["base"] = "unknown"

        # Show form based on connection type
        if connection_type == CONNECTION_TYPE_LOCAL:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_HOST,
                            default=entry.data.get(CONF_HOST, DEFAULT_API_HOST),
                        ): str,
                        vol.Required(
                            CONF_API_KEY,
                        ): str,
                        vol.Optional(
                            CONF_VERIFY_SSL,
                            default=entry.data.get(CONF_VERIFY_SSL, False),
                        ): bool,
                    }
                ),
                errors=errors,
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONSOLE_ID, default=entry.data.get(CONF_CONSOLE_ID, "")
                    ): str,
                    vol.Required(
                        CONF_API_KEY,
                    ): str,
                }
            ),
            errors=errors,
        )


class UnifiInsightsOptionsFlow(OptionsFlow):
    """Handle options for UniFi Insights integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if (
            self.config_entry.data.get(CONF_CONNECTION_TYPE)
            == CONNECTION_TYPE_CARRIER_FABRIC
        ):
            if user_input is not None:
                return self.async_create_entry(title="", data=user_input)

            default_track_subscribers = self.config_entry.options.get(
                CONF_TRACK_SUBSCRIBERS, DEFAULT_TRACK_SUBSCRIBERS
            )
            default_carrier_actions = self.config_entry.options.get(
                CONF_CARRIER_ACTIONS, DEFAULT_CARRIER_ACTIONS
            )
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_TRACK_SUBSCRIBERS,
                            default=default_track_subscribers,
                        ): bool,
                        vol.Optional(
                            CONF_CARRIER_ACTIONS,
                            default=default_carrier_actions,
                        ): bool,
                    }
                ),
            )

        available_sites = self._available_sites()
        current_site_ids: list[str] = list(
            self.config_entry.options.get(CONF_SITE_IDS) or []
        )
        # Sites are only known while the entry is loaded. Offer the picker for
        # multi-site consoles, or whenever a filter is already saved so it can
        # be cleared.
        show_site_picker = bool(available_sites) and (
            len(available_sites) > 1 or bool(current_site_ids)
        )

        if user_input is not None:
            options = dict(user_input)
            if not show_site_picker:
                # The picker was not shown (entry not loaded, or a single-site
                # console), so keep whatever filter was saved before.
                options.pop(CONF_SITE_IDS, None)
                if current_site_ids:
                    options[CONF_SITE_IDS] = current_site_ids
            elif not options.get(CONF_SITE_IDS):
                # No selection means every site; don't store an empty filter.
                options.pop(CONF_SITE_IDS, None)
            return self.async_create_entry(title="", data=options)

        # Get current values, migrating from old CONF_TRACK_CLIENTS if needed
        old_track_clients = self.config_entry.options.get(
            CONF_TRACK_CLIENTS, DEFAULT_TRACK_CLIENTS
        )
        default_wifi = self.config_entry.options.get(
            CONF_TRACK_WIFI_CLIENTS, old_track_clients
        )
        default_wired = self.config_entry.options.get(
            CONF_TRACK_WIRED_CLIENTS, old_track_clients
        )
        default_client_control = self.config_entry.options.get(
            CONF_CLIENT_CONTROL, DEFAULT_CLIENT_CONTROL
        )

        schema: dict[Any, Any] = {
            vol.Optional(
                CONF_TRACK_WIFI_CLIENTS,
                default=default_wifi,
            ): bool,
            vol.Optional(
                CONF_TRACK_WIRED_CLIENTS,
                default=default_wired,
            ): bool,
            vol.Optional(
                CONF_CLIENT_CONTROL,
                default=default_client_control,
            ): bool,
        }
        if show_site_picker:
            site_options = [
                SelectOptionDict(value=site_id, label=name)
                for site_id, name in available_sites.items()
            ]
            # Keep a saved site that has since vanished visible, so it can be
            # deselected rather than silently lingering in the stored filter.
            site_options.extend(
                SelectOptionDict(value=site_id, label=site_id)
                for site_id in current_site_ids
                if site_id not in available_sites
            )
            # Suggested value, not a default: a default would be re-applied
            # when the field is submitted empty, so the filter could never
            # be cleared.
            schema[vol.Optional(CONF_SITE_IDS)] = SelectSelector(
                SelectSelectorConfig(
                    options=site_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(schema), {CONF_SITE_IDS: current_site_ids}
            ),
        )

    def _available_sites(self) -> dict[str, str]:
        """Return the console's sites (id -> name) when the entry is loaded."""
        runtime_data = getattr(self.config_entry, "runtime_data", None)
        config_coordinator = getattr(runtime_data, "config_coordinator", None)
        sites = getattr(config_coordinator, "available_sites", None)
        return dict(sites) if isinstance(sites, dict) else {}
