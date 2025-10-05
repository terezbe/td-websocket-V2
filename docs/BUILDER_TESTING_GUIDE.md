# UI Builder - Testing Guide

## 🎉 You're Ready to Test!

The UI Builder is now complete. Follow these steps to load it into TouchDesigner and test it.

---

## Step 1: Load Files into VFS

### Option A: Using virtualFile Component UI (Easiest)

1. **Open TouchDesigner** and navigate to your WebSocketControl component
2. **Dive inside** (press `i`)
3. **Find the virtualFile component**
4. **In the virtualFile parameters:**
   - Click the **Folder** parameter
   - Browse to: `C:\Users\Erez\Desktop\PROJECTS\DEV_MAIN\td-websocket-V2\public`
   - Click **Parse** button

5. **Verify 6 files loaded:**
   - index.html
   - style.css
   - app.js
   - ✅ builder.html (NEW!)
   - ✅ builder.css (NEW!)
   - ✅ builder.js (NEW!)

### Option B: Using Python Script

1. **Open Textport** (Alt+T)
2. **Run the loader script:**
```python
execfile('C:/Users/Erez/Desktop/PROJECTS/DEV_MAIN/td-websocket-V2/load_vfs_files.py')
```

3. **Check output** - should see:
```
[VFS Loader] ✓ Loaded: builder.html
[VFS Loader] ✓ Loaded: builder.css
[VFS Loader] ✓ Loaded: builder.js
[VFS Loader] Summary:
  Loaded: 6
  Total VFS files: 6
```

---

## Step 2: Access the Builder

1. **Make sure Web Server DAT is Active**
   - Check `webserver1` has Active = On
   - Port should be 9980

2. **Open Builder in Browser:**
   - Go to: `http://localhost:9980/builder.html`

3. **You should see:**
   - Left panel: Control palette (Slider, Color, XY Pad buttons)
   - Middle panel: Empty canvas with "No controls yet"
   - Right panel: Preview area
   - Top bar: Download JSON, Upload JSON, Clear All buttons

---

## Step 3: Test Adding Controls

### Add a Slider

1. **Click "+ Slider"** button in left palette
2. **New slider appears** in canvas list
3. **Properties sidebar opens** automatically at bottom
4. **Fill in properties:**
   - Label: "Speed"
   - CHOP: "constant_params"
   - Channel: 0
   - Min: 0
   - Max: 200
   - Default: 100
5. **Click "Save Changes"**
6. **Check preview panel** - slider should appear

### Add a Color Picker

1. **Click "+ Color"** button
2. **Edit properties:**
   - Label: "Main Color"
   - CHOP: "constant_color"
   - Default: (pick a color)
3. **Save** - color picker appears in preview

### Add an XY Pad

1. **Click "+ XY Pad"** button
2. **Edit properties:**
   - Label: "Position"
   - CHOP: "constant_xy"
   - Default X: 0.5
   - Default Y: 0.5
3. **Save** - XY pad appears in preview

---

## Step 4: Test Editing Controls

1. **Click any control** in the canvas list
2. **Properties sidebar opens**
3. **Change the label** to something else
4. **Click "Save Changes"**
5. **Verify:** Label updates in both canvas AND preview

---

## Step 5: Test Reordering Controls

1. **Use ↑↓ arrows** on controls
2. **Verify:** Order changes in both canvas AND preview

---

## Step 6: Test Deleting Controls

1. **Click the X button** on a control
2. **Confirmation modal appears**
3. **Click "Confirm"**
4. **Verify:** Control removed from both canvas AND preview

---

## Step 7: Test JSON Download

1. **Click "Download JSON"** button in header
2. **File downloads:** `td-ui-config.json`
3. **Open the JSON file** in a text editor
4. **Verify:** Contains all your controls in proper format

**Example output:**
```json
{
  "version": "1.0",
  "name": "Custom UI",
  "description": "",
  "controls": [
    {
      "id": "slider1",
      "type": "slider",
      "label": "Speed",
      "chop": "constant_params",
      "channel": 0,
      "min": 0,
      "max": 200,
      "default": 100
    },
    ...
  ]
}
```

---

## Step 8: Test JSON Upload

1. **Click "Upload JSON"** button
2. **Select the JSON file** you just downloaded
3. **Verify:** All controls reload correctly

---

## Step 9: Test LocalStorage Auto-Save

1. **Add some controls**
2. **Close the browser tab**
3. **Reopen:** `http://localhost:9980/builder.html`
4. **Verify:** Your controls are still there (auto-loaded from LocalStorage!)

---

## Step 10: Test Clear All

1. **Click "Clear All"** button
2. **Confirmation appears**
3. **Click "Confirm"**
4. **Verify:** All controls removed, canvas empty

---

## Common Issues

### Builder page won't load (404 error)

**Check:**
- VFS files are loaded (check virtualFile component)
- Web Server DAT is Active
- Accessing correct URL: `http://localhost:9980/builder.html`

### Controls don't appear in preview

**Check:**
- JavaScript console for errors (F12 in browser)
- Clear browser cache and refresh (Ctrl+Shift+R)

### Can't save properties

**Check:**
- All required fields are filled
- Numbers are valid (min < max for sliders)
- CHOP name doesn't have spaces

### LocalStorage not persisting

**Check:**
- Browser allows localStorage
- Not in Private/Incognito mode

---

## What's Working

After testing, you should have:

- ✅ Dark professional UI (TouchOSC-inspired)
- ✅ Add slider, color, XY pad controls
- ✅ Edit control properties
- ✅ Delete controls
- ✅ Reorder controls (up/down)
- ✅ Live preview updates
- ✅ Download JSON config file
- ✅ Upload JSON config file
- ✅ LocalStorage auto-save
- ✅ Clear all with confirmation

---

## Next Steps (Not Built Yet)

These features are for later:

- ❌ Viewer loading config and generating dynamic UI
- ❌ Viewer sending messages to TouchDesigner with dynamic CHOPs
- ❌ TouchDesigner updating CHOPs based on config
- ❌ Storage DAT integration (for now, manual JSON paste)

---

## Testing Checklist

- [ ] Builder loads at http://localhost:9980/builder.html
- [ ] Can add slider control
- [ ] Can add color control
- [ ] Can add XY pad control
- [ ] Can edit control properties
- [ ] Can delete controls
- [ ] Can reorder controls
- [ ] Preview updates in real-time
- [ ] Can download JSON file
- [ ] Can upload JSON file
- [ ] LocalStorage persists between sessions
- [ ] Can clear all controls
- [ ] Dark theme looks professional
- [ ] Responsive layout works

---

## Success! 🎉

If all tests pass, the UI Builder is fully functional and ready for the next phase: making the viewer dynamic!

**Take a screenshot of your builder with some controls and share it - I'd love to see what you create!**
