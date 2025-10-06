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
- POST /api/deploy - Deploy CHOPs from UI config

WEBSOCKET MESSAGES:
- parameter: Updates slider values (dynamic CHOP routing)
- color: Updates RGB color values
- xy: Updates XY pad position
- button: Updates button state (0 = OFF, 1 = ON)
- reset: Resets all values to defaults
"""

import json
import sys
import os
import re

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


def sanitizeName(name):
	"""Sanitize page name for use as CHOP name."""
	# Remove special characters, replace spaces with underscore
	sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
	# Remove consecutive underscores
	sanitized = re.sub(r'_+', '_', sanitized)
	# Remove leading/trailing underscores
	sanitized = sanitized.strip('_')
	# Lowercase
	sanitized = sanitized.lower()
	return sanitized if sanitized else 'page'


def hexToRGB(hex_color):
	"""Convert hex color to normalized RGB (0-1)."""
	hex_color = hex_color.lstrip('#')

	try:
		r = int(hex_color[0:2], 16) / 255.0
		g = int(hex_color[2:4], 16) / 255.0
		b = int(hex_color[4:6], 16) / 255.0
		return (r, g, b)
	except:
		return (1.0, 0.0, 0.0)  # Default red


def deployFromConfig():
	"""
	Deploy CHOPs from ui_config Text DAT.

	Automatically creates/updates Constant CHOPs based on UI configuration.
	- Creates one Constant CHOP per page
	- Handles: sliders, colors, XY pads, buttons
	- Names: {page_name}_controls (sanitized)
	- Channels: Uses control IDs
	- Location: Inside component (same level as webserver node)
	- Updates: Re-deploys update existing CHOPs instead of erroring

	Returns dict with deployment results.
	"""

	print("=" * 70)
	print("[Deploy CHOPs] Starting deployment...")
	print("=" * 70)

	results = {
		'success': False,
		'chops': [],
		'errors': [],
		'warnings': []
	}

	# ========================================================================
	# Step 1: Read and parse config
	# ========================================================================

	# PRIMARY: Try storage first (fast, reliable)
	if 'ui_config' in parent().storage:
		config = parent().storage['ui_config']
		print(f"[Deploy] ✓ Loaded config from storage")

	# FALLBACK: Try Text DAT (for old projects or manual edits)
	else:
		config_dat = op('ui_config')

		if config_dat is None:
			error = "ui_config not found (no storage or Text DAT)"
			print(f"[ERROR] {error}")
			results['errors'].append(error)
			return results

		config_text = config_dat.text

		if not config_text:
			error = "ui_config is empty - save a configuration first"
			print(f"[ERROR] {error}")
			results['errors'].append(error)
			return results

		# Handle bytes or string representation of bytes
		if isinstance(config_text, bytes):
			config_text = config_text.decode('utf-8')

		if config_text.startswith("b'") or config_text.startswith('b"'):
			config_text = config_text[2:-1]
			config_text = config_text.encode().decode('unicode_escape')

		try:
			config = json.loads(config_text)
			print(f"[Deploy] ✓ Loaded config from Text DAT (fallback)")
		except json.JSONDecodeError as e:
			error = f"Invalid JSON in ui_config: {e}"
			print(f"[ERROR] {error}")
			results['errors'].append(error)
			return results

	pages = config.get('pages', [])

	if not pages:
		warning = "No pages found in config"
		print(f"[WARNING] {warning}")
		results['warnings'].append(warning)
		results['success'] = True
		return results

	print(f"[OK] Found {len(pages)} page(s) in config")

	# ========================================================================
	# Step 2: Get deployment location (inside component)
	# ========================================================================
	# Assuming this script is called from webserver callback
	# me.parent() = inside the component, same level as webserver
	try:
		deploy_location = me.parent()
		print(f"[OK] Deploy location: {deploy_location.path}")
	except:
		# Fallback if called from elsewhere
		deploy_location = parent()
		print(f"[OK] Deploy location (fallback): {deploy_location.path}")

	# ========================================================================
	# Step 3: Deploy CHOP for each page
	# ========================================================================
	for page_idx, page in enumerate(pages):
		page_name = page.get('name', f'Page {page_idx + 1}')
		page_id = page.get('id', f'page{page_idx + 1}')
		controls = page.get('controls', [])

		print("-" * 70)
		print(f"[Page {page_idx + 1}] Processing '{page_name}' ({len(controls)} controls)")

		if not controls:
			warning = f"Page '{page_name}' has no controls - skipping"
			print(f"[WARNING] {warning}")
			results['warnings'].append(warning)
			continue

		# Generate CHOP name from page name
		chop_name = f"{sanitizeName(page_name)}_controls"
		print(f"[INFO] CHOP name: '{chop_name}'")

		# Check if CHOP already exists
		existing_chop = deploy_location.op(chop_name)
		is_update = existing_chop is not None

		if is_update:
			print(f"[INFO] CHOP '{chop_name}' exists - will update")
		else:
			print(f"[INFO] CHOP '{chop_name}' does not exist - will create")

		# Analyze controls and build channel list
		channels = []

		for control in controls:
			control_type = control.get('type')
			control_id = control.get('id', 'unknown')
			control_label = control.get('label', control_id)

			# Use sanitized label for channel names (human-readable)
			sanitized_label = sanitizeName(control_label)

			if control_type == 'slider':
				# Slider = 1 channel
				channels.append({
					'name': sanitized_label,
					'value': control.get('default', 50),
					'type': 'slider'
				})

			elif control_type == 'color':
				# Color = 3 channels (r, g, b)
				default_hex = control.get('default', '#ff0000')
				# Convert hex to RGB (0-1)
				r, g, b = hexToRGB(default_hex)
				channels.append({'name': f"{sanitized_label}_r", 'value': r, 'type': 'color'})
				channels.append({'name': f"{sanitized_label}_g", 'value': g, 'type': 'color'})
				channels.append({'name': f"{sanitized_label}_b", 'value': b, 'type': 'color'})

			elif control_type == 'xy':
				# XY = 2 channels (x, y)
				default_xy = control.get('default', {'x': 0.5, 'y': 0.5})
				channels.append({'name': f"{sanitized_label}_x", 'value': default_xy.get('x', 0.5), 'type': 'xy'})
				channels.append({'name': f"{sanitized_label}_y", 'value': default_xy.get('y', 0.5), 'type': 'xy'})

			elif control_type == 'button':
				# Button = 1 channel (0 or 1)
				channels.append({
					'name': f"{sanitized_label}_state",
					'value': control.get('default', 0),
					'type': 'button'
				})

		if not channels:
			warning = f"Page '{page_name}' has no deployable controls"
			print(f"[WARNING] {warning}")
			results['warnings'].append(warning)
			continue

		# Create or update the CHOP
		try:
			if is_update:
				# Use existing CHOP - just overwrite the channels we need
				new_chop = existing_chop
				print(f"[INFO] Updating CHOP with {len(channels)} channels")
			else:
				# Create new CHOP
				new_chop = deploy_location.create(constantCHOP, chop_name)
				print(f"[INFO] Creating CHOP with {len(channels)} channels")

			# Configure channels (set the ones we need, leave the rest alone)
			for i, channel in enumerate(channels):
				name_param = f'const{i}name'
				value_param = f'const{i}value'

				if hasattr(new_chop.par, name_param):
					setattr(new_chop.par, name_param, channel['name'])
					setattr(new_chop.par, value_param, channel['value'])
					print(f"  [{i}] {channel['name']} = {channel['value']} ({channel['type']})")
				else:
					warning = f"Channel {i} exceeded CHOP capacity"
					print(f"[WARNING] {warning}")
					results['warnings'].append(warning)
					break

			# Position CHOP (only for new CHOPs)
			if not is_update:
				new_chop.nodeX = page_idx * 200
				new_chop.nodeY = -200
				new_chop.viewer = True

			# Success message
			action = "Updated" if is_update else "Created"
			success_msg = f"{action} '{chop_name}' with {len(channels)} channels"
			print(f"[SUCCESS] {success_msg}")

			results['chops'].append({
				'name': chop_name,
				'path': new_chop.path,
				'channels': len(channels),
				'page': page_name,
				'action': action
			})

		except Exception as e:
			action = "update" if is_update else "create"
			error = f"Failed to {action} CHOP '{chop_name}': {e}"
			print(f"[ERROR] {error}")
			results['errors'].append(error)

	# ========================================================================
	# Step 4: Summary
	# ========================================================================
	print("=" * 70)
	print(f"[Deploy CHOPs] Deployment complete!")

	# Count created vs updated
	created = [c for c in results['chops'] if c.get('action') == 'Created']
	updated = [c for c in results['chops'] if c.get('action') == 'Updated']

	if created:
		print(f"[Deploy CHOPs] Created: {len(created)} CHOP(s)")
	if updated:
		print(f"[Deploy CHOPs] Updated: {len(updated)} CHOP(s)")
	if not created and not updated:
		print(f"[Deploy CHOPs] No CHOPs processed")

	print(f"[Deploy CHOPs] Errors: {len(results['errors'])}")
	print(f"[Deploy CHOPs] Warnings: {len(results['warnings'])}")
	print("=" * 70)

	results['success'] = len(results['errors']) == 0

	return results

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
			# PRIMARY: Try storage first (fast, reliable)
			if 'ui_config' in parent().storage:
				config = parent().storage['ui_config']
				response['statusCode'] = 200
				response['statusReason'] = 'OK'
				response['data'] = json.dumps(config)
				print(f"[WebServer] ✓ Loaded config from storage")

			# FALLBACK: Try Text DAT (for old projects or manual edits)
			elif (config_dat := op('ui_config')) is not None:
				config_text = config_dat.text

				if not config_text or config_text.strip() == '':
					print("[WebServer] ui_config is empty - using default")
					response['statusCode'] = 200
					response['statusReason'] = 'OK'
					response['data'] = json.dumps({
						"version": "1.0",
						"pages": [{"id": "page1", "name": "Default", "controls": []}]
					})
				else:
					# Handle bytes format (if needed)
					if isinstance(config_text, bytes):
						config_text = config_text.decode('utf-8')

					if config_text.startswith("b'") or config_text.startswith('b"'):
						config_text = config_text[2:-1]
						config_text = config_text.encode().decode('unicode_escape')

					try:
						json.loads(config_text)  # Validate
						response['statusCode'] = 200
						response['statusReason'] = 'OK'
						response['data'] = config_text
						print(f"[WebServer] ✓ Loaded config from Text DAT (fallback)")
					except json.JSONDecodeError:
						print("[WebServer] Error: Text DAT contains invalid JSON")
						response['statusCode'] = 500
						response['statusReason'] = 'Internal Server Error'
						response['data'] = json.dumps({"error": "Invalid JSON in Text DAT"})

			# EMPTY: No storage, no Text DAT
			else:
				print("[WebServer] No config found - using empty default")
				response['statusCode'] = 200
				response['statusReason'] = 'OK'
				response['data'] = json.dumps({
					"version": "1.0",
					"pages": [{"id": "page1", "name": "Default", "controls": []}]
				})

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
			config_json = request.get('data', '')

			try:
				# Parse and validate JSON
				config_dict = json.loads(config_json)

				# PRIMARY: Save to storage (fast, reliable, no encoding issues)
				parent().storage['ui_config'] = config_dict
				print(f"[WebServer] ✓ Saved config to storage ({len(config_json)} bytes)")

				# BACKUP: Save to Text DAT (visible in UI)
				config_dat = op('ui_config')
				if config_dat is not None:
					config_dat.text = json.dumps(config_dict, indent=2)
					print(f"[WebServer] ✓ Saved config to Text DAT (backup)")
				else:
					print(f"[WebServer] ⚠ ui_config DAT not found, storage-only mode")

				response['statusCode'] = 200
				response['statusReason'] = 'OK'
				response['data'] = json.dumps({"success": True, "message": "Config saved"})

			except json.JSONDecodeError as e:
				print(f"[WebServer] Error: Invalid JSON - {e}")
				response['statusCode'] = 400
				response['statusReason'] = 'Bad Request'
				response['data'] = json.dumps({"error": "Invalid JSON", "details": str(e)})

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
	# API: POST /api/deploy - Deploy CHOPs from UI configuration
	# ========================================================================
	elif uri == '/api/deploy' and method == 'POST':
		try:
			# Call the deployFromConfig function directly (merged into this file)
			results = deployFromConfig()

			# Return results
			response['statusCode'] = 200 if results['success'] else 500
			response['statusReason'] = 'OK' if results['success'] else 'Internal Server Error'
			response['data'] = json.dumps(results)
			print(f"[WebServer] Deploy complete: {len(results['chops'])} CHOP(s) processed, {len(results['errors'])} error(s)")

			response['content-type'] = 'application/json'
			return response

		except Exception as e:
			print(f"[WebServer] Error in POST /api/deploy: {e}")
			response['statusCode'] = 500
			response['statusReason'] = 'Internal Server Error'
			response['data'] = json.dumps({"error": str(e), "success": False, "chops": [], "errors": [str(e)], "warnings": []})
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

		elif msgType == 'button':
			handleButton(message)

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
		# Check for new format (with chop)
		if 'chop' in data:
			# New dynamic format - search by sanitized LABEL (not ID)
			chop_name = data.get('chop', '')
			value = data.get('value', 0)
			control_label = data.get('label', data.get('id', 'unknown'))

			# Use sanitized label for channel search (matches deployment)
			sanitized_label = sanitizeName(control_label)

			target_chop = op(chop_name)

			if target_chop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			# Search for channel by sanitized label
			found = False
			for i in range(target_chop.numChans):
				if target_chop.par[f'const{i}name'].eval() == sanitized_label:
					target_chop.par[f'const{i}value'] = value
					found = True
					print(f"[WebSocket] Set {chop_name}.{sanitized_label} = {value}")
					break

			if not found:
				print(f"[WebSocket] Warning: Channel '{sanitized_label}' not found in {chop_name}")

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
			# New dynamic format - search by sanitized LABEL (not ID)
			chop_name = data.get('chop', 'constant_color')
			control_label = data.get('label', data.get('id', 'unknown'))

			# Use sanitized label for channel search (matches deployment)
			sanitized_label = sanitizeName(control_label)

			colorChop = op(chop_name)

			if colorChop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			# Search for channels by sanitized label: {label}_r, {label}_g, {label}_b
			channel_names = {
				f'{sanitized_label}_r': r,
				f'{sanitized_label}_g': g,
				f'{sanitized_label}_b': b
			}

			found_count = 0
			for i in range(colorChop.numChans):
				chan_name = colorChop.par[f'const{i}name'].eval()
				if chan_name in channel_names:
					colorChop.par[f'const{i}value'] = channel_names[chan_name]
					found_count += 1

			if found_count == 3:
				print(f"[WebSocket] Set {chop_name}.{sanitized_label}_[rgb] = R:{r:.2f} G:{g:.2f} B:{b:.2f}")
			else:
				print(f"[WebSocket] Warning: Only found {found_count}/3 color channels for '{sanitized_label}' in {chop_name}")

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
			# New dynamic format - search by sanitized LABEL (not ID)
			chop_name = data.get('chop', 'constant_xy')
			control_label = data.get('label', data.get('id', 'unknown'))

			# Use sanitized label for channel search (matches deployment)
			sanitized_label = sanitizeName(control_label)

			xyChop = op(chop_name)

			if xyChop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			# Search for channels by sanitized label: {label}_x, {label}_y
			channel_names = {
				f'{sanitized_label}_x': x,
				f'{sanitized_label}_y': y
			}

			found_count = 0
			for i in range(xyChop.numChans):
				chan_name = xyChop.par[f'const{i}name'].eval()
				if chan_name in channel_names:
					xyChop.par[f'const{i}value'] = channel_names[chan_name]
					found_count += 1

			if found_count == 2:
				print(f"[WebSocket] Set {chop_name}.{sanitized_label}_[xy] = X:{x:.2f} Y:{y:.2f}")
			else:
				print(f"[WebSocket] Warning: Only found {found_count}/2 XY channels for '{sanitized_label}' in {chop_name}")

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


def handleButton(data):
	"""
	Handle button toggle.

	New format:
	{
		"type": "button",
		"id": "main_button",
		"state": 1,  # 0 = OFF, 1 = ON
		"chop": "button_states"
	}

	Legacy format (if needed):
	{
		"type": "button",
		"id": "button1",
		"state": 1
	}
	"""
	try:
		control_label = data.get('label', data.get('id', 'unknown'))
		state = data.get('state', 0)

		# Use sanitized label for channel search (matches deployment)
		sanitized_label = sanitizeName(control_label)

		if 'chop' in data:
			# New dynamic format - search by sanitized LABEL
			chop_name = data.get('chop', 'button_states')

			buttonChop = op(chop_name)

			if buttonChop is None:
				print(f"[WebSocket] Error: CHOP '{chop_name}' not found!")
				return

			# Find the channel for this button
			# Button channels are named {sanitized_label}_state in deploy script
			channel_name = f"{sanitized_label}_state"

			# Search for the channel by name
			found = False
			for i in range(buttonChop.numChans):
				if buttonChop.par[f'const{i}name'].eval() == channel_name:
					buttonChop.par[f'const{i}value'] = state
					found = True
					print(f"[WebSocket] Set {chop_name}.{channel_name} = {state}")
					break

			if not found:
				print(f"[WebSocket] Warning: Channel '{channel_name}' not found in {chop_name}")

		else:
			# Legacy format - use hardcoded button CHOP
			buttonChop = op('button_states')

			if buttonChop is None:
				print("[WebSocket] Error: button_states CHOP not found!")
				return

			# Assume first channel for legacy
			buttonChop.par.value0 = state

			print(f"[WebSocket] Set button state to {state} (legacy format)")

	except Exception as e:
		print(f"[WebSocket] Error in handleButton: {e}")


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
