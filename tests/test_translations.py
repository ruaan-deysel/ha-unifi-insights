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
from custom_components.unifi_insights.site_internet_activity_sensor import (
    SITE_INTERNET_ACTIVITY_SENSOR_TYPES,
)

_INTEGRATION_DIR = Path(__file__).parent.parent / "custom_components" / "unifi_insights"
_EN_JSON = _INTEGRATION_DIR / "translations" / "en.json"
_STRINGS_JSON = _INTEGRATION_DIR / "strings.json"


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
