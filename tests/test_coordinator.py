"""Tests for UniFi Insights coordinator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiResponseError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights.coordinator import (
    UnifiInsightsDataUpdateCoordinator,
)


def _create_mock_model(**kwargs):
    """Create a mock model that properly handles model_dump."""
    mock = MagicMock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    # Use by_alias=True to simulate pydantic behavior (return dict as-is for test)
    mock.model_dump = MagicMock(return_value=kwargs)
    return mock


@pytest.fixture
def mock_network_client_for_coordinator():
    """Create a mock network client for coordinator tests."""
    client = MagicMock()
    client.base_url = "https://192.168.1.1"

    # Setup sites namespace
    client.sites = MagicMock()
    client.sites.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="site1",
                name="Default",
            )
        ]
    )

    # Setup devices namespace
    client.devices = MagicMock()
    client.devices.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="device1",
                name="Test Device",
                model="USW-24",
                mac="AA:BB:CC:DD:EE:FF",
                state="ONLINE",
                ipAddress="192.168.1.10",
            )
        ]
    )
    client.devices.get_statistics = AsyncMock(
        return_value=_create_mock_model(
            cpuUtilizationPct=10.5,
            memoryUtilizationPct=25.3,
            uptimeSec=12345,
        )
    )

    # Setup clients namespace
    client.clients = MagicMock()
    client.clients.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="client1",
                name="Test Client",
                type="WIRED",
                uplink_device_id="device1",
            )
        ]
    )

    # Setup WiFi namespace
    client.wifi = MagicMock()
    client.wifi.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="wifi1",
                name="Test WiFi",
                ssid="TestNetwork",
                enabled=True,
            )
        ]
    )

    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_protect_client_for_coordinator():
    """Create a mock protect client for coordinator tests."""
    client = MagicMock()
    client.base_url = "https://192.168.1.1"

    # Setup cameras namespace
    client.cameras = MagicMock()
    client.cameras.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="camera1",
                name="Front Door",
                state="CONNECTED",
                type="UVC-G4-DOORBELL",
                mac="11:22:33:44:55:66",
                feature_flags={"smart_detect_types": ["person", "vehicle"]},
            )
        ]
    )

    # Setup lights namespace
    client.lights = MagicMock()
    client.lights.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="light1",
                name="Test Light",
                state="CONNECTED",
            )
        ]
    )

    # Setup sensors namespace
    client.sensors = MagicMock()
    client.sensors.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="sensor1",
                name="Test Sensor",
                state="CONNECTED",
                batteryStatus={"percentage": 85},
            )
        ]
    )

    # Setup chimes namespace
    client.chimes = MagicMock()
    client.chimes.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="chime1",
                name="Ding Dong",
                state="CONNECTED",
            )
        ]
    )

    # Setup viewers namespace
    client.viewers = MagicMock()
    client.viewers.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="viewer1",
                name="Test Viewer",
                state="CONNECTED",
            )
        ]
    )

    # Setup liveviews namespace
    client.liveviews = MagicMock()
    client.liveviews.get_all = AsyncMock(
        return_value=[
            _create_mock_model(
                id="liveview1",
                name="Test Liveview",
                layout=1,
            )
        ]
    )

    # Setup NVR namespace
    client.nvr = MagicMock()
    client.nvr.get = AsyncMock(
        return_value=_create_mock_model(id="nvr1", name="NVR", type="UNVR")
    )

    # WebSocket stubs (not yet implemented in library)
    client.register_device_update_callback = None
    client.register_event_update_callback = None

    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_config_entry_for_coordinator():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {}
    return entry


async def test_coordinator_init(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator initialization."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    assert coordinator.network_client == mock_network_client_for_coordinator
    assert coordinator.protect_client == mock_protect_client_for_coordinator
    assert coordinator.available is True
    assert coordinator.data["sites"] == {}
    assert coordinator.data["devices"] == {}
    assert coordinator.data["clients"] == {}


async def test_coordinator_init_without_protect(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator initialization without Protect client."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    assert coordinator.network_client == mock_network_client_for_coordinator
    assert coordinator.protect_client is None


async def test_coordinator_async_update_data(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator data update."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Run the update
    data = await coordinator._async_update_data()

    # Verify sites were fetched
    assert "site1" in data["sites"]

    # Verify devices were fetched
    assert "site1" in data["devices"]
    assert "device1" in data["devices"]["site1"]

    # Verify stats were fetched
    assert "site1" in data["stats"]
    assert "device1" in data["stats"]["site1"]

    # Verify clients were fetched
    assert "site1" in data["clients"]

    # Verify protect data was fetched
    assert "camera1" in data["protect"]["cameras"]
    assert "light1" in data["protect"]["lights"]
    assert "chime1" in data["protect"]["chimes"]
    assert "nvr1" in data["protect"]["nvrs"]
    assert "sensor1" in data["protect"]["sensors"]
    sensor_data = data["protect"]["sensors"]["sensor1"]
    assert sensor_data.get("name") == "Test Sensor"
    assert "viewer1" in data["protect"]["viewers"]
    viewer_data = data["protect"]["viewers"]["viewer1"]
    assert viewer_data.get("name") == "Test Viewer"
    assert "liveview1" in data["protect"]["liveviews"]
    liveview_data = data["protect"]["liveviews"]["liveview1"]
    assert liveview_data.get("name") == "Test Liveview"

    # Verify WiFi networks were fetched
    assert "site1" in data["wifi"]
    assert "wifi1" in data["wifi"]["site1"]
    wifi_data = data["wifi"]["site1"]["wifi1"]
    assert wifi_data.get("name") == "Test WiFi"
    assert wifi_data.get("ssid") == "TestNetwork"

    # Verify last_update was set
    assert data["last_update"] is not None


async def test_coordinator_auth_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles auth errors."""
    mock_network_client_for_coordinator.sites.get_all = AsyncMock(
        side_effect=UniFiAuthenticationError("Auth failed")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_connection_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles connection errors."""
    mock_network_client_for_coordinator.sites.get_all = AsyncMock(
        side_effect=UniFiConnectionError("Connection failed")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_timeout_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles timeout errors."""
    mock_network_client_for_coordinator.sites.get_all = AsyncMock(
        side_effect=UniFiTimeoutError("Timeout")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_response_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles response errors."""
    mock_network_client_for_coordinator.sites.get_all = AsyncMock(
        side_effect=UniFiResponseError("Bad response", status_code=500)
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_get_site(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator get_site method."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data
    coordinator.data["sites"] = {"site1": {"id": "site1", "name": "Test Site"}}

    # Test valid site
    site = coordinator.get_site("site1")
    assert site is not None
    assert site["name"] == "Test Site"

    # Test invalid site
    site = coordinator.get_site("nonexistent")
    assert site is None


async def test_coordinator_get_device(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator get_device method."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data
    coordinator.data["devices"] = {
        "site1": {"device1": {"id": "device1", "name": "Test Device"}}
    }

    # Test valid device
    device = coordinator.get_device("site1", "device1")
    assert device is not None
    assert device["name"] == "Test Device"

    # Test invalid device
    device = coordinator.get_device("site1", "nonexistent")
    assert device is None

    # Test invalid site
    device = coordinator.get_device("nonexistent", "device1")
    assert device is None


async def test_coordinator_get_device_stats(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator get_device_stats method."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data
    coordinator.data["stats"] = {
        "site1": {"device1": {"cpuUtilizationPct": 10.5, "memoryUtilizationPct": 25.3}}
    }

    # Test valid stats
    stats = coordinator.get_device_stats("site1", "device1")
    assert stats is not None
    assert stats["cpuUtilizationPct"] == 10.5

    # Test invalid device
    stats = coordinator.get_device_stats("site1", "nonexistent")
    assert stats is None


async def test_coordinator_model_to_dict_pydantic(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict with pydantic model."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Create a mock pydantic model
    mock_model = MagicMock()
    mock_model.model_dump = MagicMock(return_value={"id": "test", "name": "Test"})

    result = coordinator._model_to_dict(mock_model)
    assert result == {"id": "test", "name": "Test"}


async def test_coordinator_model_to_dict_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict with regular dict."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Test with dict
    result = coordinator._model_to_dict({"id": "test", "name": "Test"})
    assert result == {"id": "test", "name": "Test"}


async def test_coordinator_model_to_dict_none(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict with None."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    result = coordinator._model_to_dict(None)
    assert result == {}


async def test_coordinator_handle_device_update(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_device_update method."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Test camera update
    camera_data = {"id": "camera1", "name": "Updated Camera", "state": "CONNECTED"}
    coordinator._handle_device_update("camera", camera_data)
    assert coordinator.data["protect"]["cameras"]["camera1"] == camera_data

    # Test light update
    light_data = {"id": "light1", "name": "Updated Light", "state": "CONNECTED"}
    coordinator._handle_device_update("light", light_data)
    assert coordinator.data["protect"]["lights"]["light1"] == light_data

    # Test sensor update
    sensor_data = {"id": "sensor1", "name": "Updated Sensor", "state": "CONNECTED"}
    coordinator._handle_device_update("sensor", sensor_data)
    assert coordinator.data["protect"]["sensors"]["sensor1"] == sensor_data

    # Test nvr update
    nvr_data = {"id": "nvr1", "name": "Updated NVR", "state": "CONNECTED"}
    coordinator._handle_device_update("nvr", nvr_data)
    assert coordinator.data["protect"]["nvrs"]["nvr1"] == nvr_data

    # Test chime update
    chime_data = {"id": "chime1", "name": "Updated Chime", "state": "CONNECTED"}
    coordinator._handle_device_update("chime", chime_data)
    assert coordinator.data["protect"]["chimes"]["chime1"] == chime_data

    # Test viewer update
    viewer_data = {"id": "viewer1", "name": "Updated Viewer", "state": "CONNECTED"}
    coordinator._handle_device_update("viewer", viewer_data)
    assert coordinator.data["protect"]["viewers"]["viewer1"] == viewer_data

    # Test update without ID (should be ignored)
    coordinator._handle_device_update("camera", {"name": "No ID"})


async def test_coordinator_handle_event_update_motion(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update for motion events."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up a camera
    coordinator.data["protect"]["cameras"]["camera1"] = {
        "id": "camera1",
        "name": "Test Camera",
    }

    # Test motion event
    event_data = {
        "id": "event1",
        "device": "camera1",
        "start": 1234567890,
        "end": None,
    }
    coordinator._handle_event_update("motion", event_data)

    # Verify event was stored
    assert "motion" in coordinator.data["protect"]["events"]
    assert "event1" in coordinator.data["protect"]["events"]["motion"]

    # Verify camera was updated
    assert (
        coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"]
        == 1234567890
    )
    assert coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] is None


async def test_coordinator_handle_event_update_smart_detect(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update for smart detection events."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up a camera
    coordinator.data["protect"]["cameras"]["camera1"] = {
        "id": "camera1",
        "name": "Test Camera",
    }

    # Test smart detect event
    event_data = {
        "id": "event2",
        "device": "camera1",
        "start": 1234567890,
        "end": None,
        "smartDetectTypes": ["person"],
    }
    coordinator._handle_event_update("smartDetectZone", event_data)

    # Verify camera was updated with smart detect types
    assert coordinator.data["protect"]["cameras"]["camera1"][
        "lastSmartDetectTypes"
    ] == ["person"]


async def test_coordinator_handle_event_update_ring(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update for ring events."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up a camera
    coordinator.data["protect"]["cameras"]["camera1"] = {
        "id": "camera1",
        "name": "Test Doorbell",
    }

    # Test ring event
    event_data = {
        "id": "event3",
        "device": "camera1",
        "start": 1234567890,
        "end": None,
    }
    coordinator._handle_event_update("ring", event_data)

    # Verify camera was updated
    assert (
        coordinator.data["protect"]["cameras"]["camera1"]["lastRingStart"] == 1234567890
    )
    assert coordinator.data["protect"]["cameras"]["camera1"]["lastRingEnd"] is None


async def test_coordinator_handle_event_update_light_motion(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update for light motion events."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up a light
    coordinator.data["protect"]["lights"]["light1"] = {
        "id": "light1",
        "name": "Test Light",
    }

    # Test motion event for light
    event_data = {
        "id": "event4",
        "device": "light1",
        "start": 1234567890,
        "end": None,
    }
    coordinator._handle_event_update("motion", event_data)

    # Verify light was updated
    assert (
        coordinator.data["protect"]["lights"]["light1"]["lastMotionStart"] == 1234567890
    )


async def test_coordinator_available_property(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator available property."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Initially available
    assert coordinator.available is True

    # After error, not available
    coordinator._available = False
    assert coordinator.available is False


async def test_coordinator_with_websocket_callbacks(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator registers WebSocket callbacks when available."""
    # Create protect client with WebSocket callbacks
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Add the callback registration methods
    callback_holder = {}

    def register_device_callback(callback):
        callback_holder["device"] = callback

    def register_event_callback(callback):
        callback_holder["event"] = callback

    protect_client.register_device_update_callback = register_device_callback
    protect_client.register_event_update_callback = register_event_callback

    # Setup required namespaces
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])
    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Verify callbacks were registered
    assert "device" in callback_holder
    assert "event" in callback_holder
    assert callback_holder["device"] == coordinator._handle_device_update
    assert callback_holder["event"] == coordinator._handle_event_update


