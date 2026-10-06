# Copyright (c) 2026 Ruaan Deysel
"""Tests for Carrier Fabric diagnostics."""

from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights import CarrierFabricData
from custom_components.unifi_insights.const import (
    CONF_CARRIER_ORG_ID,
    CONNECTION_TYPE_CARRIER_FABRIC,
    DOMAIN,
)
from custom_components.unifi_insights.diagnostics import (
    async_get_config_entry_diagnostics,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_carrier_fabric_diagnostics_redaction(hass):
    """Test Carrier Fabric diagnostics exports allowlisted fields and redacts PII."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="carrier_test_entry",
        unique_id="carrier_org_999",
        data={
            "connection_type": CONNECTION_TYPE_CARRIER_FABRIC,
            CONF_API_KEY: "secret_isp_key",
            CONF_CARRIER_ORG_ID: "org_999",
        },
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.last_update_success = True
    mock_coord.last_exception = None

    # Coordinator data with sensitive subscriber and plan information,
    # plus injected forbidden fields
    subscribers_data = {
        "sub-uuid-1": {
            "id": "sub-uuid-1",
            "orgId": "org_999",
            "planId": "plan-1",
            "name": "Alice RealName",
            "subscriberNumber": "SUB-12345",
            "state": "installed",
            "suspended": False,
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-02T00:00:00Z",
            "activatedAt": "2026-01-01T12:00:00Z",
            "suspendedAt": None,
            # Injected forbidden fields
            "email": "alice@example.com",
            "notes": "VIP customer",
            "serviceAddress": "123 Main St",
            "metadata": {"router_sn": "XYZ789"},
            "suspendReason": "None",
            "hostId": "host-abc-123",
        }
    }

    service_plans_data = {
        "plan-1": {
            "id": "plan-1",
            "orgId": "org_999",
            "name": "Fiber 500",
            "status": "active",
            "downloadMbps": 500,
            "uploadMbps": 500,
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-02T00:00:00Z",
            "archivedAt": None,
            "extraInternalField": "omit_this",
            # Injected forbidden fields
            "notes": "Confidential plan notes",
            "metadata": {"discount_tier": 2},
        }
    }

    summary_data = {
        "total_subscribers": 1,
        "suspended_subscribers": 0,
        "provisioned_subscribers": 0,
        "installed_subscribers": 1,
        "unassigned_subscribers": 0,
        "pending_assignment_subscribers": 0,
        "active_service_plans": 1,
    }

    mock_coord.data = {
        "org_id": "org_999",
        "summary": summary_data,
        "service_plans": service_plans_data,
        "subscribers": subscribers_data,
    }

    entry.runtime_data = CarrierFabricData(
        client=MagicMock(),
        coordinator=mock_coord,
    )

    diag = await async_get_config_entry_diagnostics(hass, entry)

    # 1. API key redacted in entry
    assert diag["entry"]["data"][CONF_API_KEY] == "**REDACTED**"

    # 2. Coordinator status
    assert diag["coordinator"]["last_update_success"] is True
    assert diag["coordinator"]["last_exception_type"] is None

    # 3. Top-level summary
    assert diag["summary"] == summary_data

    # 4. Coordinator data structure
    data = diag["data"]
    assert data["org_id"] == "org_999"
    assert data["summary"] == summary_data

    # 5. Service plans: allowlist kept, everything else absent
    plan = data["service_plans"]["plan-1"]
    assert plan["id"] == "plan-1"
    assert plan["name"] == "Fiber 500"
    assert plan["downloadMbps"] == 500
    assert "extraInternalField" not in plan
    assert "notes" not in plan
    assert "metadata" not in plan

    # 6. Subscribers: id/state/planId kept, name and number redacted, the
    # non-allowlisted fields are absent rather than redacted
    sub = data["subscribers"]["sub-uuid-1"]
    assert sub["id"] == "sub-uuid-1"
    assert sub["orgId"] == "org_999"
    assert sub["planId"] == "plan-1"
    assert sub["state"] == "installed"
    assert sub["suspended"] is False
    assert sub["createdAt"] == "2026-01-01T00:00:00Z"
    assert sub["name"] == "**REDACTED**"
    assert sub["subscriberNumber"] == "**REDACTED**"
    for dropped in (
        "email",
        "notes",
        "serviceAddress",
        "metadata",
        "suspendReason",
        "hostId",
    ):
        assert dropped not in sub


async def test_carrier_fabric_diagnostics_exception_reported(hass):
    """Test Carrier Fabric diagnostics captures last exception type."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="carrier_test_entry_2",
        unique_id="carrier_org_888",
        data={
            "connection_type": CONNECTION_TYPE_CARRIER_FABRIC,
            CONF_API_KEY: "secret_isp_key",
        },
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.last_update_success = False
    mock_coord.last_exception = TimeoutError("Connection timed out")
    mock_coord.data = {}

    entry.runtime_data = CarrierFabricData(
        client=MagicMock(),
        coordinator=mock_coord,
    )

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["coordinator"]["last_update_success"] is False
    assert diag["coordinator"]["last_exception_type"] == "TimeoutError"


async def test_carrier_fabric_diagnostics_drops_non_allowlisted_nested_data(hass):
    """A non-allowlisted nested object never reaches the export, whatever its keys."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="carrier_test_entry_nested",
        unique_id="carrier_org_nested",
        data={
            "connection_type": CONNECTION_TYPE_CARRIER_FABRIC,
            CONF_API_KEY: "secret_isp_key",
            CONF_CARRIER_ORG_ID: "org_nested",
        },
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.last_update_success = True
    mock_coord.last_exception = None
    mock_coord.data = {
        "org_id": "org_nested",
        "summary": {},
        "service_plans": {
            "plan-nested": {
                "id": "plan-nested",
                "name": "Fiber 100",
                "contacts": [{"phone": "+1 555 0100"}],
            }
        },
        "subscribers": {
            "sub-uuid-nested": {
                "id": "sub-uuid-nested",
                "orgId": "org_nested",
                "planId": "plan-nested",
                "name": "Bob Test",
                "subscriberNumber": "SUB-9",
                "state": "provisioned",
                "unrecognized_top_level_key": "should_be_dropped",
                # Keys no forbidden-field list would ever name
                "contacts": [{"phone": "+1 555 0101"}],
                "custom_details": {"safe_info": "public_val", "pager": "12345"},
            }
        },
    }
    entry.runtime_data = CarrierFabricData(
        client=MagicMock(),
        coordinator=mock_coord,
    )

    diag = await async_get_config_entry_diagnostics(hass, entry)
    sub = diag["data"]["subscribers"]["sub-uuid-nested"]

    # Allowlisted PII is redacted, other allowlisted fields are kept
    assert sub["name"] == "**REDACTED**"
    assert sub["subscriberNumber"] == "**REDACTED**"
    assert sub["id"] == "sub-uuid-nested"
    assert sub["state"] == "provisioned"

    # Anything outside the allowlist is absent, nested or not
    assert set(sub) == {"id", "orgId", "planId", "name", "subscriberNumber", "state"}
    assert "+1 555 0101" not in repr(diag)
    assert "+1 555 0100" not in repr(diag)
    assert "12345" not in repr(diag)
    assert diag["data"]["service_plans"]["plan-nested"] == {
        "id": "plan-nested",
        "name": "Fiber 100",
    }
