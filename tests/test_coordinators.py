"""Tests for multi-coordinator architecture (Platinum compliance)."""

from __future__ import annotations

import asyncio
import copy
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights.api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiNotFoundError,
    UniFiRateLimitError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.api.network.models import (
    LegacyPortMetrics,
    PortBytesMetrics,
)
from custom_components.unifi_insights.const import (
    CONF_CONNECTION_TYPE,
    CONF_SITE_IDS,
    CONNECTION_TYPE_LOCAL,
    DOMAIN,
    SCAN_INTERVAL_CONFIG,
    SCAN_INTERVAL_DEVICE,
    SCAN_INTERVAL_PROTECT,
)
from custom_components.unifi_insights.coordinators.base import UnifiBaseCoordinator
from custom_components.unifi_insights.coordinators.config import UnifiConfigCoordinator
from custom_components.unifi_insights.coordinators.device import (
    MAX_STATS_REUSE_POLLS,
    UnifiDeviceCoordinator,
)
from custom_components.unifi_insights.coordinators.facade import UnifiFacadeCoordinator
from custom_components.unifi_insights.coordinators.protect import (
    MAX_CONSECUTIVE_EMPTY_FETCHES,
    MAX_CONSECUTIVE_MISSING_POLLS,
    STALE_EVENT_TIMEOUT,
    UnifiProtectCoordinator,
)
from custom_components.unifi_insights.entity import is_device_online
from tests.conftest import mock_device_lookup_method, set_mock_device_lookup

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="UniFi Insights (Local)",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
            CONF_HOST: "https://192.168.1.1",
            CONF_API_KEY: "test_api_key",
            CONF_VERIFY_SSL: False,
        },
        options={},
        source="user",
        unique_id="test_api_key",
        entry_id="test_entry_id",
    )


def _create_mock_model(data: dict) -> MagicMock:
    """Create a mock pydantic model that returns proper dict from model_dump."""
    mock = MagicMock()
    mock.model_dump = MagicMock(return_value=data)
    # Also set attributes for direct access
    for key, value in data.items():
        setattr(mock, key, value)
    return mock


def _create_mock_network_client() -> MagicMock:
    """Create a mock network client."""
    client = MagicMock()
    client.base_url = "https://192.168.1.1"

    # Sites namespace
    client.sites = MagicMock()
    client.sites.get_all = AsyncMock(
        return_value=[
            _create_mock_model({"id": "default", "name": "Default"}),
            _create_mock_model({"id": "site2", "name": "Site 2"}),
        ]
    )
    client.sites.get_legacy_all = AsyncMock(
        return_value=[
            {"name": "default", "desc": "Default"},
            {"name": "site2", "desc": "Site 2"},
        ]
    )

    # WiFi namespace
    client.wifi = MagicMock()
    client.wifi.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {"id": "wifi1", "name": "MainWiFi", "ssid": "MyNetwork"}
            ),
        ]
    )

    # Firewall namespace
    client.firewall = MagicMock()
    client.firewall.list_rules = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "rule1",
                    "name": "Block Instagram",
                    "enabled": True,
                    "action": "drop",
                    "protocol": "all",
                }
            )
        ]
    )
    client.firewall.update_rule = AsyncMock()

    # Routes namespace
    client.routes = MagicMock()
    client.routes.list_routes = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "route1",
                    "description": "Route via VPN",
                    "enabled": True,
                    "interface": "vpn",
                }
            )
        ]
    )
    client.routes.update_route = AsyncMock()

    # Devices namespace
    client.devices = MagicMock()
    client.devices.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "device1",
                    "name": "Test Switch",
                    "model": "USW-24",
                    "mac": "AA:BB:CC:DD:EE:FF",
                }
            )
        ]
    )
    client.devices.get_statistics = AsyncMock(
        return_value=_create_mock_model(
            {
                "cpuUtilizationPct": 15.2,
                "memoryUtilizationPct": 42.8,
                "uptimeSec": 864000,
            }
        )
    )
    client.devices.get_legacy_site_devices = AsyncMock(return_value=[])
    client.devices.execute_port_action = AsyncMock(return_value=True)

    # Clients namespace
    client.clients = MagicMock()
    client.clients.get_all = AsyncMock(
        return_value=[
            _create_mock_model({"id": "client1", "name": "iPhone", "type": "WIRELESS"}),
        ]
    )

    client.close = AsyncMock()
    return client


def _create_mock_protect_client() -> MagicMock:
    """Create a mock protect client."""
    client = MagicMock()
    client.base_url = "https://192.168.1.1"

    # Cameras namespace
    client.cameras = MagicMock()
    client.cameras.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "camera1",
                    "name": "Front Door",
                    "state": "CONNECTED",
                    "type": "UVC-G4-DOORBELL",
                    "mac": "11:22:33:44:55:66",
                    "featureFlags": {"smartDetectTypes": ["person", "vehicle"]},
                }
            )
        ]
    )

    # Lights namespace
    client.lights = MagicMock()
    client.lights.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "light1",
                    "name": "Garage Light",
                    "state": "CONNECTED",
                }
            )
        ]
    )

    # Sensors namespace
    client.sensors = MagicMock()
    client.sensors.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "sensor1",
                    "name": "Door Sensor",
                    "state": "CONNECTED",
                }
            )
        ]
    )

    # NVR namespace
    client.nvr = MagicMock()
    client.nvr.get = AsyncMock(
        return_value=_create_mock_model({"id": "nvr1", "name": "NVR", "type": "UNVR"})
    )

    # Chimes namespace
    client.chimes = MagicMock()
    client.chimes.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "chime1",
                    "name": "Door Chime",
                    "state": "CONNECTED",
                }
            )
        ]
    )

    # Viewers namespace
    client.viewers = MagicMock()
    client.viewers.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "viewer1",
                    "name": "Viewport",
                    "state": "CONNECTED",
                }
            )
        ]
    )

    # Liveviews namespace
    client.liveviews = MagicMock()
    client.liveviews.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {
                    "id": "liveview1",
                    "name": "Main View",
                    "isDefault": True,
                }
            )
        ]
    )

    # WebSocket support
    client.get_host_id = AsyncMock(return_value="nvr1")
    client.websocket = MagicMock()
    client.websocket.subscribe_with_callback = AsyncMock()
    client.websocket.stop = MagicMock()

    client.close = AsyncMock()
    return client


# ============================================================================
# UnifiBaseCoordinator Tests
# ============================================================================


