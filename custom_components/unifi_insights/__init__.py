"""The UniFi Insights integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL, Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ApiKeyAuth,
    ConnectionType,
    LocalAuth,
    UniFiConnectionError,
    UniFiTimeoutError,
)
from .api.network import UniFiNetworkClient
from .api.protect import UniFiProtectClient
from .console_identity import (
    first_non_default_site_id,
    is_console_device,
    normalize_mac,
    resolve_console_identity,
)
from .const import (
    CONF_CONNECTION_TYPE,
    CONF_CONSOLE_ID,
    CONF_CONSOLE_NAME,
    CONNECTION_TYPE_LOCAL,
    DEFAULT_API_HOST,
    DOMAIN,
)
from .const import (
    CONNECTION_TYPE_REMOTE as CONNECTION_TYPE_REMOTE,
)
from .coordinators import (
    UnifiConfigCoordinator,
    UnifiDeviceCoordinator,
    UnifiFacadeCoordinator,
    UnifiProtectCoordinator,
)
from .probe import (
    ProbeResult,
    ProbeStatus,
    async_probe_network,
    async_probe_protect,
)
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry


@dataclass
class UnifiInsightsData:
    """Runtime data for UniFi Insights integration (Platinum multi-coordinator)."""

    config_coordinator: UnifiConfigCoordinator
    device_coordinator: UnifiDeviceCoordinator
    protect_coordinator: UnifiProtectCoordinator | None
    network_client: UniFiNetworkClient
    protect_client: UniFiProtectClient | None
    # Facade coordinator for backward compatibility with entity classes
    _facade_coordinator: UnifiFacadeCoordinator | None = None

    @property
    def coordinator(self) -> UnifiFacadeCoordinator:
        """
        Return facade coordinator for backward compatibility.

        This property provides a unified view combining data from all
        specialized coordinators, ensuring existing entity classes
        continue to work without modifications.
        """
        if self._facade_coordinator is None:
            msg = "Facade coordinator not initialized"
            raise RuntimeError(msg)
        return self._facade_coordinator


# Use TypeAlias for proper mypy validation (Python 3.10+ style)
UnifiInsightsConfigEntry: TypeAlias = ConfigEntry[UnifiInsightsData]  # noqa: UP040

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.DEVICE_TRACKER,
    Platform.EVENT,
    Platform.IMAGE,
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.UPDATE,
]

# Add CONFIG_SCHEMA definition
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:  # noqa: ARG001
    """Set up the UniFi Insights component."""
    # Register service actions at component setup so they are available (and
    # validatable) even when no config entry is loaded (Quality Scale:
    # action-setup).
    await async_setup_services(hass)
    return True


# Setup attempts to retry before falling back when the probes are not
# conclusive (see _raise_for_setup_probes). Home Assistant waits 5 s, 10 s,
# then 20 s between attempts (doubling, capped), so the budget lasts at least
# ~35 s from the first incomplete answer, longer if earlier retries while the
# console was unreachable have already raised the backoff.
SETUP_PROBE_RETRIES = 3
_SETUP_PROBE_ATTEMPTS = "setup_probe_attempts"
# One application usable while the other is temporarily unreachable.
_PARTIAL = "partial"
# Nothing usable and nothing more specific than "absent" or "empty".
_INCONCLUSIVE = "inconclusive"


def _clear_setup_probe_attempts(hass: HomeAssistant, entry_id: str) -> None:
    """Forget an entry's setup retry budget."""
    hass.data.get(DOMAIN, {}).get(_SETUP_PROBE_ATTEMPTS, {}).pop(entry_id, None)


