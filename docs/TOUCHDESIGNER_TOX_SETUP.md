# TouchDesigner .tox Setup Guide

This guide explains how to package the WebSocket Control UI into a self-contained TouchDesigner .tox file.

## Overview

The .tox file will contain:
- Web UI files (HTML/CSS/JS) embedded in Virtual File System (VFS)
- Web Server DAT to serve the UI to browsers
- WebSocket DAT for bidirectional communication
- CHOP operators for parameter storage

## Architecture

```
WebSocketControl (Base COMP)
├── VFS (Virtual File System)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── webserver1 (Web Server DAT) - Serves files from VFS on port 9980
├── webserver_callbacks (Text DAT) - Python callbacks for HTTP requests
├── websocket1 (WebSocket DAT) - Handles WebSocket connections
├── websocket_callbacks (Text DAT) - Python callbacks for messages
├── constant_params (Constant CHOP) - 3 channels: slider1, slider2, slider3
├── constant_color (Constant CHOP) - 3 channels: r, g, b
├── constant_xy (Constant CHOP) - 2 channels: x, y
└── trigger1 (Trigger CHOP)
```

## Step-by-Step Setup

### 1. Create Base Component

1. In TouchDesigner, create a new **Base COMP** (right-click → Add Component → Misc → Base COMP)
2. Rename it to `WebSocketControl`
3. Dive inside the component (press `i`)

### 2. Add VFS Files from Palette

1. Open the **Palette** browser (press `Alt+L` or View → Palette Browser)
2. Navigate to **Tools** → **virtualFile**
3. Drag the `virtualFile` component into your `WebSocketControl` component
4. Rename it to `vfs_manager` (optional, for clarity)

### 3. Load Web Files into VFS

**Method A: Using virtualFile Component UI**

1. In the `virtualFile` component's parameters panel:
   - Click the **Folder** parameter
   - Browse to `C:\Users\Erez\Desktop\PROJECTS\DEV_MAIN\td-websocket-V2\public`
   - Click **Parse** button to load all files

2. Verify files are loaded:
   - Open the **VFS** parameter page
   - You should see: index.html, style.css, app.js

**Method B: Using Python Script**

Run this in the Textport (Alt+T):

```python
# Get reference to your component
comp = op('/WebSocketControl')

# Load files from disk into VFS
publicFolder = 'C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/public'

files = [
    'index.html',
    'style.css',
    'app.js'
]

for filename in files:
    filepath = f'{publicFolder}/{filename}'
    comp.vfs.addFile(filepath, filename)
    print(f'✓ Added {filename} to VFS')

print(f'Total VFS files: {len(comp.vfs)}')
```

### 4. Create Web Server DAT

1. **Create Web Server DAT**:
   - Press `Tab` → type "web server" → select **Web Server DAT**
   - Rename to `webserver1`

2. **Configure Web Server**:
   - **Port**: `9980`
   - **Active**: `On`
   - **Extension 0**: `..` (points to parent component where VFS files are)

3. **Create Callbacks Text DAT**:
   - Press `Tab` → type "text" → select **Text DAT**
   - Rename to `webserver_callbacks`
   - Copy contents from `webserver_callbacks.py` into this DAT

4. **Link Callbacks**:
   - In `webserver1` parameters → **Callbacks DAT**: `webserver_callbacks`

### 5. Create WebSocket DAT

1. **Create WebSocket DAT**:
   - Press `Tab` → type "websocket" → select **WebSocket DAT**
   - Rename to `websocket1`

2. **Configure WebSocket**:
   - **Active**: `On`
   - **Network Type**: `Server`
   - **Port**: `9980` (same as Web Server - they can share)
   - **Protocol**: `ws`

3. **Create WebSocket Callbacks Text DAT**:
   - Press `Tab` → type "text" → select **Text DAT**
   - Rename to `websocket_callbacks`
   - Copy contents from `touchdesigner_websocket_callback.py` into this DAT

4. **Link Callbacks**:
   - In `websocket1` parameters → **Callbacks DAT**: `websocket_callbacks`

### 6. Create CHOP Operators

1. **Create Constant CHOP for Sliders**:
   - Press `Tab` → type "constant" → select **Constant CHOP**
   - Rename to `constant_params`
   - **Channels**: `3`
   - **Name0**: `slider1`, **Value0**: `50`
   - **Name1**: `slider2`, **Value1**: `50`
   - **Name2**: `slider3`, **Value2**: `50`

2. **Create Constant CHOP for Color**:
   - Create another **Constant CHOP**
   - Rename to `constant_color`
   - **Channels**: `3`
   - **Name0**: `r`, **Value0**: `1`
   - **Name1**: `g`, **Value1**: `0`
   - **Name2**: `b`, **Value2**: `0`

3. **Create Constant CHOP for XY**:
   - Create another **Constant CHOP**
   - Rename to `constant_xy`
   - **Channels**: `2`
   - **Name0**: `x`, **Value0**: `0.5`
   - **Name1**: `y`, **Value1**: `0.5`

4. **Create Trigger CHOP**:
   - Press `Tab` → type "trigger" → select **Trigger CHOP**
   - Rename to `trigger1`

