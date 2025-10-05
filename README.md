# TouchDesigner WebSocket Control System

A complete system for building and controlling TouchDesigner projects from a web interface with real-time WebSocket communication.

## Features

- **🎨 UI Builder** - Drag-and-drop interface to design custom control panels
- **📱 Multi-Page Interface** - Organize controls into multiple pages/tabs
- **🔌 Real-time WebSocket** - Bidirectional data exchange between browser and TouchDesigner
- **💾 Persistent Storage** - Save UI configurations in TouchDesigner or browser
- **🎛️ Multiple Control Types**:
  - Sliders with custom ranges
  - Color pickers with RGB/hex output
  - XY pads for 2D control
  - Trigger buttons
  - Custom JSON messaging
- **📦 Fully Portable** - Embed entire UI in .tox file (Web Server DAT mode)
- **🔄 Two Deployment Options** - Node.js server OR TouchDesigner Web Server DAT

## Quick Start

### Two Setup Options

**Choose based on your needs:**

#### Option 1: Web Server DAT (Recommended for .tox export)
✅ Fully self-contained - everything embedded in .tox file
✅ No Node.js required - works standalone
✅ Config saved in TouchDesigner

📖 **[Complete setup guide →](docs/WEBSERVER_DAT_SETUP.md)**

#### Option 2: Node.js Server (Easier for development)
✅ Fast iteration - auto-reload during development
✅ Separate server process
✅ Config in browser LocalStorage

**Quick steps:**
1. Install dependencies: `npm install`
2. Start server: `npm start`
3. Open builder: `http://localhost:9980/builder.html`
4. Configure TouchDesigner WebSocket DAT (see [TOUCHDESIGNER_SETUP.md](docs/TOUCHDESIGNER_SETUP.md))

**Note:** Both options use the same WebSocket protocol for control messages. The difference is in how files are served and where config is stored.

## TouchDesigner Setup

### Web Server DAT (Recommended)

For a fully self-contained .tox file with embedded UI:

1. **Setup Guide**: [docs/WEBSERVER_DAT_SETUP.md](docs/WEBSERVER_DAT_SETUP.md)
2. **Callback Script**: Use `touchdesigner/webserver_complete_callbacks.py`
   - Handles both HTTP (API) and WebSocket (control messages)
   - Copy entire script into a Text DAT in TouchDesigner
   - Link to Web Server DAT's "Callbacks DAT" parameter

### Node.js Server + WebSocket DAT

For development with fast iteration:

1. **Setup Guide**: [docs/TOUCHDESIGNER_SETUP.md](docs/TOUCHDESIGNER_SETUP.md)
2. **Callback Script**: Extract from `touchdesigner/webserver_complete_callbacks.py`
   - Use only the WebSocket callback functions
   - Or create your own based on examples in the guide

### Required CHOPs

Both setups require these Constant CHOPs in TouchDesigner:
- `constant_params` - Slider values
- `constant_color` - RGB color values (0-1)
- `constant_xy` - XY pad position (0-1)
- `trigger1` - Trigger CHOP for button pulses

## How It Works

### UI Builder Workflow

1. **Design**: Open `builder.html` and drag controls onto pages
2. **Configure**: Set control properties (label, CHOP name, channel, range)
3. **Save**: Click "Save to TD" (Web Server DAT) or browser saves automatically
4. **Deploy**: Open `index.html` to see live control interface

### Message Flow

```
Browser UI → WebSocket → TouchDesigner
   ↓                           ↓
Controls              Update CHOP values
(sliders, colors)     (constant_params, etc.)
```

### WebSocket Message Format

**Parameter (Slider)**:
```json
{
  "type": "parameter",
  "id": "speed",
  "value": 150,
  "chop": "constant_params",
  "channel": 1
}
```

**Color**:
```json
{
  "type": "color",
  "id": "main_color",
  "hex": "#ff6b00",
  "rgb": {"r": 1.0, "g": 0.42, "b": 0.0},
  "chop": "constant_color"
}
```

**XY Pad**:
```json
{
  "type": "xy",
  "id": "position",
  "x": 0.75,
  "y": 0.50,
  "chop": "constant_xy"
}
```

📖 **[Complete API Reference →](docs/API_REFERENCE.md)** for all message types and HTTP endpoints.

## Project Structure

