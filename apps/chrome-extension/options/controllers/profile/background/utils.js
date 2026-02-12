(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const FALLBACK_CARD_THEME_LIMITS = Object.freeze({
    hueDeg: Object.freeze({ min: -180, max: 180, step: 1, defaultValue: 0 }),
    saturationPercent: Object.freeze({ min: 70, max: 140, step: 1, defaultValue: 100 }),
    brightnessPercent: Object.freeze({ min: 80, max: 125, step: 1, defaultValue: 100 })
  });

  function clampOpacity(value) {
    const parsed = Number.parseFloat(value);
    if (!Number.isFinite(parsed)) {
      return 0.18;
    }
    return Math.min(1, Math.max(0, parsed));
  }

  function normalizeBackdropColor(value) {
    const candidate = String(value || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(candidate)) {
      return candidate.toLowerCase();
    }
    return "#fbf7f0";
  }

  function hexColorToRgb(value) {
    const normalized = normalizeBackdropColor(value).slice(1);
    return {
      r: Number.parseInt(normalized.slice(0, 2), 16),
      g: Number.parseInt(normalized.slice(2, 4), 16),
      b: Number.parseInt(normalized.slice(4, 6), 16)
    };
  }

  function formatBytes(bytes) {
    const value = Number(bytes);
    if (!Number.isFinite(value) || value <= 0) {
      return "0 B";
    }
    if (value < 1024) {
      return `${Math.round(value)} B`;
    }
    if (value < 1024 * 1024) {
      return `${(value / 1024).toFixed(1)} KB`;
    }
    return `${(value / (1024 * 1024)).toFixed(2)} MB`;
  }

  function resolveCardThemeLimits() {
    const themeRoot = root.profileUiTheme && typeof root.profileUiTheme === "object"
      ? root.profileUiTheme
      : {};
    const configured = themeRoot.CARD_THEME_LIMITS && typeof themeRoot.CARD_THEME_LIMITS === "object"
      ? themeRoot.CARD_THEME_LIMITS
      : {};
    const hueDeg = configured.hueDeg && typeof configured.hueDeg === "object"
      ? configured.hueDeg
      : FALLBACK_CARD_THEME_LIMITS.hueDeg;
    const saturationPercent = configured.saturationPercent && typeof configured.saturationPercent === "object"
      ? configured.saturationPercent
      : FALLBACK_CARD_THEME_LIMITS.saturationPercent;
    const brightnessPercent = configured.brightnessPercent && typeof configured.brightnessPercent === "object"
      ? configured.brightnessPercent
      : FALLBACK_CARD_THEME_LIMITS.brightnessPercent;
    return {
      hueDeg,
      saturationPercent,
      brightnessPercent
    };
  }

  function clampCardThemeHueDeg(value) {
    const limits = resolveCardThemeLimits().hueDeg;
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
      return limits.defaultValue;
    }
    return Math.min(limits.max, Math.max(limits.min, parsed));
  }

  function clampCardThemeSaturationPercent(value) {
    const limits = resolveCardThemeLimits().saturationPercent;
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
      return limits.defaultValue;
    }
    return Math.min(limits.max, Math.max(limits.min, parsed));
  }

  function clampCardThemeBrightnessPercent(value) {
    const limits = resolveCardThemeLimits().brightnessPercent;
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
      return limits.defaultValue;
    }
    return Math.min(limits.max, Math.max(limits.min, parsed));
  }

  root.optionsProfileBackgroundUtils = {
    clampOpacity,
    normalizeBackdropColor,
    hexColorToRgb,
    formatBytes,
    resolveCardThemeLimits,
    clampCardThemeHueDeg,
    clampCardThemeSaturationPercent,
    clampCardThemeBrightnessPercent
  };
})();
