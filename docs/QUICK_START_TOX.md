# Quick Start: TouchDesigner .tox Package

## What You'll Get

A single `.tox` file that contains:
- ✅ Complete web UI (HTML/CSS/JS) embedded via VFS
- ✅ Web server to serve the UI
- ✅ WebSocket server for real-time communication
- ✅ CHOPs for parameter storage
- ✅ Works offline, no external files needed!

## 5-Minute Setup

### 1. Create Component Structure

```
1. Create Base COMP → rename to "WebSocketControl"
2. Dive inside (press i)
3. Create these operators:
   - Web Server DAT (name: webserver1)
   - Text DAT (name: webserver_callbacks)
   - Constant CHOP (name: constant_params, 3 channels)
   - Constant CHOP (name: constant_color, 3 channels)
   - Constant CHOP (name: constant_xy, 2 channels)
   - Trigger CHOP (name: trigger1)
```

### 2. Load VFS Files

**Option A: Use Python Script**

1. Open Textport (Alt+T)
2. Run:
```python
# Load the script
execfile('C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/load_vfs_files.py')
```

**Option B: Use Palette Component**

1. Open Palette (Alt+L) → Tools → virtualFile
2. Drag into your component
3. Set Folder to: `C:\Users\Erez\Desktop\PROJECTS\DEV_MAIN\td-websocket-V2\public`
4. Click Parse

### 3. Configure Web Server

**webserver1 (Web Server DAT):**
- Port: `9980` (handles BOTH HTTP and WebSocket)
- Active: `On`
- Callbacks DAT: `webserver_callbacks`

**webserver_callbacks (Text DAT):**
- Copy entire contents from `webserver_callbacks.py`

**IMPORTANT:** Web Server DAT handles both HTTP file serving AND WebSocket connections on port 9980.

### 4. Configure CHOPs

**constant_params:**
- Channels: 3
- Channel Names: slider1, slider2, slider3
- Default Values: 50, 50, 50

**constant_color:**
- Channels: 3
- Channel Names: r, g, b
- Default Values: 1, 0, 0

**constant_xy:**
- Channels: 2
- Channel Names: x, y
- Default Values: 0.5, 0.5

**trigger1:**
- (Default settings OK)

### 5. Test It!

1. Check Textport shows:
   - `[Web Server] Started on port 9980`
2. Open browser: `http://localhost:9980`
3. You should see the control UI
4. Click Connect (it will connect to `ws://localhost:9980`)
5. Move sliders → watch CHOP values change in Textport!

### 6. Add Custom Parameters (Makes it User-Friendly!)

1. Press `u` to exit component
2. Right-click `WebSocketControl` → **Customize Component**
3. Add these custom parameters:

**Custom Page:**
- **Port** (Integer, default: 9980) - bind to `webserver1.par.port`
- **Active** (Toggle, default: On) - bind to `webserver1.par.active`
- **Openbrowser** (Pulse button, label: "Open Browser")
- **Status** (String, read-only) - expression: `'Running on port ' + str(parent().par.Port) if parent().par.Active else 'Stopped'`

4. Click **Accept**

5. **Dive inside** component (press `i`)

6. **Create Parameter Execute DAT**:
   - Press `Tab` → "parameter" → **Parameter Execute DAT**
   - Rename to `parameter_callbacks`
   - **Active**: On
   - **OPs**: `..`
   - **Parameters**: `Openbrowser`
   - **On Pulse**: On

7. **Add callback code** inside the Parameter Execute DAT:

```python
def onPulse(par):
    if par.name == 'Openbrowser':
        import webbrowser
        port = par.owner.par.Port.eval()
        webbrowser.open(f'http://localhost:{port}')
```

8. **Test**: Press `u` to exit, click "Open Browser" button

### 7. Create README Inside Component

1. Dive back inside (press `i`)
2. Create a Text DAT named `README`
3. Add usage instructions (see `COMPONENT_SETUP_FOR_EXPORT.md` for content)

### 8. Export .tox

1. Press `u` to exit component
2. Right-click `WebSocketControl` → **Export Component...**
3. Save as `WebSocketControl.tox`

**Done!** 🎉

## File Checklist

Make sure you have these files ready:

- ✅ `webserver_callbacks.py` - HTTP server + WebSocket logic
- ✅ `load_vfs_files.py` - VFS loader script (optional)
- ✅ `public/index.html` - Web UI
- ✅ `public/style.css` - Styles
- ✅ `public/app.js` - WebSocket client

## Using the .tox in Other Projects

Just drag `WebSocketControl.tox` into any TouchDesigner project - it's completely self-contained!

**Super Easy - 3 Steps:**
```
1. Drag .tox file into project
2. Click "Open Browser" button on the component
3. In the web UI, click "Connect"
```

**That's it!** The component auto-starts and you can control TouchDesigner remotely.

### What You Get

The component has these custom parameters for easy control:
- **Port** - Change the port (default: 9980)
- **Active** - Toggle the server on/off
- **Open Browser** - One-click launch of web UI
- **Status** - Shows if server is running

**On mobile devices**, replace `localhost` with your computer's IP address:
- Web page: `http://192.168.1.100:9980`
- WebSocket: `ws://192.168.1.100:9980` (same port!)

## Troubleshooting

**404 Errors in Browser:**
- Verify VFS has files: `print(op('/WebSocketControl').vfs)`
- Check webserver1 Extension 0 = `..`

**WebSocket Won't Connect:**
- Web Server DAT uses port **9980** (handles BOTH HTTP and WebSocket)
- Make sure Web Server DAT is Active
- Verify webserver_callbacks DAT is linked
- Check Textport for errors

**CHOPs Don't Update:**
- Verify CHOP names match exactly (constant_params, constant_color, constant_xy, trigger1)
- Check webserver_callbacks DAT is linked to webserver1
- Look for error messages in Textport when moving sliders

## What's Next?

See `TOUCHDESIGNER_TOX_SETUP.md` for:
- Adding custom parameters
- WebRender TOP integration
- Privacy mode for distribution
- Advanced configuration

---

**You now have a portable WebSocket control system in a single .tox file!** 🚀
