"""Tests for UniFi Insights services."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.unifi_insights.const import DOMAIN
from custom_components.unifi_insights.services import (
    SERVICE_REFRESH_DATA,
    SERVICE_RESTART_DEVICE,
    _get_coordinators,
    _get_first_coordinator,
    _get_protect_coordinator,
    async_setup_services,
    async_unload_services,
)


class TestGetCoordinators:
    """Tests for _get_coordinators helper."""

    def test_get_coordinators_with_entries(self, hass: HomeAssistant):
        """Test getting coordinators with valid entries."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            coordinators = _get_coordinators(hass)
            assert len(coordinators) == 1
            assert coordinators[0] == mock_coordinator

    def test_get_coordinators_no_entries(self, hass: HomeAssistant):
        """Test getting coordinators with no entries."""
        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[],
        ):
            coordinators = _get_coordinators(hass)
            assert len(coordinators) == 0

    def test_get_coordinators_entry_without_runtime_data(self, hass: HomeAssistant):
        """Test getting coordinators with entry missing runtime_data."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = None

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            coordinators = _get_coordinators(hass)
            assert len(coordinators) == 0


class TestGetFirstCoordinator:
    """Tests for _get_first_coordinator helper."""

    def test_get_first_coordinator_found(self, hass: HomeAssistant):
        """Test getting first coordinator when available."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            coordinator = _get_first_coordinator(hass)
            assert coordinator == mock_coordinator

    def test_get_first_coordinator_not_found(self, hass: HomeAssistant):
        """Test getting first coordinator when none available."""
        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[],
        ):
            coordinator = _get_first_coordinator(hass)
            assert coordinator is None


class TestGetProtectCoordinator:
    """Tests for _get_protect_coordinator helper."""

    def test_get_protect_coordinator_found(self, hass: HomeAssistant):
        """Test getting protect coordinator when available."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()  # Has protect client
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            coordinator = _get_protect_coordinator(hass)
            assert coordinator == mock_coordinator

    def test_get_protect_coordinator_no_protect_client(self, hass: HomeAssistant):
        """Test getting protect coordinator when no protect client."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None  # No protect client
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            coordinator = _get_protect_coordinator(hass)
            assert coordinator is None

    def test_get_protect_coordinator_not_found(self, hass: HomeAssistant):
        """Test getting protect coordinator when none available."""
        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[],
        ):
            coordinator = _get_protect_coordinator(hass)
            assert coordinator is None


class TestAsyncSetupServices:
    """Tests for async_setup_services."""

    async def test_setup_services_registers_services(self, hass: HomeAssistant):
        """Test that setup registers all services."""
        await async_setup_services(hass)

        # Check core services are registered
        assert hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA)
        assert hass.services.has_service(DOMAIN, SERVICE_RESTART_DEVICE)
        assert hass.services.has_service(DOMAIN, "set_recording_mode")
        assert hass.services.has_service(DOMAIN, "set_hdr_mode")
        assert hass.services.has_service(DOMAIN, "set_video_mode")
        assert hass.services.has_service(DOMAIN, "set_mic_volume")
        assert hass.services.has_service(DOMAIN, "set_light_mode")
        assert hass.services.has_service(DOMAIN, "set_light_level")
        assert hass.services.has_service(DOMAIN, "ptz_move")
        assert hass.services.has_service(DOMAIN, "ptz_patrol")

        # Clean up
        await async_unload_services(hass)


class TestAsyncUnloadServices:
    """Tests for async_unload_services."""

    async def test_unload_services_removes_services(self, hass: HomeAssistant):
        """Test that unload removes all services."""
        await async_setup_services(hass)
        assert hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA)

        await async_unload_services(hass)
        assert not hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA)


