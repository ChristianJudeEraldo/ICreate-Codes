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
// -----------------------
// Network Status Indicator
// -----------------------
function setupNetworkIndicator() {
    // Create the visual badge
    const badge = document.createElement('div');
    badge.id = 'network-status-badge';
    document.body.appendChild(badge);

    // visual badge styling 
    Object.assign(badge.style, {
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        padding: '8px 16px',
        borderRadius: '20px',
        fontSize: '0.85rem',
        fontWeight: '700',
        color: 'white',
        zIndex: '9999',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        transition: 'all 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontFamily: "'Segoe UI', sans-serif"
    });

    // changes colors based on internet status
    function updateStatus() {
        if (navigator.onLine) {
            badge.style.backgroundColor = '#10b981'; // Premium Green
            badge.innerHTML = '<i class="fa-solid fa-wifi"></i> System Online';
        } else {
            badge.style.backgroundColor = '#8c0001'; // LPU Red for Offline Warning
            badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Offline Mode';
        }
    }

    // Listener for changes in network status
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);

    // set the initial status
    updateStatus();
}

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
            setupNetworkIndicator(); // Turns on the Wi-Fi tracker
    });
} else {
    setupPage1Keypad();
    setupSleepHoursInput(); // Activates the number block
    setupNetworkIndicator(); // Turns on the Wi-Fi tracker
}