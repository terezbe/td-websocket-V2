"""
TouchDesigner Web Server DAT - Complete Callback Script

This single script handles ALL Web Server DAT functionality:
- HTTP requests (serving pages, API endpoints)
- WebSocket connections (control messages)
- Server lifecycle events

SETUP:
1. Create a Web Server DAT
   - Active: ON
   - Port: 9980
   - Auto-Start: ON

2. Create a Text DAT and paste this script into it
   - Rename to 'webserver_callbacks'

3. In Web Server DAT parameters:
   - Callbacks DAT: point to the Text DAT with this script
   - VFS: point to component containing web files

4. Create a Text DAT named 'ui_config' to store UI configuration

5. Load web files into VFS (using load_vfs_files.py or virtualFile)

That's it! One Web Server DAT does everything - HTTP + WebSocket on port 9980.

API ENDPOINTS:
- GET  /api/config - Load UI config from ui_config Text DAT
- POST /api/config - Save UI config to ui_config Text DAT

WEBSOCKET MESSAGES:
- parameter: Updates slider values (dynamic CHOP routing)
- color: Updates RGB color values
- xy: Updates XY pad position
- trigger: Triggers a pulse
- reset: Resets all values to defaults
"""

import json

# ============================================================================
# CONFIGURATION
# ============================================================================

# IMPORTANT: Set this to the component containing your VFS files!
# Examples:
#   VFS_COMPONENT = 'virtualFile'  # if virtualFile is at same level
#   VFS_COMPONENT = '/project1/WebSocketControl/virtualFile'  # absolute path
VFS_COMPONENT = 'virtualFile'  # ← UPDATE THIS PATH!

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def getMimeType(filename):
	"""Get MIME type based on file extension."""
	if filename.endswith('.html'):
		return 'text/html'
	elif filename.endswith('.css'):
		return 'text/css'
	elif filename.endswith('.js'):
		return 'application/javascript'
	elif filename.endswith('.json'):
		return 'application/json'
	elif filename.endswith('.png'):
		return 'image/png'
	elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
		return 'image/jpeg'
	elif filename.endswith('.svg'):
		return 'image/svg+xml'
	elif filename.endswith('.ico'):
		return 'image/x-icon'
	else:
		return 'application/octet-stream'

# ============================================================================
# HTTP CALLBACKS (API + File Serving)
# ============================================================================

