"""
TouchDesigner WebSocket Callback Script

This script handles incoming WebSocket messages from the web UI and
extracts values to CHOP channels.

SETUP:
1. Create a WebSocket DAT and configure it to connect to ws://localhost:9980
2. Create a Text DAT and paste this script into it
3. In the WebSocket DAT, set the 'Callbacks DAT' parameter to reference this Text DAT
4. Create the required Constant CHOPs (see setup guide)

MESSAGE TYPES HANDLED:
- parameter: Updates slider values (slider1, slider2, slider3)
- color: Updates RGB color values
- xy: Updates XY pad position
- trigger: Triggers a pulse
- reset: Resets all values to defaults
"""

import json

def onConnect(dat):
	"""
	Callback triggered when WebSocket DAT connects to server.

	Args:
		dat: The WebSocket DAT operator that connected
	"""
	print("=" * 60)
	print("[WebSocket] ✓ CONNECTED to server!")
	print(f"[WebSocket] DAT: {dat.name}")
	print("=" * 60)


def onDisconnect(dat):
	"""
	Callback triggered when WebSocket DAT disconnects from server.

	Args:
		dat: The WebSocket DAT operator that disconnected
	"""
	print("=" * 60)
	print("[WebSocket] ✗ DISCONNECTED from server")
	print(f"[WebSocket] DAT: {dat.name}")
	print("=" * 60)


def onReceiveText(dat, rowIndex, message):
	"""
	Callback triggered when WebSocket DAT receives a text message.

	Args:
		dat: The WebSocket DAT operator that received the message
		rowIndex: Row index in the DAT table
		message: The received text message (JSON string)
	"""

	# Print raw message first (before parsing)
	print("-" * 60)
	print(f"[WebSocket] RAW MESSAGE RECEIVED:")
	print(f"  Row: {rowIndex}")
	print(f"  Message: {message}")
	print("-" * 60)

	try:
		# Parse JSON message
		data = json.loads(message)
		msgType = data.get('type', '')

		# Debug output (visible in textport)
		print(f"[WebSocket] Parsed Type: {msgType}")
		print(f"[WebSocket] Full Data: {data}")

		# Handle different message types
		if msgType == 'parameter':
			handleParameter(data)

		elif msgType == 'color':
			handleColor(data)

		elif msgType == 'xy':
			handleXY(data)

		elif msgType == 'trigger':
			handleTrigger(data)

		elif msgType == 'reset':
			handleReset(data)

		else:
			print(f"[WebSocket] Unknown message type: {msgType}")

	except json.JSONDecodeError as e:
		print(f"[WebSocket] JSON parse error: {e}")
	except Exception as e:
		print(f"[WebSocket] Error handling message: {e}")


def handleParameter(data):
	"""
	Handle parameter updates from sliders.

	Expected data format:
	{
		"type": "parameter",
		"name": "slider1",  // slider1, slider2, or slider3
		"value": 75.5       // 0-100 range
	}
	"""
	try:
		name = data.get('name', '')
		value = data.get('value', 0)

		# Get reference to Constant CHOP (change 'constant_params' to your CHOP name)
		constantChop = op('constant_params')

		if constantChop is None:
			print("[WebSocket] Error: constant_params CHOP not found!")
			return

		# Map slider names to CHOP parameters
		# Constant CHOP parameters are named value0, value1, value2, etc.
		if name == 'slider1':
			constantChop.par.value0 = value
		elif name == 'slider2':
			constantChop.par.value1 = value
		elif name == 'slider3':
			constantChop.par.value2 = value
		else:
			print(f"[WebSocket] Unknown parameter name: {name}")

		print(f"[WebSocket] Set {name} to {value}")

	except Exception as e:
		print(f"[WebSocket] Error in handleParameter: {e}")


