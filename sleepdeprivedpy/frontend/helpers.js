eel.expose(refreshPage);
function refreshPage() {
    location.reload();
}

eel.expose(updateInnerText);
function updateInnerText(elementId, newText) {
    const el = document.getElementById(elementId);
    if (el) el.innerText = newText;
}

eel.expose(updateFontColor);
function updateFontColor(elementId, hex) {
    const el = document.getElementById(elementId);
    if (el) el.style.color = hex;
}

eel.expose(updateFontWeight);
function updateFontWeight(elementId, weight) {
    const el = document.getElementById(elementId);
    if (el) el.style.fontWeight = weight;
}

eel.expose(updateBackgroundColor);
function updateBackgroundColor(elementId, hex) {
    const el = document.getElementById(elementId);
    if (el) el.style.backgroundColor = hex;
}

// -----------------------
// Generic Attribute Update
// -----------------------

eel.expose(updateElementByAttribute);
function updateElementByAttribute(elementId, attributeName, value) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const attr = String(attributeName || '').trim();
    if (!attr) return;
    // Special case: set textContent or innerHTML as properties
    if (attr === 'textContent' || attr === 'innerHTML') {
        el[attr] = String(value ?? '');
        return;
    }
    // Common mistake: passing the element id as the attribute name.
    // If this happens for an <img>, treat it as setting the src.
    if (el.tagName === 'IMG' && (attr === elementId || attr === el.id)) {
        el.setAttribute('src', String(value ?? ''));
        return;
    }
    // Convenience: if setting src, always cache-bust.
    if (attr.toLowerCase() === 'src') {
        const src = String(value ?? '');
        if (src.startsWith('data:')) {
            el.setAttribute('src', src);
            return;
        }
        const busted = src + (src.includes('?') ? '&' : '?') + 'r=' + Date.now();
        el.setAttribute('src', busted);
        return;
    }
    el.setAttribute(attr, String(value ?? ''));
}

// -----------------------
// Class Management
// -----------------------

eel.expose(updateClass);
function updateClass(elementId, classList) {
    const el = document.getElementById(elementId);
    if (el) el.className = classList;
}

eel.expose(addClass);
function addClass(elementId, className) {
    try {
        const el = document.getElementById(elementId);
        if (el) el.classList.add(className);
    } catch (err) {
        console.warn(`Element '${elementId}' not found for addClass`);
    }
}

eel.expose(removeClass);
function removeClass(elementId, className) {
    try {
        const el = document.getElementById(elementId);
        if (el) el.classList.remove(className);
    } catch (err) {
        console.warn(`Element '${elementId}' not found for removeClass`);
    }
}

// -----------------------
// Navigation
// -----------------------

