# Copyright 2026 UniFi Insights contributors
"""Tests for setting up UniFi Mobility on remote config entries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights import async_remove_config_entry_device
from custom_components.unifi_insights.api import UniFiAuthenticationError
from custom_components.unifi_insights.const import DOMAIN
from tests.fixtures.mobility_responses import (
    OFFICE_ROUTER_ID,
    WORKSPACE_ID,
    mobility_client_mock,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant

pytestmark = pytest.mark.usefixtures(
    "mock_network_client",
    "mock_protect_client",
    "enable_custom_integrations",
    "site_manager_client",
)


@pytest.fixture
def site_manager_client() -> Generator[MagicMock]:
    """Keep the account-wide Site Manager poller off the network."""
    with patch(
        "custom_components.unifi_insights.coordinators.site_manager."
        "UniFiSiteManagerClient"
    ) as client_class:
        client = client_class.return_value
        for method in (
            "list_hosts",
            "list_sites",
            "list_devices",
            "get_isp_metrics",
            "list_sd_wan_configs",
        ):
            setattr(client, method, AsyncMock(return_value=[]))
        client.close = AsyncMock()
        yield client


def _remote_entry(entry_id: str, console_id: str = "console") -> MockConfigEntry:
    """Return a remote (cloud) entry using the shared test API key."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "connection_type": "remote",
            "console_id": console_id,
            "api_key": "cloud-key",
        },
        unique_id=console_id,
        entry_id=entry_id,
    )


def _serve_spec_examples(client: MagicMock) -> None:
    """Make the autouse Mobility client mock answer with the spec examples."""
    examples = mobility_client_mock()
    client.list_workspaces = examples.list_workspaces
    client.list_devices = examples.list_devices
    client.get_device = examples.get_device


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up an entry and wait for its background Mobility refresh."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_key_without_mobility_scope_loads_without_reauth(
    hass: HomeAssistant, mock_mobility_client: MagicMock
) -> None:
    """A 403 from Mobility leaves the remote entry working and asks nothing."""
    mock_mobility_client.list_workspaces.side_effect = UniFiAuthenticationError(
        "Access forbidden", status_code=403
    )
    entry = _remote_entry("01REMOTE")

    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    coordinator = entry.runtime_data.mobility_coordinator
    assert coordinator is not None
    assert coordinator.data["access"] == "denied"
    assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    mock_mobility_client.close.assert_awaited_once()


async def test_local_entry_never_uses_mobility(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_mobility_client: MagicMock,
) -> None:
    """Console-local keys cannot reach the cloud Mobility API."""
    await hass.async_block_till_done(wait_background_tasks=True)

    assert init_integration.runtime_data.mobility_coordinator is None
    mock_mobility_client.list_workspaces.assert_not_awaited()


async def test_only_one_remote_entry_per_key_polls_mobility(
    hass: HomeAssistant, mock_mobility_client: MagicMock
) -> None:
    """Two consoles behind one cloud key share a single Mobility poller."""
    _serve_spec_examples(mock_mobility_client)
    owner = _remote_entry("01A", "console-a")
    second = _remote_entry("01B", "console-b")
    second.add_to_hass(hass)

    # Setting up the integration loads every entry of the domain.
    await _setup(hass, owner)

    assert second.state is ConfigEntryState.LOADED
    assert owner.runtime_data.mobility_coordinator is not None
    assert second.runtime_data.mobility_coordinator is None
    mock_mobility_client.list_workspaces.assert_awaited_once()


def _device(identifier: str) -> Any:
    """Return a device registry entry stand-in with one identifier."""
    return MagicMock(identifiers={(DOMAIN, identifier)})


async def test_mobility_devices_are_removable_only_once_confirmed_gone(
    hass: HomeAssistant, mock_mobility_client: MagicMock
) -> None:
    """A router or workspace can be deleted once Mobility no longer reports it."""
    _serve_spec_examples(mock_mobility_client)
    entry = _remote_entry("01REMOTE")
    await _setup(hass, entry)
    coordinator = entry.runtime_data.mobility_coordinator
    gone_router = _device("mobility_00000000-0000-0000-0000-000000000000")
    gone_workspace = _device("mobility_workspace_00000000-0000-0000-0000-00000000")

    assert not await async_remove_config_entry_device(
        hass, entry, _device(f"mobility_{OFFICE_ROUTER_ID}")
    )
    assert not await async_remove_config_entry_device(
        hass, entry, _device(f"mobility_workspace_{WORKSPACE_ID}")
    )
    assert await async_remove_config_entry_device(hass, entry, gone_router)
    assert await async_remove_config_entry_device(hass, entry, gone_workspace)

    # A failed poll proves nothing about what Mobility still has.
    coordinator.last_update_success = False
    assert not await async_remove_config_entry_device(hass, entry, gone_router)

    # Nor does a coordinator that has not answered yet.
    coordinator.last_update_success = True
    coordinator.data = {**coordinator.data, "access": "unknown", "devices": {}}
    assert not await async_remove_config_entry_device(hass, entry, gone_router)


async def test_mobility_devices_are_removable_from_a_non_owner_entry(
    hass: HomeAssistant,
) -> None:
    """Devices left behind on an entry that no longer owns Mobility can go."""
    owner = _remote_entry("01A", "console-a")
    second = _remote_entry("01B", "console-b")
    second.add_to_hass(hass)
    await _setup(hass, owner)

    assert second.runtime_data.mobility_coordinator is None
    assert await async_remove_config_entry_device(
        hass, second, _device(f"mobility_{OFFICE_ROUTER_ID}")
    )
