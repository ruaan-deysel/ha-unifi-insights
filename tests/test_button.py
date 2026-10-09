"""Tests for UniFi Insights buttons."""

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
from custom_components.unifi_insights.api.network import UniFiNetworkClient
from custom_components.unifi_insights.button import (
    BUTTON_TYPES,
    UnifiClientReconnectButton,
    UnifiGenerateVoucherButton,
    UnifiInsightsButton,
    UnifiInsightsPoePowerCycleButton,
    UnifiProtectChimePlayButton,
    UnifiProtectPTZPatrolStartButton,
    UnifiProtectPTZPatrolStopButton,
    _get_port_label,
    async_setup_entry,
    get_device_port,
    get_device_ports,
    port_can_be_power_cycled,
)
from custom_components.unifi_insights.const import CONF_CLIENT_CONTROL
from custom_components.unifi_insights.coordinators.facade import (
    UnifiFacadeCoordinator,
)
from custom_components.unifi_insights.coordinators.voucher_state import VoucherSettings
from tests.test_api_network_more_endpoints import _Response, _Session

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class TestButtonTypes:
    """Tests for button type definitions."""

    def test_button_types_defined(self):
        """Test that button types are defined."""
        assert len(BUTTON_TYPES) > 0

    def test_device_restart_button(self):
        """Test device restart button is defined."""
        restart = next((b for b in BUTTON_TYPES if b.key == "device_restart"), None)
        assert restart is not None
        assert restart.name == "Device Restart"
        assert restart.icon == "mdi:restart"