eel.expose(goToPage);
function goToPage(url) {
    // Only hide elements whose id is exactly 'page1', 'page2', etc.
    const pageId = String(url || '')
        .trim()
        .replace(/^#/, '')
        .replace(/\.html$/i, '');

    // Hide all elements whose id matches /^page\d+$/
    const pages = document.querySelectorAll('[id^="page"]');
    pages.forEach((el) => {
        if (/^page\d+$/.test(el.id)) {
            el.classList.add('invisible');
            el.style.display = "none";
        }
    });

    const target = document.getElementById(pageId);
    if (target) {
        target.classList.remove('invisible');
        target.style.display = "block";
        window.location.hash = pageId;
        return;
    }
    window.location.href = url;
}

// -----------------------
// Element Visibility
// -----------------------

eel.expose(showElement);
function showElement(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.classList.remove('invisible');
    el.style.display = "block";
}

eel.expose(hideElement);
function hideElement(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.classList.add('invisible');
    el.style.display = "none";
}

// -----------------------
// Skip Button
// -----------------------

// -----------------------
// Image Src Update
// -----------------------

eel.expose(updateImageSrc);
function updateImageSrc(elementId, newSrc) {
    const el = document.getElementById(elementId);
    if (el && el.tagName === 'IMG') {
        const src = String(newSrc || '');

        // For base64 video frames (data URLs), don't append query params.
        if (src.startsWith('data:')) {
            el.src = src;
            return;
        }

        // Append a unique query parameter to prevent caching
        const uniqueSrc = src + (src.includes('?') ? '&' : '?') + 'v=' + Date.now();
        el.src = uniqueSrc;
    }
}

// -----------------------
// Shutdown Button
// -----------------------

// -----------------------
// Student ID Input Helpers
// -----------------------

eel.expose(getInput);
function getInput(inputId) {
    const input = document.getElementById(inputId);
    return input ? input.value : '';
}

eel.expose(setInput);
function setInput(inputId, value) {
    const input = document.getElementById(inputId);
    if (input) input.value = value;
}

// -----------------------
// Dialog / Modal Helper
// -----------------------

function _ensureDialogStyles() {
    if (document.getElementById('sd-dialog-styles')) return;
    const style = document.createElement('style');
    style.id = 'sd-dialog-styles';
    style.textContent = `
.sd-dialog-overlay{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:9999;}
.sd-dialog{position:fixed;top:50vh;left:50vw;transform:translate(-50%,-50%);background:#fff;border:1px solid #ddd;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,.2);z-index:10000;min-width:420px;max-width:560px;padding:18px 22px;text-align:center;}
.sd-dialog .sd-dialog-x{position:absolute;top:10px;right:12px;cursor:pointer;user-select:none;}
.sd-dialog .sd-dialog-header{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:10px;}
.sd-dialog .sd-dialog-icon{font-size:26px;line-height:1;}
.sd-dialog .sd-dialog-title{margin:0;font-size:1.15rem;}
.sd-dialog .sd-dialog-message{margin:0 0 14px 0;white-space:pre-wrap;}
.sd-dialog .sd-dialog-buttons{display:flex;flex-direction:column;gap:8px;}
.sd-dialog .sd-dialog-btn{border:0;border-radius:999px;color:#fff;padding:10px 14px;font-size:1rem;width:100%;cursor:pointer;}
`;
    document.head.appendChild(style);
}

function _dialogIconAndColor(type) {
    const t = String(type || 'info').toLowerCase();
    if (t === 'warning') return { icon: '⚠', color: '#f0ad4e' };
    if (t === 'error') return { icon: '⛔', color: '#d9534f' };
    return { icon: 'ℹ', color: '#06949b' };
}

function _removeExistingDialog() {
    const existing = document.getElementById('sd-dialog-container');
    if (existing) existing.remove();
}

eel.expose(openDialog);
function openDialog(header, message, buttons, options) {
    _ensureDialogStyles();
    _removeExistingDialog();

    const opts = options || {};
    const type = opts.type || 'info';
    const outsideClickClose = !!opts.outsideClickClose;
    const autoCloseMs = Number(opts.autoCloseMs || 0);

    const { icon, color } = _dialogIconAndColor(type);

    const container = document.createElement('div');
    container.id = 'sd-dialog-container';

    let overlay = null;
    if (outsideClickClose) {
        overlay = document.createElement('div');
        overlay.className = 'sd-dialog-overlay';
        overlay.addEventListener('click', () => close());
        container.appendChild(overlay);
    }

    const dialog = document.createElement('div');
    dialog.className = 'sd-dialog';

    const x = document.createElement('div');
    x.className = 'sd-dialog-x';
    x.textContent = '✖';
    x.addEventListener('click', () => close());
    dialog.appendChild(x);

    const headerRow = document.createElement('div');
    headerRow.className = 'sd-dialog-header';

    const iconEl = document.createElement('div');
    iconEl.className = 'sd-dialog-icon';
    iconEl.textContent = icon;
    iconEl.style.color = color;

    const title = document.createElement('h3');
    title.className = 'sd-dialog-title';
    title.textContent = String(header ?? '');

    headerRow.appendChild(iconEl);
    headerRow.appendChild(title);
    dialog.appendChild(headerRow);

    const msg = document.createElement('p');
    msg.className = 'sd-dialog-message';
    msg.textContent = String(message ?? '');
    dialog.appendChild(msg);

    const btnWrap = document.createElement('div');
    btnWrap.className = 'sd-dialog-buttons';

    const btns = Array.isArray(buttons) ? buttons : [];
    if (btns.length === 0) {
        const b = document.createElement('button');
        b.className = 'sd-dialog-btn';
        b.textContent = 'Dismiss';
        b.style.backgroundColor = '#007bff';
        b.addEventListener('click', () => close());
        btnWrap.appendChild(b);
    } else {
        btns.forEach((btn) => {
            const b = document.createElement('button');
            b.className = 'sd-dialog-btn';
            b.textContent = String(btn && btn.text ? btn.text : 'OK');
            b.style.backgroundColor = (btn && btn.backgroundColor) ? String(btn.backgroundColor) : '#550000';
            b.addEventListener('click', () => {
                try {
                    if (btn && typeof btn.functionName === 'string' && btn.functionName) {
                        const fn = window[btn.functionName];
                        if (typeof fn === 'function') fn();
                    }
                } finally {
                    close();
                }
            });
            btnWrap.appendChild(b);
        });
    }

    dialog.appendChild(btnWrap);
    container.appendChild(dialog);
    document.body.appendChild(container);

    let timer = null;
    if (autoCloseMs > 0 && Number.isFinite(autoCloseMs)) {
        timer = window.setTimeout(() => close(), autoCloseMs);
    }

    function close() {
        try {
            if (timer) window.clearTimeout(timer);
        } catch (e) {}
        _removeExistingDialog();
    }
}

eel.expose(openInfoDialog);
function openInfoDialog(header, message, buttons, options) {
    openDialog(header, message, buttons, Object.assign({}, options || {}, { type: 'info' }));
}

eel.expose(openWarningDialog);
function openWarningDialog(header, message, buttons, options) {
    openDialog(header, message, buttons, Object.assign({}, options || {}, { type: 'warning' }));
}

eel.expose(openErrorDialog);
function openErrorDialog(header, message, buttons, options) {
    openDialog(header, message, buttons, Object.assign({}, options || {}, { type: 'error' }));
}