```
td-websocket-V2/
├── touchdesigner/                          # TouchDesigner files
│   ├── webserver_complete_callbacks.py     # Complete callback script (HTTP + WebSocket)
│   ├── load_vfs_files.py                   # VFS loader utility
│   ├── td-websocket.toe                    # Example TouchDesigner project
│   └── WebSocketControl_v2.tox             # Exportable component
│
├── docs/                                   # Documentation
│   ├── WEBSERVER_DAT_SETUP.md              # Web Server DAT setup guide
│   ├── TOUCHDESIGNER_SETUP.md              # WebSocket DAT setup guide
│   ├── API_REFERENCE.md                    # Complete API documentation
│   ├── UI_CONFIG_SCHEMA.md                 # UI configuration format
│   └── BUILDER_TESTING_GUIDE.md            # Builder testing guide
│
├── public/                                 # Web UI files
│   ├── index.html                          # Viewer (control interface)
│   ├── app.js                              # Viewer logic
│   ├── style.css                           # Viewer styles
│   ├── builder.html                        # UI Builder
│   ├── builder.js                          # Builder logic
│   └── builder.css                         # Builder styles
│
├── server.js                               # Node.js WebSocket server
├── package.json                            # Node.js dependencies
├── start.bat                               # Windows launcher
├── README.md                               # This file
└── CLAUDE.md                               # AI assistant instructions
```

## Customization

### Using the UI Builder

The easiest way to customize your interface:

1. Open `http://localhost:9980/builder.html`
2. Add controls from the palette (sliders, colors, XY pads)
3. Configure each control's properties:
   - Label (display name)
   - CHOP name (target operator)
   - Channel index (which value to update)
   - Min/max/default (for sliders)
4. Organize into multiple pages/tabs
5. Save configuration to TouchDesigner or browser

No code changes needed!

### Advanced Customization

For custom control types or behavior:

1. **Callback Script**: Edit `touchdesigner/webserver_complete_callbacks.py`
   - Add new message type handlers
   - Add custom API endpoints
   - See [API_REFERENCE.md](docs/API_REFERENCE.md) for examples

2. **Web UI**: Modify `public/builder.js` and `public/app.js`
   - Add new control types to builder palette
   - Implement custom rendering in viewer

### Port Configuration

- **Node.js Server**: Edit `PORT` in `server.js`
- **Web Server DAT**: Change port parameter on Web Server DAT
- Update web UI connection URL accordingly

## Troubleshooting

### Web Server DAT Issues

**Config not saving:**
- Check `ui_config` Text DAT exists in TouchDesigner
- Verify Callbacks DAT parameter is set on Web Server DAT
- Look at Textport (Alt+T) for Python errors

**Files not loading (404):**
- Verify VFS parameter points to component with files
- Re-run `touchdesigner/load_vfs_files.py` to reload VFS
- Check file names are correct (case-sensitive)

📖 **[Complete troubleshooting guide →](docs/WEBSERVER_DAT_SETUP.md#troubleshooting)**

### Node.js Server Issues

**Server won't start:**
- Run `npm install` to install dependencies
- Check port 9980 isn't already in use
- Try a different port in `server.js`

**WebSocket not connecting:**
- Verify server is running (`npm start`)
- Check firewall isn't blocking port 9980
- Ensure TouchDesigner WebSocket DAT is Active

📖 **[Complete setup guide →](docs/TOUCHDESIGNER_SETUP.md)**

### Control Values Not Updating

**Check:**
- Required CHOPs exist in TouchDesigner (constant_params, constant_color, constant_xy, trigger1)
- CHOP names in UI config match actual CHOP names
- Callbacks DAT is properly linked
- Textport shows messages being received

**Common fixes:**
- Verify control's `chop` property matches your CHOP name
- Check `channel` index is correct (0-based)
- Look for Python errors in Textport

## Documentation

- **[Web Server DAT Setup](docs/WEBSERVER_DAT_SETUP.md)** - Self-contained .tox setup
- **[TouchDesigner Setup](docs/TOUCHDESIGNER_SETUP.md)** - Node.js server setup
- **[API Reference](docs/API_REFERENCE.md)** - Complete message format reference
- **[UI Config Schema](docs/UI_CONFIG_SCHEMA.md)** - Configuration file format
- **[Builder Testing Guide](docs/BUILDER_TESTING_GUIDE.md)** - Testing the UI builder

## Resources

**TouchDesigner Documentation:**
- [Web Server DAT](https://docs.derivative.ca/Web_Server_DAT)
- [WebSocket DAT](https://docs.derivative.ca/WebSocket_DAT)
- [Constant CHOP](https://docs.derivative.ca/Constant_CHOP)

**Community Tutorials:**
- [WebSocket Control Tutorial](https://derivative.ca/community-post/tutorial/part-1-intro-overview-websockets-control-touchdesigner-website-vice-versa)
- [WebWelder Component](https://github.com/djipco/webwelder)

## License

MIT
