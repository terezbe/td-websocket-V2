// WebSocket connection
let ws = null;
let isConnected = false;

// DOM elements
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const websocketUrlInput = document.getElementById('websocket-url');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

// Sliders
const slider1 = document.getElementById('slider1');
const slider2 = document.getElementById('slider2');
const slider3 = document.getElementById('slider3');
const slider1Value = document.getElementById('slider1-value');
const slider2Value = document.getElementById('slider2-value');
const slider3Value = document.getElementById('slider3-value');

// Color picker
const colorPicker = document.getElementById('color-picker');

// Buttons
const triggerBtn = document.getElementById('trigger-btn');
const resetBtn = document.getElementById('reset-btn');

// XY Pad
const xyPad = document.getElementById('xy-pad');
const xyCursor = document.getElementById('xy-cursor');
const xyXDisplay = document.getElementById('xy-x');
const xyYDisplay = document.getElementById('xy-y');

// Message log
const messageLog = document.getElementById('message-log');
const clearLogBtn = document.getElementById('clear-log-btn');

// Custom message
const customMessageInput = document.getElementById('custom-message');
const sendCustomBtn = document.getElementById('send-custom-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateConnectionUI(false);
});

// Setup all event listeners
function setupEventListeners() {
    // Connection controls
    connectBtn.addEventListener('click', connectWebSocket);
    disconnectBtn.addEventListener('click', disconnectWebSocket);

    // Sliders
    slider1.addEventListener('input', () => updateSliderValue(slider1, slider1Value, 'slider1'));
    slider2.addEventListener('input', () => updateSliderValue(slider2, slider2Value, 'slider2'));
    slider3.addEventListener('input', () => updateSliderValue(slider3, slider3Value, 'slider3'));

    // Color picker
    colorPicker.addEventListener('input', handleColorChange);

    // Buttons
    triggerBtn.addEventListener('click', handleTrigger);
    resetBtn.addEventListener('click', handleReset);

    // XY Pad
    xyPad.addEventListener('mousedown', startXYDrag);
    xyPad.addEventListener('touchstart', startXYDrag);

    // Message log
    clearLogBtn.addEventListener('click', clearMessageLog);

    // Custom message
    sendCustomBtn.addEventListener('click', sendCustomMessage);
}

// WebSocket connection
function connectWebSocket() {
    const url = websocketUrlInput.value.trim();

    if (!url) {
        logMessage('Please enter a WebSocket URL', 'error');
        return;
    }

    try {
        ws = new WebSocket(url);

        ws.onopen = () => {
            isConnected = true;
            updateConnectionUI(true);
            logMessage('Connected to WebSocket server', 'received');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                logMessage(`Received: ${JSON.stringify(data)}`, 'received');
                handleIncomingMessage(data);
            } catch (error) {
                logMessage(`Received: ${event.data}`, 'received');
            }
        };

        ws.onerror = (error) => {
            logMessage('WebSocket error occurred', 'error');
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            isConnected = false;
            updateConnectionUI(false);
            logMessage('Disconnected from WebSocket server', 'error');
        };

    } catch (error) {
        logMessage(`Connection failed: ${error.message}`, 'error');
    }
}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
    isConnected = false;
    updateConnectionUI(false);
}

function updateConnectionUI(connected) {
    if (connected) {
        statusIndicator.classList.remove('disconnected');
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected';
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
        websocketUrlInput.disabled = true;
    } else {
        statusIndicator.classList.remove('connected');
        statusIndicator.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        websocketUrlInput.disabled = false;
    }
}

// Send message to WebSocket
function sendMessage(data) {
    if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
        logMessage('Not connected to WebSocket', 'error');
        return false;
    }

    try {
        const message = JSON.stringify(data);
        ws.send(message);
        logMessage(`Sent: ${message}`, 'sent');
        return true;
    } catch (error) {
        logMessage(`Send error: ${error.message}`, 'error');
        return false;
    }
}

// Handle incoming messages from TouchDesigner
function handleIncomingMessage(data) {
    // Handle different message types
    switch (data.type) {
        case 'parameterUpdate':
            updateUIFromTouchDesigner(data);
            break;
        case 'connection':
            console.log('Connection message:', data.message);
            break;
        case 'echo':
            console.log('Echo received:', data.data);
            break;
        default:
            console.log('Unknown message type:', data);
    }
}

