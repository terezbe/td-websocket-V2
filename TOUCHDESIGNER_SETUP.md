# TouchDesigner Setup Guide

Complete guide to set up TouchDesigner to receive data from the web UI via WebSocket.

## Overview

This setup will allow you to control TouchDesigner parameters from the web interface using WebSocket communication. The web UI sends JSON messages that are parsed by a Python callback and converted to CHOP channels.

## Architecture

```
Web UI (Browser)
    ↓ WebSocket Messages (JSON)
WebSocket Server (Node.js on port 9980)
    ↓
WebSocket DAT (TouchDesigner Client)
    ↓
Callbacks DAT (Python Script)
    ↓
Constant CHOPs (Output Data)
```

## Step-by-Step Setup

### 1. Create the WebSocket DAT

1. In TouchDesigner, press **TAB** and type `websocket` to create a **WebSocket DAT**
2. Configure the WebSocket DAT parameters:
   - **Network Address**: `localhost`
   - **Network Port**: `9980`
   - **Active**: ON (check the box)
   - **Auto-Reconnect**: ON (recommended)

### 2. Create the Callbacks DAT

1. Press **TAB** and type `text` to create a **Text DAT**
2. Rename it to `websocket_callbacks` (right-click → Rename)
3. Open the text editor (right-click → Edit Contents or double-click)
4. Copy the entire contents of `touchdesigner_websocket_callback.py` into this Text DAT
5. Close the editor

### 3. Link Callback to WebSocket DAT

1. Click on your **WebSocket DAT**
2. In the parameters panel, find **Callbacks DAT**
3. Drag the `websocket_callbacks` Text DAT into the **Callbacks DAT** parameter field
   - Or click the field and type: `op('websocket_callbacks')`

**IMPORTANT**: The **Callbacks DAT** parameter must be set for the callbacks to work! If this is empty, you won't receive any messages.

### 4. Create the Required Constant CHOPs

You need to create 4 Constant CHOPs to receive the different data types:

#### A. Parameter CHOP (for sliders)

1. Press **TAB** → type `constant` → Create **Constant CHOP**
2. Rename to `constant_params`
3. Set parameters:
   - **Channel Names**: `slider1 slider2 slider3`
   - **Values**: `50 50 50` (default middle position)
4. Name the channels properly:
   - value0 → slider1
   - value1 → slider2
   - value2 → slider3

#### B. Color CHOP

1. Create another **Constant CHOP**
2. Rename to `constant_color`
3. Set parameters:
   - **Channel Names**: `r g b`
   - **Values**: `1 0 0` (default red)

#### C. XY Position CHOP

1. Create another **Constant CHOP**
2. Rename to `constant_xy`
3. Set parameters:
   - **Channel Names**: `x y`
   - **Values**: `0.5 0.5` (default center)

#### D. Trigger CHOP

1. Press **TAB** → type `trigger` → Create **Trigger CHOP**
2. Rename to `trigger1`
3. This will pulse when the trigger button is pressed in the web UI

### 5. Test the Connection

1. **Open the Textport FIRST** - Press **Alt+T** or **Alt+O** in TouchDesigner
   - This is where all debug messages appear
   - Keep it visible during setup!

2. Make sure the WebSocket server is running:
   ```bash
   npm start
   ```

3. In TouchDesigner:
   - Check that the WebSocket DAT is **Active** (parameter is ON)
   - Look at the WebSocket DAT contents - it should show messages appearing

4. Open the web UI in your browser:
   ```
   http://localhost:9980
   ```

5. Click **Connect** in the web UI

6. **You should immediately see in Textport:**
   ```
   ============================================================
   [WebSocket] ✓ CONNECTED to server!
   [WebSocket] DAT: websocket1
   ============================================================
   ```

7. Move a slider or use the XY pad - you should see:
   ```
   ------------------------------------------------------------
   [WebSocket] RAW MESSAGE RECEIVED:
     Row: 0
     Message: {"type":"parameter","name":"slider1","value":75}
   ------------------------------------------------------------
   [WebSocket] Parsed Type: parameter
   [WebSocket] Full Data: {'type': 'parameter', 'name': 'slider1', 'value': 75}
   [WebSocket] Set slider1 to 75
   ```

**If you DON'T see the CONNECTED message:**
- Callbacks DAT is not properly linked
- See troubleshooting section below

## Viewing CHOP Data

### Method 1: Info DAT

1. Create an **Info DAT** (TAB → type `info`)
2. Set the **Operator** parameter to one of your Constant CHOPs
3. Set **CHOP Channels** to ON
4. You'll see all channel names and values in real-time

### Method 2: Direct Parameter View

1. Click on a Constant CHOP
2. In the parameters panel, watch the values update in real-time