def _raise_for_setup_probes(
    hass: HomeAssistant,
    entry_id: str,
    network_probe: ProbeResult,
    protect_probe: ProbeResult,
) -> None:
    """
    Decide from the Network and Protect probes whether setup can continue.

    - Neither application usable and one temporarily unreachable (connection,
      timeout, 408, 429, 5xx): retry setup for as long as that lasts. These
      retries don't use up either budget below, so a console that was
      unreachable while rebooting still gets them once it answers.
    - One usable and the other temporarily unreachable: retry up to
      SETUP_PROBE_RETRIES times, so a console still starting doesn't silently
      lose that application, then load without it rather than keeping the
      working one offline too.
    - Neither usable and a key rejected (401/403): reauth.
    - Neither usable and nothing more specific (no sites, no NVR, no supported
      application, an unparseable response): retry up to SETUP_PROBE_RETRIES
      times - applications still starting answer this way - then reauth as
      before.
    Each budget is counted separately per entry and cleared when the entry
    loads, reauth starts, or the entry is unloaded or removed. Network-only
    consoles (Protect absent), Protect-only consoles (Network absent or
    rejecting the key) and camera-free NVRs load immediately.
    """
    budgets: dict[str, int] = (
        hass.data.setdefault(DOMAIN, {})
        .setdefault(_SETUP_PROBE_ATTEMPTS, {})
        .setdefault(entry_id, {})
    )
    probes = {"Network": network_probe, "Protect": protect_probe}
    available = [
        name for name, probe in probes.items() if probe.status is ProbeStatus.AVAILABLE
    ]
    unreachable = [
        (name, probe.error)
        for name, probe in probes.items()
        if probe.status is ProbeStatus.UNREACHABLE
    ]

    def retry(msg: str, err: Exception | None, budget: str | None) -> None:
        if budget is not None:
            budgets[budget] = budgets.get(budget, 0) + 1
        _LOGGER.warning(msg)
        raise ConfigEntryNotReady(msg) from err

    def budget_left(budget: str) -> bool:
        return budgets.get(budget, 0) < SETUP_PROBE_RETRIES

    if unreachable and not available:
        name, err = unreachable[0]
        retry(f"Error communicating with UniFi {name} API: {err}", err, None)

    if unreachable and budget_left(_PARTIAL):
        name, err = unreachable[0]
        retry(f"UniFi {name} API is temporarily unavailable: {err}", err, _PARTIAL)

    if available:
        _clear_setup_probe_attempts(hass, entry_id)
        for name, probe in probes.items():
            if probe.status in (
                ProbeStatus.UNREACHABLE,
                ProbeStatus.AUTH_FAILED,
                ProbeStatus.ERROR,
            ):
                _LOGGER.warning(
                    "UniFi %s API could not be validated (%s), continuing "
                    "without %s support: %s",
                    name,
                    probe.status,
                    name,
                    probe.error,
                )
        return

    if any(probe.status is ProbeStatus.AUTH_FAILED for probe in probes.values()):
        _clear_setup_probe_attempts(hass, entry_id)
        msg = "Invalid API key or unable to connect to UniFi API"
        _LOGGER.warning(msg)
        raise ConfigEntryAuthFailed(msg)

    if budget_left(_INCONCLUSIVE):
        retry(
            "No Network sites or Protect NVR found on console yet, retrying in "
            "case it is still starting",
            network_probe.error or protect_probe.error,
            _INCONCLUSIVE,
        )

    _clear_setup_probe_attempts(hass, entry_id)
    msg = "No Network sites or Protect NVR found on console"
    _LOGGER.error(msg)
    raise ConfigEntryAuthFailed(msg)


# Re-exported under its original private name: the config flow and this module
# must agree on what a console is, so the definition lives in one place now.
_is_console_device = is_console_device


def _first_site_id(config_coordinator: UnifiConfigCoordinator) -> str | None:
    """Return a stable site id to identify a console that exposes no gateway."""
    data = getattr(config_coordinator, "data", None)
    if not isinstance(data, dict):
        return None
    sites = data.get("sites")
    if not isinstance(sites, dict):
        return None
    # dict order is the API's site order, which is what the flow sees too.
    return first_non_default_site_id(sites)


