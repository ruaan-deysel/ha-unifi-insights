#!/usr/bin/env python3
"""
Non-destructive test script to explore unifi-official-api capabilities.

This script connects to your UniFi Network and Protect APIs and retrieves
information about all devices without making any changes.

Usage:
    python scripts/test_api.py
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any

# Add the library path
sys.path.insert(0, "/home/vscode/.local/lib/python3.13/site-packages")

from unifi_official_api import ConnectionType, LocalAuth
from unifi_official_api.network import UniFiNetworkClient
from unifi_official_api.protect import UniFiProtectClient


# Configuration - User's network
HOST = "https://192.168.10.1"
API_KEY = "gA-wN-8G3B0qmyM3X56WjOWWYWoQscai"
VERIFY_SSL = False


def model_to_dict(model: Any) -> dict:
    """Convert pydantic model to dictionary."""
    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        try:
            return model.model_dump(by_alias=True, exclude_none=False)
        except TypeError:
            return model.model_dump()
    if hasattr(model, "__dict__"):
        return {k: v for k, v in model.__dict__.items() if not k.startswith("_")}
    return {}


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def print_device(device: dict, indent: int = 2) -> None:
    """Print device info in a readable format."""
    prefix = " " * indent
    print(f"{prefix}ID: {device.get('id', 'N/A')}")
    print(f"{prefix}Name: {device.get('name', 'Unnamed')}")
    print(f"{prefix}Model: {device.get('model', 'Unknown')}")
    print(f"{prefix}State: {device.get('state', device.get('status', 'Unknown'))}")
    if mac := device.get("mac") or device.get("macAddress"):
        print(f"{prefix}MAC: {mac}")
    if ip := device.get("ip") or device.get("ipAddress"):
        print(f"{prefix}IP: {ip}")
    if fw := device.get("firmwareVersion") or device.get("firmware_version"):
        print(f"{prefix}Firmware: {fw}")


async def test_network_api(client: UniFiNetworkClient) -> dict:
    """Test Network API capabilities."""
    results = {}

    print_section("UNIFI NETWORK API")

    # Get sites
    print("\n📍 Sites:")
    try:
        sites = await client.sites.get_all()
        results["sites"] = []
        for site_model in sites:
            site = model_to_dict(site_model)
            results["sites"].append(site)
            print(f"  - {site.get('name', site.get('id', 'Unknown'))}")
            print(f"    ID: {site.get('id')}")
            print(f"    Description: {site.get('description', 'N/A')}")
    except Exception as e:
        print(f"  Error fetching sites: {e}")

    if not results.get("sites"):
        return results

    # Use first site
    site_id = results["sites"][0].get("id")
    print(f"\n  Using site: {site_id}")

    # Get devices
    print("\n🖥️  Network Devices:")
    try:
        devices = await client.devices.get_all(site_id)
        results["devices"] = []
        for device_model in devices:
            device = model_to_dict(device_model)
            results["devices"].append(device)
            print(f"\n  📦 {device.get('name', 'Unnamed Device')}")
            print_device(device, indent=4)

            # Check for interfaces/ports
            if interfaces := device.get("interfaces"):
                if ports := interfaces.get("ports"):
                    active_ports = [p for p in ports if p.get("state") == "UP"]
                    print(f"    Active Ports: {len(active_ports)}/{len(ports)}")

            # Check for features
            if features := device.get("features"):
                print(
                    f"    Features: {', '.join(features.keys()) if features else 'N/A'}"
                )
    except Exception as e:
        print(f"  Error fetching devices: {e}")

    # Get device statistics for first device
    if results.get("devices"):
        print("\n📊 Device Statistics (first device):")
        try:
            first_device_id = results["devices"][0].get("id")
            stats = await client.devices.get_statistics(
                site_id, device_id=first_device_id
            )
            stats_dict = model_to_dict(stats)
            results["sample_stats"] = stats_dict
            print(f"    CPU: {stats_dict.get('cpuUtilizationPct', 'N/A')}%")
            print(f"    Memory: {stats_dict.get('memoryUtilizationPct', 'N/A')}%")
            print(f"    Uptime: {stats_dict.get('uptimeSec', 'N/A')} seconds")
            if uplink := stats_dict.get("uplink"):
                print(f"    TX Rate: {uplink.get('txRateBps', 'N/A')} bps")
                print(f"    RX Rate: {uplink.get('rxRateBps', 'N/A')} bps")
        except Exception as e:
            print(f"    Error fetching stats: {e}")

    # Get clients
    print("\n👥 Clients:")
    try:
        clients = await client.clients.get_all(site_id)
        results["clients"] = []
        wired_count = 0
        wireless_count = 0
        for client_model in clients:
            c = model_to_dict(client_model)
            results["clients"].append(c)
            client_type = c.get("type", "unknown")
            if client_type.upper() == "WIRED":
                wired_count += 1
            elif client_type.upper() == "WIRELESS":
                wireless_count += 1
        print(f"  Total: {len(results['clients'])}")
        print(f"  Wired: {wired_count}")
        print(f"  Wireless: {wireless_count}")

        # Show first 5 clients
        print("\n  First 5 clients:")
        for c in results["clients"][:5]:
            name = c.get("name") or c.get("hostname") or c.get("mac", "Unknown")
            print(f"    - {name} ({c.get('type', 'unknown')})")
    except Exception as e:
        print(f"  Error fetching clients: {e}")

    # Check available methods on client
    print("\n🔧 Available Network Client Methods:")
    for attr in dir(client):
        if not attr.startswith("_") and not attr.startswith("__"):
            obj = getattr(client, attr, None)
            if obj and hasattr(obj, "__class__") and "api" in str(type(obj)).lower():
                print(f"  - {attr}")

    return results


async def test_protect_api(client: UniFiProtectClient) -> dict:
    """Test Protect API capabilities."""
    results = {}

    print_section("UNIFI PROTECT API")

    # Get NVR info
    print("\n🖥️  NVR:")
    try:
        nvr = await client.nvr.get()
        nvr_dict = model_to_dict(nvr)
        results["nvr"] = nvr_dict
        print(f"  Name: {nvr_dict.get('name', 'N/A')}")
        print(f"  ID: {nvr_dict.get('id', 'N/A')}")
        print(f"  Version: {nvr_dict.get('firmwareVersion', 'N/A')}")
        print(f"  Host: {nvr_dict.get('host', 'N/A')}")
        if storage := nvr_dict.get("storageInfo"):
            total_gb = storage.get("totalSpaceBytes", 0) / (1024**3)
            used_gb = storage.get("usedSpaceBytes", 0) / (1024**3)
            print(f"  Storage: {used_gb:.1f} GB / {total_gb:.1f} GB")
    except Exception as e:
        print(f"  Error fetching NVR: {e}")

    # Get cameras
    print("\n📷 Cameras:")
    try:
        cameras = await client.cameras.get_all()
        results["cameras"] = []
        for camera_model in cameras:
            camera = model_to_dict(camera_model)
            results["cameras"].append(camera)
            print(f"\n  📹 {camera.get('name', 'Unnamed Camera')}")
            print(f"    ID: {camera.get('id')}")
            print(f"    Model: {camera.get('type', 'Unknown')}")
            print(f"    State: {camera.get('state', 'Unknown')}")
            print(f"    MAC: {camera.get('mac', 'N/A')}")

            # Recording settings
            if rec := camera.get("recordingSettings"):
                print(f"    Recording Mode: {rec.get('mode', 'N/A')}")

            # Feature flags
            if features := camera.get("featureFlags"):
                smart_types = features.get("smartDetectTypes", [])
                if smart_types:
                    print(f"    Smart Detect: {', '.join(smart_types)}")
                has_speaker = features.get("hasSpeaker", False)
                has_mic = features.get("hasMic", False)
                print(f"    Audio: Speaker={has_speaker}, Mic={has_mic}")

            # Check if doorbell
            camera_type = camera.get("type", "").lower()
            if "doorbell" in camera_type:
                print(f"    Doorbell: Yes")
    except Exception as e:
        print(f"  Error fetching cameras: {e}")

    # Get lights
    print("\n💡 Lights:")
    try:
        lights = await client.lights.get_all()
        results["lights"] = []
        if lights:
            for light_model in lights:
                light = model_to_dict(light_model)
                results["lights"].append(light)
                print(f"\n  💡 {light.get('name', 'Unnamed Light')}")
                print_device(light, indent=4)
        else:
            print("  No lights found")
    except Exception as e:
        print(f"  Error fetching lights: {e}")

    # Get sensors
    print("\n🌡️  Sensors:")
    try:
        sensors = await client.sensors.get_all()
        results["sensors"] = []
        if sensors:
            for sensor_model in sensors:
                sensor = model_to_dict(sensor_model)
                results["sensors"].append(sensor)
                print(f"\n  🌡️  {sensor.get('name', 'Unnamed Sensor')}")
                print_device(sensor, indent=4)
                # Stats
                if stats := sensor.get("stats"):
                    if temp := stats.get("temperature"):
                        print(f"    Temperature: {temp.get('value')}°C")
                    if humidity := stats.get("humidity"):
                        print(f"    Humidity: {humidity.get('value')}%")
        else:
            print("  No sensors found")
    except Exception as e:
        print(f"  Error fetching sensors: {e}")

    # Get chimes
    print("\n🔔 Chimes:")
    try:
        chimes = await client.chimes.get_all()
        results["chimes"] = []
        if chimes:
            for chime_model in chimes:
                chime = model_to_dict(chime_model)
                results["chimes"].append(chime)
                print(f"\n  🔔 {chime.get('name', 'Unnamed Chime')}")
                print(f"    ID: {chime.get('id')}")
                print(f"    Model: {chime.get('type', 'Unknown')}")
                print(f"    State: {chime.get('state', 'Unknown')}")
                print(f"    Volume: {chime.get('volume', 'N/A')}")
                if ring_settings := chime.get("ringSettings"):
                    print(f"    Ring Settings: {len(ring_settings)} configured")
        else:
            print("  No chimes found")
    except Exception as e:
        print(f"  Error fetching chimes: {e}")

    # Get viewers
    print("\n📺 Viewers:")
    try:
        if hasattr(client, "viewers"):
            viewers = await client.viewers.get_all()
            results["viewers"] = []
            if viewers:
                for viewer_model in viewers:
                    viewer = model_to_dict(viewer_model)
                    results["viewers"].append(viewer)
                    print(f"\n  📺 {viewer.get('name', 'Unnamed Viewer')}")
                    print_device(viewer, indent=4)
            else:
                print("  No viewers found")
        else:
            print("  Viewers API not available")
    except Exception as e:
        print(f"  Error fetching viewers: {e}")

    # Get liveviews
    print("\n🖼️  Liveviews:")
    try:
        if hasattr(client, "liveviews"):
            liveviews = await client.liveviews.get_all()
            results["liveviews"] = []
            if liveviews:
                for lv_model in liveviews:
                    lv = model_to_dict(lv_model)
                    results["liveviews"].append(lv)
                    print(f"  - {lv.get('name', 'Unnamed')} (ID: {lv.get('id')})")
            else:
                print("  No liveviews found")
        else:
            print("  Liveviews API not available")
    except Exception as e:
        print(f"  Error fetching liveviews: {e}")

    # Check for WebSocket support
    print("\n🔌 WebSocket Support:")
    ws_methods = []
    for attr in dir(client):
        if (
            "websocket" in attr.lower()
            or "subscribe" in attr.lower()
            or "event" in attr.lower()
        ):
            ws_methods.append(attr)
    if ws_methods:
        print(f"  Found methods: {', '.join(ws_methods)}")
    else:
        print("  No obvious WebSocket methods found in client")

    # Check available methods
    print("\n🔧 Available Protect Client Attributes:")
    for attr in dir(client):
        if not attr.startswith("_"):
            obj = getattr(client, attr, None)
            if obj and not callable(obj):
                print(f"  - {attr}: {type(obj).__name__}")

    return results


async def main() -> None:
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  UniFi Official API Test Script")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    print(f"\nConnecting to: {HOST}")
    print("This script performs READ-ONLY operations.\n")

    # Create auth
    auth = LocalAuth(api_key=API_KEY, verify_ssl=VERIFY_SSL)

    all_results = {}

    # Test Network API
    async with UniFiNetworkClient(
        auth=auth,
        base_url=HOST,
        connection_type=ConnectionType.LOCAL,
        timeout=30,
    ) as network_client:
        all_results["network"] = await test_network_api(network_client)

    # Test Protect API
    async with UniFiProtectClient(
        auth=auth,
        base_url=HOST,
        connection_type=ConnectionType.LOCAL,
        timeout=30,
    ) as protect_client:
        all_results["protect"] = await test_protect_api(protect_client)

    # Summary
    print_section("SUMMARY")
    print(f"\n📊 Data Retrieved:")
    print(f"  Sites: {len(all_results.get('network', {}).get('sites', []))}")
    print(
        f"  Network Devices: {len(all_results.get('network', {}).get('devices', []))}"
    )
    print(f"  Clients: {len(all_results.get('network', {}).get('clients', []))}")
    print(f"  Cameras: {len(all_results.get('protect', {}).get('cameras', []))}")
    print(f"  Lights: {len(all_results.get('protect', {}).get('lights', []))}")
    print(f"  Sensors: {len(all_results.get('protect', {}).get('sensors', []))}")
    print(f"  Chimes: {len(all_results.get('protect', {}).get('chimes', []))}")
    print(f"  Liveviews: {len(all_results.get('protect', {}).get('liveviews', []))}")

    # Save full results to JSON file
    output_file = "/workspaces/ha-unifi-insights/api_test_results.json"
    with open(output_file, "w") as f:
        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump(all_results, f, indent=2, default=json_serializer)
    print(f"\n💾 Full results saved to: {output_file}")

    print("\n✅ API test completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
