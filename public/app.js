// WebSocket connection
let ws = null;
let isConnected = false;

// UI Config
let uiConfig = null;
let currentPageId = null;

// DOM elements
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const websocketUrlInput = document.getElementById('websocket-url');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const connectionPanel = document.getElementById('connection-panel');
const toggleConnectionBtn = document.getElementById('toggle-connection-btn');

// Message log
const messageLog = document.getElementById('message-log');
const clearLogBtn = document.getElementById('clear-log-btn');

// Custom message
const customMessageInput = document.getElementById('custom-message');
const sendCustomBtn = document.getElementById('send-custom-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    preventZoom();
    setupIOSFixes();
    await loadConfig(); // Wait for config to load before rendering
    renderUI();
    setupEventListeners();
    updateConnectionUI(false);
});

// ============================================================================
// CONFIG LOADING & MIGRATION
// ============================================================================

async function loadConfig() {
    // Load from TouchDesigner server (single source of truth)
    try {
        console.log('[Viewer] Loading config from TouchDesigner server...');
        const response = await fetch('/api/config');

        if (response.ok) {
            const loaded = await response.json();
            uiConfig = migrateOldConfig(loaded);
            currentPageId = uiConfig.pages[0].id;
            console.log('[Viewer] ✓ Config loaded from server');
            return;
        }
    } catch (e) {
        console.error('[Viewer] Failed to connect to server:', e);
    }

    // Server unavailable or error - use empty default
    uiConfig = getDefaultConfig();
    currentPageId = uiConfig.pages[0].id;
    console.log('[Viewer] Server unavailable - showing empty UI. Use Builder to create controls.');
}

function migrateOldConfig(config) {
    // If config has 'controls' property (old format), migrate to pages format
    if (config.controls && !config.pages) {
        return {
            version: config.version || "1.0",
            pages: [
                {
                    id: "page1",
                    name: config.name || "Main",
                    controls: config.controls
                }
            ]
        };
    }
    // Already in new format
    return config;
}

function getDefaultConfig() {
    return {
        version: "1.0",
        pages: [
            {
                id: "page1",
                name: "Default",
                controls: []  // Empty - use builder to create controls and save to TouchDesigner
            }
        ]
    };
}

// ============================================================================
// UI RENDERING
// ============================================================================

function renderUI() {
    renderPageTabs();
    renderCurrentPage();
}

function renderPageTabs() {
    const tabNav = document.querySelector('.tab-nav');
    tabNav.innerHTML = '';

    // Render page tabs from config
    uiConfig.pages.forEach(page => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        if (page.id === currentPageId) {
            btn.classList.add('active');
        }
        btn.dataset.tab = page.id;
        btn.textContent = page.name;
        btn.addEventListener('click', () => switchToPage(page.id));
        tabNav.appendChild(btn);
    });

    // Add Advanced tab (static)
    const advancedBtn = document.createElement('button');
    advancedBtn.className = 'tab-btn';
    advancedBtn.dataset.tab = 'advanced';
    advancedBtn.textContent = 'Advanced';
    advancedBtn.addEventListener('click', () => switchToAdvanced());
    tabNav.appendChild(advancedBtn);
}

function switchToPage(pageId) {
    currentPageId = pageId;

    // Hide advanced tab (if it was showing)
    const advancedTab = document.getElementById('tab-advanced');
    if (advancedTab) {
        advancedTab.classList.remove('active');
    }

    renderCurrentPage();

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === pageId);
    });
}

function switchToAdvanced() {
    // Hide all page content
    document.querySelectorAll('.tab-content[data-page]').forEach(content => {
        content.classList.remove('active');
    });

    // Show advanced tab
    const advancedTab = document.getElementById('tab-advanced');
    if (advancedTab) {
        advancedTab.classList.add('active');
    }

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === 'advanced');
    });
}

