# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TouchDesigner WebSocket control system with a visual UI builder and automatic CHOP deployment. This is a complete solution for creating custom web-based control interfaces for TouchDesigner projects.

**Key Innovation**: Uses TouchDesigner's **Web Server DAT** (NOT separate Node.js server) to handle both HTTP and WebSocket on a single port (9980). Web files are embedded in the .tox using TouchDesigner's Virtual File System (VFS).

## Architecture: Two-Part System

### 1. TouchDesigner Component (Web Server DAT)
- **Single DAT** handles HTTP + WebSocket on port 9980
- Serves static files from VFS (Virtual File System - files embedded in .tox)
- Python callbacks in `touchdesigner/webserver_complete_callbacks.py`
- HTTP API endpoints for config save/load and CHOP deployment
- WebSocket endpoint for real-time control messages

### 2. Web UI (Dual Interface)
- **Viewer** (`public/index.html` + `app.js`) - End-user control interface
- **Builder** (`public/builder.html` + `builder.js`) - Visual UI designer

## Running the Project

**In TouchDesigner:**
1. Open the .tox component
2. Web Server DAT auto-starts on port 9980
3. Access viewer: `http://localhost:9980/index.html`
4. Access builder: `http://localhost:9980/builder.html`

**No Node.js server needed** - everything runs in TouchDesigner.

## Critical Architecture Patterns

### CHOP Auto-Naming System

**Page-based CHOP creation**: Each page in the builder automatically creates a CHOP named `{sanitized_page_name}_controls`.

Example:
- Page "Main" → CHOP `main_controls`
- Page "Colors & Effects" → CHOP `colors_effects_controls`

**Channel naming**: Uses sanitized control **labels** (not IDs) for human-readable channel names.

Example:
- Control labeled "Speed Control" → channel `speed_control`
- Control labeled "Color 5" → channels `color_5_r`, `color_5_g`, `color_5_b`

**Implementation locations:**
- Deployment: `webserver_complete_callbacks.py` → `deployFromConfig()` (line 108-349)
- Builder: `builder.js` → `createDefaultControl()` (line 137-180)
- Viewer: `app.js` → sends `label` field in messages (lines 279, 305, 475, 382)
- Handlers: `webserver_complete_callbacks.py` → all `handle*()` functions use `sanitizeName(label)`

### Name Sanitization (JavaScript ↔ Python Consistency)

**CRITICAL**: Both JavaScript and Python use **identical** sanitization:

```javascript
// builder.js (line 40-51)
function sanitizeName(name) {
    let sanitized = name.replace(/[^a-zA-Z0-9_]/g, '_');
    sanitized = sanitized.replace(/_+/g, '_');
    sanitized = sanitized.replace(/^_+|_+$/g, '');
    sanitized = sanitized.toLowerCase();
    return sanitized || 'page';
}
```

```python
# webserver_complete_callbacks.py (line 82-92)
def sanitizeName(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    sanitized = sanitized.lower()
    return sanitized if sanitized else 'page'
```

### Config Storage Architecture (CRITICAL)

**Hybrid Storage + Text DAT System**: Config is stored in **two places** for reliability and visibility:

**PRIMARY: TouchDesigner Storage**
```python
parent().storage['ui_config'] = config_dict  # Fast, reliable, no encoding issues
```
- Python dictionary attached to parent component
- Persists in .toe/.tox file when saved
- No bytes/encoding problems
- Fast access (no JSON parsing)
- **This is the source of truth**

**BACKUP: Text DAT**
```python
op('ui_config').text = json.dumps(config_dict, indent=2)  # Visible in UI
```
- For visual debugging and manual inspection
- Fallback if storage is empty (old projects)
- Shows formatted JSON in TouchDesigner UI

**Read Priority** (all endpoints):
1. Try `parent().storage['ui_config']` first (fast path)
2. Fallback to Text DAT `op('ui_config').text` (compatibility)
3. Return empty default if neither exists

