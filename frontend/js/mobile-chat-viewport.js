(function () {
  let lastStableHeight = window.innerHeight;

  function isTextInputFocused() {
    const active = document.activeElement;
    if (!active) return false;
    const tagName = active.tagName;
    return tagName === "INPUT" || tagName === "TEXTAREA" || active.isContentEditable;
  }

  function setAppHeight() {
    if (isTextInputFocused()) {
      document.documentElement.style.setProperty("--app-height", `${lastStableHeight}px`);
      return;
    }

    lastStableHeight = window.innerHeight;
    document.documentElement.style.setProperty("--app-height", `${lastStableHeight}px`);
  }

  setAppHeight();
  window.addEventListener("resize", setAppHeight);
  window.addEventListener("orientationchange", setAppHeight);

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setAppHeight);
  }
})();
