/**
 * TouchDesigner UI Builder
 * Build custom control interfaces for TouchDesigner WebSocket control
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const state = {
    config: {
        version: "1.0",
        pages: [
            {
                id: "page1",
                name: "Main",
                controls: []
            }
        ]
    },
    currentPageId: "page1",
    selectedControlId: null,
    nextId: 1,
    nextPageId: 2
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getCurrentPage() {
    return state.config.pages.find(p => p.id === state.currentPageId);
}

function getCurrentControls() {
    const page = getCurrentPage();
    return page ? page.controls : [];
}

function sanitizeName(name) {
    // Sanitize page name for use as CHOP name (matches Python implementation)
    // Remove special characters, replace with underscore
    let sanitized = name.replace(/[^a-zA-Z0-9_]/g, '_');
    // Remove consecutive underscores
    sanitized = sanitized.replace(/_+/g, '_');
    // Remove leading/trailing underscores
    sanitized = sanitized.replace(/^_+|_+$/g, '');
    // Lowercase
    sanitized = sanitized.toLowerCase();
    return sanitized || 'page';
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

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadFromLocalStorage();
    initializeEventListeners();
    renderPageTabs();
    renderControlsList();
    setPreviewMode('mobile'); // Set default mobile mode
    renderPreview();
    updateControlCount();
});

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function initializeEventListeners() {
    // Control palette buttons
    document.querySelectorAll('.palette-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            addControl(type);
        });
    });

    // Header actions
    document.getElementById('save-to-server-btn').addEventListener('click', saveToServer);
    document.getElementById('load-from-server-btn').addEventListener('click', loadFromServer);
    document.getElementById('clear-all-btn').addEventListener('click', showClearConfirmation);

    // Preview mode selector
    document.getElementById('preview-mode').addEventListener('change', (e) => {
        setPreviewMode(e.target.value);
    });

    // Modal
    document.getElementById('modal-cancel').addEventListener('click', hideModal);
    document.getElementById('modal-confirm').addEventListener('click', handleModalConfirm);
}

// ============================================================================
// CONTROL MANAGEMENT
// ============================================================================

function addControl(type) {
    const control = createDefaultControl(type);
    const currentPage = getCurrentPage();
    if (!currentPage) return;

    currentPage.controls.push(control);
    state.nextId++;

    saveToLocalStorage();
    renderControlsList();
    renderPreview();
    updateControlCount();

    // Auto-select and edit the new control
    selectControl(control.id);
}

function createDefaultControl(type) {
    const id = `${type}${state.nextId}`;

    // Auto-populate CHOP name based on current page
    const currentPage = getCurrentPage();
    const pageName = currentPage ? currentPage.name : 'main';
    const chopName = `${sanitizeName(pageName)}_controls`;

    const defaults = {
        slider: {
            id,
            type: 'slider',
            label: `Slider ${state.nextId}`,
            chop: chopName,
            channel: 0,
            min: 0,
            max: 100,
            default: 50
        },
        color: {
            id,
            type: 'color',
            label: `Color ${state.nextId}`,
            chop: chopName,
            default: '#ff0000'
        },
        xy: {
            id,
            type: 'xy',
            label: `XY Pad ${state.nextId}`,
            chop: chopName,
            default: { x: 0.5, y: 0.5 }
        },
        button: {
            id,
            type: 'button',
            label: `Button ${state.nextId}`,
            chop: chopName,
            default: 0  // 0 = off, 1 = on
        }
    };

    return defaults[type];
}

function deleteControl(id) {
    const controls = getCurrentControls();
    const index = controls.findIndex(c => c.id === id);
    if (index !== -1) {
        controls.splice(index, 1);

        if (state.selectedControlId === id) {
            state.selectedControlId = null;
            closeProperties();
        }

        saveToLocalStorage();
        renderControlsList();
        renderPreview();
        updateControlCount();
    }
}

function moveControl(id, direction) {
    const controls = getCurrentControls();
    const index = controls.findIndex(c => c.id === id);
    if (index === -1) return;

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= controls.length) return;

    // Swap
    [controls[index], controls[newIndex]] = [controls[newIndex], controls[index]];

    saveToLocalStorage();
    renderControlsList();
    renderPreview();
}

function selectControl(id) {
    state.selectedControlId = id;
    renderControlsList(); // Update selection visual
}

function enterEditMode(id) {
    // Find the control item
    const items = document.querySelectorAll('.control-item');
    items.forEach(item => {
        if (item.dataset.controlId === id) {
            item.classList.add('editing');
            item.draggable = false; // Disable drag in edit mode
            // Focus first input
            const firstInput = item.querySelector('.control-edit-input');
            if (firstInput) firstInput.focus();
        } else {
            item.classList.remove('editing');
            item.draggable = true; // Ensure others are draggable
        }
    });
}

function saveInlineEdit(id) {
    const control = getCurrentControls().find(c => c.id === id);
    if (!control) return;

    // Find the control item
    const item = document.querySelector(`[data-control-id="${id}"]`);
    if (!item) return;

    // Get all input fields
    const inputs = item.querySelectorAll('.control-edit-input');
    inputs.forEach(input => {
        const field = input.dataset.field;
        const value = input.type === 'number' ? parseFloat(input.value) :
                      input.type === 'color' ? input.value :
                      input.tagName === 'SELECT' ? parseInt(input.value) :
                      input.value;

        // Handle nested fields (like default.x)
        if (field.includes('.')) {
            const parts = field.split('.');
            control[parts[0]][parts[1]] = value;
        } else {
            control[field] = value;
        }
    });

    // Exit edit mode
    item.classList.remove('editing');
    item.draggable = true; // Re-enable drag

    // Save and re-render
    saveToLocalStorage();
    renderControlsList();
    renderPreview();
}

function cancelInlineEdit(id) {
    const item = document.querySelector(`[data-control-id="${id}"]`);
    if (item) {
        item.classList.remove('editing');
        item.draggable = true; // Re-enable drag
    }
}

// ============================================================================
// DRAG & DROP HANDLERS
// ============================================================================

let draggedControlId = null;

function handleDragStart(e) {
    draggedControlId = e.currentTarget.dataset.controlId;
    e.currentTarget.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.currentTarget.innerHTML);
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Allows drop
    }
    e.dataTransfer.dropEffect = 'move';

    const target = e.currentTarget;
    if (target.dataset.controlId === draggedControlId) {
        return false; // Don't highlight self
    }

    // Calculate if cursor is in top or bottom half (continuous feedback)
    const rect = target.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    const isTopHalf = e.clientY < midpoint;

    // Remove all drag-over classes first
    document.querySelectorAll('.control-item').forEach(item => {
        item.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    // Add appropriate class
    if (isTopHalf) {
        target.classList.add('drag-over-top');
    } else {
        target.classList.add('drag-over-bottom');
    }

    return false;
}

function handleDragEnter(e) {
    // Now just used for initial hover - dragover handles continuous feedback
    e.preventDefault();
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over-top', 'drag-over-bottom');
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation(); // Stops browser redirect
    }

    const targetControlId = e.currentTarget.dataset.controlId;

    if (draggedControlId === targetControlId) {
        return false;
    }

    // Calculate drop position (above or below target)
    const rect = e.currentTarget.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    const dropBelow = e.clientY >= midpoint;

    // Reorder the controls
    reorderControl(draggedControlId, targetControlId, dropBelow);

    return false;
}

function handleDragEnd(e) {
    e.currentTarget.classList.remove('dragging');

    // Remove all drag-over indicators
    document.querySelectorAll('.control-item').forEach(item => {
        item.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    draggedControlId = null;
}

function reorderControl(draggedId, targetId, dropBelow) {
    const controls = getCurrentControls();

    // Find indices
    const draggedIndex = controls.findIndex(c => c.id === draggedId);
    const targetIndex = controls.findIndex(c => c.id === targetId);

    if (draggedIndex === -1 || targetIndex === -1) return;

    // Remove dragged control
    const [draggedControl] = controls.splice(draggedIndex, 1);

    // Calculate new index (account for removal shifting indices)
    let newIndex = targetIndex;
    if (draggedIndex < targetIndex) {
        newIndex = dropBelow ? targetIndex : targetIndex - 1;
    } else {
        newIndex = dropBelow ? targetIndex + 1 : targetIndex;
    }

    // Insert at new position
    controls.splice(newIndex, 0, draggedControl);

    // Save and re-render
    saveToLocalStorage();
    renderControlsList();
    renderPreview();
}

// ============================================================================
// RENDERING
// ============================================================================

function renderControlsList() {
    const container = document.getElementById('controls-list');
    const emptyState = document.getElementById('empty-state');
    const controls = getCurrentControls();

    if (controls.length === 0) {
        emptyState.style.display = 'flex';
        return;
    }

    emptyState.style.display = 'none';

    // Clear existing controls (except empty state)
    const existingItems = container.querySelectorAll('.control-item');
    existingItems.forEach(item => item.remove());

    controls.forEach((control, index) => {
        const item = createControlListItem(control, index);
        container.appendChild(item);
    });
}

function createControlListItem(control, index) {
    const item = document.createElement('div');
    item.className = 'control-item';
    if (control.id === state.selectedControlId) {
        item.classList.add('selected');
    }

    // Make item draggable
    item.draggable = true;
    item.dataset.controlId = control.id;

    const typeIcons = {
        slider: '<line x1="4" y1="12" x2="20" y2="12"/><circle cx="12" cy="12" r="3" fill="currentColor"/>',
        color: '<circle cx="12" cy="12" r="10"/><path d="M12 2 L12 12 L20 12"/>',
        xy: '<rect x="4" y="4" width="16" height="16" rx="2"/><circle cx="12" cy="12" r="2" fill="currentColor"/>',
        button: '<rect x="6" y="8" width="12" height="8" rx="2" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="white"/>'
    };

    const metaText = control.type === 'slider'
        ? `Range: ${control.min}-${control.max} • Default: ${control.default}`
        : control.type === 'color' ? `Color Picker • ${control.default}`
        : control.type === 'xy' ? `XY Pad • (${control.default.x}, ${control.default.y})`
        : control.type === 'button' ? `Button • ${control.default === 1 ? 'ON' : 'OFF'}`
        : '';

    const controls = getCurrentControls();

    // Create edit mode HTML based on control type
    let editHTML = `
        <div class="control-edit-row">
            <span class="control-edit-label">Label</span>
            <input type="text" class="control-edit-input" data-field="label" value="${control.label}">
        </div>
    `;

    if (control.type === 'slider') {
        editHTML += `
            <div class="control-edit-row">
                <span class="control-edit-label">Min</span>
                <input type="number" class="control-edit-input control-edit-input-small" data-field="min" value="${control.min}">
                <span class="control-edit-label">Max</span>
                <input type="number" class="control-edit-input control-edit-input-small" data-field="max" value="${control.max}">
                <span class="control-edit-label">Default</span>
                <input type="number" class="control-edit-input control-edit-input-small" data-field="default" value="${control.default}">
            </div>
        `;
    } else if (control.type === 'color') {
        editHTML += `
            <div class="control-edit-row">
                <span class="control-edit-label">Default</span>
                <input type="color" class="control-edit-input" data-field="default" value="${control.default}">
            </div>
        `;
    } else if (control.type === 'xy') {
        editHTML += `
            <div class="control-edit-row">
                <span class="control-edit-label">X</span>
                <input type="number" class="control-edit-input control-edit-input-small" data-field="default.x" value="${control.default.x}" min="0" max="1" step="0.01">
                <span class="control-edit-label">Y</span>
                <input type="number" class="control-edit-input control-edit-input-small" data-field="default.y" value="${control.default.y}" min="0" max="1" step="0.01">
            </div>
        `;
    } else if (control.type === 'button') {
        editHTML += `
            <div class="control-edit-row">
                <span class="control-edit-label">Default</span>
                <select class="control-edit-input control-edit-input-small" data-field="default">
                    <option value="0" ${control.default === 0 ? 'selected' : ''}>OFF</option>
                    <option value="1" ${control.default === 1 ? 'selected' : ''}>ON</option>
                </select>
            </div>
        `;
    }

    item.innerHTML = `
        <!-- VIEW MODE -->
        <div class="control-item-view">
            <div class="control-item-header">
                <div class="control-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${typeIcons[control.type]}
                    </svg>
                </div>
                <div class="control-info">
                    <div class="control-label">${control.label}</div>
                    <div class="control-meta">${metaText}</div>
                </div>
            </div>
            <div class="control-actions">
                <button class="btn-icon btn-edit" title="Edit">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M0 9.5L0 12L2.5 12L9.87 4.63L7.37 2.13L0 9.5ZM11.71 2.79C12.1 2.4 12.1 1.77 11.71 1.38L10.62 0.29C10.23 -0.1 9.6 -0.1 9.21 0.29L8.38 1.12L10.88 3.62L11.71 2.79Z"/>
                    </svg>
                </button>
                <div class="control-order-btns">
                    <button class="btn-icon btn-up" ${index === 0 ? 'disabled' : ''} title="Move up">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                            <path d="M6 3L2 7h8z"/>
                        </svg>
                    </button>
                    <button class="btn-icon btn-down" ${index === controls.length - 1 ? 'disabled' : ''} title="Move down">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                            <path d="M6 9L2 5h8z"/>
                        </svg>
                    </button>
                </div>
                <button class="btn-icon btn-delete" title="Delete">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M2 2l8 8M10 2l-8 8"/>
                    </svg>
                </button>
            </div>
        </div>

        <!-- EDIT MODE -->
        <div class="control-item-edit">
            ${editHTML}
            <div class="control-edit-actions">
                <button class="btn-icon btn-save" title="Save">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M4 8L0 4L1.5 2.5L4 5L10.5 0L12 1.5L4 8Z"/>
                    </svg>
                </button>
                <button class="btn-icon btn-cancel" title="Cancel">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M2 2l8 8M10 2l-8 8"/>
                    </svg>
                </button>
            </div>
        </div>
    `;

    // Event listeners for VIEW mode
    item.querySelector('.btn-edit').addEventListener('click', (e) => {
        e.stopPropagation();
        enterEditMode(control.id);
    });

    item.querySelector('.btn-up')?.addEventListener('click', (e) => {
        e.stopPropagation();
        moveControl(control.id, 'up');
    });

    item.querySelector('.btn-down')?.addEventListener('click', (e) => {
        e.stopPropagation();
        moveControl(control.id, 'down');
    });

    item.querySelector('.btn-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        showDeleteConfirmation(control.id);
    });

    // Event listeners for EDIT mode
    item.querySelector('.btn-save').addEventListener('click', (e) => {
        e.stopPropagation();
        saveInlineEdit(control.id);
    });

    item.querySelector('.btn-cancel').addEventListener('click', (e) => {
        e.stopPropagation();
        cancelInlineEdit(control.id);
    });

    // Keyboard shortcuts for EDIT mode
    const editInputs = item.querySelectorAll('.control-edit-input');
    editInputs.forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveInlineEdit(control.id);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelInlineEdit(control.id);
            }
        });
    });

    // Drag & Drop event listeners
    item.addEventListener('dragstart', handleDragStart);
    item.addEventListener('dragover', handleDragOver);
    item.addEventListener('dragenter', handleDragEnter);
    item.addEventListener('dragleave', handleDragLeave);
    item.addEventListener('drop', handleDrop);
    item.addEventListener('dragend', handleDragEnd);

    return item;
}

function renderPreview() {
    const container = document.getElementById('preview-container');
    const emptyMsg = document.getElementById('preview-empty');
    const controls = getCurrentControls();

    if (controls.length === 0) {
        emptyMsg.style.display = 'flex';
        // Clear content container
        const existingContent = container.querySelector('.preview-content');
        if (existingContent) existingContent.remove();
        return;
    }

    emptyMsg.style.display = 'none';

    // Get or create preview content wrapper
    let contentWrapper = container.querySelector('.preview-content');
    if (!contentWrapper) {
        contentWrapper = document.createElement('div');
        contentWrapper.className = 'preview-content';
        container.appendChild(contentWrapper);
    }

    // Clear existing controls
    contentWrapper.innerHTML = '';

    // Render controls inside content wrapper
    controls.forEach(control => {
        const element = createPreviewElement(control);
        contentWrapper.appendChild(element);
    });
}

function setPreviewMode(mode) {
    const container = document.getElementById('preview-container');

    // Remove existing mode classes
    container.classList.remove('mobile-mode', 'desktop-mode');

    // Add new mode class
    container.classList.add(`${mode}-mode`);

    // Re-render preview to apply new layout
    renderPreview();
}

function createPreviewElement(control) {
    const group = document.createElement('div');
    group.className = 'preview-control-group';

    if (control.type === 'slider') {
        group.innerHTML = `
            <label>${control.label}</label>
            <input type="range" class="preview-slider" min="${control.min}" max="${control.max}" value="${control.default}" disabled>
            <span class="preview-value">${control.default}</span>
        `;
    } else if (control.type === 'color') {
        group.innerHTML = `
            <label>${control.label}</label>
            <input type="color" class="preview-color" value="${control.default}" disabled>
        `;
    } else if (control.type === 'xy') {
        const x = control.default.x * 100;
        const y = (1 - control.default.y) * 100; // Invert Y for visual
        group.innerHTML = `
            <label>${control.label}</label>
            <div class="preview-xy-pad">
                <div class="preview-xy-cursor" style="left: ${x}%; top: ${y}%;"></div>
            </div>
        `;
    } else if (control.type === 'button') {
        const isActive = control.default === 1;
        group.innerHTML = `
            <label>${control.label}</label>
            <button class="preview-button ${isActive ? 'active' : ''}" disabled>
                ${isActive ? 'ON' : 'OFF'}
            </button>
        `;
    }

    return group;
}

function updateControlCount() {
    const count = getCurrentControls().length;
    const currentPage = getCurrentPage();
    const pageName = currentPage ? currentPage.name : 'Page';
    document.getElementById('control-count').textContent =
        `${pageName}: ${count} control${count !== 1 ? 's' : ''}`;
}

// ============================================================================
// PROPERTIES PANEL
// ============================================================================

function showProperties(id) {
    const control = getCurrentControls().find(c => c.id === id);
    if (!control) return;

    // Remove any existing inline properties first
    closeProperties();

    // Find the selected control item in DOM
    const controlItems = document.querySelectorAll('.control-item');
    let selectedItem = null;
    controlItems.forEach(item => {
        if (item.dataset.controlId === id) {
            selectedItem = item;
        }
    });

    if (!selectedItem) return;

    // Create inline properties panel
    const propertiesPanel = document.createElement('div');
    propertiesPanel.className = 'control-item-properties';
    propertiesPanel.id = 'inline-properties';

    const title = control.type.charAt(0).toUpperCase() + control.type.slice(1);

    propertiesPanel.innerHTML = `
        <div class="properties-inline-header">
            <h3 class="properties-inline-title">Edit ${title}</h3>
            <button class="btn-icon" id="close-properties-inline" title="Close">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <path d="M2 2l8 8M10 2l-8 8"/>
                </svg>
            </button>
        </div>
        ${createPropertiesForm(control)}
    `;

    // Insert after selected control item
    selectedItem.insertAdjacentElement('afterend', propertiesPanel);

    // Trigger reflow for animation
    propertiesPanel.offsetHeight;

    // Open with animation
    setTimeout(() => {
        propertiesPanel.classList.add('open');
    }, 10);

    // Event listeners for form
    const form = propertiesPanel.querySelector('.prop-form');
    form.querySelector('#save-btn').addEventListener('click', () => saveProperties(id));
    form.querySelector('#delete-btn').addEventListener('click', () => showDeleteConfirmation(id));
    propertiesPanel.querySelector('#close-properties-inline').addEventListener('click', closeProperties);

    // Scroll into view if needed
    setTimeout(() => {
        propertiesPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

function createPropertiesForm(control) {
    let formHTML = `<form class="prop-form">
        <div class="prop-group full-width">
            <label class="prop-label">Label</label>
            <input type="text" class="prop-input" id="prop-label" value="${control.label}" placeholder="Control label">
        </div>
    `;

    if (control.type === 'slider') {
        formHTML += `
        <div class="prop-group">
            <label class="prop-label">Channel</label>
            <input type="number" class="prop-input" id="prop-channel" value="${control.channel}" min="0">
        </div>
        <div class="prop-group">
            <label class="prop-label">Min Value</label>
            <input type="number" class="prop-input" id="prop-min" value="${control.min}">
        </div>
        <div class="prop-group">
            <label class="prop-label">Max Value</label>
            <input type="number" class="prop-input" id="prop-max" value="${control.max}">
        </div>
        <div class="prop-group">
            <label class="prop-label">Default</label>
            <input type="number" class="prop-input" id="prop-default" value="${control.default}">
        </div>
        `;
    } else if (control.type === 'color') {
        formHTML += `
        <div class="prop-group">
            <label class="prop-label">Default Color</label>
            <input type="color" class="prop-input" id="prop-default-color" value="${control.default}">
        </div>
        `;
    } else if (control.type === 'xy') {
        formHTML += `
        <div class="prop-group">
            <label class="prop-label">Default X (0-1)</label>
            <input type="number" class="prop-input" id="prop-default-x" value="${control.default.x}" min="0" max="1" step="0.01">
        </div>
        <div class="prop-group">
            <label class="prop-label">Default Y (0-1)</label>
            <input type="number" class="prop-input" id="prop-default-y" value="${control.default.y}" min="0" max="1" step="0.01">
        </div>
        `;
    } else if (control.type === 'button') {
        formHTML += `
        <div class="prop-group">
            <label class="prop-label">Default State</label>
            <select class="prop-input" id="prop-default-state">
                <option value="0" ${control.default === 0 ? 'selected' : ''}>OFF (0)</option>
                <option value="1" ${control.default === 1 ? 'selected' : ''}>ON (1)</option>
            </select>
        </div>
        `;
    }

    formHTML += `
        <div class="prop-actions">
            <button type="button" class="btn btn-success" id="save-btn">Save Changes</button>
            <button type="button" class="btn btn-danger" id="delete-btn">Delete</button>
        </div>
    </form>`;

    return formHTML;
}

function saveProperties(id) {
    const control = getCurrentControls().find(c => c.id === id);
    if (!control) return;

    // Get form values
    control.label = document.getElementById('prop-label').value;

    if (control.type === 'slider') {
        control.channel = parseInt(document.getElementById('prop-channel').value);
        control.min = parseFloat(document.getElementById('prop-min').value);
        control.max = parseFloat(document.getElementById('prop-max').value);
        control.default = parseFloat(document.getElementById('prop-default').value);
    } else if (control.type === 'color') {
        control.default = document.getElementById('prop-default-color').value;
    } else if (control.type === 'xy') {
        control.default.x = parseFloat(document.getElementById('prop-default-x').value);
        control.default.y = parseFloat(document.getElementById('prop-default-y').value);
    } else if (control.type === 'button') {
        control.default = parseInt(document.getElementById('prop-default-state').value);
    }

    saveToLocalStorage();
    renderControlsList();
    renderPreview();
    closeProperties();
}

function closeProperties() {
    const inlineProps = document.getElementById('inline-properties');
    if (inlineProps) {
        // Collapse animation
        inlineProps.classList.remove('open');

        // Remove from DOM after animation
        setTimeout(() => {
            if (inlineProps.parentNode) {
                inlineProps.remove();
            }
        }, 300);
    }

    state.selectedControlId = null;
    renderControlsList(); // Update selection visual
}

// ============================================================================
// LOCAL STORAGE
// ============================================================================

function saveToLocalStorage() {
    try {
        localStorage.setItem('td_ui_config', JSON.stringify(state.config));
    } catch (e) {
        console.error('Failed to save to localStorage:', e);
    }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem('td_ui_config');
        if (saved) {
            const loaded = JSON.parse(saved);
            // Migrate old format if needed
            const migrated = migrateOldConfig(loaded);

            // Validate and merge
            if (migrated.version && migrated.pages) {
                state.config = migrated;
                state.currentPageId = migrated.pages[0].id;

                // Update nextId based on all controls across all pages
                const allControls = migrated.pages.flatMap(p => p.controls);
                const maxId = Math.max(0, ...allControls.map(c => {
                    const match = c.id.match(/\d+$/);
                    return match ? parseInt(match[0]) : 0;
                }));
                state.nextId = maxId + 1;

                // Update nextPageId based on existing pages
                const maxPageId = Math.max(0, ...migrated.pages.map(p => {
                    const match = p.id.match(/\d+$/);
                    return match ? parseInt(match[0]) : 0;
                }));
                state.nextPageId = maxPageId + 1;
            }
        }
    } catch (e) {
        console.error('Failed to load from localStorage:', e);
    }
}

// ============================================================================
// JSON EXPORT/IMPORT
// ============================================================================

function downloadJSON() {
    const dataStr = JSON.stringify(state.config, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'td-ui-config.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function uploadJSON(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        try {
            const loaded = JSON.parse(event.target.result);
            // Migrate old format if needed
            const migrated = migrateOldConfig(loaded);

            if (validateConfig(migrated)) {
                state.config = migrated;
                state.currentPageId = migrated.pages[0].id;
                state.selectedControlId = null;
                saveToLocalStorage();
                renderPageTabs();
                renderControlsList();
                renderPreview();
                updateControlCount();
                closeProperties();
            } else {
                alert('Invalid configuration file format');
            }
        } catch (e) {
            alert('Failed to parse JSON file: ' + e.message);
        }
    };
    reader.readAsText(file);

    // Reset file input
    e.target.value = '';
}

function validateConfig(config) {
    // Support both old format (controls array) and new format (pages array)
    if (!config || !config.version) return false;

    // New format
    if (Array.isArray(config.pages)) {
        return config.pages.every(page =>
            page.id &&
            page.name &&
            Array.isArray(page.controls) &&
            page.controls.every(c => c.id && c.type && c.label && c.chop)
        );
    }

    // Old format (for backward compatibility during upload)
    if (Array.isArray(config.controls)) {
        return config.controls.every(c => c.id && c.type && c.label && c.chop);
    }

    return false;
}

// ============================================================================
// PAGE MANAGEMENT
// ============================================================================

function renderPageTabs() {
    const header = document.querySelector('.canvas-header');
    let tabsContainer = header.querySelector('.page-tabs');

    if (!tabsContainer) {
        tabsContainer = document.createElement('div');
        tabsContainer.className = 'page-tabs';
        header.insertBefore(tabsContainer, header.firstChild);
    }

    tabsContainer.innerHTML = '';

    // Render page tabs
    state.config.pages.forEach(page => {
        const tab = document.createElement('button');
        tab.className = 'page-tab';
        if (page.id === state.currentPageId) {
            tab.classList.add('active');
        }
        tab.textContent = page.name;
        tab.addEventListener('click', () => switchPage(page.id));
        tabsContainer.appendChild(tab);
    });

    // Add new page button
    const addBtn = document.createElement('button');
    addBtn.className = 'page-tab page-tab-add';
    addBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M6 1v10M1 6h10"/></svg>';
    addBtn.title = 'Add page';
    addBtn.addEventListener('click', addPage);
    tabsContainer.appendChild(addBtn);
}

function switchPage(pageId) {
    state.currentPageId = pageId;
    state.selectedControlId = null;
    closeProperties();
    renderPageTabs();
    renderControlsList();
    renderPreview();
    updateControlCount();
}

function addPage() {
    const pageId = `page${state.nextPageId}`;
    const pageName = `Page ${state.nextPageId}`;

    state.config.pages.push({
        id: pageId,
        name: pageName,
        controls: []
    });

    state.nextPageId++;
    state.currentPageId = pageId;

    saveToLocalStorage();
    renderPageTabs();
    renderControlsList();
    renderPreview();
    updateControlCount();
}

function deletePage(pageId) {
    if (state.config.pages.length <= 1) {
        alert('Cannot delete the last page');
        return;
    }

    const index = state.config.pages.findIndex(p => p.id === pageId);
    if (index === -1) return;

    state.config.pages.splice(index, 1);

    // Switch to first page if current page was deleted
    if (state.currentPageId === pageId) {
        state.currentPageId = state.config.pages[0].id;
    }

    state.selectedControlId = null;
    closeProperties();

    saveToLocalStorage();
    renderPageTabs();
    renderControlsList();
    renderPreview();
    updateControlCount();
}

// ============================================================================
// SERVER SAVE/LOAD (TouchDesigner Integration)
// ============================================================================

async function saveToServer() {
    try {
        // Step 1: Save config to TouchDesigner
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(state.config)
        });

        if (!response.ok) {
            const error = await response.json();
            alert(`✗ Failed to save to TouchDesigner:\n${error.error || 'Unknown error'}`);
            console.error('[Builder] Save error:', error);
            return;
        }

        const result = await response.json();
        console.log('[Builder] Saved to TouchDesigner:', result);

        // Step 2: Auto-deploy CHOPs
        console.log('[Builder] Deploying CHOPs...');
        const deployResponse = await fetch('/api/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (deployResponse.ok) {
            const deployResult = await deployResponse.json();
            console.log('[Builder] Deploy result:', deployResult);

            // Build success message
            let message = '✓ Configuration saved to TouchDesigner!\n\n';

            if (deployResult.success) {
                if (deployResult.chops.length > 0) {
                    // Count created vs updated
                    const created = deployResult.chops.filter(c => c.action === 'Created');
                    const updated = deployResult.chops.filter(c => c.action === 'Updated');

                    message += '✓ Deployment Results:\n';

                    if (created.length > 0) {
                        message += `\n  Created ${created.length} CHOP(s):\n`;
                        created.forEach(chop => {
                            message += `    • ${chop.name} (${chop.channels} channels)\n`;
                        });
                    }

                    if (updated.length > 0) {
                        message += `\n  Updated ${updated.length} CHOP(s):\n`;
                        updated.forEach(chop => {
                            message += `    • ${chop.name} (${chop.channels} channels)\n`;
                        });
                    }
                } else {
                    message += '✓ No CHOPs to deploy (pages have no controls)';
                }

                if (deployResult.warnings.length > 0) {
                    message += '\n⚠ Warnings:\n';
                    deployResult.warnings.forEach(warn => {
                        message += `  • ${warn}\n`;
                    });
                }
            } else {
                message += '✗ Deployment failed:\n';
                deployResult.errors.forEach(err => {
                    message += `  • ${err}\n`;
                });
            }

            alert(message);
        } else {
            // Deploy failed
            const deployError = await deployResponse.json();
            console.error('[Builder] Deploy error:', deployError);
            alert(`✓ Configuration saved to TouchDesigner!\n\n✗ But deployment failed:\n${deployError.error || 'Unknown error'}\n\nYou may need to deploy manually.`);
        }

    } catch (e) {
        console.error('[Builder] Server unavailable:', e);
        alert('✗ TouchDesigner server not available.\n\nMake sure:\n1. Web Server DAT is Active\n2. Callbacks are set up\n3. ui_config Text DAT exists\n4. deploy_chops Text DAT exists\n\nYour config is still saved in browser LocalStorage.');
    }
}

async function loadFromServer() {
    try {
        const response = await fetch('/api/config');

        if (response.ok) {
            const loaded = await response.json();
            const migrated = migrateOldConfig(loaded);

            if (validateConfig(migrated)) {
                state.config = migrated;
                state.currentPageId = migrated.pages[0].id;
                state.selectedControlId = null;

                // Also save to LocalStorage
                saveToLocalStorage();

                renderPageTabs();
                renderControlsList();
                renderPreview();
                updateControlCount();
                closeProperties();

                alert('✓ Configuration loaded from TouchDesigner!');
                console.log('[Builder] Loaded from TouchDesigner');
            } else {
                alert('✗ Invalid configuration format in TouchDesigner');
            }
        } else {
            const error = await response.json();
            alert(`✗ Failed to load from TouchDesigner:\n${error.error || 'Unknown error'}`);
        }
    } catch (e) {
        console.error('[Builder] Server unavailable:', e);
        alert('✗ TouchDesigner server not available.\n\nMake sure:\n1. Web Server DAT is Active\n2. Callbacks are set up\n3. ui_config Text DAT exists\n\nUsing browser LocalStorage instead.');
    }
}

// ============================================================================
// MODALS & CONFIRMATIONS
// ============================================================================

let modalAction = null;

function showClearConfirmation() {
    showModal(
        'Are you sure you want to clear all controls? This cannot be undone.',
        () => clearAll()
    );
}

function showDeleteConfirmation(id) {
    const control = getCurrentControls().find(c => c.id === id);
    if (!control) return;
    showModal(
        `Are you sure you want to delete "${control.label}"?`,
        () => deleteControl(id)
    );
}

function showModal(message, onConfirm) {
    document.getElementById('modal-message').textContent = message;
    document.getElementById('confirm-modal').classList.add('show');
    modalAction = onConfirm;
}

function hideModal() {
    document.getElementById('confirm-modal').classList.remove('show');
    modalAction = null;
}

function handleModalConfirm() {
    if (modalAction) {
        modalAction();
    }
    hideModal();
}

function clearAll() {
    // Clear all controls from current page
    const currentPage = getCurrentPage();
    if (currentPage) {
        currentPage.controls = [];
    }
    state.selectedControlId = null;
    saveToLocalStorage();
    renderControlsList();
    renderPreview();
    updateControlCount();
    closeProperties();
}