### 7. Create Custom Parameters (Optional)

1. **Exit the component** (press `u`)
2. **Right-click** on `WebSocketControl` → **Customize Component**
3. **Add Custom Parameters**:

   **Custom Page**:
   - Add **Pulse Button**: `Open Browser`
     - Callback: `op('webserver1').par.port`
   - Add **Toggle**: `Server Active`
     - Bind to: `webserver1.par.active`
   - Add **Integer**: `Port`
     - Bind to: `webserver1.par.port`
     - Default: `9980`

4. **Add Python Callbacks**:
   In the **Callbacks** page, add this code to open browser on button press:

```python
def onPulse(par):
    if par.name == 'Openbrowser':
        import webbrowser
        port = parent().par.Port.eval()
        webbrowser.open(f'http://localhost:{port}')
```

### 8. Test the Component

1. **Start the Server**:
   - Make sure `webserver1` is **Active**
   - Check the Textport (Alt+T) for: `[Web Server] Started on port 9980`

2. **Open in Browser**:
   - Open browser to: `http://localhost:9980`
   - You should see the WebSocket Control UI

3. **Test Controls**:
   - Move sliders → check `constant_params` CHOP values update
   - Change color → check `constant_color` CHOP values update
   - Move XY pad → check `constant_xy` CHOP values update
   - Click Trigger → check `trigger1` CHOP pulses

4. **Monitor Connections**:
   - Textport should show WebSocket connection messages
   - Server should show HTTP requests for HTML/CSS/JS files

### 9. Export as .tox

1. **Exit the component** (press `u` to go to root)
2. **Right-click** on `WebSocketControl` component
3. **Export Component...**
4. Save as: `WebSocketControl.tox`

**The .tox file is now completely self-contained!**

## Usage in Other Projects

1. Drag `WebSocketControl.tox` into any TouchDesigner project
2. The component automatically starts the web server
3. Open `http://localhost:9980` in any browser
4. Control TouchDesigner remotely!

## Troubleshooting

### Files Not Loading (404 Error)

**Problem**: Browser shows 404 errors for HTML/CSS/JS

**Solution**:
- Check VFS has files: `print(op('/WebSocketControl').vfs)`
- Verify `webserver1` → **Extension 0** parameter is set to `..`
- Check Textport for VFS path errors

### WebSocket Not Connecting

**Problem**: Web UI shows "Disconnected"

**Solution**:
- Verify `websocket1` is **Active**
- Check port numbers match (9980)
- Verify `websocket_callbacks` DAT is linked correctly
- Check firewall isn't blocking port

### CHOPs Not Updating

**Problem**: Moving sliders doesn't update CHOP values

**Solution**:
- Verify CHOP names match callback script:
  - `constant_params`
  - `constant_color`
  - `constant_xy`
  - `trigger1`
- Check Textport for Python errors
- Verify callbacks DAT is linked to WebSocket DAT

### Port Already in Use

**Problem**: Server won't start, error about port in use

**Solution**:
- Change port number to 9981 or other available port
- Update both Web Server DAT and WebSocket DAT to use same port
- Update browser URL to match new port

## Advanced: Optional WebRender TOP

To display the UI **inside TouchDesigner**:

1. **Create WebRender TOP**:
   - Press `Tab` → type "webrender" → **WebRender TOP**
   - Rename to `ui_render`

2. **Configure**:
   - **URL**: `http://localhost:9980`
   - **Active**: `On`
   - **Enable Mouse/Keyboard**: `On` (for interaction)

3. **View**:
   - The web UI will render as a texture
   - You can display this on screens, projections, etc.

## Files Reference

**Required Files**:
- `webserver_callbacks.py` → Copy into `webserver_callbacks` Text DAT
- `touchdesigner_websocket_callback.py` → Copy into `websocket_callbacks` Text DAT
- `public/index.html` → Load into VFS
- `public/style.css` → Load into VFS
- `public/app.js` → Load into VFS

**Component Structure**:
```
WebSocketControl.tox
│
├── Virtual File System (VFS)
│   ├── /index.html
│   ├── /style.css
│   └── /app.js
│
├── webserver1 (Web Server DAT)
├── webserver_callbacks (Text DAT)
├── websocket1 (WebSocket DAT)
├── websocket_callbacks (Text DAT)
│
├── constant_params (Constant CHOP)
├── constant_color (Constant CHOP)
├── constant_xy (Constant CHOP)
└── trigger1 (Trigger CHOP)
```

## Privacy & Distribution

**VFS Privacy Mode** (TouchDesigner Pro only):

To prevent users from extracting your web files:

1. Select `WebSocketControl` component
2. **Component Parameters** → **Privacy**
3. Enable **Private** toggle
4. VFS files will be encrypted in the .tox

This prevents reverse-engineering of your web UI code.

## Next Steps

- Add more controls to the web UI
- Integrate with other TouchDesigner networks
- Create custom parameters for dynamic configuration
- Add authentication for remote access
- Package with WebRender TOP for standalone installations

---

**You now have a portable, self-contained WebSocket control system!** 🎉
