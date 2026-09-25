"""
Data transformation functions for vendored UniFi API responses.

This module provides transformation functions to convert vendored API
response formats to the internal data structures expected by entities,
maintaining backward compatibility.
"""

from __future__ import annotations

import ipaddress
from typing import Any


def map_device_status(lib_status: str | None) -> str:
    """
    Map library device status to internal format.

    Args:
        lib_status: Status from library ("online", "offline", "unknown")

    Returns:
        Internal status format ("connected", "disconnected", "unknown")

    """
    if not lib_status:
        return "unknown"

    status_map = {
        "online": "connected",
        "offline": "disconnected",
        "unknown": "unknown",
    }
    return status_map.get(lib_status.lower(), lib_status)


def transform_network_device(lib_device: dict) -> dict:
    """
    Transform library network device response to internal format.

    Args:
        lib_device: Device data from the vendored UniFi API package

    Returns:
        Transformed device data in internal format

    """
    return {
        "id": lib_device.get("id"),
        "mac": lib_device.get("mac"),
        "model": lib_device.get("model"),
        "name": lib_device.get("name"),
        "state": map_device_status(lib_device.get("status")),
        "adopted": lib_device.get("adopted"),
        "version": lib_device.get("firmware_version"),
        "uptime": lib_device.get("uptime_seconds"),
        "cpu_usage": lib_device.get("cpu_percent"),
        "memory_usage": lib_device.get("memory_percent"),
        "tx_bytes": lib_device.get("tx_bytes"),
        "rx_bytes": lib_device.get("rx_bytes"),
        "site_id": lib_device.get("site"),
    }


def transform_protect_camera(lib_camera: dict) -> dict:
    """
    Transform library Protect camera response to internal format.

    Args:
        lib_camera: Camera data from the vendored UniFi API package

    Returns:
        Transformed camera data in internal format

    """
    return {
        "id": lib_camera.get("id"),
        "name": lib_camera.get("name"),
        "state": lib_camera.get("status", "").upper()
        if lib_camera.get("status")
        else "UNKNOWN",
        "is_recording": lib_camera.get("recording"),
        "motion_detected": lib_camera.get("motion"),
        "type": lib_camera.get("model"),
        "hdr_mode": lib_camera.get("hdr", "").upper()
        if lib_camera.get("hdr")
        else "AUTO",
        "video_mode": lib_camera.get("video_mode", "").upper()
        if lib_camera.get("video_mode")
        else "DEFAULT",
        "is_dark": lib_camera.get("is_dark", False),
        # snapshot_url and rtsps_url generated on-demand via client methods
    }


def transform_protect_light(lib_light: dict) -> dict:
    """
    Transform library Protect light response to internal format.

    Args:
        lib_light: Light data from the vendored UniFi API package

    Returns:
        Transformed light data in internal format

    """
    return {
        "id": lib_light.get("id"),
        "name": lib_light.get("name"),
        "is_on": lib_light.get("on"),
        "brightness": lib_light.get("brightness"),
        "mode": lib_light.get("light_mode", "").upper()
        if lib_light.get("light_mode")
        else "AUTO",
        "is_dark": lib_light.get("dark", False),
    }


def transform_protect_sensor(lib_sensor: dict) -> dict:
    """
    Transform library Protect sensor response to internal format.

    Args:
        lib_sensor: Sensor data from the vendored UniFi API package

    Returns:
        Transformed sensor data in internal format

    """
    return {
        "id": lib_sensor.get("id"),
        "name": lib_sensor.get("name"),
        "temperature": lib_sensor.get("temperature"),
        "humidity": lib_sensor.get("humidity"),
        "light_level": lib_sensor.get("light"),
        "battery_percentage": lib_sensor.get("battery"),
    }


def transform_protect_chime(lib_chime: dict) -> dict:
    """
    Transform library Protect chime response to internal format.

    Args:
        lib_chime: Chime data from the vendored UniFi API package

    Returns:
        Transformed chime data in internal format

    """
    return {
        "id": lib_chime.get("id"),
        "name": lib_chime.get("name"),
        "volume": lib_chime.get("volume"),
        "repeat_times": lib_chime.get("repeat"),
        "ringtone_id": lib_chime.get("ringtone"),
    }


