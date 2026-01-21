"""Tests for UniFi Insights repairs."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.unifi_insights.repairs import (
    UnifiInsightsRepairFlow,
    async_create_fix_flow,
)


class TestUnifiInsightsRepairFlow:
    """Tests for UnifiInsightsRepairFlow."""

    def test_init(self) -> None:
        """Test repair flow initialization."""
        flow = UnifiInsightsRepairFlow("test_issue")
        assert flow.issue_id == "test_issue"

    @pytest.mark.asyncio
    async def test_async_step_init_deprecated_yaml(self) -> None:
        """Test init step routes to deprecated_yaml."""
        flow = UnifiInsightsRepairFlow("deprecated_yaml")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_init(None)

        flow.async_show_form.assert_called_once()
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_init_api_key_expired(self) -> None:
        """Test init step routes to api_key_expired."""
        flow = UnifiInsightsRepairFlow("api_key_expired")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_init(None)

        flow.async_show_form.assert_called_once()
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_init_device_offline(self) -> None:
        """Test init step routes to device_offline."""
        flow = UnifiInsightsRepairFlow("device_offline")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_init(None)

        flow.async_show_form.assert_called_once()
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_init_unknown_issue(self) -> None:
        """Test init step handles unknown issues."""
        flow = UnifiInsightsRepairFlow("unknown_issue_type")

        # Mock the async_abort method
        flow.async_abort = MagicMock(return_value={"type": "abort"})

        result = await flow.async_step_init(None)

        flow.async_abort.assert_called_once_with(reason="unknown_issue")
        assert result == {"type": "abort"}

    @pytest.mark.asyncio
    async def test_async_step_deprecated_yaml_show_form(self) -> None:
        """Test deprecated_yaml step shows form."""
        flow = UnifiInsightsRepairFlow("deprecated_yaml")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_deprecated_yaml(None)

        flow.async_show_form.assert_called_once_with(
            step_id="deprecated_yaml",
            description_placeholders={
                "integration": "UniFi Insights",
            },
        )
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_deprecated_yaml_user_input(self) -> None:
        """Test deprecated_yaml step handles user input."""
        flow = UnifiInsightsRepairFlow("deprecated_yaml")

        # Mock the async_create_entry method
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        result = await flow.async_step_deprecated_yaml({"acknowledged": "true"})

        flow.async_create_entry.assert_called_once_with(data={})
        assert result == {"type": "create_entry"}

    @pytest.mark.asyncio
    async def test_async_step_api_key_expired_show_form(self) -> None:
        """Test api_key_expired step shows form."""
        flow = UnifiInsightsRepairFlow("api_key_expired")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_api_key_expired(None)

        flow.async_show_form.assert_called_once_with(
            step_id="api_key_expired",
            description_placeholders={
                "integration": "UniFi Insights",
            },
        )
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_api_key_expired_user_input(self) -> None:
        """Test api_key_expired step handles user input."""
        flow = UnifiInsightsRepairFlow("api_key_expired")

        # Mock the async_abort method
        flow.async_abort = MagicMock(return_value={"type": "abort"})

        result = await flow.async_step_api_key_expired({"acknowledged": "true"})

        flow.async_abort.assert_called_once_with(reason="reconfigure_required")
        assert result == {"type": "abort"}

    @pytest.mark.asyncio
    async def test_async_step_device_offline_show_form(self) -> None:
        """Test device_offline step shows form."""
        flow = UnifiInsightsRepairFlow("device_offline")

        # Mock the async_show_form method
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        result = await flow.async_step_device_offline(None)

        flow.async_show_form.assert_called_once_with(
            step_id="device_offline",
            description_placeholders={
                "integration": "UniFi Insights",
            },
        )
        assert result == {"type": "form"}

    @pytest.mark.asyncio
    async def test_async_step_device_offline_user_input(self) -> None:
        """Test device_offline step handles user input."""
        flow = UnifiInsightsRepairFlow("device_offline")

        # Mock the async_create_entry method
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        result = await flow.async_step_device_offline({"acknowledged": "true"})

        flow.async_create_entry.assert_called_once_with(data={})
        assert result == {"type": "create_entry"}


class TestAsyncCreateFixFlow:
    """Tests for async_create_fix_flow function."""

    @pytest.mark.asyncio
    async def test_create_fix_flow_deprecated_yaml(self, hass) -> None:
        """Test creating fix flow for deprecated_yaml."""
        flow = await async_create_fix_flow(hass, "deprecated_yaml", None)

        assert isinstance(flow, UnifiInsightsRepairFlow)
        assert flow.issue_id == "deprecated_yaml"

    @pytest.mark.asyncio
    async def test_create_fix_flow_api_key_expired(self, hass) -> None:
        """Test creating fix flow for api_key_expired."""
        flow = await async_create_fix_flow(hass, "api_key_expired", {"key": "value"})

        assert isinstance(flow, UnifiInsightsRepairFlow)
        assert flow.issue_id == "api_key_expired"

    @pytest.mark.asyncio
    async def test_create_fix_flow_device_offline(self, hass) -> None:
        """Test creating fix flow for device_offline."""
        flow = await async_create_fix_flow(hass, "device_offline", None)

        assert isinstance(flow, UnifiInsightsRepairFlow)
        assert flow.issue_id == "device_offline"

    @pytest.mark.asyncio
    async def test_create_fix_flow_unknown_issue(self, hass) -> None:
        """Test creating fix flow for unknown issue."""
        flow = await async_create_fix_flow(hass, "some_other_issue", None)

        assert isinstance(flow, UnifiInsightsRepairFlow)
        assert flow.issue_id == "some_other_issue"
