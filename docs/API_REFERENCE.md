# API Reference

Complete reference for the TouchDesigner WebSocket Control API

---

## HTTP API (Web Server DAT)

### Base URL
```
http://localhost:9980
```

---

### GET /api/config

Load UI configuration from TouchDesigner's `ui_config` Text DAT.

**Description**: Returns the current UI configuration stored in TouchDesigner. The viewer uses this to dynamically generate the control interface.

**Request**:
```http
GET /api/config HTTP/1.1
Host: localhost:9980
```

**Response (Success)**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "Main Controls",
      "controls": [
        {
          "id": "speed",
          "type": "slider",
          "label": "Speed",
          "chop": "constant_params",
          "channel": 0,
          "min": 0,
          "max": 200,
          "default": 100
        }
      ]
    }
  ]
}
```

**Response (No Config)**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "Default",
      "controls": []
    }
  ]
}
```

**Response (Error)**:
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Invalid JSON in ui_config"
}
```

---

### POST /api/config

Save UI configuration to TouchDesigner's `ui_config` Text DAT.

**Description**: Saves the UI configuration to TouchDesigner. The builder uses this to persist designs.

**Request**:
```http
POST /api/config HTTP/1.1
Host: localhost:9980
Content-Type: application/json

{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "Main Controls",
      "controls": [...]
    }
  ]
}
```

**Response (Success)**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "Config saved to TouchDesigner"
}
```

**Response (Invalid JSON)**:
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid JSON format",
  "details": "Expecting ',' delimiter: line 5 column 3 (char 87)"
}
```

**Response (ui_config DAT Not Found)**:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "ui_config DAT not found"
}
```

---

## WebSocket API

### Connection URL
```
ws://localhost:9980
```

### Message Format

All WebSocket messages are JSON with a `type` field.

---

### Message Types (Browser → TouchDesigner)

#### 1. Parameter (Slider)

**New Format** (with dynamic CHOP routing):
```json
{
  "type": "parameter",
  "id": "speed_slider",
  "value": 150,
  "chop": "constant_params",
  "channel": 1
}
```

**Legacy Format** (still supported):
```json
{
  "type": "parameter",
  "name": "slider1",
  "value": 75
}
```

**Fields**:
- `type`: `"parameter"`
- `id`: Control identifier (string)
- `value`: Numeric value (number)
- `chop`: Target CHOP operator name (string)
- `channel`: Channel index in CHOP (integer, 0-based)

**TouchDesigner Handling**:
```python
target_chop = op(data['chop'])
param_name = f"value{data['channel']}"
setattr(target_chop.par, param_name, data['value'])
```

---

#### 2. Color

**New Format**:
```json
{
  "type": "color",
  "id": "main_color",
  "hex": "#ff6b00",
  "rgb": {
    "r": 1.0,
    "g": 0.42,
    "b": 0.0
  },
  "chop": "constant_color"
}
```

**Legacy Format**:
```json
{
  "type": "color",
  "hex": "#ff0000",
  "rgb": {
    "r": 1.0,
    "g": 0.0,
    "b": 0.0
  }
}
```

