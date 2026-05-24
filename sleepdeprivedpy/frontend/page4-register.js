import { db } from './firebase-config.js';
import { getAuth, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { serverTimestamp, setDoc, doc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

const auth = getAuth();

// EmailJS Initialization
if(typeof emailjs !== 'undefined') {
    emailjs.init({ publicKey: "EpKnSHJwaTPv9H-LO" });
}

document.addEventListener('DOMContentLoaded', () => {
    const regForm = document.getElementById('prototypeRegForm');
    const msgDiv = document.getElementById('registrationMessage');
    const submitBtn = document.getElementById('regSubmitBtn');

    // ID Formatter (Numbers only)
    const idInput = document.getElementById('regStudentId');
    if(idInput) {
        idInput.addEventListener('input', function() {
            this.value = this.value.replace(/[a-zA-Z]/g, '');
        });
    }

    if (!regForm) return;

    regForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Reset
        msgDiv.className = 'alert-box alert-info';
        msgDiv.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing registration...';
        msgDiv.classList.remove('d-none');
        
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';

        // Gather Data
        const fullName = document.getElementById('regFullName').value.trim();
        const department = document.getElementById('regDepartment').value;
        const studentId = document.getElementById('regStudentId').value.trim();
        const schoolEmail = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        const guardianName = document.getElementById('regGuardianName').value.trim();
        const guardianEmail = document.getElementById('regGuardianEmail').value.trim();
        const guardianContact = document.getElementById('regGuardianContact').value.trim();
        
        const smsConsent = document.getElementById('regSmsConsent').checked;
        const dataConsent = document.getElementById('regDataConsent').checked;

        // Helper to show errors
        const showError = (text) => {
            msgDiv.className = 'alert-box alert-error';
            msgDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${text}`;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            msgDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };

        // 1. Password Match
        if (password !== confirmPassword) {
            return showError('Passwords do not match.');
        }

        // 2. Password Policy
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/;
        if (!passwordRegex.test(password)) {
            return showError('Password must contain 8+ chars, 1 uppercase, 1 lowercase, 1 number, and 1 symbol.');
        }

        // 3. Phone Validation
        const phoneReg = /^9\d{9}$/;
        if (!phoneReg.test(guardianContact)) {
            return showError('Invalid contact number. Must be 10 digits starting with 9.');
        }

        const formattedContact = "0" + guardianContact;

        try {
            // Create Firebase Auth User
            const userCredential = await createUserWithEmailAndPassword(auth, schoolEmail, password);
            const user = userCredential.user;

            // Save to Firestore
            await setDoc(doc(db, "students", user.uid), {
                fullName: fullName,
                department: department,
                studentId: studentId,
                schoolEmail: schoolEmail,
                guardianName: guardianName,
                guardianEmail: guardianEmail,
                guardianContact: formattedContact,
                smsConsent: smsConsent,
                dataConsent: dataConsent,
                uid: user.uid,
                createdAt: serverTimestamp(),
                status: "active"
            });

            // Send Welcome Email
            if(typeof emailjs !== 'undefined') {
                emailjs.send('service_xpxlkw5', 'template_b03xk6x', {
                    user_name: fullName,       
                    user_email: schoolEmail    
                }).catch(err => console.error("Email failed:", err));
            }

            // Success UI
            msgDiv.className = 'alert-box alert-success';
            msgDiv.innerHTML = '<i class="fa-solid fa-circle-check"></i> Registration successful! Routing to login...';
            regForm.reset();

            // Redirect back to Landing Page after 2 seconds
            setTimeout(() => {
                goToPage('page0.html'); // Assuming your router uses this function
            }, 2000);

        } catch (error) {
            console.error(error);
            let errMsg = error.message;
            if (error.code === 'auth/email-already-in-use') errMsg = "Email already registered.";
            if (error.code === 'auth/weak-password') errMsg = "Password is too weak.";
            
            showError(`Registration failed: ${errMsg}`);
        }
    });
});