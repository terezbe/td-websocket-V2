# Web Server DAT Setup Guide

Complete guide to set up TouchDesigner's Web Server DAT to serve the UI Builder and Viewer directly from TouchDesigner.

## Overview

The Web Server DAT replaces the Node.js server, making the .tox file completely self-contained. It serves HTML/CSS/JS files from the Virtual File System (VFS) and provides an API to save/load UI configurations.

## Benefits

✅ **Fully Portable** - Everything embedded in the .tox file
✅ **No External Dependencies** - No Node.js required
✅ **Persistent Storage** - Config saved in TouchDesigner Text DAT
✅ **Single Port** - HTTP and WebSocket on port 9980

---

## Step-by-Step Setup

### 1. Create the Web Server DAT

1. In TouchDesigner, press **TAB** and type `webserver`
2. Create a **Web Server DAT**
3. Configure parameters:
   - **Active**: ON
   - **Port**: 9980
   - **Auto-Start**: ON (recommended)

### 2. Create the Callbacks DAT

1. Press **TAB** and type `text` to create a **Text DAT**
2. Rename it to `webserver_callbacks`
3. Open the text editor (double-click)
4. Copy the entire contents of `touchdesigner/webserver_complete_callbacks.py` into this Text DAT
   - This script contains ALL callbacks: HTTP (API) + WebSocket (control messages)
5. Close the editor

### 3. Link Callback to Web Server DAT

1. Click on your **Web Server DAT**
2. In the parameters panel, find **Callbacks DAT**
3. Drag the `webserver_callbacks` Text DAT into the **Callbacks DAT** parameter field
   - Or type: `op('webserver_callbacks')`

**IMPORTANT**: The **Callbacks DAT** parameter must be set for API endpoints to work!

### 4. Create the UI Config Storage

1. Press **TAB** and type `text` to create another **Text DAT**
2. Rename it to `ui_config`
3. Leave it empty (config will be saved here automatically)

This Text DAT will store your UI configuration as JSON.

### 5. Load Web Files into VFS

You need to add the HTML/CSS/JS files to the component's Virtual File System.

#### Option A: Using the VFS Parameter (Easiest)

1. Click on the **Web Server DAT**
2. Find the **VFS** parameter
3. Drag your component (or type the path to the component containing VFS files)

#### Option B: Using the Python Loader Script

1. Open Textport (Alt+T)
2. Run the loader script:
   ```python
   execfile('C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/touchdesigner/load_vfs_files.py')
   ```

#### Option C: Using virtualFile Component

1. Create a **virtualFile** component
2. Set **Folder** parameter to: `C:\Users\Erez\Desktop\PROJECTS\DEV_MAIN\td-websocket-V2\public`
3. Click **Parse** button

#### Files to Load

Verify these 6 files are in VFS:
- ✅ index.html (viewer)
- ✅ style.css (viewer styles)
- ✅ app.js (viewer logic)
- ✅ builder.html (builder)
- ✅ builder.css (builder styles)
- ✅ builder.js (builder logic)

### 6. Test the Setup

1. **Check Textport** (Alt+T) - you should see:
   ```
   ============================================================
   [WebServer] ✓ Web Server STARTED
   [WebServer] Port: 9980
   [WebServer] Access builder at: http://localhost:9980/builder.html
   [WebServer] Access viewer at: http://localhost:9980/
   ============================================================
   ```

2. **Open Builder** in browser:
   ```
   http://localhost:9980/builder.html
   ```

3. **Create some controls** in the builder

4. **Click "Save to TD"** button
   - You should see: "✓ Configuration saved to TouchDesigner!"
   - Check `ui_config` Text DAT - it should now contain JSON

5. **Open Viewer** in browser:
   ```
   http://localhost:9980/
   ```
   - Should automatically load config from TouchDesigner
   - You should see your controls!

---

## API Endpoints

The Web Server DAT provides these endpoints:

### GET /api/config

Load UI configuration from `ui_config` Text DAT.

**Response:**
```json
{
  "version": "1.0",
  "pages": [...]
}
```

### POST /api/config

Save UI configuration to `ui_config` Text DAT.

**Request Body:**
```json
{
  "version": "1.0",
  "pages": [...]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Config saved to TouchDesigner"
}
```

---

## Project Structure

```
TouchDesigner Network:
├── webserver1 (Web Server DAT) ← ONE server for HTTP + WebSocket
├── webserver_callbacks (Text DAT) ← ALL callbacks (HTTP + WebSocket)
├── ui_config (Text DAT) ← UI configuration storage
├── constant_params (Constant CHOP) ← Slider values
├── constant_color (Constant CHOP) ← Color RGB values
├── constant_xy (Constant CHOP) ← XY pad position
└── trigger1 (Trigger CHOP) ← Trigger pulses
```

