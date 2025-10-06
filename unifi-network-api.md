# UniFi Network API Documentation

Version: 9.4.19

## Table of Contents

- [Getting Started](#getting-started)
- [Filtering](#filtering)
- [Errors](#errors)
- [About Application](#about-application)
- [Sites](#sites)
- [UniFi Devices](#unifi-devices)
- [Clients](#clients)
- [Hotspot Vouchers](#hotspot-vouchers)

---

## Getting Started

### Introduction

Each UniFi Application has its own API endpoints running locally on each site, offering detailed analytics and control related to that specific application. For a single endpoint with high-level insights across all your UniFi sites, refer to the UniFi Site Manager API.

### Authentication and Request Format

An API Key is a unique identifier used to authenticate API requests. To generate API Keys and view an example of the API Request Format, visit the Integrations section of your UniFi application.

---

## Filtering

Some GET and DELETE endpoints support filtering using the `filter` query parameter. Each endpoint supporting filtering will have a detailed list of filterable properties, their types, and allowed functions.

### Filtering Syntax

Filtering follows a structured, URL-safe syntax with three types of expressions.

#### 1. Property Expressions

Apply functions to an individual property using the form `<property>.<function>(<arguments>)`, where argument values are separated by commas.

**Examples:**
- `id.eq(123)` checks if id is equal to 123
- `name.isNotNull()` checks if name is not null
- `createdAt.in(2025-01-01, 2025-01-05)` checks if createdAt is either 2025-01-01 or 2025-01-05

#### 2. Compound Expressions

Combine two or more expressions with logical operators using the form `<logical-operator>(<expressions>)`, where expressions are separated by commas.

**Examples:**
- `and(name.isNull(), createdAt.gt(2025-01-01))` checks if name is null and createdAt is greater than 2025-01-01
- `or(name.isNull(), expired.isNull(), expiresAt.isNull())` checks if any of name, expired, or expiresAt is null

#### 3. Negation Expressions

Negate any other expressions using the form `not(<expression>)`.

**Example:**
- `not(name.like('guest*'))` matches all values except those that start with guest

### Filterable Property Types

The table below lists all supported property types.

| Type | Examples | Syntax |
|------|----------|--------|
| STRING | `'Hello, ''World''!'` | Must be wrapped in single quotes. To escape a single quote, use another single quote. |
| NUMBER | `123`, `123.321` | Must start with a digit. Can include a decimal point (.). |
| TIMESTAMP | `2025-01-29`, `2025-01-29T12:39:11Z` | Must follow ISO 8601 format (date or date-time). |
| BOOLEAN | `true`, `false` | Can be true or false. |
| UUID | `550e8400-e29b-41d4-a716-446655440000` | Must be a valid UUID format (8-4-4-4-12). |

### Filtering Functions

The table below lists available filtering functions, their arguments, and applicable property types:

| Function | Arguments | Semantics | Supported property types |
|----------|-----------|-----------|-------------------------|
| `isNull` | 0 | is null | all types |
| `isNotNull` | 0 | is not null | all types |
| `eq` | 1 | equals | all types |
| `ne` | 1 | not equals | all types |
| `gt` | 1 | greater than | STRING, NUMBER, TIMESTAMP, UUID |
| `ge` | 1 | greater than or equals | STRING, NUMBER, TIMESTAMP, UUID |
| `lt` | 1 | less than | STRING, NUMBER, TIMESTAMP, UUID |
| `le` | 1 | less than or equals | STRING, NUMBER, TIMESTAMP, UUID |
| `like` | 1 | matches pattern | STRING |
| `in` | 1 or more | one of | STRING, NUMBER, TIMESTAMP, UUID |
| `notIn` | 1 or more | not one of | STRING, NUMBER, TIMESTAMP, UUID |

### Pattern Matching (like Function)

The `like` function allows matching string properties using simple patterns:

- `.` matches any single character. Example: `type.like('type.')` matches `type1`, but not `type100`
- `*` matches any number of characters. Example: `name.like('guest*')` matches `guest1` and `guest100`
- `\` is used to escape `.` and `*`

---

## Errors

All endpoints use the same generic error message format:

### Error Message Structure

| Field | Type | Description |
|-------|------|-------------|
| `statusCode` | integer (int32) | HTTP status code |
| `statusName` | string | Status name |
| `message` | string | Error message |
| `timestamp` | string (date-time) | Time of error |
| `requestPath` | string | Request path |
| `requestId` | string (uuid) | Request ID for tracking |

In case of Internal Server Error (code = 500), request ID can be used to track down the error in the server log.

**Example Error Response:**

```json
{
  "statusCode": 400,
  "statusName": "UNAUTHORIZED",
  "message": "Missing credentials",
  "timestamp": "2024-11-27T08:13:46.966Z",
  "requestPath": "/integration/v1/sites/123",
  "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

---

## About Application

### Get Application Info

Retrieve general information about the UniFi Network application.

**Endpoint:** `GET /v1/info`

**Response:** `200 OK`

**Example Response:**

```json
{
  "applicationVersion": "9.1.0"
}
```

---

## Sites

### List Local Sites

Retrieve a paginated list of local sites managed by this Network application. Site ID is required for other UniFi Network API calls.

**Endpoint:** `GET /v1/sites`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | number (int32) >= 0 | 0 | Pagination offset |
| `limit` | number (int32) [0..200] | 25 | Results per page |
| `filter` | string | - | Filter expression |

**Response:** `200 OK`

**Example Response:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [{}]
}
```

---

## UniFi Devices

### Execute Port Action

Perform an action on a specific device port. The request body must include the action name and any applicable input arguments.

**Endpoint:** `POST /v1/sites/{siteId}/devices/{deviceId}/interfaces/ports/{portIdx}/actions`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `deviceId` | string (uuid) | Yes | Device identifier |
| `portIdx` | integer (int32) | Yes | Port index |

**Request Body:**

```json
{
  "action": "POWER_CYCLE"
}
```

**Actions:**
- `POWER_CYCLE`

**Response:** `200 OK`

---

### Execute Device Action

Perform an action on a specific adopted device. The request body must include the action name and any applicable input arguments.

**Endpoint:** `POST /v1/sites/{siteId}/devices/{deviceId}/actions`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `deviceId` | string (uuid) | Yes | Device identifier |

**Request Body:**

```json
{
  "action": "RESTART"
}
```

**Actions:**
- `RESTART`

**Response:** `200 OK`

---

### List Devices

Retrieve a paginated list of all adopted devices on a site, including basic device information.

**Endpoint:** `GET /v1/sites/{siteId}/devices`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | number (int32) >= 0 | 0 | Pagination offset |
| `limit` | number (int32) [0..200] | 25 | Results per page |

**Response:** `200 OK`

**Example Response:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [{}]
}
```

---

### Get Device Details

Retrieve detailed information about a specific adopted device, including firmware versioning, uplink state, details about device features and interfaces (ports, radios) and other key attributes.

**Endpoint:** `GET /v1/sites/{siteId}/devices/{deviceId}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `deviceId` | string (uuid) | Yes | Device identifier |

**Response:** `200 OK`

**Example Response:**

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "name": "IW HD",
  "model": "UHDIW",
  "supported": true,
  "macAddress": "94:2a:6f:26:c6:ca",
  "ipAddress": "192.168.1.55",
  "state": "ONLINE",
  "firmwareVersion": "6.6.55",
  "firmwareUpdatable": true,
  "adoptedAt": "2019-08-24T14:15:22Z",
  "provisionedAt": "2019-08-24T14:15:22Z",
  "configurationId": "7596498d2f367dc2",
  "uplink": {
    "deviceId": "4de4adb9-21ee-47e3-aeb4-8cf8ed6c109a"
  },
  "features": {
    "switching": null,
    "accessPoint": null
  },
  "interfaces": {
    "ports": [],
    "radios": []
  }
}
```

---

### Get Latest Device Statistics

Retrieve the latest real-time statistics of a specific adopted device, such as uptime, data transmission rates, CPU and memory utilization.

**Endpoint:** `GET /v1/sites/{siteId}/devices/{deviceId}/statistics/latest`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `deviceId` | string (uuid) | Yes | Device identifier |

**Response:** `200 OK`

**Example Response:**

```json
{
  "uptimeSec": 0,
  "lastHeartbeatAt": "2019-08-24T14:15:22Z",
  "nextHeartbeatAt": "2019-08-24T14:15:22Z",
  "loadAverage1Min": 0.1,
  "loadAverage5Min": 0.1,
  "loadAverage15Min": 0.1,
  "cpuUtilizationPct": 0.1,
  "memoryUtilizationPct": 0.1,
  "uplink": {
    "txRateBps": 0,
    "rxRateBps": 0
  },
  "interfaces": {
    "radios": []
  }
}
```

---

## Clients

### Execute Client Action

Perform an action on a specific connected client. The request body must include the action name and any applicable input arguments.

**Endpoint:** `POST /v1/sites/{siteId}/clients/{clientId}/actions`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `clientId` | string (uuid) | Yes | Client identifier |

**Request Body:**

```json
{
  "action": "AUTHORIZE_GUEST_ACCESS",
  "timeLimitMinutes": 1,
  "dataUsageLimitMBytes": 1,
  "rxRateLimitKbps": 2,
  "txRateLimitKbps": 2
}
```

**Actions:**
- `AUTHORIZE_GUEST_ACCESS`

**Action Parameters:**

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `timeLimitMinutes` | integer (int64) | [1..1000000] | (Optional) How long (in minutes) the guest will be authorized to access the network. If not specified, the default limit is used from the site settings |
| `dataUsageLimitMBytes` | integer (int64) | [1..1048576] | (Optional) Data usage limit in megabytes |
| `rxRateLimitKbps` | integer (int64) | [2..100000] | (Optional) Download rate limit in kilobits per second |
| `txRateLimitKbps` | integer (int64) | [2..100000] | (Optional) Upload rate limit in kilobits per second |

**Response:** `200 OK`

**Example Response:**

```json
{
  "action": "AUTHORIZE_GUEST_ACCESS",
  "revokedAuthorization": {
    "authorizedAt": "2019-08-24T14:15:22Z",
    "authorizationMethod": "VOUCHER",
    "expiresAt": "2019-08-24T14:15:22Z",
    "dataUsageLimitMBytes": 1024,
    "rxRateLimitKbps": 1000,
    "txRateLimitKbps": 1000,
    "usage": {}
  },
  "grantedAuthorization": {
    "authorizedAt": "2019-08-24T14:15:22Z",
    "authorizationMethod": "VOUCHER",
    "expiresAt": "2019-08-24T14:15:22Z",
    "dataUsageLimitMBytes": 1024,
    "rxRateLimitKbps": 1000,
    "txRateLimitKbps": 1000,
    "usage": {}
  }
}
```

---

### List Connected Clients

Retrieve a paginated list of all connected clients on a site, including physical devices (computers, smartphones) and active VPN connections.

**Endpoint:** `GET /v1/sites/{siteId}/clients`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | number (int32) >= 0 | 0 | Pagination offset |
| `limit` | number (int32) [0..200] | 25 | Results per page |
| `filter` | string | - | Filter expression |

**Response:** `200 OK`

**Example Response:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [{}]
}
```

---

### Get Connected Client Details

Retrieve detailed information about a specific connected client, including name, IP address, MAC address, connection type and access information.

**Endpoint:** `GET /v1/sites/{siteId}/clients/{clientId}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `clientId` | string (uuid) | Yes | Client identifier |

**Response:** `200 OK`

**Example Response (WIRED):**

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "name": "string",
  "connectedAt": "2019-08-24T14:15:22Z",
  "ipAddress": "string",
  "access": {
    "type": "string"
  },
  "type": "WIRED",
  "macAddress": "string",
  "uplinkDeviceId": "c2692e57-1e51-4519-bb90-c2bdad5882ca"
}
```

---

## Hotspot Vouchers

### List Vouchers

Retrieve a paginated list of Hotspot vouchers.

**Endpoint:** `GET /v1/sites/{siteId}/hotspot/vouchers`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | number (int32) >= 0 | 0 | Pagination offset |
| `limit` | number (int32) [0..1000] | 100 | Results per page |
| `filter` | string | - | Filter expression |

**Response:** `200 OK`

**Example Response:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [{}]
}
```

---

### Generate Vouchers

Create one or more Hotspot vouchers.

**Endpoint:** `POST /v1/sites/{siteId}/hotspot/vouchers`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |

**Request Body:**

```json
{
  "count": "1",
  "name": "string",
  "authorizedGuestLimit": 1,
  "timeLimitMinutes": 1,
  "dataUsageLimitMBytes": 1,
  "rxRateLimitKbps": 2,
  "txRateLimitKbps": 2
}
```

**Request Parameters:**

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `count` | integer (int32) | [1..1000] | Number of vouchers to generate (Default: 1) |
| `name` | string | - | Voucher note, duplicated across all generated vouchers (Required) |
| `authorizedGuestLimit` | integer (int64) | >= 1 | (Optional) Limit for how many different guests can use the same voucher to authorize network access |
| `timeLimitMinutes` | integer (int64) | [1..1000000] | How long (in minutes) the voucher will provide access to the network since authorization of the first guest (Required) |
| `dataUsageLimitMBytes` | integer (int64) | [1..1048576] | (Optional) Data usage limit in megabytes |
| `rxRateLimitKbps` | integer (int64) | [2..100000] | (Optional) Download rate limit in kilobits per second |
| `txRateLimitKbps` | integer (int64) | [2..100000] | (Optional) Upload rate limit in kilobits per second |

**Response:** `201 Created`

**Example Response:**

```json
{
  "vouchers": [{}]
}
```

---

### Delete Vouchers

Remove Hotspot vouchers based on the specified filter criteria.

**Endpoint:** `DELETE /v1/sites/{siteId}/hotspot/vouchers`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filter` | string | Yes | Filter expression |

**Response:** `200 OK`

**Example Response:**

```json
{
  "vouchersDeleted": 0
}
```

---

### Get Voucher Details

Retrieve details of a specific Hotspot voucher.

**Endpoint:** `GET /v1/sites/{siteId}/hotspot/vouchers/{voucherId}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `voucherId` | string (uuid) | Yes | Voucher identifier |

**Response:** `200 OK`

**Example Response:**

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "createdAt": "2019-08-24T14:15:22Z",
  "name": "hotel-guest",
  "code": 4861409510,
  "authorizedGuestLimit": 1,
  "authorizedGuestCount": 0,
  "activatedAt": "2019-08-24T14:15:22Z",
  "expiresAt": "2019-08-24T14:15:22Z",
  "expired": true,
  "timeLimitMinutes": 1440,
  "dataUsageLimitMBytes": 1024,
  "rxRateLimitKbps": 1000,
  "txRateLimitKbps": 1000
}
```

---

### Delete Voucher

Remove a specific Hotspot voucher.

**Endpoint:** `DELETE /v1/sites/{siteId}/hotspot/vouchers/{voucherId}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `siteId` | string (uuid) | Yes | Site identifier |
| `voucherId` | string (uuid) | Yes | Voucher identifier |

**Response:** `200 OK`

**Example Response:**

```json
{
  "vouchersDeleted": 0
}
```

---

## Additional Resources

For more information about the UniFi Site Manager API and cross-site management, refer to the official UniFi documentation.
