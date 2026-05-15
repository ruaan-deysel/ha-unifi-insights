"""Tests for vendored UniFi API client model parsing."""

from custom_components.unifi_insights.api.network.models.client import Client


def test_client_model_accepts_vpn_type() -> None:
    """Client model should parse VPN client types returned by UniFi."""
    client = Client.model_validate({"id": "client-vpn", "type": "VPN"})

    assert client.type == "VPN"


def test_client_model_accepts_teleport_type() -> None:
    """Client model should parse TELEPORT client types returned by UniFi."""
    client = Client.model_validate({"id": "client-teleport", "type": "TELEPORT"})

    assert client.type == "TELEPORT"


def test_client_model_accepts_lowercase_teleport_type() -> None:
    """Client model should parse lowercase TELEPORT values case-insensitively."""
    client = Client.model_validate({"id": "client-teleport-lower", "type": "teleport"})

    assert client.type == "TELEPORT"
