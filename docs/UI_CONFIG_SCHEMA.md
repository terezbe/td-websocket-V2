# UI Configuration Schema

This document defines the JSON format for storing UI control configurations.

## Schema Version

**Current Version:** 1.0

## Root Structure

### Multi-Page Format (Current)

```json
{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "Main Controls",
      "controls": [
        // Array of control objects
      ]
    },
    {
      "id": "page2",
      "name": "Colors",
      "controls": [
        // Array of control objects
      ]
    }
  ]
}
```

### Legacy Single-Page Format (Backward Compatible)

```json
{
  "version": "1.0",
  "name": "My Custom UI",
  "description": "Optional description",
  "controls": [
    // Array of control objects
  ]
}
```

### Root Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `version` | string | Yes | Schema version (currently "1.0") |
| `pages` | array | Yes* | Array of page objects (multi-page format) |
| `controls` | array | Yes* | Array of control objects (legacy single-page format) |
| `name` | string | No | Name of the UI configuration (legacy format only) |
| `description` | string | No | Description (legacy format only) |

*Either `pages` or `controls` must be present, not both

### Page Object Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique page identifier |
| `name` | string | Yes | Display name for the page tab |
| `controls` | array | Yes | Array of control objects for this page |

---

## Control Types

### 1. Slider Control

**Purpose:** Numeric input with min/max range

