"""Sample library response data for testing."""

# Network API responses
SAMPLE_SITE = {
    "id": "default",
    "name": "Default",
    "desc": "Default Site",
}

SAMPLE_NETWORK_DEVICE = {
    "id": "test_device_1",
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "USW-24-POE",
    "name": "Test Switch",
    "status": "online",
    "adopted": True,
    "firmware_version": "6.5.55",
    "uptime_seconds": 864000,
    "cpu_percent": 15.2,
    "memory_percent": 42.8,
    "tx_bytes": 1024000000,
    "rx_bytes": 2048000000,
    "site": "default",
}

SAMPLE_CLIENT = {
    "id": "client_1",
    "mac": "11:22:33:44:55:66",
    "name": "Test Device",
    "ip": "192.168.1.100",
    "site": "default",
}

# Protect API responses
SAMPLE_PROTECT_CAMERA = {
    "id": "test_camera_1",
    "name": "Front Door Camera",
    "model": "UVC-G4-PRO",
    "status": "connected",
    "recording": True,
    "motion": False,
    "hdr": "auto",
    "video_mode": "default",
    "is_dark": False,
}

SAMPLE_PROTECT_LIGHT = {
    "id": "test_light_1",
    "name": "Garage Light",
    "model": "UP-LIGHT",
    "on": True,
    "brightness": 80,
    "light_mode": "motion",
    "dark": False,
}

SAMPLE_PROTECT_SENSOR = {
    "id": "test_sensor_1",
    "name": "Kitchen Sensor",
    "model": "UP-SENSE",
    "temperature": 22.5,
    "humidity": 45,
    "light": 750,
    "battery": 85,
}

SAMPLE_PROTECT_CHIME = {
    "id": "test_chime_1",
    "name": "Doorbell Chime",
    "model": "UP-CHIME",
    "volume": 60,
    "repeat": 2,
    "ringtone": "DEFAULT",
}

SAMPLE_NVR = {
    "id": "nvr_1",
    "name": "UniFi Protect",
    "model": "UNVR",
    "version": "3.0.22",
}


# Mock exception responses
class MockUniFiAuthError(Exception):
    """Mock authentication error."""


class MockUniFiConnectionError(Exception):
    """Mock connection error."""


class MockUniFiTimeoutError(Exception):
    """Mock timeout error."""


class MockUniFiAPIError(Exception):
    """Mock API error."""
