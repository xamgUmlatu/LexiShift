(() => {
  const shell = document.querySelector("[data-guide-locale-shell]");
  const toggle = document.querySelector("[data-guide-locale-toggle]");
  const panel = document.querySelector("[data-guide-locale-panel]");
  if (!shell || !toggle || !panel) {
    return;
  }

  const storageKey = "lexishift_guide_locale";
  const root = document.documentElement;
  const localeLabels = {
    en: "EN",
    es: "ES",
    fr: "FR",
    eo: "EO",
    de: "DE",
    it: "IT",
    ja: "日",
    "zh-hant": "繁",
    "zh-hans": "简",
  };
  const supportedLocales = new Set(["system", ...Object.keys(localeLabels)]);
  const options = Array.from(
    panel.querySelectorAll("[data-guide-locale-option]"),
  );

  const normalizeLocale = (value) =>
    String(value || "")
      .trim()
      .toLowerCase()
      .replace(/_/g, "-");

  const resolveLocalePreference = (value) => {
    const normalized = normalizeLocale(value);
    if (supportedLocales.has(normalized)) {
      return normalized;
    }
    if (
      normalized.startsWith("zh-hant")
      || normalized.startsWith("zh-tw")
      || normalized.startsWith("zh-hk")
      || normalized.startsWith("zh-mo")
    ) {
      return "zh-hant";
    }
    if (normalized.startsWith("zh")) {
      return "zh-hans";
    }
    const languageTag = normalized.split("-")[0];
    if (supportedLocales.has(languageTag)) {
      return languageTag;
    }
    return "system";
  };

  const resolveSystemLocale = () =>
    normalizeLocale(
      (typeof navigator !== "undefined" && navigator.language) || "en",
    ) || "en";

  const setOpen = (open) => {
    shell.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) {
      const active = panel.querySelector(".guide-locale-cell.is-active");
      const focusTarget = active || options[0];
      if (focusTarget) {
        requestAnimationFrame(() => focusTarget.focus());
      }
    }
  };

  const setActiveCell = (preference) => {
    const resolved = resolveLocalePreference(preference);
    options.forEach((option) => {
      const isActive = option.dataset.guideLocaleOption === resolved;
      option.classList.toggle("is-active", isActive);
      option.setAttribute("aria-selected", isActive ? "true" : "false");
    });
  };

  const updateToggleLabel = (preference, resolvedLocale) => {
    const normalized = resolveLocalePreference(preference);
    const visibleLabel = normalized === "system"
      ? "SYS"
      : (localeLabels[normalized] || normalized.toUpperCase());
    const titleText = normalized === "system"
      ? `Language: System default (${resolvedLocale}). Click to open language grid.`
      : `Language: ${visibleLabel}. Click to open language grid.`;
    toggle.setAttribute("aria-label", titleText);
    toggle.setAttribute("title", titleText);
    toggle.setAttribute("data-locale-code", visibleLabel);
  };

  const applyLocalePreference = (preference, { persist = false } = {}) => {
    const normalized = resolveLocalePreference(preference);
    const resolvedLocale = normalized === "system"
      ? resolveSystemLocale()
      : normalized;

    root.setAttribute("data-guide-locale-preference", normalized);
    root.setAttribute("data-guide-locale", resolvedLocale);
    setActiveCell(normalized);
    updateToggleLabel(normalized, resolvedLocale);

    if (persist) {
      try {
        localStorage.setItem(storageKey, normalized);
      } catch (_error) {
        // Ignore storage failures (private browsing or blocked storage).
      }
    }
  };

  let savedPreference = "system";
  try {
    savedPreference = resolveLocalePreference(localStorage.getItem(storageKey));
  } catch (_error) {
    savedPreference = resolveLocalePreference(
      root.getAttribute("data-guide-locale-preference"),
    );
  }

  applyLocalePreference(savedPreference);
  setOpen(false);

  toggle.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setOpen(!shell.classList.contains("is-open"));
  });

  panel.addEventListener("click", (event) => {
    const target = event.target instanceof Element
      ? event.target.closest("[data-guide-locale-option]")
      : null;
    if (!target) {
      setOpen(false);
      return;
    }
    const selected = resolveLocalePreference(target.dataset.guideLocaleOption);
    const current = resolveLocalePreference(
      root.getAttribute("data-guide-locale-preference"),
    );
    const nextPreference = selected === current ? "system" : selected;
    applyLocalePreference(nextPreference, { persist: true });
    setOpen(false);
  });

  document.addEventListener("click", (event) => {
    if (!shell.classList.contains("is-open")) {
      return;
    }
    if (event.target instanceof Node && shell.contains(event.target)) {
      return;
    }
    setOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    if (!shell.classList.contains("is-open")) {
      return;
    }
    setOpen(false);
    toggle.focus();
  });
})();