```json
{
  "id": "slider1",
  "type": "slider",
  "label": "Parameter 1",
  "chop": "constant_params",
  "channel": 0,
  "min": 0,
  "max": 100,
  "default": 50
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this control |
| `type` | string | Yes | Must be "slider" |
| `label` | string | Yes | Display label for the control |
| `chop` | string | Yes | Name of target CHOP operator |
| `channel` | number | Yes | Channel index (0, 1, 2...) |
| `min` | number | Yes | Minimum value |
| `max` | number | Yes | Maximum value |
| `default` | number | Yes | Default value |

**WebSocket Message Sent:**
```json
{
  "type": "parameter",
  "id": "slider1",
  "value": 75,
  "chop": "constant_params",
  "channel": 0
}
```

---

### 2. Color Picker Control

**Purpose:** RGB color selection

```json
{
  "id": "color1",
  "type": "color",
  "label": "Color",
  "chop": "constant_color",
  "default": "#ff0000"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this control |
| `type` | string | Yes | Must be "color" |
| `label` | string | Yes | Display label for the control |
| `chop` | string | Yes | Name of target CHOP operator (must have r,g,b channels) |
| `default` | string | Yes | Default color in hex format (#RRGGBB) |

**WebSocket Message Sent:**
```json
{
  "type": "color",
  "id": "color1",
  "hex": "#ff0000",
  "rgb": {"r": 1.0, "g": 0.0, "b": 0.0},
  "chop": "constant_color"
}
```

---

### 3. XY Pad Control

**Purpose:** 2D position input (0-1 range)

```json
{
  "id": "xy1",
  "type": "xy",
  "label": "XY Position",
  "chop": "constant_xy",
  "default": {"x": 0.5, "y": 0.5}
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this control |
| `type` | string | Yes | Must be "xy" |
| `label` | string | Yes | Display label for the control |
| `chop` | string | Yes | Name of target CHOP operator (must have x,y channels or value0,value1) |
| `default` | object | Yes | Default position {x: number, y: number} |

**WebSocket Message Sent:**
```json
{
  "type": "xy",
  "id": "xy1",
  "x": 0.5,
  "y": 0.5,
  "chop": "constant_xy"
}
```

---

### 4. Trigger Button Control

**Purpose:** Single pulse/trigger action

```json
{
  "id": "trigger1",
  "type": "trigger",
  "label": "Trigger",
  "chop": "trigger1"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this control |
| `type` | string | Yes | Must be "trigger" |
| `label` | string | Yes | Display label for the control |
| `chop` | string | Yes | Name of target Trigger CHOP |

**WebSocket Message Sent:**
```json
{
  "type": "trigger",
  "id": "trigger1",
  "chop": "trigger1"
}
```

---

### 5. Toggle Button Control

**Purpose:** On/Off switch

```json
{
  "id": "toggle1",
  "type": "toggle",
  "label": "Enable Effect",
  "chop": "constant_params",
  "channel": 3,
  "default": false
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for this control |
| `type` | string | Yes | Must be "toggle" |
| `label` | string | Yes | Display label for the control |
| `chop` | string | Yes | Name of target CHOP operator |
| `channel` | number | Yes | Channel index (0, 1, 2...) |
| `default` | boolean | Yes | Default state (true/false) |

**WebSocket Message Sent:**
```json
{
  "type": "parameter",
  "id": "toggle1",
  "value": 1,
  "chop": "constant_params",
  "channel": 3
}
```

---

## Complete Example Configurations

### Multi-Page Example

```json
{
  "version": "1.0",
  "pages": [
    {
      "id": "page1",
      "name": "Parameters",
      "controls": [
        {
          "id": "intensity",
          "type": "slider",
          "label": "Intensity",
          "chop": "constant_params",
          "channel": 0,
          "min": 0,
          "max": 100,
          "default": 50
        },
        {
          "id": "speed",
          "type": "slider",
          "label": "Speed",
          "chop": "constant_params",
          "channel": 1,
          "min": 0,
          "max": 200,
          "default": 100
        }
      ]
    },
    {
      "id": "page2",
      "name": "Colors",
      "controls": [
        {
          "id": "mainColor",
          "type": "color",
          "label": "Main Color",
          "chop": "constant_color",
          "default": "#ff0000"
        }
      ]
    },
    {
      "id": "page3",
      "name": "XY Controls",
      "controls": [
        {
          "id": "position",
          "type": "xy",
          "label": "Position",
          "chop": "constant_xy",
          "default": {"x": 0.5, "y": 0.5}
        }
      ]
    }
  ]
}
```

### Legacy Single-Page Example

```json
{
  "version": "1.0",
  "name": "VJ Control Panel",
  "description": "Controls for live video performance",
  "controls": [
    {
      "id": "intensity",
      "type": "slider",
      "label": "Intensity",
      "chop": "constant_params",
      "channel": 0,
      "min": 0,
      "max": 100,
      "default": 50
    },
    {
      "id": "speed",
      "type": "slider",
      "label": "Speed",
      "chop": "constant_params",
      "channel": 1,
      "min": 0,
      "max": 200,
      "default": 100
    },
    {
      "id": "mainColor",
      "type": "color",
      "label": "Main Color",
      "chop": "constant_color",
      "default": "#ff0000"
    },
    {
      "id": "position",
      "type": "xy",
      "label": "Position",
      "chop": "constant_xy",
      "default": {"x": 0.5, "y": 0.5}
    },
    {
      "id": "flash",
      "type": "trigger",
      "label": "Flash",
      "chop": "trigger1"
    },
    {
      "id": "enableBlur",
      "type": "toggle",
      "label": "Enable Blur",
      "chop": "constant_params",
      "channel": 2,
      "default": false
    }
  ]
}
```

---

## Default Configuration

If no config is found in LocalStorage, use this default:

```json
{
  "version": "1.0",
  "name": "Default UI",
  "description": "Default control layout",
  "controls": [
    {
      "id": "slider1",
      "type": "slider",
      "label": "Parameter 1",
      "chop": "constant_params",
      "channel": 0,
      "min": 0,
      "max": 100,
      "default": 50
    },
    {
      "id": "slider2",
      "type": "slider",
      "label": "Parameter 2",
      "chop": "constant_params",
      "channel": 1,
      "min": 0,
      "max": 100,
      "default": 50
    },
    {
      "id": "slider3",
      "type": "slider",
      "label": "Parameter 3",
      "chop": "constant_params",
      "channel": 2,
      "min": 0,
      "max": 100,
      "default": 50
    },
    {
      "id": "color",
      "type": "color",
      "label": "Color",
      "chop": "constant_color",
      "default": "#ff0000"
    },
    {
      "id": "xy",
      "type": "xy",
      "label": "XY Pad",
      "chop": "constant_xy",
      "default": {"x": 0.5, "y": 0.5}
    },
    {
      "id": "trigger",
      "type": "trigger",
      "label": "Trigger",
      "chop": "trigger1"
    }
  ]
}
```

---

## Validation Rules

### Control ID
- Must be unique within the configuration
- Only alphanumeric characters and underscores
- Regex: `^[a-zA-Z0-9_]+$`

### CHOP Names
- Must reference existing CHOP operators in TouchDesigner
- Common examples: `constant_params`, `constant_color`, `constant_xy`, `trigger1`

### Channel Numbers
- Must be integers >= 0
- Must be within the CHOP's channel count
- For Constant CHOP with 3 channels: valid values are 0, 1, 2

### Slider Values
- `min` must be less than `max`
- `default` must be between `min` and `max`

### Color Values
- Must be valid hex color: `#RRGGBB`
- Each component (R, G, B) must be 00-FF

### XY Values
- `x` and `y` must be between 0 and 1
- Default: `{"x": 0.5, "y": 0.5}`

---

## Storage Locations

### 1. Browser LocalStorage (Phase 1)
**Key:** `td_ui_config`
**Value:** JSON string of config object

```javascript
// Save
localStorage.setItem('td_ui_config', JSON.stringify(config));

// Load
const config = JSON.parse(localStorage.getItem('td_ui_config'));
```

### 2. Download/Upload (Phase 1)
**Format:** `.json` file
**Filename:** `td-ui-config.json` or user-specified

### 3. Storage DAT (Phase 2 - Future)
**Operator:** `ui_config` (Storage DAT inside component)
**Access:** `op('ui_config').text`

---

## Future Control Types (Later Phases)

```json
// Dropdown/Select
{
  "type": "select",
  "options": ["Option 1", "Option 2", "Option 3"],
  "default": 0
}

// Text Input
{
  "type": "text",
  "placeholder": "Enter text...",
  "default": ""
}

// Number Input
{
  "type": "number",
  "min": 0,
  "max": 100,
  "step": 1,
  "default": 50
}
```

---

## Version History

**v1.0** (Current)
- Slider control
- Color picker control
- XY pad control
- Trigger button control
- Toggle button control