class TestRefreshDataService:
    """Tests for refresh_data service handler."""

    async def test_refresh_data_no_coordinators(self, hass: HomeAssistant):
        """Test refresh data with no coordinators raises error."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights coordinators"),
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REFRESH_DATA,
                {},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_refresh_data_success(self, hass: HomeAssistant):
        """Test refresh data success."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_refresh = AsyncMock()
        mock_coordinator.data = {"sites": {"site1": {}}}
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REFRESH_DATA,
                {},
                blocking=True,
            )

        mock_coordinator.async_refresh.assert_called_once()

        await async_unload_services(hass)

    async def test_refresh_data_with_site_id(self, hass: HomeAssistant):
        """Test refresh data with specific site_id."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_refresh = AsyncMock()
        mock_coordinator.data = {"sites": {"site1": {}}}
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REFRESH_DATA,
                {"site_id": "site1"},
                blocking=True,
            )

        mock_coordinator.async_refresh.assert_called_once()

        await async_unload_services(hass)

    async def test_refresh_data_site_not_found_skips_coordinator(
        self, hass: HomeAssistant
    ):
        """Test refresh data skips coordinator when site_id not found."""
        mock_coordinator = MagicMock()
        mock_coordinator.async_refresh = AsyncMock()
        mock_coordinator.data = {"sites": {"site1": {}}}  # Only has site1
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            # Request refresh for site2, which doesn't exist
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REFRESH_DATA,
                {"site_id": "site2"},  # Not in coordinator's sites
                blocking=True,
            )

        # Coordinator should NOT be refreshed since site2 wasn't found
        mock_coordinator.async_refresh.assert_not_called()

        await async_unload_services(hass)


class TestRestartDeviceService:
    """Tests for restart_device service handler."""

    async def test_restart_device_no_coordinator(self, hass: HomeAssistant):
        """Test restart device with no coordinator raises error."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights coordinator"),
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RESTART_DEVICE,
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_restart_device_success(self, hass: HomeAssistant):
        """Test restart device success."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.restart_device = AsyncMock(return_value=True)
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RESTART_DEVICE,
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        mock_coordinator.network_client.restart_device.assert_called_once_with(
            "site1", "device1"
        )

        await async_unload_services(hass)

    async def test_restart_device_failure(self, hass: HomeAssistant):
        """Test restart device failure raises error."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.restart_device = AsyncMock(return_value=False)
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Failed to restart device"),
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RESTART_DEVICE,
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        await async_unload_services(hass)


class TestProtectServices:
    """Tests for UniFi Protect service handlers."""

    async def test_set_recording_mode_no_coordinator(self, hass: HomeAssistant):
        """Test set_recording_mode with no coordinator."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect coordinator"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_recording_mode",
                {"camera_id": "cam1", "mode": "always"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_recording_mode_success(self, hass: HomeAssistant):
        """Test set_recording_mode success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_camera = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_recording_mode",
                {"camera_id": "cam1", "mode": "always"},
                blocking=True,
            )

        mock_coordinator.protect_client.update_camera.assert_called_once()

        await async_unload_services(hass)

    async def test_set_hdr_mode_success(self, hass: HomeAssistant):
        """Test set_hdr_mode success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_hdr_mode = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_hdr_mode",
                {"camera_id": "cam1", "mode": "auto"},
                blocking=True,
            )

        mock_coordinator.protect_client.set_hdr_mode.assert_called_once_with(
            camera_id="cam1", mode="auto"
        )

        await async_unload_services(hass)

    async def test_set_video_mode_success(self, hass: HomeAssistant):
        """Test set_video_mode success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_video_mode = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_video_mode",
                {"camera_id": "cam1", "mode": "default"},
                blocking=True,
            )

        mock_coordinator.protect_client.set_video_mode.assert_called_once_with(
            camera_id="cam1", mode="default"
        )

        await async_unload_services(hass)

    async def test_set_mic_volume_success(self, hass: HomeAssistant):
        """Test set_mic_volume success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_microphone_volume = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_mic_volume",
                {"camera_id": "cam1", "volume": 50},
                blocking=True,
            )

        mock_coordinator.protect_client.set_microphone_volume.assert_called_once_with(
            camera_id="cam1", volume=50
        )

        await async_unload_services(hass)


class TestLightServices:
    """Tests for light service handlers."""

    async def test_set_light_mode_success(self, hass: HomeAssistant):
        """Test set_light_mode success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_light_mode = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_mode",
                {"light_id": "light1", "mode": "always"},
                blocking=True,
            )

        mock_coordinator.protect_client.set_light_mode.assert_called_once_with(
            light_id="light1", mode="always"
        )

        await async_unload_services(hass)

    async def test_set_light_level_success(self, hass: HomeAssistant):
        """Test set_light_level success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_light_brightness = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_level",
                {"light_id": "light1", "level": 75},
                blocking=True,
            )

        mock_coordinator.protect_client.set_light_brightness.assert_called_once_with(
            light_id="light1", level=75
        )

        await async_unload_services(hass)


class TestPTZServices:
    """Tests for PTZ service handlers."""

    async def test_ptz_move_success(self, hass: HomeAssistant):
        """Test ptz_move success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_move_to_preset = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_move",
                {"camera_id": "cam1", "preset": 2},
                blocking=True,
            )

        mock_coordinator.protect_client.ptz_move_to_preset.assert_called_once_with(
            camera_id="cam1", preset=2
        )

        await async_unload_services(hass)

    async def test_ptz_patrol_start_success(self, hass: HomeAssistant):
        """Test ptz_patrol start success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_start_patrol = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_patrol",
                {"camera_id": "cam1", "action": "start", "slot": 1},
                blocking=True,
            )

        mock_coordinator.protect_client.ptz_start_patrol.assert_called_once_with(
            camera_id="cam1", slot=1
        )

        await async_unload_services(hass)

    async def test_ptz_patrol_stop_success(self, hass: HomeAssistant):
        """Test ptz_patrol stop success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_stop_patrol = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_patrol",
                {"camera_id": "cam1", "action": "stop"},
                blocking=True,
            )

        mock_coordinator.protect_client.ptz_stop_patrol.assert_called_once_with(
            camera_id="cam1"
        )

        await async_unload_services(hass)


