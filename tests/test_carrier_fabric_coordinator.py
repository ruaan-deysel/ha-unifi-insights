# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Carrier Fabric coordinator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights.api import (
    UniFiConnectionError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.const import (
    CONF_CARRIER_ORG_ID,
    CONNECTION_TYPE_CARRIER_FABRIC,
    DOMAIN,
)
from custom_components.unifi_insights.coordinators.carrier_fabric import (
    UnifiCarrierFabricCoordinator,
)


@pytest.fixture
def mock_carrier_entry(hass):
    """Create a mock Carrier Fabric config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="carrier_org_123",
        data={
            "connection_type": CONNECTION_TYPE_CARRIER_FABRIC,
            "api_key": "isp_secret_test_key",
            CONF_CARRIER_ORG_ID: "org_123",
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_carrier_client():
    """Create a mock UniFiCarrierFabricClient."""
    client = MagicMock()
    client.service_plans = MagicMock()
    client.service_plans.get_all = AsyncMock(return_value=[])
    client.subscribers = MagicMock()
    client.subscribers.get_all = AsyncMock(return_value=[])
    client.subscribers.suspend = AsyncMock(return_value={})
    client.subscribers.resume = AsyncMock(return_value={})
    return client


async def test_coordinator_data_ingestion_and_allowlist(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test data ingestion with allowlisting, deduplication, and summary aggregation."""
    # Raw plans from API containing extra/sensitive fields
    raw_plans = [
        {
            "id": "plan_gold",
            "orgId": "org_123",
            "name": "Gigabit Gold",
            "status": "active",
            "downloadMbps": 1000,
            "uploadMbps": 1000,
            "archivedAt": None,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
            # Extra fields that MUST NOT leak into coordinator data:
            "internalBillingCode": "BILL_999",
            "adminNotes": "Confidential margin details",
        },
        # Duplicate plan
        {
            "id": "plan_gold",
            "orgId": "org_123",
            "name": "Gigabit Gold Duplicate",
            "status": "active",
            "downloadMbps": 1000,
            "uploadMbps": 1000,
        },
        # Archived plan
        {
            "id": "plan_archived",
            "orgId": "org_123",
            "name": "Legacy 100M",
            "status": "archived",
            "downloadMbps": 100,
            "uploadMbps": 20,
        },
        # Invalid item without id - must be skipped
        {"name": "No ID Plan"},
        "not a dict plan",
    ]

    # Raw subscribers containing sensitive fields
    raw_subscribers = [
        {
            "id": "sub_1",
            "orgId": "org_123",
            "name": "Alice Smith",
            "subscriberNumber": "SUB-001",
            "planId": "plan_gold",
            "state": "installed",
            "suspended": False,
            "suspendedAt": None,
            "activatedAt": "2024-01-05T00:00:00Z",
            "createdAt": "2024-01-05T00:00:00Z",
            "updatedAt": "2024-01-05T00:00:00Z",
            # Sensitive fields that MUST NEVER leak:
            "email": "alice@example.com",
            "phone": "+15551234567",
            "serviceAddress": "123 Main St, Anytown",
            "notes": "Gate code is 1234",
            "hostId": "host_xyz",
            "metadata": {"creditCardLast4": "4242"},
            "suspendReason": None,
        },
        {
            "id": "sub_2",
            "orgId": "org_123",
            "name": "Bob Jones",
            "subscriberNumber": "SUB-002",
            "planId": "plan_gold",
            "state": "suspended",
            "suspended": True,
            "suspendedAt": "2024-02-01T00:00:00Z",
            "activatedAt": "2024-01-06T00:00:00Z",
            "createdAt": "2024-01-06T00:00:00Z",
            "updatedAt": "2024-02-01T00:00:00Z",
            "email": "bob@example.com",
            "suspendReason": "Non-payment",
        },
        {
            "id": "sub_3",
            "orgId": "org_123",
            "name": "Charlie Brown",
            "subscriberNumber": "SUB-003",
            "planId": None,  # unassigned
            "state": "pending_assignment",
            "suspended": False,
            "suspendedAt": None,
            "activatedAt": None,
            "createdAt": "2024-02-01T00:00:00Z",
            "updatedAt": "2024-02-01T00:00:00Z",
            "email": "charlie@example.com",
        },
        # Duplicate subscriber sub_1
        {
            "id": "sub_1",
            "name": "Alice Duplicate",
        },
        # Invalid item without id
        {"name": "No ID Subscriber"},
        12345,
    ]

    mock_carrier_client.service_plans.get_all.return_value = raw_plans
    mock_carrier_client.subscribers.get_all.return_value = raw_subscribers

    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    data = await coord._async_update_data()

    assert data["org_id"] == "org_123"

    # Verify plans allowlisting & deduplication
    plans = data["service_plans"]
    assert len(plans) == 2
    assert "plan_gold" in plans
    assert "plan_archived" in plans
    assert "internalBillingCode" not in plans["plan_gold"]
    assert "adminNotes" not in plans["plan_gold"]

    # Verify subscribers allowlisting & deduplication
    subs = data["subscribers"]
    assert len(subs) == 3
    assert "sub_1" in subs
    assert "sub_2" in subs
    assert "sub_3" in subs

    sub_1 = subs["sub_1"]
    assert sub_1["id"] == "sub_1"
    assert sub_1["name"] == "Alice Smith"
    # Ensure sensitive fields are purged
    for forbidden in (
        "email",
        "phone",
        "serviceAddress",
        "notes",
        "hostId",
        "metadata",
        "suspendReason",
    ):
        assert forbidden not in sub_1

    # Verify summary aggregation
    summary = data["summary"]
    assert summary["total_subscribers"] == 3
    assert summary["suspended_subscribers"] == 1
    assert summary["subscribers_by_state"] == {
        "installed": 1,
        "suspended": 1,
        "pending_assignment": 1,
        "provisioned": 0,
        "unknown": 0,
    }
    assert summary["active_service_plans"] == 1  # Only plan_gold is active
    assert summary["subscribers_by_plan"] == {
        "plan_gold": 2,
    }
    assert summary["unassigned_subscribers"] == 1


