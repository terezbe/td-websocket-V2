"""
CHOP Deployment Engine

Automatically creates/updates Constant CHOPs based on UI configuration.

USAGE:
Called automatically from /api/deploy endpoint when user clicks "Save to TD"
Or run manually: import deploy_chops; deploy_chops.deployFromConfig()

FEATURES:
- Creates one Constant CHOP per page
- Handles: sliders, colors, XY pads, buttons
- Names: {page_name}_controls (sanitized)
- Channels: Uses control IDs
- Location: Same level as webserver node
- Conflict: Shows error if CHOP exists
"""

import json
import re

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


def deployFromConfig():
	"""
	Deploy CHOPs from ui_config Text DAT.

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
	config_dat = op('ui_config')

	if config_dat is None:
		error = "ui_config Text DAT not found"
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
	# Step 2: Get deployment location (same level as webserver)
	# ========================================================================
	# Assuming this script is called from webserver callback
	# me.parent().parent() = same level as webserver
	try:
		deploy_location = me.parent().parent()
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
		if existing_chop:
			error = f"CHOP '{chop_name}' already exists at {existing_chop.path}"
			print(f"[ERROR] {error}")
			print(f"[ERROR] Delete it first or rename the page")
			results['errors'].append(error)
			continue

		# Analyze controls and build channel list
		channels = []

		for control in controls:
			control_type = control.get('type')
			control_id = control.get('id', 'unknown')

			if control_type == 'slider':
				# Slider = 1 channel
				channels.append({
					'name': control_id,
					'value': control.get('default', 50),
					'type': 'slider'
				})

			elif control_type == 'color':
				# Color = 3 channels (r, g, b)
				default_hex = control.get('default', '#ff0000')
				# Convert hex to RGB (0-1)
				r, g, b = hexToRGB(default_hex)
				channels.append({'name': f"{control_id}_r", 'value': r, 'type': 'color'})
				channels.append({'name': f"{control_id}_g", 'value': g, 'type': 'color'})
				channels.append({'name': f"{control_id}_b", 'value': b, 'type': 'color'})

			elif control_type == 'xy':
				# XY = 2 channels (x, y)
				default_xy = control.get('default', {'x': 0.5, 'y': 0.5})
				channels.append({'name': f"{control_id}_x", 'value': default_xy.get('x', 0.5), 'type': 'xy'})
				channels.append({'name': f"{control_id}_y", 'value': default_xy.get('y', 0.5), 'type': 'xy'})

			elif control_type == 'button':
				# Button = 1 channel (0 or 1)
				channels.append({
					'name': f"{control_id}_state",
					'value': control.get('default', 0),
					'type': 'button'
				})

		if not channels:
			warning = f"Page '{page_name}' has no deployable controls"
			print(f"[WARNING] {warning}")
			results['warnings'].append(warning)
			continue

		print(f"[INFO] Creating CHOP with {len(channels)} channels")

		# Create the CHOP
		try:
			new_chop = deploy_location.create(constantCHOP, chop_name)

			# Configure channels
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

			# Position CHOP
			new_chop.nodeX = page_idx * 200
			new_chop.nodeY = -200
			new_chop.viewer = True

			success_msg = f"Created '{chop_name}' with {len(channels)} channels"
			print(f"[SUCCESS] {success_msg}")

			results['chops'].append({
				'name': chop_name,
				'path': new_chop.path,
				'channels': len(channels),
				'page': page_name
			})

		except Exception as e:
			error = f"Failed to create CHOP '{chop_name}': {e}"
			print(f"[ERROR] {error}")
			results['errors'].append(error)

	# ========================================================================
	# Step 4: Summary
	# ========================================================================
	print("=" * 70)
	print(f"[Deploy CHOPs] Deployment complete!")
	print(f"[Deploy CHOPs] Created: {len(results['chops'])} CHOP(s)")
	print(f"[Deploy CHOPs] Errors: {len(results['errors'])}")
	print(f"[Deploy CHOPs] Warnings: {len(results['warnings'])}")
	print("=" * 70)

	results['success'] = len(results['errors']) == 0

	return results


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
