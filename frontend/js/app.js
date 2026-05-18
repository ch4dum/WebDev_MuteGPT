// Initialize Lucide icons
if (window.lucide) {
  lucide.createIcons();
}

function createDonateWidget() {
  if (document.getElementById('donate-widget')) return;

  const widget = document.createElement('aside');
  widget.id = 'donate-widget';
  widget.className = 'donate-widget';
  widget.setAttribute('aria-label', 'สนับสนุน MuteGPT');
  widget.innerHTML = `
    <div class="donate-widget-text">
      <span class="donate-widget-title">ชอบ MuteGPT ใช่ไหม?</span>
      <span class="donate-widget-subtitle">ถ้า MuteGPT ช่วยคุณได้ ฝากสนับสนุนการพัฒนาต่อได้นะ</span>
    </div>
    <a class="donate-widget-link" href="https://tipme.in.th/mute-gpt" target="_blank" rel="noopener">
      <i data-lucide="heart-handshake"></i>
      <span>Donate</span>
    </a>
  `;
  document.body.appendChild(widget);

  if (window.lucide) {
    lucide.createIcons();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createDonateWidget);
} else {
  createDonateWidget();
}

// --- Navbar scroll effect ---
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// --- Auth Modal (only on pages with the modal) ---
const authModal = document.getElementById('auth-modal');
if (authModal) {
  let authMode = 'login';

  const modalBackdrop = document.getElementById('modal-backdrop');
  const btnOpenAuth = document.getElementById('btn-open-auth');
  const btnHeroCta = document.getElementById('btn-hero-cta');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnToggleMode = document.getElementById('btn-toggle-mode');
  const modalTitle = document.getElementById('modal-title');
  const modalSubtitle = document.getElementById('modal-subtitle');
  const modalToggle = document.getElementById('modal-toggle');
  const nameField = document.getElementById('name-field');
  const btnAuthSubmit = document.getElementById('btn-auth-submit');

  /**
   * Opens the authentication modal.
   */
  function openModal() {
    authModal.classList.add('active');
    document.body.classList.add('no-scroll');
  }

  /**
   * Closes the authentication modal and resets to login mode.
   */
  function closeModal() {
    authModal.classList.remove('active');
    document.body.classList.remove('no-scroll');
    setTimeout(() => {
      authMode = 'login';
      updateAuthUI();
    }, 300);
  }

  /**
   * Updates the Modal UI elements based on the current authMode (login/register).
   */
  function updateAuthUI() {
    if (authMode === 'login') {
      modalTitle.textContent = 'เข้าสู่ระบบ MuteGPT';
      modalSubtitle.textContent = 'เชื่อมต่อจิตวิญญาณและรับคำทำนาย';
      nameField.classList.add('hidden');
      btnAuthSubmit.textContent = 'เข้าสู่ระบบ';
      modalToggle.innerHTML = 'ยังไม่มีบัญชีใช่หรือไม่? <button id="btn-toggle-mode">สร้างบัญชีใหม่</button>';
    } else {
      modalTitle.textContent = 'เริ่มต้นการทำนายของคุณ';
      modalSubtitle.textContent = 'สร้างบัญชีเพื่อบันทึกโปรไฟล์ดวงดาวของคุณ';
      nameField.classList.remove('hidden');
      btnAuthSubmit.textContent = 'สมัครสมาชิก';
      modalToggle.innerHTML = 'มีบัญชีอยู่แล้ว? <button id="btn-toggle-mode">เข้าสู่ระบบ</button>';
    }

    // Re-bind toggle button event listener
    const toggleBtn = document.getElementById('btn-toggle-mode');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        authMode = authMode === 'login' ? 'register' : 'login';
        updateAuthUI();
      });
    }
  }

  // Bind Event listeners
  if (btnOpenAuth) btnOpenAuth.addEventListener('click', openModal);
  if (btnHeroCta) btnHeroCta.addEventListener('click', openModal);
  if (btnCloseModal) btnCloseModal.addEventListener('click', closeModal);
  if (modalBackdrop) modalBackdrop.addEventListener('click', closeModal);
  if (btnToggleMode) {
    btnToggleMode.addEventListener('click', () => {
      authMode = authMode === 'login' ? 'register' : 'login';
      updateAuthUI();
    });
  }
}

// --- Scroll-triggered animations ---
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.animationPlayState = 'running';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.animate-fade-in-up').forEach(el => {
  el.style.animationPlayState = 'paused';
  observer.observe(el);
});

// Immediately play hero animations
document.querySelectorAll('.hero .animate-fade-in-up').forEach(el => {
  el.style.animationPlayState = 'running';
});
