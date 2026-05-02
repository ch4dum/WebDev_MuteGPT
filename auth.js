// auth.js

let GOOGLE_CLIENT_ID = null;

// ดึง Client ID จาก Backend เมื่อหน้าเว็บโหลด
async function fetchConfig() {
    try {
        const res = await fetch('http://localhost:3000/api/config');
        if (res.ok) {
            const data = await res.json();
            GOOGLE_CLIENT_ID = data.clientId;
        }
    } catch (err) {
        console.error("Failed to load Google Client ID:", err);
    }
}
fetchConfig();

function handleGoogleLogin() {
    if (!GOOGLE_CLIENT_ID) {
        alert("ระบบยังไม่พร้อมใช้งาน (ไม่สามารถโหลดตั้งค่าจากเซิร์ฟเวอร์ได้) กรุณาลองใหม่ในภายหลัง");
        return;
    }

    try {
        const client = google.accounts.oauth2.initCodeClient({
            client_id: GOOGLE_CLIENT_ID,
            scope: 'openid profile email',
            ux_mode: 'popup',
            callback: (response) => {
                if (response.code) {
                    console.log("Authorization Code:", response.code);
                    // เรียกฟังก์ชันส่งข้อมูลไป Backend
                    sendToBackend(response.code);
                }
            },
        });
        client.requestCode();
    } catch (err) {
        console.error("Google Login Error:", err);
        alert("ไม่สามารถเปิดระบบ Google Login ได้ในขณะนี้");
    }
}

async function sendToBackend(authCode) {
    try {
        const response = await fetch('http://localhost:3000/api/google-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: authCode })
        });

        const data = await response.json();

        if (response.ok) {
            // 1. เก็บข้อมูลลง localStorage
            localStorage.setItem('user', JSON.stringify(data.user));

            // 2. สร้างแถบแจ้งเตือน Toast แทนการใช้ alert
            showToast("Login Successful! Redirecting...");

            // 3. รอ 2 วินาทีเพื่อให้คนเห็น Toast แล้วค่อยเด้งไปหน้าถัดไป
            setTimeout(() => {
                window.location.href = 'user_key_data.html';
            }, 1000);

        } else {
            console.error("Backend Error:", data.message);
        }
    } catch (error) {
        console.error("Network Error:", error);
    }
}

// ฟังก์ชันสำหรับสร้างและแสดง Toast
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-success';
    toast.innerHTML = `<i data-lucide="check-circle"></i> <span>${message}</span>`;
    document.body.appendChild(toast);
    
    // สั่งให้ Lucide สร้างไอคอนใน Toast ใหม่
    if (window.lucide) lucide.createIcons();

    // ดีเลย์นิดนึงเพื่อให้ Transition ทำงาน (ให้เด้งลงมา)
    setTimeout(() => toast.classList.add('show'), 100);
}