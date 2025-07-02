"""Repairs for UniFi Insights integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .unifi_network_api import (
    UnifiInsightsClient,
    UnifiInsightsAuthError,
    UnifiInsightsConnectionError,
)
from .unifi_protect_api import UnifiProtectClient

_LOGGER = logging.getLogger(__name__)

# Repair issue identifiers
REPAIR_API_KEY_INVALID = "api_key_invalid"
REPAIR_HOST_UNREACHABLE = "host_unreachable"
REPAIR_NO_DEVICES_FOUND = "no_devices_found"
REPAIR_NETWORK_API_FAILED = "network_api_failed"
REPAIR_PROTECT_API_FAILED = "protect_api_failed"
REPAIR_WEBSOCKET_CONNECTION_FAILED = "websocket_connection_failed"
REPAIR_FIRMWARE_OUTDATED = "firmware_outdated"


class UnifiInsightsRepairFlow(RepairsFlow):
    """Handler for UniFi Insights repair flows."""

    def __init__(self, issue_id: str) -> None:
        """Initialize the repair flow."""
        super().__init__()
        self.issue_id = issue_id

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step of the repair flow."""
        if self.issue_id == REPAIR_API_KEY_INVALID:
            return await self.async_step_api_key_invalid(user_input)
        elif self.issue_id == REPAIR_HOST_UNREACHABLE:
            return await self.async_step_host_unreachable(user_input)
        elif self.issue_id == REPAIR_NO_DEVICES_FOUND:
            return await self.async_step_no_devices_found(user_input)
        elif self.issue_id == REPAIR_NETWORK_API_FAILED:
            return await self.async_step_network_api_failed(user_input)
        elif self.issue_id == REPAIR_PROTECT_API_FAILED:
            return await self.async_step_protect_api_failed(user_input)
        elif self.issue_id == REPAIR_WEBSOCKET_CONNECTION_FAILED:
            return await self.async_step_websocket_failed(user_input)
        elif self.issue_id == REPAIR_FIRMWARE_OUTDATED:
            return await self.async_step_firmware_outdated(user_input)

        return self.async_abort(reason="unknown_issue")

    async def async_step_api_key_invalid(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle API key invalid repair."""
        if user_input is not None:
            # Validate the new API key
            config_entry = self._get_config_entry()
            if config_entry:
                try:
                    api = UnifiInsightsClient(
                        hass=self.hass,
                        api_key=user_input[CONF_API_KEY],
                        host=config_entry.data[CONF_HOST],
                        verify_ssl=config_entry.data.get("verify_ssl", False),
                    )

                    if await api.async_validate_api_key():
                        # Update the config entry with the new API key
                        self.hass.config_entries.async_update_entry(
                            config_entry,
                            data={
                                **config_entry.data,
                                CONF_API_KEY: user_input[CONF_API_KEY],
                            },
                        )

                        # Remove the repair issue
                        ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)

                        return self.async_create_entry(
                            title="API Key Updated",
                            data={},
                        )
                    else:
                        return self.async_show_form(
                            step_id="api_key_invalid",
                            data_schema=vol.Schema(
                                {
                                    vol.Required(CONF_API_KEY): str,
                                }
                            ),
                            errors={"api_key": "invalid_auth"},
                            description_placeholders={
                                "host": config_entry.data[CONF_HOST],
                            },
                        )

                except (UnifiInsightsAuthError, UnifiInsightsConnectionError):
                    return self.async_show_form(
                        step_id="api_key_invalid",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_API_KEY): str,
                            }
                        ),
                        errors={"api_key": "cannot_connect"},
                        description_placeholders={
                            "host": config_entry.data[CONF_HOST],
                        },
                    )

        return self.async_show_form(
            step_id="api_key_invalid",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            description_placeholders={
                "host": self._get_config_entry().data[CONF_HOST]
                if self._get_config_entry()
                else "Unknown",
            },
        )

    async def async_step_host_unreachable(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle host unreachable repair."""
        if user_input is not None:
            config_entry = self._get_config_entry()
            if config_entry:
                # Update the config entry with the new host
                self.hass.config_entries.async_update_entry(
                    config_entry,
                    data={**config_entry.data, CONF_HOST: user_input[CONF_HOST]},
                )

                # Remove the repair issue
                ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)

                return self.async_create_entry(
                    title="Host Updated",
                    data={},
                )

        return self.async_show_form(
            step_id="host_unreachable",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="https://192.168.1.1"): str,
                }
            ),
        )

    async def async_step_no_devices_found(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle no devices found repair."""
        return self.async_create_entry(
            title="No Devices Found",
            data={},
        )

    async def async_step_network_api_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Network API failure repair."""
        return self.async_create_entry(
            title="Network API Issue Acknowledged",
            data={},
        )

    async def async_step_protect_api_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Protect API failure repair."""
        return self.async_create_entry(
            title="Protect API Issue Acknowledged",
            data={},
        )

    async def async_step_websocket_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle WebSocket connection failure repair."""
        return self.async_create_entry(
            title="WebSocket Issue Acknowledged",
            data={},
        )

    async def async_step_firmware_outdated(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle firmware outdated repair."""
        return self.async_create_entry(
            title="Firmware Warning Acknowledged",
            data={},
        )

    def _get_config_entry(self) -> ConfigEntry | None:
        """Get the config entry for this domain."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            return entry
        return None


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a fix flow for UniFi Insights issues."""
    return UnifiInsightsRepairFlow(issue_id)


# Repair issue creation functions


async def create_api_key_invalid_issue(
    hass: HomeAssistant, config_entry: ConfigEntry, error_details: str | None = None
) -> None:
    """Create a repair issue for invalid API key."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_API_KEY_INVALID,
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="api_key_invalid",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
            "error": error_details or "API key validation failed",
        },
    )
    _LOGGER.warning(
        "Created repair issue for invalid API key on host %s",
        config_entry.data.get(CONF_HOST),
    )