def _is_unspecified_address(value: str) -> bool:
    """Return True for 0.0.0.0 / ::, the placeholder a down link reports."""
    try:
        return ipaddress.ip_address(value).is_unspecified
    except ValueError:
        return False


def normalize_legacy_wans(legacy_device: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return per-WAN connection state from a legacy gateway record.

    The gateway's ``wan1..wanN`` blocks describe the physical ports (type
    "ethernet", name "eth8"), not the internet connection, so they cannot
    tell a dropped PPPoE session from a connected one. The controller's own
    per-WAN verdict lives in ``last_wan_status`` ({"WAN": "online"}) and
    ``last_wan_interfaces`` ({"WAN": {"ip": ..., "alive": true}}), keyed by
    the same WAN names the UniFi UI shows. A WAN that is configured but not
    in use does not appear in either.
    """
    statuses = legacy_device.get("last_wan_status")
    interfaces = legacy_device.get("last_wan_interfaces")
    statuses = statuses if isinstance(statuses, dict) else {}
    interfaces = interfaces if isinstance(interfaces, dict) else {}

    wans: list[dict[str, Any]] = []
    for name in dict.fromkeys((*statuses, *interfaces)):
        if not isinstance(name, str) or not name:
            continue
        status = statuses.get(name)
        status = status if isinstance(status, str) else None
        interface = interfaces.get(name)
        interface = interface if isinstance(interface, dict) else {}
        alive = interface.get("alive")
        alive = alive if isinstance(alive, bool) else None
        ip = interface.get("ip")
        has_ip = isinstance(ip, str) and bool(ip) and not _is_unspecified_address(ip)
        wans.append(
            {
                "key": name.lower(),
                "name": name,
                "status": status,
                "alive": alive,
                "ip": ip if has_ip else None,
                # The controller's status is authoritative; "alive" (its
                # reachability probe) only decides when no status is given.
                "connected": (
                    status.lower() == "online" if status is not None else alive is True
                ),
            }
        )
    return wans


def _to_mapping(record: Any) -> dict[str, Any]:
    """Convert a Pydantic model or mapping to a plain dictionary."""
    if record is None:
        return {}
    if isinstance(record, dict):
        return dict(record)
    if hasattr(record, "model_dump"):
        dumped = record.model_dump(by_alias=False, exclude_none=False)
        return dict(dumped) if isinstance(dumped, dict) else {}
    if hasattr(record, "__dict__"):
        return {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
    return {}


_MAC_HEX_LEN = 12


def _normalize_innerspace_mac(mac: Any) -> str | None:
    """Normalize a MAC address to lowercase colon-separated form (aa:bb:cc:dd:ee:ff)."""
    if not isinstance(mac, str):
        return None
    cleaned = mac.strip().lower().replace("-", "").replace(":", "").replace(".", "")
    if len(cleaned) != _MAC_HEX_LEN or any(
        ch not in "0123456789abcdef" for ch in cleaned
    ):
        return None
    return ":".join(cleaned[i : i + 2] for i in range(0, _MAC_HEX_LEN, 2))


def _valid_number(value: Any) -> float | int | None:
    """Return value if it is an int or float (excluding bool), else None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def transform_innerspace_project(project_data: Any) -> dict[str, Any] | None:
    """
    Normalize a UniFi InnerSpace project response.

    Preserves project identity and plan metadata (including siteId), while
    excluding raw shapes, image downloads, and image URLs.
    """
    raw = _to_mapping(project_data)
    if not raw:
        return None

    if "data" in raw and isinstance(raw["data"], dict):
        raw = _to_mapping(raw["data"])

    project_obj = _to_mapping(raw.get("project")) if "project" in raw else raw
    project_id = project_obj.get("id") if isinstance(project_obj, dict) else None
    project_title = (
        project_obj.get("title") or project_obj.get("name")
        if isinstance(project_obj, dict)
        else None
    )
    created_at = (
        project_obj.get("created_at") or project_obj.get("createdAt")
        if isinstance(project_obj, dict)
        else None
    )
    updated_at = (
        project_obj.get("updated_at") or project_obj.get("updatedAt")
        if isinstance(project_obj, dict)
        else None
    )

    raw_plans = raw.get("plans")
    plans: list[dict[str, Any]] = []
    if isinstance(raw_plans, list):
        for plan_item in raw_plans:
            plan_dict = _to_mapping(plan_item)
            plan_id = plan_dict.get("id")
            if not isinstance(plan_id, str) or not plan_id:
                continue
            plans.append(
                {
                    "id": plan_id,
                    "title": plan_dict.get("title") or plan_dict.get("name"),
                    "type": plan_dict.get("type"),
                    "project_id": (
                        plan_dict.get("project_id")
                        or plan_dict.get("projectId")
                        or project_id
                    ),
                    "site_id": plan_dict.get("site_id") or plan_dict.get("siteId"),
                    "ordering": _valid_number(plan_dict.get("ordering")),
                    "attenuation": _valid_number(plan_dict.get("attenuation")),
                    "created_at": (
                        plan_dict.get("created_at") or plan_dict.get("createdAt")
                    ),
                    "updated_at": (
                        plan_dict.get("updated_at") or plan_dict.get("updatedAt")
                    ),
                }
            )

    raw_products = raw.get("products")
    products: list[dict[str, Any]] = []
    if isinstance(raw_products, list):
        for prod_item in raw_products:
            prod_dict = _to_mapping(prod_item)
            prod_id = prod_dict.get("id")
            if not isinstance(prod_id, str) or not prod_id:
                continue
            products.append(
                {
                    "id": prod_id,
                    "sku": prod_dict.get("sku"),
                }
            )

    if not project_id and not plans and not products:
        return None

    wall_types = raw.get("wall_types") or raw.get("wallTypes")
    attenuation_types = raw.get("attenuation_object_types") or raw.get(
        "attenuationObjectTypes"
    )

    return {
        "id": project_id,
        "title": project_title,
        "created_at": created_at,
        "updated_at": updated_at,
        "plans": plans,
        "products": products,
        "wall_types_count": len(wall_types) if isinstance(wall_types, list) else 0,
        "attenuation_object_types_count": (
            len(attenuation_types) if isinstance(attenuation_types, list) else 0
        ),
    }


