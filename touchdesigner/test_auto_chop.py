"""
Auto-Create CHOP Test Script

Simple test to automatically create a Constant CHOP based on ui_config.

USAGE:
1. Make sure ui_config Text DAT exists with saved controls
2. Open TouchDesigner Textport (Alt+T)
3. Run this script:
   execfile('C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/touchdesigner/test_auto_chop.py')
4. Check if 'auto_test' CHOP was created

WHAT IT DOES:
- Reads ui_config Text DAT
- Parses JSON to find slider controls on first page
- Creates a Constant CHOP named 'auto_test'
- Sets correct number of channels
- Names each channel based on control ID
"""

import json

def createAutoChop():
	"""Create a Constant CHOP automatically from ui_config."""

	print("=" * 60)
	print("[Auto-CHOP Test] Starting...")
	print("=" * 60)

	# ========================================================================
	# Step 1: Read ui_config
	# ========================================================================
	config_dat = op('ui_config')

	if config_dat is None:
		print("[ERROR] ui_config Text DAT not found!")
		print("Please create a Text DAT named 'ui_config' and save a UI configuration.")
		return

	config_text = config_dat.text

	if not config_text:
		print("[ERROR] ui_config is empty!")
		print("Please save a UI configuration from the builder first.")
		return

	# Handle both bytes and strings
	if isinstance(config_text, bytes):
		print("[INFO] Converting bytes to string...")
		config_text = config_text.decode('utf-8')

	# Handle string representation of bytes (starts with "b'")
	if config_text.startswith("b'") or config_text.startswith('b"'):
		print("[INFO] Unwrapping bytes string representation...")
		# Remove b' prefix and trailing '
		config_text = config_text[2:-1]
		# Unescape any escaped characters
		config_text = config_text.encode().decode('unicode_escape')

	if config_text.strip() == '':
		print("[ERROR] ui_config is empty!")
		return

	# ========================================================================
	# Step 2: Parse JSON
	# ========================================================================
	try:
		config = json.loads(config_text)
	except json.JSONDecodeError as e:
		print(f"[ERROR] Invalid JSON in ui_config: {e}")
		return

	print(f"[OK] Loaded config version: {config.get('version', 'unknown')}")

	pages = config.get('pages', [])
	if not pages:
		print("[WARNING] No pages found in config")
		return

	# Use first page for test
	first_page = pages[0]
	page_name = first_page.get('name', 'Unknown')
	controls = first_page.get('controls', [])

	print(f"[OK] Found page: '{page_name}' with {len(controls)} controls")

	# ========================================================================
	# Step 3: Find slider controls
	# ========================================================================
	sliders = [c for c in controls if c.get('type') == 'slider']

	if not sliders:
		print("[WARNING] No slider controls found on first page")
		print("Create some sliders in the builder first!")
		return

	print(f"[OK] Found {len(sliders)} slider controls:")
	for i, slider in enumerate(sliders):
		print(f"  [{i}] {slider.get('id', 'unknown')} - {slider.get('label', 'No label')}")

	# ========================================================================
	# Step 4: Create Constant CHOP
	# ========================================================================
	chop_name = 'auto_test'

	# Check if it already exists
	existing_chop = op(chop_name)
	if existing_chop:
		print(f"[INFO] CHOP '{chop_name}' already exists - destroying it first")
		existing_chop.destroy()

	# Create new Constant CHOP
	print(f"[INFO] Creating Constant CHOP: '{chop_name}'")
	new_chop = parent().create(constantCHOP, chop_name)

	# ========================================================================
	# Step 5: Configure CHOP channels
	# ========================================================================
	num_channels = len(sliders)

	print(f"[INFO] Configuring {num_channels} channels...")

	# Set each channel's name and value
	channel_names = []

	for i, slider in enumerate(sliders):
		control_id = slider.get('id', f'slider{i}')
		default_value = slider.get('default', 50)

		# Set channel name (const0name, const1name, etc.)
		name_param = f'const{i}name'
		if hasattr(new_chop.par, name_param):
			setattr(new_chop.par, name_param, control_id)
			channel_names.append(control_id)
			print(f"  Set {name_param} = '{control_id}'")
		else:
			print(f"  [WARNING] Parameter {name_param} not found")

		# Set channel value (const0value, const1value, etc.)
		value_param = f'const{i}value'
		if hasattr(new_chop.par, value_param):
			setattr(new_chop.par, value_param, default_value)
			print(f"  Set {value_param} = {default_value}")
		else:
			print(f"  [WARNING] Parameter {value_param} not found")

	print(f"[OK] Successfully configured {len(channel_names)} channels")

	# ========================================================================
	# Step 6: Position CHOP nicely
	# ========================================================================
	new_chop.nodeX = 0
	new_chop.nodeY = 0
	new_chop.viewer = True  # Show viewer

	print("=" * 60)
	print(f"[SUCCESS] Created '{chop_name}' CHOP!")
	if channel_names:
		print(f"[INFO] Channels: {', '.join(channel_names)}")
	print(f"[INFO] Location: {new_chop.path}")
	print("=" * 60)
	print("[NEXT STEP] Update your WebSocket callback to use this CHOP:")
	print(f"[NEXT STEP]   Change 'constant_params' to '{chop_name}'")
	print("[NEXT STEP] Then test by moving sliders in the viewer!")
	print("=" * 60)

# Run the test
createAutoChop()
