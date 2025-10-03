# TouchDesigner WebSocket Server

A WebSocket server and web UI for controlling TouchDesigner projects in real-time.

## Features

- **Real-time WebSocket Communication** - Bidirectional data exchange between web UI and TouchDesigner
- **Modern Web Interface** - Clean, responsive control panel with dark theme
- **Multiple Control Types**:
  - 3 parameter sliders (0-100 range)
  - Color picker with RGB conversion
  - XY pad for 2D parameter control
  - Trigger buttons
  - Custom JSON message sender
- **Message Logging** - Real-time view of sent/received messages
- **Connection Management** - Visual connection status indicator

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start the Server

```bash
npm start
```

The server will run on `http://localhost:9980`

### 3. Open Web UI

Navigate to `http://localhost:9980` in your browser

### 4. Configure TouchDesigner

#### Option A: TouchDesigner as WebSocket Client (Recommended)

1. In TouchDesigner, add a **WebSocket DAT**
2. Set the WebSocket DAT parameters:
   - **Network Address**: `localhost`
   - **Network Port**: `9980`
   - **Active**: On
3. Add a **DAT Execute** to handle incoming messages
4. Reference the WebSocket DAT in the DAT Execute

#### Option B: Direct Server-to-Server

If you prefer TouchDesigner as the WebSocket server, modify `server.js` to act as a client instead.

## TouchDesigner Setup (WebSocket DAT)

### Basic Callback Example

Create a text DAT with the following Python callback:

```python
def onReceiveText(dat, rowIndex, message):
    try:
        import json
        data = json.loads(message)

        # Handle different message types
        msgType = data.get('type', '')

        if msgType == 'parameter':
            # Update a parameter
            name = data.get('name')
            value = data.get('value')

            # Example: control a Constant CHOP
            op('constant1')[name] = value

        elif msgType == 'color':
            # Update color parameters
            rgb = data.get('rgb')
            op('constant_color')['r'] = rgb['r']
            op('constant_color')['g'] = rgb['g']
            op('constant_color')['b'] = rgb['b']

        elif msgType == 'xy':
            # Update XY position
            op('constant_xy')['x'] = data.get('x')
            op('constant_xy')['y'] = data.get('y')

        elif msgType == 'trigger':
            # Trigger an event
            op('trigger1').par.triggerpulse.pulse()

        elif msgType == 'reset':
            # Reset all parameters
            op('constant1')['slider1'] = 50
            op('constant1')['slider2'] = 50
            op('constant1')['slider3'] = 50

    except Exception as e:
        print(f"Error parsing message: {e}")
```

### Sending Data from TouchDesigner to Web UI

Use a script in TouchDesigner to send data:

```python
import json

# Get reference to WebSocket DAT
ws = op('websocket1')

# Create message
message = {
    'type': 'parameterUpdate',
    'slider1': 75,
    'slider2': 50,
    'slider3': 25
}

# Send message
ws.sendText(json.dumps(message))
```

## Message Format Reference

### From Web UI to TouchDesigner

#### Parameter Update
```json
{
  "type": "parameter",
  "name": "slider1",
  "value": 75.5
}
```

#### Color Change
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

#### Trigger Event
```json
{
  "type": "trigger",
  "name": "mainTrigger",
  "timestamp": 1234567890
}
```

#### Reset All
```json
{
  "type": "reset",
  "timestamp": 1234567890
}
```

### From TouchDesigner to Web UI

#### Parameter Feedback
```json
{
  "type": "parameterUpdate",
  "slider1": 75,
  "slider2": 50,
  "slider3": 25
}
```

## Project Structure

```
td-websocket-server/
├── server.js           # WebSocket server
├── package.json        # Node.js dependencies
├── public/             # Static web files
│   ├── index.html      # Main UI
│   ├── style.css       # Styling
│   └── app.js          # Client-side WebSocket logic
└── README.md           # This file
```

## Customization

### Adding New Parameters

1. **In HTML** (`public/index.html`):
   - Add new input elements in the Parameters section

2. **In JavaScript** (`public/app.js`):
   - Add event listeners
   - Create message handlers
   - Define message format

3. **In TouchDesigner**:
   - Update callback to handle new message types
   - Map to your parameters/operators

### Changing Port

- In `server.js`, change `PORT` constant
- Update WebSocket URL in web UI connection field
- Update TouchDesigner WebSocket DAT port

## Troubleshooting

### Connection Issues

- **Firewall**: Ensure port 9980 is not blocked
- **Server Running**: Check that `npm start` is running without errors
- **Correct URL**: Verify `ws://localhost:9980` in the web UI
- **TouchDesigner Active**: Ensure WebSocket DAT is set to Active

### Message Not Received

- Check message format is valid JSON
- Verify callback is properly attached to WebSocket DAT
- Check TouchDesigner textport for Python errors
- Review message log in web UI

### Performance

- For high-frequency updates (>60Hz), consider throttling
- Use binary messages for large data transfers
- Limit message log to prevent memory issues

## Resources

### Official Documentation
- [TouchDesigner WebSocket DAT](https://docs.derivative.ca/WebSocket_DAT)
- [TouchDesigner Web Server DAT](https://docs.derivative.ca/Web_Server_DAT)

### Tutorials
- [Control TouchDesigner with a Website using WebSockets](https://derivative.ca/community-post/tutorial/part-1-intro-overview-websockets-control-touchdesigner-website-vice-versa)
- [WebWelder Component](https://github.com/djipco/webwelder)

## License

MIT
