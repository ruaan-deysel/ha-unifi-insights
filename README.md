# UniFi Insights integration for Home Assistant

[![HACS Integration](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/releases)
[![GitHub Issues](https://img.shields.io/github/issues/ruaan-deysel/ha-unifi-insights)](https://github.com/ruaan-deysel/ha-unifi-insights/issues)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/ruaan-deysel)](https://github.com/sponsors/ruaan-deysel)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/unifi-insights-integration)
[![codecov](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights/graph/badge.svg?token=9WMPJAYFPE)](https://codecov.io/gh/ruaan-deysel/ha-unifi-insights)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unifi-insights)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ruaan-deysel/ha-unifi-insights)

Monitor and control your UniFi system from Home Assistant: UniFi Network, UniFi Protect, UniFi InnerSpace, UniFi Mobility, UniFi Site Manager and UniFi Carrier Fabric, in one integration.

## Contents

- [Overview](#overview)
- [Supported UniFi products](#supported-unifi-products)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- Products: [Network](#unifi-network), [Protect](#unifi-protect), [InnerSpace](#unifi-innerspace), [Mobility](#unifi-mobility), [Site Manager](#unifi-site-manager), [Carrier Fabric (ISP)](#unifi-carrier-fabric-isp)
- [Dashboard cards](#dashboard-cards)
- [Troubleshooting](#troubleshooting)

## Overview

UniFi Insights is a custom integration that you install from HACS. It connects with an API key, not a user name and password. It mainly uses the official UniFi APIs that Ubiquiti publishes at [developer.ui.com](https://developer.ui.com/). For some UniFi Network features that the official API doesn't cover yet, such as Wi-Fi QR codes, VPN and route switches, and internet traffic history, it uses the console's classic Network endpoints with the same API key.

- **One integration for your UniFi system.** One console entry covers that console's Network, Protect and InnerSpace applications. A cloud API key adds Mobility and Site Manager data. ISPs can add a Carrier Fabric entry.
- **API key setup, local or remote.** Connect to a console on your network, or choose any console on your UniFi account through UniFi Cloud. You don't need a local user account.
- **Standard Home Assistant entities.** Sensors, binary sensors, switches, buttons, cameras, events, lights, selects, numbers, images, device trackers and update entities, grouped under their UniFi devices.
- **Actions** for tasks that are not entities, such as guest authorization, hotspot vouchers, PTZ moves and Protect live views.
- **Six dashboard cards**, installed with the integration: network topology, site health, internet activity, device performance, Protect status and an event timeline.
- **Diagnostics that protect your privacy.** API keys, addresses, client names and other personal data are redacted.

## Supported UniFi products

| Product                                                 | Connection           | Highlights                                                                                                                 |
| ------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [UniFi Network](#unifi-network)                         | Local or Remote      | Device, port, power, WAN and client monitoring; Wi-Fi, firewall, route, VPN and client controls; guest access and vouchers |
| [UniFi Protect](#unifi-protect)                         | Local or Remote      | Cameras, smart detection and doorbell events, lights, chimes, PTZ, sensors, NVR storage, alarm hub status                  |
| [UniFi InnerSpace](#unifi-innerspace)                   | Local or Remote      | Floor-plan placement of your UniFi devices                                                                                 |
| [UniFi Mobility](#unifi-mobility)                       | Remote               | Mobile router status, cellular data use and GPS location                                                                   |
| [UniFi Site Manager](#unifi-site-manager)               | Remote               | Account-wide host, site, ISP and SD-WAN data in diagnostics                                                                |
| [UniFi Carrier Fabric (ISP)](#unifi-carrier-fabric-isp) | Carrier Fabric (ISP) | Subscriber and service plan counts, with optional suspend and resume                                                       |

The integration only creates entities for the applications your console runs. A console with only Network, only Protect or only InnerSpace works.

## Requirements

- Home Assistant 2026.6.0 or newer.
- For Local and Remote entries: a UniFi OS console (for example a UDM, UDR, UCG or Cloud Key Gen2+) with UniFi Network, UniFi Protect or UniFi InnerSpace. The console must provide the official UniFi Integration API. Self-hosted UniFi Network Application installs (Linux, Docker, Proxmox) don't provide it, so they can't be added as Local entries.
- For Remote entries, Mobility and Site Manager: a cloud API key from [UniFi Site Manager](https://unifi.ui.com).
- For Carrier Fabric: an ISP API key.
- Keep UniFi OS and its applications up to date. Some features need recent releases. For example, the Thread and keypad fob entities, and the alarm hub's reported tamper status, need UniFi Protect 7.3.70 or newer.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-unifi-insights&category=integration)

1. Select the button above, or open HACS and search for "UniFi Insights".
2. Select **Download**.
3. Restart Home Assistant.

### Manual installation

1. Download the latest release from the [Releases page](https://github.com/ruaan-deysel/ha-unifi-insights/releases).
2. Copy the `custom_components/unifi_insights` folder into your Home Assistant `custom_components` folder.
3. Restart Home Assistant.

## Configuration

### Choose a connection type

| Connection type           | Use it for                                                        | API key                                                        |
| ------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- |
| Local (Direct connection) | A console on your network: Network, Protect and InnerSpace        | Created on the console                                         |
| Remote (UniFi Cloud)      | Any console on your UniFi account, plus Mobility and Site Manager | Created in [UniFi Site Manager](https://unifi.ui.com)          |
| Carrier Fabric (ISP)      | An ISP's Carrier Fabric subscribers and service plans             | ISP API key, see [Carrier Fabric setup](#carrier-fabric-setup) |

You can add more than one entry, for example one per console.

### Add the integration

1. In Home Assistant, go to **Settings** → **Devices & services**.
2. Select **Add integration** and search for "UniFi Insights".
3. Choose the connection type, then follow the steps for it:
   - **Local:** create an API key on the console in **Settings** → **Control Plane** → **API Keys**. Enter the console URL (for example `https://192.168.1.1`) and the key. Leave **Verify SSL Certificate** off if the console uses its default self-signed certificate.
   - **Remote:** in [UniFi Site Manager](https://unifi.ui.com), go to **Settings** → **API Keys** and select **Create New API Key**. Copy the key, enter it, then choose the console from the list of consoles that the key can access.
   - **Carrier Fabric (ISP):** enter an ISP API key. See [Carrier Fabric setup](#carrier-fabric-setup).

### Options

To change these settings after setup, go to **Settings** → **Devices & services** → **UniFi Insights** → **Configure**:

| Option                | Default | Description                                                                                                                                                                        |
| --------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track WiFi Clients    | Off     | Creates a device tracker for each wireless client. This can add many entities on busy networks.                                                                                    |
| Track Wired Clients   | Off     | Creates a device tracker for each wired client.                                                                                                                                    |
| Enable Client Control | On      | Creates allow/block switches and reconnect buttons for connected clients. Turn it off for read-only monitoring. This also prevents unavailable entities from clients that left.    |
| Sites                 | All     | Only shown when the console has more than one site. Choose the sites to poll. Sites you don't choose are not queried at all, which reduces API traffic. Leave empty for all sites. |

Carrier Fabric entries have their own options. See [Carrier Fabric setup](#carrier-fabric-setup).

## UniFi Network

- **Device health:** status, CPU, memory, uptime, temperature and uplink rates for gateways, switches and access points.
- **Ports:** PoE power, link speed, traffic counters and rates, and SFP module details.
- **Power:** PDU outlet switches with power, voltage, current and power factor, and AC power consumption and budget.
- **Internet and WAN:** gateway and per-WAN connection status, WAN IP address, site-to-site VPN tunnel status, and internet download and upload totals for the last hour, day, week and month.
- **Clients:** client counts per site, device and Wi-Fi network; optional presence tracking; allow/block switches and reconnect buttons.
- **Controls:** switches for Wi-Fi networks, firewall policies, policy-based routes and VPN clients; device restart buttons; QR code images to join each Wi-Fi network.
- **Firmware:** update entities show the installed firmware and whether a newer version is available. They don't install firmware. Use the UniFi app for that.
- **Guest access:** authorize guests and create or delete hotspot vouchers with actions.

### Network entities

| Entity                                              | Type           | Notes                                                                                |
| --------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------ |
| Status                                              | Binary sensor  | Device online state                                                                  |
| CPU Usage, Memory Usage                             | Sensor         | Per device (%)                                                                       |
| Uplink Transmit Rate, Uplink Receive Rate           | Sensor         | Per device (Mbit/s)                                                                  |
| Uptime, Temperature, Firmware Version               | Sensor         | Per device, disabled by default                                                      |
| Wired Clients, Wireless Clients                     | Sensor         | Per switch or access point                                                           |
| Total Clients, Wired Clients, Wireless Clients      | Sensor         | Per site                                                                             |
| Connected clients                                   | Sensor         | Per Wi-Fi network, on its `WiFi: <SSID>` device                                      |
| Internet Download, Internet Upload                  | Sensor         | Per site, for the last hour, 24 hours, 7 days and 30 days                            |
| Total PoE Power, _port_ PoE Power                   | Sensor         | Per switch and per port (W)                                                          |
| _Port_ TX, RX, TX Rate, RX Rate, Speed              | Sensor         | Per port: traffic (bytes), rates (Mbit/s) and link speed (Mbps, disabled by default) |
| _Port_ SFP Module, SFP Vendor, SFP Type, SFP Serial | Sensor         | Per SFP port, disabled by default                                                    |
| _Port_ SFP Module                                   | Binary sensor  | On when an SFP module is inserted                                                    |
| AC Power Consumption, AC Power Budget               | Sensor         | Devices that report power                                                            |
| _Outlet name_ Power, Voltage, Current, Power Factor | Sensor         | Per PDU outlet                                                                       |
| WAN Status                                          | Binary sensor  | Gateway online state (for the link state, use the WAN connection)                    |
| _WAN name_ Connection                               | Binary sensor  | Internet connection state of each WAN (DHCP, static or PPPoE)                        |
| _Tunnel name_ Site-to-Site VPN                      | Binary sensor  | Connection state of each site-to-site VPN tunnel                                     |
| WAN IP Address, WAN Uptime                          | Sensor         | Gateway, disabled by default                                                         |
| WiFi _network name_                                 | Switch         | Turn a Wi-Fi network on or off                                                       |
| _Policy name_                                       | Switch         | Turn a user-defined firewall policy on or off                                        |
| _Route name_                                        | Switch         | Turn a policy-based route on or off                                                  |
| _VPN client name_                                   | Switch         | Turn a VPN client (WireGuard, OpenVPN, Privado VPN) on or off                        |
| _Outlet name_                                       | Switch         | Turn a PDU outlet on or off                                                          |
| _Outlet name_ Power Cycle                           | Switch         | Automatic modem power cycling for an outlet, disabled by default                     |
| _Client name_ Allow                                 | Switch         | Block or allow a client (needs **Enable Client Control**)                            |
| _Client name_ Reconnect                             | Button         | Reconnect a client (needs **Enable Client Control**)                                 |
| Restart                                             | Button         | Restart a device                                                                     |
| WiFi QR code                                        | Image          | Scan to join a Wi-Fi network                                                         |
| Client tracker                                      | Device tracker | Presence of each client (needs **Track WiFi Clients** or **Track Wired Clients**)    |
| Firmware                                            | Update         | Installed and available firmware version (no installation)                           |

### Network actions

| Action                            | Description                                   |
| --------------------------------- | --------------------------------------------- |
| `unifi_insights.restart_device`   | Restart a network device                      |
| `unifi_insights.authorize_guest`  | Authorize a guest client on a hotspot network |
| `unifi_insights.generate_voucher` | Create one or more hotspot vouchers           |
| `unifi_insights.delete_voucher`   | Delete a hotspot voucher                      |

```yaml
# Restart a network device
action: unifi_insights.restart_device
data:
  site_id: "your-site-id"
  device_id: "device-id"
```

```yaml
# Authorize a guest client
action: unifi_insights.authorize_guest
data:
  site_id: "your-site-id"
  client_id: "client-id"
```

```yaml
# Create a hotspot voucher
action: unifi_insights.generate_voucher
data:
  site_id: "your-site-id"
  count: 1
  duration_minutes: 480
```

`authorize_guest` doesn't send a duration or limits yet, so the `duration_minutes` and limit fields are ignored and a warning is logged. The guest network's default access time and limits from UniFi apply.

## UniFi Protect

- **Cameras:** live view, snapshots and RTSPS streams, with switches and selects for the microphone, privacy mode, status light, HDR and video mode.
- **Detection:** motion, person, vehicle, animal and package binary sensors, and smart detection and doorbell event entities.
- **Lights:** floodlight on/off and brightness, and a light mode action.
- **Chimes:** play button, volume, repeat count and ringtone.
- **PTZ:** move to a preset, and start or stop a patrol.
- **Sensors:** temperature, humidity, light level, battery, motion, door/window, tamper and leak.
- **NVR:** storage used, total and available, when the console reports it.
- **Security devices:** alarm hub tamper detection, plus Thread network status for Thread gateways and read-only keypad fob settings (both need Protect 7.3.70 or newer). These devices are read-only: the Protect API only allows integrations to rename them.
- **Live views:** create live views and choose the live view on a viewer.

### Protect entities

| Entity                                                                                          | Type                  | Notes                                                            |
| ----------------------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------- |
| Camera                                                                                          | Camera                | Live view, snapshots, RTSPS stream                               |
| Motion Detection, Person Detection, Vehicle Detection, Animal Detection, Package Detection      | Binary sensor         | Cameras                                                          |
| Ring                                                                                            | Binary sensor         | Doorbells                                                        |
| Doorbell, Smart Detection, Door/Window                                                          | Event                 | Doorbell rings, smart detections, and sensor open/close events   |
| Microphone, Privacy Mode, Status Light, High FPS Mode                                           | Switch                | Camera settings                                                  |
| HDR Mode, Video Mode, PTZ Preset                                                                | Select                | Camera settings                                                  |
| Microphone Volume                                                                               | Number                | Camera microphone volume                                         |
| Start PTZ Patrol, Stop PTZ Patrol                                                               | Button                | PTZ cameras                                                      |
| Floodlight                                                                                      | Light                 | On/off and brightness                                            |
| Brightness Level                                                                                | Number                | Floodlight brightness level                                      |
| Play                                                                                            | Button                | Play the chime                                                   |
| Chime Volume, Repeat Times                                                                      | Number                | Chime settings                                                   |
| Ringtone                                                                                        | Select                | Chime ringtone                                                   |
| Liveview                                                                                        | Select                | Live view shown on a viewer                                      |
| Temperature, Humidity, Light, Battery                                                           | Sensor                | Protect sensors (°C, %, lux, %)                                  |
| Motion Detection, Door/Window Status, Tamper Detection, Leak Detection, External Leak Detection | Binary sensor         | Protect sensors                                                  |
| Storage Used, Storage Total, Storage Available, Storage Used Percentage                         | Sensor                | NVR storage (GB, %), when the console reports it                 |
| Tamper Detection                                                                                | Binary sensor         | Alarm hubs, with the time and user name of the last tamper event |
| Thread Network                                                                                  | Binary sensor         | On when a gateway's Thread network reports a problem             |
| Thread Role, Thread Joined Devices                                                              | Sensor                | Thread gateways, diagnostic                                      |
| Keypad Beep, Keypad Beep Volume, Arm Control                                                    | Binary sensor, sensor | Keypad fobs, diagnostic, disabled by default                     |

### Protect actions

| Action                                  | Description                                                              |
| --------------------------------------- | ------------------------------------------------------------------------ |
| `unifi_insights.set_recording_mode`     | Set a camera's recording mode                                            |
| `unifi_insights.set_hdr_mode`           | Set a camera's HDR mode (`auto`, `on`, `off`)                            |
| `unifi_insights.set_video_mode`         | Set a camera's video mode (`default`, `highFps`, `sport`, `slowShutter`) |
| `unifi_insights.set_mic_volume`         | Set a camera's microphone volume (0–100)                                 |
| `unifi_insights.ptz_move`               | Move a PTZ camera to a preset (0–15)                                     |
| `unifi_insights.ptz_patrol`             | Start or stop a PTZ patrol                                               |
| `unifi_insights.set_light_mode`         | Set a light's mode (`always`, `motion`, `off`)                           |
| `unifi_insights.set_light_level`        | Set a light's brightness (0–100)                                         |
| `unifi_insights.play_chime_ringtone`    | Play a ringtone on a chime                                               |
| `unifi_insights.set_chime_volume`       | Set a chime's volume (0–100)                                             |
| `unifi_insights.set_chime_ringtone`     | Set a chime's ringtone                                                   |
| `unifi_insights.set_chime_repeat_times` | Set how many times a chime repeats (1–10)                                |
| `unifi_insights.trigger_alarm`          | Trigger an Alarm Manager webhook alarm                                   |
| `unifi_insights.create_liveview`        | Create a live view                                                       |
| `unifi_insights.set_liveview`           | Set the live view shown on a viewer                                      |

```yaml
# Move a PTZ camera to a preset position
action: unifi_insights.ptz_move
data:
  camera_id: "camera-id"
  preset: 0 # 0–15
```

```yaml
# Start or stop a PTZ patrol
action: unifi_insights.ptz_patrol
data:
  camera_id: "camera-id"
  action: "start" # start, stop
  slot: 0 # 0–15
```

```yaml
# Set a Protect light's mode
action: unifi_insights.set_light_mode
data:
  light_id: "light-id"
  mode: "motion" # always, motion, off
```

```yaml
# Play a ringtone on a chime
action: unifi_insights.play_chime_ringtone
data:
  chime_id: "chime-id"
  ringtone_id: "default" # default, mechanical, digital, christmas, traditional, custom1, custom2
```

## UniFi InnerSpace

InnerSpace places your UniFi devices on floor plans. For each device that InnerSpace reports, the integration creates a diagnostic **InnerSpace Placement** sensor:

- State: `placed`, `unplaced` or `unknown`.
- Attributes: floor plan name and ID, position (`x`, `y`, `height`, `azimuth`, `mount`), model and status.
- The sensor is added to the matching Network or Protect device. If no device matches, it gets its own InnerSpace device.

InnerSpace works with Local and Remote entries, and data is refreshed every 5 minutes.

## UniFi Mobility

Remote entries also read [UniFi Mobility](https://unifi.ui.com) workspaces and mobile routers (UMR, UMR Industrial, UMR Ultra). Mobility is only available through the UniFi cloud, so Local entries can't use it.

### Mobility setup

Create the cloud API key at [unifi.ui.com](https://unifi.ui.com) with Mobility read access (the `mobility` scope with `read:mobility`).

- Mobility data is refreshed every 5 minutes. Accounts with many routers are polled less often, so the integration uses no more than half of the key's 100 requests per minute on average.
- A key without Mobility access is normal: the integration logs one message, creates no Mobility entities, does not ask you to re-authenticate, and checks again every hour. Accounts without routers are also checked every hour, so a new router can take up to an hour to appear (reload the entry to add it now).
- If several remote entries use the same API key, only one of them polls Mobility and creates its devices, so they are not duplicated: the oldest enabled entry when Home Assistant starts. If that entry is disabled or deleted, the next one takes over. If it is enabled but cannot load (for example, its console is offline), Mobility is not polled until it does.
- Mobility is read-only: router names, LAN and Wi-Fi settings can't be changed from Home Assistant, and the per-router client list is not read.

### Mobility entities

Each active Mobility workspace is a service device with **Routers** and **Online routers** counts. Each mobile router is its own device under its workspace, with these entities:

| Entity                                 | Notes                                                               |
| -------------------------------------- | ------------------------------------------------------------------- |
| Connectivity                           | On while the router is connected to the UniFi cloud                 |
| State                                  | Connected, disconnected, adopting, upgrading, restarting, and so on |
| Clients                                | Connected client count                                              |
| WAN source                             | LTE, Ethernet WAN or Wi-Fi WAN                                      |
| LTE signal                             | No signal, poor, fair or strong                                     |
| Cellular data usage                    | Data used in the current billing cycle (resets each cycle)          |
| VPN status, Subscription status        | Unknown when no VPN or subscription is configured                   |
| Location                               | GPS device tracker; unknown while the router has no GPS fix         |
| Memory usage, Firmware                 | Diagnostic                                                          |
| Cellular data limit, Subscription plan | Diagnostic; the limit is unknown for unlimited plans                |
| Uptime, WAN IP address, ISP            | Diagnostic, disabled by default                                     |

A router that Mobility stops reporting becomes unavailable. You can then delete its device from the device page.

## UniFi Site Manager

Remote entries use the same cloud API key to read account-wide data from UniFi Site Manager every 10 minutes:

- Host, site and device inventory.
- Five-minute ISP metrics.
- SD-WAN configuration types.

Site Manager data does not create entities. A limited summary is included in the diagnostics report. Entries that use the same key share one account refresh. A Site Manager error does not stop the console connection, and the diagnostics report shows whether collection works.

## UniFi Carrier Fabric (ISP)

Carrier Fabric entries let ISPs monitor their UniFi Carrier Fabric subscribers and service plans, and optionally suspend or resume subscribers.

### Carrier Fabric setup

Carrier Fabric needs an ISP API key (type ISP) with the `read:subscribers` and `read:plans` scopes. To suspend or resume subscribers, the key also needs the `suspend:service` and `resume:service` scopes. See the [Carrier Fabric developer documentation](https://developer.ui.com/carrier-fabric/v1.0.0/getting-started) to create the key. Console and Site Manager API keys don't work for Carrier Fabric.

Add the integration, choose **Carrier Fabric (ISP)** and enter the ISP API key. Data is refreshed every 5 minutes.

Carrier Fabric entries have two options, both off by default:

- **Track subscribers:** creates a device for each subscriber, with a service state sensor and a service plan sensor. Each subscriber device is named after the subscriber's name, or their subscriber number when no name is set. These names are customer data that anyone with access to your Home Assistant can see.
- **Enable service actions:** allows the `carrier_suspend_subscriber` and `carrier_resume_subscriber` actions, which suspend or resume a subscriber's internet access.

### Carrier Fabric entities

By default, the integration creates:

- **Sensors:** total subscribers and suspended subscribers.
- **Diagnostic sensors:** subscribers pending assignment, provisioned, installed and unassigned; active service plans; and the number of subscribers on each service plan (archived plans are disabled by default).

When **Track subscribers** is on, each subscriber device has:

- **Sensor:** service state (`pending_assignment`, `provisioned`, `installed`, `suspended`, or `unknown` when the API reports a state that this integration does not recognize).
- **Diagnostic sensor:** service plan (the name of the subscriber's assigned service plan).

### Carrier Fabric actions

These actions need **Enable service actions** and an API key with the required scope:

- `unifi_insights.carrier_suspend_subscriber`: stops a subscriber's internet service (optional `reason`, maximum 1024 characters). The target must be a single Carrier Fabric subscriber device or entity. Needs the `suspend:service` scope.
- `unifi_insights.carrier_resume_subscriber`: restores a subscriber's internet service. The target must be a single Carrier Fabric subscriber device or entity. Needs the `resume:service` scope.

### Carrier Fabric privacy

- Personal data such as email addresses, service addresses, customer notes, custom metadata and suspension reasons is never shown in Home Assistant entities or state attributes.
- The diagnostics report contains only an allowlist of fields. Subscriber names and subscriber numbers are redacted.

The integration does not assign plans, create or change subscribers, or attach or detach hosts.

## Dashboard cards

The integration installs six dashboard cards. There is no separate download and no dashboard resource to add. To add a card, edit a dashboard, select **Add card** and search for its name. The cards use the integration's existing data and don't create entities.

| Card                     | Shows                                                                   |
| ------------------------ | ----------------------------------------------------------------------- |
| UniFi Topology           | Interactive network topology of a UniFi site                            |
| UniFi Site Health        | Compact site health summary with WAN, gateway, device and client status |
| UniFi Internet Activity  | Historical WAN download/upload activity and live gateway throughput     |
| UniFi Device Performance | Infrastructure CPU, memory, PoE, client load and throughput summary     |
| UniFi Protect Status     | Live UniFi Protect camera, doorbell, chime and NVR status summary       |
| UniFi Event Timeline     | Recent UniFi Protect security and device activity timeline              |

### Network topology card

The **UniFi Topology** card draws each site's network: the gateway, switches and access points, and the clients connected to them. With a single UniFi site the card works without any configuration. With several sites, choose the site in the card editor.

**Use it:**

- **Graph** view: drag to pan, pinch or Ctrl + scroll to zoom (plain scroll zooms in panel view), and use the zoom buttons or `+` / `-` / `0` keys. Select a device to see its uplink port, link speed, PoE draw and client counts, with a link to its Home Assistant device page.
- **List** view: the same network as an indented list with search. It is the recommended view for screen readers.
- Clients are grouped under their switch or access point ("12 clients"). Select a group to expand it.
- The filter buttons hide gateways, switches, access points, clients or other devices. Devices under a hidden one stay visible, linked with a dashed line.

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

The card only receives what the topology API sends: names, models, states, ports and VLANs. MAC addresses, IP addresses, hostnames and firmware versions are never included.

## Troubleshooting

### Enable debug logging

Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.unifi_insights: debug
```

### Force a refresh

To refresh all data now, for example in an automation:

```yaml
action: unifi_insights.refresh_data
```

### Common problems

| Problem                       | Solution                                                                                                                                                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Cannot connect                | Check that Home Assistant can reach the console URL. For self-signed certificates, turn off **Verify SSL Certificate** (reconfigure the entry to change it).                                                       |
| Authentication failed         | Check that the API key is valid and was not revoked on the console or in UniFi Site Manager.                                                                                                                       |
| Integration API not available | Self-hosted UniFi Network Application installs don't provide the official Integration API. Use a UniFi OS console.                                                                                                 |
| No Protect entities           | UniFi Protect must run on the same console, and the API key must have access to it.                                                                                                                                |
| Entities missing              | Check that the devices are adopted and online in UniFi.                                                                                                                                                            |
| Storage sensors unavailable   | The public Protect API does not report NVR storage on all firmware versions.                                                                                                                                       |
| Many orphaned client entities | Turn off the **Enable Client Control** option.                                                                                                                                                                     |
| Duplicate entities            | If you also use the official UniFi Network or UniFi Protect integration, both create entities for the same devices. Disable the duplicates you don't need so automations don't act on two entities for one device. |

### Diagnostics

To download a diagnostics report for troubleshooting:

1. Go to **Settings** → **Devices & services**.
2. Select **UniFi Insights**.
3. Select the three-dot menu and choose **Download diagnostics**.

The report is cleaned before it is written: API keys, passwords and Wi-Fi secrets, host names and IP addresses, SSIDs, and the names of your clients are redacted. Every MAC address is replaced with a placeholder that stays the same within one report. Device, site and camera names are kept so the report stays readable. UniFi Mobility is summarized with counts only (for example routers by state and model). No workspace or router names, addresses or locations are included.

## Contributing

Contributions are welcome. Please open an issue before you submit significant changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with or endorsed by Ubiquiti Inc. Use at your own risk.
