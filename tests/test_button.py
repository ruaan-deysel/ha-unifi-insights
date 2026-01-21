"""Tests for UniFi Insights buttons."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.button import (
    BUTTON_TYPES,
    UnifiInsightsButton,
    UnifiPortPowerCycleButton,
    UnifiProtectChimePlayButton,
    UnifiProtectPTZPatrolStartButton,
    UnifiProtectPTZPatrolStopButton,
    async_setup_entry,
)


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
        coordinator.network_client.restart_device = AsyncMock(return_value=True)
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

        mock_coordinator.network_client.restart_device.assert_called_once_with(
            "site1", "device1"
        )

    async def test_button_press_failure(self, hass: HomeAssistant, mock_coordinator):
        """Test button press failure."""
        mock_coordinator.network_client.restart_device = AsyncMock(return_value=False)
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        await button.async_press()

        mock_coordinator.network_client.restart_device.assert_called_once()

    async def test_button_press_exception(self, hass: HomeAssistant, mock_coordinator):
        """Test button press handles exception."""
        mock_coordinator.network_client.restart_device = AsyncMock(
            side_effect=Exception("API Error")
        )
        description = BUTTON_TYPES[0]

        button = UnifiInsightsButton(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # Should not raise
        await button.async_press()


class TestUnifiPortPowerCycleButton:
    """Tests for UnifiPortPowerCycleButton."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.network_client.power_cycle_port = AsyncMock()
        coordinator.protect_client = None
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "PoE Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "port_table": [
                            {"port_idx": 1, "poe_enable": True},
                            {"port_idx": 2, "poe_enable": False},
                        ],
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

    async def test_port_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test port power cycle button initialization."""
        button = UnifiPortPowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert button._port_idx == 1
        assert "Port 1 Power Cycle" in button._attr_name

    async def test_port_button_available_poe_enabled(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button available when PoE enabled."""
        button = UnifiPortPowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert button.available is True

    async def test_port_button_unavailable_poe_disabled(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test button unavailable when PoE disabled."""
        button = UnifiPortPowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=2,
        )

        assert button.available is False

    async def test_port_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test port power cycle button press."""
        button = UnifiPortPowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        await button.async_press()

        mock_coordinator.network_client.power_cycle_port.assert_called_once_with(
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

    async def test_port_button_press_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port button handles exception."""
        mock_coordinator.network_client.power_cycle_port = AsyncMock(
            side_effect=Exception("API Error")
        )

        button = UnifiPortPowerCycleButton(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Should not raise
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
        coordinator.protect_client.play_chime = AsyncMock()
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
        assert button._attr_name == "Play"

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

    async def test_chime_button_press(self, hass: HomeAssistant, mock_coordinator):
        """Test chime play button press."""
        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        await button.async_press()

        mock_coordinator.protect_client.play_chime.assert_called_once_with(
            chime_id="chime1",
            ringtone_id="mechanical",
        )

    async def test_chime_button_press_exception(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test chime button handles exception."""
        mock_coordinator.protect_client.play_chime = AsyncMock(
            side_effect=Exception("API Error")
        )

        button = UnifiProtectChimePlayButton(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        # Should not raise
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
                        "featureFlags": {"hasPtz": True},
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
        assert button._attr_name == "Start PTZ Patrol"

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

        # Should not raise
        await button.async_press()

    async def test_ptz_stop_button_init(self, hass: HomeAssistant, mock_coordinator):
        """Test PTZ patrol stop button initialization."""
        button = UnifiProtectPTZPatrolStopButton(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert button._device_id == "camera1"
        assert button._attr_name == "Stop PTZ Patrol"

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
                        "port_table": [
                            {"port_idx": 1, "poe_enable": True},
                        ],
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
                        "featureFlags": {"hasPtz": True},
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

    async def test_setup_entry_creates_port_buttons(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates port power cycle buttons."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        port_buttons = [
            e for e in added_entities if isinstance(e, UnifiPortPowerCycleButton)
        ]
        assert len(port_buttons) > 0

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
