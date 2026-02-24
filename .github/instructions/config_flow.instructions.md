---
applyTo: "custom_components/unifi_insights/config_flow.py"
---

# Config Flow Instructions

**Applies to:** Configuration flow implementation

## Connection Modes

This integration supports two modes:

- **Local** — Host URL + API key (+ optional verify_ssl)
- **Remote** — Console ID + API key

## Unique ID

Based on the API key. Set via `await self.async_set_unique_id(api_key)`.

## Supported Flows

- **User setup** — Two-step: connection type selection → credentials
- **Reauth** — Handle expired/invalid credentials
- **Reconfigure** — Change host/connection settings

## Validation

Validates connectivity by fetching sites from the UniFi controller.

```python
try:
    await client.async_connect()
    sites = await client.get_sites()
except (asyncio.TimeoutError, TimeoutException) as ex:
    raise ConfigEntryNotReady("Timeout connecting") from ex
except AuthenticationError as ex:
    raise ConfigEntryAuthFailed("Invalid credentials") from ex
```

## Reserved Step Names

- Discovery: `bluetooth`, `dhcp`, `homekit`, `mqtt`, `ssdp`, `usb`, `zeroconf`
- System: `user`, `reauth`, `reconfigure`, `import`

## Unique ID Requirements

- Acceptable: Serial number, MAC address, device ID, API key hash
- Unacceptable: IP address, device name, hostname, URL

## Best Practices

- Always call `self._abort_if_unique_id_configured()` after setting unique_id
- Use `vol.Required` for mandatory fields, `vol.Optional` for optional
- Provide `suggested_value` for reconfig/reauth flows
- Show user-friendly error messages via `errors` dict
- Strings for steps, errors, and descriptions go in `strings.json`
