"""Test fixtures for port forward and traffic rule responses.

Sources:
- Port forward keys are taken from a live Network 11 probe (2026-10-09),
  exactly 14 keys.
- Traffic rule keys mirror aiounifi v96 TRAFFIC_RULES[0] (Home Assistant core unifi
  dependency); not observed on a live console (0 records on Network 11, 2026-10-09).
Values in records are synthetic unless noted.
"""

from __future__ import annotations

from typing import Any

LIVE_PORT_FORWARD_KEYS: frozenset[str] = frozenset(
    {
        "_id",
        "destination_ip",
        "destination_ips",
        "dst_port",
        "enabled",
        "fwd",
        "fwd_port",
        "log",
        "name",
        "pfwd_interface",
        "proto",
        "site_id",
        "src",
        "src_limiting_enabled",
    }
)

AIOUNIFI_TRAFFIC_RULE_KEYS: frozenset[str] = frozenset(
    {
        "_id",
        "action",
        "app_category_ids",
        "app_ids",
        "bandwidth_limit",
        "description",
        "domains",
        "enabled",
        "ip_addresses",
        "ip_ranges",
        "matching_target",
        "network_ids",
        "regions",
        "schedule",
        "target_devices",
    }
)


def port_forward_record(**overrides: Any) -> dict[str, Any]:
    """Return a synthetic port forward record with the 14 live keys."""
    record: dict[str, Any] = {
        "_id": "pf-plex",
        "name": "Plex",
        "enabled": True,
        "proto": "tcp_udp",
        "dst_port": "32400",
        "fwd_port": "32400",
        "pfwd_interface": "wan",
        "log": False,
        "src_limiting_enabled": False,
        "site_id": "classic-site-id",
        "destination_ips": [],
        "fwd": "192.168.1.50",
        "src": "198.51.100.0/24",
        "destination_ip": "203.0.113.7",
    }
    record.update(overrides)
    return record


def traffic_rule_record(**overrides: Any) -> dict[str, Any]:
    """Return a synthetic traffic rule record with the aiounifi v96 keys."""
    record: dict[str, Any] = {
        "_id": "tr-bedtime",
        "action": "BLOCK",
        "app_category_ids": [],
        "app_ids": [],
        "bandwidth_limit": {
            "download_limit_kbps": 10000,
            "enabled": False,
            "upload_limit_kbps": 5000,
        },
        "description": "Bedtime",
        "domains": ["blocked.example"],
        "enabled": True,
        "ip_addresses": [],
        "ip_ranges": [
            {
                "ip_start": "192.168.1.100",
                "ip_stop": "192.168.1.110",
                "ip_version": "v4",
            }
        ],
        "matching_target": "INTERNET",
        "network_ids": [],
        "regions": [],
        "schedule": {
            "date_end": "",
            "date_start": "",
            "mode": "ALWAYS",
            "repeat_on_days": [],
            "time_all_day": True,
            "time_range_end": "",
            "time_range_start": "",
        },
        "target_devices": [
            {
                "client_mac": "aa:bb:cc:dd:ee:01",
                "type": "CLIENT",
            }
        ],
    }
    record.update(overrides)
    return record
