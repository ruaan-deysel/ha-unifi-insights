"""Tests for helper utilities in UniFi Insights."""

from unittest.mock import MagicMock

import pytest
from homeassistant.helpers import device_registry as dr

from custom_components.unifi_insights import helpers
from custom_components.unifi_insights.helpers import async_get_device_entry

IDENTIFIER = ("unifi_insights", "dev1")


@pytest.fixture
def registry() -> MagicMock:
    """Return a registry double exposing all three lookup methods."""
    return MagicMock()


def _set_support(monkeypatch, *, by_identifier: bool, get_devices: bool) -> None:
    """Pin the detected HA device registry capabilities."""
    monkeypatch.setattr(helpers, "_SUPPORTS_BY_IDENTIFIER", by_identifier)
    monkeypatch.setattr(helpers, "_SUPPORTS_GET_DEVICES", get_devices)


def test_uses_by_identifier_when_supported(monkeypatch, registry):
    """On HA 2026.8+ the config-entry-scoped lookup is used."""
    _set_support(monkeypatch, by_identifier=True, get_devices=True)
    device = object()
    registry.async_get_device_by_identifier.return_value = device

    assert async_get_device_entry(registry, IDENTIFIER, "entry1") is device
    registry.async_get_device_by_identifier.assert_called_once_with(
        IDENTIFIER, "entry1"
    )
    registry.async_get_device.assert_not_called()


def test_miss_does_not_fall_back_to_deprecated_api(monkeypatch, registry):
    """A miss returns None without touching the deprecated async_get_device."""
    _set_support(monkeypatch, by_identifier=True, get_devices=True)
    registry.async_get_device_by_identifier.return_value = None

    assert async_get_device_entry(registry, IDENTIFIER, "entry1") is None
    registry.async_get_device.assert_not_called()
    registry.async_get_devices.assert_not_called()


def test_uses_get_devices_without_config_entry_id(monkeypatch, registry):
    """Without a config entry id the unscoped list lookup is used."""
    _set_support(monkeypatch, by_identifier=True, get_devices=True)
    device = object()
    registry.async_get_devices.return_value = [device]

    assert async_get_device_entry(registry, IDENTIFIER) is device
    registry.async_get_devices.assert_called_once_with(identifiers={IDENTIFIER})
    registry.async_get_device.assert_not_called()


def test_get_devices_empty_returns_none(monkeypatch, registry):
    """An empty list from async_get_devices resolves to None."""
    _set_support(monkeypatch, by_identifier=True, get_devices=True)
    registry.async_get_devices.return_value = []

    assert async_get_device_entry(registry, IDENTIFIER) is None
    registry.async_get_device.assert_not_called()


def test_legacy_fallback_when_new_apis_absent(monkeypatch, registry):
    """On HA < 2026.8 the legacy lookup is the only option."""
    _set_support(monkeypatch, by_identifier=False, get_devices=False)
    device = object()
    registry.async_get_device.return_value = device

    assert async_get_device_entry(registry, IDENTIFIER, "entry1") is device
    registry.async_get_device.assert_called_once_with(identifiers={IDENTIFIER})


def test_capability_flags_match_installed_homeassistant():
    """The detected capabilities reflect the real HA device registry class."""
    expected_by_identifier = hasattr(
        dr.DeviceRegistry, "async_get_device_by_identifier"
    )
    expected_get_devices = hasattr(dr.DeviceRegistry, "async_get_devices")

    assert helpers._SUPPORTS_BY_IDENTIFIER is expected_by_identifier
    assert helpers._SUPPORTS_GET_DEVICES is expected_get_devices