**Implementation:**
- POST `/api/config`: Saves to both storage and Text DAT (lines 438-448)
- GET `/api/config`: Reads from storage first (lines 375-380)
- `deployFromConfig()`: Reads from storage first (lines 139-141)

**Why This Matters:**
- Fixes all config loading issues (bytes, encoding, consistency)
- Phone and desktop always load same config
- No localStorage confusion
- Deployment and viewer use identical data

### CHOP Deployment Strategy

**Auto-deploy on save**: Builder → "Save to TD" → HTTP POST `/api/config` → saves to storage + Text DAT → HTTP POST `/api/deploy` → creates/updates CHOPs

**Update vs Create logic**:
```python
if is_update:
    # Use existing CHOP - just overwrite channels we need
    new_chop = existing_chop
else:
    # Create new CHOP
    new_chop = deploy_location.create(constantCHOP, chop_name)
```

**Channel configuration**:
- Sets only channels 0 to N-1 (where N = number of controls)
- **Does NOT clear unused channels** to avoid creating empty visible rows
- Old channels from deleted controls remain but are harmless (not referenced by viewer)

### WebSocket Message Flow

**Viewer → TouchDesigner:**
```
User moves slider in viewer
  → sendMessage({type: 'parameter', label: 'Speed Control', chop: 'main_controls', value: 75})
  → Web Server DAT onWebSocketReceiveText()
  → handleParameter()
      → Gets CHOP: op('main_controls')
      → Sanitizes label: 'Speed Control' → 'speed_control'
      → Searches channels by name: finds 'speed_control'
      → Sets value: chop.par.const{i}value = 75
```

**Dynamic CHOP routing**: Every message includes `chop` field specifying target CHOP name. No hardcoded CHOP names in handlers.

**Channel search by name** (line 698-707):
```python
for i in range(target_chop.numChans):
    if target_chop.par[f'const{i}name'].eval() == sanitized_label:
        target_chop.par[f'const{i}value'] = value
        break
```

### Control Type → CHOP Channel Mapping

**Slider**: 1 channel
- Channel name: `{sanitized_label}`

**Color**: 3 channels
- Channel names: `{sanitized_label}_r`, `{sanitized_label}_g`, `{sanitized_label}_b`
- Values: 0-1 normalized RGB

**XY Pad**: 2 channels
- Channel names: `{sanitized_label}_x`, `{sanitized_label}_y`
- Values: 0-1 normalized coordinates

**Button**: 1 channel
- Channel name: `{sanitized_label}_state`
- Values: 0 (OFF) or 1 (ON)

## Key Files and Responsibilities

### TouchDesigner Python

**`touchdesigner/webserver_complete_callbacks.py`** (single unified script)
- Web Server DAT callbacks (HTTP + WebSocket)
- Deployment engine: `deployFromConfig()` (line 108-349)
- WebSocket handlers: `handleParameter()`, `handleColor()`, `handleXY()`, `handleButton()` (lines 650-935)
- API endpoints: `/api/config` (GET/POST), `/api/deploy` (POST)
- **Location**: Paste into Text DAT, set as Web Server DAT "Callbacks DAT" parameter

**`touchdesigner/load_vfs_files.py`** (utility script)
- Loads web files from `public/` into VFS
- Run once when setting up or updating web files
- **Location**: Run via textport: `execfile('path/to/load_vfs_files.py')`

**`touchdesigner/test_auto_chop.py`** (testing utility)
- Test script for deployment system
- Not used in production

### Web UI - Builder

**`public/builder.html`** (line 1-157)
- UI builder interface structure
- Left panel: control palette (slider, color, xy, button)
- Middle panel: layout/canvas with page tabs
- Right panel: live preview (mobile/desktop)
- Properties sidebar: edit selected control