async def async_setup_entry(
    hass: HomeAssistant, entry: UnifiInsightsConfigEntry
) -> bool:
    """Set up UniFi Insights from a config entry."""
    _LOGGER.info("Setting up UniFi Insights integration")

    # Determine connection type (default to local for backward compatibility)
    connection_type = entry.data.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_LOCAL)
    is_local = connection_type == CONNECTION_TYPE_LOCAL

    # Get Home Assistant's aiohttp session for efficient connection pooling
    # (Platinum requirement)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False) if is_local else True
    websession = async_get_clientsession(hass, verify_ssl=verify_ssl)

    try:
        if is_local:
            _LOGGER.debug(
                "Initializing UniFi API clients (LOCAL) with host: %s",
                entry.data.get(CONF_HOST, DEFAULT_API_HOST),
            )

            # Create authentication object for local connection
            auth: LocalAuth | ApiKeyAuth = LocalAuth(
                api_key=entry.data[CONF_API_KEY],
                verify_ssl=verify_ssl,
            )

            # Initialize UniFi Network API client with injected websession
            network_client = UniFiNetworkClient(
                auth=auth,
                base_url=entry.data.get(CONF_HOST, DEFAULT_API_HOST),
                connection_type=ConnectionType.LOCAL,
                timeout=30,
                session=websession,
            )
        else:
            _LOGGER.debug(
                "Initializing UniFi API clients (REMOTE) with console_id: %s",
                entry.data.get(CONF_CONSOLE_ID),
            )

            # Create authentication object for remote connection
            auth = ApiKeyAuth(api_key=entry.data[CONF_API_KEY])

            # Initialize UniFi Network API client for remote connection
            network_client = UniFiNetworkClient(
                auth=auth,
                connection_type=ConnectionType.REMOTE,
                console_id=entry.data.get(CONF_CONSOLE_ID),
                timeout=30,
                session=websession,
            )

        # Initialize UniFi Protect API client
        if is_local:
            _LOGGER.debug("Initializing UniFi Protect API client (LOCAL)")
            protect_api = UniFiProtectClient(
                auth=auth,
                base_url=entry.data.get(CONF_HOST, DEFAULT_API_HOST),
                connection_type=ConnectionType.LOCAL,
                timeout=30,
                session=websession,
            )
        else:
            _LOGGER.debug("Initializing UniFi Protect API client (REMOTE)")
            protect_api = UniFiProtectClient(
                auth=auth,
                connection_type=ConnectionType.REMOTE,
                console_id=entry.data.get(CONF_CONSOLE_ID),
                timeout=30,
                session=websession,
            )

        # Probe both applications. Each result says whether the application
        # is usable, absent, rejecting the key, or temporarily unreachable.
        _LOGGER.debug("Validating Network and Protect API connections")
        network_probe = await async_probe_network(network_client)
        protect_probe = await async_probe_protect(protect_api)
        network_available = network_probe.status is ProbeStatus.AVAILABLE
        protect_available = protect_probe.status is ProbeStatus.AVAILABLE
        sites = network_probe.sites
        if network_available:
            _LOGGER.info(
                "Network API validated successfully, found %d sites", len(sites)
            )
        protect_client: UniFiProtectClient | None = None
        if protect_available:
            _LOGGER.info("UniFi Protect API validated successfully")
            protect_client = protect_api

        _raise_for_setup_probes(hass, entry.entry_id, network_probe, protect_probe)

    # Probe failures are classified in _raise_for_setup_probes; these catch
    # anything raised while building the clients.
    except UniFiConnectionError as err:
        _LOGGER.warning("Connection error: %s", err)
        msg = f"Error communicating with UniFi API: {err}"
        raise ConfigEntryNotReady(msg) from err
    except UniFiTimeoutError as err:
        _LOGGER.warning("Timeout error: %s", err)
        msg = f"Timeout connecting to UniFi API: {err}"
        raise ConfigEntryNotReady(msg) from err

    # Create multi-coordinator architecture (Platinum compliance)
    _LOGGER.debug("Creating multi-coordinator architecture")

    # 1. Config coordinator - slow updates (5 minutes) for sites, WiFi
    config_coordinator = UnifiConfigCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=protect_client,
        entry=entry,
        network_available=network_available,
    )

    # 2. Device coordinator - fast updates (30 seconds) for devices, stats
    device_coordinator = UnifiDeviceCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=protect_client,
        entry=entry,
        config_coordinator=config_coordinator,
    )

    # 3. Protect coordinator - fast updates (30 seconds) + WebSocket for events
    # WebSocket site_id: LOCAL consoles ignore site_id for the Protect REST/WS
    # paths, so "default" is fine. REMOTE (cloud connector) routing uses the
    # console_id embedded in the path, but if the Network API returned sites
    # for this console, prefer the first real site id over the placeholder.
    protect_site_id = "default"
    if not is_local and network_available and sites and sites[0].id:
        protect_site_id = sites[0].id

    protect_coordinator: UnifiProtectCoordinator | None = None
    if protect_client:
        protect_coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=entry,
            site_id=protect_site_id,
        )

    # Fetch initial data - config first, then device/protect in parallel
    _LOGGER.debug("Fetching initial data from coordinators")
    await config_coordinator.async_config_entry_first_refresh()

    # Device coordinator needs sites from config coordinator
    refresh_tasks = [device_coordinator.async_config_entry_first_refresh()]
    if protect_coordinator:
        refresh_tasks.append(protect_coordinator.async_config_entry_first_refresh())
    await asyncio.gather(*refresh_tasks)

    # Discover and update console identity if needed (backward compatibility)
    console_id = entry.data.get(CONF_CONSOLE_ID)
    console_name = entry.data.get(CONF_CONSOLE_NAME)
    console_mac: str | None = None

    if protect_coordinator and protect_coordinator.data:
        nvrs = protect_coordinator.data.get("nvrs", {})
        if isinstance(nvrs, dict) and nvrs:
            first_nvr = next(iter(nvrs.values()), None)
            if isinstance(first_nvr, dict):
                console_mac = normalize_mac(first_nvr.get("mac"))
                if not console_name:
                    console_name = first_nvr.get("name")

    if not console_mac and device_coordinator and device_coordinator.data:
        devices_by_site = device_coordinator.data.get("devices", {})
        if isinstance(devices_by_site, dict):
            console_mac, found_name = resolve_console_identity(
                dev_data
                for site_devices in devices_by_site.values()
                if isinstance(site_devices, dict)
                for dev_data in site_devices.values()
            )
            if not console_name:
                console_name = found_name

    if is_local and (not console_id or console_id == entry.data.get(CONF_API_KEY)):
        if console_mac:
            console_id = console_mac
        elif not console_id:
            # The host is an address, not an identity: it changes on a DHCP
            # renew, which is the problem this separation exists to fix. Fall
            # back to the site id first and keep the host as a last resort,
            # matching the order the config flow already uses.
            console_id = (
                _first_site_id(config_coordinator)
                or entry.data.get(CONF_HOST, "local").lower()
            )

    updates: dict[str, Any] = {}
    new_data = dict(entry.data)
    if console_id and new_data.get(CONF_CONSOLE_ID) != console_id:
        new_data[CONF_CONSOLE_ID] = console_id
        updates["data"] = new_data
    if console_name and new_data.get(CONF_CONSOLE_NAME) != console_name:
        new_data[CONF_CONSOLE_NAME] = console_name
        updates["data"] = new_data

    target_unique_id = console_id or entry.unique_id
    if target_unique_id and target_unique_id != entry.unique_id:
        existing_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, target_unique_id
        )
        if not existing_entry or existing_entry.entry_id == entry.entry_id:
            updates["unique_id"] = target_unique_id

    if console_name and entry.title in (
        "UniFi Insights (Local)",
        "UniFi Insights (Cloud)",
    ):
        updates["title"] = f"UniFi - {console_name}"

    if updates:
        hass.config_entries.async_update_entry(entry, **updates)

    # Start the real-time Protect WebSocket subscription (additive to the
    # 30s poll above, which stays as the fallback - see
    # UnifiProtectCoordinator.async_start_websocket). Registered for
    # on-unload cleanup immediately so a setup failure later in this
    # function (e.g. platform forwarding below) can't leak the background
    # task - HA still runs async_on_unload callbacks when setup fails.
    if protect_coordinator:
        await protect_coordinator.async_start_websocket()
        entry.async_on_unload(protect_coordinator.async_stop_websocket)

    # Create facade coordinator for backward compatibility with entity classes
    # (it aggregates the initial data from the sub-coordinators on creation)
    _LOGGER.debug("Creating facade coordinator for backward compatibility")
    facade_coordinator = UnifiFacadeCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=protect_client,
        entry=entry,
        config_coordinator=config_coordinator,
        device_coordinator=device_coordinator,
        protect_coordinator=protect_coordinator,
    )

    # Store runtime data in config entry (Gold requirement)
    entry.runtime_data = UnifiInsightsData(
        config_coordinator=config_coordinator,
        device_coordinator=device_coordinator,
        protect_coordinator=protect_coordinator,
        network_client=network_client,
        protect_client=protect_client,
        _facade_coordinator=facade_coordinator,
    )

    # Set up platforms
    _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when its updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("UniFi Insights integration setup completed successfully")
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: UnifiInsightsConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading UniFi Insights config entry")
    _clear_setup_probe_attempts(hass, entry.entry_id)

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Only tear down the API clients once the platforms are gone; closing them
    # first would leave loaded entities behind with dead clients if a platform
    # failed to unload.
    if unload_ok and hasattr(entry, "runtime_data") and entry.runtime_data:
        data = entry.runtime_data
        _LOGGER.debug("Closing API clients")
        if data.protect_client:
            # Stop the WebSocket (and await its background task) *before*
            # closing the client below - stopping it after would leave the
            # loop trying to use an already-closed session for whatever
            # brief window passes before entry.async_on_unload's registered
            # copy of this same call runs (see async_setup_entry - that
            # registration is the safety net for a setup failure that
            # happens after the WebSocket starts but before this function
            # ever runs; async_stop_websocket() is idempotent so running it
            # twice on a normal unload is harmless).
            if data.protect_coordinator:
                await data.protect_coordinator.async_stop_websocket()
            # Close Protect client (await the async close)
            try:
                await data.protect_client.close()
            except Exception as err:
                _LOGGER.debug("Error closing Protect client: %s", err)

        # Close Network client (await the async close)
        if data.network_client:
            try:
                await data.network_client.close()
            except Exception as err:
                _LOGGER.debug("Error closing Network client: %s", err)

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnifiInsightsConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """
    Allow deleting a device that belongs to a site no longer being polled.

    Deselecting a site in options stops it being polled, so its devices can
    never come back and would otherwise sit unavailable with no way to remove
    them. Everything else is refused: devices of polled sites are live, and
    Protect, client and WiFi devices are not site-scoped.
    """
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is None:
        return False

    config_coordinator = runtime_data.config_coordinator
    deselected = set(config_coordinator.available_sites) - set(
        config_coordinator.get_site_ids()
    )
    return any(
        domain == DOMAIN
        and any(
            _is_site_scoped_identifier(identifier, site_id) for site_id in deselected
        )
        for domain, identifier in device_entry.identifiers
    )


