---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Debug a data coordinator issue in UniFi Insights"
---

# Debug Coordinator Issue

Your goal is to diagnose and fix an issue with the UniFi Insights data coordinator system.

If not provided, ask for:

- What symptoms are observed (entities unavailable, stale data, errors in logs)
- Which coordinator is affected (config, device, protect, facade)
- Any error messages from logs
- Whether the issue is intermittent or consistent

## Diagnostic Checklist

### 1. Check coordinator data flow

```
API Clients → Config Coordinator → Device Coordinator → Protect Coordinator → Facade → Entities
```

Identify where in the chain the data breaks.

### 2. Check error handling

- Is `UpdateFailed` raised correctly for transient errors?
- Is `ConfigEntryAuthFailed` raised for auth issues?
- Are exceptions being silently swallowed?

### 3. Check data schema

- Is coordinator data structured consistently?
- Are entity lookups finding the expected keys?
- Has `data_transforms.py` mapping changed?

### 4. Check polling and timing

- Default interval: 30 seconds
- WebSocket for Protect events
- Exponential backoff on failures
- Stale device cleanup timing

### 5. Check multi-coordinator dependencies

- Config coordinator must complete before device coordinator
- Device coordinator must complete before protect coordinator
- Facade aggregates all coordinator data

### 6. Common issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All entities unavailable | Coordinator failing to update | Check `_async_update_data` exceptions |
| Stale data | Polling not triggering | Check update interval and HA scheduler |
| Missing devices | Stale cleanup too aggressive | Check device ID tracking |
| Protect entities missing | Protect client not initialized | Check local-only requirement |
| Auth failures loop | Reauth not triggering | Ensure `ConfigEntryAuthFailed` is raised |

### 7. Log analysis

Check `config/home-assistant.log` for:
- `UpdateFailed` messages
- Connection timeout errors
- Authentication errors
- Data parsing errors
