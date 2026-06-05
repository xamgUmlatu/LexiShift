(() => {
  const toggle = document.querySelector("[data-guide-theme-toggle]");
  if (!toggle) {
    return;
  }

  const storageKey = "lexishift_guide_theme";
  const root = document.documentElement;

  const setToggleLabel = (isDark) => {
    const nextModeLabel = isDark ? "light" : "dark";
    const text = `Switch to ${nextModeLabel} mode`;
    toggle.setAttribute("aria-label", text);
    toggle.setAttribute("title", text);
  };

  const applyTheme = (theme) => {
    const resolved = theme === "dark" ? "dark" : "light";
    root.setAttribute("data-guide-theme", resolved);
    setToggleLabel(resolved === "dark");
  };

  let savedTheme = null;
  try {
    savedTheme = localStorage.getItem(storageKey);
  } catch (_error) {
    savedTheme = null;
  }

  applyTheme(savedTheme === "light" ? "light" : "dark");

  toggle.addEventListener("click", () => {
    const current = root.getAttribute("data-guide-theme");
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(storageKey, next);
    } catch (_error) {
      // Ignore storage failures (private browsing or blocked storage).
    }
  });
})();