def _is_site_scoped_identifier(identifier: str, site_id: str) -> bool:
    """
    Return True if a device identifier belongs to the given site.

    Only the exact formats built for site-scoped devices match: network
    devices (``{site}_{device}``), the per-site firewall, route and VPN
    devices, and the ``site_{site}`` device that holds a gateway-less site's
    client count. A loose suffix check would also match a Protect or WiFi id that
    merely ends in the site id.
    """
    return identifier.startswith(f"{site_id}_") or identifier in {
        f"firewall_policies_{site_id}",
        f"policy_based_routes_{site_id}",
        f"vpn_clients_{site_id}",
        f"site_{site_id}",
    }


async def async_remove_entry(
    hass: HomeAssistant, entry: UnifiInsightsConfigEntry
) -> None:
    """Forget per-entry setup state when an entry is deleted."""
    _clear_setup_probe_attempts(hass, entry.entry_id)


async def async_reload_entry(
    hass: HomeAssistant, entry: UnifiInsightsConfigEntry
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry to separate console identity from transport credentials."""
    _LOGGER.debug(
        "Migrating entry %s from version %s.%s",
        config_entry.entry_id,
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 1:
        # Cannot downgrade from higher major version
        return False

    if config_entry.version == 1:
        new_data = dict(config_entry.data)
        new_unique_id = config_entry.unique_id

        # Remote migration: ensure unique_id is the console_id
        if (
            new_data.get(CONF_CONNECTION_TYPE) == CONNECTION_TYPE_REMOTE
            or new_data.get(CONF_CONNECTION_TYPE) == CONNECTION_TYPE_LOCAL
        ):
            console_id = new_data.get(CONF_CONSOLE_ID)
            if console_id and new_unique_id != console_id:
                existing = hass.config_entries.async_entry_for_domain_unique_id(
                    DOMAIN, console_id
                )
                if not existing or existing.entry_id == config_entry.entry_id:
                    new_unique_id = console_id

        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            unique_id=new_unique_id,
            version=1,
            minor_version=2,
        )

    _LOGGER.info(
        "Migration of entry %s to version %s.%s successful",
        config_entry.entry_id,
        config_entry.version,
        config_entry.minor_version,
    )
    return True