### Method 3: CHOP Viewer

1. Click on a Constant CHOP
2. At the bottom of the screen, you'll see the channel values displayed

## Using the Data in Your Project

### Connect to Other Operators

Simply reference the CHOP channels in your project:

```python
# In a parameter expression
op('constant_params')['slider1']

# In Python
slider1_value = op('constant_params')['slider1'].eval()
```

### Export to Parameters

1. Right-click on a Constant CHOP channel
2. Select **Export CHOP**
3. Drag to the parameter you want to control

### Using Math CHOP

If you need to scale or modify the values:

1. Create a **Math CHOP**
2. Set the input to your Constant CHOP
3. Use **Range** or **Multiply** to scale values
   - Example: Scale slider1 (0-100) to (0-1)
   - Math CHOP → Multiply by 0.01

## Message Format Reference

### Messages Sent FROM Web UI TO TouchDesigner

#### Parameter (Slider)
```json
{
  "type": "parameter",
  "name": "slider1",
  "value": 75.5
}
```

#### Color
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

#### XY Pad
```json
{
  "type": "xy",
  "x": 0.75,
  "y": 0.50
}
```

#### Trigger
```json
{
  "type": "trigger",
  "name": "mainTrigger",
  "timestamp": 1234567890
}
```

#### Reset
```json
{
  "type": "reset",
  "timestamp": 1234567890
}
```

### Sending Data FROM TouchDesigner TO Web UI

Use the `sendToWebUI()` function in the callback script:

```python
# In a Script DAT or Execute DAT
parent().sendToWebUI({
    'type': 'parameterUpdate',
    'slider1': 75,
    'slider2': 50,
    'slider3': 25
})
```

Or directly:

```python
import json

# Get reference to WebSocket DAT
ws = op('websocket1')

# Create and send message
message = {
    'type': 'parameterUpdate',
    'slider1': 75
}
ws.sendText(json.dumps(message))
```

## Troubleshooting

### 1. No Messages Appearing in Textport

**Problem**: You don't see the "CONNECTED" message or any message output.

**Diagnosis:**
1. Open Textport (Alt+T)
2. Toggle WebSocket DAT Active OFF then ON
3. Check if you see ANY output

**Common Causes:**
- ❌ **Callbacks DAT parameter is EMPTY** - This is the #1 issue!
- ❌ Callbacks DAT is pointing to wrong operator
- ❌ Text DAT with script is empty or has errors

**Solution:**
1. Click on your WebSocket DAT
2. Look at the **Callbacks DAT** parameter
3. If it's empty, drag your Text DAT (with the Python script) into this field
4. You should see it show: `op('websocket_callbacks')` or similar
5. Toggle Active OFF then ON again
6. You should now see the CONNECTED message when it connects

### 2. WebSocket DAT Not Connecting

**Check:**
- Is the Node.js server running? (`npm start`)
- Is the port correct? (9980)
- Firewall blocking the connection?
- WebSocket DAT **Active** parameter is ON
- WebSocket DAT **Network Address**: `localhost`
- WebSocket DAT **Network Port**: `9980`

**Verify Connection:**
1. Look at the WebSocket DAT viewer (click the DAT)
2. If connected, you might see rows of data
3. Check the Info CHOP for connection status

**Solution:**
- Restart the Node.js server
- Toggle the **Active** parameter OFF then ON
- Check Textport for error messages
- Try connecting to `127.0.0.1` instead of `localhost`

### 3. Connected but No Callback Messages

**Problem**: WebSocket DAT shows data in rows, but Textport shows nothing.

**This means callbacks are NOT set up correctly!**

**Fix:**
1. Verify the **Callbacks DAT** parameter is set on the WebSocket DAT
2. Open your Text DAT and verify the script is there
3. Check for Python syntax errors in the script
4. Make sure the function names are exact: `onConnect`, `onDisconnect`, `onReceiveText`

**Test:**
```python
# Put this simple test in your Text DAT temporarily:
def onConnect(dat):
    print("TEST: CONNECTED!")

def onReceiveText(dat, rowIndex, message):
    print(f"TEST: Got message: {message}")
```

If you see "TEST: CONNECTED!" then your callbacks ARE working and you can add the full script back.

### 4. No Values Updating in CHOPs

**Check:**
- Are the CHOP names correct in the script?
  - `constant_params`
  - `constant_color`
  - `constant_xy`
  - `trigger1`
- Do these CHOPs actually exist in your network?
- Are there error messages in the Textport?

**Solution:**
- Create an Info DAT pointing to your WebSocket DAT to see if messages are arriving
- Rename your CHOPs to match the script, or
- Edit the script to match your CHOP names
- Look for Python errors like "Error: constant_params CHOP not found!"

