# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Network topology WebSocket API (`unifi_insights/topology/sources`,
  `unifi_insights/topology/get` and `unifi_insights/topology/subscribe`)
  exposing a per-site graph of gateways, switches, access points and clients.
  The graph is derived from data the integration already polls, so it adds no
  API calls. It is the groundwork for the network topology dashboard card
  ([#166](https://github.com/ruaan-deysel/ha-unifi-insights/issues/166)).
  [#165](https://github.com/ruaan-deysel/ha-unifi-insights/issues/165)
- Topology client nodes now carry their VLAN and network name, and wired
  client links their switch port, taken from the `/stat/sta` response the
  integration already fetches.
  [#165](https://github.com/ruaan-deysel/ha-unifi-insights/issues/165)
- Remote connections now load account-wide Site Manager host, site, and device inventory, five-minute ISP metrics, and SD-WAN configuration metadata through a shared optional coordinator. Diagnostics include bounded counts, selected-host ISP samples, and collection health without exporting cloud identifiers or raw account data. A Site Manager outage does not prevent the console integration from loading. [#171](https://github.com/ruaan-deysel/ha-unifi-insights/issues/171)
- UniFi InnerSpace floor-plan, placed device, and unplaced inventory support across local and remote console connections. A dedicated `UniFiInnerSpaceClient` and `UnifiInsightsInnerSpaceCoordinator` poll `/v1/project`, `/v1/floor_plans`, `/v1/access_points`, `/v1/switches`, and `/v1/inventory` independently of Network and Protect, correlating records by normalized MAC (scoped by floor-plan `siteId` when present) and exposing diagnostic **InnerSpace Placement** enum sensors (`placed`, `unplaced`, `unknown`) without modifying existing Network or Protect entity unique IDs, device identifiers, or Home Assistant area assignments. Consoles where only InnerSpace is reachable can now complete setup, and diagnostics export redacted InnerSpace counts and correlation summaries without floor-plan image URLs or raw geometry shapes. [#170](https://github.com/ruaan-deysel/ha-unifi-insights/issues/170)

### Fixed

- UniFi Protect requests no longer exceed the console's rate limit. The local Protect Integration API allows 10 requests per second per API key, but each Protect poll fired its seven fetches within about 100 ms while camera snapshots drew from the same allowance, so polls regularly got `429 Too Many Requests`. Since 2026.9.2 these were absorbed without a log line, which hid them: one install measured 120 rate-limited requests in 15 minutes with nothing in the log. On some starts the WebSocket `host_id` lookup was the request rejected, leaving Protect on 30-second polling with no push updates. The Protect API client now spaces its requests to stay under the limit, and a rate-limited request, snapshots included, waits out the console's `Retry-After` (1 second) and is retried once. A request that is rate limited again holds the client's other requests for the same wait instead of letting them run into the limit. The Network client is unchanged, since its API is not rate limited this way.

## [2026.9.7] - 2026-09-24

### Added

- A **WAN Connection** binary sensor for each WAN in use on a gateway (named "WAN", "WAN2" like the UniFi UI), including PPPoE WANs. It follows the gateway's own per-WAN status rather than the port's link light, so a PPPoE session that drops while the cable stays connected shows as disconnected. The raw status, reachability check result and address are attributes. The existing **WAN Status** sensor keeps reporting whether the gateway itself is online. [#162](https://github.com/ruaan-deysel/ha-unifi-insights/issues/162)
- A **Site-to-Site VPN** binary sensor for each site-to-site VPN tunnel (such as IPsec or SD-WAN), named after the tunnel and attached to the gateway. It follows the gateway's live per-tunnel connection state and turns off when the tunnel is not connected; the tunnel type and raw status are attributes. The site-wide tunnel counts UniFi also reports were not used: they were found to stay at "0 active" even while an IPsec tunnel was up. [#162](https://github.com/ruaan-deysel/ha-unifi-insights/issues/162)

### Changed

- Removed the redundant vendored API version module and consolidated its version
  constant into the API constants module without changing runtime behavior.

### Fixed

- Gateway detection is now shared by every platform. Gateways recognised only by an advertised gateway/router feature now get the WAN Status sensor, and models such as "Cloud Gateway Max" now get the WAN IP/uptime sensors.

## [2026.9.6] - 2026-09-22

### Changed

- The `Response is not JSON` warning now names the request method and path that produced the non-JSON body. Previously it logged only the (redacted, truncated) response body, so when a console returned an HTML page on one of the several endpoints polled by the config coordinator, the warning could not be attributed to the call that actually failed - a sustained burst of these was undiagnosable for exactly this reason. The path is logged via `url.path`, which omits the query string, so request credentials are never written to the log or captured in a diagnostics upload.

### Fixed

- Deleting a policy-based route, firewall rule, or VPN client on the console no longer leaves its switch entity permanently unavailable. Each of these switches reports `unavailable` once its backing object is gone, but nothing ever removed the entity from the registry - so the entity stayed forever, even after the object it represented no longer existed. A one-time cleanup at startup now removes each of these three switch types when the site that owned the deleted route, rule, or client was itself confirmed present in the same refresh, so a transient config-fetch failure, a console without the feature, or an in-progress first refresh can never be mistaken for "the object is gone" and cause an over-broad prune. `UnifiWifiSwitch` has the identical gap (gated by `wifi_available`) but is intentionally left for a follow-up, since deleting a WiFi network is rarer than deleting a route, rule, or VPN client.

- Uplink TX/RX rate, per-port PoE power, and NVR storage sensors no longer report `Unknown` when a device genuinely reports a reading of `0`. Each of these value functions chained its candidate fields with `or`, which is falsy-based rather than `None`-based, so `0 or <fallback>` discarded the real `0` and fell through to a missing fallback field, landing on `Unknown`. This is user-visible: an uplink briefly idling at exactly `0 B/s` - not uncommon - flipped its rate sensor to `Unknown` until traffic resumed, creating gaps in long-term statistics and `Unknown` landmines for any template or automation testing the state. A new `first_not_none()` helper in `entity.py` walks candidates by `is not None` instead of truthiness, and the affected `sensor.py` value functions (`tx_rate`/`rx_rate`, `port_poe_power`, the int-keyed `poe_ports` stats fallback, and NVR `_get_storage_bytes`) now use it. The ~44 other `or`-chains in the integration (device/client names, MACs, IDs, booleans, and container fallbacks where an empty result is genuinely "no data") are unaffected by this change.

## [2026.9.5] - 2026-09-20

### Changed

- Device registry lookups now call `DeviceRegistry.async_get_device_by_identifier()` on Home Assistant 2026.8 and newer, scoped to this config entry. Home Assistant 2026.9 deprecated `async_get_device()` because identifiers are only unique per config entry, and schedules its removal in 2027.8. Older Home Assistant versions keep using the existing call, so the integration still runs on the 2026.6 minimum declared in `hacs.json`.

### Fixed

- A Protect-only console with no UniFi Network application (such as a standalone UNVR) no longer logs a `Response is not JSON` warning every five minutes. Such a console answers the Network sites endpoint with HTTP 200 and an HTML body, which the config coordinator retried on every five-minute poll. The coordinator now skips that poll entirely when the setup probe reports the Network application as unavailable, and stops polling it for the rest of the session the first time the console answers with a non-JSON body or a 404. The probe runs again on every integration start and reload, so installing the Network application later restores site polling.
- Fall back to classic `system-stats` (`sys_stats`) CPU, memory, and uptime metrics for gateway and console devices (such as the UCG-Max) when the v1 statistics endpoint omits them or when devices are keyed by MAC address, preventing CPU and memory usage sensors from showing "Unknown". [#151](https://github.com/ruaan-deysel/ha-unifi-insights/issues/151)
- Recognize `UCG`, `UXG`, `UDR`, and `UDW` gateway models alongside `UDM` and `USG` for WAN sensors and gateway entity discovery.

## [2026.9.4] - 2026-09-19

### Added

- New devices and entities now appear on their own, without reloading the integration. Adopting an access point, switch or Protect camera, plugging in an SFP transceiver, or a device gaining a new capability previously left the matching entities missing until the integration was reloaded or Home Assistant was restarted, because all eleven entity platforms only created entities during setup. Every platform now re-checks the coordinator data as it arrives and adds whatever is new, tracking what it has already created so nothing is duplicated, and honouring the **Client control** option for the entities it gates. [#143](https://github.com/ruaan-deysel/ha-unifi-insights/pull/143)
- A **Sites** option lets a multi-site console poll only the sites you pick. Unselected sites are not queried at all, which cuts API traffic when Home Assistant only needs one site out of many. Leave it empty to keep polling every site. The picker only appears when the console has more than one site. Devices of a site you deselect can now be deleted from the device page, since they will never update again. [#128](https://github.com/ruaan-deysel/ha-unifi-insights/issues/128)

### Fixed

- Adding the same console twice no longer creates a second config entry on a multi-site controller. The configuration flow and setup derived the console's identity by separate rules that had drifted apart: the flow inspected only the first site's devices and fell back to the host address when that site's id was `default`, while setup scanned every site, consulted the Protect NVR, and skipped ahead to the first non-`default` site id. Setup could therefore adopt a MAC address the flow was never able to derive, so the flow kept computing a host-based identity that no longer matched the stored entry and the duplicate check did not fire. Both paths now share one console predicate and one site-id rule, and the flow scans sites in order until it finds the console - a console in the first site still costs a single request, so only the controllers that were broken pay for the extra lookups.
- A v1 devices endpoint that answers with a server error (HTTP 5xx) on controllers that list device models the API cannot serialize (reported with a USW Pro XG family switch) no longer wipes the site's device sensors. When the site's classic name is known, the device coordinator falls back to the legacy `/stat/device` endpoint, which serves every device, maps its fields into the v1 shape and keeps per-device statistics working; if the classic endpoint is also unreachable, the refresh fails and keeps the last known device state instead of reporting an empty site. [#129](https://github.com/ruaan-deysel/ha-unifi-insights/issues/129)
- Redact WiFi QR payloads from downloaded diagnostics so they cannot expose WiFi passwords.
- Downloaded diagnostics no longer identify the people on the network. Only passwords and a handful of well-known keys were redacted, so a report still carried each client's name, hostname and `deviceName` (usually the owner's name), the SSID it was connected to, and the MAC addresses of the client and of the access point or switch behind it (`bssid`, `apMac`, `swMac`). Client and Wi-Fi names, SSIDs and classic-API secrets are now redacted, and every MAC address - whatever key it arrives under, including fields UniFi may add later - is replaced with a placeholder that is stable within one report, so the report still shows which access point a client sits behind without disclosing an address. Device, site and camera names are kept so the report stays readable.
- A network device the controller reports without a `model` no longer breaks entity discovery. `model` is nullable on the device model, and the WAN-status gate and the suggested-area lookup both called string methods on it directly, so one such device raised `AttributeError` and stopped the whole discovery pass for its site. [#143](https://github.com/ruaan-deysel/ha-unifi-insights/pull/143)
- Port sensors discovered after startup are no longer retained for the lifetime of the Home Assistant process. The stale-port sweep runs once at setup, but the list it sweeps was extended on every coordinator update, so each entity created at runtime left behind a strong reference that nothing ever released. [#143](https://github.com/ruaan-deysel/ha-unifi-insights/pull/143)
- Protect door/window sensors no longer stop being reconciled against the REST API on busy systems. Sensor state was only refreshed inside the main 30s Protect poll, and every WebSocket device update calls `async_set_updated_data()`, which resets the coordinator's refresh timer - so on a console where any camera reports motion more often than every 30s, the sensor poll was postponed indefinitely and door contacts rode entirely on the WebSocket stream. A missed frame then stayed wrong until traffic went quiet. Sensor reconciliation now runs on its own timer that camera traffic cannot postpone, and is triggered immediately (debounced 5s) when the devices WebSocket reconnects, instead of waiting up to 30s for the next poll.
- A slow REST response can no longer overwrite newer WebSocket door state with older data. Previously a poll that started before a door opened could land after the WebSocket had already reported the change, flipping the contact back to its previous state until the following poll. REST responses are now rejected when the cached state is demonstrably newer, comparing against both the in-flight fetch window and the controller's own `openStatusChangedAt`/`motionDetectedAt` timestamps.
  - Preservation is bounded on every path so it can never wedge: at most 3 consecutive polls for the timestamp comparison, and 10 for the WebSocket-recency check. An unbounded version of this would be worse than the bug it fixes - a door stuck `Open` in Home Assistant indefinitely.
  - Once the WebSocket-recency cap trips it latches, letting REST win until REST and the cached value actually agree, rather than resetting and preserving again for another 10 polls. Resetting would turn a sustained disagreement into a repeating flip roughly every 11th poll, and these contacts drive auto-lock automations, so a spurious flip is user-visible.
  - Door, motion, tamper and leak are tracked as independent groups. A WebSocket frame marks only the group whose fields it actually carries, and preservation copies back only the groups it decided to preserve. Ambient telemetry (temperature, humidity, battery, signal) therefore no longer suppresses a reconciliation at all, and a motion frame can no longer drag a stale cached door value over a genuinely newer REST door transition.
- Sensor fetch errors are now bounded the same way the camera and light endpoints already were: absorbed for up to 3 consecutive polls to ride out a blip, then allowed through so a genuine controller outage marks entities unavailable instead of serving a stale cache indefinitely. Authentication failures on the background refresh paths now trigger the Home Assistant reauth flow rather than surfacing as an unhandled task exception.
- Reloading the UniFi Insights config entry no longer leaks a Protect coordinator. A shutdown listener was registered without retaining its unsubscribe callback, so each reload stranded a coordinator and its cached device data for the lifetime of the Home Assistant process.
- Network devices the API lists without an `id` (reported with a UAP-AC-M "AC Mesh") are no longer dropped with `Failed to validate device ... id Field required`. They are now keyed on their MAC address. Their legacy port and PoE metrics load, but the official per-device statistics endpoint is skipped because it can only be addressed by id. [#128](https://github.com/ruaan-deysel/ha-unifi-insights/issues/128)
- A revoked API key (HTTP 401) now starts Home Assistant's re-authentication flow even when it is first detected by a device, client, statistics, WiFi or firewall refresh; previously those errors were swallowed and the integration kept reporting success.
- When a site's devices or clients cannot be fetched, the device refresh now fails: entities fed by it (devices, ports, client controls, firmware updates) show as unavailable and keep their last known values until the next successful refresh, instead of silently going stale. A 403 on those endpoints no longer sends the entry into a re-authentication loop.
- A WiFi or firewall fetch failure no longer blanks those entities while reporting success. Only that site's WiFi or firewall entities become unavailable, keeping their last known values, and the rest of the integration (including Protect, and setup itself) keeps working.
- One device's statistics timing out or erroring now keeps that device's last known statistics for up to three polls instead of dropping its sensors to unknown, without distorting its port throughput rates.
- Setup no longer asks you to re-authenticate when the console is only temporarily unavailable, for example while it is still starting after a power cut. If the Network or Protect API times out, drops the connection or answers with a server error (5xx) or rate limit, setup is retried automatically. If one application works while the other keeps failing, setup retries a few times and then loads with the working one instead of silently dropping the other or keeping both offline. A Protect console whose NVR has no cameras yet no longer fails setup when the NVR check itself errors.
- The configuration flow now reports "Failed to connect" instead of "Unknown error" or "Invalid authentication" when the console answers with a server error or is temporarily unavailable, including while discovering and validating cloud consoles.
- The `refresh_data` action now actually fetches from the consoles. It called the facade coordinator's own `async_refresh()`, which only re-aggregates data already in memory, so the action re-published the same values and reported success without a single API request.
- `refresh_data` reports failures instead of swallowing them. A coordinator refresh records the problem as `last_update_success` and returns normally rather than raising, so a refresh against an unreachable console was logged and reported as a success.
- One unreachable console no longer stops the others from being refreshed; every console is attempted and the failures are reported together.
- A `site_id` that no configured console owns is now reported as a validation error instead of quietly answering "refreshed".
- Service actions now run against the console that owns the target instead of always the first configured one. With two consoles set up, `restart_device`, the Protect camera, light, PTZ, chime and viewer actions, and guest authorisation were all sent to console 1 regardless of which console owned the device, camera or site.
- `authorize_guest` resolves a client given by MAC address, not only by client ID, so guest actions reach the right site.

### Changed

- Protect sensor `openStatusChangedAt` and `motionDetectedAt` are normalized to integer epoch milliseconds at the model boundary. The controller has been observed sending these as epoch integers, ISO 8601 strings and native datetimes depending on payload path, which previously left REST and WebSocket values for the same field as different Python types. Unparseable values become `None` rather than raising, so a reshaped field cannot drop the whole sensor from a fetch.
- The Protect `Sensor` model now declares `model_key` (`modelKey`), which every other Protect device model already did - `sensor.py` was the only one missing it. Because the model is dumped with `by_alias=True, exclude_none=False` and the field carries a default, every sensor dictionary the coordinator produces now includes `"modelKey": "sensor"`, including for controllers that omitted the field entirely, where the key was previously absent. Nothing in the integration reads that key off a sensor dictionary today.
- Targeting a resource that belongs to a different console now raises a validation error naming the conflict, rather than silently acting on the first console. Single-console setups are unaffected.
- `trigger_alarm` and `create_liveview` accept an optional `console_id` (the integration entry title or its entry ID). It is only needed when more than one UniFi Protect console is configured, because neither action carries a target that can be routed on - `alarm_id` is an alarm manager webhook trigger, not a device.
- The `camera_id` field on the chime actions is documented as what it actually is: a hint for picking the console that owns the chime. This integration applies volume, ringtone and repeat count chime-wide.

### Documentation

- Agent-facing guidance (`AGENTS.md`, `CONTRIBUTING.md`, Copilot instructions, `api.instructions.md`) now points at the UniFi Developer Portal's **machine-readable** endpoints alongside the human docs. The portal's documentation pages are JavaScript-rendered, so a coding agent fetching `developer.ui.com/...` receives HTTP 200 and an empty app shell with no API content - a silent dead end that reads like a successful fetch. The `llms.txt` index, per-service `llms.txt`, `openapi.json` specs and the Network `ai-gettingstarted.md` primer all return real content and are now named explicitly, along with the current service versions and a note to resolve versions from the root index rather than hardcoding them.

## [2026.9.3] - 2026-09-14

### Fixed

- Client device trackers now report `not_home` after a restart instead of sitting at `unavailable` until the client happens to reconnect. [#120](https://github.com/ruaan-deysel/ha-unifi-insights/pull/120) stopped the registry entry from being deleted, but no entity was created for a client that was absent from the first coordinator poll, so Home Assistant restored the entry as `unavailable` and a Person assigned to that tracker stayed `unknown`. Every surviving registry entry is now given a live entity at setup, and it keeps the name the registry retained rather than reverting to `Client <mac>`. This completes the fix for [#116](https://github.com/ruaan-deysel/ha-unifi-insights/issues/116).
- Client trackers are looked up by MAC across every site instead of only the site they were created on, so a client that roams between sites is still resolved. The site is now only a starting hint and is updated when the client is found elsewhere.
- An offline client's tracker no longer renders its name twice ("Kitchen Tablet Kitchen Tablet"). A client with no uplink is grouped under a standalone device representing the client itself, and the tracker is that device's primary entity, so the device carries the name and the entity no longer repeats it. Found by testing against a live Home Assistant instance; the path is rare for connected clients but is the normal one for an absent client.
- A client tracker's `mac_address` no longer disappears while the client is away. It was read back out of the live client payload, so it returned `None` for exactly the absent clients a restored tracker exists to represent: the `mac` state attribute vanished whenever the device left the network, and Home Assistant's MAC registration for the entity was skipped. The MAC is now held on the tracker, matching how the core `unifi` and `fritz` device trackers report it.
- Client trackers now declare their own `unique_id` so it is namespaced to this integration rather than being the bare MAC that `ScannerEntity` supplies. Existing trackers registered under the bare MAC are re-keyed in place on the next setup, preserving their name, area and entity ID. If the target ID is already taken, the legacy entry is left alone and still gets a working entity.

## [2026.9.2] - 2026-09-09

### Fixed

- Protect entities (cameras, lights, door sensors, doorbell/smart-detect events, NVR sensors) no longer go unavailable when the _Network_ API has a transient error. Entity availability is now gated on the sub-coordinator that actually provides the data instead of an aggregate fold across all of them, so a Network session drop (`Response is not JSON: <!doctype html>`) leaves Protect entities alone. PDU outlet switches gate on the device coordinator for the same reason.
- Protect devices are no longer permanently removed from the Home Assistant device registry because of a transient polling failure. A single empty list, 404, fetch error or short response used to be enough to purge a device, losing its area assignment, entity customizations and any automation keyed on `device_id`. Recovery is bounded on several fronts:
  - Empty or 404 device collections preserve the cache for up to 3 consecutive polls before clearing, so genuinely unadopted devices are still cleaned up.
  - Fetch errors (transport failures, HTTP 500s) preserve the cache without counting toward that limit - an error means "we could not ask", not "the devices are gone". This now applies to the camera and light endpoints too: previously only a 404 was handled there, so any other error aborted the whole Protect poll and took every Protect entity unavailable. Absorption is bounded at 3 consecutive failed polls per collection, after which the error is allowed through so a genuine controller outage still marks entities unavailable instead of serving a stale cache. Authentication errors are never absorbed, so reauth still triggers immediately.
  - A device missing from its collection must now be absent for more than 3 consecutive polls (~90s) before it is removed from the device registry.
  - When the Protect API returns a device whose payload fails to parse, that device is skipped as before but the response is flagged incomplete: the collection is merged over the cache rather than replacing it, so a field reshaped by a Protect release cannot evict the affected devices. If _every_ device in a family fails to parse, the cache is preserved instead of being treated as an empty controller.

### CI & Testing

- Added GitHub Actions workflow (`.github/workflows/test.yml`) to run pytest with branch coverage and upload reports to Codecov (`codecov/codecov-action@v5`).
- Added `codecov.yml` configuration defining 90% project and patch coverage targets with detailed PR coverage comments.
- Untracked `coverage.xml` build artifact from git tracking.
- Added Codecov coverage status badge to `README.md`.

### Documentation

- Updated the pull request template and developer guidance (`CONTRIBUTING.md`, `AGENTS.md`, Copilot instructions) to reference the [UniFi Developer Portal](https://developer.ui.com/) for official API documentation, latest developer capabilities, and coding agent context.

## [2026.9.1] - 2026-09-03

### Added

- Added support for UniFi Power Distribution Units (PDUs) and SmartPower strips (e.g. USP-PDU-Pro, USP-Strip):
  - Per-outlet relay switches (`UnifiOutletSwitch`) to toggle power state on individual outlets
  - Config switches (`UnifiOutletCycleSwitch`) for outlets supporting automatic modem power cycling
  - Per-outlet metering sensors for metered outlets (power in W, voltage in V, current in A, and power factor)
  - Device-level power total sensors for AC power consumption and AC power budget

### Changed

- Switch entity names now resolve through the entity translation system instead of
  hardcoded `_attr_name` values, satisfying the `entity-translations` quality scale
  rule. Covers the firewall rule, policy-based route, VPN client, client allow and
  WiFi switches. Displayed names and entity IDs are unchanged.

Thanks @delacjus

## [2026.9.0] - 2026-09-02

### Added

- Added VPN Client switch control (`UnifiInsightsVpnClientSwitch`) to enable or disable VPN client interfaces (e.g., Privado VPN, WireGuard, OpenVPN) directly from Home Assistant (closes #79)
- Added Policy-Based Routes (Traffic Routes) switch control (`UnifiInsightsPolicyBasedRouteSwitch`) to enable or disable traffic and VPN client routing rules dynamically from Home Assistant (closes #79)
- Added `VpnClientsEndpoint` and `VpnClient` model in the vendored Network API client targeting `/proxy/network/api/s/{site}/rest/networkconf` with strict `purpose == "vpn-client"` filtering and error envelope propagation
- Added `RoutesEndpoint` and `PolicyBasedRoute` model in the vendored Network API client targeting `/proxy/network/v2/api/site/{site}/trafficroutes`
- Added `get_vpn_clients` and `get_policy_based_routes` caching and retrieval in `UnifiConfigCoordinator` and action delegation in `UnifiFacadeCoordinator`
- Exposed route metadata attributes (`matching_target`, `interface`, `vpn_client_id`, `kill_switch_enabled`, `domains`, `ip_addresses`, `client_macs`, `network_ids`, `target_devices`, `network_id`, `next_hop`, `regions`, `ip_ranges`) on route switch entities
- Exposed VPN client metadata attributes (`client_id`, `purpose`, `vpn_type`, `ip_subnet`, `openvpn_id`, `wireguard_id`, `remote_host`) on VPN client switch entities
- Added automatic gateway device grouping for VPN clients and policy-based routes, with fallback site-level grouping

### Fixed

- Fixed `PolicyBasedRoute` parsing failure for domain-based traffic routes on UniFi Network 10.6+ where `domains` contains object dictionaries (`[{"domain": "...", ...}]`) rather than simple strings
- Fixed `kill_switch_enabled` attribute parsing from live controller payload shape and added warning when disabling a route with an active kill switch
- Fixed site name resolution on multi-site controllers via `resolve_legacy_site_name` on `UnifiFacadeCoordinator`

### Thanks

- Special thanks to [@delacjus](https://github.com/delacjus) for live-hardware testing on UniFi Dream Machine SE (Network 10.6), domain route model alignment, kill switch hardening, and multi-site resolution in PR #105

## [2026.8.4] - 2026-08-30

### Fixed

- Fixed setup retries on Protect-only consoles (for example UNVR/UNVR-Pro) when the Network `sites` endpoint returns HTTP 200 with a non-JSON HTML body; the config coordinator now tolerates this specific response only when Protect is configured, while still failing for non-200 statuses and non-Protect scenarios (closes #102)
- Fixed Protect WebSocket events stream error frames (for example rate-limit notices with an `error` field) being misclassified as parse failures; these frames are now handled explicitly and logged with a dedicated warned-once path so real parse-shape issues remain visible (closes #102)

### Thanks

- Special thanks to [@delacjus](https://github.com/delacjus) for the regression fix and WebSocket stream hardening in PR #102

## [2026.8.3] - 2026-08-30

### Added

- Added 5-minute event auto-off timeout (`STALE_EVENT_TIMEOUT`) and reconciliation logic during REST polls and WebSocket reconnections to prevent latched motion or ring states if an "end" frame is missed (closes #101)
- Added granular per-subscription WebSocket health tracking (`devices` and `events`) to integration diagnostics (closes #101)

### Fixed

- Fixed camera motion, doorbell ring, and smart detection binary sensors remaining permanently `off` by subscribing to the UniFi Protect WebSocket "events" stream and dispatching real-time detection events (closes #101)
- Fixed UniFi Protect entities only updating during periodic REST polling by connecting and driving the live Protect WebSocket "devices" stream with tolerant update envelope parsing and lifecycle management on setup and unload (closes #100)
- Fixed `UnifiInsightsEntity` and `UnifiProtectEntity` reporting `available = True` and serving stale cached device states when their backing coordinator fails — both base entities now gate availability and state updates on `self.coordinator.available` (closes #98)
- Fixed listener leak in `UnifiFacadeCoordinator` by storing unsubscribe callbacks returned by `async_add_listener()` and releasing them idempotently in `async_shutdown()` on config entry unload or reload (closes #99)
- Fixed `UnifiFacadeCoordinator.async_request_refresh()` to concurrently execute `async_refresh()` across all sub-coordinators instead of debounced requests, ensuring immediate state propagation after service calls and user actions (closes #99)
- Fixed missing camera and sensor binary sensor translation keys in `translations/en.json` that caused naming collisions falling back to generic names (closes #101)
- Added `heartbeat=30` to WebSocket connections to detect half-open sockets and trigger bounded reconnection (closes #101)

### Thanks

- Special thanks to [@delacjus](https://github.com/delacjus) for contributing the fixes and enhancements in PRs #98, #99, #100, and #101 (as well as #97 in 2026.8.2), bringing real-time Protect WebSocket device and event streaming, coordinator freshness gating, and lifecycle fixes!

## [2026.8.2] - 2026-08-29

### Fixed

- Fixed API client silently treating 2xx responses with non-JSON bodies (e.g. HTML login redirects or expired sessions from UniFi consoles and reverse proxies) as successful empty responses instead of raising `UniFiResponseError` — on Protect-only consoles like UNVR / UNVR-Pro, this previously allowed entities to freeze and serve stale cached data indefinitely without marking entities unavailable or triggering coordinator retry and backoff (closes #97, refs #93)

## [2026.8.1] - 2026-08-25

### Added

- Added support for standalone Protect-only consoles (e.g., UNVR, UNVR-Instant, UNVR-Pro) in both Local and Remote connection modes — onboarding and integration setup gracefully probe both Network and Protect APIs, enabling Protect monitoring and control even when UniFi Network is not installed or enabled (closes #93)
- Added dual-application connection validation in the config flow (`_async_validate_local_connection` and `_async_validate_remote_console`) to automatically detect available Network and Protect services

### Fixed

- Fixed device coordinator failing on UniFi OS 5.1.31 / Network 10.5.67 consoles returning `features` and `interfaces` as lists (e.g. `["switching"]`, `["accessPoint"]`, `["ports"]`, `["radios"]`) or string `uplink` IDs, which previously broke `Device` model validation and rendered all network entities unavailable; also added isolated per-item validation to `DevicesEndpoint` and `ClientsEndpoint` (closes #94)
- Fixed setup failure on UniFi Dream Router / Dream 7 consoles returning site payloads without an explicit `id` field — `Site` model now gracefully falls back to `internal_reference` or `name` (defaulting to `"default"`), and `SitesEndpoint.get_all()` skips malformed records with friendly `site_parse_error` translation (closes #80)
- Fixed `script/test` failing with `unbound variable` under `set -u` on macOS Bash 3.2

## [2026.8.0] - 2026-08-04

### Added

- Expanded the vendored UniFi Network and Protect API packages with typed models
  and endpoints for link aggregation groups (LAG), multi-chassis LAG domains, and
  switch stacks (Network) and for alarm hubs, arm profiles, relays, sirens,
  speakers, bridges, key fobs, and link stations (Protect) to support Network
  10.4.57 and Protect 7.1.87
- Added tolerant models for the `doorlock` and `viewport` Protect WebSocket
  device types, and routed their real-time updates through the Protect
  coordinator and facade aggregation

## [2026.6.4] - 2026-06-13

### Fixed

- Fixed UniFi Protect cameras showing "does not support play stream service" — `UnifiProtectCamera` overrode `async_stream_source()` but HA's `Camera.async_create_stream()` internally calls `stream_source()`; renamed the method to `stream_source()` so the stream pipeline is correctly wired

## [2026.6.3] - 2026-06-12

### Fixed

- Fixed UniFi Protect devices removed from the controller never being cleaned up — the Protect coordinator only ever added/merged devices into its data, so the stale-device registry cleanup could never detect a removal; each poll now rebuilds the camera/light/sensor/NVR/chime/viewer/liveview collections from the API response, making the Gold-tier stale-device cleanup actually work
- Fixed missing `@callback` decorator on the WiFi QR code image entity's `_handle_coordinator_update` override (same bug class as the 2026.6.2 coordinator fixes)
- Fixed all coordinators relying on Home Assistant's `current_entry` ContextVar fallback instead of passing `config_entry` explicitly to `DataUpdateCoordinator` — HA flags this pattern for removal (core breaks in 2026.8) and the explicit entry also auto-registers coordinator shutdown on entry unload
- Fixed the facade coordinator's `data` being `None` until an external (private) `_aggregate_data()` call from `__init__.py`; the facade now aggregates sub-coordinator data during its own initialization
- Fixed config entry unloading closing the API clients _before_ unloading the platforms — a failed platform unload previously left loaded entities behind with closed clients; clients are now only closed after all platforms unloaded successfully
- Fixed `script/test` being broken: it pinned `homeassistant==2026.4.1` against `pytest-homeassistant-custom-component==0.13.317` (which requires HA 2026.3.1, an unsolvable conflict) and did not install the `segno` manifest requirement; it now installs HA 2026.6.2 with plugin 0.13.338 and `segno`

### Changed

- Service actions are now registered in `async_setup` instead of the first config entry setup, per the Quality Scale `action-setup` rule — actions are validatable even when no entry is loaded, and handlers raise `ServiceValidationError` when no coordinator is available
- Replaced the deprecated `OptionsFlowWithConfigEntry` base class with `OptionsFlow` (the config entry is provided automatically since HA 2024.11)
- Bumped the minimum Home Assistant version to `2026.6.0` in `hacs.json` and the README (HA is now on Python 3.14)
- Added `data_description` helper texts to the reauthentication and reconfigure config flow steps (Quality Scale `config-flow` rule)

### Tests

- Test suite now runs (and passes: 1043 tests, 90.5% coverage) against Home Assistant 2026.6.2 / Python 3.14
- Added a test module for the WiFi QR code image platform (`tests/test_image.py`)
- Updated stale tests that still asserted pre-2026.6.0 behavior (camera snapshot width/height parameters, uppercase tracker unique IDs, the removed global tracked-clients set) and fixed coordinator/config-flow test fixtures that leaked refresh timers and sockets

## [2026.6.2] - 2026-06-06

### Fixed

- Fixed missing `@callback` decorator on `UnifiFacadeCoordinator._handle_coordinator_update` — the method is registered as an event-loop listener via `async_add_listener()` on all three sub-coordinators and must be decorated with `@callback` per HA coding standards (closes #59)
- Fixed missing `@callback` decorators on `UnifiProtectCoordinator._handle_device_update` and `_handle_event_update` — these WebSocket callback handlers call `async_update_listeners()` (itself a `@callback`), so they must also be marked as event-loop callbacks
- Fixed misleading "WebSocket callbacks registered" debug log in the Protect coordinator — the message previously fired even when neither WebSocket callback was actually registered (both are guarded by `hasattr` checks that currently return `False`)

### Notes

- The HA warning "Updating state for switch.firewall_policies_default_crowdsec_bouncer_ban_2 took 0.548 seconds" reported in #59 is **not a code bug**. HA's threshold is 0.4 s and the warning fires only once per entity lifetime (`_slow_reported = True`). The entity's properties are all O(1) dict lookups; the 0.548 s was caused by the UDM-SE host running at 100% CPU, starving HA's event loop. The `@callback` changes above are correctness improvements aligned with HA standards that reduce the chance of async-violation warnings from HA's debug checker.

## [2026.6.1] - 2026-06-04

### Added

- Added **Client Control** option (enabled by default) to the integration's options flow — disabling it prevents creation of client allow/block switch entities and client reconnect button entities, eliminating orphaned unavailable entities when clients leave the network (closes #57)

### Fixed

- Fixed deprecation warning "The deprecated alias ScannerEntity was used from unifi_insights" by updating the import to `homeassistant.components.device_tracker.ScannerEntity`; the old path in `config_entry` is removed in HA Core 2027.6 (closes #58)
- Fixed microphone switch always showing as OFF on Protect v7.1.x — the API renamed the field from `micEnabled` to `isMicEnabled`; both names are now read with `isMicEnabled` taking priority, and the PATCH call now correctly sends `isMicEnabled`
- Fixed High FPS mode switch never being created on Protect v7.1.x cameras that support it — the API removed the `hasHighFpsCapability` feature flag in favour of listing `highFps` in `featureFlags.videoModes`; both detection methods are now checked

## [2026.6.0] - 2026-05-30

### Added

- Added per-WiFi-network connected client count sensors (`sensor.<ssid>_connected_clients`) — shows how many clients are currently on each SSID, updated every polling cycle (closes #49)
- Added WiFi QR code image entities (`image.<ssid>_wifi_qr_code`) — phone cameras can scan these directly to join the network; credentials sourced from the classic API (closes #49)
- Added `authorize_guest` and `unauthorize_guest` coordinator methods wired to the official Network Integration API `POST /clients/{id}/actions` endpoint with `AUTHORIZE_GUEST_ACCESS` / `UNAUTHORIZE_GUEST_ACCESS`; the previously stubbed `authorize_guest` service now works

### Fixed

- Fixed client block, unblock, reconnect, and forget actions returning HTTP 404 — the official Network Integration API does not expose these operations; they are now routed through the classic `POST /api/s/{site}/cmd/stamgr` endpoint (`block-sta`, `unblock-sta`, `kick-sta`, `forget-sta`) which is accessible with the same local API key (closes #44)
- Fixed classic API error envelopes (`{"meta":{"rc":"error",...}}` returned with HTTP 200) now raising `UniFiResponseError` instead of silently succeeding in client station-manager commands
- Fixed UniFi Protect cameras returning HTTP 500 (`AJV_PARSE_ERROR`) when HA requested a snapshot — the Protect Integration API rejects `w`/`h` query parameters; removed them from `get_snapshot`; HA scales the returned JPEG internally
- Fixed Protect model parsing silently dropping all cameras/sensors/lights/chimes/viewers when any single device in the response contains an unrecognised field value (e.g. a new enum from Protect 7.1) — each endpoint's `get_all()` now skips and logs the individual malformed item instead of failing the whole list (closes #52)
- Fixed `CameraState` and `ViewerState` (and `CameraType`) enums mapping unknown values to `UNKNOWN` instead of raising a `ValidationError`; Protect 7.1.x new states no longer break camera entities
- Fixed toggling "Track WiFi clients" / "Track wired clients" in the integration options having no effect — the dedup set previously survived config-entry reloads (stored in `hass.data`), so re-enabling tracking added nothing; the set is now local to each setup call, and the entity registry is reconciled on every reload to remove trackers that are no longer wanted and add those that are
- Fixed stale/historical client trackers polluting the integration when tracking was enabled — only currently-connected clients (from the official `/clients` endpoint) become tracker entities; known-but-disconnected devices from the controller history are not imported
- Fixed transient controller connectivity failures (`UniFiConnectionError`, `UniFiTimeoutError`) during device coordinator site processing logging a full ERROR traceback; they are now a concise WARNING

### Changed

- Bumped minimum Home Assistant version to `2026.5.4` in `manifest.json` and `requirements.txt`
- `script/setup/bootstrap` now installs the **latest available** Home Assistant release on every run (`uv pip install --upgrade ".[dev]" homeassistant`) instead of a hard-pinned version, so the dev environment stays current automatically
- WiFi data is now enriched at config-coordinator level: secrets (SSID, passphrase, security) are pulled from the classic `/rest/wlanconf` endpoint (the official API redacts them), and per-SSID client counts are computed from the classic `/stat/sta` endpoint
- `CameraType`, `CameraState`, and `ViewerState` Protect enums now extend a shared `_TolerantStrEnum` base that maps any unrecognised value to `UNKNOWN` instead of raising
- Added `segno==1.6.6` to `manifest.json` requirements for QR code image generation

- Fixed missing `TELEPORT` value in the vendored `ClientType` enum (alongside `VPN`) to prevent client model validation failures when controllers return this connection type

## [2026.5.0] - 2026-05-05

### Fixed

- Fixed port sensor display names showing generic labels like "Data size" and "Power" by restoring missing sensor translation keys in `translations/en.json`
- Fixed per-port sensor naming to use `{port_label}` translation placeholders so each metric has a distinct name (for example, "Port 1 TX", "Port 1 RX", and "Port 1 PoE Power")
- Fixed local/remote config flow handling for UniFi Network Integration API 404 responses by surfacing a clear `api_unsupported` user-facing error instead of an unexpected exception

## [2026.4.1] - 2026-04-12

### Security

- Fixed pip tar extraction symlink vulnerability (CVE-2025-8869) by raising minimum `pip` to `>=25.3` in `requirements.txt`
- Redacted sensitive field values (API keys, passwords, tokens, credentials, PSKs, passphrases, vouchers) from debug log messages and API error bodies in the vendored API base client
- `UniFiResponseError.__str__()` now returns only the exception type and status code (`ExceptionType(status=<code>)`), preventing `message` or raw response body from leaking into logs or error messages
- Expanded `diagnostics.py` redaction set to cover tokens, credentials, network identifiers (IP, hostname, WAN/LAN IPs), device identifiers (MAC, serial), config entry fields, and location data (latitude, longitude)
- Pinned GitHub Actions `actions/checkout` and `actions/stale` to full SHA digests to mitigate supply chain attacks

### Added

- Added `"homeassistant": "2026.4.1"` minimum version requirement to `manifest.json`
- Added Aikido security scan instructions (`.github/instructions/aikido_rules.instructions.md`) to enforce pre-commit and PR security scanning

### Fixed

- Fixed `script/setup/bootstrap` pre-commit hook installation failing when a global `core.hooksPath` is configured (e.g. by the Aikido devcontainer scanner); the local repo value is now overridden to the default `.git/hooks` path before installing
- Fixed incorrect `unique_id` values in test fixtures — both remote and local config entries now use the API key as `unique_id`, matching the actual config flow behavior (`async_set_unique_id(api_key)`)

### Changed

- Replaced `softprops/action-gh-release` in the release workflow with the native `gh release create` CLI command, removing a third-party action dependency
- Log-line string concatenations in `__init__.py` consolidated to single-line strings (cosmetic)

## [2026.4.0] - 2026-04-09

### Added

- Added `.github/dependabot.yml` configuration for `devcontainers`, `github-actions`, and `pip` updates with daily checks, grouped updates, labels, and commit message prefixes

### Changed

- Updated Home Assistant minimum/runtime version to `2026.4.1` across `requirements.txt`, `hacs.json`, `script/setup/bootstrap`, and `script/test`
- Updated dependency automation to allow future Home Assistant version updates (removed Dependabot ignore rule for `homeassistant`)

### Fixed

- Fixed Protect API validation to probe the NVR endpoint when camera discovery returns an empty list, preventing valid "no cameras" setups from being misclassified as Protect API failures (PR #22)

## [2026.3.2] - 2026-03-31

### Added

- Added SFP/SFP+ port differentiation with user-friendly port names (e.g., "SFP+ 1" instead of "Port 25")
- Added SFP module diagnostic sensors: module model, vendor, type (compliance), and serial number
- Added SFP module presence binary sensor for all SFP/SFP+ ports with module detail attributes
- Added port type extra state attributes (media type, uplink status, network, SFP presence) to all port sensors
- Added auto-pagination support for wired client fetching to handle large networks correctly

### Fixed

- Fixed PoE sensor creation failing on non-PoE devices (e.g., UDM Pro) by checking port PoE capability before creating sensors
- Fixed firewall rule switches to properly filter predefined/system rules and group by gateway device
- Fixed port sensor filtering to skip inactive (DOWN) ports
- Fixed `get_port_metrics` endpoint to check PoE capability before requesting PoE data

### Removed

- Removed port enable/disable switches (unreliable with current UniFi API)
- Removed PoE toggle switches (unreliable with current UniFi API)
- Removed port power cycle buttons for PoE ports

## [2026.3.1] - 2026-03-22

### Fixed

- Fixed Unifi Remote Cloud authentication issue.

## [2026.3.0] - 2026-03-15

### Added

- Expanded the vendored UniFi Network API package with typed models and endpoints for firewall policies, DNS policies, traffic matching lists, vouchers, supporting resources, and legacy site and device lookups
- Added a full vendored UniFi Protect client with endpoint coverage for cameras, sensors, lights, chimes, NVRs, viewers, live views, events, application files, RTSPS streams, talkback sessions, and WebSocket subscriptions
- Added enable and disable switches for user-defined UniFi Network firewall rules
- Added network device temperature sensors backed by legacy controller temperature data when available
- Added a new `script/` command suite for bootstrap, linting, testing, spell checking, hassfest validation, Home Assistant startup, config reset, and HACS sync

### Changed

- Vendored the upstream `unifi-official-api` project into `custom_components/unifi_insights/api`
- Switched the integration to use the local vendored API package instead of an external runtime dependency
- Reworked the remote cloud config flow so API keys discover accessible consoles first, then validate the selected console during setup, reauth, and reconfigure
- Updated the development environment and repository tooling for the new `script/` layout, Python 3.14, and Home Assistant 2026.3.1

### Fixed

- Fixed remote cloud setup and reconfiguration flows for API keys that can access multiple UniFi consoles by prompting for console selection instead of relying on manual console ID entry
- Fixed coordinator updates to merge legacy device temperature data without failing refreshes when legacy controller endpoints are unavailable
- Fixed diagnostics and tests to report and validate the vendored API package instead of the removed external dependency
- Fixed vendored WiFi broadcast updates to send full controller-compatible payloads on update
- Added `_attr_translation_key` to 18 Protect and network entity classes for proper HA name localization
- Removed unused SSDP discovery matchers from `manifest.json` (no `async_step_ssdp` handler existed)
- Downgraded auth, connection, and timeout error logging from `exception` to `warning` to reduce log noise on expected failures
- Deduplicated `_get_client_type` helper into `entity.py` as the shared `get_client_type` function
- Added `mac` and `mac_address` to diagnostics redaction set alongside the existing `macAddress` entry
- Fixed `update.py` `latest_version` to return the actual target firmware version instead of a static placeholder string
- Added complete entity translation entries in `strings.json` for switch, select, number, event, and update platforms
- Fixed pre-existing test failures in diagnostics, entity, and update test modules

### Removed

- Removed `unifi-official-api` from manifest and project dependency declarations
- Removed the legacy `scripts/` helpers in favor of the new `script/` tooling layout

### Technical

- Added a `py.typed` marker for the vendored API package and excluded the vendored subtree from first-party Ruff, mypy, and pre-commit checks
- Updated contributor and agent documentation to reference the vendored API package and the new development script workflow

## [2026.2.0] - 2026-01-22

### Changed

- **BREAKING**: Migrated from custom API implementation to `unifi-official-api` library
- Replaced `unifi_network_api.py` and `unifi_protect_api.py` with official library
- Updated coordinator to use library's pydantic models with `model_dump(by_alias=True)` for camelCase compatibility
- Improved data transformation layer for consistent field naming

### Added

#### UniFi Network

- **WiFi Network Switches**: Enable/disable WiFi networks directly from Home Assistant
- **Client Block/Allow Switches**: Block or allow network clients
- **Device Tracker Platform**: Track wireless and wired clients as device_tracker entities
- **Port Enable Switches**: Enable/disable switch ports
- **PoE Switches**: Control PoE on switch ports
- **Update Platform**: Firmware update entities for network devices

#### UniFi Protect

- **Event Platform**: Motion, ring, and smart detection events as event entities
- **Smart Detection Binary Sensors**: Person, vehicle, animal, and package detection
- **Camera Switches**: Microphone, privacy mode, status light, and high FPS mode controls
- **PTZ Controls**: Move to preset and patrol controls via services
- **Chime Services**: Volume, ringtone, and repeat time controls

#### Integration Features

- **Connection Type Selection**: Support for both Local (direct) and Remote (cloud) connections
- **Options Flow**: Configure WiFi and wired client tracking preferences
- **Reauth Flow**: Handle expired API keys gracefully
- **Reconfigure Flow**: Update connection settings without removing the integration
- **Repairs Platform**: Automatic repair suggestions for common issues
- **Diagnostics**: Enhanced diagnostic data for troubleshooting
- **Icons**: Custom icons for all entity types via icons.json

### Fixed

- Fixed `interfaces` field handling for list vs dict format from different API responses
- Fixed NVR storage sensors showing "Unavailable" when API doesn't provide storage data
- Fixed WiFi switch device info to avoid via_device warnings
- Fixed translations for all new entity types
- Fixed client type detection for wired/wireless client counting
- Fixed availability checks for all entity types

### Removed

- Removed custom `unifi_network_api.py` (replaced by `unifi-official-api` library)
- Removed custom `unifi_protect_api.py` (replaced by `unifi-official-api` library)
- Removed unused test files and API test results

### Technical

- Updated to Home Assistant 2026.1.2 compatibility
- 621 tests with 91.62% code coverage
- Full type hints with `py.typed` marker
- Comprehensive linting with ruff/black
- Pre-commit hooks for code quality

## [2025.06.05] - 2025-06-05

### Added

- Initial release of UniFi Insights integration
- Basic sensor support for UniFi Network devices
- CPU, memory, uptime, and throughput sensors
- Device status binary sensors
- Basic camera support for UniFi Protect
- Light control for UniFi Protect lights
- Number entities for camera/light settings
- Select entities for recording modes and video modes

[Unreleased]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.8.2...HEAD
[2026.8.2]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.8.1...v2026.8.2
[2026.8.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.8.0...v2026.8.1
[2026.8.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.4...v2026.8.0
[2026.6.4]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.3...v2026.6.4
[2026.6.3]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.2...v2026.6.3
[2026.6.2]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.1...v2026.6.2
[2026.6.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.0...v2026.6.1
[2026.6.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.5.0...v2026.6.0
[2026.5.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.4.1...v2026.5.0
[2026.4.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.4.0...v2026.4.1
[2026.4.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.2...v2026.4.0
[2026.3.2]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.1...v2026.3.2
[2026.3.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.0...v2026.3.1
[2026.3.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.2.0...v2026.3.0
[2026.2.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2025.06.05...v2026.2.0
[2025.06.05]: https://github.com/ruaan-deysel/ha-unifi-insights/releases/tag/v2025.06.05