class TestUnifiInsightsButton:
    """Tests for UnifiInsightsButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.network_client.devices.restart = AsyncMock(return_value=True)
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Default"}}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "firmwareVersion": "6.5.55",
                    },
                    "device2": {
                        "id": "device2",
                        "name": "Offline Switch",
                        "model": "USW-24-POE",
                        "state": "OFFLINE",
                        "macAddress": "11:22:33:44:55:66",
                    },
                },
            },
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test button initialization."""
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert button._site_id == "site1"
        assert button._device_id == "device1"

    async def test_button_available_online(self, hass: HomeAssistant, mock_coordinator):
        """Test button available when device online."""
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert button.available is True

    async def test_button_available_offline(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button unavailable when device offline."""
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device2",
        )

        assert button.available is False

    async def test_button_press_success(self, hass: HomeAssistant, mock_coordinator):
        """Test button press success."""
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        await button.async_press()

        mock_coordinator.network_client.devices.restart.assert_called_once_with(
            "site1", "device1"
        )

    async def test_button_press_failure(self, hass: HomeAssistant, mock_coordinator):
        """Test button press failure."""
        mock_coordinator.network_client.devices.restart = AsyncMock(return_value=False)
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        with pytest.raises(HomeAssistantError, match="Unable to restart device"):
            await button.async_press()

        mock_coordinator.network_client.devices.restart.assert_called_once()

    async def test_button_press_exception(self, hass: HomeAssistant, mock_coordinator):
        """Test button press handles exception."""
        mock_coordinator.network_client.devices.restart = AsyncMock(
            side_effect=Exception("API Error")
        )
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        with pytest.raises(HomeAssistantError, match="Unable to restart device"):
            await button.async_press()

    async def test_button_press_uses_facade_restart(
        self, hass: HomeAssistant, mock_coordinator: MagicMock
    ) -> None:
        """The facade coroutine runs when present (no fallback)."""
        mock_coordinator.async_restart_device = AsyncMock(return_value=True)
        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=BUTTON_TYPES[0],
            site_id="site1",
            device_id="device1",
        )

        await button.async_press()

        mock_coordinator.async_restart_device.assert_awaited_once_with(
            "site1", "device1"
        )
        mock_coordinator.network_client.devices.restart.assert_not_called()


class TestUnifiClientReconnectButton:
    """Tests for UnifiClientReconnectButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.network_client.clients = MagicMock()
        coordinator.network_client.clients.reconnect = AsyncMock()
        coordinator.async_reconnect_client = AsyncMock()
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                    },
                },
            },
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "name": "My Laptop",
                        "mac": "11:22:33:44:55:66",
                        "hostname": "laptop",
                        "uplinkDeviceId": "device1",
                    },
                    "client2": {
                        "id": "client2",
                        "mac": "AA:BB:CC:DD:EE:00",
                        "hostname": "unknown",
                    },
                },
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_reconnect_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test client reconnect button initialization."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert button._client_id == "client1"
        assert "My Laptop" in button._attr_name
        assert "Reconnect" in button._attr_name

    async def test_reconnect_button_available(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button available when client exists."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert button.available is True

    async def test_reconnect_button_unavailable_no_client(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button unavailable when client doesn't exist."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="nonexistent",
        )

        assert button.available is False

    async def test_reconnect_button_unavailable_when_device_refresh_fails(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button unavailable while the device refresh is failing."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )
        mock_coordinator.device_available = False

        assert button.available is False

    async def test_reconnect_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test client reconnect button press."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        await button.async_press()

        mock_coordinator.async_reconnect_client.assert_called_once_with(
            "site1", "client1"
        )

    async def test_reconnect_button_press_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test reconnect button handles exception."""
        mock_coordinator.async_reconnect_client = AsyncMock(
            side_effect=Exception("API Error")
        )

        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        with pytest.raises(HomeAssistantError, match="Unable to reconnect client"):
            await button.async_press()


class TestUnifiProtectChimePlayButton:
    """Tests for UnifiProtectChimePlayButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.chimes.play = AsyncMock()
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Front Door Chime",
                        "state": "CONNECTED",
                        "ringSettings": [
                            {"ringtoneId": "mechanical", "cameraId": "camera1"}
                        ],
                    },
                },
                "liveviews": {},
            },
        }
        return coordinator

    async def test_chime_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test chime play button initialization."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert button._device_id == "chime1"
        assert button._attr_translation_key == "play"

    async def test_chime_button_attributes(self, hass: HomeAssistant, mock_coordinator):
        """Test chime button attributes."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        attrs = button.extra_state_attributes
        assert attrs["chime_id"] == "chime1"
        assert attrs["chime_name"] == "Front Door Chime"
        assert attrs["chime_ringtone_id"] == "mechanical"

    async def test_chime_button_press_uses_facade(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """The facade coroutine receives exactly the chime id."""
        mock_coordinator.async_play_chime = AsyncMock()
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        await button.async_press()

        mock_coordinator.async_play_chime.assert_awaited_once_with("chime1")

    async def test_chime_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test chime play button press."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        await button.async_press()

        mock_coordinator.protect_client.chimes.play.assert_awaited_once_with("chime1")

    async def test_chime_button_press_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test chime button handles exception."""
        mock_coordinator.protect_client.chimes.play = AsyncMock(
            side_effect=Exception("API Error")
        )

        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        with pytest.raises(
            HomeAssistantError, match="Unable to play ringtone on chime"
        ):
            await button.async_press()