def onHTTPRequest(webServerDAT, request, response):
	"""
	Handle HTTP requests - both API endpoints and static file serving.

	Args:
		webServerDAT: The Web Server DAT operator
		request: Dictionary with request data (uri, method, data, etc.)
		response: Dictionary to populate with response (statusCode, data, etc.)

	Returns:
		response: Modified response dictionary
	"""

	uri = request.get('uri', '/')
	method = request.get('method', 'GET')

	print(f"[WebServer] {method} {uri}")

	# ========================================================================
	# API: GET /api/config - Load UI configuration
	# ========================================================================
	if uri == '/api/config' and method == 'GET':
		try:
			config_dat = op('ui_config')

			if config_dat is None:
				print("[WebServer] Warning: ui_config DAT not found - using empty config")
				response['statusCode'] = 200
				response['statusReason'] = 'OK'
				response['data'] = json.dumps({
					"version": "1.0",
					"pages": [{"id": "page1", "name": "Default", "controls": []}]
				})
			else:
				config_text = config_dat.text

				if not config_text or config_text.strip() == '':
					print("[WebServer] ui_config is empty - using default config")
					response['statusCode'] = 200
					response['statusReason'] = 'OK'
					response['data'] = json.dumps({
						"version": "1.0",
						"pages": [{"id": "page1", "name": "Default", "controls": []}]
					})
				else:
					try:
						json.loads(config_text)  # Validate JSON
						response['statusCode'] = 200
						response['statusReason'] = 'OK'
						response['data'] = config_text
						print(f"[WebServer] Loaded config from ui_config ({len(config_text)} bytes)")
					except json.JSONDecodeError:
						print("[WebServer] Error: ui_config contains invalid JSON")
						response['statusCode'] = 500
						response['statusReason'] = 'Internal Server Error'
						response['data'] = json.dumps({"error": "Invalid JSON in ui_config"})

			response['content-type'] = 'application/json'
			return response

		except Exception as e:
			print(f"[WebServer] Error in GET /api/config: {e}")
			response['statusCode'] = 500
			response['statusReason'] = 'Internal Server Error'
			response['data'] = json.dumps({"error": str(e)})
			response['content-type'] = 'application/json'
			return response

	# ========================================================================
	# API: POST /api/config - Save UI configuration
	# ========================================================================
	elif uri == '/api/config' and method == 'POST':
		try:
			config_dat = op('ui_config')

			if config_dat is None:
				print("[WebServer] Error: ui_config DAT not found")
				response['statusCode'] = 404
				response['statusReason'] = 'Not Found'
				response['data'] = json.dumps({"error": "ui_config DAT not found"})
			else:
				config_json = request.get('data', '')

				try:
					json.loads(config_json)  # Validate JSON

					config_dat.text = config_json

					response['statusCode'] = 200
					response['statusReason'] = 'OK'
					response['data'] = json.dumps({"success": True, "message": "Config saved to TouchDesigner"})
					print(f"[WebServer] Saved config to ui_config ({len(config_json)} bytes)")

				except json.JSONDecodeError as e:
					print(f"[WebServer] Error: Invalid JSON in POST data - {e}")
					response['statusCode'] = 400
					response['statusReason'] = 'Bad Request'
					response['data'] = json.dumps({"error": "Invalid JSON format", "details": str(e)})

			response['content-type'] = 'application/json'
			return response

		except Exception as e:
			print(f"[WebServer] Error in POST /api/config: {e}")
			response['statusCode'] = 500
			response['statusReason'] = 'Internal Server Error'
			response['data'] = json.dumps({"error": str(e)})
			response['content-type'] = 'application/json'
			return response

	# ========================================================================
	# VFS: Serve static files from Virtual File System
	# ========================================================================
	else:
		try:
			# Map URI to filename
			filename = uri.lstrip('/')  # Remove leading slash
			if filename == '' or filename == '/':
				filename = 'index.html'

			# Get VFS component
			vfs_comp = op(VFS_COMPONENT)

			if vfs_comp is None:
				print(f"[WebServer] Error: VFS component '{VFS_COMPONENT}' not found!")
				print(f"[WebServer] Please update VFS_COMPONENT path in callback script")
				response['statusCode'] = 500
				response['statusReason'] = 'Internal Server Error'
				response['data'] = 'VFS component not found - check callback script configuration'
				return response

			# Try to get file from VFS
			# Use .find() to get list of VFSFile objects (official API)
			vfs_file = None
			all_vfs_files = vfs_comp.vfs.find()  # Returns list of VFSFile objects

			for file_obj in all_vfs_files:
				# file_obj.name is just the filename (portable!)
				if file_obj.name == filename:
					vfs_file = file_obj
					break

			if vfs_file is None:
				print(f"[WebServer] Error: File '{filename}' not found in VFS")
				print(f"[WebServer] Available files:")
				for file_obj in all_vfs_files:
					print(f"[WebServer]   - {file_obj.name}")
				response['statusCode'] = 404
				response['statusReason'] = 'Not Found'
				response['data'] = f'File not found: {filename}'
				return response

			# Read file from VFS
			file_data = vfs_file.byteArray
			file_size = vfs_file.size

			# Set response
			response['statusCode'] = 200
			response['statusReason'] = 'OK'
			response['data'] = file_data
			response['content-type'] = getMimeType(filename)

			# Get client IP for logging
			client_ip = request.get('clientAddress', 'unknown')

			print("-" * 60)
			print(f"[Web Server] GET /{filename}")
			print(f"[Web Server] Client: {client_ip}")
			print(f"[Web Server] ✓ Served: {filename} ({file_size} bytes, {response['content-type']})")
			print("-" * 60)

			return response

		except Exception as e:
			print("-" * 60)
			print(f"[Web Server] GET {uri}")
			print(f"[Web Server] Client: {request.get('clientAddress', 'unknown')}")
			print(f"[Web Server] Error serving file: {e} Context:{parent().path}")
			print("-" * 60)
			response['statusCode'] = 500
			response['statusReason'] = 'Internal Server Error'
			response['data'] = str(e)
			return response


# ============================================================================
# WEBSOCKET CALLBACKS (Control Messages)
# ============================================================================