### 5. Python Errors in Textport

**Check:**
- Is the callback script properly formatted?
- Are there any indentation errors? (Python is strict about tabs/spaces)
- Are the CHOP operators named correctly?

**Solution:**
- Copy the script again from `touchdesigner_websocket_callback.py`
- Use a code editor to check indentation
- Verify CHOP names match between script and network
- Check for typos in function names

### 6. Messages Received but Values Not Changing

**Check:**
- Open Textport and verify messages are being received and parsed
- Look for the "Set slider1 to X" messages
- Check that the message type matches the handler functions
- Verify CHOP parameter names (value0, value1, etc.)

**Solution:**
- Check the Constant CHOP parameters are not locked or driven by another operator
- Verify you're using parameter assignment: `op('constant1').par.value0 = value`
- Ensure the JSON format from web UI matches expected format
- Click on the Constant CHOP and watch the Value parameters to see if they change

### Quick Diagnostic Checklist

Run through this list:

- [ ] Node.js server is running (`npm start`)
- [ ] Web UI can connect (browser shows "Connected")
- [ ] TouchDesigner Textport is open (Alt+T)
- [ ] WebSocket DAT parameter **Active** is ON
- [ ] WebSocket DAT parameter **Callbacks DAT** is SET (not empty!)
- [ ] Text DAT contains the Python callback script
- [ ] When you toggle Active, you see "CONNECTED" in Textport
- [ ] When you move sliders, you see "RAW MESSAGE RECEIVED" in Textport
- [ ] All 4 CHOPs exist: `constant_params`, `constant_color`, `constant_xy`, `trigger1`

**If ALL checkboxes are checked and it's still not working:**
- Copy the error message from Textport
- Check CHOP names in script match your actual CHOP names
- Verify Python indentation is correct (use tabs, not spaces)

## Advanced: Customizing for Your Project

### Changing CHOP Names

In `touchdesigner_websocket_callback.py`, update these lines:

```python
# Line 77 - Parameters CHOP
constantChop = op('constant_params')  # Change to your CHOP name

# Line 119 - Color CHOP
colorChop = op('constant_color')  # Change to your CHOP name

# Line 151 - XY CHOP
xyChop = op('constant_xy')  # Change to your CHOP name

# Line 182 - Trigger CHOP
triggerChop = op('trigger1')  # Change to your CHOP name
```

### Adding New Parameters

1. **In Web UI** (`public/app.js`):
   - Add new UI element
   - Send message with your custom type

2. **In TouchDesigner Callback**:
   - Add new handler function
   - Add case in `onReceiveText()` function

Example:

```python
def handleCustom(data):
    value = data.get('customValue', 0)
    op('my_custom_chop').par.value0 = value

# In onReceiveText():
elif msgType == 'custom':
    handleCustom(data)
```

### Using Relative Paths

If your callback script is inside a component:

```python
# Instead of:
constantChop = op('constant_params')

# Use:
constantChop = op('../constant_params')  # Parent level
# or
constantChop = op('/project1/constant_params')  # Absolute path
```

## Project Layout Example

```
TouchDesigner Network:
├── websocket1 (WebSocket DAT)
├── websocket_callbacks (Text DAT) ← Contains Python script
├── constant_params (Constant CHOP)
├── constant_color (Constant CHOP)
├── constant_xy (Constant CHOP)
├── trigger1 (Trigger CHOP)
└── info1 (Info DAT) ← For debugging
```

## Additional Resources

- [WebSocket DAT Documentation](https://docs.derivative.ca/WebSocket_DAT)
- [Constant CHOP Documentation](https://docs.derivative.ca/Constant_CHOP)
- [Python in TouchDesigner](https://docs.derivative.ca/Introduction_to_Python_Tutorial)
- [TDJSON Module](https://docs.derivative.ca/TDJSON)

## Tips

1. **Use the Textport** - Press `Alt+T` to see all debug messages
2. **Test JSON** - Use the Custom Message sender in the web UI to test different formats
3. **Name Everything** - Use clear, descriptive names for all operators
4. **Component It** - Put everything in a Container COMP for organization
5. **Export Values** - Use CHOP exports to easily connect to other parameters

## Performance Notes

- WebSocket communication is very fast (low latency)
- For high-frequency updates (>60Hz), consider throttling in the web UI
- The callback script is efficient but avoid heavy processing in the handlers
- Use Script CHOP for complex channel manipulation instead of Constant CHOPs

## Next Steps

Once everything is working:
1. Build your interactive visuals
2. Connect the CHOP channels to TOP/SOP/MAT parameters
3. Create presets using the web UI
4. Add more controls as needed
5. Consider using the data to drive generative animations

Enjoy controlling TouchDesigner from your web interface!