**IMPORTANT**: You only need ONE Web Server DAT! It handles both:
- HTTP requests (serving web pages and /api/config endpoints)
- WebSocket connections (real-time control messages)

No separate WebSocket DAT is needed.

---

## Workflow

### Design Workflow

1. **Open Builder**: `http://localhost:9980/builder.html`
2. **Add controls** using the palette
3. **Configure properties** for each control
4. **Click "Save to TD"** - saves to `ui_config` Text DAT
5. **Config is now embedded in .tox file!**

### Usage Workflow

1. **Open Viewer**: `http://localhost:9980/`
2. **Viewer loads config from TouchDesigner automatically**
3. **Control UI appears based on your design**
4. **Move controls** - values sent to TouchDesigner CHOPs

### Sharing Workflow

1. **Save your .tox file** - config is embedded
2. **Share .tox** with others
3. **Recipients open .tox** - everything works!
4. No need to share JSON files separately

---

## Troubleshooting

### Web Server Not Starting

**Check:**
- Active parameter is ON
- Port 9980 is not used by another application
- Look at Textport for error messages

**Solution:**
- Toggle Active OFF then ON
- Try a different port (update in viewer/builder too)
- Close other applications using port 9980

### "Save to TD" Button Not Working

**Check:**
- Web Server DAT is Active
- Callbacks DAT parameter is set
- `ui_config` Text DAT exists
- Open browser console (F12) for errors

**Solution:**
1. Verify Web Server DAT Active = ON
2. Check Callbacks DAT parameter points to `webserver_callbacks`
3. Create `ui_config` Text DAT if missing
4. Look at Textport for Python errors

### Files Not Loading (404 Error)

**Check:**
- VFS parameter is set on Web Server DAT
- Files are actually in VFS (check component.vfs in Python)
- File names are correct (case-sensitive!)

**Solution:**
- Re-run VFS loader script
- Check VFS parameter points to correct component
- List VFS contents:
  ```python
  for f in op('component').vfs:
      print(f.name)
  ```

### Config Not Persisting

**Problem**: Config disappears when reloading TouchDesigner

**Check:**
- `ui_config` Text DAT contains JSON (click to view)
- You clicked "Save to TD" in builder
- .tox file is saved after updating config

**Solution:**
1. Click "Save to TD" in builder
2. Verify `ui_config` has content
3. Save your .tox file (File → Save Component)

### Viewer Shows Default Config

**Check:**
- Config was saved to TouchDesigner
- `ui_config` Text DAT is not empty
- Browser console (F12) shows where config loaded from

**Solution:**
1. Check `ui_config` Text DAT content
2. Click "Load from TD" in builder to test
3. Clear browser cache and reload
4. Check browser console logs

---

## Advanced

### Custom API Endpoints

Add your own endpoints in `touchdesigner/webserver_complete_callbacks.py`:

```python
def onHTTPRequest(webServerDAT, request, response):
    uri = request['uri']
    method = request['method']

    # Your custom endpoint
    if uri == '/api/custom' and method == 'GET':
        response['statusCode'] = 200
        response['data'] = '{"custom": "data"}'
        response['content-type'] = 'application/json'
        return response

    # ... existing code for /api/config
```

### CHOP Names in Config

The config now includes CHOP names per control:

```json
{
  "id": "speed",
  "type": "slider",
  "chop": "constant_params",
  "channel": 1
}
```

This allows multiple controls to target different CHOPs dynamically.

### WebSocket + HTTP on Same Port

The Web Server DAT handles both on port 9980:
- **HTTP requests** - Serves web pages (index.html, builder.html) and API endpoints (/api/config)
- **WebSocket connections** - Receives real-time control messages from browser

All callbacks (HTTP and WebSocket) are in ONE callback script. When the browser connects via WebSocket to `ws://localhost:9980`, the same Web Server DAT that serves the HTML files also handles the WebSocket messages.

---

## Migration from Node.js Server

### Current Setup (Node.js)
- Run `npm start` to start server
- Files served from `public/` folder
- Config in LocalStorage only

### New Setup (Web Server DAT)
- Web Server DAT always active
- Files served from VFS (embedded in .tox)
- Config in Text DAT (embedded in .tox)

### Both Can Coexist
You can use both during development:
- **Node.js** for fast iteration (auto-reload files)
- **Web Server DAT** for deployment (.tox export)

---

## Next Steps

1. ✅ Set up Web Server DAT
2. ✅ Load files into VFS
3. ✅ Create `ui_config` Text DAT
4. ✅ Test builder and viewer
5. 🎯 Design your UI in builder
6. 🎯 Save .tox file with config embedded
7. 🎯 Share portable .tox file!

Enjoy your fully self-contained TouchDesigner control interface!