class TestChimeServices:
    """Tests for chime service handlers."""

    async def test_set_chime_volume_success(self, hass: HomeAssistant):
        """Test set_chime_volume success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_volume = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_volume",
                {"chime_id": "chime1", "volume": 80},
                blocking=True,
            )

        mock_coordinator.protect_client.set_chime_volume.assert_called_once()

        await async_unload_services(hass)

    async def test_play_chime_ringtone_success(self, hass: HomeAssistant):
        """Test play_chime_ringtone success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.play_chime = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "play_chime_ringtone",
                {"chime_id": "chime1"},
                blocking=True,
            )

        mock_coordinator.protect_client.play_chime.assert_called_once()

        await async_unload_services(hass)


class TestNetworkServices:
    """Tests for network service handlers."""

    async def test_authorize_guest_success(self, hass: HomeAssistant):
        """Test authorize_guest success."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.authorize_guest = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "authorize_guest",
                {"site_id": "site1", "client_id": "client1"},
                blocking=True,
            )

        mock_coordinator.network_client.authorize_guest.assert_called_once()

        await async_unload_services(hass)

    async def test_generate_voucher_success(self, hass: HomeAssistant):
        """Test generate_voucher success."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.generate_voucher = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "generate_voucher",
                {"site_id": "site1"},
                blocking=True,
            )

        mock_coordinator.network_client.generate_voucher.assert_called_once()

        await async_unload_services(hass)

    async def test_delete_voucher_success(self, hass: HomeAssistant):
        """Test delete_voucher success."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.delete_voucher = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "delete_voucher",
                {"site_id": "site1", "voucher_id": "voucher1"},
                blocking=True,
            )

        mock_coordinator.network_client.delete_voucher.assert_called_once()

        await async_unload_services(hass)


class TestServiceErrorHandling:
    """Tests for service error handling."""

    async def test_refresh_data_no_coordinator(self, hass: HomeAssistant):
        """Test refresh_data when no coordinators are found."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "refresh_data",
                {},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_refresh_data_error(self, hass: HomeAssistant):
        """Test refresh_data with coordinator error."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {"sites": {"default": {}}}
        mock_coordinator.async_refresh = AsyncMock(
            side_effect=Exception("Refresh failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error refreshing"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "refresh_data",
                {},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_restart_device_no_coordinator(self, hass: HomeAssistant):
        """Test restart_device when no coordinator is found."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "restart_device",
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_restart_device_failed(self, hass: HomeAssistant):
        """Test restart_device when restart fails."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.restart_device = AsyncMock(return_value=False)
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Failed to restart"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "restart_device",
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_restart_device_error(self, hass: HomeAssistant):
        """Test restart_device with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.restart_device = AsyncMock(
            side_effect=Exception("Restart failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error restarting"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "restart_device",
                {"site_id": "site1", "device_id": "device1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_recording_mode_no_protect(self, hass: HomeAssistant):
        """Test set_recording_mode when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_recording_mode",
                {"camera_id": "cam1", "mode": "always"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_recording_mode_error(self, hass: HomeAssistant):
        """Test set_recording_mode with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_camera = AsyncMock(
            side_effect=Exception("Update failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting recording"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_recording_mode",
                {"camera_id": "cam1", "mode": "always"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_hdr_mode_no_protect(self, hass: HomeAssistant):
        """Test set_hdr_mode when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_hdr_mode",
                {"camera_id": "cam1", "mode": "on"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_hdr_mode_error(self, hass: HomeAssistant):
        """Test set_hdr_mode with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_hdr_mode = AsyncMock(
            side_effect=Exception("HDR failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting HDR"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_hdr_mode",
                {"camera_id": "cam1", "mode": "on"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_video_mode_no_protect(self, hass: HomeAssistant):
        """Test set_video_mode when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_video_mode",
                {"camera_id": "cam1", "mode": "default"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_video_mode_error(self, hass: HomeAssistant):
        """Test set_video_mode with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_video_mode = AsyncMock(
            side_effect=Exception("Video failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting video"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_video_mode",
                {"camera_id": "cam1", "mode": "default"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_mic_volume_no_protect(self, hass: HomeAssistant):
        """Test set_mic_volume when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_mic_volume",
                {"camera_id": "cam1", "volume": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_mic_volume_error(self, hass: HomeAssistant):
        """Test set_mic_volume with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_microphone_volume = AsyncMock(
            side_effect=Exception("Mic failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting mic"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_mic_volume",
                {"camera_id": "cam1", "volume": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_light_mode_no_protect(self, hass: HomeAssistant):
        """Test set_light_mode when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_mode",
                {"light_id": "light1", "mode": "always"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_light_mode_error(self, hass: HomeAssistant):
        """Test set_light_mode with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_light_mode = AsyncMock(
            side_effect=Exception("Light mode failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting light mode"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_mode",
                {"light_id": "light1", "mode": "always"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_light_level_no_protect(self, hass: HomeAssistant):
        """Test set_light_level when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_level",
                {"light_id": "light1", "level": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_light_level_error(self, hass: HomeAssistant):
        """Test set_light_level with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_light_brightness = AsyncMock(
            side_effect=Exception("Light level failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting light level"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_light_level",
                {"light_id": "light1", "level": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_ptz_move_no_protect(self, hass: HomeAssistant):
        """Test ptz_move when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_move",
                {"camera_id": "cam1", "preset": 1},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_ptz_move_error(self, hass: HomeAssistant):
        """Test ptz_move with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_move_to_preset = AsyncMock(
            side_effect=Exception("PTZ failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error moving PTZ"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_move",
                {"camera_id": "cam1", "preset": 1},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_ptz_patrol_start_no_protect(self, hass: HomeAssistant):
        """Test ptz_patrol start when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_patrol",
                {"camera_id": "cam1", "action": "start"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_ptz_patrol_stop_success(self, hass: HomeAssistant):
        """Test ptz_patrol stop success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_stop_patrol = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_patrol",
                {"camera_id": "cam1", "action": "stop"},
                blocking=True,
            )

        mock_coordinator.protect_client.ptz_stop_patrol.assert_called_once()

        await async_unload_services(hass)

    async def test_ptz_patrol_error(self, hass: HomeAssistant):
        """Test ptz_patrol with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_start_patrol = AsyncMock(
            side_effect=Exception("Patrol failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error controlling PTZ"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "ptz_patrol",
                {"camera_id": "cam1", "action": "start"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_volume_no_protect(self, hass: HomeAssistant):
        """Test set_chime_volume when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_volume",
                {"chime_id": "chime1", "volume": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_volume_error(self, hass: HomeAssistant):
        """Test set_chime_volume with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_volume = AsyncMock(
            side_effect=Exception("Chime volume failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting chime volume"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_volume",
                {"chime_id": "chime1", "volume": 50},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_play_chime_ringtone_no_protect(self, hass: HomeAssistant):
        """Test play_chime_ringtone when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "play_chime_ringtone",
                {"chime_id": "chime1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_play_chime_ringtone_error(self, hass: HomeAssistant):
        """Test play_chime_ringtone with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.play_chime = AsyncMock(
            side_effect=Exception("Play chime failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error playing chime"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "play_chime_ringtone",
                {"chime_id": "chime1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_ringtone_no_protect(self, hass: HomeAssistant):
        """Test set_chime_ringtone when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_ringtone",
                {"chime_id": "chime1", "ringtone_id": "default"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_ringtone_error(self, hass: HomeAssistant):
        """Test set_chime_ringtone with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_ringtone = AsyncMock(
            side_effect=Exception("Set ringtone failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting chime ringtone"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_ringtone",
                {"chime_id": "chime1", "ringtone_id": "default"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_repeat_times_no_protect(self, hass: HomeAssistant):
        """Test set_chime_repeat_times when no Protect coordinator is found."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Protect"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_repeat_times",
                {"chime_id": "chime1", "repeat_times": 3},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_repeat_times_error(self, hass: HomeAssistant):
        """Test set_chime_repeat_times with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_repeat = AsyncMock(
            side_effect=Exception("Set repeat failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error setting chime repeat times"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_repeat_times",
                {"chime_id": "chime1", "repeat_times": 3},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_chime_ringtone_success(self, hass: HomeAssistant):
        """Test set_chime_ringtone success (covers line 784)."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_ringtone = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_ringtone",
                {"chime_id": "chime1", "ringtone_id": "default"},
                blocking=True,
            )

        mock_coordinator.protect_client.set_chime_ringtone.assert_called_once()

        await async_unload_services(hass)

    async def test_set_chime_repeat_times_success(self, hass: HomeAssistant):
        """Test set_chime_repeat_times success (covers line 816)."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_repeat = AsyncMock()
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with patch.object(
            hass.config_entries,
            "async_entries",
            return_value=[mock_entry],
        ):
            await hass.services.async_call(
                DOMAIN,
                "set_chime_repeat_times",
                {"chime_id": "chime1", "repeat_times": 3},
                blocking=True,
            )

        mock_coordinator.protect_client.set_chime_repeat.assert_called_once()

        await async_unload_services(hass)

    async def test_authorize_guest_no_coordinator(self, hass: HomeAssistant):
        """Test authorize_guest when no coordinator is found."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "authorize_guest",
                {"site_id": "site1", "client_id": "client1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_authorize_guest_error(self, hass: HomeAssistant):
        """Test authorize_guest with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.authorize_guest = AsyncMock(
            side_effect=Exception("Auth failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error authorizing guest"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "authorize_guest",
                {"site_id": "site1", "client_id": "client1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_generate_voucher_no_coordinator(self, hass: HomeAssistant):
        """Test generate_voucher when no coordinator is found."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "generate_voucher",
                {"site_id": "site1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_generate_voucher_error(self, hass: HomeAssistant):
        """Test generate_voucher with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.generate_voucher = AsyncMock(
            side_effect=Exception("Generate failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error generating voucher"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "generate_voucher",
                {"site_id": "site1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_delete_voucher_no_coordinator(self, hass: HomeAssistant):
        """Test delete_voucher when no coordinator is found."""
        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[],
            ),
            pytest.raises(HomeAssistantError, match="No UniFi Insights"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "delete_voucher",
                {"site_id": "site1", "voucher_id": "voucher1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_delete_voucher_error(self, hass: HomeAssistant):
        """Test delete_voucher with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.network_client = MagicMock()
        mock_coordinator.network_client.delete_voucher = AsyncMock(
            side_effect=Exception("Delete failed")
        )
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        await async_setup_services(hass)

        with (
            patch.object(
                hass.config_entries,
                "async_entries",
                return_value=[mock_entry],
            ),
            pytest.raises(HomeAssistantError, match="Error deleting voucher"),
        ):
            await hass.services.async_call(
                DOMAIN,
                "delete_voucher",
                {"site_id": "site1", "voucher_id": "voucher1"},
                blocking=True,
            )

        await async_unload_services(hass)


class TestTriggerAlarmService:
    """Tests for trigger_alarm service."""

    async def test_trigger_alarm_success(self, hass: HomeAssistant):
        """Test trigger_alarm service success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.trigger_alarm = AsyncMock()

        await async_setup_services(hass)

        # Set up hass.data[DOMAIN] as the service uses it directly
        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        await hass.services.async_call(
            DOMAIN,
            "trigger_alarm",
            {"alarm_id": "alarm1"},
            blocking=True,
        )

        mock_coordinator.protect_client.trigger_alarm.assert_called_once_with(
            alarm_id="alarm1"
        )

        await async_unload_services(hass)

    async def test_trigger_alarm_no_coordinator(self, hass: HomeAssistant):
        """Test trigger_alarm when no coordinator is found."""
        await async_setup_services(hass)

        hass.data[DOMAIN] = {}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "trigger_alarm",
                {"alarm_id": "alarm1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_trigger_alarm_no_protect_client(self, hass: HomeAssistant):
        """Test trigger_alarm when coordinator has no protect_client."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "trigger_alarm",
                {"alarm_id": "alarm1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_trigger_alarm_error(self, hass: HomeAssistant):
        """Test trigger_alarm with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.trigger_alarm = AsyncMock(
            side_effect=Exception("Alarm failed")
        )

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="Error triggering alarm"):
            await hass.services.async_call(
                DOMAIN,
                "trigger_alarm",
                {"alarm_id": "alarm1"},
                blocking=True,
            )

        await async_unload_services(hass)


class TestCreateLiveviewService:
    """Tests for create_liveview service."""

    async def test_create_liveview_success(self, hass: HomeAssistant):
        """Test create_liveview service success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.create_liveview = AsyncMock()

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        await hass.services.async_call(
            DOMAIN,
            "create_liveview",
            {"name": "Test Liveview", "layout": 2, "is_default": True},
            blocking=True,
        )

        mock_coordinator.protect_client.create_liveview.assert_called_once_with(
            data={"name": "Test Liveview", "layout": 2, "isDefault": True}
        )

        await async_unload_services(hass)

    async def test_create_liveview_no_coordinator(self, hass: HomeAssistant):
        """Test create_liveview when no coordinator is found."""
        await async_setup_services(hass)

        hass.data[DOMAIN] = {}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "create_liveview",
                {"name": "Test Liveview", "layout": 2},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_create_liveview_no_protect_client(self, hass: HomeAssistant):
        """Test create_liveview when coordinator has no protect_client."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "create_liveview",
                {"name": "Test Liveview", "layout": 2},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_create_liveview_error(self, hass: HomeAssistant):
        """Test create_liveview with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.create_liveview = AsyncMock(
            side_effect=Exception("Liveview failed")
        )

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="Error creating liveview"):
            await hass.services.async_call(
                DOMAIN,
                "create_liveview",
                {"name": "Test Liveview", "layout": 2},
                blocking=True,
            )

        await async_unload_services(hass)


class TestSetLiveviewService:
    """Tests for set_liveview service."""

    async def test_set_liveview_success(self, hass: HomeAssistant):
        """Test set_liveview service success."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_viewer = AsyncMock()

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        await hass.services.async_call(
            DOMAIN,
            "set_liveview",
            {"viewer_id": "viewer1", "liveview_id": "liveview1"},
            blocking=True,
        )

        mock_coordinator.protect_client.update_viewer.assert_called_once_with(
            viewer_id="viewer1", data={"liveview": "liveview1"}
        )

        await async_unload_services(hass)

    async def test_set_liveview_no_coordinator(self, hass: HomeAssistant):
        """Test set_liveview when no coordinator is found."""
        await async_setup_services(hass)

        hass.data[DOMAIN] = {}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "set_liveview",
                {"viewer_id": "viewer1", "liveview_id": "liveview1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_liveview_no_protect_client(self, hass: HomeAssistant):
        """Test set_liveview when coordinator has no protect_client."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="No UniFi Protect"):
            await hass.services.async_call(
                DOMAIN,
                "set_liveview",
                {"viewer_id": "viewer1", "liveview_id": "liveview1"},
                blocking=True,
            )

        await async_unload_services(hass)

    async def test_set_liveview_error(self, hass: HomeAssistant):
        """Test set_liveview with exception."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_viewer = AsyncMock(
            side_effect=Exception("Set liveview failed")
        )

        await async_setup_services(hass)

        hass.data[DOMAIN] = {"test_entry": mock_coordinator}

        with pytest.raises(HomeAssistantError, match="Error setting liveview"):
            await hass.services.async_call(
                DOMAIN,
                "set_liveview",
                {"viewer_id": "viewer1", "liveview_id": "liveview1"},
                blocking=True,
            )

        await async_unload_services(hass)
