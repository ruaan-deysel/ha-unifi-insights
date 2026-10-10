"""Tests for translation key completeness.

`translations/en.json` is the file Home Assistant actually loads at
runtime for a custom integration; `strings.json` is the source of truth
maintainers edit. These two files had drifted apart for the Protect
binary_sensor entities specifically - see
`test_binary_sensor_camera_and_sensor_translation_keys_present_in_en_json`.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from string import Formatter

from custom_components.unifi_insights.binary_sensor import BINARY_SENSOR_TYPES
from custom_components.unifi_insights.mobility_entity import (
    LOCATION_DESCRIPTION,
    ROUTER_SENSORS,
    WORKSPACE_SENSORS,
)
from custom_components.unifi_insights.network_rule_switch import (
    NETWORK_RULE_SWITCH_TYPES,
)
from custom_components.unifi_insights.protect_security_entity import (
    SECURITY_BINARY_SENSOR_TYPES,
    SECURITY_SENSOR_TYPES,
)
from custom_components.unifi_insights.site_internet_activity_sensor import (
    SITE_INTERNET_ACTIVITY_SENSOR_TYPES,
)

_INTEGRATION_DIR = Path(__file__).parent.parent / "custom_components" / "unifi_insights"
_EN_JSON = _INTEGRATION_DIR / "translations" / "en.json"
_STRINGS_JSON = _INTEGRATION_DIR / "strings.json"
_ICONS_JSON = _INTEGRATION_DIR / "icons.json"


def test_binary_sensor_camera_and_sensor_translation_keys_present_in_en_json() -> None:
    """Every camera_*/sensor_* binary_sensor translation_key must resolve
    in translations/en.json, matching strings.json.

    Regression test: translations/en.json's entity.binary_sensor section
    had only 6 keys (device_status, door, doorbell, is_dark, is_recording,
    motion) while strings.json correctly defined camera_motion,
    camera_person_detection, etc. HA falls back to the device_class name
    ("Motion") when a translation_key lookup fails, so all four per-camera
    detection sensors rendered as "Motion" and collided into _2/_3/_4
    entity_id suffixes.
    """
    en_data = json.loads(_EN_JSON.read_text())
    en_keys = set(en_data["entity"]["binary_sensor"].keys())

    camera_and_sensor_keys = {
        description.translation_key
        for description in BINARY_SENSOR_TYPES
        if description.translation_key
        and description.translation_key.startswith(("camera_", "sensor_"))
    }

    missing = camera_and_sensor_keys - en_keys
    assert missing == set()


def test_en_json_camera_and_sensor_names_match_strings_json() -> None:
    """The values added to en.json must mirror strings.json exactly, not
    just exist as keys - a mismatched display name would be its own bug.
    """
    en_data = json.loads(_EN_JSON.read_text())
    strings_data = json.loads(_STRINGS_JSON.read_text())
    en_binary_sensor = en_data["entity"]["binary_sensor"]
    strings_binary_sensor = strings_data["entity"]["binary_sensor"]

    for key, value in strings_binary_sensor.items():
        if key.startswith(("camera_", "sensor_")):
            assert key in en_binary_sensor, f"{key} missing from translations/en.json"
            assert en_binary_sensor[key] == value


def _switch_translation_keys() -> set[str]:
    """Collect every `_attr_translation_key` string literal in switch.py."""
    tree = ast.parse((_INTEGRATION_DIR / "switch.py").read_text())
    return {
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Attribute) and target.attr == "_attr_translation_key"
    }


def _switch_supplied_placeholders() -> set[str]:
    """Collect every key passed to `_attr_translation_placeholders` in switch.py."""
    tree = ast.parse((_INTEGRATION_DIR / "switch.py").read_text())
    return {
        key.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
        for target in node.targets
        if isinstance(target, ast.Attribute)
        and target.attr == "_attr_translation_placeholders"
        for key in node.value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def test_switch_translation_keys_resolve_in_both_files() -> None:
    """Every translation_key used in switch.py must resolve in both files.

    Regression guard for the naming change that moved the dynamically named
    switches (firewall rule, policy-based route, VPN client, client allow,
    WiFi) off `_attr_name` and onto translation keys. Those entities set
    `_attr_has_entity_name = True` and have no `entity_description`, so a
    missing key makes `Entity._name_internal` return `UNDEFINED` and the
    friendly name silently collapses to the *device* name - every switch on
    a gateway then renders identically and collides on entity_id, exactly
    the failure documented above for the Protect binary sensors.
    """
    en_switch = json.loads(_EN_JSON.read_text())["entity"]["switch"]
    strings_switch = json.loads(_STRINGS_JSON.read_text())["entity"]["switch"]

    for key in sorted(_switch_translation_keys()):
        assert key in strings_switch, f"{key} missing from strings.json"
        assert key in en_switch, f"{key} missing from translations/en.json"
        assert en_switch[key] == strings_switch[key], (
            f"{key} differs between strings.json and translations/en.json"
        )


def test_switch_translation_placeholders_are_supplied() -> None:
    """Placeholders required by a switch name must be supplied by the code.

    `Entity._substitute_name_placeholders` raises `HomeAssistantError` on a
    missing placeholder outside the stable release channel, so a typo here
    breaks the entity rather than degrading it.
    """
    strings_switch = json.loads(_STRINGS_JSON.read_text())["entity"]["switch"]
    supplied = _switch_supplied_placeholders()

    for key in sorted(_switch_translation_keys()):
        required = {
            field
            for _, field, _, _ in Formatter().parse(strings_switch[key]["name"])
            if field
        }
        missing = required - supplied
        assert missing == set(), (
            f"switch.{key} name needs placeholders {sorted(missing)} "
            "which switch.py never supplies"
        )


def test_site_internet_activity_sensor_translations_resolve_in_both_files() -> None:
    """Every site internet activity sensor must have matching translations."""
    en_sensor = json.loads(_EN_JSON.read_text())["entity"]["sensor"]
    strings_sensor = json.loads(_STRINGS_JSON.read_text())["entity"]["sensor"]

    for desc in SITE_INTERNET_ACTIVITY_SENSOR_TYPES:
        key = desc.translation_key
        assert key is not None
        assert key in strings_sensor, f"{key} missing from strings.json"
        assert key in en_sensor, f"{key} missing from translations/en.json"
        assert en_sensor[key] == strings_sensor[key], (
            f"{key} differs between strings.json and translations/en.json"
        )
        assert desc.name == strings_sensor[key]["name"]


def test_mobility_translations_and_icons_resolve_in_every_file() -> None:
    """Every Mobility entity has a name, enum state names and an icon."""
    files = {
        "strings.json": json.loads(_STRINGS_JSON.read_text())["entity"],
        "translations/en.json": json.loads(_EN_JSON.read_text())["entity"],
    }
    icons = json.loads(_ICONS_JSON.read_text())["entity"]
    descriptions = [
        ("sensor", desc) for desc in (*ROUTER_SENSORS, *WORKSPACE_SENSORS)
    ] + [("device_tracker", LOCATION_DESCRIPTION)]

    for platform, desc in descriptions:
        key = desc.translation_key
        assert key is not None, desc.key
        assert key.startswith("mobility_"), key
        for name, entity in files.items():
            translation = entity.get(platform, {}).get(key)
            assert translation, f"{platform}.{key} missing from {name}"
            assert translation["name"], f"{platform}.{key} has no name in {name}"
            for option in getattr(desc, "options", None) or []:
                assert translation.get("state", {}).get(option), (
                    f"{platform}.{key} state {option} missing from {name}"
                )
        assert (
            files["strings.json"][platform][key]
            == (files["translations/en.json"][platform][key])
        )
        assert icons.get(platform, {}).get(key, {}).get("default"), (
            f"{platform}.{key} has no icon"
        )


def test_protect_security_entity_translations_resolve_in_both_files() -> None:
    """Alarm hub/Thread/fob entities resolve, ENUM states included."""
    en = json.loads(_EN_JSON.read_text())["entity"]
    strings = json.loads(_STRINGS_JSON.read_text())["entity"]

    for platform, descriptions in (
        ("binary_sensor", SECURITY_BINARY_SENSOR_TYPES),
        ("sensor", SECURITY_SENSOR_TYPES),
    ):
        for desc in descriptions:
            key = desc.translation_key
            assert key is not None
            assert key in strings[platform], f"{key} missing from strings.json"
            assert key in en[platform], f"{key} missing from translations/en.json"
            assert en[platform][key] == strings[platform][key], (
                f"{key} differs between strings.json and translations/en.json"
            )
            assert strings[platform][key]["name"]
            options = getattr(desc, "options", None)
            if options:
                assert set(strings[platform][key]["state"]) == set(options), key


def test_protect_security_entity_icons_defined() -> None:
    """Every alarm hub/Thread/fob entity has an icon in icons.json."""
    icons = json.loads(_ICONS_JSON.read_text())["entity"]

    for platform, descriptions in (
        ("binary_sensor", SECURITY_BINARY_SENSOR_TYPES),
        ("sensor", SECURITY_SENSOR_TYPES),
    ):
        for desc in descriptions:
            entry = icons.get(platform, {}).get(desc.translation_key)
            assert entry is not None, f"{desc.translation_key} has no icon"
            assert entry["default"].startswith("mdi:")


def test_voucher_translation_and_icon_keys_present() -> None:
    """Hotspot voucher entity keys exist in strings.json, en.json, and icons.json."""
    strings_data = json.loads(_STRINGS_JSON.read_text())["entity"]
    en_data = json.loads(_EN_JSON.read_text())["entity"]
    icons_data = json.loads(_ICONS_JSON.read_text())["entity"]

    expected_keys = {
        "number": [
            "voucher_duration",
            "voucher_guest_limit",
            "voucher_download_limit",
            "voucher_upload_limit",
            "voucher_data_limit",
        ],
        "button": [
            "generate_voucher",
        ],
        "sensor": [
            "latest_voucher_code",
            "latest_voucher_expiration",
            "active_vouchers",
        ],
        "image": [
            "voucher_qr_code",
        ],
    }

    for platform, keys in expected_keys.items():
        for key in keys:
            assert key in strings_data[platform], (
                f"{platform}.{key} missing from strings.json"
            )
            assert key in en_data[platform], (
                f"{platform}.{key} missing from translations/en.json"
            )
            assert strings_data[platform][key] == en_data[platform][key], (
                f"{platform}.{key} mismatch between strings.json and en.json"
            )
            assert key in icons_data[platform], (
                f"{platform}.{key} missing from icons.json"
            )
            icon_entry = icons_data[platform][key]
            assert "default" in icon_entry, f"{platform}.{key} missing default icon"
            assert icon_entry["default"].startswith("mdi:"), (
                f"{platform}.{key} invalid icon"
            )


def test_network_rule_switch_translations_resolve_in_both_files() -> None:
    """Network rule switch translations match in both files with placeholders."""
    en_switch = json.loads(_EN_JSON.read_text())["entity"]["switch"]
    strings_switch = json.loads(_STRINGS_JSON.read_text())["entity"]["switch"]

    for desc in NETWORK_RULE_SWITCH_TYPES:
        for key, placeholder in (
            (desc.translation_key, "{rule_name}"),
            (desc.unnamed_translation_key, "{rule_id}"),
        ):
            assert key in strings_switch, f"{key} missing from strings.json"
            assert key in en_switch, f"{key} missing from translations/en.json"
            assert en_switch[key] == strings_switch[key], (
                f"{key} differs between strings.json and translations/en.json"
            )
            assert placeholder in strings_switch[key]["name"], (
                f"{key} name must contain {placeholder}"
            )


def test_network_rule_switch_icons_defined() -> None:
    """Network rule switch icons are defined with default and state.off."""
    icons = json.loads(_ICONS_JSON.read_text())["entity"]["switch"]

    for desc in NETWORK_RULE_SWITCH_TYPES:
        for key in (desc.translation_key, desc.unnamed_translation_key):
            entry = icons.get(key)
            assert entry is not None, f"{key} has no icon entry in icons.json"
            assert entry.get("default", "").startswith("mdi:"), (
                f"{key} default icon missing or not mdi:"
            )
            assert entry.get("state", {}).get("off", "").startswith("mdi:"), (
                f"{key} state.off icon missing or not mdi:"
            )
