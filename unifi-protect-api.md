# UniFi Protect API Documentation

Version: 6.1.78

## Table of Contents

- [Information about Application](#information-about-application)
- [Viewer Information & Management](#viewer-information--management)
- [Live View Management](#live-view-management)
- [WebSocket Updates](#websocket-updates)
- [Camera PTZ Control & Management](#camera-ptz-control--management)
- [Alarm Manager Integration](#alarm-manager-integration)
- [Light Information & Management](#light-information--management)
- [Camera Information & Management](#camera-information--management)
- [Sensor Information & Management](#sensor-information--management)
- [NVR Information & Management](#nvr-information--management)
- [Device Asset File Management](#device-asset-file-management)
- [Chime Information & Management](#chime-information--management)

---

## Information about Application

### Get Application Information

Get generic information about the Protect application.

**Endpoint:** `GET /v1/meta/info`

**Response:** `200 Success`

**Example Response:**

```json
{
  "applicationVersion": "1.0.0"
}
```

---

## Viewer Information & Management

### Get Viewer Details

Get detailed information about a specific viewer.

**Endpoint:** `GET /v1/viewers/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (viewerId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of viewer |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "viewer",
  "state": "CONNECTED",
  "name": "string",
  "liveview": "66d025b301ebc903e80003ea",
  "streamLimit": 0
}
```

---

### Patch Viewer Settings

Patch the settings for a specific viewer.

**Endpoint:** `PATCH /v1/viewers/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (viewerId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of viewer |

**Request Body:**

```json
{
  "name": "string",
  "liveview": "66d025b301ebc903e80003ea"
}
```

**Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (name) | The name of the model |
| `liveview` | liveviewId (string) or null | Live view identifier |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "viewer",
  "state": "CONNECTED",
  "name": "string",
  "liveview": "66d025b301ebc903e80003ea",
  "streamLimit": 0
}
```

---

### Get All Viewers

Get detailed information about all viewers.

**Endpoint:** `GET /v1/viewers`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "viewer",
    "state": "CONNECTED",
    "name": "string",
    "liveview": "66d025b301ebc903e80003ea",
    "streamLimit": 0
  }
]
```

---

## Live View Management

### Get Live View Details

Get detailed information about a specific live view.

**Endpoint:** `GET /v1/liveviews/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (liveviewId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of liveview |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "liveview",
  "name": "string",
  "isDefault": true,
  "isGlobal": true,
  "owner": "66d025b301ebc903e80003ea",
  "layout": 1,
  "slots": [{}]
}
```

---

### Patch Live View Configuration

Patch the configuration about a specific live view.

**Endpoint:** `PATCH /v1/liveviews/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (liveviewId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of liveview |

**Request Body:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "liveview",
  "name": "string",
  "isDefault": true,
  "isGlobal": true,
  "owner": "66d025b301ebc903e80003ea",
  "layout": 1,
  "slots": [{}]
}
```

**Request Fields:**

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | string (liveviewId) | - | The primary key of liveview (Required) |
| `modelKey` | string (liveviewModelKey) | Value: "liveview" | The model key of the liveview (Required) |
| `name` | string | - | The name of this live view (Required) |
| `isDefault` | boolean | - | Whether this live view is the default one for all viewers (Required) |
| `isGlobal` | boolean | - | Whether this live view is global and available system-wide to all users (Required) |
| `owner` | string (userId) | - | The primary key of user (Required) |
| `layout` | number | [1..26] | The number of slots this live view contains (Required) |
| `slots` | Array of objects | - | List of cameras visible in each given slot (Required) |

**Response:** `200 Success`

---

### Get All Live Views

Get detailed information about all live views.

**Endpoint:** `GET /v1/liveviews`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "liveview",
    "name": "string",
    "isDefault": true,
    "isGlobal": true,
    "owner": "66d025b301ebc903e80003ea",
    "layout": 1,
    "slots": []
  }
]
```

---

### Create Live View

Create a new live view.

**Endpoint:** `POST /v1/liveviews`

**Request Body:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "liveview",
  "name": "string",
  "isDefault": true,
  "isGlobal": true,
  "owner": "66d025b301ebc903e80003ea",
  "layout": 1,
  "slots": [{}]
}
```

**Response:** `200 Success`

---

## WebSocket Updates

### Get Update Messages About Devices

A WebSocket subscription which broadcasts all changes happening to Protect-managed hardware devices.

**Endpoint:** `GET /v1/subscribe/devices`

**Response:** `200 Success`

**Example Response (add event):**

```json
{
  "type": "add",
  "item": {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "nvr",
    "name": "string",
    "doorbellSettings": {}
  }
}
```

---

### Get Protect Event Messages

A WebSocket subscription that broadcasts Protect events.

**Endpoint:** `GET /v1/subscribe/events`

**Response:** `200 Success`

**Example Response (add event):**

```json
{
  "type": "add",
  "item": {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "event",
    "type": "ring",
    "start": 1445408038748,
    "end": 1445408048748,
    "device": "66d025b301ebc903e80003ea"
  }
}
```

---

## Camera PTZ Control & Management

### Start a Camera PTZ Patrol

Start a camera PTZ patrol.

**Endpoint:** `POST /v1/cameras/{id}/ptz/patrol/start/{slot}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |
| `slot` | string (activePatrolSlotString) | Yes | `0`, `1`, `2`, `3`, `4` | The slot number (0-4) of the patrol |

**Response:** `204 The camera PTZ patrol was started successfully`

---

### Stop Active Camera PTZ Patrol

Stop active camera PTZ patrol.

**Endpoint:** `POST /v1/cameras/{id}/ptz/patrol/stop`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Response:** `204 The camera PTZ patrol was stopped successfully`

---

### Move PTZ Camera to Preset

Adjust the PTZ camera position to a specified preset.

**Endpoint:** `POST /v1/cameras/{id}/ptz/goto/{slot}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |
| `slot` | string | Yes | `-1`, `0`, `2`, `8`, `9` | The slot number (0-4) of the preset to move the camera to |

**Response:** `204 The PTZ camera was moved to the given preset successfully`

---

## Alarm Manager Integration

### Send a Webhook to the Alarm Manager

Send a webhook to the alarm manager to trigger configured alarms.

**Endpoint:** `POST /v1/alarm-manager/webhook/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (alarmTriggerId) | Yes | `AnyRandomString` | User defined string used to trigger only specific alarms. Alarm should be configured with the same ID to be triggered. |

**Response:** `204 Webhook was sent to alarm manager successfully`

**Error Response (400):**

```json
{
  "error": "'id' is required",
  "name": "BAD_REQUEST",
  "cause": {
    "error": "Unexpected functionality error",
    "name": "UNKNOWN_ERROR"
  }
}
```

---

## Light Information & Management

### Get Light Details

Get detailed information about a specific light.

**Endpoint:** `GET /v1/lights/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (lightId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of light |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "light",
  "state": "CONNECTED",
  "name": "string",
  "lightModeSettings": {
    "mode": "always",
    "enableAt": "fulltime"
  },
  "lightDeviceSettings": {
    "isIndicatorEnabled": true,
    "pirDuration": 0,
    "pirSensitivity": 100,
    "ledLevel": 1
  },
  "isDark": true,
  "isLightOn": true,
  "isLightForceEnabled": true,
  "lastMotion": 0,
  "isPirMotionDetected": true,
  "camera": "66d025b301ebc903e80003ea"
}
```

---

### Patch Light Settings

Patch the settings for a specific light.

**Endpoint:** `PATCH /v1/lights/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (lightId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of light |

**Request Body:**

```json
{
  "name": "string",
  "isLightForceEnabled": true,
  "lightModeSettings": {
    "mode": "always",
    "enableAt": "fulltime"
  },
  "lightDeviceSettings": {
    "isIndicatorEnabled": true,
    "pirDuration": 0,
    "pirSensitivity": 100,
    "ledLevel": 1
  }
}
```

**Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (name) | The name of the model |
| `isLightForceEnabled` | boolean | Whether the light has its main LED currently force-enabled |
| `lightModeSettings` | object | Settings for when and how your light gets activated |
| `lightDeviceSettings` | object | Hardware settings for light device |

**Response:** `200 Success`

---

### Get All Lights

Get detailed information about all lights.

**Endpoint:** `GET /v1/lights`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "light",
    "state": "CONNECTED",
    "name": "string",
    "lightModeSettings": {},
    "lightDeviceSettings": {},
    "isDark": true,
    "isLightOn": true,
    "isLightForceEnabled": true,
    "lastMotion": 0,
    "isPirMotionDetected": true,
    "camera": "66d025b301ebc903e80003ea"
  }
]
```

---

## Camera Information & Management

### Get Camera Details

Get detailed information about a specific camera.

**Endpoint:** `GET /v1/cameras/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "camera",
  "state": "CONNECTED",
  "name": "string",
  "isMicEnabled": true,
  "osdSettings": {
    "isNameEnabled": true,
    "isDateEnabled": true,
    "isLogoEnabled": true,
    "isDebugEnabled": true,
    "overlayLocation": "topLeft"
  },
  "ledSettings": {
    "isEnabled": true
  },
  "lcdMessage": {
    "type": "LEAVE_PACKAGE_AT_DOOR",
    "resetAt": 0,
    "text": "string"
  },
  "micVolume": 100,
  "activePatrolSlot": 0,
  "videoMode": "default",
  "hdrType": "auto",
  "featureFlags": {
    "supportFullHdSnapshot": true,
    "hasHdr": true,
    "smartDetectTypes": [],
    "smartDetectAudioTypes": [],
    "videoModes": [],
    "hasMic": true,
    "hasLedStatus": true,
    "hasSpeaker": true
  },
  "smartDetectSettings": {
    "objectTypes": [],
    "audioTypes": []
  }
}
```

---

### Patch Camera Settings

Patch the settings for a specific camera.

**Endpoint:** `PATCH /v1/cameras/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Request Body:**

```json
{
  "name": "string",
  "osdSettings": {
    "isNameEnabled": true,
    "isDateEnabled": true,
    "isLogoEnabled": true,
    "isDebugEnabled": true,
    "overlayLocation": "topLeft"
  },
  "ledSettings": {
    "isEnabled": true
  },
  "lcdMessage": {
    "type": "DO_NOT_DISTURB",
    "resetAt": 0
  },
  "micVolume": 100,
  "videoMode": "default",
  "hdrType": "auto",
  "smartDetectSettings": {
    "objectTypes": [],
    "audioTypes": []
  }
}
```

**Request Fields:**

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `name` | string | - | The name of the camera |
| `osdSettings` | object | - | On Screen Display settings |
| `ledSettings` | object | - | LED settings |
| `lcdMessage` | object | - | LCD message settings |
| `micVolume` | number | [0..100] | Mic volume: a number from 0-100 |
| `videoMode` | string | Enum: "default", "highFps", "sport", "slowShutter", "lprReflex", "lprNoneReflex" | Current video mode of the camera |
| `hdrType` | string | Enum: "auto", "on", "off" | High Dynamic Range (HDR) mode setting |
| `smartDetectSettings` | object | - | Smart detection settings for the camera |

**Response:** `200 Success`

---

### Get All Cameras

Get detailed information about all cameras.

**Endpoint:** `GET /v1/cameras`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "camera",
    "state": "CONNECTED",
    "name": "string",
    "isMicEnabled": true,
    "osdSettings": {},
    "ledSettings": {},
    "lcdMessage": {},
    "micVolume": 100,
    "activePatrolSlot": 0,
    "videoMode": "default",
    "hdrType": "auto",
    "featureFlags": {},
    "smartDetectSettings": {}
  }
]
```

---

### Create RTSPS Streams for Camera

Returns RTSPS stream URLs for specified quality levels.

**Endpoint:** `POST /v1/cameras/{id}/rtsps-stream`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Request Body:**

```json
{
  "qualities": [
    "high",
    "medium"
  ]
}
```

**Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `qualities` | Array of strings (non-empty) | Array of quality levels: "high", "medium", "low", "package" (Required) |

**Response:** `200 Success`

**Example Response:**

```json
{
  "high": "rtsps://192.168.1.1:7441/5nPr7RCmueGTKMP7?enableSrtp",
  "medium": "rtsps://192.168.1.1:7441/AbUgnDb5IqIEMidk?enableSrtp"
}
```

---

### Delete Camera RTSPS Stream

Remove the RTSPS stream for a specified camera.

**Endpoint:** `DELETE /v1/cameras/{id}/rtsps-stream`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Query Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `qualities` | Array of strings | Yes | `qualities=high&qualities=medium` | The array of quality levels for the RTSPS streams to be removed |

**Response:** `204 RTSPS stream successfully removed`

---

### Get RTSPS Streams for Camera

Returns existing RTSPS stream URLs for camera.

**Endpoint:** `GET /v1/cameras/{id}/rtsps-stream`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Response:** `200 Success`

**Example Response:**

```json
{
  "high": "rtsps://192.168.1.1:7441/5nPr7RCmueGTKMP7?enableSrtp",
  "medium": "rtsps://192.168.1.1:7441/AbUgnDb5IqIEMidk?enableSrtp",
  "low": null,
  "package": null
}
```

---

### Get Camera Snapshot

Get a snapshot image from a specific camera.

**Endpoint:** `GET /v1/cameras/{id}/snapshot`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `highQuality` | string (forceHighQuality) | "false" | Enum: "true", "false". Whether to force 1080P or higher resolution snapshot |

**Response:** `200 Camera snapshot`

---

### Permanently Disable Camera Microphone

Disable the microphone for a specific camera. This action cannot be undone unless the camera is reset.

**Endpoint:** `POST /v1/cameras/{id}/disable-mic-permanently`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Response:** `200 Success`

---

### Create Talkback Session for Camera

Returns the talkback stream URL and audio configuration for a specific camera.

**Endpoint:** `POST /v1/cameras/{id}/talkback-session`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (cameraId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of camera |

**Response:** `200 Success`

**Example Response:**

```json
{
  "url": "rtp://192.168.1.123:7004",
  "codec": "opus",
  "samplingRate": 24000,
  "bitsPerSample": 16
}
```

---

## Sensor Information & Management

### Get Sensor Details

Get detailed information about a specific sensor.

**Endpoint:** `GET /v1/sensors/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (sensorId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of sensor |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "sensor",
  "state": "CONNECTED",
  "name": "string",
  "mountType": "garage",
  "batteryStatus": {
    "percentage": 0,
    "isLow": true
  },
  "stats": {
    "light": {},
    "humidity": {},
    "temperature": {}
  },
  "lightSettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": 1,
    "highThreshold": 0
  },
  "humiditySettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": 1,
    "highThreshold": 0
  },
  "temperatureSettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": -39,
    "highThreshold": 0
  },
  "isOpened": true,
  "openStatusChangedAt": 0,
  "isMotionDetected": true,
  "motionDetectedAt": 0,
  "motionSettings": {
    "isEnabled": true,
    "sensitivity": 100
  },
  "alarmTriggeredAt": 0,
  "alarmSettings": {
    "isEnabled": true
  },
  "leakDetectedAt": 0,
  "externalLeakDetectedAt": 0,
  "leakSettings": {
    "isInternalEnabled": true,
    "isExternalEnabled": true
  },
  "tamperingDetectedAt": 0
}
```

---

### Patch Sensor Settings

Patch the settings for a specific sensor.

**Endpoint:** `PATCH /v1/sensors/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (sensorId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of sensor |

**Request Body:**

```json
{
  "name": "string",
  "lightSettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": 1,
    "highThreshold": 0
  },
  "humiditySettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": 1,
    "highThreshold": 0
  },
  "temperatureSettings": {
    "isEnabled": true,
    "margin": 0,
    "lowThreshold": -39,
    "highThreshold": 0
  },
  "motionSettings": {
    "isEnabled": true,
    "sensitivity": 100
  },
  "alarmSettings": {
    "isEnabled": true
  }
}
```

**Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (name) | The name of the model |
| `lightSettings` | object | Ambient light sensor settings |
| `humiditySettings` | object | Relative humidity sensor settings |
| `temperatureSettings` | object | Temperature sensor settings |
| `motionSettings` | object | Motion sensor settings |
| `alarmSettings` | object | Smoke and carbon monoxide alarm sensor settings |

**Response:** `200 Success`

---

### Get All Sensors

Get detailed information about all sensors.

**Endpoint:** `GET /v1/sensors`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "sensor",
    "state": "CONNECTED",
    "name": "string",
    "mountType": "garage",
    "batteryStatus": {},
    "stats": {},
    "lightSettings": {},
    "humiditySettings": {},
    "temperatureSettings": {},
    "isOpened": true,
    "openStatusChangedAt": 0,
    "isMotionDetected": true,
    "motionDetectedAt": 0,
    "motionSettings": {},
    "alarmTriggeredAt": 0,
    "alarmSettings": {},
    "leakDetectedAt": 0,
    "externalLeakDetectedAt": 0,
    "leakSettings": {},
    "tamperingDetectedAt": 0
  }
]
```

---

## NVR Information & Management

### Get NVR Details

Get detailed information about the NVR.

**Endpoint:** `GET /v1/nvrs`

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "nvr",
  "name": "string",
  "doorbellSettings": {
    "defaultMessageText": "string",
    "defaultMessageResetTimeoutMs": 0,
    "customMessages": [],
    "customImages": []
  }
}
```

---

## Device Asset File Management

### Upload Device Asset File

Upload a new device asset file.

**Endpoint:** `POST /v1/files/{fileType}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileType` | string (assetFileType) | Yes | Device asset file type. Value: "animations" |

**Request Body (multipart/form-data):**

A binary file with one of these MIME types:
- image/gif
- image/jpeg
- image/png
- audio/mpeg
- audio/mp4
- audio/wave
- audio/x-caf

**Response:** `200 Processed and persisted device asset`

**Example Response:**

```json
{
  "name": "string",
  "type": "animations",
  "originalName": "string",
  "path": "string"
}
```

---

### Get Device Asset Files

Get a list of all device asset files.

**Endpoint:** `GET /v1/files/{fileType}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileType` | string (assetFileType) | Yes | Device asset file type. Value: "animations" |

**Response:** `200 Device asset list`

**Example Response:**

```json
[
  {
    "name": "string",
    "type": "animations",
    "originalName": "string",
    "path": "string"
  }
]
```

---

## Chime Information & Management

### Get Chime Details

Get detailed information about a specific chime.

**Endpoint:** `GET /v1/chimes/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (chimeId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of chime |

**Response:** `200 Success`

**Example Response:**

```json
{
  "id": "66d025b301ebc903e80003ea",
  "modelKey": "chime",
  "state": "CONNECTED",
  "name": "string",
  "cameraIds": [
    "66d025b301ebc903e80003ea"
  ],
  "ringSettings": [{}]
}
```

---

### Patch Chime Settings

Patch the settings for a specific chime.

**Endpoint:** `PATCH /v1/chimes/{id}`

**Path Parameters:**

| Parameter | Type | Required | Examples | Description |
|-----------|------|----------|----------|-------------|
| `id` | string (chimeId) | Yes | `66d025b301ebc903e80003ea`, `672094f900e26303e800062a` | The primary key of chime |

**Request Body:**

```json
{
  "name": "string",
  "cameraIds": [
    "66d025b301ebc903e80003ea"
  ],
  "ringSettings": [{}]
}
```

**Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | The name of the chime |
| `cameraIds` | Array of strings (cameraId) | The list of (doorbell-only) cameras which this chime is paired to |
| `ringSettings` | Array of objects | List of custom ringtone settings for cameras paired to this chime |

**Response:** `200 Success`

---

### Get All Chimes

Get detailed information about all chimes.

**Endpoint:** `GET /v1/chimes`

**Response:** `200 Success`

**Example Response:**

```json
[
  {
    "id": "66d025b301ebc903e80003ea",
    "modelKey": "chime",
    "state": "CONNECTED",
    "name": "string",
    "cameraIds": [],
    "ringSettings": []
  }
]
```

---

## Error Responses

All endpoints use a generic error response format:

**Default Error Response:**

```json
{
  "error": "Unexpected API error occurred",
  "name": "API_ERROR",
  "cause": {
    "error": "Unexpected functionality error",
    "name": "UNKNOWN_ERROR"
  }
}
```

---

## Additional Resources

For more information about UniFi Protect and integration guides, refer to the official UniFi documentation.
