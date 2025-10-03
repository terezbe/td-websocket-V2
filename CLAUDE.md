# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WebSocket server that enables real-time bidirectional communication between a web UI and TouchDesigner. The architecture allows control of TouchDesigner parameters from a browser interface using WebSocket messages.

## Running the Project

**Start the server:**
```bash
npm start
```
Or on Windows, double-click `start.bat`

**Access web UI:**
Open `http://localhost:9980` in browser

**No build step required** - static files are served directly from `public/`

## Architecture

### Three-Part System

1. **Node.js WebSocket Server** (`server.js`)
   - Runs on port 9980
   - Serves static web UI files from `public/`
   - Manages multiple WebSocket clients (web UI + TouchDesigner)
   - **Critical**: Uses `broadcastToOthers()` to relay messages between clients

2. **Web UI** (`public/`)
   - Browser-based control interface
   - Connects to server as WebSocket client
   - Sends control messages (sliders, colors, XY pad, triggers)
   - Receives parameter updates from TouchDesigner

3. **TouchDesigner Integration** (`touchdesigner_websocket_callback.py`)
   - TouchDesigner connects as WebSocket client via WebSocket DAT
   - Python callbacks parse JSON messages
   - Extracts data to Constant CHOP channels
   - See `TOUCHDESIGNER_SETUP.md` for complete setup instructions

### Message Flow

**Web UI → TouchDesigner:**
```
Browser (slider change)
  → WebSocket message to server
  → Server broadcasts to other clients
  → TouchDesigner receives message
  → Python callback parses JSON
  → Updates CHOP values
```

**TouchDesigner → Web UI:**
```
TouchDesigner (ws.sendText())
  → Server receives message
  → Server broadcasts to web UI
  → Browser updates interface
```

## Message Protocol

All messages are JSON with a `type` field:

- `parameter` - Slider values (name: slider1/2/3, value: 0-100)
- `color` - RGB color (hex + normalized rgb object)
- `xy` - 2D position (x, y: 0-1 range)
- `trigger` - Pulse event
- `reset` - Reset all to defaults
- `connection` - Server welcome message
- `parameterUpdate` - TouchDesigner → Web UI feedback

See README.md for complete message format reference.

## Key Implementation Details

### Server Broadcasting Strategy

**IMPORTANT**: The server must broadcast messages to OTHER clients, not echo back to sender.

```javascript
// CORRECT - in server.js line 38
broadcastToOthers(ws, data);  // Sends to all clients EXCEPT sender

// WRONG - would only echo back
ws.send(data);  // Only sends back to sender
```

This is crucial because web UI and TouchDesigner are separate clients. Messages from web UI must reach TouchDesigner.

### TouchDesigner Callback Requirements

The Python script in `touchdesigner_websocket_callback.py` must be:
1. Pasted into a Text DAT in TouchDesigner
2. Referenced in WebSocket DAT's "Callbacks DAT" parameter
3. Uses exact callback names: `onConnect`, `onDisconnect`, `onReceiveText`

**Required CHOP operators:**
- `constant_params` - 3 channels (slider1, slider2, slider3)
- `constant_color` - 3 channels (r, g, b)
- `constant_xy` - 2 channels (x, y)
- `trigger1` - Trigger CHOP

These names are hardcoded in the Python script (lines 77, 119, 151, 182).

### Web UI State Management

`public/app.js` manages WebSocket connection state and UI updates:
- `isConnected` - Connection status flag
- `ws` - WebSocket instance
- Each control (slider, color, xy) sends messages on input events
- `handleIncomingMessage()` processes TouchDesigner feedback

## Common Modifications

### Adding New Controls

1. **HTML** (`public/index.html`): Add input element
2. **CSS** (`public/style.css`): Style if needed
3. **JavaScript** (`public/app.js`): Add event listener and sendMessage() call with new type
4. **Python** (`touchdesigner_websocket_callback.py`): Add handler function and case in onReceiveText()

### Changing Port

Update in 3 places:
- `server.js` line 10: `const PORT = 9980`
- Web UI default connection (already uses form input)
- TouchDesigner WebSocket DAT Network Port parameter

### Modifying CHOP Names

Edit Python script functions (handleParameter, handleColor, handleXY, handleTrigger) to reference your CHOP operator names using `op('your_chop_name')`.

## Troubleshooting

### Messages not reaching TouchDesigner

**Check:**
1. Server is using `broadcastToOthers()` not echo (line 38 in server.js)
2. WebSocket DAT "Callbacks DAT" parameter is set
3. TouchDesigner Textport (Alt+T) shows connection message
4. Both web UI AND TouchDesigner are connected (2 clients)

### Callbacks not firing

**Issue**: Callbacks DAT parameter on WebSocket DAT is empty
**Fix**: Drag Text DAT with Python script into WebSocket DAT's "Callbacks DAT" parameter

### Values not updating in CHOPs

**Check:**
- CHOP names match script (constant_params, constant_color, constant_xy, trigger1)
- Using parameter assignment: `op('chop').par.value0 = x` not channel assignment
- CHOPs exist in TouchDesigner network

## Files

**Server:**
- `server.js` - WebSocket server with client management and broadcasting
- `package.json` - Dependencies (express, ws)

**Web UI:**
- `public/index.html` - Control interface with sliders, color picker, XY pad
- `public/style.css` - Dark theme styling
- `public/app.js` - WebSocket client logic and UI event handlers

**TouchDesigner:**
- `touchdesigner_websocket_callback.py` - Python callbacks for WebSocket DAT
- `TOUCHDESIGNER_SETUP.md` - Complete TouchDesigner configuration guide

**Utilities:**
- `start.bat` - Windows launcher (runs npm install + npm start)
- `README.md` - User-facing documentation

## References

- [TouchDesigner WebSocket DAT Docs](https://docs.derivative.ca/WebSocket_DAT)
- [WebSocket DAT Class Callbacks](https://docs.derivative.ca/WebsocketDAT_Class)
