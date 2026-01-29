"""Tests for multi-coordinator architecture (Platinum compliance)."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiResponseError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights.const import (
    CONF_CONNECTION_TYPE,
    CONNECTION_TYPE_LOCAL,
    DOMAIN,
    SCAN_INTERVAL_CONFIG,
    SCAN_INTERVAL_DEVICE,
    SCAN_INTERVAL_PROTECT,
)
from custom_components.unifi_insights.coordinators.base import UnifiBaseCoordinator
from custom_components.unifi_insights.coordinators.config import UnifiConfigCoordinator
from custom_components.unifi_insights.coordinators.device import UnifiDeviceCoordinator
from custom_components.unifi_insights.coordinators.facade import UnifiFacadeCoordinator
from custom_components.unifi_insights.coordinators.protect import (
    UnifiProtectCoordinator,
)


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

    # WiFi namespace
    client.wifi = MagicMock()
    client.wifi.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                {"id": "wifi1", "name": "MainWiFi", "ssid": "MyNetwork"}
            ),
        ]
    )

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
                    "feature_flags": {"smart_detect_types": ["person", "vehicle"]},
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

    # WebSocket registration
    client.register_device_update_callback = MagicMock()
    client.register_event_update_callback = MagicMock()

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
        assert "network_info" in coordinator.data

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator: UnifiConfigCoordinator):
        """Test successful data fetch."""
        result = await coordinator._async_update_data()

        assert "sites" in result
        assert "default" in result["sites"]
        assert "site2" in result["sites"]
        assert "wifi" in result
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_wifi_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with WiFi error (should not fail)."""
        coordinator.network_client.wifi.get_all = AsyncMock(
            side_effect=Exception("WiFi fetch failed")
        )

        result = await coordinator._async_update_data()

        # Sites should still be fetched
        assert "sites" in result
        assert "default" in result["sites"]
        # WiFi should be empty for failed sites
        assert result["wifi"]["default"] == {}
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_auth_error(
        self, coordinator: UnifiConfigCoordinator
    ):
        """Test data fetch with auth error."""
        coordinator.network_client.sites.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        with pytest.raises(ConfigEntryAuthFailed):
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
    async def test_async_update_data_no_sites(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch with no sites available."""
        coordinator.config_coordinator.data["sites"] = {}

        result = await coordinator._async_update_data()

        # Should return existing data without changes
        assert result == coordinator.data

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
    async def test_process_site_error(self, coordinator: UnifiDeviceCoordinator):
        """Test site processing with error."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=Exception("Site fetch failed")
        )

        await coordinator._async_update_data()

        # Should handle error gracefully
        assert coordinator._available is True

    @pytest.mark.asyncio
    async def test_async_update_data_auth_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch handles auth error gracefully at site level."""
        # Errors in _process_site are caught and logged, not re-raised
        # The coordinator continues processing other sites
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiAuthenticationError("Invalid API key")
        )

        # Should complete without raising (error is caught in _process_site)
        result = await coordinator._async_update_data()
        # Returns existing data when sites fail
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_update_data_connection_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch handles connection error gracefully at site level."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiConnectionError("Connection refused")
        )

        # Should complete without raising (error is caught in _process_site)
        result = await coordinator._async_update_data()
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_update_data_timeout_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch handles timeout error gracefully at site level."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiTimeoutError("Request timed out")
        )

        # Should complete without raising (error is caught in _process_site)
        result = await coordinator._async_update_data()
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_update_data_response_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch handles response error gracefully at site level."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=UniFiResponseError("Bad response", status_code=400)
        )

        # Should complete without raising (error is caught in _process_site)
        result = await coordinator._async_update_data()
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_update_data_generic_error(
        self, coordinator: UnifiDeviceCoordinator
    ):
        """Test data fetch handles generic error gracefully at site level."""
        coordinator.network_client.devices.get_all = AsyncMock(
            side_effect=Exception("Something broke")
        )

        # Should complete without raising (error is caught in _process_site)
        result = await coordinator._async_update_data()
        assert result is not None

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
            mock_registry.return_value.async_get_device = MagicMock(
                return_value=mock_device
            )

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
            mock_registry.return_value.async_get_device = MagicMock(return_value=None)

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


# ============================================================================
# UnifiProtectCoordinator Tests
# ============================================================================


class TestUnifiProtectCoordinator:
    """Tests for UnifiProtectCoordinator."""

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

    @pytest.fixture
    def coordinator_no_protect(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> UnifiProtectCoordinator:
        """Create a protect coordinator without protect client."""
        network_client = _create_mock_network_client()
        return UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
        )

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

    def test_websocket_callbacks_registered(self, coordinator: UnifiProtectCoordinator):
        """Test WebSocket callbacks are registered."""
        coordinator.protect_client.register_device_update_callback.assert_called_once()
        coordinator.protect_client.register_event_update_callback.assert_called_once()

    def test_websocket_callbacks_not_registered_without_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test WebSocket callbacks not registered without protect client."""
        # No assertions needed - just ensure no exceptions
        assert coordinator_no_protect.protect_client is None

    def test_setup_websocket_callbacks_returns_early_without_client(
        self, coordinator_no_protect: UnifiProtectCoordinator
    ):
        """Test _setup_websocket_callbacks returns early without client (line 99)."""
        # Explicitly call _setup_websocket_callbacks with no protect_client
        # This should return early and not raise any exceptions
        coordinator_no_protect._setup_websocket_callbacks()
        # If we get here, the return statement was executed
        assert coordinator_no_protect.protect_client is None

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
        """Test data fetch with connection error."""
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiConnectionError("Connection refused")
        )

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
            mock_registry.return_value.async_get_device = MagicMock(
                return_value=mock_device
            )

            coordinator._cleanup_stale_devices()

            # camera2 should be marked for removal
            mock_registry.return_value.async_update_device.assert_called()

    def test_websocket_callbacks_exception(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test WebSocket callback setup handles exceptions gracefully."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        # Make callback registration raise an exception
        protect_client.register_device_update_callback = MagicMock(
            side_effect=Exception("Callback error")
        )

        # Should not raise - coordinator should handle the exception
        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        assert coordinator is not None

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
            mock_registry.return_value.async_get_device = MagicMock(return_value=None)

            # Should not raise - just skip removal
            coordinator._cleanup_stale_devices()

            # No device updates should happen (nothing found)
            mock_registry.return_value.async_update_device.assert_not_called()

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
                "feature_flags": {
                    "smart_detect_types": ["person", "vehicle"],
                },
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
                "feature_flags": "not_a_dict",  # Invalid type
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )

        await coordinator._fetch_cameras()

        assert "camera2" in coordinator.data["cameras"]
        # Should default to empty list when feature_flags is not a dict
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
                # No feature_flags key
            }
        )
        coordinator.protect_client.cameras.get_all = AsyncMock(
            return_value=[mock_camera]
        )

        await coordinator._fetch_cameras()

        assert "camera3" in coordinator.data["cameras"]
        assert coordinator.data["cameras"]["camera3"]["smartDetectTypes"] == []

    @pytest.mark.asyncio
    async def test_async_update_data_response_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with response error."""
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiResponseError("Invalid response", status_code=400)
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_update_data_timeout_error(
        self, coordinator: UnifiProtectCoordinator
    ):
        """Test data fetch with timeout error."""
        coordinator.protect_client.cameras.get_all = AsyncMock(
            side_effect=UniFiTimeoutError("Request timed out")
        )

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
    def facade_coordinator(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
        protect_coordinator: UnifiProtectCoordinator,
    ) -> UnifiFacadeCoordinator:
        """Create a facade coordinator."""
        network_client = _create_mock_network_client()
        protect_client = _create_mock_protect_client()
        return UnifiFacadeCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
            device_coordinator=device_coordinator,
            protect_coordinator=protect_coordinator,
        )

    @pytest.fixture
    def facade_coordinator_no_protect(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
    ) -> UnifiFacadeCoordinator:
        """Create a facade coordinator without protect."""
        network_client = _create_mock_network_client()
        return UnifiFacadeCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=None,
            entry=mock_config_entry,
            config_coordinator=config_coordinator,
            device_coordinator=device_coordinator,
            protect_coordinator=None,
        )

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

    def test_available_config_fails(self, facade_coordinator: UnifiFacadeCoordinator):
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

    def test_available_device_fails(self, facade_coordinator: UnifiFacadeCoordinator):
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

    def test_available_protect_fails(self, facade_coordinator: UnifiFacadeCoordinator):
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
        """Test async request refresh."""
        facade_coordinator._config_coordinator.async_request_refresh = AsyncMock()
        facade_coordinator._device_coordinator.async_request_refresh = AsyncMock()
        facade_coordinator._protect_coordinator.async_request_refresh = AsyncMock()

        await facade_coordinator.async_request_refresh()

        facade_coordinator._config_coordinator.async_request_refresh.assert_called_once()
        facade_coordinator._device_coordinator.async_request_refresh.assert_called_once()
        facade_coordinator._protect_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_request_refresh_no_protect(
        self, facade_coordinator_no_protect: UnifiFacadeCoordinator
    ):
        """Test async request refresh without protect."""
        facade_coordinator_no_protect._config_coordinator.async_request_refresh = (
            AsyncMock()
        )
        facade_coordinator_no_protect._device_coordinator.async_request_refresh = (
            AsyncMock()
        )

        await facade_coordinator_no_protect.async_request_refresh()

        facade_coordinator_no_protect._config_coordinator.async_request_refresh.assert_called_once()
        facade_coordinator_no_protect._device_coordinator.async_request_refresh.assert_called_once()

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

    def test_setup_websocket_callbacks_no_register_device_callback(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test setup when protect_client lacks register_device_update_callback."""
        network_client = _create_mock_network_client()
        protect_client = MagicMock()
        # Remove register_device_update_callback from spec
        del protect_client.register_device_update_callback
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

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        # Should not raise and event callback should still be registered
        protect_client.register_event_update_callback.assert_called_once()
        assert coordinator.protect_client is not None

    def test_setup_websocket_callbacks_no_register_event_callback(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test setup when protect_client lacks register_event_update_callback."""
        network_client = _create_mock_network_client()
        protect_client = MagicMock()
        protect_client.register_device_update_callback = MagicMock()
        # Remove register_event_update_callback from spec
        del protect_client.register_event_update_callback
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

        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )

        # Should not raise and device callback should still be registered
        protect_client.register_device_update_callback.assert_called_once()
        assert coordinator.protect_client is not None

    def test_setup_websocket_callbacks_exception(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test setup when callback registration raises exception."""
        network_client = _create_mock_network_client()
        protect_client = MagicMock()
        protect_client.register_device_update_callback = MagicMock(
            side_effect=Exception("Registration failed")
        )
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

        # Should not raise
        coordinator = UnifiProtectCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=mock_config_entry,
        )
        assert coordinator.protect_client is not None

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
        """Test camera fetch when feature_flags is not a dict."""
        camera_mock = MagicMock()
        camera_mock.id = "camera1"
        camera_mock.name = "Test Camera"
        camera_mock.feature_flags = "not_a_dict"  # Invalid type
        # Make model_dump return the non-dict feature_flags
        camera_mock.model_dump = MagicMock(
            return_value={
                "id": "camera1",
                "name": "Test Camera",
                "feature_flags": "not_a_dict",
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
