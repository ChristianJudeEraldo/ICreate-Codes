// Page 1 ---------------------------------------------------
function onStartScan() {
    const input = document.getElementById('student-id-display') || document.querySelector('.student-id-display');
    const studentId = input ? String(input.value || '') : '';

    // 1. Validate Student ID
    if (!studentId) {
        alert("Please enter your Student ID.");
        return;
    }

    // 2. Validate Sleep Hours
    const sleepInput = document.getElementById('sleepHoursInput');
    const sleepHours = sleepInput ? sleepInput.value.trim() : '';

    if (!sleepHours) {
        alert("Please enter how many hours of sleep you got last night.");
        return;
    }

    if (parseInt(sleepHours) > 24) {
        alert("Please enter a valid number of hours (0-24).");
        return;
    }

    // 3. Send BOTH pieces of data to your Python backend!
    eel.start_scan(studentId, sleepHours);
}

// Page 2 ---------------------------------------------------
function onScanNextStudent() {
    eel.scan_next();
}

function setupPage1Keypad() {
    const idInput = document.getElementById('student-id-display');
    const sleepInput = document.getElementById('sleepHoursInput');
    const keypad = document.querySelector('.keypad-grid');
    
    if (!keypad) return;

    // Track which input is currently active (Default to Student ID)
    let activeInput = idInput;

    // Listen for when the user taps either input box
    if (idInput) {
        idInput.addEventListener('focus', () => { activeInput = idInput; });
    }
    if (sleepInput) {
        sleepInput.addEventListener('focus', () => { activeInput = sleepInput; });
    }

    const focusInput = () => {
        if (!activeInput) return;
        try {
            activeInput.focus({ preventScroll: true });
        } catch {
            activeInput.focus();
        }
    };

    keypad.addEventListener('click', (e) => {
        const btn = e.target && e.target.closest ? e.target.closest('button') : null;
        if (!btn || !keypad.contains(btn) || !activeInput) return;

        const action = btn.getAttribute('data-action');
        if (action === 'backspace') {
            activeInput.value = activeInput.value.slice(0, -1);
            focusInput();
            return;
        }

        const key = btn.getAttribute('data-key');
        if (key != null && key !== '') {
            // Prevent typing past the max length (e.g., 2 characters for sleep hours)
            if (activeInput.maxLength > 0 && activeInput.value.length >= activeInput.maxLength) {
                focusInput();
                return; 
            }
            activeInput.value = activeInput.value + key;
            focusInput();
        }
    });

    // Start with the Student ID focused
    if (idInput) focusInput();
}

// Setup function to block letters in the Sleep Hours input
function setupSleepHoursInput() {
    const sleepInput = document.getElementById('sleepHoursInput');
    if (sleepInput) {
        sleepInput.addEventListener('input', function() {
            // Instantly deletes anything that isn't a number 0-9
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
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
    document.addEventListener('DOMContentLoaded', () => {
        setupPage1Keypad();
        setupSleepHoursInput(); // Activates the number block
    });
} else {
    setupPage1Keypad();
    setupSleepHoursInput(); // Activates the number block
}