// Update UI based on TouchDesigner feedback
function updateUIFromTouchDesigner(data) {
    if (data.slider1 !== undefined) {
        slider1.value = data.slider1;
        slider1Value.textContent = data.slider1;
    }
    if (data.slider2 !== undefined) {
        slider2.value = data.slider2;
        slider2Value.textContent = data.slider2;
    }
    if (data.slider3 !== undefined) {
        slider3.value = data.slider3;
        slider3Value.textContent = data.slider3;
    }
}

// Slider handling
function updateSliderValue(slider, display, name) {
    const value = slider.value;
    display.textContent = value;

    sendMessage({
        type: 'parameter',
        name: name,
        value: parseFloat(value)
    });
}

// Color picker handling
function handleColorChange(e) {
    const color = e.target.value;
    const rgb = hexToRgb(color);

    sendMessage({
        type: 'color',
        hex: color,
        rgb: rgb
    });
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16) / 255,
        g: parseInt(result[2], 16) / 255,
        b: parseInt(result[3], 16) / 255
    } : null;
}

// Trigger button
function handleTrigger() {
    sendMessage({
        type: 'trigger',
        name: 'mainTrigger',
        timestamp: Date.now()
    });
}

// Reset button
function handleReset() {
    slider1.value = 50;
    slider2.value = 50;
    slider3.value = 50;
    slider1Value.textContent = '50';
    slider2Value.textContent = '50';
    slider3Value.textContent = '50';
    colorPicker.value = '#ff0000';

    // Reset XY pad to center
    updateXYPosition(0.5, 0.5);

    sendMessage({
        type: 'reset',
        timestamp: Date.now()
    });
}

// XY Pad handling
let isDragging = false;

function startXYDrag(e) {
    isDragging = true;
    updateXYFromEvent(e);

    const moveHandler = (e) => {
        if (isDragging) {
            updateXYFromEvent(e);
        }
    };

    const endHandler = () => {
        isDragging = false;
        document.removeEventListener('mousemove', moveHandler);
        document.removeEventListener('mouseup', endHandler);
        document.removeEventListener('touchmove', moveHandler);
        document.removeEventListener('touchend', endHandler);
    };

    document.addEventListener('mousemove', moveHandler);
    document.addEventListener('mouseup', endHandler);
    document.addEventListener('touchmove', moveHandler);
    document.addEventListener('touchend', endHandler);
}

function updateXYFromEvent(e) {
    e.preventDefault();
    const rect = xyPad.getBoundingClientRect();
    let clientX, clientY;

    if (e.type.startsWith('touch')) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    } else {
        clientX = e.clientX;
        clientY = e.clientY;
    }

    let x = (clientX - rect.left) / rect.width;
    let y = 1 - ((clientY - rect.top) / rect.height); // Invert Y axis

    // Clamp values
    x = Math.max(0, Math.min(1, x));
    y = Math.max(0, Math.min(1, y));

    updateXYPosition(x, y);

    sendMessage({
        type: 'xy',
        x: x,
        y: y
    });
}

function updateXYPosition(x, y) {
    const rect = xyPad.getBoundingClientRect();
    xyCursor.style.left = `${x * 100}%`;
    xyCursor.style.top = `${(1 - y) * 100}%`; // Invert Y for display

    xyXDisplay.textContent = x.toFixed(2);
    xyYDisplay.textContent = y.toFixed(2);
}

// Message logging
function logMessage(message, type = 'sent') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;

    const timestamp = new Date().toLocaleTimeString();
    entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;

    messageLog.appendChild(entry);
    messageLog.scrollTop = messageLog.scrollHeight;

    // Limit log entries
    while (messageLog.children.length > 100) {
        messageLog.removeChild(messageLog.firstChild);
    }
}

function clearMessageLog() {
    messageLog.innerHTML = '';
}

// Custom message
function sendCustomMessage() {
    const messageText = customMessageInput.value.trim();

    if (!messageText) {
        logMessage('Please enter a message', 'error');
        return;
    }

    try {
        const data = JSON.parse(messageText);
        sendMessage(data);
    } catch (error) {
        logMessage(`Invalid JSON: ${error.message}`, 'error');
    }
}

// Initialize XY pad position
updateXYPosition(0.5, 0.5);
