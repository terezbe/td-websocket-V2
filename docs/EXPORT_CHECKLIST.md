# Export Checklist - WebSocketControl.tox

Quick checklist before exporting the .tox file for distribution.

## Pre-Export Checklist

### ✅ Component Structure
- [ ] WebSocketControl component exists at root level
- [ ] Component is properly named (not "base1")

### ✅ Custom Parameters (on component)
- [ ] Port (Integer, default: 9980, linked to webserver1.par.port)
- [ ] Active (Toggle, default: On, linked to webserver1.par.active)
- [ ] Open Browser (Pulse button - name: Openbrowser)
- [ ] Status (String, read-only, expression-based)

### ✅ Parameter Execute DAT (handles pulse callbacks)
- [ ] parameter_callbacks (Parameter Execute DAT) exists inside component
  - Active: On
  - OPs: .. (parent)
  - Parameters: Openbrowser
  - On Pulse: On
- [ ] onPulse() callback code added
- [ ] Opens browser using webbrowser.open()
- [ ] Tested - clicking button opens browser

### ✅ Inside Component - Operators

**Web Server:**
- [ ] webserver1 (Web Server DAT)
  - Active: On
  - Port: 9980
  - Callbacks DAT: webserver_callbacks

**Callbacks:**
- [ ] webserver_callbacks (Text DAT)
  - Contains latest code from webserver_callbacks.py
  - All WebSocket callbacks present
  - Uses simple op('chop_name') references

**VFS:**
- [ ] virtualFile component exists
  - index.html (latest version, ws://localhost:9980)
  - style.css
  - app.js
  - Total: 3 files in VFS

**CHOPs:**
- [ ] constant_params (Constant CHOP)
  - 3 channels: slider1, slider2, slider3
  - Values: 50, 50, 50

- [ ] constant_color (Constant CHOP)
  - 3 channels: r, g, b
  - Values: 1, 0, 0

- [ ] constant_xy (Constant CHOP)
  - 2 channels: x, y
  - Values: 0.5, 0.5

- [ ] trigger1 (Trigger CHOP)
  - Default settings

**Documentation:**
- [ ] README (Text DAT) with usage instructions

### ✅ Testing
- [ ] Web server starts when Active = On
- [ ] "Open Browser" button opens http://localhost:9980
- [ ] Web page loads correctly
- [ ] WebSocket connects (green indicator)
- [ ] Sliders update CHOP values
- [ ] Color picker updates CHOP values
- [ ] XY pad updates CHOP values
- [ ] Trigger button pulses CHOP
- [ ] Reset button works
- [ ] Tested on mobile device (optional)

### ✅ Optional
- [ ] Privacy mode enabled (Pro only)
- [ ] Custom icon set (optional)
- [ ] Tags added for organization (optional)

## Export Steps

1. Exit the component (press `u`)
2. Right-click WebSocketControl → **Export Component...**
3. Choose location and filename: `WebSocketControl.tox`
4. Click Save

## Post-Export Verification

1. Open a **new TouchDesigner project**
2. Drag `WebSocketControl.tox` into the network
3. Verify component appears with custom parameters
4. Check "Active" is On by default
5. Click "Open Browser" - should open web page
6. Test all controls work
7. Close test project

## Distribution

Your .tox is ready to share! Include these instructions for recipients:

```
WebSocketControl.tox - Quick Start
===================================

1. Drag WebSocketControl.tox into your TouchDesigner project
2. The component auto-starts (Active = On)
3. Click "Open Browser" button
4. In web UI, click "Connect"
5. Control TouchDesigner remotely!

For mobile: Use http://YOUR_PC_IP:9980
```

## Common Issues to Check

**If web page doesn't load:**
- Verify port 9980 isn't in use by another app
- Check firewall settings
- Confirm Active = On

**If WebSocket doesn't connect:**
- Make sure URL is ws://localhost:9980 (same port!)
- Check Textport (Alt+T) for errors
- Verify webserver_callbacks is linked

**If CHOPs don't update:**
- Confirm CHOP names match exactly
- Check Textport for "CHOP not found" errors
- Verify callbacks DAT is linked to webserver1

---

**Version:** 1.0
**Date:** 2025-10-03
**Tested on:** TouchDesigner 2023.x
