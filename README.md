# UniFi Insights Integration for Home Assistant

[![HACS Integration][hacsbadge]][hacs]
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unifi-insights?style=for-the-badge)](https://github.com/ruaan-deysel/ha-unifi-insights/commits/main)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unifi-insights?style=for-the-badge)](./LICENSE)

This custom integration allows you to monitor your UniFi devices through the UniFi Network API. Get detailed insights into your UniFi infrastructure directly in Home Assistant.

## Features

- Monitor device status (online/offline)
- Track CPU and memory usage
- Monitor device uplink rates (TX/RX)
- Track device uptime
- Restart devices through Home Assistant services
- Support for multiple UniFi sites

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-unifi-insights&category=integration)

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/unifi_insights` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

1. A UniFi Network controller (local or cloud)
2. API access enabled on your UniFi controller
3. An API key with appropriate permissions

### Getting an API Key

1. Open your site in UniFi Site Manager at [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Control Plane** → **Admins & Users**
3. Select your Admin
4. Click **Create API Key**
5. Provide a name for your API Key and copy it
6. Click **Done** to securely store the key

### Setting up the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click the "+" button to add a new integration
3. Search for "UniFi Insights"
4. Enter your:
   - API Key
   - Host URL (e.g., <https://192.168.1.1>)

## Available Entities

### Sensors

- CPU Usage (%)
- Memory Usage (%)
- Uptime (seconds)
- TX Rate (bytes/second)
- RX Rate (bytes/second)

### Binary Sensors

- Device Status (online/offline)

### Switches

- Device Restart

## Services

### `unifi_insights.refresh_data`

Force an immediate refresh of UniFi Insights data.

```yaml
service: unifi_insights.refresh_data
data:
  site_id: optional-site-id  # Optional
```

### `unifi_insights.restart_device`

Restart a UniFi device.

```yaml
service: unifi_insights.restart_device
data:
  site_id: your-site-id
  device_id: device-id-to-restart
```

## Troubleshooting

### Debug Logging

To enable debug logging, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.unifi_insights: debug
```

### Common Issues

- **Cannot Connect**: Verify your host URL and ensure your UniFi controller is accessible
- **Authentication Failed**: Verify your API key and ensure it has the necessary permissions
- **No Data**: Check that your devices are properly adopted in your UniFi controller

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially affiliated with or endorsed by Ubiquiti Inc.

## Support

For bugs and feature requests, please create an issue on GitHub.

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
