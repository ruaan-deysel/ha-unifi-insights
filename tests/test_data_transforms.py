"""Tests for data transformation functions."""

from custom_components.unifi_insights.data_transforms import (
    map_device_status,
    transform_network_device,
    transform_protect_camera,
    transform_protect_chime,
    transform_protect_light,
    transform_protect_sensor,
)
from tests.fixtures.library_responses import (
    SAMPLE_NETWORK_DEVICE,
    SAMPLE_PROTECT_CAMERA,
    SAMPLE_PROTECT_CHIME,
    SAMPLE_PROTECT_LIGHT,
    SAMPLE_PROTECT_SENSOR,
)


def test_map_device_status_online():
    """Test mapping online status."""
    assert map_device_status("online") == "connected"


def test_map_device_status_offline():
    """Test mapping offline status."""
    assert map_device_status("offline") == "disconnected"


def test_map_device_status_unknown():
    """Test mapping unknown status."""
    assert map_device_status("unknown") == "unknown"


def test_map_device_status_none():
    """Test mapping None status."""
    assert map_device_status(None) == "unknown"


def test_transform_network_device():
    """Test network device transformation."""
    result = transform_network_device(SAMPLE_NETWORK_DEVICE)

    assert result["id"] == "test_device_1"
    assert result["mac"] == "AA:BB:CC:DD:EE:FF"
    assert result["model"] == "USW-24-POE"
    assert result["name"] == "Test Switch"
    assert result["state"] == "connected"  # Mapped from "online"
    assert result["adopted"] is True
    assert result["version"] == "6.5.55"  # Renamed from firmware_version
    assert result["uptime"] == 864000  # Renamed from uptime_seconds
    assert result["cpu_usage"] == 15.2  # Renamed from cpu_percent
    assert result["memory_usage"] == 42.8  # Renamed from memory_percent
    assert result["tx_bytes"] == 1024000000
    assert result["rx_bytes"] == 2048000000
    assert result["site_id"] == "default"  # Renamed from site


def test_transform_protect_camera():
    """Test Protect camera transformation."""
    result = transform_protect_camera(SAMPLE_PROTECT_CAMERA)

    assert result["id"] == "test_camera_1"
    assert result["name"] == "Front Door Camera"
    assert result["state"] == "CONNECTED"  # Uppercased from "connected"
    assert result["is_recording"] is True  # Renamed from recording
    assert result["motion_detected"] is False  # Renamed from motion
    assert result["type"] == "UVC-G4-PRO"  # Renamed from model
    assert result["hdr_mode"] == "AUTO"  # Uppercased from "auto"
    assert result["video_mode"] == "DEFAULT"  # Uppercased from "default"


def test_transform_protect_light():
    """Test Protect light transformation."""
    result = transform_protect_light(SAMPLE_PROTECT_LIGHT)

    assert result["id"] == "test_light_1"
    assert result["name"] == "Garage Light"
    assert result["is_on"] is True  # Renamed from on
    assert result["brightness"] == 80
    assert result["mode"] == "MOTION"  # Uppercased from "motion"
    assert result["is_dark"] is False  # Renamed from dark


def test_transform_protect_sensor():
    """Test Protect sensor transformation."""
    result = transform_protect_sensor(SAMPLE_PROTECT_SENSOR)

    assert result["id"] == "test_sensor_1"
    assert result["name"] == "Kitchen Sensor"
    assert result["temperature"] == 22.5
    assert result["humidity"] == 45
    assert result["light_level"] == 750  # Renamed from light
    assert result["battery_percentage"] == 85  # Renamed from battery


def test_transform_protect_chime():
    """Test Protect chime transformation."""
    result = transform_protect_chime(SAMPLE_PROTECT_CHIME)

    assert result["id"] == "test_chime_1"
    assert result["name"] == "Doorbell Chime"
    assert result["volume"] == 60
    assert result["repeat_times"] == 2  # Renamed from repeat
    assert result["ringtone_id"] == "DEFAULT"  # Renamed from ringtone


def test_transform_network_device_missing_fields():
    """Test network device transformation with missing fields."""
    minimal_device = {"id": "test", "mac": "AA:BB:CC:DD:EE:FF"}
    result = transform_network_device(minimal_device)

    assert result["id"] == "test"
    assert result["mac"] == "AA:BB:CC:DD:EE:FF"
    assert result["state"] == "unknown"  # Default when status missing
    assert result["version"] is None
    assert result["cpu_usage"] is None


def test_transform_protect_camera_missing_fields():
    """Test Protect camera transformation with missing fields."""
    minimal_camera = {"id": "cam1", "name": "Test"}
    result = transform_protect_camera(minimal_camera)

    assert result["id"] == "cam1"
    assert result["name"] == "Test"
    assert result["state"] == "UNKNOWN"  # Default when status missing
    assert result["hdr_mode"] == "AUTO"  # Default when hdr missing
    assert result["video_mode"] == "DEFAULT"  # Default when video_mode missing
