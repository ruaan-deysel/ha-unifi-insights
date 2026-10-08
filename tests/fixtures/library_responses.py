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

SAMPLE_PDU_DEVICE = {
    "id": "pdu_device_1",
    "mac": "00:11:22:33:44:55",
    "model": "USP-PDU-Pro",
    "name": "Server Room PDU",
    "status": "online",
    "state": "ONLINE",
    "adopted": True,
    "firmware_version": "6.6.65",
    "site": "default",
    "site_id": "default",
}

SAMPLE_PDU_LEGACY_DEVICE = {
    "_id": "60a1b2c3d4e5f67890123456",
    "mac": "00:11:22:33:44:55",
    "model": "USP-PDU-Pro",
    "name": "Server Room PDU",
    "outlet_ac_power_consumption": "245.50",
    "outlet_ac_power_budget": "1800.00",
    "outlet_table": [
        {
            "index": 1,
            "name": "Main Server",
            "relay_state": True,
            "cycle_enabled": True,
            "outlet_caps": 3,
            "outlet_voltage": "120.2",
            "outlet_current": "1.25",
            "outlet_power": "150.0",
            "outlet_power_factor": "0.98",
        },
        {
            "index": 2,
            "name": "Backup Server",
            "relay_state": False,
            "cycle_enabled": False,
            "outlet_caps": 3,
            "outlet_voltage": "120.1",
            "outlet_current": "0.00",
            "outlet_power": "0.0",
            "outlet_power_factor": "0.00",
        },
        {
            "index": 3,
            "name": "Unmetered Switch",
            "relay_state": True,
            "cycle_enabled": None,
            "outlet_caps": 1,
            "outlet_voltage": None,
            "outlet_current": None,
            "outlet_power": None,
            "outlet_power_factor": None,
        },
    ],
    "outlet_overrides": [
        {
            "index": 1,
            "name": "Main Server",
            "relay_state": True,
            "cycle_enabled": True,
        },
    ],
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

SAMPLE_USL_ENTRY_SENSOR = {
    "id": "test_sensor_usl",
    "name": "Front Door Sensor",
    "model": "USL-Entry",
    "state": "CONNECTED",
    "mountType": "door",
    "isOpened": False,
    "isTamperingDetected": False,
    "batteryStatus": {"percentage": 92, "isLow": False},
    "temperature": None,
    "humidity": None,
    "lightValue": None,
}

SAMPLE_PROTECT_CHIME = {
    "id": "test_chime_1",
    "name": "Doorbell Chime",
    "model": "UP-CHIME",
    "volume": 60,
    "repeat": 2,
    "ringtone": "DEFAULT",
}

# A doorbell camera and a chime shaped like the public Integration API returns
# them (spec: chime keys id, modelKey, state, name, type, guid, mac, cameraIds,
# ringSettings). The ids, MACs and guid are fakes.
SAMPLE_DOORBELL_CAMERA = {
    "id": "doorbell_cam_1",
    "modelKey": "camera",
    "mac": "AABBCC0000D1",
    "name": "Front Doorbell",
    "type": "UVC G4 Doorbell Pro",
    "state": "CONNECTED",
}

SAMPLE_PUBLIC_CHIME = {
    "id": "chime_1",
    "modelKey": "chime",
    "state": "CONNECTED",
    "name": "Hallway Chime",
    "type": "UP-Chime",
    "guid": "00000000-0000-4000-8000-0000000000c1",
    "mac": "AABBCC0000C1",
    "cameraIds": [],
    "ringSettings": [],
}

SAMPLE_NVR = {
    "id": "nvr_1",
    "name": "UniFi Protect",
    "model": "UNVR",
    "version": "3.0.22",
}

# Redacted capture of a real /nvrs object on Protect 7.3.70 (2026-10-06) with
# the global alarm manager on. The id, MAC, guid, name and armProfileId are
# fakes; every other value is as the console reported it.
SAMPLE_NVR_WITH_ARM_MODE = {
    "id": "nvr_1",
    "modelKey": "nvr",
    "name": "UniFi Protect",
    "type": "UNVR-PRO",
    "guid": "00000000-0000-4000-8000-0000000000aa",
    "mac": "AABBCC0000AA",
    "doorbellSettings": {
        "defaultMessageText": "WELCOME",
        "defaultMessageResetTimeoutMs": 60000,
        "customMessages": [],
        "customImages": [],
    },
    "armMode": {
        "status": "disabled",
        "armProfileId": "arm_profile_away",
        "armedAt": 1755916908659,
        "willBeArmedAt": None,
        "breachDetectedAt": None,
        "breachEventCount": 0,
        "breachTriggerEventId": None,
        "breachEventId": None,
    },
}

# Redacted capture of a real /link-stations item on Protect 7.3.70
# (2026-10-05). A SuperLink sends no "threadState" key at all, although the
# spec marks it required.
SAMPLE_LINK_STATION = {
    "id": "link_station_1",
    "modelKey": "linkstation",
    "state": "CONNECTED",
    "name": "SuperLink",
    "type": "UP-SuperLink-US",
    "guid": "00000000-0000-0000-0000-000000000001",
    "mac": "AABBCC000001",
    "isAlarmHub": False,
    "ledSettings": {"isEnabled": True},
    "lastEvent": None,
}

# The rest are built from the Protect 7.3.70 OpenAPI schemas: no console used
# for these captures had a Thread gateway, an alarm hub or a fob.
SAMPLE_THREAD_LINK_STATION = {
    "id": "link_station_thread",
    "modelKey": "linkstation",
    "state": "CONNECTED",
    "name": "Thread Gateway",
    "type": "UP-SuperLink-US",
    "mac": "AABBCC000002",
    "isAlarmHub": False,
    "ledSettings": {"isEnabled": True},
    "lastEvent": 1759628000000,
    "threadState": {
        "network": {
            "status": "ready",
            "role": "leader",
            "networkName": "Home Thread",
            "channel": 15,
            "panId": "1a2b",
            "extendedPanId": "0011223344556677",
            "joinedDeviceCount": 4,
            "errorReason": None,
            "lastUpdatedAt": 1759628000000,
        }
    },
}

SAMPLE_ALARM_HUB = {
    "id": "alarm_hub_1",
    "modelKey": "linkstation",
    "state": "CONNECTED",
    "name": "Alarm Hub",
    "type": "UP-AlarmHub",
    "mac": "AABBCC000003",
    "isAlarmHub": True,
    "ledSettings": {"isEnabled": True},
    "lastEvent": None,
    "alarmHub": {
        "armed": "off",
        "battery": {"charging": "off", "batteryStatus": "ok", "voltage": 13.1},
        "deviceTamperStatus": "restored",
    },
    "threadState": {"network": None},
}

SAMPLE_KEYPAD_FOB = {
    "id": "fob_1",
    "modelKey": "fob",
    "state": "CONNECTED",
    "name": "Hallway Keypad",
    "type": "UP-Keypad",
    "mac": "AABBCC000004",
    "awayState": "ONLINE",
    "buttonLabels": "securityActions",
    "featureFlags": {"buttons": ["arm", "disarm", "night"], "hasKeypad": True},
    "armControlSettings": {
        "enabled": True,
        "armProfileId": "arm_profile_away",
        "nightProfileId": None,
    },
    "keypadSettings": {"beepEnabled": True, "beepVolume": 60},
    "wirelessConnectionState": {
        "signalState": "good",
        "batteryStatus": {"percentage": 90, "isLow": False},
        "bridge": "link_station_1",
    },
}

# Redacted capture of a live UP-Siren-PoE (Protect 7.3.70). The id, MAC and guid
# are fakes; every other value is as the console reported it.
SAMPLE_SIREN = {
    "id": "siren_1",
    "modelKey": "siren",
    "state": "CONNECTED",
    "name": "Garage Siren",
    "type": "UP-Siren-PoE",
    "guid": "00000000-0000-4000-8000-000000000005",
    "mac": "AABBCC000005",
    "volume": 50,
    "ledSettings": {"isEnabled": True},
    "sirenStatus": {"isActive": False, "activatedAt": None, "duration": None},
    "connectionType": "ucp4",
    "wirelessConnectionState": {
        "signalState": {"signalQuality": None, "signalStrength": None},
        "batteryStatus": {"percentage": None, "isLow": False},
        "bridge": None,
    },
}

SAMPLE_ALARM_HUB_TAMPER_EVENT = {
    "id": "event_tamper_1",
    "modelKey": "event",
    "type": "alarmHubDeviceTamper",
    "start": 1759628100000,
    "end": None,
    "device": "alarm_hub_1",
    "metadata": {
        "status": {"text": "tampered"},
        "deviceId": {"text": "alarm_hub_1"},
        "deviceName": {"text": "Alarm Hub"},
        "userName": "Installer",
    },
}

SAMPLE_SITE_REPORT_RESPONSE = {
    "meta": {"rc": "ok"},
    "data": [
        {
            "time": 1790373600000,
            "wan-rx_bytes": 1.2628779867391305e8,
            "wan-tx_bytes": 5991446.652173913,
            "wan2-rx_bytes": 0.0,
            "wan2-tx_bytes": 0.0,
            "site": "600ee7a7c6aeaa055108e337",
            "o": "site",
            "oid": "600ee7a7c6aeaa055108e337",
        },
        {
            "time": 1790373900000,
            "wan-rx_bytes": 9.552575601358695e7,
            "wan-tx_bytes": 4120000.0,
            "wan2-rx_bytes": 1000000.0,
            "wan2-tx_bytes": 500000.0,
            "site": "600ee7a7c6aeaa055108e337",
            "o": "site",
            "oid": "600ee7a7c6aeaa055108e337",
        },
    ],
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
