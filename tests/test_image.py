"""Tests for the UniFi Insights WiFi QR code image platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from custom_components.unifi_insights.image import (
    UnifiWifiQrCodeImage,
    async_setup_entry,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

QR_PAYLOAD: str = "WIFI:T:WPA;S:TestNet;P:secret123;;"


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create mock coordinator with WiFi data."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "wifi": {
            "site1": {
                "wifi1": {
                    "id": "wifi1",
                    "name": "TestNet",
                    "ssid": "TestNet",
                    "qr_code": QR_PAYLOAD,
                },
                "wifi2": {
                    "id": "wifi2",
                    "name": "NoSecretNet",
                    # No qr_code: passphrase unavailable from classic API
                },
            }
        },
    }
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_setup_creates_qr_entities_only_with_payload(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """Only networks with a resolved QR payload get an image entity."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()
        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert entities[0].unique_id == "site1_wifi1_qr_code"

    @pytest.mark.asyncio
    async def test_setup_no_entities_without_payloads(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """No entities are added when no network has a QR payload."""
        mock_coordinator.data["wifi"]["site1"]["wifi1"].pop("qr_code")

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()
        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_not_called()


class TestUnifiWifiQrCodeImage:
    """Tests for the UnifiWifiQrCodeImage entity."""

    def _make_entity(
        self, hass: HomeAssistant, mock_coordinator
    ) -> UnifiWifiQrCodeImage:
        return UnifiWifiQrCodeImage(
            hass=hass,
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
        )

    def test_initialization(self, hass: HomeAssistant, mock_coordinator) -> None:
        """Test unique ID, name, and device info."""
        entity = self._make_entity(hass, mock_coordinator)

        assert entity.unique_id == "site1_wifi1_qr_code"
        assert entity._attr_name == "WiFi QR code"
        assert entity._attr_content_type == "image/png"
        assert entity._attr_device_info["name"] == "WiFi: TestNet"

    def test_available_with_payload(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """Entity is available while a payload exists and updates succeed."""
        entity = self._make_entity(hass, mock_coordinator)
        assert entity.available is True

    def test_unavailable_without_payload(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """Entity becomes unavailable when the payload disappears."""
        entity = self._make_entity(hass, mock_coordinator)
        mock_coordinator.data["wifi"]["site1"]["wifi1"].pop("qr_code")
        assert entity.available is False

    def test_unavailable_on_failed_update(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """Entity is unavailable when the coordinator update failed."""
        entity = self._make_entity(hass, mock_coordinator)
        mock_coordinator.last_update_success = False
        assert entity.available is False

    @pytest.mark.asyncio
    async def test_async_image_returns_png(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """async_image renders a PNG for the current payload."""
        entity = self._make_entity(hass, mock_coordinator)

        image = await entity.async_image()

        assert image is not None
        assert image.startswith(b"\x89PNG")

    @pytest.mark.asyncio
    async def test_async_image_cached_until_payload_changes(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """The rendered PNG is cached for an unchanged payload."""
        entity = self._make_entity(hass, mock_coordinator)

        first = await entity.async_image()
        second = await entity.async_image()
        assert first is second

        mock_coordinator.data["wifi"]["site1"]["wifi1"]["qr_code"] = (
            "WIFI:T:WPA;S:TestNet;P:newsecret;;"
        )
        third = await entity.async_image()
        assert third is not None
        assert third != first

    @pytest.mark.asyncio
    async def test_async_image_none_without_payload(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """async_image returns None when no payload is available."""
        entity = self._make_entity(hass, mock_coordinator)
        mock_coordinator.data["wifi"]["site1"]["wifi1"].pop("qr_code")

        assert await entity.async_image() is None

    def test_coordinator_update_refreshes_timestamp_on_change(
        self, hass: HomeAssistant, mock_coordinator
    ) -> None:
        """A payload change bumps image_last_updated; no change keeps it."""
        entity = self._make_entity(hass, mock_coordinator)

        with patch.object(entity, "async_write_ha_state"):
            initial = entity._attr_image_last_updated

            # Payload changed since the cached render → timestamp bumps
            mock_coordinator.data["wifi"]["site1"]["wifi1"]["qr_code"] = (
                "WIFI:T:WPA;S:TestNet;P:rotated;;"
            )
            entity._handle_coordinator_update()
            changed = entity._attr_image_last_updated
            assert changed is not None
            assert initial is not None
            assert changed >= initial

            # No payload change since the last render → timestamp is kept
            entity._cached_payload = mock_coordinator.data["wifi"]["site1"]["wifi1"][
                "qr_code"
            ]
            entity._handle_coordinator_update()
            assert entity._attr_image_last_updated == changed