**`public/builder.js`** (1000+ lines)
- State management: `state.config.pages[]`
- Page management: `addPage()`, `deletePage()`, `switchPage()`
- Control management: `addControl()`, `createDefaultControl()`, `deleteControl()`
- Properties panel: `createPropertiesForm()`, `saveProperties()`
- Server integration: `saveToServer()`, `loadFromServer()`
- Local storage: `saveToLocalStorage()`, `loadFromLocalStorage()`
- **Auto-CHOP naming**: Line 140-143 (sets `chop: "{sanitized_page_name}_controls"`)

**`public/builder.css`**
- Builder-specific styling

### Web UI - Viewer

**`public/index.html`**
- End-user control interface
- Renders controls from loaded config
- Page tabs for multi-page configs

**`public/app.js`**
- WebSocket client for real-time control
- **Config loading**: Server only (no localStorage) - line 40-61
- Renders UI from config: `renderUI()`, `renderPageTabs()`, `renderCurrentPage()`
- Control rendering: `createControl()` for each type
- Message sending: `sendMessage()` with `label` field
- Empty state: Shows "No controls configured" with link to builder (line 181-204)
- **Single source of truth**: Always loads from TouchDesigner server

**`public/style.css`**
- Viewer styling

## Common Development Tasks

### Adding a New Control Type

1. **Deployment** (`webserver_complete_callbacks.py` line 226-263):
```python
elif control_type == 'newtype':
    channels.append({
        'name': sanitized_label,
        'value': control.get('default', 0),
        'type': 'newtype'
    })
```

2. **Builder** (`builder.js` line 145-177):
```javascript
newtype: {
    id,
    type: 'newtype',
    label: `New Type ${state.nextId}`,
    chop: chopName,
    default: 0
}
```

3. **Viewer** (`app.js` - add rendering in `createControl()`):
```javascript
else if (control.type === 'newtype') {
    // Create input element
    // Add event listener that calls sendMessage()
}
```

4. **Handler** (`webserver_complete_callbacks.py` - add handler function):
```python
def handleNewType(data):
    # Extract data, find CHOP, update channel
```

### Modifying CHOP Deployment Location

Currently deploys to `me.parent()` (inside component, same level as Web Server DAT).

To change location, edit line 186:
```python
deploy_location = me.parent()  # Change to desired location
```

### Testing the System

**Test builder → deployment:**
1. Open `http://localhost:9980/builder.html`
2. Add controls to page
3. Click "Save to TD"
4. Check TouchDesigner textport for deployment logs
5. Verify CHOP created with correct channels

**Test viewer → CHOP updates:**
1. Open `http://localhost:9980/index.html`
2. Move a slider
3. Check textport for WebSocket message logs
4. Verify CHOP value updates in TouchDesigner

**Check channel naming:**
- CHOP channel names should be sanitized control labels (not IDs)
- Example: Control "Speed Control" → channel "speed_control"

## Troubleshooting

### Viewer shows empty UI after saving from builder

**Cause**: Config not loading from storage properly.

**Check TouchDesigner Textport for:**
```
[WebServer] ✓ Saved config to storage (XXX bytes)
[WebServer] ✓ Loaded config from storage
```

**Fix**:
1. Verify Web Server DAT callbacks are set to the script with storage code
2. Check that Web Server DAT is inside a component (storage needs parent)
3. Clear browser cache and refresh viewer
4. If Text DAT has old data, it will be migrated to storage on next save

### "CHOP '{name}' not found!" error

**Cause**: CHOP names in config don't match deployed CHOPs.

**Fix**:
1. Open builder, click "Save to TD" (this deploys CHOPs)
2. Refresh viewer
3. Check textport for deployment success message

### Phone and desktop show different UIs

**Cause**: This should NOT happen with storage architecture.

**Check**:
1. Both devices loading from same server (`http://localhost:9980` or `http://[computer-ip]:9980`)
2. Textport shows "Loaded from storage" (not "Text DAT fallback")
3. No browser errors in console (F12)

