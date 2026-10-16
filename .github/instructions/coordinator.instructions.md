---
applyTo: "custom_components/unifi_insights/coordinator.py, custom_components/unifi_insights/coordinators/**/*.py"
---

# Coordinator Instructions

**Applies to:** Data coordinator implementation files

## Multi-Coordinator Architecture

This integration uses a multi-coordinator architecture under `custom_components/unifi_insights/coordinators/`:

- **Base Coordinator** (`coordinators/base.py`) — Abstract base with shared error handling, backoff, and availability logging
- **Config Coordinator** (`coordinators/config.py` & `coordinators/config_sections.py`) — Site, WiFi, firewall, ACL, traffic, NAT, QoS, DNS, VPN, and network configuration data (slow polling)
- **Device Coordinator** (`coordinators/device.py`) — Network device metrics, ports, PoE, SFP, and connected clients (30s default polling)
- **Protect Coordinator** (`coordinators/protect.py`) — Cameras, lights, sensors, NVRs, chimes, viewers, liveviews, and real-time WebSocket event stream
- **Access Coordinator** (`coordinators/access.py`) — UniFi Access doors, locks, readers, hubs, and access events
- **InnerSpace Coordinator** (`coordinators/innerspace.py`) — UniFi InnerSpace floor plans, zones, and spatial occupancy/environment data
- **Site Manager Coordinator** (`coordinators/site_manager.py`) — UniFi Site Manager cloud multi-site health and ISP metrics
- **Mobility Coordinator** (`coordinators/mobility.py`) — UniFi Mobility cellular/5G devices and SIM metrics
- **Carrier Fabric Coordinator** (`coordinators/carrier_fabric.py`) — UniFi Carrier Fabric OLTs, ONUs, subscribers, and alarms
- **Internet Activity Coordinator** (`coordinators/internet_activity.py`) — Per-site WAN/internet activity and latency telemetry
- **Rule Audit & Export Coordinators** (`coordinators/rule_audit.py`, `coordinators/rule_export.py`) — Network rule change auditing and snapshot export
- **Voucher State Helper** (`coordinators/voucher_state.py`) — Guest hotspot voucher tracking
- **Facade Coordinator** (`coordinators/facade.py`) — Unified view combining sub-coordinators for entity platforms

## Runtime Data (`entry.runtime_data`)

- Store coordinators and clients on `entry.runtime_data` (`UnifiInsightsData` or `CarrierFabricData` in `__init__.py`), never in `hass.data[DOMAIN]` (Bronze `runtime-data`).

## Error Handling & Availability Logging

- Raise `ConfigEntryAuthFailed` (with `translation_domain=DOMAIN`, `translation_key=...`) for authentication/authorization failures to trigger the reauth flow.
- Raise `UpdateFailed` for transient network/controller errors so `DataUpdateCoordinator` retries automatically.
- **Log once when unavailable (Silver `log-when-unavailable`):** Log a single `INFO`/`WARNING` message when the controller transitions to unreachable and once when it recovers; never log errors on every failed poll cycle.

```python
async def _async_update_data(self) -> dict[str, Any]:
    try:
        data = await self.api_client.get_data()
    except UniFiAuthenticationError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
        ) from err
    except (UniFiConnectionError, UniFiTimeoutError, UniFiError) as err:
        raise UpdateFailed(f"Error fetching data: {err}") from err
    return data
```

## First Refresh

Always use `async_config_entry_first_refresh()` during `async_setup_entry`:

```python
await coordinator.async_config_entry_first_refresh()
```

## Dynamic & Stale Device Cleanup (HA 2026.8–2026.10+)

- **Dynamic devices (`dynamic-devices`):** Automatically register new devices discovered on subsequent coordinator refreshes.
- **Stale devices (`stale-devices`):** Remove stale devices from the Home Assistant device registry when they disappear from the controller.
- **HA 2026.8–2026.10 Device Registry rules:**
  - Use `dr.async_entries_for_config_entry(dev_reg, entry.entry_id)` or `dev_reg.async_get_device_by_identifier(entry.entry_id, (DOMAIN, device_id))`.
  - Use `device.config_entry_id` (single config entry per device) — never access deprecated `device.config_entries`, `device.config_entries_subentries`, or `device.primary_config_entry`.
  - Never call dict methods (`.get()`, `.values()`, `.keys()`) on `dev_reg.devices` or `dev_reg.child_devices`.

## Best Practices

- Never expose API clients directly to entity `@property` getters — always read from `coordinator.data`.
- Normalize API responses via `data_transforms.py` (`get_field`, `first_not_none`) before storing in coordinator dictionaries.
- Clean up WebSocket listeners and background tasks in `async_unload_entry` (Bronze `config-entry-unloading`).
