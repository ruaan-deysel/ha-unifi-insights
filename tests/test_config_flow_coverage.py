# Copyright (c) 2026 Ruaan Deysel
"""Tests for config flow error paths and edge cases to achieve 100% coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.unifi_insights.config_flow import UnifiInsightsConfigFlow

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture(autouse=True)
def mock_protect_client_flow():
    """Auto-mock Protect client for config flow tests unless overridden."""
    mock_protect_client = MagicMock()
    mock_protect_client.cameras = MagicMock()
    mock_protect_client.cameras.get_all = AsyncMock(return_value=[])
    mock_protect_client.nvr = MagicMock()
    mock_protect_client.nvr.get = AsyncMock(return_value=None)
    mock_protect_client.close = AsyncMock()

    protect_cm = MagicMock()
    protect_cm.__aenter__ = AsyncMock(return_value=mock_protect_client)
    protect_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiProtectClient",
            return_value=protect_cm,
        ),
        patch(
            "custom_components.unifi_insights.async_setup_entry",
            return_value=True,
        ),
    ):
        yield mock_protect_client


def test_extract_remote_console_options_skips_invalid_hosts() -> None:
    """Test _extract_remote_console_options skips invalid types or missing IDs."""
    hosts = [
        {"id": None, "type": "console"},
        {"id": "", "type": "console"},
        {"id": 123, "type": "console"},
        {"id": "valid_id_no_type", "type": None},
        {"id": "valid_id_other_type", "type": "gateway"},
        {
            "id": "console_1",
            "type": "console",
            "reportedState": "not-a-dict",
        },
        {
            "id": "console_2",
            "type": "console",
            "reportedState": {"hostname": None},
        },
    ]

    options = UnifiInsightsConfigFlow._extract_remote_console_options(hosts)
    assert options == {
        "console_1": "console_1 (console)",
        "console_2": "console_2 (console)",
    }


def test_extract_remote_console_options_uses_network_servers_when_no_consoles() -> None:
    """Test _extract_remote_console_options falls back to network servers."""
    hosts = [
        {
            "id": "server_1",
            "type": "network-server",
            "reportedState": {"hostname": "Cloud Key Gen2"},
        },
        {
            "id": "server_2",
            "type": "network-server",
            "reportedState": {},
        },
    ]

    options = UnifiInsightsConfigFlow._extract_remote_console_options(hosts)
    assert options == {
        "server_1": "Cloud Key Gen2 (network server)",
        "server_2": "server_2 (network server)",
    }


def test_normalize_remote_console_id_variants() -> None:
    """Test _normalize_remote_console_id for empty, prefix, and missing candidates."""
    discovered = {
        "console-123:site-a": "Console 123 (console)",
        "plain-console": "Plain (console)",
    }

    # Empty and whitespace candidates return None
    assert UnifiInsightsConfigFlow._normalize_remote_console_id("", discovered) is None
    assert (
        UnifiInsightsConfigFlow._normalize_remote_console_id("   ", discovered) is None
    )

    # Exact match (case insensitive)
    assert (
        UnifiInsightsConfigFlow._normalize_remote_console_id(
            "PLAIN-CONSOLE", discovered
        )
        == "plain-console"
    )

    # Prefix match before colon (case insensitive)
    assert (
        UnifiInsightsConfigFlow._normalize_remote_console_id("CONSOLE-123", discovered)
        == "console-123:site-a"
    )

    # Unknown candidate returns None
    assert (
        UnifiInsightsConfigFlow._normalize_remote_console_id("unknown-id", discovered)
        is None
    )