async def create_host_unreachable_issue(
    hass: HomeAssistant, config_entry: ConfigEntry, error_details: str | None = None
) -> None:
    """Create a repair issue for unreachable host."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_HOST_UNREACHABLE,
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="host_unreachable",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
            "error": error_details or "Host is unreachable",
        },
    )
    _LOGGER.warning(
        "Created repair issue for unreachable host %s",
        config_entry.data.get(CONF_HOST),
    )


async def create_no_devices_found_issue(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Create a repair issue for no devices found."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_NO_DEVICES_FOUND,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="no_devices_found",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
        },
    )
    _LOGGER.info(
        "Created repair issue for no devices found on host %s",
        config_entry.data.get(CONF_HOST),
    )


async def create_network_api_failed_issue(
    hass: HomeAssistant, config_entry: ConfigEntry, error_details: str | None = None
) -> None:
    """Create a repair issue for Network API failure."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_NETWORK_API_FAILED,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="network_api_failed",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
            "error": error_details or "Network API connection failed",
        },
    )
    _LOGGER.warning(
        "Created repair issue for Network API failure on host %s: %s",
        config_entry.data.get(CONF_HOST),
        error_details,
    )


async def create_protect_api_failed_issue(
    hass: HomeAssistant, config_entry: ConfigEntry, error_details: str | None = None
) -> None:
    """Create a repair issue for Protect API failure."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_PROTECT_API_FAILED,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="protect_api_failed",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
            "error": error_details or "Protect API connection failed",
        },
    )
    _LOGGER.warning(
        "Created repair issue for Protect API failure on host %s: %s",
        config_entry.data.get(CONF_HOST),
        error_details,
    )


async def create_websocket_connection_failed_issue(
    hass: HomeAssistant, config_entry: ConfigEntry, error_details: str | None = None
) -> None:
    """Create a repair issue for WebSocket connection failure."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REPAIR_WEBSOCKET_CONNECTION_FAILED,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="websocket_connection_failed",
        translation_placeholders={
            "host": config_entry.data.get(CONF_HOST, "Unknown"),
            "error": error_details or "WebSocket connection failed",
        },
    )
    _LOGGER.info(
        "Created repair issue for WebSocket failure on host %s: %s",
        config_entry.data.get(CONF_HOST),
        error_details,
    )


async def create_firmware_outdated_issue(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_name: str,
    current_version: str,
    recommended_version: str | None = None,
) -> None:
    """Create a repair issue for outdated firmware."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{REPAIR_FIRMWARE_OUTDATED}_{device_name.lower().replace(' ', '_')}",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="firmware_outdated",
        translation_placeholders={
            "device_name": device_name,
            "current_version": current_version,
            "recommended_version": recommended_version or "latest",
        },
    )
    _LOGGER.info(
        "Created repair issue for outdated firmware on device %s (version %s)",
        device_name,
        current_version,
    )


# Repair issue cleanup functions


async def clear_repair_issues(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Clear all repair issues for a config entry."""
    issues_to_clear = [
        REPAIR_API_KEY_INVALID,
        REPAIR_HOST_UNREACHABLE,
        REPAIR_NO_DEVICES_FOUND,
        REPAIR_NETWORK_API_FAILED,
        REPAIR_PROTECT_API_FAILED,
        REPAIR_WEBSOCKET_CONNECTION_FAILED,
    ]

    for issue_id in issues_to_clear:
        ir.async_delete_issue(hass, DOMAIN, issue_id)

    # Clear firmware issues (they have dynamic IDs)
    registry = ir.async_get(hass)
    for issue in registry.issues.values():
        if issue.domain == DOMAIN and issue.issue_id.startswith(
            REPAIR_FIRMWARE_OUTDATED
        ):
            ir.async_delete_issue(hass, DOMAIN, issue.issue_id)

    _LOGGER.debug("Cleared all repair issues for UniFi Insights integration")