**Fix**: Viewer loads from server only (no localStorage). Both devices should be identical.

### Empty channels appearing after re-deploy

**Cause**: Old deployment code cleared all 40 channels (fixed).

**Status**: Already fixed. Code now only sets channels 0 to N-1.

### Web files not loading

**Cause**: VFS not populated or Web Server DAT VFS parameter not set.

**Fix**:
1. Run `load_vfs_files.py` to populate VFS
2. Set Web Server DAT "VFS" parameter to component path
3. Restart Web Server DAT (toggle Active off/on)

### Advanced tab stuck on screen

**Cause**: Switching from Advanced to regular page didn't hide Advanced tab.

**Status**: Already fixed (app.js line 201-205). Advanced tab is hidden when switching pages.

## Message Protocol Reference

All WebSocket messages are JSON with `type` field.

**Parameter (Slider):**
```json
{
  "type": "parameter",
  "id": "slider1",
  "label": "Speed Control",
  "value": 75,
  "chop": "main_controls",
  "channel": 0
}
```

**Color:**
```json
{
  "type": "color",
  "id": "color1",
  "label": "Background Color",
  "hex": "#ff0000",
  "rgb": {"r": 1.0, "g": 0.0, "b": 0.0},
  "chop": "main_controls"
}
```

**XY Pad:**
```json
{
  "type": "xy",
  "id": "xy1",
  "label": "Position",
  "x": 0.75,
  "y": 0.50,
  "chop": "main_controls"
}
```

**Button:**
```json
{
  "type": "button",
  "id": "button1",
  "label": "Trigger Effect",
  "state": 1,
  "chop": "main_controls"
}
```

## Important Implementation Notes

### Why Web Server DAT (Not WebSocket DAT)

Original design used WebSocket DAT + external Node.js server. **Current architecture** uses only Web Server DAT because:
- Handles both HTTP (serving pages) AND WebSocket (control messages)
- Single port 9980 for everything
- VFS support embeds web files in .tox
- Simpler setup (no external server)

### Why Hybrid Storage + Text DAT

**Storage Advantages:**
- No encoding/bytes issues (stores Python dicts directly)
- Fast (no JSON parsing)
- Reliable (survives .toe save)
- **Solves the config loading problem**

**Text DAT Advantages:**
- Visible in UI (can see config data)
- Manual editing possible
- Backwards compatible with old projects

**Best of both worlds**: Storage for reliability, Text DAT for visibility.

### Why VFS (Virtual File System)

Web files (`public/*.html`, `public/*.js`, `public/*.css`) are embedded in the TouchDesigner component using virtualFile operators. This allows distributing the component as a single .tox file without external dependencies.

### Why Viewer Has No localStorage

**Before**: Viewer used localStorage fallback → inconsistent between devices

**Now**: Viewer loads from server only → always consistent

**Benefit**: Phone and desktop always show identical UI. Single source of truth.

### Channel Parameters vs Channel Values

**ALWAYS use parameter assignment**, not channel assignment:

```python
# CORRECT
op('chop').par.const0value = 75

# WRONG - does not work in TouchDesigner
op('chop')['channel_name'] = 75
```

Constant CHOP channels are accessed via parameters: `const{N}name` and `const{N}value`.

### Deployment Does Not Clear Old Channels

By design, deployment only overwrites channels 0 to N-1. Old channels beyond N remain unchanged. This is intentional to avoid creating empty visible channels in the TouchDesigner UI.

## References

- [TouchDesigner Web Server DAT](https://docs.derivative.ca/Web_Server_DAT)
- [TouchDesigner WebSocket DAT](https://docs.derivative.ca/WebSocket_DAT)
- [VirtualFile Component](https://docs.derivative.ca/VirtualFile)
- [Constant CHOP](https://docs.derivative.ca/Constant_CHOP)
