"""UniFi Protect API module."""

from __future__ import annotations

from .client import UniFiProtectClient
from .models import (
    NVR,
    Camera,
    CameraState,
    CameraType,
    Chime,
    Event,
    EventType,
    Light,
    LightMode,
    LiveView,
    RecordingMode,
    Sensor,
    SensorType,
    UlpUser,
    UlpUserStatus,
    User,
    VideoMode,
)
from .websocket import ProtectWebSocket

__all__ = [
    "NVR",
    "Camera",
    "CameraState",
    "CameraType",
    "Chime",
    "Event",
    "EventType",
    "Light",
    "LightMode",
    "LiveView",
    "ProtectWebSocket",
    "RecordingMode",
    "Sensor",
    "SensorType",
    "UlpUser",
    "UlpUserStatus",
    "UniFiProtectClient",
    "User",
    "VideoMode",
]