async def test_coordinator_websocket_callback_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles errors when registering WebSocket callbacks."""
    # Create protect client with WebSocket callbacks that raise errors
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    def raise_error(callback):
        msg = "WebSocket not supported"
        raise RuntimeError(msg)

    protect_client.register_device_update_callback = raise_error
    protect_client.register_event_update_callback = raise_error

    # Should not raise - error is caught and logged
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    assert coordinator is not None


async def test_coordinator_handle_event_update_no_id(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update ignores events without ID."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Event without ID should be ignored
    coordinator._handle_event_update("motion", {"device": "camera1"})
    assert "motion" not in coordinator.data["protect"]["events"]


async def test_coordinator_handle_event_update_no_device(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update handles events without device ID."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Event with ID but no device should still be stored
    event_data = {"id": "event1", "type": "system"}
    coordinator._handle_event_update("system", event_data)

    assert "system" in coordinator.data["protect"]["events"]
    assert "event1" in coordinator.data["protect"]["events"]["system"]


async def test_coordinator_handle_event_update_unknown_device(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update handles events for unknown devices."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Motion event for unknown camera should not crash
    event_data = {"id": "event1", "device": "unknown_camera", "start": 123456}
    coordinator._handle_event_update("motion", event_data)

    # Event should still be stored
    assert "motion" in coordinator.data["protect"]["events"]


async def test_coordinator_model_to_dict_object_with_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict with object using __dict__."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Create an object without model_dump but with __dict__
    class SimpleObject:
        def __init__(self):
            self.id = "test"
            self.name = "Test"
            self._private = "hidden"

    obj = SimpleObject()
    result = coordinator._model_to_dict(obj)

    assert result == {"id": "test", "name": "Test"}
    assert "_private" not in result


async def test_coordinator_model_to_dict_model_dump_type_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict handles TypeError from model_dump."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Create a mock model that raises TypeError on by_alias
    mock_model = MagicMock()

    def model_dump_impl(**kwargs):
        _ = kwargs  # unused since we check below
        msg = "by_alias not supported"
        raise TypeError(msg)

    mock_model.model_dump = MagicMock(side_effect=model_dump_impl)
    # Fix: Reset side effect for fallback call
    mock_model.model_dump = MagicMock()
    mock_model.model_dump.side_effect = [
        TypeError("by_alias not supported"),
        {"id": "fallback"},
    ]

    result = coordinator._model_to_dict(mock_model)
    assert result == {"id": "fallback"}


async def test_coordinator_model_to_dict_model_dump_returns_non_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict handles model_dump returning non-dict."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Create a mock model that returns a non-dict
    mock_model = MagicMock()
    mock_model.model_dump = MagicMock(return_value="not a dict")

    result = coordinator._model_to_dict(mock_model)
    assert result == {}


async def test_coordinator_model_to_dict_primitive(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _model_to_dict with primitive types."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Primitive without __dict__ attribute should return empty dict
    result = coordinator._model_to_dict("string")
    assert result == {}


async def test_coordinator_process_device_stats_success(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _process_device returns stats with client data on success."""
    # Setup get_statistics to return valid data
    mock_network_client_for_coordinator.devices.get_statistics = AsyncMock(
        return_value=_create_mock_model(
            cpuUtilizationPct=15.0,
            memoryUtilizationPct=30.0,
            uptimeSec=99999,
        )
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    device_dict = {"id": "device1", "name": "Test Device"}
    # Add clients that match the device (using both camelCase and snake_case)
    clients = [
        {"id": "client1", "name": "Client 1", "uplinkDeviceId": "device1"},
        {"id": "client2", "name": "Client 2", "uplink_device_id": "device1"},
        {"id": "client3", "name": "Client 3", "uplinkDeviceId": "other_device"},
    ]

    device_id, device, stats = await coordinator._process_device(
        "site1", device_dict, clients
    )

    assert device_id == "device1"
    assert device == device_dict
    # Verify stats has expected values
    assert stats.get("cpuUtilizationPct") == 15.0
    assert stats.get("memoryUtilizationPct") == 30.0
    # Verify clients were filtered to only matching device
    assert stats.get("id") == "device1"
    assert len(stats.get("clients", [])) == 2
    # Verify only clients with matching device are included
    client_ids = [c["id"] for c in stats["clients"]]
    assert "client1" in client_ids
    assert "client2" in client_ids
    assert "client3" not in client_ids


async def test_coordinator_process_device_stats_none(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _process_device handles None stats (skips client filtering)."""
    # Return None from get_statistics - this covers the 284->294 branch
    mock_network_client_for_coordinator.devices.get_statistics = AsyncMock(
        return_value=None
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    device_dict = {"id": "device1", "name": "Test Device"}
    clients = [{"id": "client1", "name": "Client 1", "uplinkDeviceId": "device1"}]

    device_id, device, stats = await coordinator._process_device(
        "site1", device_dict, clients
    )

    assert device_id == "device1"
    assert device == device_dict
    # Stats should be empty dict when get_statistics returns None
    assert stats == {}
    # Clients should NOT be added since stats is empty
    assert "clients" not in stats


async def test_coordinator_process_device_stats_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _process_device handles stats errors gracefully."""
    # Make get_statistics fail
    mock_network_client_for_coordinator.devices.get_statistics = AsyncMock(
        side_effect=Exception("Stats error")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    device_dict = {"id": "device1", "name": "Test Device"}
    clients = []

    device_id, device, stats = await coordinator._process_device(
        "site1", device_dict, clients
    )

    assert device_id == "device1"
    assert device == device_dict
    assert stats == {}  # Empty stats on error


async def test_coordinator_process_site_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _process_site handles errors gracefully."""
    # Make devices.get_all fail
    mock_network_client_for_coordinator.devices.get_all = AsyncMock(
        side_effect=Exception("Site processing error")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    result = await coordinator._process_site("site1")
    assert result is None


async def test_coordinator_protect_fetch_errors(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles Protect fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Setup cameras to succeed
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])

    # Setup lights to succeed
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])

    # Setup sensors to fail
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(side_effect=Exception("Sensors error"))

    # Setup chimes to fail
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(side_effect=Exception("Chimes error"))

    # Setup NVR to fail
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(side_effect=Exception("NVR error"))

    # Setup viewers to fail
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(side_effect=Exception("Viewers error"))

    # Setup liveviews to fail
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(
        side_effect=Exception("Liveviews error")
    )

    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Should complete without raising
    data = await coordinator._async_update_data()

    # Data should still be returned
    assert data is not None
    assert data["protect"]["sensors"] == {}
    assert data["protect"]["chimes"] == {}


async def test_coordinator_protect_general_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles general Protect errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Setup cameras to fail immediately
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(
        side_effect=Exception("General protect error")
    )

    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Should complete without raising
    data = await coordinator._async_update_data()
    assert data is not None


async def test_coordinator_get_site_non_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test get_site returns None for non-dict values."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data with non-dict value
    coordinator.data["sites"] = {"site1": "not a dict"}

    result = coordinator.get_site("site1")
    assert result is None


async def test_coordinator_get_device_non_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test get_device returns None for non-dict values."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data with non-dict value
    coordinator.data["devices"] = {"site1": {"device1": "not a dict"}}

    result = coordinator.get_device("site1", "device1")
    assert result is None


async def test_coordinator_get_device_stats_non_dict(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test get_device_stats returns None for non-dict values."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up test data with non-dict value
    coordinator.data["stats"] = {"site1": {"device1": "not a dict"}}

    result = coordinator.get_device_stats("site1", "device1")
    assert result is None


async def test_coordinator_unexpected_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles unexpected errors."""
    mock_network_client_for_coordinator.sites.get_all = AsyncMock(
        side_effect=RuntimeError("Unexpected error")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    with pytest.raises(UpdateFailed, match="Error updating data"):
        await coordinator._async_update_data()

    assert coordinator.available is False


async def test_coordinator_cleanup_stale_devices(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _cleanup_stale_devices removes stale devices."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up previous device IDs
    coordinator._previous_network_device_ids = {"site1_device1", "site1_device2"}

    # Current data only has device1
    coordinator.data["devices"] = {"site1": {"device1": {"id": "device1"}}}

    # Call cleanup
    coordinator._cleanup_stale_devices()

    # Previous IDs should be updated
    assert coordinator._previous_network_device_ids == {"site1_device1"}


async def test_coordinator_cleanup_stale_network_device_removal(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _cleanup_stale_devices removes stale network device from registry."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up previous device IDs (device2 was previously known but no longer exists)
    coordinator._previous_network_device_ids = {"site1_device1", "site1_device2"}

    # Current data only has device1
    coordinator.data["devices"] = {"site1": {"device1": {"id": "device1"}}}

    # Mock the device registry
    mock_device = MagicMock()
    mock_device.id = "registry_device_id"

    with (
        patch(
            "custom_components.unifi_insights.coordinator.dr.async_get"
        ) as mock_async_get,
    ):
        mock_registry = MagicMock()
        mock_registry.async_get_device.return_value = mock_device
        mock_async_get.return_value = mock_registry

        # Call cleanup
        coordinator._cleanup_stale_devices()

        # Verify device was looked up
        mock_registry.async_get_device.assert_called_with(
            identifiers={("unifi_insights", "site1_device2")}
        )

        # Verify device was removed from registry
        mock_registry.async_update_device.assert_called_with(
            device_id="registry_device_id",
            remove_config_entry_id=mock_config_entry_for_coordinator.entry_id,
        )


async def test_coordinator_cleanup_stale_protect_devices(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _cleanup_stale_devices removes stale Protect devices."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Set up previous Protect device IDs
    coordinator._previous_protect_device_ids = {
        "cameras": {"camera1", "camera2"},
        "lights": {"light1"},
        "sensors": set(),
        "nvrs": set(),
        "viewers": set(),
        "chimes": set(),
    }

    # Current data only has camera1
    coordinator.data["protect"]["cameras"] = {"camera1": {"id": "camera1"}}
    coordinator.data["protect"]["lights"] = {}

    # Call cleanup
    coordinator._cleanup_stale_devices()

    # Previous IDs should be updated
    assert coordinator._previous_protect_device_ids["cameras"] == {"camera1"}
    assert coordinator._previous_protect_device_ids["lights"] == set()


async def test_coordinator_camera_with_non_dict_feature_flags(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles cameras with non-dict feature_flags."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Setup camera with non-dict feature_flags
    camera_model = _create_mock_model(
        id="camera1",
        name="Test Camera",
        state="CONNECTED",
        feature_flags="not a dict",  # This should be handled
    )
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[camera_model])

    # Setup other endpoints
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])
    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()

    # Camera should have empty smartDetectTypes
    assert data["protect"]["cameras"]["camera1"]["smartDetectTypes"] == []


async def test_coordinator_nvr_with_empty_result(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles NVR returning empty/None result."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Setup camera, lights, etc.
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])

    # NVR returns None
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)

    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])
    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()
    assert data["protect"]["nvrs"] == {}


async def test_coordinator_nvr_without_id(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles NVR data without ID."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    # Setup other endpoints
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])

    # NVR returns data without ID
    nvr_model = _create_mock_model(name="NVR", type="UNVR")  # No id field
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=nvr_model)

    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])
    protect_client.close = AsyncMock()

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()
    # NVR without ID should not be stored
    assert data["protect"]["nvrs"] == {}


