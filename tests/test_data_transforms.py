"""Tests for data transformation functions."""

from custom_components.unifi_insights.data_transforms import (
    map_device_status,
    normalize_innerspace_snapshot,
    normalize_legacy_wans,
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


def test_normalize_legacy_wans_uses_controller_status():
    """Each WAN named in last_wan_status becomes one connection entry."""
    wans = normalize_legacy_wans(
        {
            # The physical port block is ignored: it cannot see a PPP session.
            "wan1": {"type": "ethernet", "name": "eth8", "up": True},
            "last_wan_status": {"WAN": "online", "WAN2": "offline"},
            "last_wan_interfaces": {
                "WAN": {"ip": "198.51.100.7", "alive": True},
                "WAN2": {"ip": "", "alive": False},
            },
        }
    )
    assert wans == [
        {
            "key": "wan",
            "name": "WAN",
            "status": "online",
            "alive": True,
            "ip": "198.51.100.7",
            "connected": True,
        },
        {
            "key": "wan2",
            "name": "WAN2",
            "status": "offline",
            "alive": False,
            "ip": None,
            "connected": False,
        },
    ]


def test_normalize_legacy_wans_status_wins_over_alive():
    """The controller's status decides even when the probe disagrees."""
    (wan,) = normalize_legacy_wans(
        {
            "last_wan_status": {"WAN": "Offline"},
            "last_wan_interfaces": {"WAN": {"ip": "198.51.100.7", "alive": True}},
        }
    )
    assert wan["connected"] is False


def test_normalize_legacy_wans_falls_back_to_alive():
    """Without a status string, the reachability probe decides."""
    wans = normalize_legacy_wans(
        {
            "last_wan_interfaces": {
                "WAN": {"ip": "198.51.100.7", "alive": True},
                "WAN2": {"alive": "yes"},
            }
        }
    )
    assert [(w["key"], w["connected"], w["alive"]) for w in wans] == [
        ("wan", True, True),
        ("wan2", False, None),
    ]


def test_normalize_legacy_wans_unspecified_address_is_none():
    """Placeholder addresses a down link reports are not exposed as its IP."""
    # 0.0.0.0 is a payload value compared against here, not an address bound.
    for missing_ip in ("", "0.0.0.0", "::", None):  # noqa: S104
        (wan,) = normalize_legacy_wans(
            {"last_wan_interfaces": {"WAN": {"ip": missing_ip, "alive": False}}}
        )
        assert wan["ip"] is None


def test_normalize_legacy_wans_without_wan_data():
    """Non-gateways and malformed payloads yield no WAN entries."""
    assert normalize_legacy_wans({"port_table": []}) == []
    assert normalize_legacy_wans({"last_wan_status": ["WAN"]}) == []
    assert (
        normalize_legacy_wans(
            {"last_wan_status": {"": "online", 3: "online"}, "last_wan_interfaces": 1}
        )
        == []
    )


def test_normalize_innerspace_snapshot_excludes_shapes_and_urls_and_correlates_macs():
    """Test InnerSpace normalization, placement states, and MAC correlation."""
    project = {
        "project": {"id": "proj-1", "model": None, "environment": None},
        "plans": [
            {
                "id": "fp-1",
                "name": "Office Floor",
                "ppm": 20.0,
                "ordering": 1,
                "siteId": "site-a",
            }
        ],
        "products": [{"id": "ap-1", "planId": "fp-1", "code": "U6-Pro"}],
        "shapes": [{"id": "shape-1", "type": "wall"}],
    }
    floor_plans = [
        {
            "id": "fp-1",
            "name": "Office Floor",
            "floor_number": 2,
            "image_url": "/proxy/innerspace/assets/fp-1.png",
            "ppm": 20.0,
            "width": 1000,
            "height": 800,
            "origin_x": 0.0,
            "origin_y": 0.0,
            "site_id": None,
        },
        {
            "id": "fp-unmapped",
            "name": "Warehouse Floor",
            "floor_number": 1,
            "site_id": None,
        },
    ]
    access_points = [
        {
            "id": "ap-1",
            "name": "Office AP",
            "model": "U6-Pro",
            "mac": "AA-BB-CC-11-22-33",
            "serial": "SN1",
            "floor_plan_id": "fp-1",
            "x": 120.5,
            "y": 340.0,
            "height": 2.8,
            "azimuth": 180.0,
            "mount": "ceiling",
            "status": "online",
        }
    ]
    switches = [
        {
            "id": "sw-1",
            "name": "Ambiguous Switch",
            "model": "USW-24",
            "mac": "AA:BB:CC:44:55:66",
            "floor_plan_id": "fp-unmapped",
            "x": 10.0,
            "y": 20.0,
            "status": "online",
        }
    ]
    inventory = [
        {
            "id": "inv-1",
            "name": "Spare Camera or AP",
            "model": "U6-Enterprise",
            "mac": "11:22:33:44:55:66",
            "serial": "SN-INV",
        }
    ]

    # Site-a and Site-b both have AA:BB:CC:11:22:33, narrowed by fp-1 to site-a.
    # AA:BB:CC:44:55:66 has no site_id across two sites -> ambiguous -> no match.
    network_devices = {
        "site-a": {
            "net-ap-a": {"id": "net-ap-a", "macAddress": "aa:bb:cc:11:22:33"},
            "net-sw-a": {"id": "net-sw-a", "macAddress": "aa:bb:cc:44:55:66"},
        },
        "site-b": {
            "net-ap-b": {"id": "net-ap-b", "macAddress": "aa:bb:cc:11:22:33"},
            "net-sw-b": {"id": "net-sw-b", "macAddress": "aa:bb:cc:44:55:66"},
        },
    }
    protect_devices = {
        "cameras": {
            "cam-1": {"id": "cam-1", "mac": "112233445566"},
        }
    }

    snapshot = normalize_innerspace_snapshot(
        project=project,
        floor_plans=floor_plans,
        access_points=access_points,
        switches=switches,
        inventory=inventory,
        network_devices=network_devices,
        protect_devices=protect_devices,
    )

    # Project shapes and floor_plan image_url must be excluded
    assert "shapes" not in snapshot["project"]
    assert "image_url" not in snapshot["floor_plans"]["fp-1"]
    assert snapshot["floor_plans"]["fp-1"]["site_id"] == "site-a"

    # Placed AP has placement_state='placed', site_id='site-a', and matches net-ap-a
    ap_rec = snapshot["access_points"]["ap-1"]
    assert ap_rec["placement_state"] == "placed"
    assert ap_rec["device_type"] == "access_point"
    assert ap_rec["matched_domain"] == "network"
    assert ap_rec["matched_site_id"] == "site-a"
    assert ap_rec["matched_device_id"] == "net-ap-a"

    # Ambiguous switch across two sites without site_id is NOT matched
    sw_rec = snapshot["switches"]["sw-1"]
    assert sw_rec["placement_state"] == "placed"
    assert sw_rec["matched_domain"] is None
    assert sw_rec["correlation"] is None

    # Unplaced inventory record stays distinct, never infers device_type from model,
    # and correlates with Protect camera by normalized MAC
    inv_rec = snapshot["inventory"]["inv-1"]
    assert inv_rec["placement_state"] == "unplaced"
    assert inv_rec["device_type"] is None
    assert inv_rec["matched_domain"] == "protect"
    assert inv_rec["matched_protect_type"] == "camera"
    assert inv_rec["matched_device_id"] == "cam-1"