**Fields**:
- `type`: `"color"`
- `id`: Control identifier (string)
- `hex`: Hex color code (string, #RRGGBB)
- `rgb`: Normalized RGB values (object)
  - `r`: Red (0-1)
  - `g`: Green (0-1)
  - `b`: Blue (0-1)
- `chop`: Target CHOP operator name (string)

**TouchDesigner Handling**:
```python
color_chop = op(data['chop'])
color_chop.par.value0 = data['rgb']['r']
color_chop.par.value1 = data['rgb']['g']
color_chop.par.value2 = data['rgb']['b']
```

---

#### 3. XY Pad

**New Format**:
```json
{
  "type": "xy",
  "id": "position_xy",
  "x": 0.75,
  "y": 0.50,
  "chop": "constant_xy"
}
```

**Legacy Format**:
```json
{
  "type": "xy",
  "x": 0.75,
  "y": 0.50
}
```

**Fields**:
- `type`: `"xy"`
- `id`: Control identifier (string)
- `x`: X position (0-1, float)
- `y`: Y position (0-1, float)
- `chop`: Target CHOP operator name (string)

**TouchDesigner Handling**:
```python
xy_chop = op(data['chop'])
xy_chop.par.value0 = data['x']
xy_chop.par.value1 = data['y']
```

---

#### 4. Trigger

```json
{
  "type": "trigger",
  "id": "flash_trigger",
  "timestamp": 1678901234567
}
```

**Fields**:
- `type`: `"trigger"`
- `id`: Control identifier (string)
- `timestamp`: Client timestamp (integer, milliseconds)

**TouchDesigner Handling**:
```python
trigger_chop = op('trigger1')
trigger_chop.par.triggerpulse.pulse()
```

---

#### 5. Reset

```json
{
  "type": "reset",
  "timestamp": 1678901234567
}
```

**Fields**:
- `type`: `"reset"`
- `timestamp`: Client timestamp (integer, milliseconds)

**TouchDesigner Handling**:
```python
# Resets all CHOPs to default values
op('constant_params').par.value0 = 50
op('constant_params').par.value1 = 50
op('constant_color').par.value0 = 1.0
# ... etc
```

---

### Message Types (TouchDesigner → Browser)

#### Connection Acknowledgment

Sent when client connects to server.

```json
{
  "type": "connection",
  "message": "Connected to TouchDesigner WebSocket Server",
  "timestamp": 1678901234567
}
```

---

#### Parameter Update

Send parameter feedback from TouchDesigner to browser (for bidirectional sync).

```json
{
  "type": "parameterUpdate",
  "slider1": 75,
  "slider2": 50,
  "slider3": 100
}
```

**Sending from TouchDesigner**:
```python
import json

ws = op('websocket1')
message = {
    'type': 'parameterUpdate',
    'slider1': 75
}
ws.sendText(json.dumps(message))
```

---

## UI Configuration Schema

### Root Structure

```json
{
  "version": "1.0",
  "pages": [...]
}
```

### Page Object

```json
{
  "id": "page1",
  "name": "Main Controls",
  "controls": [...]
}
```

**Fields**:
- `id`: Unique page identifier (string)
- `name`: Display name for tab (string)
- `controls`: Array of control objects

### Control Objects

#### Slider Control

```json
{
  "id": "speed",
  "type": "slider",
  "label": "Speed",
  "chop": "constant_params",
  "channel": 0,
  "min": 0,
  "max": 200,
  "default": 100
}
```

**Fields**:
- `id`: Unique identifier (string)
- `type`: `"slider"`
- `label`: Display label (string)
- `chop`: Target CHOP name (string)
- `channel`: Channel index (integer, 0-based)
- `min`: Minimum value (number)
- `max`: Maximum value (number)
- `default`: Default value (number)

---

#### Color Control

```json
{
  "id": "main_color",
  "type": "color",
  "label": "Main Color",
  "chop": "constant_color",
  "default": "#ff0000"
}
```

**Fields**:
- `id`: Unique identifier (string)
- `type`: `"color"`
- `label`: Display label (string)
- `chop`: Target CHOP name (string)
- `default`: Default hex color (string, #RRGGBB)

---

#### XY Pad Control

```json
{
  "id": "position",
  "type": "xy",
  "label": "Position",
  "chop": "constant_xy",
  "default": {
    "x": 0.5,
    "y": 0.5
  }
}
```

**Fields**:
- `id`: Unique identifier (string)
- `type`: `"xy"`
- `label`: Display label (string)
- `chop`: Target CHOP name (string)
- `default`: Default position (object)
  - `x`: X position (0-1)
  - `y`: Y position (0-1)

---

## Backward Compatibility

### Legacy Format Support

The system supports the old single-page format for backward compatibility:

**Old Format**:
```json
{
  "version": "1.0",
  "name": "My UI",
  "description": "Control interface",
  "controls": [...]
}
```

**Automatically Migrated To**:
```json
{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "My UI",
      "controls": [...]
    }
  ]
}
```

Migration happens automatically on:
- Config load from LocalStorage
- Config load from server
- JSON file upload

---

## Error Codes

### HTTP Status Codes

| Code | Reason | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid JSON format |
| 404 | Not Found | Resource not found (e.g., ui_config DAT) |
| 500 | Internal Server Error | Server-side error |

### WebSocket Connection States

| State | Value | Description |
|-------|-------|-------------|
| CONNECTING | 0 | Connection establishing |
| OPEN | 1 | Connection active, can send/receive |
| CLOSING | 2 | Connection closing |
| CLOSED | 3 | Connection closed |

---

## Usage Examples

### JavaScript (Browser)

#### Load Config
```javascript
async function loadConfig() {
    const response = await fetch('/api/config');
    const config = await response.json();
    console.log('Config:', config);
}
```

#### Save Config
```javascript
async function saveConfig(config) {
    const response = await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(config)
    });
    const result = await response.json();
    console.log('Saved:', result);
}
```

#### Send WebSocket Message
```javascript
const ws = new WebSocket('ws://localhost:9980');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'parameter',
        id: 'speed',
        value: 150,
        chop: 'constant_params',
        channel: 0
    }));
};
```

### Python (TouchDesigner)

#### Send Message to Browser
```python
import json

ws = op('websocket1')
message = {
    'type': 'parameterUpdate',
    'slider1': 75
}
ws.sendText(json.dumps(message))
```

#### Read Config from Text DAT
```python
config_dat = op('ui_config')
config_json = config_dat.text
config = json.loads(config_json)
print('Pages:', len(config['pages']))
```

#### Write Config to Text DAT
```python
import json

config = {
    'version': '1.0',
    'pages': [...]
}

config_dat = op('ui_config')
config_dat.text = json.dumps(config, indent=2)
```

---

## Security Notes

⚠️ **Local Network Only**: This system is designed for local development and should only be used on trusted networks.

⚠️ **No Authentication**: There is no authentication or authorization built-in.

⚠️ **CORS**: Web Server DAT allows all origins by default. Be cautious when exposing to public networks.

For production use, consider:
- Adding authentication
- Using HTTPS/WSS
- Restricting origins
- Validating all inputs

---

## Rate Limiting

There are no built-in rate limits. For high-frequency control (>60Hz):
- Throttle updates in JavaScript
- Use requestAnimationFrame
- Consider batching messages

Example throttling:
```javascript
let lastSent = 0;
const throttle = 16; // ~60Hz

function sendIfReady(data) {
    const now = Date.now();
    if (now - lastSent >= throttle) {
        ws.send(JSON.stringify(data));
        lastSent = now;
    }
}
```

---

## Versioning

**Current Version**: 1.0

Future versions may add:
- Authentication
- Compression
- Binary WebSocket messages
- Additional control types

All versions will maintain backward compatibility where possible.