function renderCurrentPage() {
    const wrapper = document.querySelector('.tab-content-wrapper');
    const page = uiConfig.pages.find(p => p.id === currentPageId);
    if (!page) return;

    // Clear existing page tabs (not advanced tab)
    wrapper.querySelectorAll('.tab-content[data-page]').forEach(el => el.remove());

    // Create content for current page
    const content = document.createElement('div');
    content.className = 'tab-content active';
    content.dataset.page = currentPageId;

    const scrollable = document.createElement('div');
    scrollable.className = 'scrollable-content';

    // Show helpful message if no controls configured
    if (page.controls.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.style.cssText = 'text-align: center; padding: 60px 20px; color: #888;';
        emptyState.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 20px; opacity: 0.3;">📱</div>
            <p style="font-size: 20px; margin-bottom: 15px; color: #aaa;">No controls configured</p>
            <p style="font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                Use the <strong>Builder</strong> to create your custom UI<br>
                and save it to TouchDesigner
            </p>
            <a href="/builder.html" style="
                display: inline-block;
                padding: 12px 24px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 500;
                transition: background 0.2s;
            " onmouseover="this.style.background='#45a049'"
               onmouseout="this.style.background='#4CAF50'">
                Open Builder →
            </a>
        `;
        scrollable.appendChild(emptyState);
    } else {
        // Render controls
        page.controls.forEach(control => {
            const element = createControlElement(control);
            scrollable.appendChild(element);
        });
    }

    content.appendChild(scrollable);
    wrapper.insertBefore(content, document.getElementById('tab-advanced'));
}

function createControlElement(control) {
    const group = document.createElement('div');
    group.className = 'control-group';

    if (control.type === 'slider') {
        const label = document.createElement('label');
        label.setAttribute('for', control.id);
        label.textContent = control.label;

        const slider = document.createElement('input');
        slider.type = 'range';
        slider.id = control.id;
        slider.className = 'slider';
        slider.min = control.min;
        slider.max = control.max;
        slider.value = control.default;

        const valueDisplay = document.createElement('span');
        valueDisplay.id = `${control.id}-value`;
        valueDisplay.className = 'value-display';
        valueDisplay.textContent = control.default;

        slider.addEventListener('input', () => {
            valueDisplay.textContent = slider.value;
            sendMessage({
                type: 'parameter',
                id: control.id,
                label: control.label,
                value: parseFloat(slider.value),
                chop: control.chop,
                channel: control.channel
            });
        });

        group.appendChild(label);
        group.appendChild(slider);
        group.appendChild(valueDisplay);

    } else if (control.type === 'color') {
        const label = document.createElement('label');
        label.setAttribute('for', control.id);
        label.textContent = control.label;

        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.id = control.id;
        colorPicker.value = control.default;

        colorPicker.addEventListener('input', (e) => {
            const rgb = hexToRgb(e.target.value);
            sendMessage({
                type: 'color',
                id: control.id,
                label: control.label,
                hex: e.target.value,
                rgb: rgb,
                chop: control.chop
            });
        });

        group.appendChild(label);
        group.appendChild(colorPicker);

    } else if (control.type === 'xy') {
        const label = document.createElement('label');
        label.textContent = control.label;

        const xyContainer = document.createElement('div');
        xyContainer.className = 'xy-pad-container';

        const xyPad = document.createElement('div');
        xyPad.className = 'xy-pad';
        xyPad.id = control.id;

        const xyCursor = document.createElement('div');
        xyCursor.className = 'xy-cursor';
        xyCursor.id = `${control.id}-cursor`;
        xyPad.appendChild(xyCursor);

        const xyValues = document.createElement('div');
        xyValues.className = 'xy-values';
        xyValues.innerHTML = `
            <div class="xy-value">
                <span class="xy-label">X</span>
                <span id="${control.id}-x" class="xy-number">${control.default.x.toFixed(2)}</span>
            </div>
            <div class="xy-value">
                <span class="xy-label">Y</span>
                <span id="${control.id}-y" class="xy-number">${control.default.y.toFixed(2)}</span>
            </div>
        `;

        xyContainer.appendChild(xyPad);
        xyContainer.appendChild(xyValues);

        group.appendChild(label);
        group.appendChild(xyContainer);

        // Setup XY pad interaction
        setTimeout(() => setupXYPadForControl(control), 0);

    } else if (control.type === 'button') {
        const label = document.createElement('label');
        label.textContent = control.label;

        const button = document.createElement('button');
        button.id = control.id;
        button.className = 'control-button';
        button.dataset.state = control.default || 0;

        // Set initial appearance
        if (parseInt(button.dataset.state) === 1) {
            button.classList.add('active');
            button.textContent = 'ON';
        } else {
            button.textContent = 'OFF';
        }

        // Toggle on click
        button.addEventListener('click', () => {
            const currentState = parseInt(button.dataset.state);
            const newState = currentState === 1 ? 0 : 1;

            button.dataset.state = newState;
            button.classList.toggle('active', newState === 1);
            button.textContent = newState === 1 ? 'ON' : 'OFF';

            sendMessage({
                type: 'button',
                id: control.id,
                label: control.label,
                state: newState,
                chop: control.chop
            });
        });

        group.appendChild(label);
        group.appendChild(button);
    }

    return group;
}

function setupXYPadForControl(control) {
    const xyPad = document.getElementById(control.id);
    const xyCursor = document.getElementById(`${control.id}-cursor`);
    const xyXDisplay = document.getElementById(`${control.id}-x`);
    const xyYDisplay = document.getElementById(`${control.id}-y`);

    if (!xyPad) return;

    let isDragging = false;

    // Touch events
    xyPad.addEventListener('touchstart', (e) => {
        e.preventDefault();
        isDragging = true;
        updateXYFromEvent(e, control);
    }, { passive: false });

    xyPad.addEventListener('touchmove', (e) => {
        e.preventDefault();
        if (isDragging) {
            updateXYFromEvent(e, control);
        }
    }, { passive: false });

    xyPad.addEventListener('touchend', (e) => {
        e.preventDefault();
        isDragging = false;
    }, { passive: false });

    xyPad.addEventListener('touchcancel', (e) => {
        e.preventDefault();
        isDragging = false;
    }, { passive: false });

    // Mouse events
    xyPad.addEventListener('mousedown', (e) => {
        isDragging = true;
        updateXYFromEvent(e, control);
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging && document.getElementById(control.id) === xyPad) {
            updateXYFromEvent(e, control);
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    function updateXYFromEvent(e, ctrl) {
        const rect = xyPad.getBoundingClientRect();
        let clientX, clientY;

        if (e.type.startsWith('touch')) {
            if (e.touches.length > 0) {
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            } else {
                return;
            }
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        let x = (clientX - rect.left) / rect.width;
        let y = 1 - ((clientY - rect.top) / rect.height);

        // Clamp values
        x = Math.max(0, Math.min(1, x));
        y = Math.max(0, Math.min(1, y));

        xyCursor.style.left = `${x * 100}%`;
        xyCursor.style.top = `${(1 - y) * 100}%`;
        xyXDisplay.textContent = x.toFixed(2);
        xyYDisplay.textContent = y.toFixed(2);

        sendMessage({
            type: 'xy',
            id: ctrl.id,
            label: ctrl.label,
            x: x,
            y: y,
            chop: ctrl.chop
        });
    }

    // Initialize position
    xyCursor.style.left = `${control.default.x * 100}%`;
    xyCursor.style.top = `${(1 - control.default.y) * 100}%`;
}

// ============================================================================
// EVENT LISTENERS (LEGACY COMPATIBILITY)
// ============================================================================

// Prevent Double-Tap and Pinch Zoom (iOS)
function preventZoom() {
    // Prevent double-tap zoom
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (e) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, { passive: false });

    // Prevent pinch zoom
    document.addEventListener('gesturestart', (e) => {
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('gesturechange', (e) => {
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('gestureend', (e) => {
        e.preventDefault();
    }, { passive: false });

    // Prevent pinch with touchmove
    let initialDistance = null;
    document.addEventListener('touchstart', (e) => {
        if (e.touches.length >= 2) {
            initialDistance = getDistance(e.touches[0], e.touches[1]);
        }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        if (e.touches.length >= 2) {
            e.preventDefault();
        }
    }, { passive: false });
}

function getDistance(touch1, touch2) {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

// iOS Specific Fixes
function setupIOSFixes() {
    // Prevent bounce scrolling on body
    document.body.addEventListener('touchmove', (e) => {
        if (e.target === document.body) {
            e.preventDefault();
        }
    }, { passive: false });

    // Fix 100vh on iOS
    const setVh = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    setVh();
    window.addEventListener('resize', setVh);
    window.addEventListener('orientationchange', setVh);
}

// Setup all event listeners
function setupEventListeners() {
    // Connection controls
    connectBtn.addEventListener('click', connectWebSocket);
    disconnectBtn.addEventListener('click', disconnectWebSocket);
    toggleConnectionBtn.addEventListener('click', toggleConnectionPanel);

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

        // Auto-minimize connection panel on connect
        connectionPanel.classList.add('minimized');
        toggleConnectionBtn.classList.add('rotated');
    } else {
        statusIndicator.classList.remove('connected');
        statusIndicator.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        websocketUrlInput.disabled = false;

        // Auto-expand connection panel on disconnect
        connectionPanel.classList.remove('minimized');
        toggleConnectionBtn.classList.remove('rotated');
    }
}

// Toggle connection panel visibility
function toggleConnectionPanel() {
    connectionPanel.classList.toggle('minimized');
    toggleConnectionBtn.classList.toggle('rotated');
}

// Send message to WebSocket
function sendMessage(data) {
    if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }

    try {
        const message = JSON.stringify(data);
        ws.send(message);
        logMessage(`Sent: ${message}`, 'sent');
    } catch (error) {
        logMessage(`Send error: ${error.message}`, 'error');
    }
}

// Handle incoming messages from TouchDesigner
function handleIncomingMessage(data) {
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

// Update UI based on TouchDesigner feedback (for bidirectional updates)
function updateUIFromTouchDesigner(data) {
    if (data.slider1 !== undefined) {
        slider1.value = data.slider1;
        document.getElementById('slider1-value').textContent = data.slider1;
    }
    if (data.slider2 !== undefined) {
        slider2.value = data.slider2;
        document.getElementById('slider2-value').textContent = data.slider2;
    }
    if (data.slider3 !== undefined) {
        slider3.value = data.slider3;
        document.getElementById('slider3-value').textContent = data.slider3;
    }
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16) / 255,
        g: parseInt(result[2], 16) / 255,
        b: parseInt(result[3], 16) / 255
    } : null;
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