async def test_coordinator_refresh_auth_failed_401(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test 401 raises ConfigEntryAuthFailed."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiResponseError(
        status_code=401, message="Unauthorized"
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(
        ConfigEntryAuthFailed, match="Carrier Fabric authentication failed"
    ):
        await coord._async_update_data()


async def test_coordinator_refresh_auth_failed_403(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test 403 raises ConfigEntryAuthFailed naming insufficient_scope."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiResponseError(
        status_code=403,
        message="Forbidden",
        api_error_code="insufficient_scope",
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(ConfigEntryAuthFailed, match="insufficient_scope"):
        await coord._async_update_data()


async def test_coordinator_refresh_rate_limited_429(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test 429 raises UpdateFailed."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiResponseError(
        status_code=429, message="Too Many Requests"
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(UpdateFailed, match="Carrier Fabric API rate limited"):
        await coord._async_update_data()


async def test_coordinator_refresh_server_error_500(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test 500 raises UpdateFailed."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiResponseError(
        status_code=500, message="Internal Server Error"
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(UpdateFailed, match="Carrier Fabric API error"):
        await coord._async_update_data()


async def test_coordinator_refresh_connection_error(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test connection error raises UpdateFailed."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiConnectionError(
        "Connection refused"
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(UpdateFailed, match="Error connecting to Carrier Fabric API"):
        await coord._async_update_data()


async def test_coordinator_refresh_timeout_error(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test timeout error raises UpdateFailed."""
    mock_carrier_client.service_plans.get_all.side_effect = UniFiTimeoutError(
        "Request timed out"
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(UpdateFailed, match="Timeout connecting to Carrier Fabric API"):
        await coord._async_update_data()


async def test_coordinator_suspend_invalid_uuid(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test suspend validates UUID before any HTTP call."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(HomeAssistantError, match="Invalid subscriber ID format"):
        await coord.async_suspend_subscriber("invalid-uuid-format")
    mock_carrier_client.subscribers.suspend.assert_not_called()


async def test_coordinator_suspend_success(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test successful suspend calls client and refreshes coordinator."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    coord.async_request_refresh = AsyncMock()

    valid_id = "11111111-2222-3333-4444-555555555555"
    await coord.async_suspend_subscriber(valid_id)

    mock_carrier_client.subscribers.suspend.assert_called_once_with(
        valid_id, reason=None
    )
    coord.async_request_refresh.assert_called_once()


async def test_coordinator_suspend_retry_on_write_conflict(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test suspend retries exactly once on write_conflict_retryable."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    coord.async_request_refresh = AsyncMock()

    mock_carrier_client.subscribers.suspend.side_effect = [
        UniFiResponseError(
            status_code=409,
            message="Conflict",
            api_error_code="write_conflict_retryable",
        ),
        {"status": "ok"},
    ]

    valid_id = "11111111-2222-3333-4444-555555555555"
    await coord.async_suspend_subscriber(valid_id)

    assert mock_carrier_client.subscribers.suspend.call_count == 2
    coord.async_request_refresh.assert_called_once()


async def test_coordinator_suspend_failure_raises_ha_error(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test suspend failure raises HomeAssistantError."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    mock_carrier_client.subscribers.suspend.side_effect = UniFiResponseError(
        status_code=400, message="Bad Request"
    )

    valid_id = "11111111-2222-3333-4444-555555555555"
    with pytest.raises(HomeAssistantError, match="Failed to suspend subscriber"):
        await coord.async_suspend_subscriber(valid_id)


async def test_coordinator_resume_invalid_uuid(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test resume validates UUID before any HTTP call."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    with pytest.raises(HomeAssistantError, match="Invalid subscriber ID format"):
        await coord.async_resume_subscriber("invalid-uuid-format")
    mock_carrier_client.subscribers.resume.assert_not_called()


async def test_coordinator_resume_success(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test successful resume calls client and refreshes coordinator."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    coord.async_request_refresh = AsyncMock()

    valid_id = "11111111-2222-3333-4444-555555555555"
    await coord.async_resume_subscriber(valid_id)

    mock_carrier_client.subscribers.resume.assert_called_once_with(valid_id)
    coord.async_request_refresh.assert_called_once()


async def test_coordinator_resume_retry_exhausted(
    hass, mock_carrier_entry, mock_carrier_client
):
    """Test resume retries once and raises HomeAssistantError if retry also fails."""
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, mock_carrier_entry)
    conflict = UniFiResponseError(
        status_code=409,
        message="Conflict",
        api_error_code="write_conflict_retryable",
    )
    mock_carrier_client.subscribers.resume.side_effect = [conflict, conflict]

    valid_id = "11111111-2222-3333-4444-555555555555"
    with pytest.raises(HomeAssistantError, match="Failed to resume subscriber"):
        await coord.async_resume_subscriber(valid_id)

    assert mock_carrier_client.subscribers.resume.call_count == 2


async def test_coordinator_refresh_unexpected_exception(hass, mock_carrier_client):
    """Test unexpected exception raises UpdateFailed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CARRIER_ORG_ID: "org_1"},
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, entry)
    mock_carrier_client.service_plans.get_all.side_effect = RuntimeError("Disk full")

    with pytest.raises(
        UpdateFailed, match="Unexpected error communicating with Carrier Fabric API"
    ):
        await coord._async_update_data()


async def test_coordinator_org_id_fallback_discovery(hass, mock_carrier_client):
    """Test org_id fallback discovery when entry data is None."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CARRIER_ORG_ID: None},
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, entry)

    # 1. From service plan
    mock_carrier_client.service_plans.get_all.return_value = [
        {"id": "plan_1", "orgId": "org_from_plan"}
    ]
    mock_carrier_client.subscribers.get_all.return_value = []
    data = await coord._async_update_data()
    assert data["org_id"] == "org_from_plan"

    # 2. From subscriber when plans have no orgId
    mock_carrier_client.service_plans.get_all.return_value = [{"id": "plan_2"}]
    mock_carrier_client.subscribers.get_all.return_value = [
        {"id": "sub_1", "orgId": "org_from_sub", "state": "unknown_status"}
    ]
    data = await coord._async_update_data()
    assert data["org_id"] == "org_from_sub"
    assert data["summary"]["subscribers_by_state"]["unknown"] == 1


async def test_coordinator_validate_subscriber_uuid_non_string(
    hass, mock_carrier_client
):
    """Test non-string subscriber ID raises HomeAssistantError."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CARRIER_ORG_ID: "org_1"},
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, entry)

    with pytest.raises(
        HomeAssistantError, match=r"Invalid subscriber ID \(UUID string required\)"
    ):
        await coord.async_suspend_subscriber(12345)  # type: ignore[arg-type]


async def test_coordinator_resume_retry_on_write_conflict(hass, mock_carrier_client):
    """Test resume retries once on write_conflict_retryable and succeeds."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CARRIER_ORG_ID: "org_1"},
    )
    coord = UnifiCarrierFabricCoordinator(hass, mock_carrier_client, entry)

    valid_id = "11111111-2222-3333-4444-555555555555"
    conflict_err = Exception("Write conflict")
    conflict_err.api_error_code = "write_conflict_retryable"

    mock_carrier_client.subscribers.resume.side_effect = [
        conflict_err,
        {"id": valid_id, "suspended": False},
    ]

    with patch.object(
        coord, "async_request_refresh", new_callable=AsyncMock
    ) as mock_refresh:
        await coord.async_resume_subscriber(valid_id)
        assert mock_carrier_client.subscribers.resume.call_count == 2
        mock_refresh.assert_awaited_once()
