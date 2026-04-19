// Page 1 ---------------------------------------------------
function onStartScan() {
    const input = document.getElementById('student-id-display') || document.querySelector('.student-id-display');
    const studentId = input ? String(input.value || '') : '';
    eel.start_scan(studentId);
}

// Page 2 ---------------------------------------------------
function onScanNextStudent() {
    eel.scan_next();
}

function setupPage1Keypad() {
    const input = document.getElementById('student-id-display') || document.querySelector('.student-id-display');
    const keypad = document.querySelector('.keypad-grid');
    if (!input || !keypad) return;

    const focusInput = () => {
        try {
            input.focus({ preventScroll: true });
        } catch {
            input.focus();
        }
    };

    keypad.addEventListener('click', (e) => {
        const btn = e.target && e.target.closest ? e.target.closest('button') : null;
        if (!btn || !keypad.contains(btn)) return;

        const action = btn.getAttribute('data-action');
        if (action === 'backspace') {
            input.value = input.value.slice(0, -1);
            focusInput();
            return;
        }

        const key = btn.getAttribute('data-key');
        if (key != null && key !== '') {
            input.value = input.value + key;
            focusInput();
        }
    });

    focusInput();
}

// -----------------------
// App / Global Buttons
// -----------------------

function onSkipButtonClicked() {
    if (typeof eel !== 'undefined' && eel.handle_skip_button) {
        eel.handle_skip_button();
    }
}

function onShutdownButtonClicked() {
    if (typeof eel !== 'undefined' && eel.shutdown_pi) {
        eel.shutdown_pi();
    }
}

function onMinimizeButtonClicked() {
    if (typeof eel !== 'undefined' && eel.quit_app) {
        eel.quit_app();
    }
}

// Initialize any non-inline wiring
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupPage1Keypad);
} else {
    setupPage1Keypad();
}