class TestUnifiProtectPTZButtons:
    """Tests for PTZ patrol buttons."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.ptz_start_patrol = AsyncMock()
        coordinator.protect_client.ptz_stop_patrol = AsyncMock()
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "isPtz": True,
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_ptz_start_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test PTZ patrol start button initialization."""
        button = UnifiProtectPTZPatrolStartButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert button._device_id == "camera1"
        assert button._attr_translation_key == "ptz_patrol_start"

    async def test_ptz_start_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test PTZ patrol start button press."""
        button = UnifiProtectPTZPatrolStartButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        await button.async_press()

        mock_coordinator.protect_client.ptz_start_patrol.assert_called_once_with(
            camera_id="camera1",
            slot=0,
        )

    async def test_ptz_start_button_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test PTZ start button handles exception."""
        mock_coordinator.protect_client.ptz_start_patrol = AsyncMock(
            side_effect=Exception("API Error")
        )

        button = UnifiProtectPTZPatrolStartButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        with pytest.raises(HomeAssistantError, match="Unable to start PTZ patrol"):
            await button.async_press()

    async def test_ptz_stop_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test PTZ patrol stop button initialization."""
        button = UnifiProtectPTZPatrolStopButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert button._device_id == "camera1"
        assert button._attr_translation_key == "ptz_patrol_stop"

    async def test_ptz_stop_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test PTZ patrol stop button press."""
        button = UnifiProtectPTZPatrolStopButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        await button.async_press()

        mock_coordinator.protect_client.ptz_stop_patrol.assert_called_once_with(
            camera_id="camera1",
        )


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.get_site = MagicMock(
            return_value={"id": "site1", "meta": {"name": "Default"}}
        )
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                {"idx": 1, "poe": {"enabled": True}},
                            ],
                        },
                    },
                },
            },
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "isPtz": True,
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Front Door Chime",
                        "state": "CONNECTED",
                    },
                },
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.fixture
    def mock_config_entry(self, mock_coordinator):
        """Create mock config entry."""
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.coordinator = mock_coordinator
        return entry

    async def test_setup_entry_creates_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup entry creates buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        assert len(added_entities) > 0

    async def test_setup_entry_creates_device_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates device restart buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        device_buttons = [
            e for e in added_entities if isinstance(e, UnifiInsightsButton)
        ]
        assert len(device_buttons) > 0

    async def test_setup_entry_creates_chime_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates chime play buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        chime_buttons = [
            e for e in added_entities if isinstance(e, UnifiProtectChimePlayButton)
        ]
        assert len(chime_buttons) > 0

    async def test_setup_entry_creates_ptz_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates PTZ patrol buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        ptz_start_buttons = [
            e for e in added_entities if isinstance(e, UnifiProtectPTZPatrolStartButton)
        ]
        ptz_stop_buttons = [
            e for e in added_entities if isinstance(e, UnifiProtectPTZPatrolStopButton)
        ]
        assert len(ptz_start_buttons) > 0
        assert len(ptz_stop_buttons) > 0

    async def test_setup_entry_without_protect_client(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup without protect client."""
        mock_coordinator.protect_client = None

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should still create device buttons
        device_buttons = [
            e for e in added_entities if isinstance(e, UnifiInsightsButton)
        ]
        assert len(device_buttons) > 0

        # But no protect buttons
        chime_buttons = [
            e for e in added_entities if isinstance(e, UnifiProtectChimePlayButton)
        ]
        assert len(chime_buttons) == 0

    async def test_setup_entry_skips_non_switching_devices(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup skips devices without switching feature."""
        # Add device without switching feature
        mock_coordinator.data["devices"]["site1"]["device2"] = {
            "id": "device2",
            "name": "Access Point",
            "model": "UAP-AC-PRO",
            "state": "ONLINE",
            "features": ["accessPoint"],  # No switching
        }

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

    async def test_setup_entry_dedupes_ptz_and_chime_buttons_on_rediscovery(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Re-running discovery with unchanged data skips already-known buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)
        listener = mock_coordinator.async_add_listener.call_args[0][0]

        first_count = len(added_entities)
        assert first_count > 0

        ptz_start_before = len(
            [
                e
                for e in added_entities
                if isinstance(e, UnifiProtectPTZPatrolStartButton)
            ]
        )
        ptz_stop_before = len(
            [
                e
                for e in added_entities
                if isinstance(e, UnifiProtectPTZPatrolStopButton)
            ]
        )
        chime_before = len(
            [e for e in added_entities if isinstance(e, UnifiProtectChimePlayButton)]
        )

        # Re-run discovery on unchanged data; nothing new should be added.
        listener()

        assert len(added_entities) == first_count
        assert (
            len(
                [
                    e
                    for e in added_entities
                    if isinstance(e, UnifiProtectPTZPatrolStartButton)
                ]
            )
            == ptz_start_before
        )
        assert (
            len(
                [
                    e
                    for e in added_entities
                    if isinstance(e, UnifiProtectPTZPatrolStopButton)
                ]
            )
            == ptz_stop_before
        )
        assert (
            len(
                [
                    e
                    for e in added_entities
                    if isinstance(e, UnifiProtectChimePlayButton)
                ]
            )
            == chime_before
        )

    async def test_setup_entry_dedupes_client_reconnect_button_on_rediscovery(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Reconnect buttons are only created once per client across rediscovery."""
        mock_config_entry.options = {CONF_CLIENT_CONTROL: True}
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "aa:bb:cc:dd:ee:ff",
                "name": "Test Client",
            }
        }

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)
        listener = mock_coordinator.async_add_listener.call_args[0][0]

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        assert len(reconnect_buttons) == 1

        listener()

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        assert len(reconnect_buttons) == 1

    async def test_setup_entry_clients_not_a_dict_is_skipped(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """A non-dict top-level clients collection is skipped without raising."""
        mock_config_entry.options = {CONF_CLIENT_CONTROL: True}
        mock_coordinator.data["clients"] = "not-a-dict"

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        assert len(reconnect_buttons) == 0


class TestClientReconnectButtonEdgeCases:
    """Test edge cases for UnifiClientReconnectButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.network_client.clients = MagicMock()
        coordinator.network_client.clients.reconnect = AsyncMock()
        coordinator.async_reconnect_client = AsyncMock()
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                    },
                },
            },
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "name": None,
                        "hostname": None,
                        "mac": "11:22:33:44:55:66",
                    },
                },
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    async def test_reconnect_button_name_from_mac(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button name defaults to MAC when no name or hostname."""
        button = UnifiClientReconnectButton(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Name should include MAC address
        assert "11:22:33:44:55:66" in button._attr_name


class TestChimePlayButtonEdgeCases:
    """Test edge cases for UnifiProtectChimePlayButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.chimes.play = AsyncMock()
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Front Door Chime",
                        "state": "CONNECTED",
                        "ringSettings": [],  # Empty ring settings
                    },
                },
                "liveviews": {},
            },
        }
        return coordinator

    async def test_chime_button_empty_ring_settings(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test chime button with empty ring settings defaults to 'default'."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        attrs = button.extra_state_attributes
        # When ring settings are empty, defaults to "default"
        assert attrs["chime_ringtone_id"] == "default"

    async def test_chime_button_press_with_empty_ring_settings(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Chime press still plays when the chime has no ring settings."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        await button.async_press()

        mock_coordinator.protect_client.chimes.play.assert_awaited_once_with("chime1")


class TestAsyncSetupEntryWithClients:
    """Tests for async_setup_entry with client data."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator with clients."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = None
        coordinator.get_site = MagicMock(
            return_value={"id": "site1", "meta": {"name": "Default"}}
        )
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "features": ["switching"],
                        "interfaces": {},
                    },
                },
            },
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "name": "Test Client",
                        "mac": "00:11:22:33:44:55",
                    },
                    "client2": {
                        "id": "client2",
                        "hostname": "laptop-hostname",
                        "mac": "66:77:88:99:AA:BB",
                    },
                    "client3": {
                        "id": "client3",
                        "mac": "CC:DD:EE:FF:00:11",
                    },
                },
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.fixture
    def mock_config_entry(self, mock_coordinator):
        """Create mock config entry."""
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.coordinator = mock_coordinator
        return entry

    async def test_setup_entry_creates_client_reconnect_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates client reconnect buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should have client reconnect buttons
        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        assert len(reconnect_buttons) == 3

    async def test_setup_entry_client_button_uses_name(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test client button uses name when available."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        # Find button for client1 which has a name
        client1_button = next(
            (b for b in reconnect_buttons if b._client_id == "client1"), None
        )
        assert client1_button is not None

    async def test_setup_entry_client_button_uses_hostname_fallback(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test client button uses hostname when name not available."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        # Find button for client2 which has hostname but no name
        client2_button = next(
            (b for b in reconnect_buttons if b._client_id == "client2"), None
        )
        assert client2_button is not None

    async def test_setup_entry_client_button_uses_mac_fallback(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test client button uses MAC when name and hostname not available."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        reconnect_buttons = [
            e for e in added_entities if isinstance(e, UnifiClientReconnectButton)
        ]
        # Find button for client3 which only has MAC
        client3_button = next(
            (b for b in reconnect_buttons if b._client_id == "client3"), None
        )
        assert client3_button is not None


class TestUnifiInsightsButtonAvailableEdgeCases:
    """Tests for available property edge cases in UnifiInsightsButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                    },
                },
            },
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_available_devices_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test available returns False when devices is not a dict."""
        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=BUTTON_TYPES[0],
            site_id="site1",
            device_id="device1",
        )

        # Set devices to non-dict value
        mock_coordinator.data["devices"] = "not a dict"
        assert button.available is False

    async def test_available_site_devices_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test available returns False when site_devices is not a dict."""
        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=BUTTON_TYPES[0],
            site_id="site1",
            device_id="device1",
        )

        # Set site devices to non-dict value
        mock_coordinator.data["devices"]["site1"] = "not a dict"
        assert button.available is False

    async def test_available_device_data_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test available returns False when device_data is not a dict."""
        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=BUTTON_TYPES[0],
            site_id="site1",
            device_id="device1",
        )

        # Set device data to non-dict value
        mock_coordinator.data["devices"]["site1"]["device1"] = "not a dict"
        assert button.available is False


class TestPTZPatrolStopButtonException:
    """Tests for PTZ patrol stop button exception handling."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.ptz_stop_patrol = AsyncMock(
            side_effect=Exception("API Error")
        )
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "isPtz": True,
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_ptz_stop_patrol_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test PTZ stop patrol handles exceptions."""
        button = UnifiProtectPTZPatrolStopButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        with pytest.raises(HomeAssistantError, match="Unable to stop PTZ patrol"):
            await button.async_press()

        mock_coordinator.protect_client.ptz_stop_patrol.assert_called_once_with(
            camera_id="camera1",
        )


class TestUnifiInsightsPoePowerCycleButton:
    """Tests for UnifiInsightsPoePowerCycleButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.network_client.devices = MagicMock()
        coordinator.network_client.devices.execute_port_action = AsyncMock()
        coordinator.async_power_cycle_port = AsyncMock()
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "interfaces": {
                            "ports": [
                                {
                                    "idx": 1,
                                    "name": "Port 1",
                                    "poe": {"enabled": True},
                                },
                            ]
                        },
                    },
                },
            },
        }
        return coordinator

    async def test_poe_power_cycle_button_init(
        self, hass: HomeAssistant, mock_coordinator: MagicMock
    ) -> None:
        """Test button initialization and properties."""
        button = UnifiInsightsPoePowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
            port_label="Port 1",
        )

        assert button.unique_id == "site1_device1_port1_poe_power_cycle"
        assert button.entity_category == EntityCategory.CONFIG
        assert button.entity_registry_enabled_default is False
        assert button.translation_key == "poe_power_cycle"
        assert button.translation_placeholders == {"port_label": "Port 1"}
        assert button.port_idx == 1

    async def test_poe_power_cycle_button_availability(
        self, hass: HomeAssistant, mock_coordinator: MagicMock
    ) -> None:
        """Test button availability tracks port presence and PoE enablement."""
        mock_coordinator.device_available = True
        button = UnifiInsightsPoePowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
            port_label="Port 1",
        )

        # Initially available
        assert button.available is True

        # PoE disabled after setup -> button becomes unavailable
        ports = mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"][
            "ports"
        ]
        ports[0]["poe"]["enabled"] = False
        assert button.available is False

        # Port disappears -> button becomes unavailable
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"]["ports"] = []
        assert button.available is False

        # Port reappears with PoE enabled -> button becomes available again
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"]["ports"] = [
            {"idx": 1, "name": "Port 1", "poe": {"enabled": True}}
        ]
        assert button.available is True

        # Device offline -> button becomes unavailable
        mock_coordinator.data["devices"]["site1"]["device1"]["state"] = "OFFLINE"
        assert button.available is False

    async def test_poe_power_cycle_button_press_uses_facade(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Button press uses facade coroutine when present."""
        button = UnifiInsightsPoePowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
            port_label="Port 1",
        )

        with caplog.at_level(logging.INFO):
            await button.async_press()

        assert "Power cycling PoE port 1 on device device1" in caplog.text

        mock_coordinator.async_power_cycle_port.assert_awaited_once_with(
            "site1", "device1", 1
        )
        mock_coordinator.network_client.devices.execute_port_action.assert_not_called()

    async def test_poe_power_cycle_button_press_fallback(
        self, hass: HomeAssistant, mock_coordinator: MagicMock
    ) -> None:
        """Test button press falls back to execute_port_action."""
        mock_coordinator.async_power_cycle_port = None
        button = UnifiInsightsPoePowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
            port_label="Port 1",
        )

        await button.async_press()

        devices_api = mock_coordinator.network_client.devices
        devices_api.execute_port_action.assert_awaited_once_with(
            "site1", "device1", 1, "POWER_CYCLE"
        )

    async def test_poe_power_cycle_button_press_failure(
        self, hass: HomeAssistant, mock_coordinator: MagicMock
    ) -> None:
        """Button press raises HomeAssistantError on exception."""
        mock_coordinator.async_power_cycle_port = AsyncMock(
            side_effect=Exception("API Error")
        )
        button = UnifiInsightsPoePowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
            port_label="Port 1",
        )

        with pytest.raises(
            HomeAssistantError, match="Unable to power cycle PoE port 1"
        ):
            await button.async_press()


class TestSetupEntryPoeButtons:
    """Tests for setup entry PoE button discovery."""

    async def test_setup_entry_creates_poe_power_cycle_buttons(
        self, hass: HomeAssistant
    ):
        """Test that setup creates PoE power-cycle buttons for PoE ports only."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "interfaces": {
                            "ports": [
                                {
                                    "idx": 1,
                                    "name": "Port 1",
                                    "poe": {"enabled": True},
                                },
                                {
                                    "idx": 2,
                                    "name": "Port 2",
                                    "poe": {"enabled": False},
                                },
                            ]
                        },
                    },
                },
            },
        }

        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.options = {}

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_entry, add_entities)

        poe_buttons = [
            e for e in added_entities if isinstance(e, UnifiInsightsPoePowerCycleButton)
        ]
        assert len(poe_buttons) == 1
        assert poe_buttons[0].unique_id == "site1_device1_port1_poe_power_cycle"
        assert poe_buttons[0].entity_category == EntityCategory.CONFIG
        assert poe_buttons[0].entity_registry_enabled_default is False

    def test_get_port_label(self):
        """Test _get_port_label helper variations."""
        assert _get_port_label({"name": "Custom Name"}, 1) == "Custom Name"
        assert _get_port_label({"name": "Port 1"}, 1) == "Port 1"
        assert _get_port_label({"media": "SFP+"}, 2) == "SFP+ 2"
        assert _get_port_label({}, 3) == "Port 3"

    def test_get_device_port_and_helpers(self):
        """Test get_device_port and related helper edge cases."""
        # Missing site_id or device_id
        assert get_device_port({}, None, "dev1", 1) is None
        assert get_device_port({}, "site1", None, 1) is None

        # Non-dict coordinator data or subkeys
        assert get_device_port(None, "site1", "dev1", 1) is None
        assert get_device_port({"devices": None}, "site1", "dev1", 1) is None
        assert get_device_port({"devices": {"site1": None}}, "site1", "dev1", 1) is None
        assert (
            get_device_port({"devices": {"site1": {"dev1": None}}}, "site1", "dev1", 1)
            is None
        )

        # get_device_ports non-dict interfaces and non-list ports
        assert get_device_ports({}) == []
        assert get_device_ports({"interfaces": "invalid", "ports": "invalid"}) == []

        # Top-level (legacy-merged) ports win; interfaces["ports"] is the fallback
        legacy = [{"idx": 1, "poe": {"enabled": True}}]
        v1 = [{"idx": 2, "poe": {"enabled": True}}]
        both = {"ports": legacy, "interfaces": {"ports": v1}}
        assert get_device_ports(both) == legacy
        assert get_device_ports({"ports": legacy, "interfaces": {}}) == legacy
        assert get_device_ports({"ports": [], "interfaces": {"ports": v1}}) == v1
        assert get_device_ports({"interfaces": {"ports": [None, *v1]}}) == v1

        # Successful port lookup and power-cycle capability checks
        data = {
            "devices": {
                "site1": {
                    "dev1": {
                        "interfaces": {
                            "ports": [
                                {"idx": 1, "poe": {"enabled": True}},
                                {"idx": 2, "poe": {"enabled": False}},
                            ]
                        }
                    }
                }
            }
        }
        port1 = get_device_port(data, "site1", "dev1", 1)
        assert port1 == {"idx": 1, "poe": {"enabled": True}}
        assert port_can_be_power_cycled(port1) is True

        port2 = get_device_port(data, "site1", "dev1", 2)
        assert port2 == {"idx": 2, "poe": {"enabled": False}}
        assert port_can_be_power_cycled(port2) is False

        assert get_device_port(data, "site1", "dev1", 3) is None

    async def test_setup_entry_poe_discovery_edge_cases_and_dedup(
        self, hass: HomeAssistant
    ):
        """Test PoE button discovery edge cases, legacy formats, and deduplication."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "ports": [
                            None,  # non-dict
                            {"name": "No Idx"},  # no idx
                            {"idx": "invalid"},  # non-int idx
                            {
                                "idx": 3,
                                "poe": {"enabled": True},
                                "name": "AP Port",
                            },
                            {
                                "idx": 4,
                                "poe": {"enabled": False},
                            },
                            {
                                "idx": 6,
                                "name": "No PoE Info",
                            },
                        ],
                    },
                },
            },
        }

        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.options = {}

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        listeners = []
        mock_coordinator.async_add_listener = listeners.append

        await async_setup_entry(hass, mock_entry, add_entities)

        poe_buttons = [
            e for e in added_entities if isinstance(e, UnifiInsightsPoePowerCycleButton)
        ]
        assert len(poe_buttons) == 1
        assert poe_buttons[0].unique_id == "site1_device1_port3_poe_power_cycle"
        assert poe_buttons[0].translation_placeholders == {"port_label": "AP Port"}

        # Trigger rediscovery callback to verify deduplication
        prev_count = len(added_entities)
        for listener in listeners:
            listener()
        assert len(added_entities) == prev_count


class TestGenerateVoucherButton:
    """Tests for UnifiGenerateVoucherButton."""

    @pytest.fixture
    def mock_coordinator(self):
        coord = MagicMock()
        coord.data = {
            "sites": {"default": {"desc": "Default"}},
            "vouchers": {"default": []},
        }
        coord.vouchers_available = MagicMock(return_value=True)
        coord.get_voucher_settings = MagicMock(
            return_value=VoucherSettings(
                duration_minutes=1440,
                guest_limit=1,
                download_limit_mbps=0,
                upload_limit_mbps=0,
                data_limit_mb=0,
            )
        )
        coord.async_generate_voucher = AsyncMock(
            return_value=[MagicMock(code="1234567890")]
        )
        return coord

    def test_init_and_properties(self, mock_coordinator):
        button = UnifiGenerateVoucherButton(mock_coordinator, "default")
        assert button.unique_id == "default_generate_voucher"
        assert button.translation_key == "generate_voucher"
        assert button.available is True
        assert button.has_entity_name is True

    def test_available(self, mock_coordinator):
        button = UnifiGenerateVoucherButton(mock_coordinator, "default")
        mock_coordinator.vouchers_available.return_value = False
        assert button.available is False

    async def test_async_press_success(self, mock_coordinator):
        button = UnifiGenerateVoucherButton(mock_coordinator, "default")
        await button.async_press()
        mock_coordinator.get_voucher_settings.assert_called_once_with("default")
        mock_coordinator.async_generate_voucher.assert_awaited_once_with(
            "default",
            name="Home Assistant",
            count=1,
            time_limit_minutes=1440,
            authorized_guest_limit=1,
        )

    async def test_async_press_empty_result_raises_error(self, mock_coordinator):
        button = UnifiGenerateVoucherButton(mock_coordinator, "default")
        mock_coordinator.async_generate_voucher.return_value = []
        with pytest.raises(HomeAssistantError, match="UniFi returned no voucher"):
            await button.async_press()

    async def test_async_press_coordinator_error_raises_error(self, mock_coordinator):
        button = UnifiGenerateVoucherButton(mock_coordinator, "default")
        mock_coordinator.async_generate_voucher.side_effect = RuntimeError(
            "API failure"
        )
        with pytest.raises(
            HomeAssistantError, match="Unable to generate a guest voucher"
        ):
            await button.async_press()

    async def test_discovery_and_deduplication(self, hass, mock_coordinator):
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.options = {}

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        listeners = []
        mock_coordinator.async_add_listener = listeners.append

        await async_setup_entry(hass, mock_entry, add_entities)

        voucher_buttons = [
            e for e in added_entities if isinstance(e, UnifiGenerateVoucherButton)
        ]
        assert len(voucher_buttons) == 1
        assert voucher_buttons[0].unique_id == "default_generate_voucher"

        # Deduplication
        prev_count = len(added_entities)
        for listener in listeners:
            listener()
        assert len(added_entities) == prev_count

    async def test_button_press_through_real_facade_and_real_endpoint_pins_http(
        self, hass: HomeAssistant
    ) -> None:
        """Button press through real facade and real endpoint pins POST URL and body."""
        post_response = {
            "vouchers": [
                {
                    "id": "v-1",
                    "code": "1234567890",
                    "name": "Home Assistant",
                    "timeLimitMinutes": 90,
                }
            ]
        }
        session = _Session(
            [
                _Response(post_response),
                _Response(post_response),
            ]
        )
        client = UniFiNetworkClient(
            auth=ApiKeyAuth(api_key="test-key"),
            base_url="https://192.168.1.1",
            connection_type=ConnectionType.LOCAL,
            session=session,  # type: ignore[arg-type]
        )
        config_coord = MagicMock()
        config_coord.data = {"sites": {"default": {"id": "default"}}, "vouchers": {}}
        config_coord.vouchers_available.return_value = True
        config_coord.async_refresh_vouchers = AsyncMock()

        facade = UnifiFacadeCoordinator(
            hass=hass,
            network_client=client,
            protect_client=None,
            entry=MagicMock(),
            config_coordinator=config_coord,
            device_coordinator=MagicMock(),
            protect_coordinator=None,
        )

        settings = facade.get_voucher_settings("default")
        settings.duration_minutes = 90
        settings.guest_limit = 3
        settings.download_limit_mbps = 1.5
        settings.upload_limit_mbps = 0.5
        settings.data_limit_mb = 2048

        button = UnifiGenerateVoucherButton(facade, "default")
        await button.async_press()

        assert len(session.requests) == 1
        req1 = session.requests[0]
        assert req1["method"] == "POST"
        assert (
            req1["url"]
            == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
        )
        assert req1["json"] == {
            "count": 1,
            "name": "Home Assistant",
            "timeLimitMinutes": 90,
            "authorizedGuestLimit": 3,
            "dataUsageLimitMBytes": 2048,
            "rxRateLimitKbps": 1500,
            "txRateLimitKbps": 500,
        }

        # Second press: zero limits omitted
        settings.guest_limit = 0
        settings.download_limit_mbps = 0.0
        settings.upload_limit_mbps = 0.0
        settings.data_limit_mb = 0
        await button.async_press()

        assert len(session.requests) == 2
        req2 = session.requests[1]
        assert req2["method"] == "POST"
        assert (
            req2["url"]
            == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
        )
        assert req2["json"] == {
            "count": 1,
            "name": "Home Assistant",
            "timeLimitMinutes": 90,
        }
