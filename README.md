# UniFi Insights Integration for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![CI](https://github.com/ruaan-deysel/ha-unifi-insights/actions/workflows/ci.yml/badge.svg)](https://github.com/ruaan-deysel/ha-unifi-insights/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights/branch/main/graph/badge.svg)](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/releases)
[![GitHub Issues](https://img.shields.io/github/issues/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/issues)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/ruaan-deysel)](https://github.com/sponsors/ruaan-deysel)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/unifi-insights-integration)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unifi-insights)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ruaan-deysel/ha-unifi-insights)

A comprehensive Home Assistant custom integration for monitoring and controlling your UniFi Network and UniFi Protect infrastructure using the official UniFi APIs.

## Features

### UniFi Network

- **Device Monitoring**: CPU, memory, uptime, and throughput sensors for all network devices
- **Port Sensors**: PoE power consumption, port speed, TX/RX bytes for switch ports
- **Client Tracking**: Device tracker for wireless and wired clients
- **WiFi Control**: Enable/disable WiFi networks
- **Client Management**: Block/allow network clients
- **Port Control**: Enable/disable switch ports, PoE control
- **Firmware Updates**: Update entities for device firmware management
- **Device Actions**: Restart devices, power cycle ports

### UniFi Protect

- **Camera Support**: Live streaming, snapshots, RTSPS streams
- **Motion Detection**: Binary sensors for motion and smart detection (person, vehicle, animal, package)
- **Doorbell Support**: Ring detection for doorbell cameras
- **Camera Controls**: Microphone, privacy mode, status light, high FPS mode switches
- **Light Control**: Brightness and mode control for Protect lights
- **PTZ Cameras**: Move to preset and patrol control via services
- **Chime Control**: Volume, ringtone, and repeat settings
- **Sensor Support**: Temperature, humidity, light, battery sensors for Protect sensors
- **NVR Monitoring**: Storage usage sensors (when available)
- **Events**: Motion, ring, and smart detection events

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-unifi-insights&category=integration)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots in the top right and select "Custom repositories"
4. Add `https://github.com/ruaan-deysel/ha-unifi-insights` as a custom repository (Category: Integration)
5. Click "Add"
6. Search for "UniFi Insights" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Copy the `custom_components/unifi_insights` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

1. A UniFi Network controller (UDM, UDM Pro, UDM SE, Cloud Key, or self-hosted)
2. UniFi Protect (for camera/sensor features) - optional
3. An API key from the UniFi Site Manager

### Getting an API Key

1. Go to [UniFi Site Manager](https://unifi.ui.com)
2. Navigate to **Control Plane** → **Admins & Users**
3. Select your Admin account
4. Click **Create API Key**
5. Provide a name (e.g., "Home Assistant") and copy the key
6. Click **Done** to save

### Setting up the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "UniFi Insights"
4. Choose your connection type:
   - **Local**: Direct connection to your UniFi console
   - **Remote**: Connection via UniFi Cloud
5. Enter your credentials:
   - **Local**: Host URL (e.g., `https://192.168.1.1`) and API Key
   - **Remote**: Console ID and API Key
6. Click **Submit**

### Options

After setup, you can configure tracking options:

- **Track WiFi Clients**: Enable device tracker for wireless clients
- **Track Wired Clients**: Enable device tracker for wired clients

## Entities

### Sensors

| Entity                       | Description                            |
| ---------------------------- | -------------------------------------- |
| CPU Usage                    | Device CPU utilization percentage      |
| Memory Usage                 | Device memory utilization percentage   |
| Uptime                       | Device uptime in human-readable format |
| TX Rate                      | Uplink transmit rate (Mbit/s)          |
| RX Rate                      | Uplink receive rate (Mbit/s)           |
| Firmware Version             | Current firmware version               |
| Wired Clients                | Count of wired clients (switches only) |
| Wireless Clients             | Count of wireless clients (APs only)   |
| Port PoE Power               | PoE power consumption per port (W)     |
| Port Speed                   | Link speed per port (Mbps)             |
| Port TX/RX Bytes             | Traffic counters per port              |
| Temperature                  | Protect sensor temperature (°C)        |
| Humidity                     | Protect sensor humidity (%)            |
| Light                        | Protect sensor light level (lux)       |
| Battery                      | Protect sensor battery level (%)       |
| Storage Used/Total/Available | NVR storage metrics (GB)               |

### Binary Sensors

| Entity            | Description                         |
| ----------------- | ----------------------------------- |
| Device Status     | Network device connectivity         |
| WAN Status        | Gateway WAN connectivity            |
| Motion Detection  | Camera/sensor motion detection      |
| Person Detection  | AI person detection                 |
| Vehicle Detection | AI vehicle detection                |
| Animal Detection  | AI animal detection                 |
| Package Detection | AI package detection                |
| Doorbell Ring     | Doorbell ring detection             |
| Door/Window       | Protect sensor open/close status    |
| Tamper            | Protect sensor tamper detection     |
| Leak              | Protect sensor water leak detection |

### Switches

| Entity              | Description                         |
| ------------------- | ----------------------------------- |
| Port Enable         | Enable/disable switch ports         |
| Port PoE            | Enable/disable PoE on ports         |
| WiFi Network        | Enable/disable WiFi networks        |
| Client Allow        | Block/allow network clients         |
| Camera Microphone   | Enable/disable camera microphone    |
| Camera Privacy Mode | Enable/disable privacy mode         |
| Camera Status Light | Enable/disable status LED           |
| Camera High FPS     | Enable/disable high frame rate mode |

### Other Entities

| Platform       | Description                                      |
| -------------- | ------------------------------------------------ |
| Button         | Restart device, power cycle port                 |
| Camera         | Live view, snapshots, RTSPS streaming            |
| Device Tracker | Client presence detection                        |
| Event          | Motion, ring, and smart detection events         |
| Light          | Protect light brightness control                 |
| Number         | Mic volume, chime volume, light level            |
| Select         | Recording mode, HDR mode, video mode, light mode |
| Update         | Firmware update management                       |

## Services

### Core Services

```yaml
# Refresh all data
service: unifi_insights.refresh_data

# Restart a device
service: unifi_insights.restart_device
data:
  site_id: "your-site-id"
  device_id: "device-mac-address"
```

### Camera Services

```yaml
# Set recording mode
service: unifi_insights.set_recording_mode
data:
  camera_id: "camera-id"
  mode: "always"  # always, motion, never

# Set HDR mode
service: unifi_insights.set_hdr_mode
data:
  camera_id: "camera-id"
  mode: "auto"  # auto, on, off

# PTZ move to preset
service: unifi_insights.ptz_move
data:
  camera_id: "camera-id"
  preset: 0  # 0-15

# PTZ patrol
service: unifi_insights.ptz_patrol
data:
  camera_id: "camera-id"
  action: "start"  # start, stop
  slot: 0  # 0-15
```

### Light Services

```yaml
# Set light mode
service: unifi_insights.set_light_mode
data:
  light_id: "light-id"
  mode: "motion"  # always, motion, off

# Set light level
service: unifi_insights.set_light_level
data:
  light_id: "light-id"
  level: 50  # 0-100
```

### Chime Services

```yaml
# Play chime
service: unifi_insights.play_chime_ringtone
data:
  chime_id: "chime-id"
  ringtone_id: "default"

# Set chime volume
service: unifi_insights.set_chime_volume
data:
  chime_id: "chime-id"
  volume: 50  # 0-100
```

### Guest/Voucher Services

```yaml
# Authorize guest
service: unifi_insights.authorize_guest
data:
  site_id: "your-site-id"
  client_id: "client-mac"
  duration_minutes: 480

# Generate voucher
service: unifi_insights.generate_voucher
data:
  site_id: "your-site-id"
  count: 1
  duration_minutes: 480
```

## Troubleshooting

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.unifi_insights: debug
```

### Common Issues

| Issue                       | Solution                                                |
| --------------------------- | ------------------------------------------------------- |
| Cannot Connect              | Verify host URL is accessible, check SSL settings       |
| Authentication Failed       | Verify API key is valid and has appropriate permissions |
| No Protect Data             | Ensure you have UniFi Protect on your console           |
| Missing Entities            | Check that devices are adopted in UniFi controller      |
| Storage Sensors Unavailable | The public API doesn't expose NVR storage data          |

### Diagnostics

This integration supports Home Assistant's built-in diagnostics feature. Go to **Settings** → **Devices & Services** → **UniFi Insights** → **3 dots menu** → **Download diagnostics** to get a sanitized report for troubleshooting.

## Requirements

- Home Assistant 2024.1.0 or newer
- Python 3.11 or newer
- UniFi Network Application 8.0 or newer (recommended)
- UniFi Protect 3.0 or newer (for Protect features)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Run linter: `./scripts/lint`
6. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially affiliated with or endorsed by Ubiquiti Inc. Use at your own risk.

## Acknowledgments

- [unifi-official-api](https://github.com/uilibs/unifi-official-api) - The official UniFi API library
- [Home Assistant](https://www.home-assistant.io/) - The open source home automation platform

## Support

- 🐛 [Report a Bug](https://github.com/ruaan-deysel/ha-unifi-insights/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/ruaan-deysel/ha-unifi-insights/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/ruaan-deysel/ha-unifi-insights/discussions)