def onWebSocketOpen(webServerDAT, client, uri):
	"""
	Callback when a WebSocket connection is opened.

	Args:
		webServerDAT: The Web Server DAT operator
		client: Client info dictionary
		uri: Requested URI
	"""
	print("=" * 60)
	print("[WebSocket] ✓ Client CONNECTED")
	print(f"[WebSocket] URI: {uri}")
	print("=" * 60)

	# Send welcome message
	welcome = {
		'type': 'connection',
		'message': 'Connected to TouchDesigner WebSocket Server',
		'timestamp': int(me.time.seconds * 1000)
	}
	webServerDAT.webSocketSendText(client, json.dumps(welcome))


def onWebSocketClose(webServerDAT, client):
	"""
	Callback when a WebSocket connection is closed.

	Args:
		webServerDAT: The Web Server DAT operator
		client: Client info dictionary
	"""
	print("=" * 60)
	print("[WebSocket] ✗ Client DISCONNECTED")
	print("=" * 60)


def onWebSocketReceiveText(webServerDAT, client, data):
	"""
	Callback when WebSocket receives text data (control messages).

	Args:
		webServerDAT: The Web Server DAT operator
		client: Client info dictionary
		data: Received text message (JSON string)
	"""

	print("-" * 60)
	print(f"[WebSocket] RAW MESSAGE RECEIVED:")
	print(f"  Data: {data}")
	print("-" * 60)

	try:
		message = json.loads(data)
		msgType = message.get('type', '')

		print(f"[WebSocket] Parsed Type: {msgType}")
		print(f"[WebSocket] Full Data: {message}")

		# Handle different message types
		if msgType == 'parameter':
			handleParameter(message)

		elif msgType == 'color':
			handleColor(message)

		elif msgType == 'xy':
			handleXY(message)

		elif msgType == 'trigger':
			handleTrigger(message)

		elif msgType == 'reset':
			handleReset(message)

		else:
			print(f"[WebSocket] Unknown message type: {msgType}")

	except json.JSONDecodeError as e:
		print(f"[WebSocket] JSON parse error: {e}")
	except Exception as e:
		print(f"[WebSocket] Error handling message: {e}")


# ============================================================================
# MESSAGE HANDLERS (CHOP Updates)
# ============================================================================

def handleParameter(data):
	"""
	Handle parameter updates from sliders.

	New format (with dynamic CHOP routing):
	{
		"type": "parameter",
		"id": "speed_slider",
		"value": 150,
		"chop": "constant_params",
		"channel": 1
	}

	Legacy format (still supported):
	{
		"type": "parameter",
		"name": "slider1",
		"value": 75.5
	}
	"""
	try:
		# Check for new format (with chop and channel)
		if 'chop' in data and 'channel' in data:
			# New dynamic format
			chop_name = data.get('chop', '')
			channel = data.get('channel', 0)
			value = data.get('value', 0)
			control_id = data.get('id', 'unknown')

			target_chop = op(chop_name)

			if target_chop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			param_name = f'value{channel}'

			if hasattr(target_chop.par, param_name):
				setattr(target_chop.par, param_name, value)
				print(f"[WebSocket] Set {chop_name}.{param_name} = {value} (id: {control_id})")
			else:
				print(f"[WebSocket] Error: Parameter '{param_name}' not found in {chop_name}")

		else:
			# Legacy format support (old hardcoded slider1/2/3)
			name = data.get('name', '')
			value = data.get('value', 0)

			constantChop = op('constant_params')

			if constantChop is None:
				print("[WebSocket] Error: constant_params CHOP not found!")
				return

			if name == 'slider1':
				constantChop.par.value0 = value
			elif name == 'slider2':
				constantChop.par.value1 = value
			elif name == 'slider3':
				constantChop.par.value2 = value
			else:
				print(f"[WebSocket] Unknown parameter name: {name}")

			print(f"[WebSocket] Set {name} to {value} (legacy format)")

	except Exception as e:
		print(f"[WebSocket] Error in handleParameter: {e}")


