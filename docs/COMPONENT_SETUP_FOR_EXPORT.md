# Component Setup for Portable .tox Export

Follow these steps to make your WebSocketControl component completely portable and hassle-free for end users.

## Step 1: Add Custom Parameters

1. **Select the WebSocketControl component** (press `u` to exit it first)
2. **Right-click** → **Customize Component**
3. In the **Custom Parameters** section, add these parameters:

### Custom Page - "Web Control"

**Parameter 1: Port**
- **Name**: `Port`
- **Label**: `Port`
- **Type**: `Integer`
- **Default**: `9980`
- **Bind**: `webserver1.par.port` (link to web server port)

**Parameter 2: Active**
- **Name**: `Active`
- **Label**: `Active`
- **Type**: `Toggle`
- **Default**: `On`
- **Bind**: `webserver1.par.active` (link to web server active)

**Parameter 3: Open Browser**
- **Name**: `Openbrowser`
- **Label**: `Open Browser`
- **Type**: `Pulse`
- **Help**: "Opens web UI in browser"

**Parameter 4: Status (Read-Only Display)**
- **Name**: `Status`
- **Label**: `Status`
- **Type**: `String`
- **Default**: `Ready`
- **Read Only**: `On`
- **Expression**:
  ```python
  'Running on port ' + str(parent().par.Port) if parent().par.Active else 'Stopped'
  ```

## Step 2: Create Parameter Execute DAT for Pulse Callbacks

1. **Click "Accept"** to save the custom parameters and close Component Editor

2. **Dive inside** the WebSocketControl component (press `i`)

3. **Create a Parameter Execute DAT**:
   - Press `Tab` → type "parameter" → **Parameter Execute DAT**
   - Rename to `parameter_callbacks`

4. **Configure the Parameter Execute DAT**:
   - **Active**: `On`
   - **OPs**: `..` (monitors the parent component)
   - **Parameters**: `Openbrowser` (or leave blank to monitor all)
   - **On Pulse**: `On` (checkbox)

5. **Add the onPulse() callback code**:

   Click inside the Parameter Execute DAT and add this code:

```python
# Parameter Execute DAT - Handles custom pulse parameters
# This runs when the "Open Browser" button is clicked

def onPulse(par):
	"""
	Called when custom pulse parameter is pressed.

	Args:
		par: The parameter that was pulsed
	"""
	# Handle "Open Browser" button
	if par.name == 'Openbrowser':
		import webbrowser
		# Get the port from the component's custom parameter
		port = par.owner.par.Port.eval()
		url = f'http://localhost:{port}'
		print("=" * 60)
		print(f"[WebSocketControl] Opening browser to: {url}")
		print("=" * 60)
		webbrowser.open(url)

	return
```

6. **Test the button**:
   - Exit component (press `u`)
   - Click the "Open Browser" parameter
   - Browser should open to http://localhost:9980

## Step 3: Create README Text DAT

1. **While inside the component** (you should still be inside from Step 2)
2. **Create a Text DAT**:
   - Press `Tab` → type "text" → **Text DAT**
   - Rename to `README`
3. **Paste this content** into the README Text DAT:

```
================================================================================
                        WebSocket Control Component
================================================================================

VERSION: 1.0
AUTHOR: Your Name
DATE: 2025-10-03

DESCRIPTION:
This component provides a web-based control interface for TouchDesigner.
Control parameters remotely from any device with a web browser.

================================================================================
QUICK START
================================================================================

1. Set "Active" parameter to ON (it should be on by default)
2. Click "Open Browser" button
3. In the web UI, click "Connect"
4. Control TouchDesigner parameters from the web interface!

================================================================================
ACCESSING FROM MOBILE DEVICES
================================================================================

1. Find your computer's IP address:
   - Windows: Open CMD, type "ipconfig", look for IPv4 Address
   - Mac: System Preferences → Network

2. On your mobile device's browser, go to:
   http://YOUR_PC_IP:9980

   Example: http://192.168.1.100:9980

3. In the web UI connection panel, change WebSocket URL to:
   ws://YOUR_PC_IP:9980

4. Click "Connect" and start controlling!

================================================================================
COMPONENT STRUCTURE
================================================================================

OPERATORS:
- webserver1         - Web Server DAT (serves files + handles WebSocket)
- webserver_callbacks - Python callbacks for HTTP and WebSocket
- virtualFile        - VFS container with HTML/CSS/JS files
- constant_params    - Constant CHOP (3 channels: slider1, slider2, slider3)
- constant_color     - Constant CHOP (3 channels: r, g, b)
- constant_xy        - Constant CHOP (2 channels: x, y)
- trigger1           - Trigger CHOP

WEB FILES (Embedded in VFS):
- index.html         - Web UI interface
- style.css          - Styles
- app.js            - WebSocket client logic

================================================================================
USING THE DATA
================================================================================

To use the control data in your project, reference the CHOPs:

SLIDERS (0-100 range):
- op('WebSocketControl/constant_params')['slider1']
- op('WebSocketControl/constant_params')['slider2']
- op('WebSocketControl/constant_params')['slider3']

COLOR (0-1 range):
- op('WebSocketControl/constant_color')['r']
- op('WebSocketControl/constant_color')['g']
- op('WebSocketControl/constant_color')['b']

XY PAD (0-1 range):
- op('WebSocketControl/constant_xy')['x']
- op('WebSocketControl/constant_xy')['y']

TRIGGER:
- op('WebSocketControl/trigger1')

================================================================================
CUSTOMIZATION
================================================================================

CHANGE PORT:
- Adjust the "Port" parameter on the component (default: 9980)

ADD NEW CONTROLS:
1. Edit web files in VFS (index.html, app.js)
2. Add new message handlers in webserver_callbacks
3. Create new CHOPs to receive the data

MODIFY UI:
- Edit index.html (structure)
- Edit style.css (appearance)
- Edit app.js (functionality)
- Reload VFS files after changes

================================================================================
TROUBLESHOOTING
================================================================================

WEB PAGE WON'T LOAD:
- Check "Active" parameter is ON
- Verify port 9980 is not used by another application
- Check firewall isn't blocking the port

WEBSOCKET WON'T CONNECT:
- Make sure you're using the same port for HTTP and WebSocket (9980)
- Check Textport (Alt+T) for error messages
- Verify webserver_callbacks is linked to webserver1

CHOPS NOT UPDATING:
- Look for error messages in Textport when moving controls
- Verify CHOP names match exactly (constant_params, constant_color, etc.)
- Make sure CHOPs exist and have correct number of channels

================================================================================
TECHNICAL NOTES
================================================================================

- Web Server DAT handles BOTH HTTP and WebSocket on port 9980
- All web files are embedded in VFS (no external dependencies)
- Component is completely self-contained and portable
- Works offline - no internet connection required
- Supports multiple simultaneous connections

================================================================================
```