def handleColor(data):
	"""
	Handle color picker updates.

	Expected data format:
	{
		"type": "color",
		"hex": "#ff0000",
		"rgb": {
			"r": 1.0,
			"g": 0.0,
			"b": 0.0
		}
	}
	"""
	try:
		rgb = data.get('rgb', {})
		r = rgb.get('r', 0)
		g = rgb.get('g', 0)
		b = rgb.get('b', 0)

		# Get reference to Constant CHOP for color (change 'constant_color' to your CHOP name)
		colorChop = op('constant_color')

		if colorChop is None:
			print("[WebSocket] Error: constant_color CHOP not found!")
			return

		# Set RGB values (normalized 0-1)
		colorChop.par.value0 = r
		colorChop.par.value1 = g
		colorChop.par.value2 = b

		print(f"[WebSocket] Set color to R:{r:.2f} G:{g:.2f} B:{b:.2f}")

	except Exception as e:
		print(f"[WebSocket] Error in handleColor: {e}")


def handleXY(data):
	"""
	Handle XY pad position updates.

	Expected data format:
	{
		"type": "xy",
		"x": 0.75,  // 0-1 range
		"y": 0.50   // 0-1 range
	}
	"""
	try:
		x = data.get('x', 0.5)
		y = data.get('y', 0.5)

		# Get reference to Constant CHOP for XY (change 'constant_xy' to your CHOP name)
		xyChop = op('constant_xy')

		if xyChop is None:
			print("[WebSocket] Error: constant_xy CHOP not found!")
			return

		# Set X and Y values (normalized 0-1)
		xyChop.par.value0 = x
		xyChop.par.value1 = y

		print(f"[WebSocket] Set XY to X:{x:.2f} Y:{y:.2f}")

	except Exception as e:
		print(f"[WebSocket] Error in handleXY: {e}")


def handleTrigger(data):
	"""
	Handle trigger button press.

	Expected data format:
	{
		"type": "trigger",
		"name": "mainTrigger",
		"timestamp": 1234567890
	}
	"""
	try:
		triggerName = data.get('name', 'mainTrigger')

		# Get reference to Trigger CHOP (change 'trigger1' to your CHOP name)
		triggerChop = op('trigger1')

		if triggerChop is None:
			print("[WebSocket] Error: trigger1 CHOP not found!")
			return

		# Pulse the trigger
		triggerChop.par.triggerpulse.pulse()

		print(f"[WebSocket] Triggered: {triggerName}")

	except Exception as e:
		print(f"[WebSocket] Error in handleTrigger: {e}")


def handleReset(data):
	"""
	Handle reset button - resets all parameters to default values.

	Expected data format:
	{
		"type": "reset",
		"timestamp": 1234567890
	}
	"""
	try:
		# Reset sliders to 50 (middle position)
		constantChop = op('constant_params')
		if constantChop:
			constantChop.par.value0 = 50
			constantChop.par.value1 = 50
			constantChop.par.value2 = 50

		# Reset color to red
		colorChop = op('constant_color')
		if colorChop:
			colorChop.par.value0 = 1.0  # R
			colorChop.par.value1 = 0.0  # G
			colorChop.par.value2 = 0.0  # B

		# Reset XY to center
		xyChop = op('constant_xy')
		if xyChop:
			xyChop.par.value0 = 0.5  # X
			xyChop.par.value1 = 0.5  # Y

		print("[WebSocket] Reset all parameters to defaults")

	except Exception as e:
		print(f"[WebSocket] Error in handleReset: {e}")


# Optional: Function to send data back to web UI
def sendToWebUI(data):
	"""
	Send data from TouchDesigner to the web UI.

	Args:
		data: Dictionary to send (will be converted to JSON)

	Example usage:
		sendToWebUI({
			'type': 'parameterUpdate',
			'slider1': 75,
			'slider2': 50,
			'slider3': 25
		})
	"""
	try:
		# Get reference to WebSocket DAT
		ws = op('websocket1')  # Change to your WebSocket DAT name

		if ws is None:
			print("[WebSocket] Error: WebSocket DAT not found!")
			return

		# Convert to JSON and send
		message = json.dumps(data)
		ws.sendText(message)

		print(f"[WebSocket] Sent to web UI: {message}")

	except Exception as e:
		print(f"[WebSocket] Error sending to web UI: {e}")
