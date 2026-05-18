// Initialize Lucide icons
if (window.lucide) {
  lucide.createIcons();
}

function createDonateWidget() {
  if (document.getElementById('donate-widget')) return;
  injectDonateWidgetStyles();

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

function injectDonateWidgetStyles() {
  if (document.getElementById('donate-widget-styles')) return;

  const style = document.createElement('style');
  style.id = 'donate-widget-styles';
  style.textContent = `
    .donate-widget {
      position: fixed;
      left: max(1rem, env(safe-area-inset-left));
      bottom: max(1rem, env(safe-area-inset-bottom));
      z-index: 2147483000;

      display: flex;
      align-items: center;
      gap: 0.75rem;

      width: 3.8rem;
      min-height: 3.4rem;
      padding: 0.45rem;

      overflow: hidden;
      border-radius: 999px;
      border: 1px solid rgba(251, 191, 36, 0.22);
      background:
        linear-gradient(135deg, rgba(24, 10, 42, 0.95), rgba(46, 12, 56, 0.92));
      box-shadow:
        0 14px 35px rgba(0, 0, 0, 0.28),
        0 0 0 1px rgba(255, 255, 255, 0.03) inset,
        0 0 20px rgba(236, 72, 153, 0.10);
      backdrop-filter: blur(14px);
      font-family: 'Prompt', sans-serif;

      transition:
        width 0.28s ease,
        padding 0.28s ease,
        border-radius 0.28s ease,
        transform 0.2s ease,
        box-shadow 0.25s ease;
    }

    .donate-widget::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: linear-gradient(
        135deg,
        rgba(245, 158, 11, 0.10),
        rgba(236, 72, 153, 0.08)
      );
      pointer-events: none;
    }

    .donate-widget:hover,
    .donate-widget:focus-within {
      width: min(390px, calc(100vw - 2rem));
      padding: 0.75rem;
      border-radius: 1.1rem;
      transform: translateY(-2px);
      box-shadow:
        0 20px 45px rgba(0, 0, 0, 0.32),
        0 0 30px rgba(236, 72, 153, 0.16);
    }

    .donate-widget-text {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 0.12rem;

      opacity: 0;
      transform: translateX(-8px);
      pointer-events: none;
      white-space: nowrap;
      transition:
        opacity 0.2s ease,
        transform 0.24s ease;
    }

    .donate-widget:hover .donate-widget-text,
    .donate-widget:focus-within .donate-widget-text {
      opacity: 1;
      transform: translateX(0);
      pointer-events: auto;
      white-space: normal;
    }

    .donate-widget-title {
      color: #fff7ed;
      font-size: 0.9rem;
      font-weight: 700;
      line-height: 1.25;
    }

    .donate-widget-subtitle {
      color: #cbd5e1;
      font-size: 0.75rem;
      line-height: 1.35;
    }

    .donate-widget-link {
      position: relative;
      z-index: 1;
      flex: 0 0 auto;

      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.45rem;

      width: 2.55rem;
      min-width: 2.55rem;
      height: 2.55rem;
      padding: 0;

      border-radius: 999px;
      background: linear-gradient(135deg, #fb923c, #ec4899);
      color: #fff;
      font-size: 0.82rem;
      font-weight: 800;
      text-decoration: none;
      box-shadow:
        0 10px 22px rgba(236, 72, 153, 0.24),
        0 0 0 1px rgba(255, 255, 255, 0.10) inset;

      transition:
        width 0.24s ease,
        min-width 0.24s ease,
        padding 0.24s ease,
        border-radius 0.24s ease,
        transform 0.2s ease,
        filter 0.2s ease;
    }

    .donate-widget:hover .donate-widget-link,
    .donate-widget:focus-within .donate-widget-link {
      width: auto;
      min-width: 2.7rem;
      padding: 0 0.9rem;
      border-radius: 999px;
    }

    .donate-widget-link:hover {
      transform: scale(1.03);
      filter: brightness(1.06);
    }

    .donate-widget-link svg {
      width: 1rem;
      height: 1rem;
      flex-shrink: 0;
    }

    .donate-widget-link span {
      display: none;
    }

    .donate-widget:hover .donate-widget-link span,
    .donate-widget:focus-within .donate-widget-link span {
      display: inline;
    }

    @media (max-width: 640px) {
    .donate-widget {
      left: auto;
      right: max(0.75rem, env(safe-area-inset-right));
      bottom: max(5.5rem, env(safe-area-inset-bottom));

      width: 3.45rem;
      min-height: 3.15rem;
      padding: 0.38rem;
    }

    .donate-widget:hover,
    .donate-widget:focus-within {
      width: min(320px, calc(100vw - 1.5rem));
      padding: 0.65rem;
    }

    .donate-widget-subtitle {
      display: none;
    }

    .donate-widget-link {
      width: 2.4rem;
      min-width: 2.4rem;
      height: 2.4rem;
    }
  }
  `;
  document.head.appendChild(style);
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