def handleColor(data):
	"""
	Handle color picker updates.

	New format:
	{
		"type": "color",
		"id": "main_color",
		"hex": "#ff0000",
		"rgb": {"r": 1.0, "g": 0.0, "b": 0.0},
		"chop": "constant_color"
	}

	Legacy format:
	{
		"type": "color",
		"hex": "#ff0000",
		"rgb": {"r": 1.0, "g": 0.0, "b": 0.0}
	}
	"""
	try:
		rgb = data.get('rgb', {})
		r = rgb.get('r', 0)
		g = rgb.get('g', 0)
		b = rgb.get('b', 0)

		if 'chop' in data:
			# New dynamic format
			chop_name = data.get('chop', 'constant_color')
			control_id = data.get('id', 'unknown')

			colorChop = op(chop_name)

			if colorChop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			colorChop.par.value0 = r
			colorChop.par.value1 = g
			colorChop.par.value2 = b

			print(f"[WebSocket] Set {chop_name} to R:{r:.2f} G:{g:.2f} B:{b:.2f} (id: {control_id})")

		else:
			# Legacy format
			colorChop = op('constant_color')

			if colorChop is None:
				print("[WebSocket] Error: constant_color CHOP not found!")
				return

			colorChop.par.value0 = r
			colorChop.par.value1 = g
			colorChop.par.value2 = b

			print(f"[WebSocket] Set color to R:{r:.2f} G:{g:.2f} B:{b:.2f} (legacy format)")

	except Exception as e:
		print(f"[WebSocket] Error in handleColor: {e}")


def handleXY(data):
	"""
	Handle XY pad position updates.

	New format:
	{
		"type": "xy",
		"id": "position_xy",
		"x": 0.75,
		"y": 0.50,
		"chop": "constant_xy"
	}

	Legacy format:
	{
		"type": "xy",
		"x": 0.75,
		"y": 0.50
	}
	"""
	try:
		x = data.get('x', 0.5)
		y = data.get('y', 0.5)

		if 'chop' in data:
			# New dynamic format
			chop_name = data.get('chop', 'constant_xy')
			control_id = data.get('id', 'unknown')

			xyChop = op(chop_name)

			if xyChop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			xyChop.par.value0 = x
			xyChop.par.value1 = y

			print(f"[WebSocket] Set {chop_name} to X:{x:.2f} Y:{y:.2f} (id: {control_id})")

		else:
			# Legacy format
			xyChop = op('constant_xy')

			if xyChop is None:
				print("[WebSocket] Error: constant_xy CHOP not found!")
				return

			xyChop.par.value0 = x
			xyChop.par.value1 = y

			print(f"[WebSocket] Set XY to X:{x:.2f} Y:{y:.2f} (legacy format)")

	except Exception as e:
		print(f"[WebSocket] Error in handleXY: {e}")


def handleTrigger(data):
	"""
	Handle trigger button press.

	Expected data format:
	{
		"type": "trigger",
		"id": "flash_trigger",
		"timestamp": 1234567890
	}
	"""
	try:
		trigger_id = data.get('id', 'unknown')

		# For now, use hardcoded trigger1
		# TODO: Support dynamic trigger routing
		triggerChop = op('trigger1')

		if triggerChop is None:
			print("[WebSocket] Error: trigger1 CHOP not found!")
			return

		triggerChop.par.triggerpulse.pulse()

		print(f"[WebSocket] Triggered: {trigger_id}")

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


# ============================================================================
# SERVER LIFECYCLE CALLBACKS
# ============================================================================

def onServerStart(webServerDAT):
	"""
	Callback when the web server starts.

	Args:
		webServerDAT: The Web Server DAT operator
	"""
	print("=" * 60)
	print("[WebServer] ✓ Web Server STARTED")
	print(f"[WebServer] Port: {webServerDAT.par.port}")
	print(f"[WebServer] Builder: http://localhost:{webServerDAT.par.port}/builder.html")
	print(f"[WebServer] Viewer: http://localhost:{webServerDAT.par.port}/")
	print(f"[WebServer] WebSocket: ws://localhost:{webServerDAT.par.port}")
	print("[WebServer] ONE server handles HTTP + WebSocket!")
	print("=" * 60)


def onServerStop(webServerDAT):
	"""
	Callback when the web server stops.

	Args:
		webServerDAT: The Web Server DAT operator
	"""
	print("=" * 60)
	print("[WebServer] ✗ Web Server STOPPED")
	print("=" * 60)