def transform_innerspace_floor_plan(
    plan: Any,
    *,
    project_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Normalize a UniFi InnerSpace floor plan record.

    Preserves floor-plan identity, name, dimensions, scale, and site_id while
    explicitly omitting image_url and asset URLs.
    """
    raw = _to_mapping(plan)
    proj = project_plan or {}
    plan_id = raw.get("id") or proj.get("id")
    name = raw.get("name") or raw.get("title") or proj.get("title") or proj.get("name")
    floor_number = _valid_number(
        raw.get("floor_number")
        if raw.get("floor_number") is not None
        else raw.get("floorNumber")
    )
    if floor_number is None:
        floor_number = _valid_number(proj.get("ordering"))

    site_id = (
        raw.get("site_id")
        or raw.get("siteId")
        or proj.get("site_id")
        or proj.get("siteId")
    )
    return {
        "id": plan_id,
        "name": name,
        "floor_number": floor_number,
        "ppm": _valid_number(raw.get("ppm")),
        "width": _valid_number(raw.get("width")),
        "height": _valid_number(raw.get("height")),
        "origin_x": _valid_number(
            raw.get("origin_x")
            if raw.get("origin_x") is not None
            else raw.get("originX")
        ),
        "origin_y": _valid_number(
            raw.get("origin_y")
            if raw.get("origin_y") is not None
            else raw.get("originY")
        ),
        "site_id": site_id if isinstance(site_id, str) and site_id else None,
        "type": raw.get("type") or proj.get("type"),
        "project_id": (
            raw.get("project_id") or raw.get("projectId") or proj.get("project_id")
        ),
    }


def transform_innerspace_device(
    device: Any,
    *,
    device_kind: str | None = None,
    placed: bool = False,
    floor_plans: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Normalize a UniFi InnerSpace device or inventory record.

    For unplaced inventory, `device_type` is only set when explicitly provided
    by the source payload (`type`) and is NEVER inferred from `model`.
    `placement_state` is reported as `"placed"`, `"unplaced"`, or `"unknown"`
    strictly when supported by the source data.
    """
    raw = _to_mapping(device)
    record_id = raw.get("id")
    raw_mac = raw.get("mac")
    norm_mac = _normalize_innerspace_mac(raw_mac)
    status = raw.get("status")
    status_str = status.lower() if isinstance(status, str) and status else None

    if device_kind in ("access_point", "switch"):
        device_type: str | None = device_kind
    else:
        explicit_type = raw.get("type")
        device_type = (
            explicit_type
            if isinstance(explicit_type, str) and explicit_type.strip()
            else None
        )

    floor_plan_id = raw.get("floor_plan_id") or raw.get("floorPlanId")
    floor_plan_id = (
        floor_plan_id
        if isinstance(floor_plan_id, str) and floor_plan_id.strip()
        else None
    )
    x_coord = _valid_number(raw.get("x"))
    y_coord = _valid_number(raw.get("y"))

    floor_plan_name: str | None = None
    site_id = raw.get("site_id") or raw.get("siteId")
    if floor_plan_id and floor_plans and floor_plan_id in floor_plans:
        plan_info = floor_plans[floor_plan_id]
        floor_plan_name = plan_info.get("name")
        if not site_id:
            site_id = plan_info.get("site_id")

    if placed:
        has_valid_plan = floor_plan_id is not None and (
            not floor_plans or floor_plan_id in floor_plans
        )
        if has_valid_plan and x_coord is not None and y_coord is not None:
            placement_state = "placed"
        else:
            placement_state = "unknown"
    # Unplaced inventory record from /v1/inventory
    elif (
        isinstance(record_id, str)
        and record_id
        and floor_plan_id is None
        and x_coord is None
        and y_coord is None
    ):
        placement_state = "unplaced"
    else:
        placement_state = "unknown"

    return {
        "id": record_id,
        "name": raw.get("name"),
        "model": raw.get("model"),
        "device_type": device_type,
        "mac": norm_mac or (raw_mac if isinstance(raw_mac, str) and raw_mac else None),
        "normalized_mac": norm_mac,
        "serial": raw.get("serial"),
        "status": status_str,
        "placed": placement_state == "placed",
        "placement_state": placement_state,
        "floor_plan_id": floor_plan_id,
        "floor_plan_name": floor_plan_name,
        "site_id": site_id if isinstance(site_id, str) and site_id else None,
        "x": x_coord,
        "y": y_coord,
        "height": _valid_number(raw.get("height")),
        "azimuth": _valid_number(raw.get("azimuth")),
        "mount": raw.get("mount") if isinstance(raw.get("mount"), str) else None,
        "correlation": None,
    }


def correlate_innerspace_devices(
    placed_or_snapshot: dict[str, Any],
    inventory_devices: dict[str, dict[str, Any]] | None = None,
    *,
    network_devices_by_site: dict[str, Any] | None = None,
    network_devices: dict[str, Any] | None = None,
    protect_data: dict[str, Any] | None = None,
    protect_devices: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any] | None]:
    """
    Correlate InnerSpace records with Network and Protect devices by normalized MAC.

    Rules:
    - Correlate only when a normalized MAC identifies exactly one device unambiguously.
    - If a floor-plan (or record) `site_id` is available and matches a polled site in
      `network_devices_by_site`, narrow Network candidate matching to that site.
    - Store correlations as metadata (`record["correlation"]` and `matched_*` keys)
      without altering existing Network or Protect unique IDs, device identifiers,
      or areas.
    """
    raw_net = (
        network_devices_by_site
        if network_devices_by_site is not None
        else network_devices
    )
    raw_prot = protect_data if protect_data is not None else protect_devices
    net_by_site = raw_net if isinstance(raw_net, dict) else {}
    prot = raw_prot if isinstance(raw_prot, dict) else {}

    # Pre-index Network devices by site_id and normalized MAC
    net_index_by_site: dict[str, dict[str, list[dict[str, Any]]]] = {}
    net_index_all: dict[str, list[dict[str, Any]]] = {}
    for site_id, site_devices in net_by_site.items():
        if not isinstance(site_devices, dict):
            continue
        site_map: dict[str, list[dict[str, Any]]] = {}
        for dev_id, dev_data in site_devices.items():
            if not isinstance(dev_data, dict):
                continue
            raw_mac = (
                dev_data.get("macAddress")
                or dev_data.get("mac_address")
                or dev_data.get("mac")
            )
            norm = _normalize_innerspace_mac(raw_mac)
            if not norm:
                continue
            candidate = {
                "application": "network",
                "device_id": str(dev_data.get("id") or dev_id),
                "site_id": str(site_id),
                "device_type": dev_data.get("type") or dev_data.get("model"),
                "mac": norm,
            }
            site_map.setdefault(norm, []).append(candidate)
            net_index_all.setdefault(norm, []).append(candidate)
        net_index_by_site[str(site_id)] = site_map

    # Pre-index Protect devices by normalized MAC
    prot_index_all: dict[str, list[dict[str, Any]]] = {}
    protect_collections = (
        ("cameras", "camera"),
        ("lights", "light"),
        ("sensors", "sensor"),
        ("nvrs", "nvr"),
        ("viewers", "viewer"),
        ("chimes", "chime"),
        ("doorlocks", "doorlock"),
        ("viewports", "viewport"),
    )
    for collection_key, dtype in protect_collections:
        items = prot.get(collection_key)
        if not isinstance(items, dict):
            continue
        for dev_id, dev_data in items.items():
            if not isinstance(dev_data, dict):
                continue
            raw_mac = (
                dev_data.get("mac")
                or dev_data.get("macAddress")
                or dev_data.get("mac_address")
            )
            norm = _normalize_innerspace_mac(raw_mac)
            if not norm:
                continue
            prot_index_all.setdefault(norm, []).append(
                {
                    "application": "protect",
                    "device_id": str(dev_data.get("id") or dev_id),
                    "site_id": None,
                    "device_type": dtype,
                    "mac": norm,
                }
            )

    collections_to_update: list[dict[str, Any]] = []
    if inventory_devices is None and (
        "access_points" in placed_or_snapshot
        or "switches" in placed_or_snapshot
        or "inventory" in placed_or_snapshot
        or "devices" in placed_or_snapshot
    ):
        for section_name in ("access_points", "switches", "inventory", "devices"):
            sec = placed_or_snapshot.get(section_name)
            if isinstance(sec, dict):
                collections_to_update.append(sec)
    else:
        collections_to_update.append(placed_or_snapshot)
        if isinstance(inventory_devices, dict):
            collections_to_update.append(inventory_devices)

    correlations: dict[str, dict[str, Any] | None] = {}
    for collection in collections_to_update:
        for record_id, record in collection.items():
            if not isinstance(record, dict):
                continue
            norm_mac = record.get("normalized_mac") or _normalize_innerspace_mac(
                record.get("mac")
            )
            if not norm_mac:
                record["correlation"] = None
                record["matched_domain"] = None
                record["matched_site_id"] = None
                record["matched_device_id"] = None
                record["matched_protect_type"] = None
                correlations[record_id] = None
                continue

            record_site_id = record.get("site_id")
            if (
                isinstance(record_site_id, str)
                and record_site_id
                and record_site_id in net_index_by_site
            ):
                net_candidates = net_index_by_site[record_site_id].get(norm_mac, [])
            else:
                net_candidates = net_index_all.get(norm_mac, [])

            prot_candidates = prot_index_all.get(norm_mac, [])
            all_candidates = [*net_candidates, *prot_candidates]

            if len(all_candidates) == 1:
                match = dict(all_candidates[0])
                record["correlation"] = match
                record["matched_domain"] = match["application"]
                record["matched_site_id"] = match["site_id"]
                record["matched_device_id"] = match["device_id"]
                record["matched_protect_type"] = (
                    match["device_type"] if match["application"] == "protect" else None
                )
                correlations[record_id] = match
            else:
                record["correlation"] = None
                record["matched_domain"] = None
                record["matched_site_id"] = None
                record["matched_device_id"] = None
                record["matched_protect_type"] = None
                correlations[record_id] = None

    return correlations


