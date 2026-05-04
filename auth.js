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
        showErrorToast("ระบบยังไม่พร้อมใช้งาน กรุณารอสักครู่");
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

            // สมัครสำเร็จ → ทำการ Sign Out ทันทีเพื่อบังคับให้ผู้ใช้ต้อง Login เองใหม่
            await supabaseClient.auth.signOut();

            showToast("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ");
            
            // เปลี่ยนหน้าต่างกลับไปเป็นโหมด Login
            setTimeout(() => {
                const toggleBtn = document.getElementById('btn-toggle-mode');
                if (toggleBtn) toggleBtn.click();
                
                // เคลียร์ช่องรหัสผ่าน และชื่อ
                document.querySelector('input[type="password"]').value = '';
                const nameInput = document.querySelector('#name-field input');
                if (nameInput) nameInput.value = '';
            }, 1500);
        } else {
            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email,
                password
            });
            if (error) throw error;

            // Login สำเร็จ → แสดง toast แล้ว redirect
            localStorage.setItem('user', JSON.stringify(data.user));
            showToast("เข้าสู่ระบบสำเร็จ!");
            setTimeout(() => {
                window.location.href = 'separator.html';
            }, 1500);
        }
    } catch (err) {
        console.error("Auth Error:", err.message);
        showErrorToast(err.message || "เกิดข้อผิดพลาด กรุณาลองอีกครั้ง");
    }
}

/**
 * Handles Google Login via Supabase OAuth.
 */
async function handleGoogleLogin() {
    if (!supabaseClient) {
        showErrorToast("ระบบยังไม่พร้อมใช้งาน กรุณารอสักครู่");
        return;
    }

    const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin + '/separator.html'
        }
    });

    if (error) {
        console.error("Google Login Error:", error.message);
        showErrorToast("ไม่สามารถเข้าสู่ระบบด้วย Google ได้");
    }
}

/**
 * Handles Logout.
 */
async function handleLogout() {
    if (supabaseClient) {
        await supabaseClient.auth.signOut();
        window.location.href = 'index.html';
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

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

/**
 * Creates and displays an error Toast notification.
 * @param {string} message - The error message to display.
 */
function showErrorToast(message) {
    // Remove existing error toasts
    document.querySelectorAll('.toast-auth-error').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = 'toast-auth-error';
    toast.innerHTML = `<i data-lucide="alert-circle"></i> <span>${message}</span>`;
    document.body.appendChild(toast);

    if (window.lucide) lucide.createIcons();

    setTimeout(() => toast.classList.add('show'), 100);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Bind event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('auth-form');
    if (authForm) {
        authForm.addEventListener('submit', handleEmailAuth);
    }

    // รอให้ supabaseClient พร้อมใช้งานแล้วจับ Event การ Login
    const checkReady = setInterval(() => {
        if (supabaseClient) {
            clearInterval(checkReady);
            supabaseClient.auth.onAuthStateChange((event, session) => {
                // เช็คสถานะเมื่อ Login สำเร็จ หรือโหลดหน้าเว็บมาเจอ Session
                if (event === 'INITIAL_SESSION' || event === 'SIGNED_IN') {
                    if (session && session.user) {
                        checkUserProfile(session.user);
                    }
                }
            });
        }
    }, 100);
});

/**
 * ตรวจสอบสถานะโปรไฟล์ของ User และเลือกหน้าที่จะส่งไป
 */
async function checkUserProfile(user) {
    if (!user) return;

    try {
        const { data: profile, error } = await supabaseClient
            .from('profiles')
            .select('*')
            .eq('id', user.id)
            .single();

        if (error && error.code !== 'PGRST116') {
            throw error;
        }

        const isProfileComplete = profile && profile.full_name && profile.nickname && profile.phone_last4 &&
            profile.birth_date && profile.birth_time && profile.gender;
        const currentPath = window.location.pathname;
        const isOnProfilePage = currentPath.includes('user_key_data.html');
        const isLoadingPage = currentPath.includes('separator.html') || currentPath.includes('index.html') || currentPath.endsWith('/');

        if (!isProfileComplete) {
            // ไม่เคยกรอก หรือ กรอกไม่ครบ -> ต้องไป user_key_data.html
            if (!isOnProfilePage) {
                window.location.href = 'user_key_data.html';
            }
        } else {
            // กรอกครบแล้ว -> ไป main.html
            // เพื่อไม่ให้รบกวนถ้าผู้ใช้จงใจเข้าหน้า user_key_data.html เพื่อแก้ข้อมูล
            if (isLoadingPage) {
                window.location.href = 'main.html';
            }
        }
    } catch (err) {
        console.error("Error checking profile:", err);
    }
}