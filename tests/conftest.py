"""Test fixtures for ha-unifi-insights integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_network_client() -> Generator[MagicMock]:
    """Return a mocked UniFi Network client."""
    with patch(
        "custom_components.unifi_insights.UniFiNetworkClient", autospec=True
    ) as mock:
        client = mock.return_value
        client.base_url = "https://192.168.1.1"

        # Setup sites namespace
        client.sites = MagicMock()
        client.sites.get_all = AsyncMock(
            return_value=[MagicMock(id="default", name="Default", desc="Default")]
        )

        # Setup devices namespace
        client.devices = MagicMock()
        client.devices.get_all = AsyncMock(
            return_value=[
                MagicMock(
                    id="device1",
                    name="Test Device",
                    model="USW-24",
                    mac="AA:BB:CC:DD:EE:FF",
                    state="ONLINE",
                    ipAddress="192.168.1.10",
                )
            ]
        )
        client.devices.get = AsyncMock(
            return_value=MagicMock(id="device1", name="Test Device", model="USW-24")
        )
        client.devices.get_statistics = AsyncMock(
            return_value=MagicMock(cpu=10.5, mem=25.3)
        )
        client.devices.restart = AsyncMock(return_value=True)

        # Setup clients namespace
        client.clients = MagicMock()
        client.clients.get_all = AsyncMock(return_value=[])
        client.clients.authorize_guest = AsyncMock(return_value=True)

        # Setup vouchers namespace
        client.vouchers = MagicMock()
        client.vouchers.create = AsyncMock(return_value=[MagicMock(id="voucher1")])
        client.vouchers.delete = AsyncMock(return_value=True)

        # Legacy methods (keeping for backwards compatibility in tests)
        client.restart_device = AsyncMock(return_value=True)
        client.authorize_guest = AsyncMock(return_value=True)
        client.generate_voucher = AsyncMock(return_value=[{"id": "voucher1"}])
        client.delete_voucher = AsyncMock(return_value=True)
        client.power_cycle_port = AsyncMock(return_value=True)
        client.close = AsyncMock()
        yield client


@pytest.fixture
def mock_protect_client() -> Generator[MagicMock]:
    """Return a mocked UniFi Protect client."""
    with patch(
        "custom_components.unifi_insights.UniFiProtectClient", autospec=True
    ) as mock:
        client = mock.return_value
        client.base_url = "https://192.168.1.1"

        # Setup cameras namespace
        client.cameras = MagicMock()
        client.cameras.get_all = AsyncMock(
            return_value=[
                MagicMock(
                    id="camera1",
                    name="Front Door",
                    state="CONNECTED",
                    type="UVC-G4-DOORBELL",
                    mac="11:22:33:44:55:66",
                    featureFlags=MagicMock(smartDetectTypes=["person", "vehicle"]),
                )
            ]
        )
        client.cameras.get_snapshot = AsyncMock(return_value=b"fake_image_data")
        client.cameras.create_rtsps_stream = AsyncMock(
            return_value=MagicMock(url="rtsps://192.168.1.1/stream")
        )
        client.cameras.set_recording_mode = AsyncMock(return_value=True)
        client.cameras.set_hdr_mode = AsyncMock(return_value=True)
        client.cameras.set_video_mode = AsyncMock(return_value=True)
        client.cameras.set_microphone_volume = AsyncMock(return_value=True)

        # Setup lights namespace
        client.lights = MagicMock()
        client.lights.get_all = AsyncMock(return_value=[])
        client.lights.set_mode = AsyncMock(return_value=True)
        client.lights.set_brightness = AsyncMock(return_value=True)

        # Setup sensors namespace
        client.sensors = MagicMock()
        client.sensors.get_all = AsyncMock(return_value=[])

        # Setup chimes namespace
        client.chimes = MagicMock()
        client.chimes.get_all = AsyncMock(return_value=[])
        client.chimes.play = AsyncMock(return_value=True)
        client.chimes.set_volume = AsyncMock(return_value=True)
        client.chimes.set_ringtone = AsyncMock(return_value=True)
        client.chimes.set_repeat = AsyncMock(return_value=True)

        # Setup viewers namespace (if available)
        client.viewers = MagicMock()
        client.viewers.get_all = AsyncMock(return_value=[])
        client.viewers.update = AsyncMock(return_value=True)

        # Setup liveviews namespace (if available)
        client.liveviews = MagicMock()
        client.liveviews.get_all = AsyncMock(return_value=[])
        client.liveviews.create = AsyncMock(return_value=MagicMock(id="liveview1"))

        # Setup NVR namespace
        client.nvr = MagicMock()
        client.nvr.get = AsyncMock(
            return_value=MagicMock(id="nvr1", name="NVR", type="UNVR")
        )
        client.nvr.restart = AsyncMock(return_value=True)

        # Legacy methods (keeping for backwards compatibility)
        client.update_camera = AsyncMock(return_value=True)
        client.set_hdr_mode = AsyncMock(return_value=True)
        client.set_video_mode = AsyncMock(return_value=True)
        client.set_microphone_volume = AsyncMock(return_value=True)
        client.set_light_mode = AsyncMock(return_value=True)
        client.set_light_brightness = AsyncMock(return_value=True)
        client.ptz_move_to_preset = AsyncMock(return_value=True)
        client.ptz_start_patrol = AsyncMock(return_value=True)
        client.ptz_stop_patrol = AsyncMock(return_value=True)
        client.set_chime_volume = AsyncMock(return_value=True)
        client.play_chime = AsyncMock(return_value=True)
        client.set_chime_ringtone = AsyncMock(return_value=True)
        client.set_chime_repeat = AsyncMock(return_value=True)
        client.trigger_alarm = AsyncMock(return_value=True)
        client.create_liveview = AsyncMock(return_value={"id": "liveview1"})
        client.update_viewer = AsyncMock(return_value=True)
        client.register_device_update_callback = MagicMock()
        client.register_event_update_callback = MagicMock()
        client.start_websocket = AsyncMock()
        client.close = MagicMock()
        yield client


@pytest.fixture
def mock_local_auth() -> Generator[MagicMock]:
    """Return a mocked LocalAuth."""
    with patch("custom_components.unifi_insights.LocalAuth", autospec=True) as mock:
        yield mock.return_value


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return the default mocked config entry."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="UniFi Insights",
        data={
            CONF_HOST: "https://192.168.1.1",
            CONF_API_KEY: "test_api_key",
            CONF_VERIFY_SSL: False,
        },
        options={},
        source="user",
        unique_id="test_unique_id",
        entry_id="test_entry_id",
        discovery_keys={},
        subentries_data={},
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client: MagicMock,
    mock_protect_client: MagicMock,
    mock_local_auth: MagicMock,
) -> ConfigEntry:
    """Set up the integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