class TestUnifiBaseCoordinator:
    """Tests for UnifiBaseCoordinator."""

    @pytest.fixture
    def coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiBaseCoordinator:
        """Create a base coordinator for testing."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        return UnifiBaseCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            name="test",
            update_interval=timedelta(seconds=30),
        )

    def test_initialization(self, coordinator: UnifiBaseCoordinator):
        """Test coordinator initialization."""
        assert coordinator.name == f"{DOMAIN}_test"
        assert coordinator.update_interval == timedelta(seconds=30)
        assert coordinator._available is True
        assert coordinator.data == {}

    def test_available_property(self, coordinator: UnifiBaseCoordinator):
        """Test available property."""
        assert coordinator.available is True
        coordinator._available = False
        assert coordinator.available is False

    def test_model_to_dict_with_none(self, coordinator: UnifiBaseCoordinator):
        """Test model_to_dict with None input."""
        result = coordinator._model_to_dict(None)
        assert result == {}

    def test_model_to_dict_with_dict(self, coordinator: UnifiBaseCoordinator):
        """Test model_to_dict with dict input."""
        input_dict = {"key": "value"}
        result = coordinator._model_to_dict(input_dict)
        assert result == input_dict

    def test_model_to_dict_with_pydantic_model(self, coordinator: UnifiBaseCoordinator):
        """Test model_to_dict with pydantic model."""
        mock_model = MagicMock()
        mock_model.model_dump = MagicMock(return_value={"id": "test", "name": "Test"})
        result = coordinator._model_to_dict(mock_model)
        assert result == {"id": "test", "name": "Test"}
        mock_model.model_dump.assert_called_once_with(by_alias=True, exclude_none=False)

    def test_model_to_dict_with_pydantic_model_type_error(
        self, coordinator: UnifiBaseCoordinator
    ):
        """Test model_to_dict fallback when by_alias raises TypeError."""
        mock_model = MagicMock()
        # First call raises TypeError, second call succeeds
        mock_model.model_dump = MagicMock(
            side_effect=[TypeError("by_alias not supported"), {"id": "fallback"}]
        )
        result = coordinator._model_to_dict(mock_model)
        assert result == {"id": "fallback"}

    def test_model_to_dict_with_object_dict(self, coordinator: UnifiBaseCoordinator):
        """Test model_to_dict with object having __dict__."""

        class SimpleObject:
            def __init__(self):
                self.id = "test"
                self.name = "Test Object"
                self._private = "hidden"

        obj = SimpleObject()
        result = coordinator._model_to_dict(obj)
        assert result == {"id": "test", "name": "Test Object"}
        assert "_private" not in result

    def test_model_to_dict_with_primitive(self, coordinator: UnifiBaseCoordinator):
        """Test model_to_dict with primitive value."""
        result = coordinator._model_to_dict("string")
        assert result == {}

    def test_handle_auth_error(self, coordinator: UnifiBaseCoordinator):
        """Test handling authentication error."""
        err = UniFiAuthenticationError("Invalid credentials")
        with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
            coordinator._handle_auth_error(err)
        assert coordinator._available is False

    def test_handle_connection_error(self, coordinator: UnifiBaseCoordinator):
        """Test handling connection error."""
        err = UniFiConnectionError("Connection refused")
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            coordinator._handle_connection_error(err)
        assert coordinator._available is False

    def test_handle_timeout_error(self, coordinator: UnifiBaseCoordinator):
        """Test handling timeout error."""
        err = UniFiTimeoutError("Request timed out")
        with pytest.raises(UpdateFailed, match="Timeout"):
            coordinator._handle_timeout_error(err)
        assert coordinator._available is False

    def test_handle_response_error(self, coordinator: UnifiBaseCoordinator):
        """Test handling API response error."""
        err = UniFiResponseError("Bad response", status_code=400)
        with pytest.raises(UpdateFailed, match="API error"):
            coordinator._handle_response_error(err)
        assert coordinator._available is False

    def test_handle_response_error_server_error_logs_warning(
        self, coordinator: UnifiBaseCoordinator, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 5xx API response errors are logged as warnings."""
        err = UniFiResponseError("Bad gateway", status_code=502)
        caplog.set_level(
            logging.WARNING, logger="custom_components.unifi_insights.coordinators.base"
        )

        with pytest.raises(UpdateFailed, match="API error"):
            coordinator._handle_response_error(err)

        assert coordinator._available is False
        assert any(
            record.levelno == logging.WARNING
            and "Server error during update" in record.message
            for record in caplog.records
        )
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_handle_response_error_client_error_logs_exception(
        self, coordinator: UnifiBaseCoordinator, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 4xx API response errors retain exception logging."""
        err = UniFiResponseError("Bad response", status_code=400)
        caplog.set_level(
            logging.ERROR, logger="custom_components.unifi_insights.coordinators.base"
        )

        with pytest.raises(UpdateFailed, match="API error"):
            coordinator._handle_response_error(err)

        assert coordinator._available is False
        assert any(
            record.levelno == logging.ERROR
            and "API error during update" in record.message
            and record.exc_info is not None
            for record in caplog.records
        )

    def test_handle_generic_error(self, coordinator: UnifiBaseCoordinator):
        """Test handling generic error."""
        err = Exception("Something went wrong")
        with pytest.raises(UpdateFailed, match="Error updating data"):
            coordinator._handle_generic_error(err)
        assert coordinator._available is False


# ============================================================================
# UnifiConfigCoordinator Tests
# ============================================================================


class TestUnifiConfigCoordinator:
    """Tests for UnifiConfigCoordinator."""

    @pytest.fixture
    def coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiConfigCoordinator:
        """Create a config coordinator for testing."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        return UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

    def test_initialization(self, coordinator: UnifiConfigCoordinator):
        """Test coordinator initialization."""
        assert coordinator.name == f"{DOMAIN}_config"
        assert coordinator.update_interval == SCAN_INTERVAL_CONFIG
        assert "sites" in coordinator.data
        assert "wifi" in coordinator.data
        assert "firewall_rules" in coordinator.data
        assert "policy_based_routes" in coordinator.data
        assert "network_info" in coordinator.data

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator: UnifiConfigCoordinator):
        """Test successful data fetch."""
        result = await coordinator._async_update_data()

        assert "sites" in result
        assert "default" in result["sites"]
        assert "site2" in result["sites"]
        assert "wifi" in result
        assert "firewall_rules" in result
        assert "rule1" in result["firewall_rules"]["default"]
        assert "policy_based_routes" in result
        assert "route1" in result["policy_based_routes"]["default"]
        assert coordinator._available is True
        assert coordinator.available_sites == {
            "default": "Default",
            "site2": "Site 2",
        }

    @pytest.mark.asyncio
    async def test_async_update_data_filters_selected_sites(self, hass: HomeAssistant):
        """Only the sites picked in options are polled (Issue #128)."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_API_KEY: "test_api_key"},
            options={CONF_SITE_IDS: ["site2"]},
        )
        network_client = _create_mock_network_client()
        coordinator = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=entry,
        )

        result = await coordinator._async_update_data()

        assert list(result["sites"]) == ["site2"]
        assert coordinator.get_site_ids() == ["site2"]
        # Every site stays selectable in the options flow.
        assert coordinator.available_sites == {
            "default": "Default",
            "site2": "Site 2",
        }
        polled = [call.args[0] for call in network_client.wifi.get_all.await_args_list]
        assert polled == ["site2"]

    @pytest.mark.asyncio
    async def test_async_update_data_prunes_per_site_maps(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Per-site config data for a site no longer polled is dropped."""
        for key in ("wifi", "firewall_rules", "policy_based_routes", "vpn_clients"):
            coordinator.data[key]["gone"] = {"stale": {"id": "stale"}}

        result = await coordinator._async_update_data()

        for key in ("wifi", "firewall_rules", "policy_based_routes", "vpn_clients"):
            assert "gone" not in result[key]
            assert "default" in result[key]

    @pytest.mark.asyncio
    async def test_async_update_data_selected_sites_all_gone(
        self, hass: HomeAssistant, caplog: pytest.LogCaptureFixture
    ):
        """A selection matching no current site polls nothing and says why."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_API_KEY: "test_api_key"},
            options={CONF_SITE_IDS: ["removed-site"]},
        )
        coordinator = UnifiConfigCoordinator(
            hass=hass,
            network_client=_create_mock_network_client(),
            protect_client=None,
            entry=entry,
        )

        with caplog.at_level(logging.WARNING):
            result = await coordinator._async_update_data()
            await coordinator._async_update_data()

        assert result["sites"] == {}
        # Warned once, not on every 5-minute poll.
        assert caplog.text.count("none of the selected sites") == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", ["wifi.get_all", "firewall.list_rules"])
    @pytest.mark.parametrize(
        "error",
        [
            UniFiNotFoundError("Not found", status_code=404),
            UniFiResponseError("Bad request", status_code=400),
            UniFiAuthenticationError("Forbidden", status_code=403),
            UniFiResponseError("HTML instead of JSON", status_code=200),
        ],
        ids=["404", "400", "403", "200-non-json"],
    )
    async def test_async_update_data_optional_endpoint_unsupported(
        self, coordinator: UnifiConfigCoordinator, endpoint: str, error: Exception
    ):
        """A 4xx from WiFi/firewall means the feature is absent, not a failure."""
        namespace, method = endpoint.split(".")
        setattr(
            getattr(coordinator.network_client, namespace),
            method,
            AsyncMock(side_effect=error),
        )

        result = await coordinator._async_update_data()

        section = "wifi" if namespace == "wifi" else "firewall_rules"
        assert result[section]["default"] == {}
        assert "default" in result["sites"]
        assert coordinator._available is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("endpoint", "section", "other_section"),
        [
            ("wifi.get_all", "wifi", "firewall_rules"),
            ("firewall.list_rules", "firewall_rules", "wifi"),
        ],
        ids=["wifi", "firewall"],
    )
    @pytest.mark.parametrize(
        "error",
        [
            UniFiResponseError("Server error", status_code=500),
            UniFiRateLimitError("Slow down", status_code=429),
            UniFiConnectionError("Connection refused"),
            UniFiTimeoutError("Timed out"),
            ValueError("Unparseable payload"),
        ],
        ids=["500", "429", "connection", "timeout", "unexpected"],
    )
    async def test_async_update_data_optional_section_failure(
        self,
        coordinator: UnifiConfigCoordinator,
        endpoint: str,
        section: str,
        other_section: str,
        error: Exception,
    ):
        """A failed WiFi/firewall fetch keeps that section's data and flags it."""
        await coordinator.async_refresh()
        assert coordinator.wifi_available("default") is True
        assert coordinator.firewall_available("default") is True
        previous = copy.deepcopy(coordinator.data[section])
        assert previous["default"]

        namespace, method = endpoint.split(".")
        working = getattr(getattr(coordinator.network_client, namespace), method)
        setattr(
            getattr(coordinator.network_client, namespace),
            method,
            AsyncMock(side_effect=error),
        )

        await coordinator.async_refresh()

        # The refresh itself succeeds so other sections and platforms keep
        # working, but the failed section is not reported as fresh.
        assert coordinator.last_update_success is True
        assert coordinator.data[section] == previous
        section_flag = {
            "wifi": coordinator.wifi_available,
            "firewall_rules": coordinator.firewall_available,
        }
        assert section_flag[section]("default") is False
        assert section_flag[other_section]("default") is True

        setattr(getattr(coordinator.network_client, namespace), method, working)
        await coordinator.async_refresh()
        assert section_flag[section]("default") is True

    @pytest.mark.asyncio
    async def test_optional_section_failure_is_per_site(
        self, coordinator: UnifiConfigCoordinator
    ):
        """A WiFi failure on one site leaves other sites' WiFi available."""
        working = coordinator.network_client.wifi.get_all

        async def get_all(site_id: str):
            if site_id == "site2":
                msg = "site2 WiFi down"
                raise UniFiConnectionError(msg)
            return await working(site_id)

        coordinator.network_client.wifi.get_all = AsyncMock(side_effect=get_all)
        await coordinator.async_refresh()

        assert coordinator.wifi_available("default") is True
        assert coordinator.wifi_available("site2") is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", ["wifi.get_all", "firewall.list_rules"])
    async def test_async_update_data_optional_endpoint_auth_failure_reauths(
        self, coordinator: UnifiConfigCoordinator, endpoint: str
    ):
        """A 401 from WiFi/firewall means revoked credentials and starts reauth."""
        namespace, method = endpoint.split(".")
        setattr(
            getattr(coordinator.network_client, namespace),
            method,
            AsyncMock(side_effect=UniFiAuthenticationError("Revoked", status_code=401)),
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_async_update_data_enriches_wifi_and_collects_sections(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Legacy WiFi enrichment, VPN clients and id-less rules on a good poll."""
        client = coordinator.network_client
        client.wifi.get_legacy_configs = AsyncMock(
            return_value=[
                {"name": "MainWiFi", "x_passphrase": "secret", "security": "wpapsk"}
            ]
        )
        client.clients.get_active_legacy = AsyncMock(
            return_value=[
                {"essid": "MainWiFi"},
                {"essid": "MainWiFi", "is_wired": True},
            ]
        )
        client.vpn_clients.list_vpn_clients = AsyncMock(
            return_value=[{"_id": "vpn1", "name": "Office"}, {"name": "no id"}]
        )
        client.firewall.list_rules = AsyncMock(
            return_value=[_create_mock_model({"name": "rule without id"})]
        )

        result = await coordinator._async_update_data()

        wifi = result["wifi"]["default"]["wifi1"]
        assert wifi["num_connected_clients"] == 1
        assert wifi["qr_code"].startswith("WIFI:T:WPA;S:MainWiFi;P:")
        assert list(result["vpn_clients"]["default"]) == ["vpn1"]
        assert result["firewall_rules"]["default"] == {}
        assert coordinator.firewall_available("default") is True

    @pytest.mark.asyncio
    async def test_async_update_data_drops_sites_that_disappeared(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Per-site sections are rebuilt, so a removed site's data is not kept."""
        coordinator.data["wifi"]["gone"] = {"wifi-x": {"id": "wifi-x"}}
        coordinator.data["firewall_rules"]["gone"] = {"rule-x": {"id": "rule-x"}}

        result = await coordinator._async_update_data()

        assert "gone" not in result["wifi"]
        assert "gone" not in result["firewall_rules"]

    @pytest.mark.asyncio
    async def test_async_update_data_routes_error(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test policy-based routes are optional when the endpoint is unavailable."""
        coordinator.network_client.routes.list_routes = AsyncMock(
            side_effect=Exception("Routes endpoint unavailable")
        )

        result = await coordinator._async_update_data()

        assert "sites" in result
        assert "default" in result["sites"]
        assert result["policy_based_routes"]["default"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_routes_auth_error(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test auth error during routes fetch triggers reauth."""
        coordinator.protect_client = None
        coordinator.network_client.routes.list_routes = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_vpn_clients_error(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test VPN clients are optional when the endpoint is unavailable."""
        coordinator.network_client.vpn_clients.list_vpn_clients = AsyncMock(
            side_effect=Exception("VPN clients endpoint unavailable")
        )

        result = await coordinator._async_update_data()

        assert "sites" in result
        assert "default" in result["sites"]
        assert result["vpn_clients"]["default"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_vpn_clients_auth_error(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test auth error during VPN clients fetch triggers reauth."""
        coordinator.protect_client = None
        coordinator.network_client.vpn_clients.list_vpn_clients = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_auth_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with auth error on network-only setup."""
        coordinator.protect_client = None
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_protect_only_console(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test fetch succeeds on Protect-only console with empty sites (Issue 93)."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("Not found", status_code=404)
        )

        result = await coordinator._async_update_data()
        assert result["sites"] == {}
        assert result["wifi"] == {}
        assert result["firewall_rules"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_protect_only_console_non_json_sites(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test fetch succeeds when the sites endpoint returns 200 and no JSON."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError(
                "API returned non-JSON response (status 200)", status_code=200
            )
        )

        result = await coordinator._async_update_data()
        assert result["sites"] == {}
        assert result["wifi"] == {}
        assert result["firewall_rules"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_non_json_sites_without_protect(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test a non-JSON sites response still fails when Protect is absent."""
        coordinator.protect_client = None
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError(
                "API returned non-JSON response (status 200)", status_code=200
            )
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_redirect_sites_still_fails(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test only a 200 is tolerated, so a 3xx is not swallowed."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError("Redirected", status_code=302)
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_server_error_sites_still_fails(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test a >=400 response is not swallowed by the non-JSON tolerance."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError("Server error", status_code=500)
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_connection_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with connection error."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiConnectionError("Connection refused")
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_timeout_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with timeout error."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiTimeoutError("Request timed out")
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_response_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with response error."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError("Bad response", status_code=400)
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_generic_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with generic error."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=Exception("Something broke")
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    def test_get_site_existing(self, coordinator: UnifiConfigCoordinator):
        """Test getting existing site."""
        coordinator.data["sites"] = {"default": {"id": "default", "name": "Default"}}
        result = coordinator.get_site("default")
        assert result == {"id": "default", "name": "Default"}

    def test_get_site_missing(self, coordinator: UnifiConfigCoordinator):
        """Test getting missing site."""
        result = coordinator.get_site("nonexistent")
        assert result is None

    def test_get_site_ids(self, coordinator: UnifiConfigCoordinator):
        """Test getting all site IDs."""
        coordinator.data["sites"] = {
            "default": {"id": "default"},
            "site2": {"id": "site2"},
        }
        result = coordinator.get_site_ids()
        assert set(result) == {"default", "site2"}

    def test_get_wifi_networks(self, coordinator: UnifiConfigCoordinator):
        """Test getting WiFi networks for a site."""
        coordinator.data["wifi"] = {
            "default": {"wifi1": {"id": "wifi1", "name": "MainWiFi"}}
        }
        result = coordinator.get_wifi_networks("default")
        assert "wifi1" in result

    def test_get_wifi_networks_missing_site(self, coordinator: UnifiConfigCoordinator):
        """Test getting WiFi networks for missing site."""
        result = coordinator.get_wifi_networks("nonexistent")
        assert result == {}

    def test_get_firewall_rules(self, coordinator: UnifiConfigCoordinator):
        """Test getting firewall rules for a site."""
        coordinator.data["firewall_rules"] = {
            "default": {"rule1": {"id": "rule1", "name": "Block Instagram"}}
        }
        result = coordinator.get_firewall_rules("default")
        assert "rule1" in result

    def test_get_firewall_rules_missing_site(self, coordinator: UnifiConfigCoordinator):
        """Test getting firewall rules for missing site."""
        result = coordinator.get_firewall_rules("nonexistent")
        assert result == {}

    def test_get_policy_based_routes(self, coordinator: UnifiConfigCoordinator):
        """Test getting policy-based routes for a site."""
        coordinator.data["policy_based_routes"] = {
            "default": {"route1": {"id": "route1", "description": "Route to VPN"}}
        }
        result = coordinator.get_policy_based_routes("default")
        assert "route1" in result

    def test_get_policy_based_routes_missing_site(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test getting policy-based routes for missing site."""
        result = coordinator.get_policy_based_routes("nonexistent")
        assert result == {}

    def test_get_vpn_clients(self, coordinator: UnifiConfigCoordinator) -> None:
        """Test getting VPN clients for a site."""
        coordinator.data["vpn_clients"] = {
            "default": {"client1": {"_id": "client1", "name": "Privado VPN"}}
        }
        result = coordinator.get_vpn_clients("default")
        assert "client1" in result

    def test_get_vpn_clients_missing_site(
        self, coordinator: UnifiConfigCoordinator
    ) -> None:
        """Test getting VPN clients for missing site."""
        result = coordinator.get_vpn_clients("nonexistent")
        assert result == {}

    @pytest.mark.asyncio
    async def test_async_update_data_skips_none_site_id(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test that WiFi fetch skips None site IDs."""
        # Create a site model that returns None for id
        site_with_none_id = MagicMock()
        site_with_none_id.model_dump.return_value = {"id": None, "name": "BadSite"}

        site_valid = MagicMock()
        site_valid.model_dump.return_value = {"id": "valid_site", "name": "ValidSite"}

        coordinator.network_client.sites.get_all = AsyncMock(
            return_value=[site_with_none_id, site_valid]
        )

        result = await coordinator._async_update_data()

        # Should only have the valid site (None id is filtered out)
        assert "valid_site" in result["sites"]
        assert None not in result["sites"]

    @pytest.mark.asyncio
    async def test_async_update_data_skips_wifi_without_id(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test that WiFi networks without an ID are skipped."""
        # Create WiFi models - one with ID, one without
        wifi_with_id = MagicMock()
        wifi_with_id.model_dump.return_value = {"id": "wifi1", "name": "ValidWiFi"}

        wifi_without_id = MagicMock()
        wifi_without_id.model_dump.return_value = {"id": None, "name": "BadWiFi"}

        coordinator.network_client.wifi.get_all = AsyncMock(
            return_value=[wifi_with_id, wifi_without_id]
        )

        result = await coordinator._async_update_data()

        # Should only have the WiFi with valid ID
        assert "wifi1" in result["wifi"].get("default", {})
        # WiFi without ID should not be in the dict
        assert None not in result["wifi"].get("default", {})


# ============================================================================
# UnifiDeviceCoordinator Tests
# ============================================================================


class TestUnifiDeviceCoordinator:
    """Tests for UnifiDeviceCoordinator."""

    @pytest.fixture
    def config_coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiConfigCoordinator:
        """Create a config coordinator."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        coord = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        # Pre-populate with site data
        coord.data["sites"] = {"default": {"id": "default", "name": "Default"}}
        return coord

    @pytest.fixture
    def coordinator(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
    ) -> UnifiDeviceCoordinator:
        """Create a device coordinator for testing."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        return UnifiDeviceCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
        )

    def test_initialization(self, coordinator: UnifiDeviceCoordinator):
        """Test coordinator initialization."""
        assert coordinator.name == f"{DOMAIN}_device"
        assert coordinator.update_interval == SCAN_INTERVAL_DEVICE
        assert "devices" in coordinator.data
        assert "clients" in coordinator.data
        assert "stats" in coordinator.data

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator: UnifiDeviceCoordinator):
        """Test successful data fetch."""
        result = await coordinator._async_update_data()

        assert "devices" in result
        assert "default" in result["devices"]
        assert "device1" in result["devices"]["default"]
        assert "clients" in result
        assert "stats" in result
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_process_site_5xx_fallback_with_client_retry(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """v1 devices 5xx falls back to legacy devices and retries clients.

        Regression test: the v1 devices endpoint returns 500 (USW Pro XG
        family), the site has a legacy name, and the first clients.get_all()
        call fails. The legacy device becomes the primary device, the retried
        client appears, and clients.get_all is awaited twice.
        """
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Internal Server Error", status_code=500)
        )
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            return_value=[
                {
                    "_id": "60a1b2c3d4e5f67890123456",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "name": "Legacy Switch",
                    "model": "USW-24",
                    "type": "usw",
                    "ip": "192.168.1.10",
                    "up": True,
                    "port_table": [
                        {
                            "port_idx": 1,
                            "up": True,
                            "speed": 1000,
                            "name": "Port 1",
                        }
                    ],
                }
            ]
        )

        clients_call_count = 0

        async def clients_side_effect(site_id):
            nonlocal clients_call_count
            clients_call_count += 1
            if clients_call_count == 1:
                msg = "Service Unavailable"
                raise UniFiResponseError(msg, status_code=503)
            return [
                _create_mock_model(
                    {"id": "client1", "name": "Retried Client", "type": "WIRED"}
                )
            ]

        coordinator.network_client.clients.get_all = AsyncMock(
            side_effect=clients_side_effect
        )

        devices_dict, stats_dict, clients_dict = await coordinator._process_site(
            "default", legacy_site_name="default"
        )

        # The legacy device is keyed by its controller id (mapped from _id),
        # consistent with the v1 keying: devices without an id fall back to
        # their MAC, but this legacy device has an _id.
        assert "60a1b2c3d4e5f67890123456" in devices_dict
        assert "AA:BB:CC:DD:EE:FF" not in devices_dict
        legacy_device = devices_dict["60a1b2c3d4e5f67890123456"]
        assert legacy_device["name"] == "Legacy Switch"
        assert legacy_device["macAddress"] == "AA:BB:CC:DD:EE:FF"
        # Legacy "up": True is mapped to a v1-style string state that
        # is_device_online() can read.
        assert legacy_device["state"] == "ONLINE"
        assert is_device_online(legacy_device)
        # port_table is normalized into the v1-shaped ports list
        assert legacy_device["ports"][0]["idx"] == 1

        # The retried client appears, keyed by client id
        assert "client1" in clients_dict
        assert clients_dict["client1"]["name"] == "Retried Client"

        assert clients_call_count == 2
        assert coordinator.network_client.clients.get_all.await_count == 2

        # The per-device statistics endpoint still works in fallback mode:
        # the 5xx was on the v1 devices list endpoint only.
        assert stats_dict["60a1b2c3d4e5f67890123456"]["id"] == (
            "60a1b2c3d4e5f67890123456"
        )

    @pytest.mark.asyncio
    async def test_legacy_device_to_v1_dict_up_state_mapping(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Legacy bool ``up`` maps to a string ``state`` is_device_online reads."""
        online = coordinator._legacy_device_to_v1_dict(
            {"_id": "abc123", "mac": "AA:BB:CC:DD:EE:FF", "up": True}
        )
        offline = coordinator._legacy_device_to_v1_dict(
            {"_id": "abc123", "mac": "AA:BB:CC:DD:EE:FF", "up": False}
        )
        assert online["state"] == "ONLINE"
        assert is_device_online(online)
        assert offline["state"] == "OFFLINE"
        assert not is_device_online(offline)

        # An existing usable string state is preserved, and a non-string
        # legacy ``state`` (0/1) does not block the conversion.
        preserved = coordinator._legacy_device_to_v1_dict(
            {"_id": "abc123", "up": True, "state": "ONLINE"}
        )
        assert preserved["state"] == "ONLINE"
        int_state = coordinator._legacy_device_to_v1_dict(
            {"_id": "abc123", "up": True, "state": 1}
        )
        assert int_state["state"] == "ONLINE"
        assert is_device_online(int_state)

    def test_legacy_device_to_v1_dict_falls_back_to_mac_id(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """No ``_id`` maps id from mac; field_map keys are copied when absent."""
        mapped = coordinator._legacy_device_to_v1_dict(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "fw_version": "6.6.55",
                "port_table": [
                    {"port_idx": 1, "up": True},
                    {"name": "no port_idx, dropped"},
                    "not-a-dict-entry",
                ],
            }
        )

        # No "_id" present, so id falls back to the device's mac.
        assert mapped["id"] == "AA:BB:CC:DD:EE:FF"
        # A field_map key present in legacy and absent from mapped is copied
        # to its v1 camelCase alias.
        assert mapped["firmwareVersion"] == "6.6.55"
        # port_table entries are filtered: the dict without port_idx and the
        # non-dict entry are both dropped, leaving only the valid port.
        assert len(mapped["ports"]) == 1
        assert mapped["ports"][0]["port_idx"] == 1

    def test_legacy_device_to_v1_dict_preserves_existing_id_and_mapped_field(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """An existing ``id``/mapped alias is not clobbered by the fallbacks."""
        mapped = coordinator._legacy_device_to_v1_dict(
            {
                "_id": "60a1b2c3d4e5f67890123456",
                "mac": "AA:BB:CC:DD:EE:FF",
                "id": "already-set",
                "fw_version": "6.6.55",
                "firmwareVersion": "already-mapped",
            }
        )
        # legacy_id is truthy but "id" is already present, so it is untouched.
        assert mapped["id"] == "already-set"
        # firmwareVersion is already present, so fw_version is not copied over.
        assert mapped["firmwareVersion"] == "already-mapped"

    def test_legacy_device_to_v1_dict_no_valid_ports_omits_ports_key(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A port_table with no valid entries leaves ``ports`` unset."""
        mapped = coordinator._legacy_device_to_v1_dict(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "port_table": [
                    {"name": "missing port_idx"},
                    "not-a-dict-entry",
                ],
            }
        )
        assert "ports" not in mapped

    def test_normalize_legacy_port_missing_port_idx_returns_none(self):
        """A port_table entry without port_idx cannot be normalized."""
        assert UnifiDeviceCoordinator._normalize_legacy_port({"name": "no idx"}) is None

    def test_normalize_legacy_port_maps_all_optional_fields(self):
        """Optional identification/SFP fields are copied through when present."""
        normalized = UnifiDeviceCoordinator._normalize_legacy_port(
            {
                "port_idx": 5,
                "up": True,
                "media": "GE",
                "is_uplink": True,
                "name": "Uplink",
                "ifname": "eth5",
                "network_name": "Corporate LAN",
                "sfp_found": True,
                "sfp_part": "SFP-10G-SR",
                "sfp_vendor": "Ubiquiti",
                "sfp_serial": "SN12345",
                "sfp_compliance": "10GBASE-SR",
            }
        )
        assert normalized is not None
        assert normalized["media"] == "GE"
        assert normalized["is_uplink"] is True
        assert normalized["ifname"] == "eth5"
        assert normalized["network_name"] == "Corporate LAN"
        assert normalized["sfp_found"] is True
        assert normalized["sfp_part"] == "SFP-10G-SR"
        assert normalized["sfp_vendor"] == "Ubiquiti"
        assert normalized["sfp_serial"] == "SN12345"
        assert normalized["sfp_compliance"] == "10GBASE-SR"

    @pytest.mark.asyncio
    async def test_process_site_5xx_fallback_legacy_failure_raises(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """When v1 5xx and the legacy fetch both fail, the v1 error propagates."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Internal Server Error", status_code=500)
        )
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            side_effect=UniFiConnectionError("Connection refused")
        )

        with pytest.raises(UniFiResponseError):
            await coordinator._process_site("default", legacy_site_name="default")

    @pytest.mark.asyncio
    async def test_process_site_5xx_with_empty_legacy_raises(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A v1 5xx with an empty legacy response fails instead of wiping devices."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Internal Server Error", status_code=500)
        )
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            return_value=[]
        )

        with pytest.raises(UniFiResponseError):
            await coordinator._process_site("default", legacy_site_name="default")

        # The refresh keeps the previous snapshot instead of writing an
        # empty device map (same contract as any other site failure).
        previous = copy.deepcopy(coordinator.data["devices"])
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        assert coordinator.data["devices"] == previous

    @pytest.mark.asyncio
    async def test_process_site_5xx_without_legacy_site_raises(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A v1 5xx without a legacy site name cannot fall back and raises."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Internal Server Error", status_code=500)
        )

        with pytest.raises(UniFiResponseError):
            await coordinator._process_site("default")

    @pytest.mark.asyncio
    async def test_process_site_4xx_does_not_fall_back(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Only 5xx triggers the legacy fallback; a 4xx error propagates."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Forbidden", status_code=403)
        )

        with pytest.raises(UniFiResponseError):
            await coordinator._process_site("default", legacy_site_name="default")

        coordinator.network_client.devices.get_legacy_site_devices.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_site_clients_4xx_raises_without_fallback(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A clients failure with healthy v1 devices propagates (no fallback)."""
        coordinator.network_client.clients.get_all = AsyncMock(
            side_effect=UniFiResponseError("Service Unavailable", status_code=503)
        )

        with pytest.raises(UniFiResponseError):
            await coordinator._process_site("default", legacy_site_name="default")

        coordinator.network_client.clients.get_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_update_data_uses_legacy_devices_on_v1_5xx(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """End-to-end: a v1 devices 5xx refresh succeeds via legacy devices."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Internal Server Error", status_code=500)
        )
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            return_value=[
                {
                    "_id": "60a1b2c3d4e5f67890123456",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "name": "Legacy Switch",
                    "model": "USW-24",
                    "type": "usw",
                    "up": True,
                }
            ]
        )

        result = await coordinator._async_update_data()

        assert "60a1b2c3d4e5f67890123456" in result["devices"]["default"]
        assert result["devices"]["default"]["60a1b2c3d4e5f67890123456"]["name"] == (
            "Legacy Switch"
        )
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_merges_legacy_temperature(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test successful merge of legacy temperature fields into device data."""
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            return_value=[
                {
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "general_temperature": 47.5,
                    "temperatures": [
                        {"name": "CPU", "value": 51.0},
                        {"name": "Local", "value": 47.5},
                    ],
                    "has_temperature": False,
                }
            ]
        )

        result = await coordinator._async_update_data()

        device_data = result["devices"]["default"]["device1"]
        assert device_data["generalTemperature"] == 47.5
        assert device_data["hasTemperature"] is True
        assert device_data["temperatures"][0]["name"] == "CPU"

    @pytest.mark.asyncio
    async def test_async_update_data_merges_legacy_outlets(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test merge of legacy outlet table and power totals into device data."""
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            return_value=[
                {
                    "_id": "60a1b2c3d4e5f67890123456",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "outlet_ac_power_consumption": "245.50",
                    "outlet_ac_power_budget": "1800.00",
                    "outlet_table": [
                        {
                            "index": 1,
                            "name": "Outlet 1",
                            "relay_state": True,
                            "cycle_enabled": True,
                            "outlet_caps": 3,
                            "outlet_voltage": "120.2",
                            "outlet_current": "1.25",
                            "outlet_power": "150.0",
                            "outlet_power_factor": "0.98",
                        }
                    ],
                    "outlet_overrides": [
                        {
                            "index": 1,
                            "relay_state": True,
                            "cycle_enabled": True,
                        }
                    ],
                }
            ]
        )

        result = await coordinator._async_update_data()

        device_data = result["devices"]["default"]["device1"]
        assert device_data["_id"] == "60a1b2c3d4e5f67890123456"
        assert device_data["ac_power_consumption"] == 245.5
        assert device_data["ac_power_budget"] == 1800.0
        assert len(device_data["outlet_table"]) == 1
        assert device_data["outlet_table"][0]["name"] == "Outlet 1"
        assert device_data["outlet_table"][0]["relay_state"] is True
        assert device_data["outlet_table"][0]["cycle_enabled"] is True
        assert device_data["outlet_table"][0]["outlet_power"] == 150.0
        assert len(device_data["outlet_overrides"]) == 1

    def test_merge_legacy_outlet_data_edge_cases(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test _merge_legacy_outlet_data edge cases."""
        # 1. Missing MAC in device_dict
        dev: dict[str, Any] = {"name": "No MAC"}
        coordinator._merge_legacy_outlet_data(
            dev, {"aa:bb:cc:dd:ee:ff": {"outlet_table": [{"index": 1}]}}
        )
        assert "outlet_table" not in dev

        # 2. Legacy device not in legacy_devices_by_mac
        dev = {"mac": "AA:BB:CC:DD:EE:FF"}
        coordinator._merge_legacy_outlet_data(dev, {})
        assert "outlet_table" not in dev

        # 3. Legacy device has no outlets and no power totals
        dev = {"mac": "AA:BB:CC:DD:EE:FF"}
        coordinator._merge_legacy_outlet_data(
            dev, {"aa:bb:cc:dd:ee:ff": {"name": "Empty"}}
        )
        assert "outlet_table" not in dev

        # 4. Legacy device has only ac_power_consumption
        dev = {"mac": "AA:BB:CC:DD:EE:FF"}
        coordinator._merge_legacy_outlet_data(
            dev, {"aa:bb:cc:dd:ee:ff": {"outlet_ac_power_consumption": "50.5"}}
        )
        assert dev["ac_power_consumption"] == 50.5
        assert "outlet_table" not in dev

        # 5. Legacy device has only ac_power_budget
        dev = {"mac": "AA:BB:CC:DD:EE:FF"}
        coordinator._merge_legacy_outlet_data(
            dev, {"aa:bb:cc:dd:ee:ff": {"outlet_ac_power_budget": "100.0"}}
        )
        assert dev["ac_power_budget"] == 100.0

    @pytest.mark.asyncio
    async def test_async_update_data_legacy_temperature_failure_is_ignored(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test legacy temperature fetch failure does not drop device data."""
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock(
            side_effect=Exception("Legacy endpoint unavailable")
        )

        result = await coordinator._async_update_data()

        assert "device1" in result["devices"]["default"]
        assert "generalTemperature" not in result["devices"]["default"]["device1"]

    @pytest.mark.asyncio
    async def test_async_update_data_no_sites(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch with no sites available."""
        coordinator.config_coordinator.data["sites"] = {}

        result = await coordinator._async_update_data()

        # Should return existing data without changes
        assert result == coordinator.data
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_prunes_sites_no_longer_listed(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Data for a site no longer listed is dropped, and its devices go stale."""
        for key in ("devices", "stats", "clients"):
            coordinator.data[key]["gone"] = {"dev-gone": {"id": "dev-gone"}}
        coordinator._previous_network_device_ids = {"gone_dev-gone"}

        with patch.object(coordinator, "_cleanup_stale_devices") as cleanup:
            await coordinator._async_update_data()

        for key in ("devices", "stats", "clients"):
            assert "gone" not in coordinator.data[key]
            assert "default" in coordinator.data[key]
        cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_update_data_no_sites_clears_data_keeps_registry(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """An empty site list clears stale data but never purges registry devices."""
        for key in ("devices", "stats", "clients"):
            coordinator.data[key]["default"] = {"device1": {"id": "device1"}}
        coordinator._previous_network_device_ids = {"default_device1"}
        coordinator.config_coordinator.data["sites"] = {}

        with patch.object(coordinator, "_cleanup_stale_devices") as cleanup:
            await coordinator._async_update_data()

        for key in ("devices", "stats", "clients"):
            assert coordinator.data[key] == {}
        # An empty list is also what a transient API failure looks like.
        cleanup.assert_not_called()
        assert coordinator._previous_network_device_ids == {"default_device1"}

    @pytest.mark.asyncio
    async def test_process_device_stats_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test device processing with stats error."""
        coordinator.network_client.devices.get_statistics = AsyncMock(
            side_effect=Exception("Stats failed")
        )

        result = await coordinator._async_update_data()

        # Devices should still be fetched, just without stats
        assert "devices" in result
        assert "default" in result["devices"]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_mac_keyed_device_skips_statistics_keeps_legacy_metrics(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A device keyed on its MAC has no controller id to fetch stats by (#128)."""
        mac = "e0:63:da:00:00:01"
        coordinator.network_client.devices.get_all = AsyncMock(
            return_value=[
                _create_mock_model(
                    {"id": mac, "macAddress": mac, "name": "AC Mesh", "state": "ONLINE"}
                )
            ]
        )
        coordinator.network_client.devices.get_port_metrics = AsyncMock(
            return_value=LegacyPortMetrics(
                port_bytes={1: PortBytesMetrics(rx_bytes=10, tx_bytes=20)}
            )
        )

        result = await coordinator._async_update_data()

        coordinator.network_client.devices.get_statistics.assert_not_awaited()
        coordinator.network_client.devices.get_port_metrics.assert_awaited_once()
        assert mac in result["devices"]["default"]
        stats = result["stats"]["default"][mac]
        assert stats["port_bytes"] == {1: {"rx_bytes": 10, "tx_bytes": 20}}
        assert stats["id"] == mac

    @pytest.mark.parametrize("endpoint", ["devices.get_all", "clients.get_all"])
    @pytest.mark.parametrize(
        "error",
        [
            UniFiConnectionError("Connection refused"),
            UniFiTimeoutError("Request timed out"),
            UniFiResponseError("Server error", status_code=502),
            UniFiResponseError("Bad response", status_code=400),
            Exception("Something broke"),
        ],
        ids=["connection", "timeout", "502", "400", "unexpected"],
    )
    async def test_site_failure_fails_refresh_and_keeps_snapshot(
        self, coordinator: UnifiDeviceCoordinator, endpoint: str, error: Exception
    ):
        """A site that cannot be fetched fails the refresh; old data is kept."""
        await coordinator._async_update_data()
        previous_devices = copy.deepcopy(coordinator.data["devices"]["default"])
        previous_stats = copy.deepcopy(coordinator.data["stats"]["default"])
        assert previous_devices

        namespace, method = endpoint.split(".")
        setattr(
            getattr(coordinator.network_client, namespace),
            method,
            AsyncMock(side_effect=error),
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

        assert coordinator._available is False
        assert coordinator.data["devices"]["default"] == previous_devices
        assert coordinator.data["stats"]["default"] == previous_stats

    @pytest.mark.asyncio
    async def test_site_auth_failure_starts_reauth(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A revoked key on the devices endpoint raises ConfigEntryAuthFailed."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key", status_code=401)
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_one_failed_site_fails_refresh_without_partial_write(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """With several sites, one failure fails the refresh and writes nothing."""
        coordinator.config_coordinator.data["sites"]["site2"] = {"id": "site2"}
        original_get_all = coordinator.network_client.devices.get_all

        async def get_all(site_id: str):
            if site_id == "site2":
                msg = "site2 unreachable"
                raise UniFiConnectionError(msg)
            return await original_get_all(site_id)

        coordinator.network_client.devices.get_all = AsyncMock(side_effect=get_all)

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

        assert coordinator.data["devices"] == {}
        assert coordinator.data["stats"] == {}

    @pytest.mark.asyncio
    async def test_auth_failure_wins_over_other_site_failures(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """If any site reports revoked credentials, reauth is triggered."""
        coordinator.config_coordinator.data["sites"]["site2"] = {"id": "site2"}

        async def get_all(site_id: str):
            if site_id == "site2":
                msg = "Revoked"
                raise UniFiAuthenticationError(msg, status_code=401)
            msg = "default unreachable"
            raise UniFiConnectionError(msg)

        coordinator.network_client.devices.get_all = AsyncMock(side_effect=get_all)

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_stats_auth_failure_starts_reauth(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Revoked credentials surfacing on the stats endpoint start reauth."""
        coordinator.network_client.devices.get_statistics = AsyncMock(
            side_effect=UniFiAuthenticationError("Revoked", status_code=401)
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error",
        [
            UniFiConnectionError("Connection lost"),
            UniFiTimeoutError("Timed out"),
            UniFiResponseError("Server error", status_code=500),
            UniFiRateLimitError("Slow down", status_code=429),
        ],
        ids=["connection", "timeout", "500", "429"],
    )
    async def test_stats_transient_failure_keeps_previous_stats(
        self, coordinator: UnifiDeviceCoordinator, error: Exception
    ):
        """One device's stats failing keeps its last stats, not the refresh."""
        await coordinator._async_update_data()
        previous = copy.deepcopy(coordinator.data["stats"]["default"]["device1"])
        assert previous

        coordinator.network_client.devices.get_statistics = AsyncMock(side_effect=error)
        result = await coordinator._async_update_data()

        assert coordinator._available is True
        assert result["stats"]["default"]["device1"] == previous

    @pytest.mark.asyncio
    async def test_refresh_without_legacy_site_mapping(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Sites still refresh when the classic site mapping is unavailable."""
        coordinator.network_client.sites.get_legacy_all = AsyncMock(
            side_effect=UniFiConnectionError("classic API down")
        )
        coordinator.network_client.devices.get_legacy_site_devices = AsyncMock()

        result = await coordinator._async_update_data()

        assert "device1" in result["devices"]["default"]
        coordinator.network_client.devices.get_legacy_site_devices.assert_not_called()

    @pytest.mark.asyncio
    async def test_stats_reuse_is_capped(self, coordinator: UnifiDeviceCoordinator):
        """A device whose stats keep failing stops reusing them after the cap."""
        await coordinator._async_update_data()
        assert coordinator.data["stats"]["default"]["device1"]
        coordinator.network_client.devices.get_statistics = AsyncMock(
            side_effect=UniFiTimeoutError("Timed out")
        )

        for _ in range(MAX_STATS_REUSE_POLLS):
            result = await coordinator._async_update_data()
            assert result["stats"]["default"]["device1"]

        result = await coordinator._async_update_data()
        assert result["stats"]["default"]["device1"] == {}

    @pytest.mark.asyncio
    async def test_stats_failure_count_resets(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Unsupported responses and vanished devices clear the failure count."""
        await coordinator._async_update_data()
        client = coordinator.network_client
        client.devices.get_statistics = AsyncMock(
            side_effect=UniFiTimeoutError("Timed out")
        )
        await coordinator._async_update_data()
        assert coordinator._stats_failures == {"device1": 1}

        client.devices.get_statistics = AsyncMock(
            side_effect=UniFiNotFoundError("Not found", status_code=404)
        )
        await coordinator._async_update_data()
        assert coordinator._stats_failures == {}

        coordinator._stats_failures["gone-device"] = 2
        await coordinator._async_update_data()
        assert "gone-device" not in coordinator._stats_failures

    @pytest.mark.asyncio
    async def test_port_rates_skip_reused_stats(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Reused stats don't produce a 0 rate or a doubled rate on recovery."""
        counters = {"bytes": 0}

        async def port_metrics(*_args, **_kwargs):
            return MagicMock(
                port_bytes={
                    1: MagicMock(rx_bytes=counters["bytes"], tx_bytes=counters["bytes"])
                },
                poe_ports={},
                poe_total_w=None,
            )

        coordinator.network_client.devices.get_port_metrics = AsyncMock(
            side_effect=port_metrics
        )
        coordinator.data["devices"] = {}
        working_stats = coordinator.network_client.devices.get_statistics
        clock = {"now": 1000.0}

        def rate() -> float:
            return coordinator.data["stats"]["default"]["device1"]["port_rates"][1][
                "rx_bytes_rate"
            ]

        with patch(
            "custom_components.unifi_insights.coordinators.device.time.monotonic",
            side_effect=lambda: clock["now"],
        ):
            await coordinator._async_update_data()  # first sample
            await coordinator._async_update_data()  # no time elapsed: no rate
            assert "port_rates" not in coordinator.data["stats"]["default"]["device1"]

            clock["now"] += 10
            counters["bytes"] += 1000
            await coordinator._async_update_data()
            assert rate() == 100.0

            clock["now"] += 10
            counters["bytes"] += 1000
            coordinator.network_client.devices.get_statistics = AsyncMock(
                side_effect=UniFiTimeoutError("Timed out")
            )
            await coordinator._async_update_data()
            assert rate() == 100.0  # last real rate kept, not 0

            clock["now"] += 10
            counters["bytes"] += 1000
            coordinator.network_client.devices.get_statistics = working_stats
            await coordinator._async_update_data()
            assert rate() == 100.0  # 2000 bytes over 20 s, not 200

    @pytest.mark.asyncio
    async def test_site_forbidden_fails_refresh_without_reauth(
        self,
        coordinator: UnifiDeviceCoordinator,
        caplog: pytest.LogCaptureFixture,
    ):
        """A 403 on devices fails the refresh but does not start a reauth loop."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Forbidden", status_code=403)
        )

        with pytest.raises(UpdateFailed, match="^Access forbidden for site"):
            await coordinator._async_update_data()

        assert coordinator._available is False
        # Not re-wrapped and logged as an unexpected error on every poll.
        assert "Unexpected error" not in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error",
        [
            UniFiAuthenticationError("Forbidden", status_code=403),
            UniFiNotFoundError("Not found", status_code=404),
        ],
        ids=["403", "404"],
    )
    async def test_stats_unavailable_for_one_device_is_tolerated(
        self, coordinator: UnifiDeviceCoordinator, error: Exception
    ):
        """A per-device stats error leaves that device without stats only."""
        coordinator.network_client.devices.get_statistics = AsyncMock(side_effect=error)

        result = await coordinator._async_update_data()

        assert "device1" in result["devices"]["default"]
        assert result["stats"]["default"]["device1"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_refresh_recovers_after_failure(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """last_update_success goes False on failure and True again on recovery."""
        await coordinator.async_refresh()
        assert coordinator.last_update_success is True

        working = coordinator.network_client.devices.get_all
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiConnectionError("Console rebooting")
        )
        await coordinator.async_refresh()
        assert coordinator.last_update_success is False
        assert coordinator.available is False
        assert "device1" in coordinator.data["devices"]["default"]

        coordinator.network_client.devices.get_all = working
        await coordinator.async_refresh()
        assert coordinator.last_update_success is True
        assert coordinator.available is True

    def test_get_device_existing(self, coordinator: UnifiDeviceCoordinator):
        """Test getting existing device."""
        coordinator.data["devices"] = {
            "default": {"device1": {"id": "device1", "name": "Switch"}}
        }
        result = coordinator.get_device("default", "device1")
        assert result == {"id": "device1", "name": "Switch"}

    def test_get_device_missing(self, coordinator: UnifiDeviceCoordinator):
        """Test getting missing device."""
        result = coordinator.get_device("default", "nonexistent")
        assert result is None

    def test_get_device_stats_existing(self, coordinator: UnifiDeviceCoordinator):
        """Test getting existing device stats."""
        coordinator.data["stats"] = {"default": {"device1": {"cpu": 15.2, "mem": 42.8}}}
        result = coordinator.get_device_stats("default", "device1")
        assert result == {"cpu": 15.2, "mem": 42.8}

    def test_get_device_stats_missing(self, coordinator: UnifiDeviceCoordinator):
        """Test getting missing device stats."""
        result = coordinator.get_device_stats("default", "nonexistent")
        assert result is None

    def test_get_clients(self, coordinator: UnifiDeviceCoordinator):
        """Test getting clients for a site."""
        coordinator.data["clients"] = {
            "default": {"client1": {"id": "client1", "name": "iPhone"}}
        }
        result = coordinator.get_clients("default")
        assert "client1" in result

    def test_get_clients_missing_site(self, coordinator: UnifiDeviceCoordinator):
        """Test getting clients for missing site."""
        result = coordinator.get_clients("nonexistent")
        assert result == {}

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices(
        self, hass: HomeAssistant, coordinator: UnifiDeviceCoordinator
    ):
        """Test stale device cleanup."""
        # Set up previous device IDs
        coordinator._previous_network_device_ids = {
            "default_device1",
            "default_device2",
        }

        # Current devices only have device1
        coordinator.data["devices"] = {"default": {"device1": {"id": "device1"}}}

        # Mock device registry
        with patch(
            "custom_components.unifi_insights.coordinators.device.dr.async_get"
        ) as mock_registry:
            mock_device = MagicMock()
            mock_device.id = "device_entry_id"
            set_mock_device_lookup(mock_registry.return_value, mock_device)

            coordinator._cleanup_stale_devices()

            # device2 should be marked for removal
            mock_registry.return_value.async_update_device.assert_called()

    @pytest.mark.asyncio
    async def test_process_site_empty_devices(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test site processing with empty devices list."""
        # Return empty list of devices
        coordinator.network_client.devices.get_all = AsyncMock(return_value=[])

        result = await coordinator._async_update_data()

        # Should handle empty devices gracefully
        assert result is not None
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_no_registry_match(
        self, hass: HomeAssistant, coordinator: UnifiDeviceCoordinator
    ):
        """Test cleanup when stale device is not found in registry."""
        # Set up previous device IDs
        coordinator._previous_network_device_ids = {"default_stale_device"}

        # Current devices are empty
        coordinator.data["devices"] = {"default": {}}

        # Mock device registry to return None for the device lookup
        with patch(
            "custom_components.unifi_insights.coordinators.device.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, None)

            # Should not raise even when device not in registry
            coordinator._cleanup_stale_devices()

            # async_update_device should not be called since device wasn't found
            mock_registry.return_value.async_update_device.assert_not_called()

    def test_get_device_non_dict_value(self, coordinator: UnifiDeviceCoordinator):
        """Test get_device returns None for non-dict values."""
        coordinator.data["devices"] = {"default": {"device1": "not_a_dict"}}

        result = coordinator.get_device("default", "device1")
        assert result is None

    def test_get_device_stats_non_dict_value(self, coordinator: UnifiDeviceCoordinator):
        """Test get_device_stats returns None for non-dict values."""
        coordinator.data["stats"] = {"default": {"device1": "not_a_dict"}}

        result = coordinator.get_device_stats("default", "device1")
        assert result is None

    # -------------------------------------------------------------------
    # Top-level error handler tests
    # These test the defensive error handlers in _async_update_data (lines 214-223).
    # In normal operation, these can't be reached because _process_site catches
    # all exceptions. We test them by making config_coordinator.get_site_ids raise.
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_async_update_top_level_auth_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test top-level auth error handling in _async_update_data."""
        # Make get_site_ids raise to trigger top-level handler
        coordinator.config_coordinator.get_site_ids = MagicMock(
            side_effect=UniFiAuthenticationError("Token expired")
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_async_update_top_level_connection_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test top-level connection error handling in _async_update_data."""
        coordinator.config_coordinator.get_site_ids = MagicMock(
            side_effect=UniFiConnectionError("Network unreachable")
        )

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error communicating" in str(exc_info.value)
        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_async_update_top_level_timeout_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test top-level timeout error handling in _async_update_data."""
        coordinator.config_coordinator.get_site_ids = MagicMock(
            side_effect=UniFiTimeoutError("Request timeout")
        )

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Timeout" in str(exc_info.value)
        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_async_update_top_level_response_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test top-level response error handling in _async_update_data."""
        coordinator.config_coordinator.get_site_ids = MagicMock(
            side_effect=UniFiResponseError("Bad gateway", status_code=502)
        )

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "API error" in str(exc_info.value)
        assert coordinator._available is False

    @pytest.mark.asyncio
    async def test_async_update_top_level_generic_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test top-level generic error handling in _async_update_data."""
        coordinator.config_coordinator.get_site_ids = MagicMock(
            side_effect=RuntimeError("Unexpected failure")
        )

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error updating data" in str(exc_info.value)
        assert coordinator._available is False

    def test_merge_legacy_port_data_includes_poe_good(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test _merge_legacy_port_data passes through poe_good flag."""
        device_dict: dict[str, Any] = {"macAddress": "AA:BB:CC:DD:EE:FF"}
        legacy_devices_by_mac: dict[str, dict[str, Any]] = {
            "aa:bb:cc:dd:ee:ff": {
                "port_table": [
                    {
                        "port_idx": 1,
                        "up": True,
                        "port_poe": True,
                        "poe_enable": True,
                        "poe_power": "8.50",
                        "poe_good": True,
                    },
                    {
                        "port_idx": 2,
                        "up": True,
                        "port_poe": True,
                        "poe_enable": True,
                        "poe_power": "0.00",
                        "poe_good": False,
                    },
                    {
                        "port_idx": 3,
                        "up": True,
                        "port_poe": False,
                    },
                ]
            }
        }

        UnifiDeviceCoordinator._merge_legacy_port_data(
            device_dict, legacy_devices_by_mac
        )

        ports = device_dict.get("ports", [])
        assert len(ports) == 3

        port1 = next(p for p in ports if p["port_idx"] == 1)
        assert port1["poe"]["good"] is True
        assert port1["poe"]["enabled"] is True
        assert port1["poe"]["power"] == "8.50"

        port2 = next(p for p in ports if p["port_idx"] == 2)
        assert port2["poe"]["good"] is False
        assert port2["poe"]["enabled"] is True

        port3 = next(p for p in ports if p["port_idx"] == 3)
        assert "poe" not in port3

    def test_merge_legacy_port_data_skips_port_without_port_idx(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """A port_table entry without port_idx is dropped, not appended."""
        device_dict: dict[str, Any] = {"macAddress": "AA:BB:CC:DD:EE:FF"}
        legacy_devices_by_mac: dict[str, dict[str, Any]] = {
            "aa:bb:cc:dd:ee:ff": {
                "port_table": [
                    {"port_idx": 1, "up": True},
                    {"up": True, "name": "no port_idx"},
                ]
            }
        }

        UnifiDeviceCoordinator._merge_legacy_port_data(
            device_dict, legacy_devices_by_mac
        )

        ports = device_dict.get("ports", [])
        assert len(ports) == 1
        assert ports[0]["port_idx"] == 1


# ============================================================================
# UnifiProtectCoordinator Tests
# ============================================================================


class TestUnifiProtectCoordinator:
    """Tests for UnifiProtectCoordinator."""

    @pytest.fixture
    async def coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> AsyncGenerator[UnifiProtectCoordinator]:
        """Create a protect coordinator for testing, shut down on teardown.

        Was a plain (non-yield) fixture with no teardown at all - this
        class constructs `UnifiProtectCoordinator` directly rather than
        going through config-entry setup/unload, so nothing ever cancelled
        the sensor-reconcile timer, the three tracked sensor background
        tasks (`_sensor_refresh_task`/`_sensor_reconcile_task`/
        `_sensor_reconnect_task`), or shut down the
        `_sensor_reconnect_debouncer`'s trailing-edge timer that a test
        left pending. `async_shutdown()` (see coordinators/protect.py)
        cancels exactly those per-test - it is hygiene for this test file's
        own per-test coordinator instances, not a fix for a leak or a
        regression guard: measured via a real
        `entry._async_process_on_unload(hass)` reload-cycle probe, the
        `EVENT_HOMEASSISTANT_STOP` listener wrapped in
        `entry.async_on_unload` releases its coordinator on unload
        regardless of whether this fixture calls `async_shutdown()`, and
        the full 286-test file passes unmodified even with this fixture
        reverted to a plain non-yield fixture.
        """
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        coord = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        yield coord
        await coord.async_shutdown()

    @pytest.fixture
    async def coordinator_no_protect(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> AsyncGenerator[UnifiProtectCoordinator]:
        """Create a protect coordinator without protect client, shut down on teardown.

        See `coordinator` above - same per-test cleanup, this fixture just
        omits the `protect_client`.
        """
        network_client = _create_mock_network_client()
        coord = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
        )
        yield coord
        await coord.async_shutdown()

    def test_initialization(self, coordinator: UnifiProtectCoordinator):
        """Test coordinator initialization."""
        assert coordinator.name == f"{DOMAIN}_protect"
        assert coordinator.update_interval == SCAN_INTERVAL_PROTECT
        assert "cameras" in coordinator.data
        assert "lights" in coordinator.data
        assert "sensors" in coordinator.data
        assert "nvrs" in coordinator.data
        assert "chimes" in coordinator.data
        assert "viewers" in coordinator.data
        assert "liveviews" in coordinator.data
        assert "events" in coordinator.data

    def test_websocket_state_initialized(self, coordinator: UnifiProtectCoordinator):
        """Test WebSocket state is initialized but not started at construction."""
        assert coordinator.websocket_task is None
        assert coordinator.events_websocket_task is None
        assert coordinator._protect_websocket is coordinator.protect_client.websocket

    def test_websocket_state_without_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test WebSocket state without a protect client."""
        assert coordinator_no_protect.protect_client is None
        assert coordinator_no_protect._protect_websocket is None
        assert coordinator_no_protect.websocket_task is None
        assert coordinator_no_protect.events_websocket_task is None

    @pytest.mark.asyncio
    async def test_async_start_websocket_without_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test async_start_websocket returns early without a protect client."""
        await coordinator_no_protect.async_start_websocket()
        assert coordinator_no_protect.websocket_task is None

    @pytest.mark.asyncio
    async def test_async_start_websocket_success(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test async_start_websocket resolves host_id and starts both the
        devices and events subscriptions (see task 1: the missing events
        subscription is the root cause of motion detection never firing).

        Each subscription is registered with its OWN connection-state
        callback (review finding 1: a single shared callback couldn't tell
        the caller which subscription actually transitioned, which is what
        made a devices-only reconnect look identical to a full recovery).
        """
        coordinator.protect_client.get_host_id = AsyncMock(return_value="nvr1")
        coordinator._protect_websocket.subscribe_with_callback = AsyncMock()

        await coordinator.async_start_websocket()

        assert coordinator.websocket_task is not None
        assert coordinator.events_websocket_task is not None
        coordinator.protect_client.get_host_id.assert_awaited_once()
        await coordinator.websocket_task
        await coordinator.events_websocket_task

        coordinator._protect_websocket.subscribe_with_callback.assert_any_await(
            "nvr1",
            coordinator._site_id,
            "devices",
            coordinator._on_websocket_message,
            reconnect=True,
            on_connection_state_change=coordinator._on_devices_connection_state_change,
        )
        coordinator._protect_websocket.subscribe_with_callback.assert_any_await(
            "nvr1",
            coordinator._site_id,
            "events",
            coordinator._on_websocket_event_message,
            reconnect=True,
            on_connection_state_change=coordinator._on_events_connection_state_change,
        )
        assert coordinator._protect_websocket.subscribe_with_callback.await_count == 2

    @pytest.mark.asyncio
    async def test_async_start_websocket_already_running(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test async_start_websocket is a no-op if already running."""
        existing_task = asyncio.get_event_loop().create_future()
        coordinator.websocket_task = existing_task  # type: ignore[assignment]
        coordinator.protect_client.get_host_id = AsyncMock(return_value="nvr1")

        await coordinator.async_start_websocket()

        coordinator.protect_client.get_host_id.assert_not_called()
        assert coordinator.websocket_task is existing_task
        existing_task.set_result(None)

    @pytest.mark.asyncio
    async def test_async_start_websocket_host_id_failure(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test async_start_websocket swallows host_id resolution failures."""
        coordinator.protect_client.get_host_id = AsyncMock(
            side_effect=Exception("no NVR")
        )

        # Should not raise - WebSocket is additive, polling stays the fallback.
        await coordinator.async_start_websocket()

        assert coordinator.websocket_task is None
        assert coordinator.events_websocket_task is None

    def test_on_websocket_message_top_level(self, coordinator: UnifiProtectCoordinator):
        """Test the WS message adapter with fields at the top level."""
        coordinator._on_websocket_message(
            {"modelKey": "sensor", "id": "sensor3", "isOpened": True}
        )

        assert coordinator.data["sensors"]["sensor3"]["isOpened"] is True

    def test_on_websocket_message_nested_payload(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the WS message adapter with fields nested under 'payload'."""
        coordinator._on_websocket_message(
            {"payload": {"modelKey": "sensor", "id": "sensor4", "isOpened": False}}
        )

        assert coordinator.data["sensors"]["sensor4"]["isOpened"] is False

    def test_on_websocket_message_item_wrapper(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the WS message adapter with fields nested under 'item'.

        Confirmed live against hardware 2026-08-12: local-console update
        frames use {"type": "update", "item": {...}}, not top-level fields.
        """
        coordinator._on_websocket_message(
            {
                "type": "update",
                "item": {"modelKey": "sensor", "id": "sensor9", "isOpened": True},
            }
        )

        assert coordinator.data["sensors"]["sensor9"]["isOpened"] is True

    def test_on_websocket_message_snake_case_model_key(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the WS message adapter accepts snake_case model_key."""
        coordinator._on_websocket_message({"model_key": "light", "id": "light3"})

        assert "light3" in coordinator.data["lights"]

    def test_on_websocket_message_missing_model_key(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test the WS message adapter warns and drops unparseable messages."""
        with caplog.at_level(logging.WARNING):
            coordinator._on_websocket_message({"id": "sensor5"})

        assert "missing modelKey" in caplog.text
        assert "sensor5" not in coordinator.data["sensors"]

    def test_on_websocket_message_not_a_dict(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test the WS message adapter warns on non-dict payloads."""
        with caplog.at_level(logging.WARNING):
            coordinator._on_websocket_message("not-a-dict")  # type: ignore[arg-type]

        assert "not a JSON object" in caplog.text

    def test_on_websocket_message_action_payload_split(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the adapter merges a header/payload-split message.

        Some UniFi WebSocket surfaces split the model identity into an
        "action" header and the changed fields into "payload" (rather than
        a single flat object). The adapter must resolve modelKey/id and the
        field dict independently instead of picking one container and
        giving up, or a message shaped this way would silently drop every
        real frame.
        """
        coordinator._on_websocket_message(
            {
                "action": {"action": "update", "modelKey": "sensor", "id": "sensor6"},
                "payload": {"isOpened": True},
            }
        )

        assert coordinator.data["sensors"]["sensor6"]["id"] == "sensor6"
        assert coordinator.data["sensors"]["sensor6"]["isOpened"] is True

    def test_on_websocket_message_model_key_without_id(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test a resolvable modelKey with no id logs at debug, not silently."""
        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_message({"modelKey": "sensor", "isOpened": True})

        assert "missing device id" in caplog.text
        assert coordinator.data["sensors"] == {}

    def test_on_websocket_message_warning_capped_after_first(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test repeated unparseable messages only WARNING once, then DEBUG."""
        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_message({"id": "sensor7"})
            caplog.clear()
            coordinator._on_websocket_message({"id": "sensor8"})

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert warning_records == []
        assert any("sensor8" in r.getMessage() for r in debug_records)

    def test_on_websocket_message_does_not_clobber_type_with_envelope_verb(
        self, coordinator: UnifiProtectCoordinator
    ):
        """The envelope's top-level "type" (the action verb) must not
        overwrite a real device "type" field on a partial update frame.

        Regression test: `containers = [payload, action, item, message]`
        included the raw envelope unconditionally, so its "type": "update"
        leaked into the merged device dict whenever `item` was a partial
        delta that didn't re-send the unchanged "type" field - clobbering
        the previously-correct hardware model string. Measured in
        production flipping back and forth 49 times in 10 minutes for
        UFP-SENSE/USL-Entry-US/USL-Environmental-US sensors.
        """
        coordinator.data["sensors"]["sensor10"] = {
            "id": "sensor10",
            "modelKey": "sensor",
            "type": "UFP-SENSE",
            "isOpened": False,
        }

        # A partial WS update: the envelope says "update", and the item
        # only carries the field that actually changed (isOpened) - real
        # Protect delta frames are not guaranteed to re-send "type".
        coordinator._on_websocket_message(
            {
                "type": "update",
                "item": {"modelKey": "sensor", "id": "sensor10", "isOpened": True},
            }
        )

        assert coordinator.data["sensors"]["sensor10"]["type"] == "UFP-SENSE"
        assert coordinator.data["sensors"]["sensor10"]["isOpened"] is True

    def test_on_websocket_message_replaces_device_dict_not_mutates_in_place(
        self, coordinator: UnifiProtectCoordinator
    ):
        """A WS update must produce a new per-device dict, not mutate the
        old one in place - in-place mutation can make HA listeners that
        hold a stale reference miss the transition (see task 4).
        """
        original = {"id": "sensor11", "modelKey": "sensor", "isOpened": False}
        coordinator.data["sensors"]["sensor11"] = original

        coordinator._on_websocket_message(
            {"modelKey": "sensor", "id": "sensor11", "isOpened": True}
        )

        assert coordinator.data["sensors"]["sensor11"] is not original
        assert original["isOpened"] is False
        assert coordinator.data["sensors"]["sensor11"]["isOpened"] is True

    @pytest.mark.asyncio
    async def test_async_stop_websocket_noop_when_never_started(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test async_stop_websocket is safe when no task was ever started.

        It still calls ProtectWebSocket.stop() unconditionally (harmless -
        it just sets a flag), but must not touch websocket_task since it's
        None.
        """
        await coordinator.async_stop_websocket()

        assert coordinator.websocket_task is None

    @pytest.mark.asyncio
    async def test_async_stop_websocket_stops_and_awaits_real_task(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test async_stop_websocket stops the socket and awaits BOTH real
        tasks (devices and events - task 1 requires both to be stopped and
        awaited, mirroring the existing devices-only teardown ordering).
        """
        coordinator.protect_client.get_host_id = AsyncMock(return_value="nvr1")

        async def _run_forever(*_args, **_kwargs):
            await asyncio.sleep(3600)

        coordinator._protect_websocket.subscribe_with_callback = AsyncMock(
            side_effect=_run_forever
        )
        await coordinator.async_start_websocket()
        devices_task = coordinator.websocket_task
        events_task = coordinator.events_websocket_task
        assert devices_task is not None
        assert events_task is not None
        assert not devices_task.done()
        assert not events_task.done()

        await coordinator.async_stop_websocket()

        coordinator._protect_websocket.stop.assert_called_once()
        assert devices_task.done()
        assert events_task.done()

    @pytest.mark.asyncio
    async def test_async_update_data_success(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test successful data fetch."""
        result = await coordinator._async_update_data()

        assert "cameras" in result
        assert "camera1" in result["cameras"]
        assert "lights" in result
        assert "light1" in result["lights"]
        assert "sensors" in result
        assert "sensor1" in result["sensors"]
        assert "nvrs" in result
        assert "nvr1" in result["nvrs"]
        assert "chimes" in result
        assert "chime1" in result["chimes"]
        assert "viewers" in result
        assert "viewer1" in result["viewers"]
        assert "liveviews" in result
        assert "liveview1" in result["liveviews"]
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test data fetch without protect client."""
        result = await coordinator_no_protect._async_update_data()

        # Should return empty data
        assert result["cameras"] == {}
        assert result["lights"] == {}

    @pytest.mark.asyncio
    async def test_async_update_data_sensors_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with sensors error (should not fail)."""
        coordinator.protect_client.sensors.get_all = AsyncMock(
            side_effect=Exception("Sensors failed")
        )

        result = await coordinator._async_update_data()

        # Other devices should still be fetched
        assert "camera1" in result["cameras"]
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_nvr_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with NVR error (should not fail)."""
        coordinator.protect_client.nvr.get = AsyncMock(
            side_effect=Exception("NVR failed")
        )

        result = await coordinator._async_update_data()

        # Other devices should still be fetched
        assert "camera1" in result["cameras"]
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_chimes_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with chimes error (should not fail)."""
        coordinator.protect_client.chimes.get_all = AsyncMock(
            side_effect=Exception("Chimes failed")
        )

        result = await coordinator._async_update_data()

        # Other devices should still be fetched
        assert "camera1" in result["cameras"]

    @pytest.mark.asyncio
    async def test_async_update_data_viewers_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with viewers error (should not fail)."""
        coordinator.protect_client.viewers.get_all = AsyncMock(
            side_effect=Exception("Viewers failed")
        )

        result = await coordinator._async_update_data()

        # Other devices should still be fetched
        assert "camera1" in result["cameras"]

    @pytest.mark.asyncio
    async def test_async_update_data_liveviews_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with liveviews error (should not fail)."""
        coordinator.protect_client.liveviews.get_all = AsyncMock(
            side_effect=Exception("Liveviews failed")
        )

        result = await coordinator._async_update_data()

        # Other devices should still be fetched
        assert "camera1" in result["cameras"]

    @pytest.mark.asyncio
    async def test_async_update_data_auth_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with auth error."""
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_connection_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a sustained connection error eventually fails the poll.

        The first MAX_CONSECUTIVE_EMPTY_FETCHES polls are absorbed so a single
        blipped endpoint does not take every Protect entity unavailable; past
        that window the error propagates and the coordinator reports failure.
        """
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiConnectionError("Connection refused")
        )

        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._async_update_data()

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    def test_handle_device_update_camera(self, coordinator: UnifiProtectCoordinator):
        """Test handling camera device update."""
        coordinator._handle_device_update(
            "camera", {"id": "camera2", "name": "Back Camera"}
        )

        assert "camera2" in coordinator.data["cameras"]
        assert coordinator.data["cameras"]["camera2"]["name"] == "Back Camera"

    def test_handle_device_update_light(self, coordinator: UnifiProtectCoordinator):
        """Test handling light device update."""
        coordinator._handle_device_update(
            "light", {"id": "light2", "name": "Porch Light"}
        )

        assert "light2" in coordinator.data["lights"]

    def test_handle_device_update_sensor(self, coordinator: UnifiProtectCoordinator):
        """Test handling sensor device update."""
        coordinator._handle_device_update(
            "sensor", {"id": "sensor2", "name": "Window Sensor"}
        )

        assert "sensor2" in coordinator.data["sensors"]

    def test_handle_device_update_nvr(self, coordinator: UnifiProtectCoordinator):
        """Test handling NVR device update."""
        coordinator._handle_device_update("nvr", {"id": "nvr2", "name": "NVR 2"})

        assert "nvr2" in coordinator.data["nvrs"]

    def test_handle_device_update_viewer(self, coordinator: UnifiProtectCoordinator):
        """Test handling viewer device update."""
        coordinator._handle_device_update(
            "viewer", {"id": "viewer2", "name": "Viewport 2"}
        )

        assert "viewer2" in coordinator.data["viewers"]

    def test_handle_device_update_chime(self, coordinator: UnifiProtectCoordinator):
        """Test handling chime device update."""
        coordinator._handle_device_update("chime", {"id": "chime2", "name": "Chime 2"})

        assert "chime2" in coordinator.data["chimes"]

    def test_handle_device_update_no_id(self, coordinator: UnifiProtectCoordinator):
        """Test handling device update without ID."""
        coordinator._handle_device_update("camera", {"name": "No ID Camera"})

        # Should not add device without ID
        assert len(coordinator.data["cameras"]) == 0

    def test_handle_event_update_motion(self, coordinator: UnifiProtectCoordinator):
        """Test handling motion event."""
        # First add a camera
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._handle_event_update(
            "motion",
            {
                "id": "event1",
                "device": "camera1",
                "start": 1234567890,
                "end": None,
            },
        )

        assert "motion" in coordinator.data["events"]
        assert coordinator.data["cameras"]["camera1"]["lastMotionStart"] == 1234567890
        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is None

    def test_handle_event_update_smart_detect(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test handling smart detection event."""
        # First add a camera
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._handle_event_update(
            "smartDetectZone",
            {
                "id": "event2",
                "device": "camera1",
                "smartDetectTypes": ["person", "vehicle"],
                "start": 1234567890,
                "end": None,
            },
        )

        assert coordinator.data["cameras"]["camera1"]["lastSmartDetectTypes"] == [
            "person",
            "vehicle",
        ]

    def test_handle_event_update_doorbell_ring(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test handling doorbell ring event."""
        # First add a camera
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Doorbell"}

        coordinator._handle_event_update(
            "ring",
            {
                "id": "event3",
                "device": "camera1",
                "start": 1234567890,
                "end": None,
            },
        )

        assert coordinator.data["cameras"]["camera1"]["lastRingStart"] == 1234567890
        assert coordinator.data["cameras"]["camera1"]["lastRingEnd"] is None

    def test_handle_event_update_light_motion(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test handling light motion event."""
        # First add a light
        coordinator.data["lights"]["light1"] = {"id": "light1", "name": "Test"}

        coordinator._handle_event_update(
            "motion",
            {
                "id": "event4",
                "device": "light1",
                "start": 1234567890,
                "end": None,
            },
        )

        assert coordinator.data["lights"]["light1"]["lastMotionStart"] == 1234567890

    def test_handle_event_update_no_id(self, coordinator: UnifiProtectCoordinator):
        """Test handling event without ID."""
        initial_events = dict(coordinator.data["events"])
        coordinator._handle_event_update("motion", {"device": "camera1"})

        # Events should not change without event ID
        assert coordinator.data["events"] == initial_events

    def test_get_camera_existing(self, coordinator: UnifiProtectCoordinator):
        """Test getting existing camera."""
        coordinator.data["cameras"] = {"camera1": {"id": "camera1", "name": "Test"}}
        result = coordinator.get_camera("camera1")
        assert result == {"id": "camera1", "name": "Test"}

    def test_get_camera_missing(self, coordinator: UnifiProtectCoordinator):
        """Test getting missing camera."""
        result = coordinator.get_camera("nonexistent")
        assert result is None

    def test_get_light_existing(self, coordinator: UnifiProtectCoordinator):
        """Test getting existing light."""
        coordinator.data["lights"] = {"light1": {"id": "light1", "name": "Test"}}
        result = coordinator.get_light("light1")
        assert result == {"id": "light1", "name": "Test"}

    def test_get_light_missing(self, coordinator: UnifiProtectCoordinator):
        """Test getting missing light."""
        result = coordinator.get_light("nonexistent")
        assert result is None

    def test_get_sensor_existing(self, coordinator: UnifiProtectCoordinator):
        """Test getting existing sensor."""
        coordinator.data["sensors"] = {"sensor1": {"id": "sensor1", "name": "Test"}}
        result = coordinator.get_sensor("sensor1")
        assert result == {"id": "sensor1", "name": "Test"}

    def test_get_sensor_missing(self, coordinator: UnifiProtectCoordinator):
        """Test getting missing sensor."""
        result = coordinator.get_sensor("nonexistent")
        assert result is None

    def test_get_nvr_existing(self, coordinator: UnifiProtectCoordinator):
        """Test getting existing NVR."""
        coordinator.data["nvrs"] = {"nvr1": {"id": "nvr1", "name": "Test"}}
        result = coordinator.get_nvr("nvr1")
        assert result == {"id": "nvr1", "name": "Test"}

    def test_get_nvr_missing(self, coordinator: UnifiProtectCoordinator):
        """Test getting missing NVR."""
        result = coordinator.get_nvr("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test stale device cleanup."""
        # Set up previous device IDs
        coordinator._previous_protect_device_ids = {
            "cameras": {"camera1", "camera2"},
            "lights": set(),
            "sensors": set(),
            "nvrs": set(),
            "viewers": set(),
            "chimes": set(),
        }

        # Current cameras only have camera1
        coordinator.data["cameras"] = {"camera1": {"id": "camera1"}}

        # Mock device registry
        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            mock_device = MagicMock()
            mock_device.id = "device_entry_id"
            set_mock_device_lookup(mock_registry.return_value, mock_device)

            # Removal waits out the MAX_CONSECUTIVE_MISSING_POLLS grace window.
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS + 1):
                coordinator._cleanup_stale_devices()

            # camera2 should be marked for removal
            mock_registry.return_value.async_update_device.assert_called()

    def test_websocket_construction_does_not_start_task(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test constructing the coordinator never starts the WebSocket task.

        Starting requires an await (to resolve host_id), so it must happen via
        async_start_websocket(), not as a side effect of __init__.
        """
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        assert coordinator.websocket_task is None

    def test_handle_event_update_unknown_device(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test handling event for unknown device - no device_id match."""
        # Don't add any cameras/lights/sensors
        coordinator.data["cameras"] = {}
        coordinator.data["lights"] = {}

        # Event with device_id that doesn't match any known device type
        coordinator._handle_event_update(
            "motion",
            {
                "id": "event_unknown",
                "device": "unknown_device",
                "start": 1234567890,
                "end": None,
            },
        )

        # Events should still be stored
        assert "motion" in coordinator.data["events"]
        assert "event_unknown" in coordinator.data["events"]["motion"]

    def test_handle_event_update_no_device_id(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test handling event without device field."""
        coordinator._handle_event_update(
            "motion",
            {
                "id": "event_no_device",
                "start": 1234567890,
                "end": None,
                # No "device" field
            },
        )

        # Events should still be stored
        assert "motion" in coordinator.data["events"]
        assert "event_no_device" in coordinator.data["events"]["motion"]

    def test_handle_event_update_resolves_camera_id_field(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test device id resolution tolerates "cameraId" (models/event.py's
        actual field name), not just the invented "device" key.

        UNVALIDATED (task 3): the real `Event` model
        (api/protect/models/event.py) has no generic "device" field - only
        `camera`/`cameraId` or `sensor`/`sensorId`. Before this fix,
        `_process_event_for_device` was unreachable dead code in practice
        because it only ever looked for "device".
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._handle_event_update(
            "motion",
            {"id": "event20", "cameraId": "camera1", "start": 111, "end": None},
        )

        assert coordinator.data["cameras"]["camera1"]["lastMotionStart"] == 111

    def test_handle_event_update_smart_detect_type_alias(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the "smartDetect" event type (models/event.py's
        EventType.SMART_DETECT) is accepted alongside the original
        "smartDetectZone" comparison - UNVALIDATED (task 3) which of the
        two (or both) a real frame actually uses.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._handle_event_update(
            "smartDetect",
            {
                "id": "event21",
                "device": "camera1",
                "smartDetectTypes": ["person"],
                "start": 111,
                "end": None,
            },
        )

        assert coordinator.data["cameras"]["camera1"]["lastSmartDetectTypes"] == [
            "person"
        ]

    # -- Task 1 / 3: the "events" WebSocket subscription adapter ------------

    def test_on_websocket_event_message_item_wrapper(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the events adapter with fields nested under "item", mirroring
        the confirmed "devices" envelope shape (see _on_websocket_message).
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._on_websocket_event_message(
            {
                "type": "add",
                "item": {
                    "type": "motion",
                    "id": "event30",
                    "camera": "camera1",
                    "start": 555,
                    "end": None,
                },
            }
        )

        assert "event30" in coordinator.data["events"]["motion"]
        assert coordinator.data["cameras"]["camera1"]["lastMotionStart"] == 555
        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is None

    def test_on_websocket_event_message_flat_frame(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the events adapter with no item/payload/action wrapper - a
        flat frame's own top-level "type" is the real event type (there is
        no separate envelope to strip it from in this shape).
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._on_websocket_event_message(
            {"type": "motion", "id": "event31", "camera": "camera1", "start": 777}
        )

        assert coordinator.data["cameras"]["camera1"]["lastMotionStart"] == 777

    def test_on_websocket_event_message_not_a_dict(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test the events adapter warns and drops non-dict payloads instead
        of raising (task 3: never raise into the WS callback).
        """
        with caplog.at_level(logging.WARNING):
            coordinator._on_websocket_event_message("not-a-dict")  # type: ignore[arg-type]

        assert "not a JSON object" in caplog.text

    def test_on_websocket_event_message_missing_type_warns_once_then_debug(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test an unparseable (missing event type) frame logs WARNING once,
        then DEBUG on repeat - mirrors the devices adapter's existing cap.
        """
        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_event_message({"id": "event32"})
            caplog.clear()
            coordinator._on_websocket_event_message({"id": "event33"})

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert warning_records == []
        assert any("event33" in r.getMessage() for r in debug_records)

    def test_on_websocket_event_message_error_frame_warns_once_then_debug(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test a console error frame is reported as an error, not as a
        parse failure, and is capped the same warn-once way.
        """
        frame: dict[str, Any] = {
            "error": "Too many requests",
            "name": "TOO_MANY_REQUESTS_ERROR",
            "windowMs": 1000,
            "limit": 10,
        }

        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_event_message(dict(frame))
            first: list[logging.LogRecord] = [
                r for r in caplog.records if r.levelno == logging.WARNING
            ]
            assert any("reported an error" in r.getMessage() for r in first)
            assert not any("missing event type" in r.getMessage() for r in first)
            caplog.clear()
            coordinator._on_websocket_event_message(dict(frame))

        assert [r for r in caplog.records if r.levelno == logging.WARNING] == []
        assert any(
            "reported an error" in r.getMessage()
            for r in caplog.records
            if r.levelno == logging.DEBUG
        )

    def test_on_websocket_event_message_error_frame_keeps_parse_warning(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an error frame does not spend the unparseable-frame warning.

        The two share a stream but not a cause, so a genuinely malformed
        frame must still reach WARNING after an error frame has arrived.
        """
        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_event_message(
                {
                    "error": "Too many requests",
                    "name": "TOO_MANY_REQUESTS_ERROR",
                    "windowMs": 1000,
                    "limit": 10,
                }
            )
            caplog.clear()
            coordinator._on_websocket_event_message({"id": "event41"})

        warnings: list[logging.LogRecord] = [
            r for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any("missing event type" in r.getMessage() for r in warnings)

    def test_on_websocket_event_message_missing_id_is_dropped(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test a resolvable type with no id logs at debug and is dropped."""
        with caplog.at_level(logging.DEBUG):
            coordinator._on_websocket_event_message({"type": "motion"})

        assert "missing event id" in caplog.text
        assert coordinator.data["events"] == {}

    def test_on_websocket_event_message_never_raises_on_handler_error(
        self, coordinator: UnifiProtectCoordinator, caplog: pytest.LogCaptureFixture
    ):
        """Test an exception from `_handle_event_update` is logged and
        swallowed, not propagated into the WS callback (task 3: the events
        path has never run in production, so its schema assumptions must
        degrade safely rather than kill the reconnect loop).
        """
        with (
            patch.object(
                coordinator,
                "_handle_event_update",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.ERROR),
        ):
            coordinator._on_websocket_event_message(
                {"type": "motion", "id": "event34", "device": "camera1"}
            )

        assert "unexpected error processing" in caplog.text.lower()

    # -- Task 2: bounded auto-off for the motion/smart-detect/ring latch ----

    def test_motion_latch_survives_within_timeout(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """Test reconciliation does not clear a latch that is still young."""
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event40", "device": "camera1", "start": 1, "end": None},
        )

        freezer.tick(STALE_EVENT_TIMEOUT - timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is None

    def test_motion_latch_auto_clears_after_stale_timeout(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """CRITICAL regression test: a dropped "end" frame must not latch
        `camera_motion` ON forever - it must self-clear after
        STALE_EVENT_TIMEOUT rather than trusting event pairing alone. A
        permanently-ON motion sensor in a home security system is worse
        than one that never fires (see coordinator module docstring).
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event41", "device": "camera1", "start": 1, "end": None},
        )
        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is None

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is not None

    def test_smart_detect_latch_auto_clears_and_resets_types(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """Test a stale smart-detect latch clears lastMotionEnd AND resets
        lastSmartDetectTypes, so person/vehicle/animal detection sensors
        also turn back off rather than staying latched on a stale type.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "smartDetectZone",
            {
                "id": "event42",
                "device": "camera1",
                "smartDetectTypes": ["person"],
                "start": 1,
                "end": None,
            },
        )

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] is not None
        assert coordinator.data["cameras"]["camera1"]["lastSmartDetectTypes"] == []

    def test_smart_detect_event_tolerates_non_list_smart_detect_types(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a non-list smartDetectTypes value (unconfirmed real shape -
        see class docstring) degrades to an empty list instead of storing
        garbage or raising.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}

        coordinator._handle_event_update(
            "smartDetectZone",
            {
                "id": "event46",
                "device": "camera1",
                "smartDetectTypes": "person",  # not a list
                "start": 1,
                "end": 2,
            },
        )

        assert coordinator.data["cameras"]["camera1"]["lastSmartDetectTypes"] == []

    def test_light_motion_latch_auto_clears_after_stale_timeout(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """Test the same bounded auto-off applies to light motion latches."""
        coordinator.data["lights"]["light1"] = {"id": "light1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event43", "device": "light1", "start": 1, "end": None},
        )

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert coordinator.data["lights"]["light1"]["lastMotionEnd"] is not None

    def test_ring_latch_auto_clears_after_stale_timeout(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """Test the doorbell ring latch is bounded the same way as motion -
        it is exposed to the identical dropped-end-frame risk once the
        events stream is live.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "ring",
            {"id": "event44", "device": "camera1", "start": 1, "end": None},
        )

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert coordinator.data["cameras"]["camera1"]["lastRingEnd"] is not None

    def test_ring_latch_normal_end_event_clears_tracker(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a normal paired ring "end" event pops the ring tracker
        immediately, mirroring the motion latch's normal-clear path.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "ring",
            {"id": "event47", "device": "camera1", "start": 1, "end": None},
        )
        assert "camera1" in coordinator._camera_ring_started

        coordinator._handle_event_update(
            "ring",
            {"id": "event47", "device": "camera1", "start": 1, "end": 2},
        )

        assert coordinator.data["cameras"]["camera1"]["lastRingEnd"] == 2
        assert "camera1" not in coordinator._camera_ring_started

    def test_reconcile_stale_events_skips_tracker_for_removed_device(
        self, coordinator: UnifiProtectCoordinator, freezer
    ):
        """Test reconciliation for a stale tracker entry whose device has
        since disappeared (e.g. removed by a REST poll rebuild) just drops
        the tracker entry instead of raising or recreating the device.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event48", "device": "camera1", "start": 1, "end": None},
        )
        assert "camera1" in coordinator._camera_motion_started

        # Simulate the camera vanishing (e.g. a REST poll rebuild that no
        # longer includes it) before the timeout elapses.
        del coordinator.data["cameras"]["camera1"]

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        coordinator._reconcile_stale_events()

        assert "camera1" not in coordinator._camera_motion_started
        assert "camera1" not in coordinator.data["cameras"]

    def test_motion_latch_normal_end_event_clears_without_reconciliation(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a normal paired "end" event clears the latch immediately -
        reconciliation is a safety net, not the primary clearing path.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event45", "device": "camera1", "start": 1, "end": None},
        )
        assert "camera1" in coordinator._camera_motion_started

        coordinator._handle_event_update(
            "motion",
            {"id": "event45", "device": "camera1", "start": 1, "end": 2},
        )

        assert coordinator.data["cameras"]["camera1"]["lastMotionEnd"] == 2
        assert "camera1" not in coordinator._camera_motion_started

    @pytest.mark.asyncio
    async def test_reconcile_stale_events_runs_on_periodic_poll(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the periodic REST poll also reconciles stale latches,
        rather than relying solely on event pairing.
        """
        with patch.object(coordinator, "_reconcile_stale_events") as mock_reconcile:
            await coordinator._async_update_data()

        mock_reconcile.assert_called_once()

    def test_reconcile_stale_events_runs_on_websocket_reconnect(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a WS (re)connect triggers reconciliation - a missed "end"
        frame during the outage would otherwise wait for the next poll.

        Applies per-stream (the callback now needs a `stream` argument -
        see review finding 1), but a reconnect of EITHER subscription
        still triggers reconciliation, matching the original behavior.
        """
        with patch.object(coordinator, "_reconcile_stale_events") as mock_reconcile:
            coordinator._on_websocket_connection_state_change("devices", connected=True)

        mock_reconcile.assert_called_once()

        with patch.object(
            coordinator, "_reconcile_stale_events"
        ) as mock_reconcile_disconnect:
            coordinator._on_websocket_connection_state_change(
                "devices", connected=False
            )

        mock_reconcile_disconnect.assert_not_called()

    # -- Task 5: WebSocket health signal -------------------------------------

    def test_websocket_health_initial_state(self, coordinator: UnifiProtectCoordinator):
        """Test the WS health signal starts unconnected/unknown, per stream
        and in the top-level roll-up.
        """
        assert coordinator._ws_connected is False
        assert coordinator._last_ws_message is None
        assert coordinator.websocket_health == {
            "connected": False,
            "last_message_at": None,
            "devices": {"connected": False, "last_message_at": None},
            "events": {"connected": False, "last_message_at": None},
        }

    def test_websocket_health_updates_on_devices_frame(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test an inbound devices frame marks only the devices stream
        connected - even an unparseable one, since receiving anything is
        evidence that stream's wire is alive. The top-level roll-up must
        NOT report overall-healthy off of one stream alone (review finding
        1): the events subscription is still unknown/disconnected here.
        """
        coordinator._on_websocket_message({"id": "sensor50"})

        assert coordinator.websocket_health["devices"]["connected"] is True
        assert coordinator.websocket_health["devices"]["last_message_at"] is not None
        assert coordinator.websocket_health["events"]["connected"] is False
        assert coordinator.websocket_health["events"]["last_message_at"] is None

        assert coordinator._ws_connected is False
        assert coordinator.websocket_health["connected"] is False
        # The top-level "any wire alive" timestamp still advances.
        assert coordinator._last_ws_message is not None
        assert coordinator.websocket_health["last_message_at"] is not None

    def test_websocket_health_updates_on_events_frame(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test an inbound events frame marks only the events stream
        connected, mirroring the devices case above.
        """
        coordinator._on_websocket_event_message({"id": "event51"})

        assert coordinator.websocket_health["events"]["connected"] is True
        assert coordinator.websocket_health["events"]["last_message_at"] is not None
        assert coordinator.websocket_health["devices"]["connected"] is False

        assert coordinator._ws_connected is False
        assert coordinator._last_ws_message is not None

    def test_websocket_health_reflects_connection_state_changes(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the connection-state callback drives per-stream state, and
        the top-level roll-up only reports connected once BOTH streams are.
        """
        coordinator._on_websocket_connection_state_change("devices", connected=True)
        assert coordinator.websocket_health["devices"]["connected"] is True
        assert coordinator._ws_connected is False  # events not connected yet

        coordinator._on_websocket_connection_state_change("events", connected=True)
        assert coordinator.websocket_health["events"]["connected"] is True
        assert coordinator._ws_connected is True  # both streams now connected

        coordinator._on_websocket_connection_state_change("devices", connected=False)
        assert coordinator.websocket_health["devices"]["connected"] is False
        assert coordinator.websocket_health["events"]["connected"] is True
        assert coordinator._ws_connected is False

    def test_on_devices_connection_state_change_updates_devices_stream_only(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the bound wrapper registered as the devices subscription's
        `on_connection_state_change` callback (see `async_start_websocket`)
        updates only the devices stream's health entry.
        """
        coordinator._on_devices_connection_state_change(True)

        assert coordinator.websocket_health["devices"]["connected"] is True
        assert coordinator.websocket_health["events"]["connected"] is False

    def test_on_events_connection_state_change_updates_events_stream_only(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test the bound wrapper registered as the events subscription's
        `on_connection_state_change` callback updates only the events
        stream's health entry.
        """
        coordinator._on_events_connection_state_change(True)

        assert coordinator.websocket_health["events"]["connected"] is True
        assert coordinator.websocket_health["devices"]["connected"] is False

    def test_websocket_health_detects_half_dead_pair(
        self, coordinator: UnifiProtectCoordinator
    ):
        """CRITICAL regression test (review finding 1, Major): a chatty
        devices subscription must never mask a hung/disconnected events
        subscription in `websocket_health`.

        This health signal exists specifically to catch "motion silently
        stopped working for days and nobody noticed" - that failure mode is
        exactly an NVR restart where the devices stream reconnects cleanly
        and keeps delivering frames while the events stream hangs half-open
        (no error, no close frame, just blocked forever). Before this fix,
        both subscriptions wrote the same shared `_ws_connected`/
        `_last_ws_message` fields, so devices traffic alone kept
        `websocket_health` reporting `connected: True` with a fresh
        `last_message_at` while motion detection was silently dead.
        """
        # Devices subscription connects and stays chatty.
        coordinator._on_websocket_connection_state_change("devices", connected=True)
        coordinator._on_websocket_message({"id": "sensor52", "modelKey": "sensor"})
        coordinator._on_websocket_message({"id": "sensor52", "modelKey": "sensor"})

        # Events subscription connected once, then hung - no more frames,
        # no disconnect callback (that's exactly what a half-open hang
        # looks like: nothing fires, `async for msg in ws` just blocks).
        coordinator._on_websocket_connection_state_change("events", connected=True)
        coordinator._on_websocket_event_message({"id": "event52", "type": "motion"})

        health = coordinator.websocket_health

        # Per-stream detail must show the events stream as connected but
        # its own traffic is what a human would inspect for staleness -
        # the critical assertion is that the top-level summary does not
        # paper over an events-side outage with devices-side traffic.
        assert health["devices"]["connected"] is True
        assert health["events"]["connected"] is True

        # Now the events subscription actually drops (half-open hang
        # eventually surfaces as a connection-state transition once the
        # heartbeat/reconnect logic in websocket.py notices) while devices
        # keeps flowing.
        coordinator._on_websocket_connection_state_change("events", connected=False)
        coordinator._on_websocket_message({"id": "sensor52", "modelKey": "sensor"})

        health = coordinator.websocket_health
        assert health["devices"]["connected"] is True
        assert health["events"]["connected"] is False
        # The overall roll-up must reflect the outage, not the chatty
        # devices stream alone.
        assert health["connected"] is False
        assert coordinator._ws_connected is False

    def test_cleanup_stale_devices_no_match(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test stale device cleanup when device not found in registry."""
        # Set up previous device IDs
        coordinator._previous_protect_device_ids = {
            "cameras": {"stale_camera"},
            "lights": {"stale_light"},
            "sensors": set(),
            "nvrs": set(),
            "viewers": {"stale_viewer"},
            "chimes": {"stale_chime"},
        }

        # Current data has nothing
        coordinator.data["cameras"] = {}
        coordinator.data["lights"] = {}
        coordinator.data["viewers"] = {}
        coordinator.data["chimes"] = {}

        # Mock device registry to return None (device not found)
        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, None)

            # Poll past the grace window so eviction is actually attempted,
            # then fall through both identifier patterns without a match.
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS + 1):
                coordinator._cleanup_stale_devices()

            # No device updates should happen (nothing found)
            mock_registry.return_value.async_update_device.assert_not_called()
            assert mock_device_lookup_method(
                mock_registry.return_value, coordinator.config_entry.entry_id
            ).called

    @pytest.mark.asyncio
    async def test_fetch_sensors_error(self, coordinator: UnifiProtectCoordinator):
        """Test sensor fetch handles errors gracefully."""
        coordinator.protect_client.sensors.get_all = AsyncMock(
            side_effect=Exception("Sensors error")
        )

        # Call the internal method directly
        await coordinator._fetch_sensors()

        # Should not raise, sensors should remain empty
        assert coordinator.data["sensors"] == {}

    @pytest.mark.asyncio
    async def test_fetch_sensors_preserves_cache_on_empty(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test sensor fetch preserves cached sensors across transient empty polls."""
        cached = {"sensor1": {"id": "sensor1", "state": "CONNECTED"}}
        coordinator.data["sensors"] = cached
        coordinator.protect_client.sensors.get_all = AsyncMock(return_value=[])

        # Polls 1, 2, 3 should preserve cache
        for _ in range(3):
            await coordinator._fetch_sensors()
            assert "sensor1" in coordinator.data["sensors"]

    @pytest.mark.asyncio
    async def test_fetch_sensors_clears_cache_after_max_consecutive_empty(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test sensor cache is cleared after MAX_CONSECUTIVE_EMPTY_FETCHES polls."""
        cached = {"sensor1": {"id": "sensor1", "state": "CONNECTED"}}
        coordinator.data["sensors"] = cached
        coordinator.protect_client.sensors.get_all = AsyncMock(return_value=[])

        # 4 consecutive empty polls exceeds threshold of 3
        for _ in range(4):
            await coordinator._fetch_sensors()

        assert coordinator.data["sensors"] == {}

    @pytest.mark.asyncio
    async def test_fetch_sensors_preserves_cache_on_404(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test sensor fetch preserves cached sensors across transient 404s."""
        cached = {"sensor1": {"id": "sensor1", "state": "CONNECTED"}}
        coordinator.data["sensors"] = cached
        coordinator.protect_client.sensors.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("Not Found", 404)
        )

        for _ in range(3):
            await coordinator._fetch_sensors()
            assert "sensor1" in coordinator.data["sensors"]

    @pytest.mark.asyncio
    async def test_fetch_sensors_clears_cache_after_max_consecutive_404(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test sensor cache is cleared after consecutive 404s exceed threshold."""
        cached = {"sensor1": {"id": "sensor1", "state": "CONNECTED"}}
        coordinator.data["sensors"] = cached
        coordinator.protect_client.sensors.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("Not Found", 404)
        )

        for _ in range(4):
            await coordinator._fetch_sensors()

        assert coordinator.data["sensors"] == {}

    @pytest.mark.asyncio
    async def test_fetch_sensors_404_when_no_sensors_configured(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test sensor fetch 404 leaves dict empty without error."""
        coordinator.data["sensors"] = {}
        coordinator.protect_client.sensors.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("Not Found", 404)
        )

        await coordinator._fetch_sensors()
        assert coordinator.data["sensors"] == {}

    def test_update_device_collection_handles_non_dict_existing(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test _update_device_collection handles existing data being non-dict."""
        coordinator.data["cameras"] = None  # type: ignore[assignment]
        coordinator._update_device_collection("cameras", {})
        assert coordinator.data["cameras"] == {}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("collection", "client_attr", "client_method", "fetch_method"),
        [
            ("cameras", "cameras", "get_all", "_fetch_cameras"),
            ("lights", "lights", "get_all", "_fetch_lights"),
            ("nvrs", "nvr", "get", "_fetch_nvr"),
            ("chimes", "chimes", "get_all", "_fetch_chimes"),
            ("viewers", "viewers", "get_all", "_fetch_viewers"),
        ],
    )
    async def test_fetch_endpoints_preserve_cache_on_404(
        self,
        coordinator: UnifiProtectCoordinator,
        collection: str,
        client_attr: str,
        client_method: str,
        fetch_method: str,
    ):
        """Test fetch methods handle UniFiNotFoundError (404) by preserving cache."""
        device_id = f"{collection}_1"
        cached = {device_id: {"id": device_id}}
        coordinator.data[collection] = cached
        setattr(
            getattr(coordinator.protect_client, client_attr),
            client_method,
            AsyncMock(side_effect=UniFiNotFoundError("Not Found", 404)),
        )
        await getattr(coordinator, fetch_method)()
        assert device_id in coordinator.data[collection]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("collection", ["sensors", "nvrs", "chimes", "viewers"])
    async def test_fetch_preserves_cache_across_persistent_errors(
        self,
        hass: HomeAssistant,
        coordinator: UnifiProtectCoordinator,
        collection: str,
    ):
        """Test a persistent fetch error never evicts devices or registry entries.

        An error means "we could not ask", not "the server says they are gone",
        so it must not feed the empty-response eviction counter. When it did,
        roughly two minutes of HTTP 500s cleared the collection and
        _cleanup_stale_devices then removed every device in it from the device
        registry, losing area assignments and any automation keyed on device_id.
        """
        # collection -> (protect_client attribute, its fetch method, coordinator fetch)
        endpoints = {
            "sensors": ("sensors", "get_all", "_fetch_sensors"),
            "nvrs": ("nvr", "get", "_fetch_nvr"),
            "chimes": ("chimes", "get_all", "_fetch_chimes"),
            "viewers": ("viewers", "get_all", "_fetch_viewers"),
        }
        client_attr, client_method, fetch_method = endpoints[collection]

        device_id = f"{collection}_device1"
        coordinator.data[collection] = {device_id: {"id": device_id}}
        coordinator._previous_protect_device_ids = {
            key: set()
            for key in ("cameras", "lights", "sensors", "nvrs", "viewers", "chimes")
        }
        coordinator._previous_protect_device_ids[collection] = {device_id}
        setattr(
            getattr(coordinator.protect_client, client_attr),
            client_method,
            AsyncMock(side_effect=Exception("500 Internal Server Error")),
        )

        # Well past MAX_CONSECUTIVE_EMPTY_FETCHES: errors have no threshold.
        for _ in range(6):
            await getattr(coordinator, fetch_method)()
            assert device_id in coordinator.data[collection]

        assert coordinator._consecutive_empty_fetches.get(collection, 0) == 0

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, MagicMock())
            coordinator._cleanup_stale_devices()
            mock_registry.return_value.async_update_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_nvr_missing_id_clears_cache_after_max_consecutive(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test NVR response without id is treated as empty."""
        cached = {"nvr1": {"id": "nvr1", "name": "NVR"}}
        coordinator.data["nvrs"] = cached
        mock_model = MagicMock()
        coordinator._model_to_dict = MagicMock(return_value={"name": "No ID"})
        coordinator.protect_client.nvr.get = AsyncMock(return_value=mock_model)

        for _ in range(3):
            await coordinator._fetch_nvr()
            assert "nvr1" in coordinator.data["nvrs"]

        await coordinator._fetch_nvr()
        assert coordinator.data["nvrs"] == {}

    @pytest.mark.asyncio
    async def test_fetch_cameras_preserves_cache_on_transient_empty(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera fetch preserves cache across transient empty polls."""
        cached = {"camera1": {"id": "camera1", "state": "CONNECTED"}}
        coordinator.data["cameras"] = cached
        coordinator.protect_client.cameras.get_all = AsyncMock(return_value=[])

        await coordinator._fetch_cameras()
        assert "camera1" in coordinator.data["cameras"]

    @pytest.mark.asyncio
    async def test_fetch_cameras_clears_cache_after_max_consecutive_empty(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera cache is cleared after consecutive empty polls."""
        cached = {"camera1": {"id": "camera1", "state": "CONNECTED"}}
        coordinator.data["cameras"] = cached
        coordinator.protect_client.cameras.get_all = AsyncMock(return_value=[])

        for _ in range(4):
            await coordinator._fetch_cameras()

        assert coordinator.data["cameras"] == {}

    @pytest.mark.asyncio
    async def test_fetch_lights_preserves_cache_on_transient_empty(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test light fetch preserves cached lights across transient empty responses."""
        cached = {"light1": {"id": "light1", "state": "CONNECTED"}}
        coordinator.data["lights"] = cached
        coordinator.protect_client.lights.get_all = AsyncMock(return_value=[])

        await coordinator._fetch_lights()
        assert "light1" in coordinator.data["lights"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "err",
        [
            # The session-drop the controller serves as an HTML login page.
            pytest.param(
                UniFiResponseError("Response is not JSON", status_code=200),
                id="response_error",
            ),
            pytest.param(UniFiConnectionError("Connection reset"), id="connection"),
            pytest.param(UniFiTimeoutError("Timed out"), id="timeout"),
        ],
    )
    async def test_fetch_cameras_preserves_cache_on_transient_error(
        self, coordinator: UnifiProtectCoordinator, err: Exception
    ):
        """A transient camera fetch error must not fail the whole Protect poll.

        `_fetch_cameras` runs first, so letting the error escape aborts every
        later fetcher and raises `UpdateFailed`, marking all Protect entities
        unavailable for that cycle.
        """
        cached = {"camera1": {"id": "camera1", "state": "CONNECTED"}}
        coordinator.data["cameras"] = cached
        coordinator.protect_client.cameras.get_all = AsyncMock(side_effect=err)

        await coordinator._fetch_cameras()

        assert "camera1" in coordinator.data["cameras"]

    @pytest.mark.asyncio
    async def test_fetch_lights_preserves_cache_on_transient_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """A transient light fetch error must not fail the whole Protect poll."""
        cached = {"light1": {"id": "light1", "state": "CONNECTED"}}
        coordinator.data["lights"] = cached
        coordinator.protect_client.lights.get_all = AsyncMock(
            side_effect=UniFiResponseError("Response is not JSON", status_code=200)
        )

        await coordinator._fetch_lights()

        assert "light1" in coordinator.data["lights"]

    @pytest.mark.asyncio
    async def test_fetch_cameras_transient_error_does_not_advance_eviction(
        self, coordinator: UnifiProtectCoordinator
    ):
        """A fetch error is not evidence a camera was removed, unlike an empty poll.

        An empty response clears the cache after MAX_CONSECUTIVE_EMPTY_FETCHES so
        genuinely removed devices are cleaned up. An error says nothing about the
        device set, so it must not advance that counter: errored polls followed by
        a single empty one must still preserve the cache.
        """
        cached = {"camera1": {"id": "camera1", "state": "CONNECTED"}}
        coordinator.data["cameras"] = cached
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Bad gateway", status_code=502)
        )
        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._fetch_cameras()

        # First clean poll after the outage genuinely returns no cameras.
        coordinator.protect_client.cameras.get_all = AsyncMock(return_value=[])
        await coordinator._fetch_cameras()

        assert "camera1" in coordinator.data["cameras"]

    @pytest.mark.asyncio
    async def test_sustained_camera_fetch_errors_fail_the_poll(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Preservation is bounded: a lasting outage must mark Protect unavailable.

        Serving a warm cache forever would leave every Protect entity reporting
        stale state through a controller outage, which is worse than the flapping
        the bounded window prevents.
        """
        coordinator.data["cameras"] = {"camera1": {"id": "camera1"}}
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Response is not JSON", status_code=200)
        )

        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._fetch_cameras()

        with pytest.raises(UniFiResponseError):
            await coordinator._fetch_cameras()

    @pytest.mark.asyncio
    async def test_camera_fetch_error_counter_resets_on_handled_404(
        self, coordinator: UnifiProtectCoordinator
    ):
        """A 404 is a healthy answer, so it breaks the transient-error streak.

        The endpoint replied, which is evidence the session is alive. Without
        the reset, three absorbed errors plus a 404 plus one more error would
        fail the poll on errors that were never consecutive.
        """
        coordinator.data["cameras"] = {"camera1": {"id": "camera1"}}
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._fetch_cameras()

        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("No cameras configured", 404)
        )
        await coordinator._fetch_cameras()

        # Streak was broken, so this error is the first of a new window.
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        await coordinator._fetch_cameras()

    @pytest.mark.asyncio
    async def test_light_fetch_error_counter_resets_on_handled_404(
        self, coordinator: UnifiProtectCoordinator
    ):
        """See the camera case: a handled 404 resets the light error streak."""
        coordinator.data["lights"] = {"light1": {"id": "light1"}}
        coordinator.protect_client.lights.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._fetch_lights()

        coordinator.protect_client.lights.get_all = AsyncMock(
            side_effect=UniFiNotFoundError("No lights configured", 404)
        )
        await coordinator._fetch_lights()

        coordinator.protect_client.lights.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        await coordinator._fetch_lights()

    @pytest.mark.asyncio
    async def test_camera_fetch_error_counter_resets_on_success(
        self, coordinator: UnifiProtectCoordinator
    ):
        """A recovered poll re-arms the full preservation window."""
        coordinator.data["cameras"] = {"camera1": {"id": "camera1"}}
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._fetch_cameras()

        camera = MagicMock()
        camera.model_dump = MagicMock(return_value={"id": "camera1", "name": "Cam"})
        coordinator.protect_client.cameras.get_all = AsyncMock(return_value=[camera])
        await coordinator._fetch_cameras()

        # Window is re-armed, so the next error is absorbed rather than raised.
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Blip", status_code=502)
        )
        await coordinator._fetch_cameras()

        assert "camera1" in coordinator.data["cameras"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["_fetch_cameras", "_fetch_lights"])
    async def test_fetch_propagates_auth_error(
        self, coordinator: UnifiProtectCoordinator, method: str
    ):
        """An expired key must still reach the reauth flow, not be swallowed."""
        collection = "cameras" if method == "_fetch_cameras" else "lights"
        getattr(coordinator.protect_client, collection).get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("API key expired")
        )

        with pytest.raises(UniFiAuthenticationError):
            await getattr(coordinator, method)()

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_preserves_devices_on_transient_empty(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test stale device cleanup preserves devices during transient empty poll."""
        coordinator._previous_protect_device_ids = {
            "cameras": set(),
            "lights": set(),
            "sensors": {"sensor1"},
            "nvrs": set(),
            "viewers": set(),
            "chimes": set(),
        }
        coordinator.data["sensors"] = {"sensor1": {"id": "sensor1"}}
        coordinator.protect_client.sensors.get_all = AsyncMock(return_value=[])

        # 1 transient empty fetch
        await coordinator._fetch_sensors()
        assert "sensor1" in coordinator.data["sensors"]

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            mock_device = MagicMock()
            set_mock_device_lookup(mock_registry.return_value, mock_device)
            coordinator._cleanup_stale_devices()
            mock_registry.return_value.async_update_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_removes_device_after_max_consecutive_empty(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test stale device cleanup removes devices after max empty polls."""
        coordinator._previous_protect_device_ids = {
            "cameras": set(),
            "lights": set(),
            "sensors": {"sensor1"},
            "nvrs": set(),
            "viewers": set(),
            "chimes": set(),
        }
        coordinator.data["sensors"] = {"sensor1": {"id": "sensor1"}}
        coordinator.protect_client.sensors.get_all = AsyncMock(return_value=[])

        # 4 consecutive empty polls
        for _ in range(4):
            await coordinator._fetch_sensors()

        assert coordinator.data["sensors"] == {}

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            mock_device = MagicMock()
            mock_device.id = "sensor1_entry_id"
            set_mock_device_lookup(mock_registry.return_value, mock_device)
            # Removal waits out the MAX_CONSECUTIVE_MISSING_POLLS grace window.
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS + 1):
                coordinator._cleanup_stale_devices()
            mock_registry.return_value.async_update_device.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_cameras_preserves_camera_skipped_by_validation(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test a camera dropped on a ValidationError keeps its cached entry.

        `get_all()` skips an item whose payload will not parse - typically a
        field reshaped by a Protect release - and returns the rest. That short
        list is non-empty, so the bounded empty-response guard never engages
        and the grace window only delays the loss: the skip is deterministic
        and repeats on every poll. The collection must merge instead of
        replace while the endpoint reports the result incomplete.
        """
        coordinator.data["cameras"] = {
            "camera1": {"id": "camera1", "name": "Front"},
            "camera2": {"id": "camera2", "name": "Back"},
        }
        coordinator._previous_protect_device_ids["cameras"] = {"camera1", "camera2"}

        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(
            return_value={"id": "camera1", "name": "Front"}
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )
        coordinator.protect_client.cameras.last_result_complete = False

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, MagicMock())
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS + 2):
                await coordinator._fetch_cameras()
                coordinator._cleanup_stale_devices()

            assert "camera2" in coordinator.data["cameras"]
            mock_registry.return_value.async_update_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_cameras_still_refreshes_data_when_result_incomplete(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test preserving a skipped camera does not stall the others' data.

        Merging must layer the fresh response over the cache, not fall back to
        it, or one unparseable camera would freeze every sibling's state.
        """
        coordinator.data["cameras"] = {
            "camera1": {"id": "camera1", "state": "DISCONNECTED"},
            "camera2": {"id": "camera2", "state": "CONNECTED"},
        }

        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(
            return_value={"id": "camera1", "state": "CONNECTED"}
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )
        coordinator.protect_client.cameras.last_result_complete = False

        await coordinator._fetch_cameras()

        assert coordinator.data["cameras"]["camera1"]["state"] == "CONNECTED"
        assert coordinator.data["cameras"]["camera2"]["state"] == "CONNECTED"

    @pytest.mark.asyncio
    async def test_fetch_cameras_replaces_collection_when_result_complete(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a complete response still drops cameras removed from Protect.

        The merge is scoped to incomplete results; a clean listing remains
        authoritative so genuinely unadopted cameras are cleaned up.
        """
        coordinator.data["cameras"] = {
            "camera1": {"id": "camera1"},
            "camera2": {"id": "camera2"},
        }

        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(return_value={"id": "camera1"})
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )
        coordinator.protect_client.cameras.last_result_complete = True

        await coordinator._fetch_cameras()

        assert set(coordinator.data["cameras"]) == {"camera1"}

    @pytest.mark.asyncio
    async def test_fetch_cameras_preserves_cache_when_every_camera_fails_parsing(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a schema break that drops every camera does not purge the cache.

        A Protect release reshaping a shared field fails validation for all
        cameras at once, so `get_all()` returns an empty list that looks
        exactly like "no cameras adopted". Left there, the bounded
        empty-response guard clears the collection a few polls later and hands
        every camera to `_cleanup_stale_devices`. An endpoint that reports the
        result incomplete must not advance that counter.
        """
        coordinator.data["cameras"] = {"camera1": {"id": "camera1"}}
        coordinator.protect_client.cameras.get_all = AsyncMock(return_value=[])
        coordinator.protect_client.cameras.last_result_complete = False

        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES + 3):
            await coordinator._fetch_cameras()

        assert "camera1" in coordinator.data["cameras"]
        assert coordinator._consecutive_empty_fetches["cameras"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_defers_removal_on_brief_absence(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test a device missing from one poll is not purged from the registry.

        A partial controller response - or an item that `get_all()` skipped on
        a ValidationError - drops a still-adopted device out of the collection.
        Acting on that single poll is irreversible: the registry entry, its
        area assignment and every automation keyed on device_id are lost.
        """
        coordinator._previous_protect_device_ids["cameras"] = {"cam1", "cam2"}
        coordinator.data["cameras"] = {"cam1": {"id": "cam1"}}

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, MagicMock())
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS):
                coordinator._cleanup_stale_devices()

            mock_registry.return_value.async_update_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_removes_device_after_sustained_absence(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test a device absent past the grace window is still evicted.

        Guards the other half of the deferral: a device genuinely unadopted
        from Protect must not be tracked forever just because removal is no
        longer immediate (Gold stale-device requirement).
        """
        coordinator._previous_protect_device_ids["cameras"] = {"cam1", "cam2"}
        coordinator.data["cameras"] = {"cam1": {"id": "cam1"}}
        mock_device = MagicMock()
        mock_device.id = "registry_id_cam2"

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, mock_device)
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS + 1):
                coordinator._cleanup_stale_devices()

            mock_registry.return_value.async_update_device.assert_called_once_with(
                device_id="registry_id_cam2",
                remove_config_entry_id=coordinator.config_entry.entry_id,
            )

    @pytest.mark.asyncio
    async def test_cleanup_stale_devices_resets_absence_counter_on_return(
        self, hass: HomeAssistant, coordinator: UnifiProtectCoordinator
    ):
        """Test a device that reappears restarts its grace window.

        Without a reset, intermittent partial responses would accumulate
        across unrelated polls and eventually evict a healthy device.
        """
        coordinator._previous_protect_device_ids["cameras"] = {"cam1", "cam2"}

        with patch(
            "custom_components.unifi_insights.coordinators.protect.dr.async_get"
        ) as mock_registry:
            set_mock_device_lookup(mock_registry.return_value, MagicMock())
            # Absent for one poll short of the threshold.
            coordinator.data["cameras"] = {"cam1": {"id": "cam1"}}
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS):
                coordinator._cleanup_stale_devices()

            # cam2 comes back, then goes missing again for the same span.
            coordinator.data["cameras"] = {
                "cam1": {"id": "cam1"},
                "cam2": {"id": "cam2"},
            }
            coordinator._cleanup_stale_devices()

            coordinator.data["cameras"] = {"cam1": {"id": "cam1"}}
            for _ in range(MAX_CONSECUTIVE_MISSING_POLLS):
                coordinator._cleanup_stale_devices()

            mock_registry.return_value.async_update_device.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_nvr_error(self, coordinator: UnifiProtectCoordinator):
        """Test NVR fetch handles errors gracefully."""
        coordinator.protect_client.nvr.get = AsyncMock(
            side_effect=Exception("NVR error")
        )

        # Call the internal method directly
        await coordinator._fetch_nvr()

        # Should not raise, nvrs should remain empty
        assert coordinator.data["nvrs"] == {}

    @pytest.mark.asyncio
    async def test_fetch_cameras_processes_smart_detect_types(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera fetch extracts smartDetectTypes from featureFlags."""
        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(
            return_value={
                "id": "camera1",
                "name": "Front Camera",
                "featureFlags": {
                    "smartDetectTypes": ["person", "vehicle"],
                },
                "isPtz": True,
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )

        await coordinator._fetch_cameras()

        assert "camera1" in coordinator.data["cameras"]
        assert coordinator.data["cameras"]["camera1"]["smartDetectTypes"] == [
            "person",
            "vehicle",
        ]
        assert coordinator.data["cameras"]["camera1"]["hasPtz"] is True

    @pytest.mark.asyncio
    async def test_fetch_cameras_non_dict_feature_flags(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera fetch handles non-dict featureFlags."""
        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(
            return_value={
                "id": "camera2",
                "name": "Camera 2",
                "featureFlags": "not_a_dict",  # Invalid type
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )

        await coordinator._fetch_cameras()

        assert "camera2" in coordinator.data["cameras"]
        # Should default to empty list when featureFlags is not a dict
        assert coordinator.data["cameras"]["camera2"]["smartDetectTypes"] == []

    @pytest.mark.asyncio
    async def test_fetch_cameras_no_feature_flags(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera fetch handles missing featureFlags."""
        mock_camera = MagicMock()
        mock_camera.model_dump = MagicMock(
            return_value={
                "id": "camera3",
                "name": "Camera 3",
                # No featureFlags key
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )

        await coordinator._fetch_cameras()

        assert "camera3" in coordinator.data["cameras"]
        assert coordinator.data["cameras"]["camera3"]["smartDetectTypes"] == []

    @pytest.mark.asyncio
    async def test_fetch_cameras_rebuild_drops_motion_tracker_for_fieldless_camera(
        self,
        coordinator: UnifiProtectCoordinator,
        freezer,
        caplog: pytest.LogCaptureFixture,
    ):
        """Test a `_fetch_cameras()` rebuild pops the in-progress motion
        latch tracker for a camera whose rebuilt dict carries no
        `lastMotionStart` field, instead of leaving it to be "discovered"
        stale 5 minutes later.

        Regression test (review finding 2): the REST camera model never
        carries `lastMotionStart`/`lastMotionEnd` (those are only ever
        written by a paired WebSocket "start"/"end" event - see
        `_apply_motion_event`). Before this fix, a `_fetch_cameras()`
        rebuild silently cleared the latch's own fields without popping the
        tracker entry, so on virtually every real motion event
        `_reconcile_stale_events` would later "discover" the orphaned
        tracker and log a false "missed 'end' event?" warning for motion
        detection that was already correctly cleared ~4m30s earlier by the
        REST poll - flooding INFO logs during exactly the window someone is
        watching them to confirm a deploy worked.
        """
        # A live event-derived latch: WebSocket saw a "start" with no "end"
        # yet, so the tracker is armed - mirrors real motion detection.
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "motion",
            {"id": "event49", "device": "camera1", "start": 1, "end": None},
        )
        assert "camera1" in coordinator._camera_motion_started
        assert coordinator.data["cameras"]["camera1"]["lastMotionStart"] == 1

        # The mock protect client's default camera fixture returns
        # "camera1" but with no lastMotionStart/lastMotionEnd fields at all
        # (matching the real REST model - see api/protect/models/camera.py).
        await coordinator._fetch_cameras()

        assert "lastMotionStart" not in coordinator.data["cameras"]["camera1"]
        assert "camera1" not in coordinator._camera_motion_started

        # 5+ minutes later, the periodic reconciliation safety net must not
        # find (and log about) a tracker that no longer exists.
        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        with caplog.at_level(logging.INFO):
            coordinator._reconcile_stale_events()

        assert "missed 'end' event" not in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_cameras_rebuild_drops_ring_tracker_for_fieldless_camera(
        self,
        coordinator: UnifiProtectCoordinator,
        freezer,
        caplog: pytest.LogCaptureFixture,
    ):
        """Test the identical fix also applies to the doorbell ring latch.

        The ring latch is stored on the same per-camera dict that
        `_fetch_cameras()` wholesale-replaces, so it is exposed to the
        identical dropped-tracker risk as the motion latch above.
        """
        coordinator.data["cameras"]["camera1"] = {"id": "camera1", "name": "Test"}
        coordinator._handle_event_update(
            "ring",
            {"id": "event50", "device": "camera1", "start": 1, "end": None},
        )
        assert "camera1" in coordinator._camera_ring_started

        await coordinator._fetch_cameras()

        assert "lastRingStart" not in coordinator.data["cameras"]["camera1"]
        assert "camera1" not in coordinator._camera_ring_started

        freezer.tick(STALE_EVENT_TIMEOUT + timedelta(seconds=1))
        with caplog.at_level(logging.INFO):
            coordinator._reconcile_stale_events()

        assert "missed 'end' event" not in caplog.text

    @pytest.mark.asyncio
    async def test_async_update_data_response_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a sustained response error eventually fails the poll.

        The first MAX_CONSECUTIVE_EMPTY_FETCHES polls are absorbed so a single
        blipped endpoint does not take every Protect entity unavailable; past
        that window the error propagates and the coordinator reports failure.
        """
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Invalid response", status_code=400)
        )

        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._async_update_data()

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_timeout_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test a sustained timeout error eventually fails the poll.

        The first MAX_CONSECUTIVE_EMPTY_FETCHES polls are absorbed so a single
        blipped endpoint does not take every Protect entity unavailable; past
        that window the error propagates and the coordinator reports failure.
        """
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiTimeoutError("Request timed out")
        )

        for _ in range(MAX_CONSECUTIVE_EMPTY_FETCHES):
            await coordinator._async_update_data()

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_generic_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with generic error."""
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=Exception("Unknown error")
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_fetch_lights_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test light fetch returns early without protect client."""
        await coordinator_no_protect._fetch_lights()
        # Should not raise, lights remain empty
        assert coordinator_no_protect.data["lights"] == {}

    @pytest.mark.asyncio
    async def test_fetch_sensors_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test sensor fetch returns early without protect client."""
        await coordinator_no_protect._fetch_sensors()
        assert coordinator_no_protect.data["sensors"] == {}

    @pytest.mark.asyncio
    async def test_fetch_nvr_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test NVR fetch returns early without protect client."""
        await coordinator_no_protect._fetch_nvr()
        assert coordinator_no_protect.data["nvrs"] == {}

    @pytest.mark.asyncio
    async def test_fetch_chimes_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test chime fetch returns early without protect client."""
        await coordinator_no_protect._fetch_chimes()
        assert coordinator_no_protect.data["chimes"] == {}

    @pytest.mark.asyncio
    async def test_fetch_viewers_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test viewer fetch returns early without protect client."""
        await coordinator_no_protect._fetch_viewers()
        assert coordinator_no_protect.data["viewers"] == {}

    @pytest.mark.asyncio
    async def test_fetch_liveviews_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test liveview fetch returns early without protect client."""
        await coordinator_no_protect._fetch_liveviews()
        assert coordinator_no_protect.data["liveviews"] == {}

    @pytest.mark.asyncio
    async def test_fetch_cameras_no_protect_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test camera fetch returns early without protect client."""
        await coordinator_no_protect._fetch_cameras()
        assert coordinator_no_protect.data["cameras"] == {}


# ============================================================================
# UnifiFacadeCoordinator Tests
# ============================================================================


class TestUnifiFacadeCoordinator:
    """Tests for UnifiFacadeCoordinator."""

    @pytest.fixture
    def config_coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiConfigCoordinator:
        """Create a config coordinator."""
        network_client = _create_mock_network_client()
        coord = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
        )
        coord.data = {
            "sites": {"default": {"id": "default", "name": "Default"}},
            "wifi": {"default": {"wifi1": {"id": "wifi1"}}},
            "firewall_rules": {
                "default": {"rule1": {"id": "rule1", "name": "Block Instagram"}}
            },
            "network_info": {},
        }
        return coord

    @pytest.fixture
    def device_coordinator(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
    ) -> UnifiDeviceCoordinator:
        """Create a device coordinator."""
        network_client = _create_mock_network_client()
        coord = UnifiDeviceCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
        )
        coord.data = {
            "devices": {"default": {"device1": {"id": "device1"}}},
            "clients": {"default": {"client1": {"id": "client1"}}},
            "stats": {"default": {"device1": {"cpu": 10}}},
            "vouchers": {},
            "last_update": None,
        }
        return coord

    @pytest.fixture
    def protect_coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiProtectCoordinator:
        """Create a protect coordinator."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        coord = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        coord.data = {
            "cameras": {"camera1": {"id": "camera1"}},
            "lights": {},
            "sensors": {},
            "nvrs": {},
            "viewers": {},
            "chimes": {},
            "liveviews": {},
            "protect_info": {},
            "events": {},
            "last_update": None,
        }
        return coord

    @pytest.fixture
    async def facade_coordinator(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
        protect_coordinator: UnifiProtectCoordinator,
    ) -> AsyncGenerator[UnifiFacadeCoordinator]:
        """Create a facade coordinator."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        coordinator = UnifiFacadeCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
            device_coordinator=device_coordinator,
            protect_coordinator=protect_coordinator,
        )
        yield coordinator
        # Shut down so refresh timers scheduled by the facade's listeners on
        # the sub-coordinators don't linger past the test.
        await coordinator.async_shutdown()
        await config_coordinator.async_shutdown()
        await device_coordinator.async_shutdown()
        await protect_coordinator.async_shutdown()

    @pytest.fixture
    async def facade_coordinator_no_protect(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
    ) -> AsyncGenerator[UnifiFacadeCoordinator]:
        """Create a facade coordinator without protect."""
        network_client = _create_mock_network_client()
        coordinator = UnifiFacadeCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
            device_coordinator=device_coordinator,
            protect_coordinator=None,
        )
        yield coordinator
        await coordinator.async_shutdown()
        await config_coordinator.async_shutdown()
        await device_coordinator.async_shutdown()

    def test_initialization(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test facade coordinator initialization."""
        assert facade_coordinator.name == f"{DOMAIN}_facade"

    def test_aggregate_data(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test data aggregation."""
        facade_coordinator._aggregate_data()

        # Check config coordinator data
        assert "sites" in facade_coordinator.data
        assert "default" in facade_coordinator.data["sites"]
        assert "wifi" in facade_coordinator.data
        assert "firewall_rules" in facade_coordinator.data
        assert "rule1" in facade_coordinator.data["firewall_rules"]["default"]

        # Check device coordinator data
        assert "devices" in facade_coordinator.data
        assert "default" in facade_coordinator.data["devices"]
        assert "clients" in facade_coordinator.data
        assert "stats" in facade_coordinator.data

        # Check protect coordinator data
        assert "protect" in facade_coordinator.data
        assert "cameras" in facade_coordinator.data["protect"]
        assert "camera1" in facade_coordinator.data["protect"]["cameras"]

        # Check timestamp
        assert "last_update" in facade_coordinator.data

    def test_aggregate_data_no_protect(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test data aggregation without protect."""
        facade_coordinator_no_protect._aggregate_data()

        # Protect data should have default empty structure
        assert facade_coordinator_no_protect.data["protect"]["cameras"] == {}
        assert facade_coordinator_no_protect.data["protect"]["lights"] == {}

    def test_get_site(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test get_site delegation to config coordinator."""
        facade_coordinator._aggregate_data()
        result = facade_coordinator.get_site("default")
        assert result == {"id": "default", "name": "Default"}

    def test_get_device(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test get_device."""
        facade_coordinator._aggregate_data()
        result = facade_coordinator.get_device("default", "device1")
        assert result == {"id": "device1"}

    def test_get_device_missing(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test get_device for missing device."""
        facade_coordinator._aggregate_data()
        result = facade_coordinator.get_device("default", "nonexistent")
        assert result is None

    def test_get_device_stats(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test get_device_stats."""
        facade_coordinator._aggregate_data()
        result = facade_coordinator.get_device_stats("default", "device1")
        assert result == {"cpu": 10}

    def test_get_device_stats_missing(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test get_device_stats for missing device."""
        facade_coordinator._aggregate_data()
        result = facade_coordinator.get_device_stats("default", "nonexistent")
        assert result is None

    def test_available_all_success(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test available property when all coordinators succeed."""
        # Replace coordinators with mocks that have last_update_success attribute
        mock_config = MagicMock()
        mock_config.last_update_success = True
        mock_device = MagicMock()
        mock_device.last_update_success = True
        mock_protect = MagicMock()
        mock_protect.last_update_success = True

        facade_coordinator._config_coordinator = mock_config
        facade_coordinator._device_coordinator = mock_device
        facade_coordinator._protect_coordinator = mock_protect

        assert facade_coordinator.available is True

    def test_available_config_fails_decoupled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test available property when config coordinator fails."""
        mock_config = MagicMock()
        mock_config.last_update_success = False
        mock_device = MagicMock()
        mock_device.last_update_success = True
        mock_protect = MagicMock()
        mock_protect.last_update_success = True

        facade_coordinator._config_coordinator = mock_config
        facade_coordinator._device_coordinator = mock_device
        facade_coordinator._protect_coordinator = mock_protect

        assert facade_coordinator.available is False
        assert facade_coordinator.config_available is False
        assert facade_coordinator.device_available is True
        assert facade_coordinator.protect_available is True

    def test_available_device_fails_decoupled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test available property when device coordinator fails."""
        mock_config = MagicMock()
        mock_config.last_update_success = True
        mock_device = MagicMock()
        mock_device.last_update_success = False
        mock_protect = MagicMock()
        mock_protect.last_update_success = True

        facade_coordinator._config_coordinator = mock_config
        facade_coordinator._device_coordinator = mock_device
        facade_coordinator._protect_coordinator = mock_protect

        assert facade_coordinator.available is False
        assert facade_coordinator.device_available is False
        assert facade_coordinator.config_available is True
        assert facade_coordinator.protect_available is True

    def test_available_protect_fails_decoupled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test available property when protect coordinator fails."""
        mock_config = MagicMock()
        mock_config.last_update_success = True
        mock_device = MagicMock()
        mock_device.last_update_success = True
        mock_protect = MagicMock()
        mock_protect.last_update_success = False

        facade_coordinator._config_coordinator = mock_config
        facade_coordinator._device_coordinator = mock_device
        facade_coordinator._protect_coordinator = mock_protect

        assert facade_coordinator.available is False
        assert facade_coordinator.protect_available is False
        assert facade_coordinator.device_available is True
        assert facade_coordinator.config_available is True

    def test_available_all_coordinators_fail(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test available property when all coordinators fail."""
        mock_config = MagicMock()
        mock_config.last_update_success = False
        mock_device = MagicMock()
        mock_device.last_update_success = False
        mock_protect = MagicMock()
        mock_protect.last_update_success = False

        facade_coordinator._config_coordinator = mock_config
        facade_coordinator._device_coordinator = mock_device
        facade_coordinator._protect_coordinator = mock_protect

        assert facade_coordinator.available is False
        assert facade_coordinator.device_available is False
        assert facade_coordinator.config_available is False
        assert facade_coordinator.protect_available is False

    def test_available_no_protect(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test available property without protect coordinator."""
        mock_config = MagicMock()
        mock_config.last_update_success = True
        mock_device = MagicMock()
        mock_device.last_update_success = True

        facade_coordinator_no_protect._config_coordinator = mock_config
        facade_coordinator_no_protect._device_coordinator = mock_device
        # protect_coordinator is None by default for this fixture

        assert facade_coordinator_no_protect.available is True
        assert facade_coordinator_no_protect.protect_available is True

    @pytest.mark.asyncio
    async def test_async_update_data(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test async update data."""
        result = await facade_coordinator._async_update_data()

        assert "sites" in result
        assert "devices" in result
        assert "protect" in result

    @pytest.mark.asyncio
    async def test_async_request_refresh(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """
        Test async_request_refresh forces a genuine refresh on each
        sub-coordinator (async_refresh), not the debounced
        async_request_refresh which can return before any fetch happens.
        """
        facade_coordinator._config_coordinator.async_refresh = AsyncMock()
        facade_coordinator._device_coordinator.async_refresh = AsyncMock()
        facade_coordinator._protect_coordinator.async_refresh = AsyncMock()

        await facade_coordinator.async_request_refresh()

        facade_coordinator._config_coordinator.async_refresh.assert_called_once()
        facade_coordinator._device_coordinator.async_refresh.assert_called_once()
        facade_coordinator._protect_coordinator.async_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_is_quiet_when_children_succeed(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """A clean refresh raises nothing and still notifies listeners."""
        listener_calls = 0

        def listener() -> None:
            nonlocal listener_calls
            listener_calls += 1

        facade_coordinator.async_add_listener(listener)
        for child in (
            facade_coordinator._config_coordinator,
            facade_coordinator._device_coordinator,
            facade_coordinator._protect_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        await facade_coordinator.async_refresh_or_raise()

        assert listener_calls >= 1

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_reports_recorded_failure(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """
        A child that failed is reported even though nothing was raised.

        ``DataUpdateCoordinator.async_refresh()`` swallows the error and only
        records ``last_update_success`` / ``last_exception``, so awaiting it
        tells the caller nothing. Without this the service reported success.
        """
        for child in (
            facade_coordinator._config_coordinator,
            facade_coordinator._device_coordinator,
            facade_coordinator._protect_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        facade_coordinator._device_coordinator.last_update_success = False
        facade_coordinator._device_coordinator.last_exception = OSError("console down")

        with pytest.raises(HomeAssistantError) as err:
            await facade_coordinator.async_refresh_or_raise()

        assert "devices coordinator" in str(err.value)
        assert "console down" in str(err.value)

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_reports_escaped_exception(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """An exception that escapes a child refresh is reported, not lost."""
        for child in (
            facade_coordinator._config_coordinator,
            facade_coordinator._device_coordinator,
            facade_coordinator._protect_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        facade_coordinator._protect_coordinator.async_refresh = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        with pytest.raises(HomeAssistantError) as err:
            await facade_coordinator.async_refresh_or_raise()

        assert "protect coordinator" in str(err.value)
        assert "boom" in str(err.value)

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_propagates_cancellation(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Cancellation is teardown, not a console failure - it must propagate.

        ``CancelledError`` is a ``BaseException``; an ``isinstance(x, Exception)``
        check would miss it and report the refresh as a success.
        """
        for child in (
            facade_coordinator._config_coordinator,
            facade_coordinator._device_coordinator,
            facade_coordinator._protect_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        facade_coordinator._device_coordinator.async_refresh = AsyncMock(
            side_effect=asyncio.CancelledError
        )

        with pytest.raises(asyncio.CancelledError):
            await facade_coordinator.async_refresh_or_raise()

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_can_skip_protect(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """A site-scoped refresh is a Network concern and skips Protect."""
        for child in (
            facade_coordinator._config_coordinator,
            facade_coordinator._device_coordinator,
            facade_coordinator._protect_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        await facade_coordinator.async_refresh_or_raise(include_protect=False)

        facade_coordinator._config_coordinator.async_refresh.assert_called_once()
        facade_coordinator._device_coordinator.async_refresh.assert_called_once()
        facade_coordinator._protect_coordinator.async_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_refresh_or_raise_without_protect_console(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """A Network-only console refreshes cleanly with no Protect child."""
        for child in (
            facade_coordinator_no_protect._config_coordinator,
            facade_coordinator_no_protect._device_coordinator,
        ):
            child.async_refresh = AsyncMock()
            child.last_update_success = True

        await facade_coordinator_no_protect.async_refresh_or_raise()

        facade_coordinator_no_protect._config_coordinator.async_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_request_refresh_no_protect(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test async request refresh without protect."""
        facade_coordinator_no_protect._config_coordinator.async_refresh = AsyncMock()
        facade_coordinator_no_protect._device_coordinator.async_refresh = AsyncMock()

        await facade_coordinator_no_protect.async_request_refresh()

        facade_coordinator_no_protect._config_coordinator.async_refresh.assert_called_once()
        facade_coordinator_no_protect._device_coordinator.async_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_request_refresh_waits_for_fresh_data_and_notifies(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """
        Regression test for the async_request_refresh contract violation.

        Callers (e.g. switch.py action handlers) await
        ``coordinator.async_request_refresh()`` expecting two things: (1)
        the aggregated data reflects a fetch that actually happened during
        the call, and (2) their own listener gets notified. The previous
        implementation awaited each sub-coordinator's *debounced*
        ``async_request_refresh()``, which can return before any fetch
        starts (see ``Debouncer`` cooldown), and never called
        ``async_update_listeners()`` itself - so both guarantees could be
        silently violated.

        This test drives a real (mocked) async_refresh that mutates the
        sub-coordinator's data, then asserts the facade's aggregated data
        reflects it and that a registered listener was actually called.
        """
        listener_calls = 0

        def listener() -> None:
            nonlocal listener_calls
            listener_calls += 1

        facade_coordinator.async_add_listener(listener)

        async def _fake_refresh() -> None:
            facade_coordinator._config_coordinator.data["sites"] = {
                "new-site": {"id": "new-site"}
            }

        facade_coordinator._config_coordinator.async_refresh = AsyncMock(
            side_effect=_fake_refresh
        )
        facade_coordinator._device_coordinator.async_refresh = AsyncMock()
        facade_coordinator._protect_coordinator.async_refresh = AsyncMock()
        # The debounced path must not be used for this explicit,
        # user-triggered refresh - assert it's never touched.
        facade_coordinator._config_coordinator.async_request_refresh = AsyncMock()
        facade_coordinator._device_coordinator.async_request_refresh = AsyncMock()
        facade_coordinator._protect_coordinator.async_request_refresh = AsyncMock()

        await facade_coordinator.async_request_refresh()

        facade_coordinator._config_coordinator.async_request_refresh.assert_not_called()
        facade_coordinator._device_coordinator.async_request_refresh.assert_not_called()
        facade_coordinator._protect_coordinator.async_request_refresh.assert_not_called()

        # The aggregated data must reflect what the (mocked) genuine
        # refresh produced, proving the call actually waited for it.
        assert facade_coordinator.data["sites"] == {"new-site": {"id": "new-site"}}

        # Listeners (entities) must be notified so they can reflect the
        # refreshed state without waiting for the next natural poll.
        assert listener_calls >= 1

    def test_handle_coordinator_update(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test handling coordinator updates."""
        # Track if listeners were called
        listener_called = False

        def listener():
            nonlocal listener_called
            listener_called = True

        facade_coordinator.async_add_listener(listener)
        facade_coordinator._handle_coordinator_update()

        assert listener_called

    @pytest.mark.asyncio
    async def test_require_protect_client_raises(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test _require_protect_client raises when protect is None."""
        with pytest.raises(HomeAssistantError, match="Protect is not available"):
            facade_coordinator_no_protect._require_protect_client()

    @pytest.mark.asyncio
    async def test_require_protect_client_returns_client(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test _require_protect_client returns client when available."""
        client = facade_coordinator._require_protect_client()
        assert client is facade_coordinator.protect_client

    @pytest.mark.asyncio
    async def test_async_execute_api_action_success(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test _async_execute_api_action on success."""
        action = AsyncMock(return_value="ok")
        result = await facade_coordinator._async_execute_api_action(
            "test error", action, "arg1"
        )
        assert result == "ok"
        action.assert_called_once_with("arg1")

    @pytest.mark.asyncio
    async def test_async_execute_api_action_ha_error(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test _async_execute_api_action re-raises HomeAssistantError."""
        action = AsyncMock(side_effect=HomeAssistantError("ha error"))
        with pytest.raises(HomeAssistantError, match="ha error"):
            await facade_coordinator._async_execute_api_action("test error", action)

    @pytest.mark.asyncio
    async def test_async_execute_api_action_generic_error(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test _async_execute_api_action wraps generic errors."""
        action = AsyncMock(side_effect=RuntimeError("boom"))
        with pytest.raises(HomeAssistantError, match="test error"):
            await facade_coordinator._async_execute_api_action("test error", action)

    @pytest.mark.asyncio
    async def test_async_restart_device(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_restart_device delegates to network client."""
        facade_coordinator.network_client.devices.restart = AsyncMock(return_value=True)
        result = await facade_coordinator.async_restart_device("site1", "dev1")
        assert result is True
        facade_coordinator.network_client.devices.restart.assert_called_once_with(
            "site1", "dev1"
        )

    @pytest.mark.asyncio
    async def test_async_set_firewall_rule_enabled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_firewall_rule_enabled delegates correctly."""
        facade_coordinator.network_client.firewall.update_rule = AsyncMock()
        await facade_coordinator.async_set_firewall_rule_enabled(
            "site1", "rule1", enabled=True
        )
        facade_coordinator.network_client.firewall.update_rule.assert_called_once_with(
            "site1", "rule1", enabled=True
        )

    @pytest.mark.asyncio
    async def test_async_set_policy_based_route_enabled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ) -> None:
        """Test async_set_policy_based_route_enabled delegates correctly."""
        facade_coordinator.network_client.routes.update_route = AsyncMock()
        facade_coordinator._device_coordinator.get_legacy_site_name = MagicMock(
            return_value="default"
        )
        await facade_coordinator.async_set_policy_based_route_enabled(
            "site1", "route1", enabled=True
        )
        facade_coordinator.network_client.routes.update_route.assert_called_once_with(
            "default", "route1", enabled=True
        )

    @pytest.mark.asyncio
    async def test_async_set_policy_based_route_enabled_fallback(
        self, facade_coordinator: UnifiFacadeCoordinator
    ) -> None:
        """Test async_set_policy_based_route_enabled falls back to default."""
        facade_coordinator.network_client.routes.update_route = AsyncMock()
        facade_coordinator._device_coordinator.get_legacy_site_name = MagicMock(
            return_value=None
        )
        await facade_coordinator.async_set_policy_based_route_enabled(
            "unknown_site", "route1", enabled=True
        )
        facade_coordinator.network_client.routes.update_route.assert_called_once_with(
            "default", "route1", enabled=True
        )

    @pytest.mark.asyncio
    async def test_async_set_vpn_client_enabled(
        self, facade_coordinator: UnifiFacadeCoordinator
    ) -> None:
        """Test async_set_vpn_client_enabled delegates correctly."""
        facade_coordinator.network_client.vpn_clients.update_vpn_client = AsyncMock()
        facade_coordinator._device_coordinator.get_legacy_site_name = MagicMock(
            return_value="default"
        )
        await facade_coordinator.async_set_vpn_client_enabled(
            "site1", "vpn1", enabled=True
        )
        mock_update = facade_coordinator.network_client.vpn_clients.update_vpn_client
        mock_update.assert_called_once_with("default", "vpn1", enabled=True)

    @pytest.mark.asyncio
    async def test_async_set_vpn_client_enabled_fallback(
        self, facade_coordinator: UnifiFacadeCoordinator
    ) -> None:
        """Test async_set_vpn_client_enabled falls back to default site."""
        facade_coordinator.network_client.vpn_clients.update_vpn_client = AsyncMock()
        facade_coordinator._device_coordinator.get_legacy_site_name = MagicMock(
            return_value=None
        )
        await facade_coordinator.async_set_vpn_client_enabled(
            "unknown_site", "vpn1", enabled=True
        )
        mock_update = facade_coordinator.network_client.vpn_clients.update_vpn_client
        mock_update.assert_called_once_with("default", "vpn1", enabled=True)

    @pytest.mark.asyncio
    async def test_async_update_camera(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_update_camera delegates to protect client."""
        facade_coordinator.protect_client.cameras.update = AsyncMock()
        await facade_coordinator.async_update_camera("cam1", hdrMode="on")
        facade_coordinator.protect_client.cameras.update.assert_called_once_with(
            "cam1", hdrMode="on"
        )

    @pytest.mark.asyncio
    async def test_async_update_camera_settings(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_update_camera_settings is alias for async_update_camera."""
        facade_coordinator.protect_client.cameras.update = AsyncMock()
        await facade_coordinator.async_update_camera_settings("cam1", videoMode="hd")
        facade_coordinator.protect_client.cameras.update.assert_called_once_with(
            "cam1", videoMode="hd"
        )

    @pytest.mark.asyncio
    async def test_async_unblock_client(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_unblock_client resolves the MAC and classic site name."""
        facade_coordinator.data["clients"] = {
            "site1": {"client1": {"id": "client1", "macAddress": "AA:BB:CC:DD:EE:FF"}}
        }
        facade_coordinator.network_client.clients.unblock = AsyncMock()
        await facade_coordinator.async_unblock_client("site1", "client1")
        facade_coordinator.network_client.clients.unblock.assert_called_once_with(
            "default", "AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_async_block_client(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test async_block_client resolves the MAC and classic site name."""
        facade_coordinator.data["clients"] = {
            "site1": {"client1": {"id": "client1", "macAddress": "AA:BB:CC:DD:EE:FF"}}
        }
        facade_coordinator.network_client.clients.block = AsyncMock()
        await facade_coordinator.async_block_client("site1", "client1")
        facade_coordinator.network_client.clients.block.assert_called_once_with(
            "default", "AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_async_reconnect_client(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_reconnect_client resolves the MAC and classic site name."""
        facade_coordinator.data["clients"] = {
            "site1": {"client1": {"id": "client1", "macAddress": "AA:BB:CC:DD:EE:FF"}}
        }
        facade_coordinator.network_client.clients.reconnect = AsyncMock()
        await facade_coordinator.async_reconnect_client("site1", "client1")
        facade_coordinator.network_client.clients.reconnect.assert_called_once_with(
            "default", "AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_async_forget_client(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_forget_client resolves the MAC and classic site name."""
        facade_coordinator.data["clients"] = {
            "site1": {"client1": {"id": "client1", "macAddress": "AA:BB:CC:DD:EE:FF"}}
        }
        facade_coordinator.network_client.clients.forget = AsyncMock()
        await facade_coordinator.async_forget_client("site1", "client1")
        facade_coordinator.network_client.clients.forget.assert_called_once_with(
            "default", "AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_client_action_uses_mapped_site_name(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """A non-default classic site name from the device coordinator is used."""
        facade_coordinator.data["clients"] = {
            "site1": {"client1": {"id": "client1", "macAddress": "AA:BB:CC:DD:EE:FF"}}
        }
        facade_coordinator._device_coordinator._legacy_site_names = {"site1": "branch"}
        facade_coordinator.network_client.clients.block = AsyncMock()
        await facade_coordinator.async_block_client("site1", "client1")
        facade_coordinator.network_client.clients.block.assert_called_once_with(
            "branch", "AA:BB:CC:DD:EE:FF"
        )

    @pytest.mark.asyncio
    async def test_async_set_outlet_state(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_outlet_state resolves site and targets legacy _id."""
        facade_coordinator.data["devices"] = {
            "site1": {
                "device1": {
                    "id": "device1",
                    "_id": "60a1b2c3d4e5f67890123456",
                    "macAddress": "AA:BB:CC:DD:EE:FF",
                }
            }
        }
        facade_coordinator._device_coordinator._legacy_site_names = {"site1": "branch"}
        facade_coordinator.network_client.devices.set_outlet_state = AsyncMock(
            return_value=True
        )

        result = await facade_coordinator.async_set_outlet_state(
            "site1", "device1", 1, state=True, cycle_enabled=False
        )
        assert result is True
        set_outlet = facade_coordinator.network_client.devices.set_outlet_state
        set_outlet.assert_called_once_with(
            "branch",
            "60a1b2c3d4e5f67890123456",
            1,
            True,
            cycle_enabled=False,
            current_device={
                "id": "device1",
                "_id": "60a1b2c3d4e5f67890123456",
                "macAddress": "AA:BB:CC:DD:EE:FF",
            },
        )

    @pytest.mark.asyncio
    async def test_async_authorize_guest(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_authorize_guest delegates to the official actions endpoint."""
        facade_coordinator.network_client.clients.authorize_guest = AsyncMock()
        await facade_coordinator.async_authorize_guest("site1", "client1")
        facade_coordinator.network_client.clients.authorize_guest.assert_called_once_with(
            "site1", "client1"
        )

    @pytest.mark.asyncio
    async def test_async_unauthorize_guest(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_unauthorize_guest delegates to the official actions endpoint."""
        facade_coordinator.network_client.clients.unauthorize_guest = AsyncMock()
        await facade_coordinator.async_unauthorize_guest("site1", "client1")
        mock = facade_coordinator.network_client.clients.unauthorize_guest
        mock.assert_called_once_with("site1", "client1")

    @pytest.mark.asyncio
    async def test_async_update_wifi_network(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_update_wifi_network delegates correctly."""
        facade_coordinator.network_client.wifi.update = AsyncMock()
        await facade_coordinator.async_update_wifi_network(
            "site1", "wifi1", enabled=False
        )
        facade_coordinator.network_client.wifi.update.assert_called_once_with(
            "site1", "wifi1", enabled=False
        )

    @pytest.mark.asyncio
    async def test_async_play_chime(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test async_play_chime delegates correctly."""
        facade_coordinator.protect_client.chimes.play = AsyncMock()
        await facade_coordinator.async_play_chime("chime1")
        facade_coordinator.protect_client.chimes.play.assert_called_once_with("chime1")

    @pytest.mark.asyncio
    async def test_async_start_ptz_patrol(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_start_ptz_patrol delegates correctly."""
        facade_coordinator.protect_client.cameras.ptz_patrol_start = AsyncMock()
        await facade_coordinator.async_start_ptz_patrol("cam1", 1)
        facade_coordinator.protect_client.cameras.ptz_patrol_start.assert_called_once_with(
            "cam1", 1
        )

    @pytest.mark.asyncio
    async def test_async_stop_ptz_patrol(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_stop_ptz_patrol delegates correctly."""
        facade_coordinator.protect_client.cameras.ptz_patrol_stop = AsyncMock()
        await facade_coordinator.async_stop_ptz_patrol("cam1")
        facade_coordinator.protect_client.cameras.ptz_patrol_stop.assert_called_once_with(
            "cam1"
        )

    @pytest.mark.asyncio
    async def test_async_set_hdr_mode(self, facade_coordinator: UnifiFacadeCoordinator):
        """Test async_set_hdr_mode delegates correctly."""
        facade_coordinator.protect_client.cameras.set_hdr_mode = AsyncMock()
        await facade_coordinator.async_set_hdr_mode("cam1", "auto")
        facade_coordinator.protect_client.cameras.set_hdr_mode.assert_called_once_with(
            "cam1", "auto"
        )

    @pytest.mark.asyncio
    async def test_async_set_video_mode(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_video_mode delegates correctly."""
        facade_coordinator.protect_client.cameras.set_video_mode = AsyncMock()
        await facade_coordinator.async_set_video_mode("cam1", "highFps")
        facade_coordinator.protect_client.cameras.set_video_mode.assert_called_once_with(
            "cam1", "highFps"
        )

    @pytest.mark.asyncio
    async def test_async_set_recording_mode(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_recording_mode delegates correctly."""
        facade_coordinator.protect_client.cameras.update = AsyncMock()
        await facade_coordinator.async_set_recording_mode("cam1", "always")
        facade_coordinator.protect_client.cameras.update.assert_called_once_with(
            "cam1", recordingMode="always"
        )

    @pytest.mark.asyncio
    async def test_async_set_chime_ringtone(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_chime_ringtone delegates correctly."""
        facade_coordinator.protect_client.chimes.update = AsyncMock()
        await facade_coordinator.async_set_chime_ringtone("chime1", "ring2")
        facade_coordinator.protect_client.chimes.update.assert_called_once_with(
            "chime1", ringtone="ring2"
        )

    @pytest.mark.asyncio
    async def test_async_move_ptz_to_preset(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_move_ptz_to_preset delegates correctly."""
        facade_coordinator.protect_client.cameras.ptz_goto_preset = AsyncMock()
        await facade_coordinator.async_move_ptz_to_preset("cam1", 3)
        facade_coordinator.protect_client.cameras.ptz_goto_preset.assert_called_once_with(
            "cam1", "3"
        )

    @pytest.mark.asyncio
    async def test_async_update_viewer(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_update_viewer delegates correctly."""
        facade_coordinator.protect_client.viewers.update = AsyncMock()
        await facade_coordinator.async_update_viewer("viewer1", liveview="lv1")
        facade_coordinator.protect_client.viewers.update.assert_called_once_with(
            "viewer1", liveview="lv1"
        )

    @pytest.mark.asyncio
    async def test_async_set_microphone_volume(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_microphone_volume delegates correctly."""
        facade_coordinator.protect_client.cameras.set_microphone_volume = AsyncMock()
        await facade_coordinator.async_set_microphone_volume("cam1", 50)
        facade_coordinator.protect_client.cameras.set_microphone_volume.assert_called_once_with(
            "cam1", 50
        )

    @pytest.mark.asyncio
    async def test_async_set_light_brightness(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_light_brightness delegates correctly."""
        facade_coordinator.protect_client.lights.set_brightness = AsyncMock()
        await facade_coordinator.async_set_light_brightness("light1", 75)
        facade_coordinator.protect_client.lights.set_brightness.assert_called_once_with(
            "light1", 75
        )

    @pytest.mark.asyncio
    async def test_async_set_light_mode(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_light_mode delegates correctly."""
        facade_coordinator.protect_client.lights.update = AsyncMock()
        await facade_coordinator.async_set_light_mode("light1", "motion")
        facade_coordinator.protect_client.lights.update.assert_called_once_with(
            "light1", lightMode="motion"
        )

    @pytest.mark.asyncio
    async def test_async_set_chime_volume(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_chime_volume delegates correctly."""
        facade_coordinator.protect_client.chimes.set_volume = AsyncMock()
        await facade_coordinator.async_set_chime_volume("chime1", 80)
        facade_coordinator.protect_client.chimes.set_volume.assert_called_once_with(
            "chime1", 80
        )

    @pytest.mark.asyncio
    async def test_async_set_chime_repeat(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_set_chime_repeat delegates correctly."""
        facade_coordinator.protect_client.chimes.update = AsyncMock()
        await facade_coordinator.async_set_chime_repeat("chime1", 3)
        facade_coordinator.protect_client.chimes.update.assert_called_once_with(
            "chime1", repeatTimes=3
        )

    @pytest.mark.asyncio
    async def test_async_generate_voucher(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_generate_voucher delegates correctly."""
        facade_coordinator.network_client.vouchers.create = AsyncMock()
        await facade_coordinator.async_generate_voucher(
            "site1",
            count=5,
            time_limit_minutes=60,
            tx_rate_limit_kbps=1024,
            rx_rate_limit_kbps=2048,
            data_usage_limit_mbytes=500,
            name="test",
        )
        facade_coordinator.network_client.vouchers.create.assert_called_once_with(
            "site1",
            count=5,
            time_limit_minutes=60,
            tx_rate_limit_kbps=1024,
            rx_rate_limit_kbps=2048,
            data_usage_limit_mbytes=500,
            name="test",
        )

    @pytest.mark.asyncio
    async def test_async_generate_voucher_minimal(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_generate_voucher with minimal args."""
        facade_coordinator.network_client.vouchers.create = AsyncMock()
        await facade_coordinator.async_generate_voucher("site1")
        facade_coordinator.network_client.vouchers.create.assert_called_once_with(
            "site1", count=1
        )

    @pytest.mark.asyncio
    async def test_async_delete_voucher(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_delete_voucher delegates correctly."""
        facade_coordinator.network_client.vouchers.delete = AsyncMock()
        await facade_coordinator.async_delete_voucher("site1", "voucher1")
        facade_coordinator.network_client.vouchers.delete.assert_called_once_with(
            "site1", "voucher1"
        )

    @pytest.mark.asyncio
    async def test_async_trigger_alarm(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_trigger_alarm delegates correctly."""
        facade_coordinator.protect_client.application.trigger_alarm_webhook = (
            AsyncMock()
        )
        await facade_coordinator.async_trigger_alarm("alarm1")
        facade_coordinator.protect_client.application.trigger_alarm_webhook.assert_called_once_with(
            "alarm1"
        )

    @pytest.mark.asyncio
    async def test_async_create_liveview(
        self, facade_coordinator: UnifiFacadeCoordinator
    ):
        """Test async_create_liveview delegates correctly."""
        facade_coordinator.protect_client.liveviews.create = AsyncMock()
        await facade_coordinator.async_create_liveview(
            name="Main View", layout=2, is_default=True
        )
        facade_coordinator.protect_client.liveviews.create.assert_called_once_with(
            name="Main View", layout=2, isDefault=True
        )

    @pytest.mark.asyncio
    async def test_protect_methods_raise_without_protect(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test protect methods raise when protect is unavailable."""
        coord = facade_coordinator_no_protect
        with pytest.raises(HomeAssistantError, match="Protect is not available"):
            await coord.async_update_camera("cam1")
        with pytest.raises(HomeAssistantError, match="Protect is not available"):
            await coord.async_play_chime("chime1")
        with pytest.raises(HomeAssistantError, match="Protect is not available"):
            await coord.async_trigger_alarm("alarm1")

    @pytest.mark.asyncio
    async def test_async_shutdown_releases_sub_coordinator_listeners(
        self,
        facade_coordinator: UnifiFacadeCoordinator,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
        protect_coordinator: UnifiProtectCoordinator,
    ):
        """
        Regression test for the sub-coordinator listener leak.

        ``_setup_listeners`` registers the facade as a listener on each
        sub-coordinator via ``async_add_listener``, which returns a
        remove-callback. Discarding that callback (the previous behavior)
        means nothing ever undoes the registration: on config-entry
        reload, a fresh facade is built and a fresh listener piles onto
        the sub-coordinators, while the outgoing facade instance and its
        listener registration are never released. Shutting the facade
        down must release exactly what it registered, returning each
        sub-coordinator's listener count to its pre-facade baseline.
        """
        # Baseline: __init__ -> _setup_listeners already registered
        # exactly one listener (this facade) on each sub-coordinator.
        assert len(config_coordinator._listeners) == 1
        assert len(device_coordinator._listeners) == 1
        assert len(protect_coordinator._listeners) == 1

        await facade_coordinator.async_shutdown()

        assert len(config_coordinator._listeners) == 0
        assert len(device_coordinator._listeners) == 0
        assert len(protect_coordinator._listeners) == 0

    async def test_async_shutdown_is_idempotent(
        self,
        facade_coordinator: UnifiFacadeCoordinator,
    ):
        """
        Shutting the facade down twice must be safe.

        ``DataUpdateCoordinator.__init__`` registers
        ``entry.async_on_unload(self.async_shutdown)``, so HA invokes
        shutdown on its own at unload -- which can coincide with an
        explicit call from our unload path. The second pass must not
        raise and must not re-invoke the already-spent remove-callbacks
        (which would unregister listeners belonging to a *newer* facade
        built by the reload that followed).
        """
        # Stand in for the real remove-callbacks so a second release is
        # observable. Listener-count behavior is covered by
        # test_async_shutdown_releases_sub_coordinator_listeners.
        unsubs = [MagicMock() for _ in range(3)]
        facade_coordinator._sub_coordinator_unsubs = list(unsubs)

        await facade_coordinator.async_shutdown()
        for unsub in unsubs:
            assert unsub.call_count == 1

        # Second shutdown: must not raise, and must not re-invoke the
        # already-spent callbacks.
        await facade_coordinator.async_shutdown()
        for unsub in unsubs:
            assert unsub.call_count == 1

        assert facade_coordinator._sub_coordinator_unsubs == []


# ============================================================================
# Integration Tests for Coordinator Data Flow
# ============================================================================


class TestCoordinatorDataFlow:
    """Integration tests for coordinator data flow."""

    @pytest.mark.asyncio
    async def test_full_data_flow(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test complete data flow from API to facade coordinator."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()

        # Create coordinators
        config_coord = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        device_coord = UnifiDeviceCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            config_coordinator=config_coord,
        )

        protect_coord = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        facade_coord = UnifiFacadeCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            config_coordinator=config_coord,
            device_coordinator=device_coord,
            protect_coordinator=protect_coord,
        )

        # Fetch data through coordinators
        await config_coord._async_update_data()
        await device_coord._async_update_data()
        await protect_coord._async_update_data()
        facade_coord._aggregate_data()

        # Verify data is properly aggregated
        assert "default" in facade_coord.data["sites"]
        assert "default" in facade_coord.data["devices"]
        assert "camera1" in facade_coord.data["protect"]["cameras"]

        # Shut down so scheduled refresh timers don't linger past the test
        await facade_coord.async_shutdown()
        await config_coord.async_shutdown()
        await device_coord.async_shutdown()
        await protect_coord.async_shutdown()


class TestProtectCoordinatorEdgeCases:
    """Tests for edge cases in UnifiProtectCoordinator."""

    @pytest.fixture
    def coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiProtectCoordinator:
        """Create a protect coordinator for testing."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        return UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

    def test_site_id_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test the coordinator defaults site_id to 'default' when unset."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        assert coordinator._site_id == "default"

    def test_site_id_custom(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test the coordinator accepts a custom site_id (REMOTE routing)."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            site_id="site2",
        )

        assert coordinator._site_id == "site2"

    @pytest.mark.asyncio
    async def test_fetch_viewers_no_viewers_attribute(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test fetch viewers when protect_client lacks viewers attribute."""
        network_client = _create_mock_network_client()
        protect_client = MagicMock()
        protect_client.register_device_update_callback = MagicMock()
        protect_client.register_event_update_callback = MagicMock()
        protect_client.cameras = MagicMock()
        protect_client.cameras.get_all = AsyncMock(return_value=[])
        protect_client.lights = MagicMock()
        protect_client.lights.get_all = AsyncMock(return_value=[])
        protect_client.sensors = MagicMock()
        protect_client.sensors.get_all = AsyncMock(return_value=[])
        protect_client.nvr = MagicMock()
        protect_client.nvr.get = AsyncMock(return_value=MagicMock(id="nvr1"))
        protect_client.chimes = MagicMock()
        protect_client.chimes.get_all = AsyncMock(return_value=[])
        # Remove viewers attribute
        del protect_client.viewers
        protect_client.liveviews = MagicMock()
        protect_client.liveviews.get_all = AsyncMock(return_value=[])

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        result = await coordinator._async_update_data()

        # Should not raise and viewers should be empty
        assert result["viewers"] == {}

    @pytest.mark.asyncio
    async def test_fetch_liveviews_no_liveviews_attribute(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test fetch liveviews when protect_client lacks liveviews attribute."""
        network_client = _create_mock_network_client()
        protect_client = MagicMock()
        protect_client.register_device_update_callback = MagicMock()
        protect_client.register_event_update_callback = MagicMock()
        protect_client.cameras = MagicMock()
        protect_client.cameras.get_all = AsyncMock(return_value=[])
        protect_client.lights = MagicMock()
        protect_client.lights.get_all = AsyncMock(return_value=[])
        protect_client.sensors = MagicMock()
        protect_client.sensors.get_all = AsyncMock(return_value=[])
        protect_client.nvr = MagicMock()
        protect_client.nvr.get = AsyncMock(return_value=MagicMock(id="nvr1"))
        protect_client.chimes = MagicMock()
        protect_client.chimes.get_all = AsyncMock(return_value=[])
        protect_client.viewers = MagicMock()
        protect_client.viewers.get_all = AsyncMock(return_value=[])
        # Remove liveviews attribute
        del protect_client.liveviews

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        result = await coordinator._async_update_data()

        # Should not raise and liveviews should be empty
        assert result["liveviews"] == {}

    @pytest.mark.asyncio
    async def test_fetch_cameras_feature_flags_not_dict(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test camera fetch when featureFlags is not a dict."""
        camera_mock = MagicMock()
        camera_mock.id = "camera1"
        camera_mock.name = "Test Camera"
        camera_mock.feature_flags = "not_a_dict"  # Invalid type
        # Make model_dump return the non-dict featureFlags
        camera_mock.model_dump = MagicMock(
            return_value={
                "id": "camera1",
                "name": "Test Camera",
                "featureFlags": "not_a_dict",
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[camera_mock]
        )

        result = await coordinator._async_update_data()

        # Should still work, smartDetectTypes should be empty list
        assert result["cameras"]["camera1"]["smartDetectTypes"] == []

    def test_handle_event_unknown_type(self, coordinator: UnifiProtectCoordinator):
        """Test handling event with unknown type."""
        # Add camera first
        coordinator.data["cameras"]["camera1"] = {"id": "camera1"}

        # Process unknown event type
        coordinator._handle_event_update(
            "unknown_event",
            {"id": "event1", "device": "camera1", "start": 123},
        )

        # Event should be stored but no device update
        assert "unknown_event" in coordinator.data["events"]

    def test_handle_event_device_not_found(self, coordinator: UnifiProtectCoordinator):
        """Test handling event when device not in data."""
        coordinator._handle_event_update(
            "motion",
            {"id": "event1", "device": "nonexistent_device", "start": 123},
        )

        # Event should be stored but no error
        assert "motion" in coordinator.data["events"]