async def test_coordinator_handle_device_update_viewer(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles viewer device updates."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Call _handle_device_update for viewer
    coordinator._handle_device_update("viewer", {"id": "viewer1", "name": "Viewer 1"})

    assert "viewer1" in coordinator.data["protect"]["viewers"]
    assert coordinator.data["protect"]["viewers"]["viewer1"]["name"] == "Viewer 1"


async def test_coordinator_handle_device_update_chime(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles chime device updates."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Call _handle_device_update for chime
    coordinator._handle_device_update("chime", {"id": "chime1", "name": "Chime 1"})

    assert "chime1" in coordinator.data["protect"]["chimes"]
    assert coordinator.data["protect"]["chimes"]["chime1"]["name"] == "Chime 1"


async def test_coordinator_handle_device_update_sensor(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles sensor device updates."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Call _handle_device_update for sensor
    coordinator._handle_device_update("sensor", {"id": "sensor1", "name": "Sensor 1"})

    assert "sensor1" in coordinator.data["protect"]["sensors"]


async def test_coordinator_handle_device_update_nvr(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles NVR device updates."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Call _handle_device_update for NVR
    coordinator._handle_device_update("nvr", {"id": "nvr1", "name": "NVR 1"})

    assert "nvr1" in coordinator.data["protect"]["nvrs"]


async def test_coordinator_wifi_fetch_error(
    hass: HomeAssistant,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles WiFi fetch errors gracefully."""
    network_client = MagicMock()
    network_client.base_url = "https://192.168.1.1"

    # Sites return successfully
    site_mock = _create_mock_model(id="site1")
    network_client.sites = MagicMock()
    network_client.sites.get_all = AsyncMock(return_value=[site_mock])

    # Devices return successfully
    network_client.devices = MagicMock()
    network_client.devices.get_all = AsyncMock(return_value=[])

    # Clients return successfully
    network_client.clients = MagicMock()
    network_client.clients.get_all = AsyncMock(return_value=[])

    # WiFi raises an exception
    network_client.wifi = MagicMock()
    network_client.wifi.get_all = AsyncMock(side_effect=Exception("WiFi fetch failed"))

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=None,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()
    # WiFi should be empty dict for the site
    assert data["wifi"]["site1"] == {}


async def test_coordinator_chimes_fetch_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles chimes fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)

    # Chimes raises error
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(
        side_effect=Exception("Chimes fetch failed")
    )

    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Should not raise
    data = await coordinator._async_update_data()
    assert data["protect"]["chimes"] == {}


async def test_coordinator_viewers_fetch_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles viewers fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])

    # Viewers raises error
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(
        side_effect=Exception("Viewers fetch failed")
    )

    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Should not raise
    data = await coordinator._async_update_data()
    assert data["protect"]["viewers"] == {}


async def test_coordinator_liveviews_fetch_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles liveviews fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])

    # Liveviews raises error
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(
        side_effect=Exception("Liveviews fetch failed")
    )

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    # Should not raise
    data = await coordinator._async_update_data()
    assert data["protect"]["liveviews"] == {}


async def test_coordinator_cleanup_stale_protect_devices_with_identifier_match(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
):
    """Test coordinator cleanup removes protect devices by identifier."""
    # Create a real config entry
    config_entry = MockConfigEntry(
        domain="unifi_insights",
        data={"host": "192.168.1.1", "api_key": "test_key"},
        entry_id="test_cleanup_entry",
    )
    config_entry.add_to_hass(hass)

    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"
    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=config_entry,
    )

    # Set previous IDs
    coordinator._previous_protect_device_ids["cameras"] = {"old_camera1"}

    # Register a device that should be cleaned up
    device_registry = dr.async_get(hass)

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("unifi_insights", "protect_camera_old_camera1")},
        name="Old Camera",
    )

    # Run update which triggers cleanup
    await coordinator._async_update_data()

    # Verify the cleanup logic was called - previous IDs should be updated
    assert coordinator._previous_protect_device_ids["cameras"] == set()


async def test_coordinator_handle_event_update_no_event_id(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update returns early when no event_id."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Call with event data missing id - should return early
    coordinator._handle_event_update("motion", {"device": "camera1", "start": 123})

    # Events should be empty since it returned early
    assert coordinator.data["protect"]["events"] == {}


async def test_coordinator_handle_event_update_no_device_id(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_event_update stores event without updating device."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Call with event that has id but no device
    coordinator._handle_event_update("motion", {"id": "event1", "start": 123})

    # Event should be stored
    assert "motion" in coordinator.data["protect"]["events"]
    assert "event1" in coordinator.data["protect"]["events"]["motion"]


async def test_coordinator_handle_device_update_unknown_type(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_protect_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test _handle_device_update with unknown device type."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=mock_protect_client_for_coordinator,
        entry=mock_config_entry_for_coordinator,
    )

    # Mock async_update_listeners
    coordinator.async_update_listeners = MagicMock()

    # Call with unknown device type
    device_data = {"id": "unknown1", "name": "Unknown Device"}
    coordinator._handle_device_update("unknown_type", device_data)

    # Should call async_update_listeners but not add to any known dict
    coordinator.async_update_listeners.assert_called_once()
    # Verify device was not added to any known collection
    assert "unknown1" not in coordinator.data["protect"]["cameras"]
    assert "unknown1" not in coordinator.data["protect"]["lights"]
    assert "unknown1" not in coordinator.data["protect"]["sensors"]


async def test_coordinator_sensors_fetch_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles sensors fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])

    # Sensors raises error
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(
        side_effect=Exception("Sensors fetch failed")
    )

    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(return_value=None)
    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()
    # Sensors should be empty
    assert data["protect"]["sensors"] == {}


async def test_coordinator_nvr_fetch_error(
    hass: HomeAssistant,
    mock_network_client_for_coordinator,
    mock_config_entry_for_coordinator,
):
    """Test coordinator handles NVR fetch errors gracefully."""
    protect_client = MagicMock()
    protect_client.base_url = "https://192.168.1.1"

    protect_client.cameras = MagicMock()
    protect_client.cameras.get_all = AsyncMock(return_value=[])
    protect_client.lights = MagicMock()
    protect_client.lights.get_all = AsyncMock(return_value=[])
    protect_client.sensors = MagicMock()
    protect_client.sensors.get_all = AsyncMock(return_value=[])

    # NVR raises error
    protect_client.nvr = MagicMock()
    protect_client.nvr.get = AsyncMock(side_effect=Exception("NVR fetch failed"))

    protect_client.chimes = MagicMock()
    protect_client.chimes.get_all = AsyncMock(return_value=[])
    protect_client.viewers = MagicMock()
    protect_client.viewers.get_all = AsyncMock(return_value=[])
    protect_client.liveviews = MagicMock()
    protect_client.liveviews.get_all = AsyncMock(return_value=[])

    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        network_client=mock_network_client_for_coordinator,
        protect_client=protect_client,
        entry=mock_config_entry_for_coordinator,
    )

    data = await coordinator._async_update_data()
    # NVRs should be empty
    assert data["protect"]["nvrs"] == {}