def normalize_innerspace_snapshot(
    *,
    project: Any = None,
    floor_plans: list[Any] | None = None,
    access_points: list[Any] | None = None,
    switches: list[Any] | None = None,
    inventory: list[Any] | None = None,
    network_devices_by_site: dict[str, Any] | None = None,
    network_devices: dict[str, Any] | None = None,
    protect_data: dict[str, Any] | None = None,
    protect_devices: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the normalized InnerSpace coordinator snapshot.

    Keeps unplaced inventory distinct from placed access points and switches,
    excludes raw shapes and image URLs, and computes unambiguous MAC correlations.
    """
    normalized_project = transform_innerspace_project(project)
    project_plans_by_id: dict[str, dict[str, Any]] = {}
    if normalized_project and isinstance(normalized_project.get("plans"), list):
        for p_plan in normalized_project["plans"]:
            if isinstance(p_plan, dict) and p_plan.get("id"):
                project_plans_by_id[str(p_plan["id"])] = p_plan

    floor_plans_dict: dict[str, dict[str, Any]] = {}
    for fp_item in floor_plans or []:
        fp_raw = _to_mapping(fp_item)
        fp_id = fp_raw.get("id")
        if not isinstance(fp_id, str) or not fp_id:
            continue
        floor_plans_dict[fp_id] = transform_innerspace_floor_plan(
            fp_raw,
            project_plan=project_plans_by_id.get(fp_id),
        )

    # Also include any project plans not already listed in /v1/floor_plans
    for fp_id, proj_plan in project_plans_by_id.items():
        if fp_id not in floor_plans_dict:
            floor_plans_dict[fp_id] = transform_innerspace_floor_plan(
                proj_plan,
                project_plan=proj_plan,
            )

    access_points_dict: dict[str, dict[str, Any]] = {}
    placed_devices_dict: dict[str, dict[str, Any]] = {}
    for ap_item in access_points or []:
        ap_norm = transform_innerspace_device(
            ap_item,
            device_kind="access_point",
            placed=True,
            floor_plans=floor_plans_dict,
        )
        ap_id = ap_norm.get("id")
        if isinstance(ap_id, str) and ap_id:
            access_points_dict[ap_id] = ap_norm
            placed_devices_dict[ap_id] = ap_norm

    switches_dict: dict[str, dict[str, Any]] = {}
    for sw_item in switches or []:
        sw_norm = transform_innerspace_device(
            sw_item,
            device_kind="switch",
            placed=True,
            floor_plans=floor_plans_dict,
        )
        sw_id = sw_norm.get("id")
        if isinstance(sw_id, str) and sw_id:
            switches_dict[sw_id] = sw_norm
            placed_devices_dict[sw_id] = sw_norm

    inventory_dict: dict[str, dict[str, Any]] = {}
    for inv_item in inventory or []:
        inv_norm = transform_innerspace_device(
            inv_item,
            device_kind=None,
            placed=False,
            floor_plans=floor_plans_dict,
        )
        inv_id = inv_norm.get("id")
        if isinstance(inv_id, str) and inv_id and inv_id not in placed_devices_dict:
            inventory_dict[inv_id] = inv_norm

    correlations = correlate_innerspace_devices(
        placed_devices_dict,
        inventory_dict,
        network_devices_by_site=network_devices_by_site,
        network_devices=network_devices,
        protect_data=protect_data,
        protect_devices=protect_devices,
    )

    devices_dict: dict[str, dict[str, Any]] = {
        **inventory_dict,
        **placed_devices_dict,
    }

    return {
        "project": normalized_project,
        "floor_plans": floor_plans_dict,
        "access_points": access_points_dict,
        "switches": switches_dict,
        "placed_devices": placed_devices_dict,
        "inventory": inventory_dict,
        "devices": devices_dict,
        "correlations": correlations,
    }
