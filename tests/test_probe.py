"""Tests for classifying Network/Protect probe results."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, ValidationError

from custom_components.unifi_insights.api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiNotFoundError,
    UniFiRateLimitError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.probe import (
    ProbeStatus,
    async_probe_innerspace,
    async_probe_network,
    async_probe_protect,
    async_probe_with_client,
    classify_error,
    is_transient_error,
)


def _validation_error() -> ValidationError:
    class _Model(BaseModel):
        value: int

    try:
        _Model.model_validate({"value": "not an int"})
    except ValidationError as err:
        return err
    raise AssertionError  # pragma: no cover


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (UniFiAuthenticationError("Unauthorized", status_code=401), "auth_failed"),
        (UniFiAuthenticationError("Forbidden", status_code=403), "auth_failed"),
        (UniFiConnectionError("Connection refused"), "unreachable"),
        (UniFiTimeoutError("Timed out"), "unreachable"),
        (UniFiRateLimitError("Slow down", status_code=429), "unreachable"),
        (UniFiResponseError("Bad gateway", status_code=502), "unreachable"),
        (UniFiResponseError("Server error", status_code=500), "unreachable"),
        (UniFiNotFoundError("Not found", status_code=404), "unsupported"),
        (UniFiResponseError("Bad request", status_code=400), "unsupported"),
        (UniFiResponseError("HTML page", status_code=200), "unsupported"),
        (UniFiResponseError("Redirect", status_code=302), "unsupported"),
        (ValueError("Unexpected"), "error"),
    ],
    ids=[
        "401",
        "403",
        "connection",
        "timeout",
        "429",
        "502",
        "500",
        "404",
        "400",
        "200-non-json",
        "302",
        "unexpected",
    ],
)
def test_classify_error(error: Exception, expected: str) -> None:
    """Each client error maps to one probe status."""
    assert classify_error(error) == ProbeStatus(expected)
    assert is_transient_error(error) is (expected == "unreachable")


async def test_probe_network_statuses() -> None:
    """Sites are available, an empty list is empty, errors are classified."""
    client = MagicMock()
    client.sites.get_all = AsyncMock(return_value=[MagicMock(id="default")])
    result = await async_probe_network(client)
    assert result.status is ProbeStatus.AVAILABLE
    assert len(result.sites) == 1

    client.sites.get_all = AsyncMock(return_value=[])
    assert (await async_probe_network(client)).status is ProbeStatus.EMPTY

    error = UniFiResponseError("Server error", status_code=503)
    client.sites.get_all = AsyncMock(side_effect=error)
    result = await async_probe_network(client)
    assert result.status is ProbeStatus.UNREACHABLE
    assert result.error is error


@pytest.mark.parametrize(
    ("cameras", "nvr", "expected"),
    [
        ([MagicMock()], None, "available"),
        ([], MagicMock(id="nvr1"), "available"),
        ([], None, "empty"),
        ([], ValueError("NVR not found"), "empty"),
        ([], "validation", "error"),
        ([], UniFiResponseError("Server error", status_code=503), "unreachable"),
        ([], UniFiAuthenticationError("Unauthorized", status_code=401), "auth_failed"),
        (UniFiTimeoutError("Timed out"), None, "unreachable"),
        (UniFiNotFoundError("Not found", status_code=404), None, "unsupported"),
    ],
    ids=[
        "cameras",
        "camera-free-nvr",
        "no-nvr-record",
        "nvr-not-found",
        "nvr-parse-error",
        "nvr-5xx",
        "nvr-401",
        "cameras-timeout",
        "cameras-404",
    ],
)
async def test_probe_protect_statuses(
    cameras: object, nvr: object, expected: str
) -> None:
    """A camera-free NVR is usable; the NVR probe's own errors are classified."""
    client = MagicMock()
    if isinstance(cameras, Exception):
        client.cameras.get_all = AsyncMock(side_effect=cameras)
    else:
        client.cameras.get_all = AsyncMock(return_value=cameras)
    if nvr == "validation":
        client.nvr.get = AsyncMock(side_effect=_validation_error())
    elif isinstance(nvr, Exception):
        client.nvr.get = AsyncMock(side_effect=nvr)
    else:
        client.nvr.get = AsyncMock(return_value=nvr)

    result = await async_probe_protect(client)

    assert result.status is ProbeStatus(expected)


async def test_probe_with_client_classifies_context_errors() -> None:
    """An error while opening the client is classified, not raised."""
    context = MagicMock()
    context.__aenter__ = AsyncMock(side_effect=UniFiConnectionError("Refused"))
    context.__aexit__ = AsyncMock(return_value=None)

    result = await async_probe_with_client(context, async_probe_network)

    assert result.status is ProbeStatus.UNREACHABLE


@pytest.mark.parametrize(
    ("project", "floor_plans", "inventory", "expected"),
    [
        (
            MagicMock(
                project=MagicMock(id="proj-1"),
                plans=[],
                products=[],
            ),
            [],
            [],
            "available",
        ),
        (
            MagicMock(project=None, plans=[], products=[]),
            [MagicMock(id="fp-1")],
            [],
            "available",
        ),
        (
            MagicMock(project=None, plans=[], products=[]),
            [],
            [MagicMock(id="inv-1")],
            "available",
        ),
        (
            MagicMock(project=None, plans=[], products=[]),
            [],
            [],
            "empty",
        ),
        (
            UniFiNotFoundError("Not found", status_code=404),
            [],
            [],
            "unsupported",
        ),
        (
            UniFiAuthenticationError("Unauthorized", status_code=401),
            [],
            [],
            "auth_failed",
        ),
        (
            UniFiTimeoutError("Timed out"),
            [],
            [],
            "unreachable",
        ),
        (
            MagicMock(project=None, plans=[], products=[]),
            UniFiResponseError("Bad gateway", status_code=502),
            [],
            "unreachable",
        ),
    ],
    ids=[
        "project-id",
        "floor-plans-fallback",
        "inventory-fallback",
        "all-empty",
        "404-unsupported",
        "401-auth-failed",
        "timeout-unreachable",
        "secondary-502-unreachable",
    ],
)
async def test_probe_innerspace_statuses(
    project: object,
    floor_plans: object,
    inventory: object,
    expected: str,
) -> None:
    """InnerSpace probe classifies available, empty, unsupported, and errors."""
    client = MagicMock()
    if isinstance(project, Exception):
        client.get_project = AsyncMock(side_effect=project)
    else:
        client.get_project = AsyncMock(return_value=project)
    if isinstance(floor_plans, Exception):
        client.list_floor_plans = AsyncMock(side_effect=floor_plans)
    else:
        client.list_floor_plans = AsyncMock(return_value=floor_plans)
    client.list_access_points = AsyncMock(return_value=[])
    client.list_switches = AsyncMock(return_value=[])
    client.list_inventory = AsyncMock(return_value=inventory)

    result = await async_probe_innerspace(client)

    assert result.status is ProbeStatus(expected)
