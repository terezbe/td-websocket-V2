# Parameter Execute DAT - Quick Guide

## What is Parameter Execute DAT?

The **Parameter Execute DAT** allows you to run Python code when parameters change or are pulsed. This is how we make the "Open Browser" button work!

## Setup for "Open Browser" Button

### Step 1: Create Custom Pulse Parameter

1. Right-click component → **Customize Component**
2. Add a **Pulse** type parameter:
   - **Name**: `Openbrowser` (no spaces!)
   - **Label**: `Open Browser` (what user sees)
   - **Type**: `Pulse`

### Step 2: Create Parameter Execute DAT

**Inside the component:**

1. Press `Tab` → type "parameter" → **Parameter Execute DAT**
2. Rename to: `parameter_callbacks`

### Step 3: Configure Parameters

**Parameter Execute DAT settings:**

```
Active:     On
OPs:        ..          (monitors parent component)
Parameters: Openbrowser (the pulse parameter name)
On Pulse:   On          (checkbox - enables onPulse callback)
```

**Important:**
- **OPs** should be `..` (parent) to monitor the component itself
- **Parameters** must match the exact parameter name (`Openbrowser`)
- **On Pulse** checkbox must be checked!

### Step 4: Add Python Code

**Click inside the Parameter Execute DAT** and add:

```python
def onPulse(par):
	"""
	Called when any pulse parameter is pressed.

	Args:
		par: The parameter object that was pulsed
			 par.name - name of the parameter
			 par.owner - the operator that owns the parameter
	"""
	if par.name == 'Openbrowser':
		import webbrowser
		# Get port from component's custom parameter
		port = par.owner.par.Port.eval()
		url = f'http://localhost:{port}'
		print(f"Opening browser to: {url}")
		webbrowser.open(url)

	return
```

### Step 5: Test

1. **Exit component** (press `u`)
2. **Click** the "Open Browser" parameter
3. **Browser should open** to http://localhost:9980

## How It Works

```
User clicks "Open Browser" button
    ↓
Parameter Execute DAT detects pulse
    ↓
Calls onPulse(par)
    ↓
Code checks par.name == 'Openbrowser'
    ↓
Gets port from par.owner.par.Port
    ↓
Opens browser with webbrowser.open()
```

## Common Issues

### "Nothing happens when I click the button"

**Check:**
- [ ] Parameter Execute DAT Active = On
- [ ] OPs parameter = `..` (parent)
- [ ] Parameters field = `Openbrowser` (exact name)
- [ ] "On Pulse" checkbox is checked
- [ ] Python code is inside the DAT (not empty)

### "AttributeError: par.owner has no attribute 'Port'"

**Problem:** Using wrong reference
**Fix:** Use `par.owner.par.Port` not `parent().par.Port`

### "Parameter not found"

**Problem:** Parameter name mismatch
**Check:**
- Component has custom parameter named exactly `Openbrowser`
- Parameter Execute DAT Parameters field matches: `Openbrowser`
- Case-sensitive!

## Understanding par vs parent()

**In Parameter Execute DAT callbacks:**

```python
def onPulse(par):
    # par = the parameter that was pulsed
    # par.owner = the operator that owns the parameter (the component)
    # par.owner.par.Port = access other parameters on the component

    port = par.owner.par.Port.eval()  # ✅ CORRECT
    port = parent().par.Port.eval()    # ❌ WRONG (parent() is not defined here)
```

**Key difference:**
- `par.owner` - the operator that owns the pulsed parameter
- `parent()` - would refer to parent of the Parameter Execute DAT (not what we want)

## Parameter Execute DAT vs Script DAT

**Parameter Execute DAT:**
- Monitors other operators' parameters
- Runs when parameters change
- Good for: Responding to UI interactions

**Script DAT:**
- Has its own custom parameters
- Uses `me` to reference itself
- Good for: Creating reusable functions

**For "Open Browser" button, we need Parameter Execute DAT** because we're monitoring the component's custom parameter.

## Multiple Pulse Buttons

If you have multiple pulse buttons:

```python
def onPulse(par):
    if par.name == 'Openbrowser':
        import webbrowser
        port = par.owner.par.Port.eval()
        webbrowser.open(f'http://localhost:{port}')

    elif par.name == 'Resetall':
        # Reset all CHOPs to defaults
        op('constant_params').par.value0 = 50
        op('constant_params').par.value1 = 50
        op('constant_params').par.value2 = 50

    elif par.name == 'Testconnection':
        # Test WebSocket connection
        print("Testing connection...")

    return
```

**Parameters field:** Leave blank to monitor ALL pulse parameters, or list them: `Openbrowser Resetall Testconnection`

## Advanced: Other Callbacks

Parameter Execute DAT supports other callbacks too:

```python
def onValueChange(par, prev):
    """Called when any parameter value changes"""
    print(f"{par.name} changed from {prev} to {par.eval()}")

def offToOn(par):
    """Called when toggle parameter goes from off to on"""
    print(f"{par.name} turned ON")

def whileOn(par):
    """Called every frame while toggle is on"""
    print(f"{par.name} is ON")
```

Enable these in the Parameter Execute DAT parameters:
- **Value Change** checkbox
- **Off to On** checkbox
- **While On** checkbox

## Summary

**For "Open Browser" button:**

1. ✅ Create pulse parameter on component: `Openbrowser`
2. ✅ Create Parameter Execute DAT inside component
3. ✅ Configure: Active=On, OPs=.., Parameters=Openbrowser, On Pulse=On
4. ✅ Add onPulse() code with `par.owner.par.Port`
5. ✅ Test by clicking button

**That's it!** The button now opens the browser to the correct port. 🎉

## References

- [Parameter Execute DAT Docs](https://docs.derivative.ca/Parameter_Execute_DAT)
- [Custom Parameters](https://docs.derivative.ca/Custom_Parameters)
- [OP Class](https://docs.derivative.ca/OP_Class)
