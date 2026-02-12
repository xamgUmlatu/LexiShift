(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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

  function clampPositionPercent(value, fallback) {
    const parsed = Number.parseFloat(value);
    const fallbackValue = Number.isFinite(Number(fallback)) ? Number(fallback) : 50;
    const base = Number.isFinite(parsed) ? parsed : fallbackValue;
    const clamped = Math.min(100, Math.max(0, base));
    return Math.round(clamped * 100) / 100;
  }

  root.optionsProfileBackgroundUtils = {
    clampOpacity,
    normalizeBackdropColor,
    hexColorToRgb,
    formatBytes,
    clampPositionPercent
  };
})();
