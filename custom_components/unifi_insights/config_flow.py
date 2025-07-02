"""Config flow for UniFi Insights integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

from .unifi_network_api import (
    UnifiInsightsClient,
    UnifiInsightsAuthError,
    UnifiInsightsConnectionError,
)
from .unifi_protect_api import UnifiProtectClient
from .const import DEFAULT_API_HOST, DOMAIN, CONF_ENABLE_NETWORK, CONF_ENABLE_PROTECT

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Insights."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                api = UnifiInsightsClient(
                    hass=self.hass,
                    api_key=user_input[CONF_API_KEY],
                    host=user_input.get(CONF_HOST, DEFAULT_API_HOST),
                    verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
                )

                # Validate the API key
                if await api.async_validate_api_key():
                    await self.async_set_unique_id(user_input[CONF_API_KEY])
                    self._abort_if_unique_id_configured()

                    # Automatically detect which UniFi applications are available
                    connection_data = {
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_HOST: user_input.get(CONF_HOST, DEFAULT_API_HOST),
                        CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, False),
                    }

                    # Detect available applications
                    (
                        network_available,
                        protect_available,
                    ) = await self._detect_applications(connection_data)

                    # Ensure at least one application is available
                    if not network_available and not protect_available:
                        errors["base"] = "no_devices_found"
                    else:
                        # Create entry with detected applications
                        final_data = {
                            **connection_data,
                            CONF_ENABLE_NETWORK: network_available,
                            CONF_ENABLE_PROTECT: protect_available,
                        }

                        return self.async_create_entry(
                            title="UniFi Insights",
                            data=final_data,
                        )

                errors[CONF_API_KEY] = "invalid_auth"

            except UnifiInsightsAuthError:
                errors[CONF_API_KEY] = "invalid_auth"
            except UnifiInsightsConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_HOST, default=DEFAULT_API_HOST): str,
                    vol.Optional(CONF_VERIFY_SSL, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def _detect_applications(
        self, connection_data: dict[str, Any]
    ) -> tuple[bool, bool]:
        """Detect which UniFi applications are available by checking for devices."""
        network_available = False
        protect_available = False

        # Test UniFi Network API
        try:
            network_api = UnifiInsightsClient(
                hass=self.hass,
                api_key=connection_data[CONF_API_KEY],
                host=connection_data[CONF_HOST],
                verify_ssl=connection_data[CONF_VERIFY_SSL],
            )

            # Try to get sites and devices
            sites = await network_api.async_get_sites()
            if sites:
                # Check if any site has devices
                for site in sites:
                    try:
                        devices = await network_api.async_get_devices(site["id"])
                        if devices:
                            network_available = True
                            _LOGGER.debug(
                                "UniFi Network devices found: %d devices in site %s",
                                len(devices),
                                site["id"],
                            )
                            break
                    except Exception as err:
                        _LOGGER.debug(
                            "Error checking devices for site %s: %s", site["id"], err
                        )
                        continue

        except Exception as err:
            _LOGGER.debug("UniFi Network API not available: %s", err)

        # Test UniFi Protect API
        try:
            protect_api = UnifiProtectClient(
                hass=self.hass,
                api_key=connection_data[CONF_API_KEY],
                host=connection_data[CONF_HOST],
                verify_ssl=connection_data[CONF_VERIFY_SSL],
            )

            # Try to get cameras (most common Protect device)
            cameras = await protect_api.async_get_cameras()
            if cameras:
                protect_available = True
                _LOGGER.debug("UniFi Protect devices found: %d cameras", len(cameras))
            else:
                # Also check for other Protect devices
                try:
                    lights = await protect_api.async_get_lights()
                    sensors = await protect_api.async_get_sensors()
                    chimes = await protect_api.async_get_chimes()
                    if lights or sensors or chimes:
                        protect_available = True
                        _LOGGER.debug(
                            "UniFi Protect devices found: %d lights, %d sensors, %d chimes",
                            len(lights or []),
                            len(sensors or []),
                            len(chimes or []),
                        )
                except Exception:
                    pass  # Some devices might not be supported

        except Exception as err:
            _LOGGER.debug("UniFi Protect API not available: %s", err)

        _LOGGER.info(
            "Application detection complete - Network: %s, Protect: %s",
            network_available,
            protect_available,
        )
        return network_available, protect_available

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthorization if the API key becomes invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors = {}

        if user_input is not None:
            try:
                api = UnifiInsightsClient(
                    hass=self.hass,
                    api_key=user_input[CONF_API_KEY],
                    host=self.entry.data.get(CONF_HOST, DEFAULT_API_HOST),
                    verify_ssl=self.entry.data.get(CONF_VERIFY_SSL, False),
                )

                if await api.async_validate_api_key():
                    existing_entry = await self.async_set_unique_id(
                        user_input[CONF_API_KEY]
                    )
                    if existing_entry:
                        self.hass.config_entries.async_update_entry(
                            existing_entry,
                            data={
                                **self.entry.data,
                                CONF_API_KEY: user_input[CONF_API_KEY],
                            },
                        )
                        await self.hass.config_entries.async_reload(
                            existing_entry.entry_id
                        )
                        return self.async_abort(reason="reauth_successful")

            except UnifiInsightsAuthError:
                errors[CONF_API_KEY] = "invalid_auth"
            except UnifiInsightsConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )
