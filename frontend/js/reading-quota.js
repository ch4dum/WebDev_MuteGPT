(function () {
  const LIMITED_POST_PATHS = new Set([
    "/api/v1/horoscope",
    "/api/v1/numerology",
    "/api/v1/lucky-color",
    "/api/v1/thai-astrology",
    "/api/v1/tarot-reading",
  ]);

  let quotaEl = null;
  let isRefreshing = false;

  function getPath(input) {
    try {
      const raw = typeof input === "string" ? input : input?.url || "";
      return new URL(raw, window.location.origin).pathname;
    } catch {
      return "";
    }
  }

  function getMethod(input, init) {
    return (init?.method || input?.method || "GET").toUpperCase();
  }

  function ensureQuotaBadge() {
    if (quotaEl) return quotaEl;

    const inputArea = document.querySelector(".chat-input-area");
    if (!inputArea) return null;

    quotaEl = document.createElement("div");
    quotaEl.id = "reading-quota-badge";
    quotaEl.className = [
      "mb-3",
      "inline-flex",
      "items-center",
      "gap-2",
      "rounded-full",
      "border",
      "border-[rgb(var(--c-primary)/0.35)]",
      "bg-black/25",
      "px-3",
      "py-1.5",
      "text-[11px]",
      "font-medium",
      "text-[rgb(var(--c-light))]",
      "shadow-[0_0_16px_rgb(var(--c-primary)/0.12)]",
    ].join(" ");
    quotaEl.innerHTML = '<span class="h-2 w-2 rounded-full bg-[rgb(var(--c-accent))]"></span><span>กำลังโหลดสิทธิ์ดูดวง...</span>';

    inputArea.insertBefore(quotaEl, inputArea.firstChild);
    return quotaEl;
  }

  async function getAccessToken() {
    if (!window.supabaseClient?.auth?.getSession) return "";
    const { data: { session } } = await window.supabaseClient.auth.getSession();
    return session?.access_token || "";
  }

  function setBadgeText(text, state = "normal") {
    const el = ensureQuotaBadge();
    if (!el) return;

    const dotClass = state === "empty"
      ? "bg-red-400"
      : state === "warn"
        ? "bg-amber-300"
        : "bg-[rgb(var(--c-accent))]";

    el.innerHTML = `<span class="h-2 w-2 rounded-full ${dotClass}"></span><span>${text}</span>`;
    el.classList.toggle("opacity-60", state === "muted");
  }

  async function refreshReadingQuota() {
    if (isRefreshing) return;
    isRefreshing = true;
    try {
      const token = await getAccessToken();
      if (!token) {
        setBadgeText("เข้าสู่ระบบเพื่อดูสิทธิ์ดูดวงวันนี้", "muted");
        return;
      }

      const res = await window.__muteGptOriginalFetch("/api/v1/reading-usage", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      if (!res.ok) {
        setBadgeText("ยังไม่สามารถโหลดสิทธิ์ดูดวงได้", "warn");
        return;
      }

      if (!data.limit) {
        setBadgeText("ไม่จำกัดจำนวนครั้งวันนี้", "normal");
        return;
      }

      const remaining = Math.max(Number(data.remaining || 0), 0);
      const limit = Number(data.limit || 0);
      const state = remaining === 0 ? "empty" : remaining <= 1 ? "warn" : "normal";
      setBadgeText(`เหลือสิทธิ์ดูดวงวันนี้ ${remaining}/${limit} ครั้ง`, state);
    } catch (error) {
      console.warn("Unable to refresh reading quota:", error);
      setBadgeText("ยังไม่สามารถโหลดสิทธิ์ดูดวงได้", "warn");
    } finally {
      isRefreshing = false;
    }
  }

  window.__muteGptOriginalFetch = window.__muteGptOriginalFetch || window.fetch.bind(window);
  window.fetch = async function patchedFetch(input, init) {
    const path = getPath(input);
    const method = getMethod(input, init);
    const response = await window.__muteGptOriginalFetch(input, init);

    if (method === "POST" && LIMITED_POST_PATHS.has(path) && (response.ok || response.status === 429)) {
      window.setTimeout(refreshReadingQuota, 300);
    }

    return response;
  };

  window.MuteGPTQuota = { refresh: refreshReadingQuota };

  document.addEventListener("DOMContentLoaded", () => {
    ensureQuotaBadge();
    const timer = window.setInterval(() => {
      if (window.supabaseClient?.auth?.getSession) {
        window.clearInterval(timer);
        refreshReadingQuota();
      }
    }, 100);
  });
})();
