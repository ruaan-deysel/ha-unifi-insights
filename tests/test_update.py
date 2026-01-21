"""Tests for UniFi Insights update platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.unifi_insights.update import (
    PARALLEL_UPDATES,
    UnifiNetworkDeviceUpdate,
    UnifiProtectDeviceUpdate,
    async_setup_entry,
)


class TestParallelUpdates:
    """Test PARALLEL_UPDATES constant."""

    def test_parallel_updates_value(self) -> None:
        """Test that PARALLEL_UPDATES is set correctly."""
        assert PARALLEL_UPDATES == 0


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {"site1": {}},
            "clients": {"site1": {}},
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

    @pytest.mark.asyncio
    async def test_setup_entry_no_devices(self, hass, mock_coordinator) -> None:
        """Test setup when no devices present."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_setup_entry_with_network_devices(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with network devices present."""
        mock_coordinator.data["devices"]["site1"] = {
            "device1": {
                "id": "device1",
                "name": "Test Switch",
                "model": "USW-24-POE",
                "state": "ONLINE",
                "firmwareVersion": "6.5.55",
                "upgradeAvailable": True,
                "upgradableFirmwareVersion": "6.6.65",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiNetworkDeviceUpdate)

    @pytest.mark.asyncio
    async def test_setup_entry_with_protect_devices(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with Protect devices present."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {
                "id": "camera1",
                "name": "Test Camera",
                "state": "CONNECTED",
                "firmwareVersion": "1.0.0",
                "isFirmwareUpdateAvailable": True,
                "firmwareBuild": "1.1.0",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectDeviceUpdate)

    @pytest.mark.asyncio
    async def test_setup_entry_no_protect_client(self, hass, mock_coordinator) -> None:
        """Test setup without Protect API."""
        mock_coordinator.protect_client = None
        mock_coordinator.data["devices"]["site1"] = {
            "device1": {
                "id": "device1",
                "name": "Test Switch",
                "model": "USW-24-POE",
                "state": "ONLINE",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Should only have network device, no Protect devices
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiNetworkDeviceUpdate)


class TestUnifiNetworkDeviceUpdate:
    """Tests for UnifiNetworkDeviceUpdate entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "firmwareVersion": "6.5.55",
                        "firmwareUpdatable": True,
                    }
                }
            },
            "clients": {"site1": {}},
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

    def test_initialization(self, mock_coordinator) -> None:
        """Test entity initialization."""
        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert entity._site_id == "site1"
        assert entity._device_id == "device1"

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert "device1" in entity._attr_unique_id
        assert "update" in entity._attr_unique_id

    def test_installed_version(self, mock_coordinator) -> None:
        """Test installed version property."""
        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert entity.installed_version == "6.5.55"

    def test_latest_version_available(self, mock_coordinator) -> None:
        """Test latest version when update available."""
        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        # When firmwareUpdatable=True, returns placeholder
        assert entity.latest_version == "Update Available"

    def test_latest_version_no_update(self, mock_coordinator) -> None:
        """Test latest version when no update available."""
        device = mock_coordinator.data["devices"]["site1"]["device1"]
        device["firmwareUpdatable"] = False

        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert entity.latest_version == entity.installed_version

    def test_available_when_coordinator_success(self, mock_coordinator) -> None:
        """Test availability when coordinator update succeeds."""
        mock_coordinator.last_update_success = True

        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert entity.available is True

    def test_unavailable_when_coordinator_fails(self, mock_coordinator) -> None:
        """Test availability when coordinator update fails."""
        mock_coordinator.last_update_success = False

        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        assert entity.available is False

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        entity = UnifiNetworkDeviceUpdate(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="device1",
        )

        device_info = entity.device_info
        assert device_info is not None


class TestUnifiProtectDeviceUpdate:
    """Tests for UnifiProtectDeviceUpdate entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {"site1": {}},
            "clients": {"site1": {}},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "type": "UVC-G4-PRO",
                        "state": "CONNECTED",
                        "firmwareVersion": "1.0.0",
                        "isFirmwareUpdateAvailable": True,
                        "firmwareBuild": "1.1.0",
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test entity initialization."""
        # Use singular device_type - the entity adds 's' to access data
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity._device_type == "camera"
        assert entity._device_id == "camera1"

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity._attr_unique_id is not None
        assert "camera1" in entity._attr_unique_id

    def test_installed_version(self, mock_coordinator) -> None:
        """Test installed version property."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity.installed_version == "1.0.0"

    def test_latest_version_available(self, mock_coordinator) -> None:
        """Test latest version when update available."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity.latest_version == "1.1.0"

    def test_latest_version_no_update(self, mock_coordinator) -> None:
        """Test latest version when no update available."""
        cameras = mock_coordinator.data["protect"]["cameras"]
        cameras["camera1"]["isFirmwareUpdateAvailable"] = False
        cameras["camera1"]["firmwareBuild"] = None

        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity.latest_version == entity.installed_version

    def test_available_when_connected(self, mock_coordinator) -> None:
        """Test availability when device is connected."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(self, mock_coordinator) -> None:
        """Test availability when device is disconnected."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["state"] = "DISCONNECTED"

        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        assert entity.available is False

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="camera",
            device_id="camera1",
        )

        device_info = entity.device_info
        assert device_info is not None
        assert device_info.get("manufacturer") == "Ubiquiti Inc."


class TestProtectDeviceTypes:
    """Tests for different Protect device types."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with multiple device types."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "protect": {
                "cameras": {},
                "lights": {
                    "light1": {
                        "id": "light1",
                        "name": "Test Light",
                        "state": "CONNECTED",
                        "firmwareVersion": "2.0.0",
                    }
                },
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Test Sensor",
                        "state": "CONNECTED",
                        "firmwareVersion": "3.0.0",
                    }
                },
                "nvrs": {
                    "nvr1": {
                        "id": "nvr1",
                        "name": "Test NVR",
                        "state": "CONNECTED",
                        "firmwareVersion": "4.0.0",
                    }
                },
                "viewers": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "firmwareVersion": "5.0.0",
                    }
                },
            },
        }
        return coordinator

    def test_light_update_entity(self, mock_coordinator) -> None:
        """Test update entity for lights."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="light",
            device_id="light1",
        )

        assert entity._device_type == "light"
        assert entity.installed_version == "2.0.0"

    def test_sensor_update_entity(self, mock_coordinator) -> None:
        """Test update entity for sensors."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="sensor",
            device_id="sensor1",
        )

        assert entity._device_type == "sensor"
        assert entity.installed_version == "3.0.0"

    def test_nvr_update_entity(self, mock_coordinator) -> None:
        """Test update entity for NVRs."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="nvr",
            device_id="nvr1",
        )

        assert entity._device_type == "nvr"
        assert entity.installed_version == "4.0.0"

    def test_chime_update_entity(self, mock_coordinator) -> None:
        """Test update entity for chimes."""
        entity = UnifiProtectDeviceUpdate(
            coordinator=mock_coordinator,
            device_type="chime",
            device_id="chime1",
        )

        assert entity._device_type == "chime"
        assert entity.installed_version == "5.0.0"
