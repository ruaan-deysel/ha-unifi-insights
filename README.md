# UniFi Insights Integration for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/releases)
[![GitHub Issues](https://img.shields.io/github/issues/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/issues)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/ruaan-deysel)](https://github.com/sponsors/ruaan-deysel)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/unifi-insights-integration)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unifi-insights)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ruaan-deysel/ha-unifi-insights)

A Home Assistant custom integration for monitoring and controlling your UniFi Network and UniFi Protect infrastructure using the official UniFi APIs.

## How this differs from the official integrations

This project overlaps with and complements Home Assistant's official integrations:

- [UniFi Network (official)](https://www.home-assistant.io/integrations/unifi/)
- [UniFi Protect (official)](https://www.home-assistant.io/integrations/unifiprotect/)

| Area | UniFi Insights (this project) | Official integrations |
|---|---|---|
| Packaging | Single integration covering both Network and Protect in one setup flow | Two separate core integrations (`unifi` and `unifiprotect`) |
| Authentication | API key — local and cloud (remote console) connection modes | UniFi Network: local credentials. UniFi Protect: local credentials + API key |
| Remote management | Supports UniFi cloud console discovery and selection | Primarily local controller connectivity |
| Service surface | Adds integration-specific services for Network and Protect actions (vouchers, PTZ, chime, light) | Uses Home Assistant core entities and actions per integration |
| Project lifecycle | Community custom component released via GitHub and HACS | Included in Home Assistant Core release cycle |

**Which to choose:**

- Use the official integrations if you prefer core-maintained components with the widest documented feature surface.
- Use UniFi Insights if you want a single integration with API-key-first setup and combined Network and Protect support in one place.
- Running both side-by-side can create overlapping entities. Review and disable duplicates to avoid automation conflicts.

## Features

### UniFi Network

- Device monitoring: CPU, memory, uptime, and throughput for all adopted devices
- Per-port sensors: PoE power, port speed, TX/RX traffic counters
- Client tracking: device tracker entities for wireless and wired clients
- WiFi control: enable and disable WiFi networks
- Firewall policy control: enable and disable user-defined firewall rules
- Client management: block and allow network clients
- Firmware update management
- Device and port actions: restart devices, power cycle PoE ports

### UniFi Protect

- Camera streaming: live view, snapshots, RTSPS streams
- Motion and smart detection: person, vehicle, animal, and package binary sensors
- Doorbell ring detection
- Camera controls: microphone, privacy mode, status light, high FPS mode
- Protect light control: brightness and mode (always on, motion, off)
- PTZ cameras: move to preset position and run patrol via services
- Chime control: volume, ringtone selection, and repeat settings
- Protect sensor readings: temperature, humidity, light level, battery
- NVR storage monitoring (when available)
- Motion, ring, and smart detection events

## Requirements

- Home Assistant 2026.6.0 or newer
- UniFi Network Application 8.0 or newer
- UniFi Protect 3.0 or newer (required only for Protect features)

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-unifi-insights&category=integration)

1. Open HACS in Home Assistant.
2. Click **Integrations**.
3. Click the three-dot menu in the top right and select **Custom repositories**.
4. Add `https://github.com/ruaan-deysel/ha-unifi-insights` as a custom repository with the category set to **Integration**.
5. Search for "UniFi Insights" and install it.
6. Restart Home Assistant.

### Manual installation

1. Download the latest release from the [Releases page](https://github.com/ruaan-deysel/ha-unifi-insights/releases).
2. Copy the `custom_components/unifi_insights` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

### Getting an API key

1. Go to [UniFi Site Manager](https://unifi.ui.com).
2. Navigate to **Integrations**.
3. Click **Create API Key**, give it a name (for example "Home Assistant"), and copy the generated key.
4. The API key is shown on screen for you to **Copy** for the next step.

### Adding the integration

1. In Home Assistant, go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration** and search for "UniFi Insights".
3. Choose your connection type:
   - **Local** — direct connection to your UniFi console on the local network.
   - **Remote** — connect via UniFi Cloud. Enter your API key and then select the console from the list of discovered devices.
4. For a local connection, enter the host URL (for example `https://192.168.1.1`) and your API key.
5. Click **Submit**.

### Options

After setup, open the integration's options flow (**Settings** → **Devices & Services** → **UniFi Insights** → **Configure**) to adjust these settings:

| Option | Default | Description |
|---|---|---|
| Track WiFi Clients | Off | Creates device tracker entities for connected wireless clients. May add a large number of entities on busy networks. |
| Track Wired Clients | Off | Creates device tracker entities for connected wired clients. |
| Enable Client Control | On | Creates allow/block switch and reconnect button entities for each connected client. Disable this if you only need read-only monitoring — it prevents orphaned unavailable entities from accumulating when clients leave the network. |

## Entities

### Sensors

| Entity | Description |
|---|---|
| CPU Usage | Device CPU utilization (%) |
| Memory Usage | Device memory utilization (%) |
| Uptime | Device uptime |
| TX Rate | Uplink transmit rate (Mbit/s) |
| RX Rate | Uplink receive rate (Mbit/s) |
| Firmware Version | Installed firmware version |
| Wired Clients | Count of wired clients (switches) |
| Wireless Clients | Count of wireless clients (access points) |
| Total Clients | Total client count (site-level) |
| Port PoE Power | PoE power consumption per switch port (W) |
| Port Speed | Link speed per port (Mbps) |
| Port TX / RX | Traffic counters per port (bytes) |
| Temperature | Protect sensor temperature (°C) |
| Humidity | Protect sensor humidity (%) |
| Light Level | Protect sensor ambient light (lux) |
| Battery | Protect sensor battery level (%) |
| Storage Used / Total / Available | NVR storage metrics (GB, when available) |

### Binary sensors

| Entity | Description |
|---|---|
| Device Status | Network device online/offline state |
| WAN Status | Gateway WAN connectivity |
| Motion Detection | Camera or sensor motion activity |
| Person Detection | AI person detection |
| Vehicle Detection | AI vehicle detection |
| Animal Detection | AI animal detection |
| Package Detection | AI package detection |
| Doorbell Ring | Doorbell ring activity |
| Door / Window | Protect sensor open/close state |
| Tamper | Protect sensor tamper detection |
| Leak | Protect sensor water leak detection |
| Recording | Camera actively recording |

### Switches

| Entity | Description |
|---|---|
| WiFi Network | Enable or disable a WiFi broadcast |
| Firewall Rule | Enable or disable a user-defined firewall policy |
| Client Allow | Block or allow a connected network client |
| Camera Microphone | Enable or disable the camera microphone |
| Camera Privacy Mode | Enable or disable privacy mode |
| Camera Status Light | Enable or disable the status LED |
| Camera High FPS | Enable or disable high frame rate mode |

### Other entities

| Platform | Description |
|---|---|
| Button | Restart device, reconnect client, play chime, PTZ patrol start/stop |
| Camera | Live view, snapshots, RTSPS streaming |
| Device Tracker | Client presence detection |
| Event | Motion, doorbell ring, and smart detection events |
| Image | WiFi QR codes for each broadcast network |
| Light | Protect floodlight brightness control |
| Number | Microphone volume, chime volume, light brightness level |
| Select | Recording mode, HDR mode, video mode, ringtone, PTZ preset, live view |
| Update | Firmware update management |

## Services

### Core

```yaml
# Force an immediate data refresh
service: unifi_insights.refresh_data

# Restart a network device
service: unifi_insights.restart_device
data:
  site_id: "your-site-id"
  device_id: "device-id"
```

### Camera

```yaml
# Set recording mode
service: unifi_insights.set_recording_mode
data:
  camera_id: "camera-id"
  mode: "motion"  # always, motion, smart, never

# Set HDR mode
service: unifi_insights.set_hdr_mode
data:
  camera_id: "camera-id"
  mode: "auto"  # auto, on, off

# Move PTZ camera to a preset position
service: unifi_insights.ptz_move
data:
  camera_id: "camera-id"
  preset: 0  # 0–15

# Start or stop PTZ patrol
service: unifi_insights.ptz_patrol
data:
  camera_id: "camera-id"
  action: "start"  # start, stop
  slot: 0  # 0–15
```

### Light

```yaml
# Set Protect light mode
service: unifi_insights.set_light_mode
data:
  light_id: "light-id"
  mode: "motion"  # always, motion, off

# Set Protect light brightness
service: unifi_insights.set_light_level
data:
  light_id: "light-id"
  level: 50  # 0–100
```

### Chime

```yaml
# Play a ringtone on a chime
service: unifi_insights.play_chime_ringtone
data:
  chime_id: "chime-id"
  ringtone_id: "default"  # default, mechanical, digital, christmas, traditional

# Set chime volume
service: unifi_insights.set_chime_volume
data:
  chime_id: "chime-id"
  volume: 50  # 0–100
```

### Guest network and hotspot

```yaml
# Authorize a guest client
service: unifi_insights.authorize_guest
data:
  site_id: "your-site-id"
  client_id: "client-id"
  duration_minutes: 480

# Generate a hotspot voucher
service: unifi_insights.generate_voucher
data:
  site_id: "your-site-id"
  count: 1
  duration_minutes: 480
```

## Troubleshooting

### Enable debug logging

Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.unifi_insights: debug
```

### Common problems

| Problem | Solution |
|---|---|
| Cannot connect | Verify the host URL is reachable from Home Assistant. For self-signed certificates, disable SSL verification in the integration options. |
| Authentication failed | Confirm the API key is valid and was not revoked in the UniFi Site Manager. |
| No Protect entities | UniFi Protect must be running on the same console. Verify your API key has access to it. |
| Entities missing | Confirm the devices are adopted and online in the UniFi controller. |
| Storage sensors unavailable | The public Protect API does not expose NVR storage data on all firmware versions. |
| Many orphaned client entities | Disable the **Enable Client Control** option in the integration's settings. |

### Diagnostics

To download a sanitized diagnostic report for troubleshooting:

1. Go to **Settings** → **Devices & Services**.
2. Select **UniFi Insights**.
3. Click the three-dot menu and choose **Download diagnostics**.

## Contributing

Contributions are welcome. Please open an issue before submitting significant changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with or endorsed by Ubiquiti Inc. Use at your own risk.