4. **Save the Text DAT**

## Step 4: Verify VFS Files Are Loaded

1. **Select virtualFile component** inside WebSocketControl
2. **Check VFS contains**:
   - index.html
   - style.css
   - app.js
3. **If missing**, load them:
   - Set Folder parameter to: `C:\Users\Erez\Desktop\PROJECTS\DEV_MAIN\td-websocket-V2\public`
   - Click **Parse** button

## Step 5: Verify All Operators Exist

Inside WebSocketControl component, verify these operators exist:

- ✅ `webserver1` (Web Server DAT)
  - Port: 9980
  - Active: On
  - Callbacks DAT: `webserver_callbacks`

- ✅ `webserver_callbacks` (Text DAT)
  - Contains code from `webserver_callbacks.py`

- ✅ `virtualFile` (VirtualFile component)
  - Contains 3 files in VFS

- ✅ `constant_params` (Constant CHOP)
  - 3 channels: slider1, slider2, slider3
  - Default values: 50, 50, 50

- ✅ `constant_color` (Constant CHOP)
  - 3 channels: r, g, b
  - Default values: 1, 0, 0

- ✅ `constant_xy` (Constant CHOP)
  - 2 channels: x, y
  - Default values: 0.5, 0.5

- ✅ `trigger1` (Trigger CHOP)

- ✅ `README` (Text DAT)
  - Contains usage instructions

## Step 6: Test Before Export

1. **Exit component** (press `u`)
2. **Check custom parameters** appear on component
3. **Click "Open Browser"** - should open web page
4. **Test from mobile device** if available
5. **Verify all controls work**:
   - Sliders → CHOP values update
   - Color picker → RGB CHOP updates
   - XY pad → XY CHOP updates
   - Trigger button → Trigger CHOP pulses

## Step 7: Export .tox

1. **Right-click** on WebSocketControl component
2. **Export Component...**
3. **Save as**: `WebSocketControl.tox`
4. **Choose location**: Desktop or shared folder

## Step 8: Test the .tox

1. **Open a new TouchDesigner project**
2. **Drag WebSocketControl.tox** into the project
3. **Component should auto-start** (Active = On)
4. **Click "Open Browser"**
5. **Verify everything works**

## Optional: Enable Privacy Mode (Pro Only)

To prevent users from extracting your web files:

1. **Select WebSocketControl component**
2. **Component Parameters** → **Privacy**
3. **Enable "Private" toggle**
4. **Re-export the .tox**

This encrypts the VFS and prevents reverse-engineering.

---

## Final Checklist Before Sharing

- ✅ Custom parameters added and working
- ✅ Component callbacks added (Open Browser works)
- ✅ README Text DAT created inside component
- ✅ All VFS files loaded (3 files)
- ✅ All CHOPs created with correct names
- ✅ webserver_callbacks code is up-to-date
- ✅ Web Server DAT Active = On by default
- ✅ Tested in fresh TouchDesigner project
- ✅ Works on mobile device (optional)
- ✅ Privacy mode enabled (optional, Pro only)

**Your .tox is now ready to share!** 🎉

Recipients just need to:
1. Drag .tox into project
2. Click "Open Browser"
3. Control TouchDesigner remotely!
