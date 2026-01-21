"""Tests for UniFi Protect select entities."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.unifi_insights.const import (
    CHIME_RINGTONE_DEFAULT,
    CHIME_RINGTONE_MECHANICAL,
    DEVICE_TYPE_CAMERA,
    DEVICE_TYPE_CHIME,
    DEVICE_TYPE_VIEWER,
    HDR_MODE_AUTO,
    HDR_MODE_ON,
    VIDEO_MODE_DEFAULT,
    VIDEO_MODE_HIGH_FPS,
)
from custom_components.unifi_insights.select import (
    PARALLEL_UPDATES,
    UnifiProtectChimeRingtoneSelect,
    UnifiProtectHDRModeSelect,
    UnifiProtectPTZPresetSelect,
    UnifiProtectVideoModeSelect,
    UnifiProtectViewerLiveviewSelect,
    async_setup_entry,
)


class TestParallelUpdates:
    """Tests for PARALLEL_UPDATES constant."""

    def test_parallel_updates_value(self):
        """Test that PARALLEL_UPDATES is set to 1 for action-based entities."""
        assert PARALLEL_UPDATES == 1


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_entry_no_protect_client(self, mock_config_entry):
        """Test setup skips when no Protect client available."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = None
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def add_entities(new_entities, **kwargs):
            entities.extend(new_entities)

        await async_setup_entry(MagicMock(), mock_config_entry, add_entities)
        assert len(entities) == 0

    async def test_setup_entry_with_cameras(self, mock_config_entry):
        """Test setup creates select entities for cameras."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Front Camera",
                        "state": "CONNECTED",
                        "hasPtz": False,
                    },
                },
                "chimes": {},
                "viewers": {},
                "liveviews": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def add_entities(new_entities, **kwargs):
            entities.extend(new_entities)

        await async_setup_entry(MagicMock(), mock_config_entry, add_entities)
        # Should create 2 entities per camera (HDR mode + video mode)
        assert len(entities) == 2

    async def test_setup_entry_with_ptz_camera(self, mock_config_entry):
        """Test setup creates PTZ preset select for PTZ cameras."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "hasPtz": True,
                    },
                },
                "chimes": {},
                "viewers": {},
                "liveviews": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def add_entities(new_entities, **kwargs):
            entities.extend(new_entities)

        await async_setup_entry(MagicMock(), mock_config_entry, add_entities)
        # Should create 3 entities (HDR + video + PTZ preset)
        assert len(entities) == 3

    async def test_setup_entry_with_chimes(self, mock_config_entry):
        """Test setup creates ringtone select for chimes."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Door Chime",
                        "state": "CONNECTED",
                    },
                },
                "viewers": {},
                "liveviews": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def add_entities(new_entities, **kwargs):
            entities.extend(new_entities)

        await async_setup_entry(MagicMock(), mock_config_entry, add_entities)
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectChimeRingtoneSelect)

    async def test_setup_entry_with_viewers(self, mock_config_entry):
        """Test setup creates liveview select for viewers."""
        mock_coordinator = MagicMock()
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {},
                "viewers": {
                    "viewer1": {
                        "id": "viewer1",
                        "name": "Living Room Viewer",
                        "state": "CONNECTED",
                    },
                },
                "liveviews": {
                    "lv1": {"id": "lv1", "name": "Default View"},
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_config_entry.runtime_data = MagicMock()
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def add_entities(new_entities, **kwargs):
            entities.extend(new_entities)

        await async_setup_entry(MagicMock(), mock_config_entry, add_entities)
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectViewerLiveviewSelect)


class TestUnifiProtectHDRModeSelect:
    """Tests for UnifiProtectHDRModeSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test HDR mode select initialization."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "hdrType": "auto",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectHDRModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )

        assert entity._device_type == DEVICE_TYPE_CAMERA
        assert entity._device_id == "cam1"
        assert entity._attr_name == "HDR Mode"
        assert entity._attr_current_option == "auto"
        assert HDR_MODE_AUTO in entity._attr_options
        assert HDR_MODE_ON in entity._attr_options

    def test_update_from_data(self, mock_coordinator):
        """Test update from data."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "hdrType": "on",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectHDRModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )

        assert entity._attr_current_option == "on"

    async def test_async_select_option_success(self, mock_coordinator):
        """Test selecting HDR mode option successfully."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "hdrType": "auto",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_hdr_mode = AsyncMock()

        entity = UnifiProtectHDRModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("on")

        mock_coordinator.protect_client.set_hdr_mode.assert_called_once_with(
            camera_id="cam1", mode="on"
        )
        assert entity._attr_current_option == "on"

    async def test_async_select_option_error(self, mock_coordinator):
        """Test selecting HDR mode option with error."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "hdrType": "auto",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_hdr_mode = AsyncMock(
            side_effect=Exception("API Error")
        )

        entity = UnifiProtectHDRModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("on")
        # Should not raise, just log the error


class TestUnifiProtectVideoModeSelect:
    """Tests for UnifiProtectVideoModeSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test video mode select initialization."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "videoMode": "default",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectVideoModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )

        assert entity._device_type == DEVICE_TYPE_CAMERA
        assert entity._device_id == "cam1"
        assert entity._attr_name == "Video Mode"
        assert entity._attr_current_option == "default"
        assert VIDEO_MODE_DEFAULT in entity._attr_options
        assert VIDEO_MODE_HIGH_FPS in entity._attr_options

    async def test_async_select_option_success(self, mock_coordinator):
        """Test selecting video mode option successfully."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "videoMode": "default",
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_video_mode = AsyncMock()

        entity = UnifiProtectVideoModeSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("highFps")

        mock_coordinator.protect_client.set_video_mode.assert_called_once_with(
            camera_id="cam1", mode="highFps"
        )
        assert entity._attr_current_option == "highFps"


class TestUnifiProtectChimeRingtoneSelect:
    """Tests for UnifiProtectChimeRingtoneSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test chime ringtone select initialization."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "ringSettings": [{"ringtoneId": "default"}],
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectChimeRingtoneSelect(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert entity._device_type == DEVICE_TYPE_CHIME
        assert entity._device_id == "chime1"
        assert entity._attr_name == "Ringtone"
        assert entity._attr_current_option == "default"
        assert CHIME_RINGTONE_DEFAULT in entity._attr_options
        assert CHIME_RINGTONE_MECHANICAL in entity._attr_options

    def test_initialization_no_ring_settings(self, mock_coordinator):
        """Test chime ringtone select with no ring settings."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "ringSettings": [],
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectChimeRingtoneSelect(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert entity._attr_current_option == CHIME_RINGTONE_DEFAULT

    async def test_async_select_option_success(self, mock_coordinator):
        """Test selecting ringtone option successfully."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "ringSettings": [],
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "liveviews": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.set_chime_ringtone = AsyncMock()

        entity = UnifiProtectChimeRingtoneSelect(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("mechanical")

        mock_coordinator.protect_client.set_chime_ringtone.assert_called_once_with(
            chime_id="chime1", ringtone_id="mechanical"
        )


class TestUnifiProtectPTZPresetSelect:
    """Tests for UnifiProtectPTZPresetSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test PTZ preset select initialization."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "hasPtz": True,
                        "currentPtzPreset": 2,
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }

        entity = UnifiProtectPTZPresetSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )

        assert entity._device_type == DEVICE_TYPE_CAMERA
        assert entity._device_id == "cam1"
        assert entity._attr_name == "PTZ Preset"
        assert entity._attr_current_option == "2"
        assert "0" in entity._attr_options

    async def test_async_select_option_success(self, mock_coordinator):
        """Test selecting PTZ preset option successfully."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "cam1": {
                        "id": "cam1",
                        "name": "PTZ Camera",
                        "state": "CONNECTED",
                        "hasPtz": True,
                        "currentPtzPreset": 0,
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "chimes": {},
                "viewers": {},
                "liveviews": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.ptz_move_to_preset = AsyncMock()

        entity = UnifiProtectPTZPresetSelect(
            coordinator=mock_coordinator,
            camera_id="cam1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("3")

        mock_coordinator.protect_client.ptz_move_to_preset.assert_called_once_with(
            camera_id="cam1", slot=3
        )
        assert entity._attr_current_option == "3"


class TestUnifiProtectViewerLiveviewSelect:
    """Tests for UnifiProtectViewerLiveviewSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test viewer liveview select initialization."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {},
                "viewers": {
                    "viewer1": {
                        "id": "viewer1",
                        "name": "Test Viewer",
                        "state": "CONNECTED",
                        "liveview": "lv1",
                    },
                },
                "liveviews": {
                    "lv1": {"id": "lv1", "name": "Default View"},
                    "lv2": {"id": "lv2", "name": "All Cameras"},
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }

        entity = UnifiProtectViewerLiveviewSelect(
            coordinator=mock_coordinator,
            viewer_id="viewer1",
        )

        assert entity._device_type == DEVICE_TYPE_VIEWER
        assert entity._device_id == "viewer1"
        assert entity._attr_name == "Liveview"
        assert entity._attr_current_option == "Default View"
        assert "Default View" in entity._attr_options
        assert "All Cameras" in entity._attr_options

    def test_initialization_no_liveview_set(self, mock_coordinator):
        """Test viewer liveview select with no liveview set."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {},
                "viewers": {
                    "viewer1": {
                        "id": "viewer1",
                        "name": "Test Viewer",
                        "state": "CONNECTED",
                    },
                },
                "liveviews": {
                    "lv1": {"id": "lv1", "name": "Default View"},
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }

        entity = UnifiProtectViewerLiveviewSelect(
            coordinator=mock_coordinator,
            viewer_id="viewer1",
        )

        assert entity._attr_current_option is None

    async def test_async_select_option_success(self, mock_coordinator):
        """Test selecting liveview option successfully."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {},
                "viewers": {
                    "viewer1": {
                        "id": "viewer1",
                        "name": "Test Viewer",
                        "state": "CONNECTED",
                        "liveview": "lv1",
                    },
                },
                "liveviews": {
                    "lv1": {"id": "lv1", "name": "Default View"},
                    "lv2": {"id": "lv2", "name": "All Cameras"},
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_viewer = AsyncMock()

        entity = UnifiProtectViewerLiveviewSelect(
            coordinator=mock_coordinator,
            viewer_id="viewer1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("All Cameras")

        mock_coordinator.protect_client.update_viewer.assert_called_once_with(
            viewer_id="viewer1", data={"liveview": "lv2"}
        )
        assert entity._attr_current_option == "All Cameras"

    async def test_async_select_option_liveview_not_found(self, mock_coordinator):
        """Test selecting liveview that doesn't exist."""
        mock_coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "chimes": {},
                "viewers": {
                    "viewer1": {
                        "id": "viewer1",
                        "name": "Test Viewer",
                        "state": "CONNECTED",
                    },
                },
                "liveviews": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
            },
        }
        mock_coordinator.protect_client = MagicMock()
        mock_coordinator.protect_client.update_viewer = AsyncMock()

        entity = UnifiProtectViewerLiveviewSelect(
            coordinator=mock_coordinator,
            viewer_id="viewer1",
        )
        entity.async_write_ha_state = MagicMock()

        await entity.async_select_option("NonExistent")

        mock_coordinator.protect_client.update_viewer.assert_not_called()
