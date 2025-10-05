"""
VFS File Loader Script

This script automates loading web files into TouchDesigner's Virtual File System.

USAGE:
1. Create a Base COMP (e.g., 'WebSocketControl')
2. Dive inside the component
3. Run this script in the Textport (Alt+T)
4. Or create an Execute DAT and paste this script

This will load all web files (HTML, CSS, JS) from the public folder
into the component's VFS.
"""

import os

def loadWebFilesIntoVFS(comp, publicFolder):
	"""
	Load web files from a folder into a component's VFS.

	Args:
		comp: TouchDesigner COMP operator to load files into
		publicFolder: Path to folder containing web files
	"""

	# Define files to load
	filesToLoad = [
		'index.html',
		'style.css',
		'app.js',
		'builder.html',
		'builder.css',
		'builder.js',
	]

	print("=" * 60)
	print("[VFS Loader] Loading web files into VFS...")
	print(f"[VFS Loader] Component: {comp.path}")
	print(f"[VFS Loader] Source: {publicFolder}")
	print("=" * 60)

	loadedCount = 0
	errorCount = 0

	for filename in filesToLoad:
		filepath = os.path.join(publicFolder, filename)

		try:
			# Check if file exists
			if not os.path.exists(filepath):
				print(f"[VFS Loader] ✗ File not found: {filepath}")
				errorCount += 1
				continue

			# Check if already in VFS
			if filename in comp.vfs:
				print(f"[VFS Loader] ⚠ Replacing existing: {filename}")
				# Remove old version
				comp.vfs.deleteFile(filename)

			# Add file to VFS
			comp.vfs.addFile(filepath, filename)

			# Get file size for confirmation
			fileSize = os.path.getsize(filepath)
			print(f"[VFS Loader] ✓ Loaded: {filename} ({fileSize:,} bytes)")
			loadedCount += 1

		except Exception as e:
			print(f"[VFS Loader] ✗ Error loading {filename}: {e}")
			errorCount += 1

	print("-" * 60)
	print(f"[VFS Loader] Summary:")
	print(f"  Loaded: {loadedCount}")
	print(f"  Errors: {errorCount}")
	print(f"  Total VFS files: {len(comp.vfs)}")
	print("=" * 60)

	# List all VFS files
	if len(comp.vfs) > 0:
		print("[VFS Loader] VFS Contents:")
		for vfsFile in comp.vfs:
			print(f"  - {vfsFile.name} ({vfsFile.size:,} bytes)")
		print("=" * 60)

	return loadedCount, errorCount


# =============================================================================
# CONFIGURATION - EDIT THESE VALUES
# =============================================================================

# Path to the component where you want to load VFS files
# Examples:
#   - For root level: op('/WebSocketControl')
#   - For nested: op('/project1/WebSocketControl')
#   - If running inside component: parent()
COMPONENT_PATH = '/WebSocketControl'

# Path to the public folder containing your web files
# Update this to match your system
PUBLIC_FOLDER = 'C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/public'

# =============================================================================
# RUN THE LOADER
# =============================================================================

if __name__ == '__main__':
	try:
		# Get reference to component
		targetComp = op(COMPONENT_PATH)

		if targetComp is None:
			print(f"[VFS Loader] Error: Component not found: {COMPONENT_PATH}")
			print("[VFS Loader] Available components:")
			for comp in root.findChildren(type=baseCOMP):
				print(f"  - {comp.path}")
		else:
			# Load files
			loaded, errors = loadWebFilesIntoVFS(targetComp, PUBLIC_FOLDER)

			if errors == 0:
				print("[VFS Loader] ✓ All files loaded successfully!")
			else:
				print(f"[VFS Loader] ⚠ Completed with {errors} error(s)")

	except Exception as e:
		print(f"[VFS Loader] Fatal error: {e}")
		import traceback
		traceback.print_exc()


# =============================================================================
# ALTERNATIVE: Load from current component
# =============================================================================
# If you paste this into an Execute DAT inside your component, use this instead:

def loadFromCurrentComponent():
	"""Load VFS files when running from inside the target component."""
	publicFolder = 'C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/public'
	return loadWebFilesIntoVFS(parent(), publicFolder)

# Uncomment to use:
# loadFromCurrentComponent()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def listVFS(comp):
	"""
	List all files in a component's VFS.

	Args:
		comp: TouchDesigner COMP operator
	"""
	print("=" * 60)
	print(f"[VFS] Files in {comp.path}:")
	print("=" * 60)

	if len(comp.vfs) == 0:
		print("  (empty)")
	else:
		for vfsFile in comp.vfs:
			print(f"  - {vfsFile.name}")
			print(f"    Size: {vfsFile.size:,} bytes")
			print(f"    Path: vfs:{comp.path}/{vfsFile.name}")
			print()

	print("=" * 60)


def clearVFS(comp):
	"""
	Clear all files from a component's VFS.

	Args:
		comp: TouchDesigner COMP operator
	"""
	print(f"[VFS] Clearing VFS for {comp.path}...")

	count = len(comp.vfs)
	if count == 0:
		print("[VFS] VFS is already empty")
		return

	# Delete all files
	for vfsFile in list(comp.vfs):
		comp.vfs.deleteFile(vfsFile.name)
		print(f"[VFS] ✓ Deleted: {vfsFile.name}")

	print(f"[VFS] Cleared {count} file(s)")


def exportVFS(comp, outputFolder):
	"""
	Export all VFS files to a folder on disk.

	Args:
		comp: TouchDesigner COMP operator
		outputFolder: Path to export files to
	"""
	import os

	print(f"[VFS Export] Exporting VFS from {comp.path} to {outputFolder}...")

	# Create output folder if it doesn't exist
	if not os.path.exists(outputFolder):
		os.makedirs(outputFolder)
		print(f"[VFS Export] Created folder: {outputFolder}")

	count = 0
	for vfsFile in comp.vfs:
		outputPath = os.path.join(outputFolder, vfsFile.name)

		# Write bytes to file
		with open(outputPath, 'wb') as f:
			f.write(vfsFile.bytes)

		print(f"[VFS Export] ✓ Exported: {vfsFile.name} ({vfsFile.size:,} bytes)")
		count += 1

	print(f"[VFS Export] Exported {count} file(s) to {outputFolder}")


# =============================================================================
# EXAMPLE USAGE FROM TEXTPORT
# =============================================================================

"""
# Load files into VFS:
run("load_vfs_files")

# List VFS contents:
listVFS(op('/WebSocketControl'))

# Clear VFS:
clearVFS(op('/WebSocketControl'))

# Export VFS to disk:
exportVFS(op('/WebSocketControl'), 'C:/temp/exported_vfs')
"""
