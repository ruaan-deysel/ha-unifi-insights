# UniFi Insights Integration for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/releases)
[![GitHub Issues](https://img.shields.io/github/issues/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/issues)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/ruaan-deysel)](https://github.com/sponsors/ruaan-deysel)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/unifi-insights-integration)
[![codecov](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights/graph/badge.svg?token=9WMPJAYFPE)](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unifi-insights)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ruaan-deysel/ha-unifi-insights)

A Home Assistant custom integration for monitoring and controlling your UniFi Network and UniFi Protect infrastructure using the official UniFi APIs.

## How this differs from the official integrations

This project overlaps with and complements Home Assistant's official integrations:

- [UniFi Network (official)](https://www.home-assistant.io/integrations/unifi/)
- [UniFi Protect (official)](https://www.home-assistant.io/integrations/unifiprotect/)

| Area              | UniFi Insights (this project)                                                                    | Official integrations                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Packaging         | Single integration covering both Network and Protect in one setup flow                           | Two separate core integrations (`unifi` and `unifiprotect`)                  |
| Authentication    | API key — local and cloud (remote console) connection modes                                      | UniFi Network: local credentials. UniFi Protect: local credentials + API key |
| Remote management | Supports UniFi cloud console discovery and selection                                             | Primarily local controller connectivity                                      |
| Service surface   | Adds integration-specific services for Network and Protect actions (vouchers, PTZ, chime, light) | Uses Home Assistant core entities and actions per integration                |
| Project lifecycle | Community custom component released via GitHub and HACS                                          | Included in Home Assistant Core release cycle                                |

**Which to choose:**

- Use the official integrations if you prefer core-maintained components with the widest documented feature surface.
- Use UniFi Insights if you want a single integration with API-key-first setup and combined Network and Protect support in one place.
- Running both side-by-side can create overlapping entities. Review and disable duplicates to avoid automation conflicts.

## Features

### UniFi Network

- Device monitoring: CPU, memory, uptime, temperature, and throughput for all adopted devices
- Per-port sensors: PoE power, port speed, link state, SFP module info, TX/RX traffic counters
- Client tracking & control: presence detection, block/allow switches, and reconnect buttons
- WiFi control & QR codes: enable/disable WiFi networks and scan-to-connect QR code images
- Firewall policy control: enable and disable user-defined firewall rules
- Traffic route management: enable and disable policy-based routing rules dynamically
- VPN client control: enable and disable VPN client interfaces (WireGuard, OpenVPN, Privado VPN)
- Firmware update management: check and initiate device upgrades
- Device and port actions: restart devices, power cycle PoE ports
- Guest & voucher services: authorize guests, generate and delete hotspot vouchers

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

### UniFi Mobility

- Mobile router (UMR) monitoring for remote entries: connection state, clients, WAN source, LTE signal, and cellular data usage
- VPN and data-plan subscription status
- GPS location as a device tracker
- Router counts per Mobility workspace

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

Remote entries also use the same API key to refresh Site Manager host, site, and
device inventory, five-minute ISP metrics, and SD-WAN configuration types every
10 minutes. Entries using the same key share one account refresh. This data is
available in the integration's coordinator and as a limited summary in the
downloadable diagnostics report; it does not create additional entities. A Site
Manager error does not stop the console connection, and collection availability
is shown in diagnostics.

#### UniFi Mobility

Remote entries also read [UniFi Mobility](https://unifi.ui.com) workspaces and
mobile routers (UMR, UMR Industrial, UMR Ultra) when the API key allows it. To
use it, create the key at [unifi.ui.com](https://unifi.ui.com) with Mobility read
access (the `mobility` scope with `read:mobility`). Local entries cannot use
Mobility: it is only offered by the UniFi cloud.

- Mobility data is refreshed every 5 minutes. Accounts with many routers are
  polled less often, so the integration averages no more than half of the key's
  100 requests per minute.
- A key without Mobility access is normal: the integration logs one message,
  creates no Mobility entities, does not ask you to re-authenticate, and checks
  again every hour. Accounts without routers are also checked hourly, so a new
  router can take up to an hour to appear (reload the entry to pick it up now).
- If several remote entries use the same API key, only one of them polls
  Mobility and creates its devices, so they are not duplicated: the oldest
  enabled entry when Home Assistant starts. If that entry is disabled or
  deleted, the next one takes over. If it is enabled but cannot load (for
  example, its console is offline), Mobility is not polled until it does.
- Mobility is read-only: router names, LAN, and Wi-Fi settings cannot be
  changed from Home Assistant, and the per-router client list is not read.

### Options

After setup, open the integration's options flow (**Settings** → **Devices & Services** → **UniFi Insights** → **Configure**) to adjust these settings:

| Option                | Default | Description                                                                                                                                                                                                                          |
| --------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Track WiFi Clients    | Off     | Creates device tracker entities for connected wireless clients. May add a large number of entities on busy networks.                                                                                                                 |
| Track Wired Clients   | Off     | Creates device tracker entities for connected wired clients.                                                                                                                                                                         |
| Enable Client Control | On      | Creates allow/block switch and reconnect button entities for each connected client. Disable this if you only need read-only monitoring — it prevents orphaned unavailable entities from accumulating when clients leave the network. |
| Sites                 | All     | Only shown when the console has more than one site. Pick the sites to poll; unselected sites are not queried at all, which cuts API traffic on multi-site consoles. Leave empty to include every site.                               |

## Entities

### Sensors

| Entity                           | Description                               |
| -------------------------------- | ----------------------------------------- |
| CPU Usage                        | Device CPU utilization (%)                |
| Memory Usage                     | Device memory utilization (%)             |
| Uptime                           | Device uptime                             |
| TX Rate                          | Uplink transmit rate (Mbit/s)             |
| RX Rate                          | Uplink receive rate (Mbit/s)              |
| Firmware Version                 | Installed firmware version                |
| Wired Clients                    | Count of wired clients (switches)         |
| Wireless Clients                 | Count of wireless clients (access points) |
| Total Clients                    | Total client count (site-level)           |
| Port PoE Power                   | PoE power consumption per switch port (W) |
| Port Speed                       | Link speed per port (Mbps)                |
| Port TX / RX                     | Traffic counters per port (bytes)         |
| Temperature                      | Protect sensor temperature (°C)           |
| Humidity                         | Protect sensor humidity (%)               |
| Light Level                      | Protect sensor ambient light (lux)        |
| Battery                          | Protect sensor battery level (%)          |
| Storage Used / Total / Available | NVR storage metrics (GB, when available)  |

### Binary sensors

| Entity            | Description                                                                         |
| ----------------- | ----------------------------------------------------------------------------------- |
| Device Status     | Network device online/offline state                                                 |
| WAN Status        | Gateway online state (for link state use WAN Connection)                            |
| WAN Connection    | Per-WAN internet connection state (DHCP, static or PPPoE) as the gateway reports it |
| Site-to-Site VPN  | Connection state of each site-to-site VPN tunnel (one sensor per tunnel)            |
| Motion Detection  | Camera or sensor motion activity                                                    |
| Person Detection  | AI person detection                                                                 |
| Vehicle Detection | AI vehicle detection                                                                |
| Animal Detection  | AI animal detection                                                                 |
| Package Detection | AI package detection                                                                |
| Doorbell Ring     | Doorbell ring activity                                                              |
| Door / Window     | Protect sensor open/close state                                                     |
| Tamper            | Protect sensor tamper detection                                                     |
| Leak              | Protect sensor water leak detection                                                 |
| Recording         | Camera actively recording                                                           |

### Switches

| Entity              | Description                                      |
| ------------------- | ------------------------------------------------ |
| WiFi Network        | Enable or disable a WiFi broadcast               |
| Firewall Rule       | Enable or disable a user-defined firewall policy |
| Client Allow        | Block or allow a connected network client        |
| Traffic Route       | Enable or disable a policy-based traffic route   |
| VPN Client          | Enable or disable a VPN client interface         |
| Camera Microphone   | Enable or disable the camera microphone          |
| Camera Privacy Mode | Enable or disable privacy mode                   |
| Camera Status Light | Enable or disable the status LED                 |
| Camera High FPS     | Enable or disable high frame rate mode           |

### Other entities

| Platform       | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| Button         | Restart device, reconnect client, play chime, PTZ patrol start/stop   |
| Camera         | Live view, snapshots, RTSPS streaming                                 |
| Device Tracker | Client presence detection, Mobility router GPS location               |
| Event          | Motion, doorbell ring, and smart detection events                     |
| Image          | WiFi QR codes for each broadcast network                              |
| Light          | Protect floodlight brightness control                                 |
| Number         | Microphone volume, chime volume, light brightness level               |
| Select         | Recording mode, HDR mode, video mode, ringtone, PTZ preset, live view |
| Update         | Firmware update management                                            |

### UniFi Mobility

Each active Mobility workspace is a service device with **Routers** and
**Online routers** counts. Each mobile router is its own device under its
workspace, with these entities:

| Entity                                 | Notes                                                               |
| -------------------------------------- | ------------------------------------------------------------------- |
| Connectivity                           | On while the router is connected to the UniFi cloud                 |
| State                                  | Connected, disconnected, adopting, upgrading, restarting, and so on |
| Clients                                | Connected client count                                              |
| WAN source                             | LTE, Ethernet WAN, or Wi-Fi WAN                                     |
| LTE signal                             | No signal, poor, fair, or strong                                    |
| Cellular data usage                    | Data used in the current billing cycle (resets each cycle)          |
| VPN status, Subscription status        | Unknown when no VPN or subscription is configured                   |
| Location                               | GPS device tracker; unknown while the router has no GPS fix         |
| Memory usage, Firmware                 | Diagnostic                                                          |
| Cellular data limit, Subscription plan | Diagnostic; the limit is unknown for unlimited plans                |
| Uptime, WAN IP address, ISP            | Diagnostic, disabled by default                                     |

A router that Mobility stops reporting becomes unavailable. You can then
delete its device from the device page.

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

## Carrier Fabric (ISP)

UniFi Insights supports monitoring and service management for UniFi Carrier Fabric (ISP) deployments.

### Getting an API Key

Carrier Fabric requires an ISP API key (type ISP) with the `read:subscribers` and `read:plans` scopes for monitoring. If you plan to use service actions to suspend or resume subscribers, the key also requires the `suspend:service` and `resume:service` scopes.

Refer to the [Carrier Fabric Developer Documentation](https://developer.ui.com/carrier-fabric/v1.0.0/getting-started) for details on creating an ISP API key. Console and Site Manager API keys do not work for Carrier Fabric.

### Configuration

Carrier Fabric is configured as a separate entry type. When adding the integration in Home Assistant (**Settings** → **Devices & Services** → **Add Integration** → **UniFi Insights**), select **Carrier Fabric (ISP)** and provide your ISP API key. Polling runs every 5 minutes.

### Options

The Carrier Fabric configuration entry provides two optional settings (both disabled by default):

- **Track subscribers**: When enabled, creates a device for each subscriber, providing a service state sensor and an assigned plan sensor. Each subscriber device is named after the subscriber's name (or their subscriber number when no name is set), so these names are customer data that anyone with access to your Home Assistant will see.
- **Enable service actions**: When enabled, permits executing the `carrier_suspend_subscriber` and `carrier_resume_subscriber` service actions to suspend or resume subscriber internet access.

### Entities

By default, the integration creates:
- **Primary sensors**: Total subscribers, suspended subscribers.
- **Diagnostic sensors**: Pending assignment subscribers, provisioned subscribers, installed subscribers, unassigned subscribers, active service plans count, and per-plan subscribers on each service plan (archived plans are disabled by default).

When subscriber tracking is enabled, each subscriber device includes:
- **Primary sensor**: Subscriber service state (`pending_assignment`, `provisioned`, `installed`, `suspended`, or `unknown` when the API reports a state this integration does not recognize).
- **Diagnostic sensor**: Subscriber service plan (the name of the subscriber's assigned service plan).

### Services

When "Enable service actions" is active and your API key has the required scopes:
- `unifi_insights.carrier_suspend_subscriber`: Stops a subscriber's internet service (optional `reason`, maximum 1024 characters). Target must be a single Carrier Fabric subscriber device or entity. Requires `suspend:service` scope.
- `unifi_insights.carrier_resume_subscriber`: Restores a subscriber's internet service. Target must be a single Carrier Fabric subscriber device or entity. Requires `resume:service` scope.

### Privacy & Diagnostics

Subscriber privacy is strictly preserved:
- Personal data such as email addresses, service addresses, customer notes, custom metadata, and suspension reasons are never exposed in Home Assistant entities or state attributes.
- Downloadable diagnostics reports contain only an allowlist of fields, and subscriber names and subscriber numbers are redacted from them.

### Out of Scope

The integration does not support plan assignment, subscriber creation or modification, or host attach/detach operations.

## Network topology card

The integration ships a Lovelace card that draws each site's network: the
gateway, switches and access points, and the clients connected to them. It is
installed with the integration — there is no separate download and no
dashboard resource to add.

**Add it:** edit a dashboard → _Add card_ → search for **UniFi Insights
Topology**. With a single UniFi site the card works without any configuration;
with several, pick the site in the card editor.

**Use it:**

- **Graph** view: drag to pan, pinch or Ctrl + scroll to zoom (plain scroll
  zooms in panel view), and use the zoom buttons or `+` / `-` / `0` keys.
  Select a device to see its uplink port, link speed, PoE draw and client
  counts, with a link to its Home Assistant device page.
- **List** view: the same network as an indented list with search. It is the
  recommended view for screen readers.
- Clients are grouped under their switch or access point ("12 clients");
  select a group to expand it.
- The filter buttons hide gateways, switches, access points, clients or other
  devices; devices under a hidden one stay visible, linked with a dashed line.

**Options** (all optional, all available in the card editor):

| Option                 | Values                                                        | Default                             |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------- |
| `entry_id` + `site_id` | the site to show                                              | the only site, if there is one      |
| `title`                | text                                                          | the site name                       |
| `view`                 | `graph`, `list`                                               | `graph`                             |
| `show_site_selector`   | `true`, `false`                                               | `false`                             |
| `clients`              | `collapsed`, `expanded`, `hidden`                             | `collapsed`                         |
| `kinds`                | any of `gateway`, `switch`, `access_point`, `client`, `other` | all                                 |
| `density`              | `comfortable`, `compact`                                      | automatic (compact on narrow cards) |
| `orientation`          | `vertical`, `horizontal`                                      | `vertical`                          |
| `show_labels`          | `true`, `false`                                               | `true`                              |
| `max_clients`          | 1–500                                                         | 500                                 |

The card only receives what the topology API sends — names, models, states,
ports and VLANs. MAC addresses, IP addresses, hostnames and firmware versions
are never included.

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

| Problem                       | Solution                                                                                                                                 |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Cannot connect                | Verify the host URL is reachable from Home Assistant. For self-signed certificates, disable SSL verification in the integration options. |
| Authentication failed         | Confirm the API key is valid and was not revoked in the UniFi Site Manager.                                                              |
| No Protect entities           | UniFi Protect must be running on the same console. Verify your API key has access to it.                                                 |
| Entities missing              | Confirm the devices are adopted and online in the UniFi controller.                                                                      |
| Storage sensors unavailable   | The public Protect API does not expose NVR storage data on all firmware versions.                                                        |
| Many orphaned client entities | Disable the **Enable Client Control** option in the integration's settings.                                                              |

### Diagnostics

To download a sanitized diagnostic report for troubleshooting:

1. Go to **Settings** → **Devices & Services**.
2. Select **UniFi Insights**.
3. Click the three-dot menu and choose **Download diagnostics**.

The report is sanitized before it is written: API keys, passwords and Wi-Fi
secrets, host names and IP addresses, SSIDs, and the names of your clients are
redacted, and every MAC address is replaced with a placeholder that stays
consistent within a single report. Device, site and camera names are kept so
the report remains readable. UniFi Mobility is summarized with counts only (for
example routers by state and model); no workspace or router names, addresses, or
locations are included.

## Contributing

Contributions are welcome. Please open an issue before submitting significant changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with or endorsed by Ubiquiti Inc. Use at your own risk.
