// auth.js

let GOOGLE_CLIENT_ID = null;
let supabaseClient = null;

/**
 * Fetch configuration from the backend on page load.
 * Initializes Supabase client with the retrieved URL and Key.
 */
async function fetchConfig() {
    try {
        const res = await fetch('http://localhost:3000/api/config');
        if (res.ok) {
            const data = await res.json();
            GOOGLE_CLIENT_ID = data.clientId;
            
            // Initialize Supabase Client
            if (data.supabaseUrl && data.supabaseKey) {
                // @ts-ignore
                supabaseClient = supabase.createClient(data.supabaseUrl, data.supabaseKey);
                console.log("Supabase initialized");
            }
        }
    } catch (err) {
        console.error("Failed to load Config:", err);
    }
}
fetchConfig();

/**
 * Handles Email/Password Authentication (Sign Up or Sign In).
 * Detects mode based on the visibility of the name field.
 */
async function handleEmailAuth(event) {
    event.preventDefault();
    if (!supabaseClient) {
        alert("ระบบยังไม่พร้อมใช้งาน (Supabase Not Initialized)");
        return;
    }

    const email = document.querySelector('input[type="email"]').value;
    const password = document.querySelector('input[type="password"]').value;
    const nameField = document.getElementById('name-field');
    const isRegister = !nameField.classList.contains('hidden');

    try {
        if (isRegister) {
            const fullName = nameField.querySelector('input').value;
            const { data, error } = await supabaseClient.auth.signUp({
                email,
                password,
                options: {
                    data: { full_name: fullName }
                }
            });
            if (error) throw error;
            alert("สมัครสมาชิกสำเร็จ! กรุณาตรวจสอบอีเมลเพื่อยืนยันตัวตน (ถ้าตั้งค่าไว้)");
        } else {
            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email,
                password
            });
            if (error) throw error;
            
            // Login success
            localStorage.setItem('user', JSON.stringify(data.user));
            showToast("Login Successful!");
            setTimeout(() => {
                window.location.href = 'user_key_data.html';
            }, 1000);
        }
    } catch (err) {
        console.error("Auth Error:", err.message);
        alert("เกิดข้อผิดพลาด: " + err.message);
    }
}

/**
 * Handles Google Login via Supabase OAuth.
 */
async function handleGoogleLogin() {
    if (!supabaseClient) {
        alert("ระบบยังไม่พร้อมใช้งาน");
        return;
    }

    const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin + '/user_key_data.html'
        }
    });

    if (error) {
        console.error("Google Login Error:", error.message);
        alert("ไม่สามารถเข้าสู่ระบบด้วย Google ได้: " + error.message);
    }
}

/**
 * Creates and displays a success Toast notification.
 * @param {string} message - The message to display.
 */
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-success';
    toast.innerHTML = `<i data-lucide="check-circle"></i> <span>${message}</span>`;
    document.body.appendChild(toast);
    
    // Refresh Lucide icons for the new Toast
    if (window.lucide) lucide.createIcons();

    // Trigger transition delay
    setTimeout(() => toast.classList.add('show'), 100);
}

// Bind event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('auth-form');
    if (authForm) {
        authForm.addEventListener('submit', handleEmailAuth);
    }
});