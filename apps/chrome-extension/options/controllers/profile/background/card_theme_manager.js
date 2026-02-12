(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const BASE_CARD_THEME_TOKENS = Object.freeze({
    "--ls-card-surface": "#fffaf2",
    "--ls-card-border": "#e3dccf",
    "--ls-card-shadow": "rgba(54, 47, 38, 0.08)",
    "--ls-card-accent-start": "rgba(44, 42, 38, 0.2)",
    "--ls-card-accent-end": "rgba(44, 42, 38, 0)",
    "--ls-modal-surface": "#fffaf2",
    "--ls-modal-border": "#e3d8c8",
    "--ls-modal-shadow": "rgba(31, 27, 22, 0.28)",
    "--ls-module-card-border": "#e1d5c2",
    "--ls-module-card-bg-start": "#fffefb",
    "--ls-module-card-bg-end": "#fffaf1",
    "--ls-module-card-shadow": "rgba(33, 28, 20, 0.08)",
    "--ls-profile-panel-border": "#e6dccc",
    "--ls-profile-panel-bg": "#fffdf8",
    "--ls-profile-preview-border": "#e7ddcf",
    "--ls-profile-preview-bg": "#f5eee2",
    "--ls-srs-preview-border": "#e1d6c6",
    "--ls-srs-preview-bg": "#fffdf8",
    "--ls-helper-status-border": "#efe3d4",
    "--ls-helper-status-bg": "#fffaf2",
    "--ls-advanced-border": "#e1d6c6",
    "--ls-advanced-bg": "#fffdf8"
  });

  const FALLBACK_LIMITS = Object.freeze({
    hueDeg: Object.freeze({ defaultValue: 0 }),
    saturationPercent: Object.freeze({ defaultValue: 100 }),
    brightnessPercent: Object.freeze({ defaultValue: 100 })
  });

  function clamp01(value) {
    return Math.min(1, Math.max(0, value));
  }

  function wrapHue(value) {
    const wrapped = value % 360;
    return wrapped < 0 ? wrapped + 360 : wrapped;
  }

  function parseHexColor(value) {
    const raw = String(value || "").trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(raw)) {
      return null;
    }
    return {
      format: "hex",
      r: Number.parseInt(raw.slice(1, 3), 16),
      g: Number.parseInt(raw.slice(3, 5), 16),
      b: Number.parseInt(raw.slice(5, 7), 16),
      a: 1
    };
  }

  function parseRgbaColor(value) {
    const raw = String(value || "").trim();
    const match = raw.match(/^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+)\s*)?\)$/i);
    if (!match) {
      return null;
    }
    const r = Number.parseFloat(match[1]);
    const g = Number.parseFloat(match[2]);
    const b = Number.parseFloat(match[3]);
    const a = match[4] === undefined ? 1 : Number.parseFloat(match[4]);
    if (![r, g, b, a].every(Number.isFinite)) {
      return null;
    }
    return {
      format: raw.toLowerCase().startsWith("rgba(") ? "rgba" : "rgb",
      r: clamp01(r / 255) * 255,
      g: clamp01(g / 255) * 255,
      b: clamp01(b / 255) * 255,
      a: clamp01(a)
    };
  }

  function parseColor(value) {
    return parseHexColor(value) || parseRgbaColor(value);
  }

  function rgbToHsl(rgb) {
    const r = clamp01(rgb.r / 255);
    const g = clamp01(rgb.g / 255);
    const b = clamp01(rgb.b / 255);
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;
    const l = (max + min) / 2;
    if (delta === 0) {
      return { h: 0, s: 0, l };
    }
    const s = l > 0.5 ? delta / (2 - max - min) : delta / (max + min);
    let h = 0;
    switch (max) {
      case r:
        h = (g - b) / delta + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / delta + 2;
        break;
      default:
        h = (r - g) / delta + 4;
        break;
    }
    h /= 6;
    return {
      h: h * 360,
      s,
      l
    };
  }

  function hueToRgb(p, q, t) {
    let local = t;
    if (local < 0) {
      local += 1;
    }
    if (local > 1) {
      local -= 1;
    }
    if (local < (1 / 6)) {
      return p + (q - p) * 6 * local;
    }
    if (local < (1 / 2)) {
      return q;
    }
    if (local < (2 / 3)) {
      return p + (q - p) * ((2 / 3) - local) * 6;
    }
    return p;
  }

  function hslToRgb(hsl) {
    const h = wrapHue(hsl.h) / 360;
    const s = clamp01(hsl.s);
    const l = clamp01(hsl.l);
    if (s === 0) {
      const gray = Math.round(l * 255);
      return { r: gray, g: gray, b: gray };
    }
    const q = l < 0.5 ? l * (1 + s) : (l + s - l * s);
    const p = 2 * l - q;
    return {
      r: Math.round(hueToRgb(p, q, h + (1 / 3)) * 255),
      g: Math.round(hueToRgb(p, q, h) * 255),
      b: Math.round(hueToRgb(p, q, h - (1 / 3)) * 255)
    };
  }

  function toHex(rgb) {
    const r = Math.max(0, Math.min(255, Math.round(rgb.r))).toString(16).padStart(2, "0");
    const g = Math.max(0, Math.min(255, Math.round(rgb.g))).toString(16).padStart(2, "0");
    const b = Math.max(0, Math.min(255, Math.round(rgb.b))).toString(16).padStart(2, "0");
    return `#${r}${g}${b}`;
  }

  function toRgba(rgb, alpha) {
    const r = Math.max(0, Math.min(255, Math.round(rgb.r)));
    const g = Math.max(0, Math.min(255, Math.round(rgb.g)));
    const b = Math.max(0, Math.min(255, Math.round(rgb.b)));
    const a = Math.max(0, Math.min(1, Number(alpha)));
    return `rgba(${r}, ${g}, ${b}, ${a.toFixed(3).replace(/0+$/, "").replace(/\.$/, "") || "0"})`;
  }

  function transformColor(value, transform) {
    const parsed = parseColor(value);
    if (!parsed) {
      return value;
    }
    const hsl = rgbToHsl(parsed);
    const transformedHsl = {
      h: wrapHue(hsl.h + transform.hueDeg),
      s: clamp01(hsl.s * (transform.saturationPercent / 100)),
      l: clamp01(hsl.l * (transform.brightnessPercent / 100))
    };
    const rgb = hslToRgb(transformedHsl);
    if (parsed.format === "hex") {
      return toHex(rgb);
    }
    if (parsed.format === "rgb") {
      return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
    }
    return toRgba(rgb, parsed.a);
  }

  function createManager(options) {
    const opts = options && typeof options === "object" ? options : {};
    const documentRef = opts.documentRef && opts.documentRef.documentElement
      ? opts.documentRef
      : document;
    const clampCardThemeHueDeg = typeof opts.clampCardThemeHueDeg === "function"
      ? opts.clampCardThemeHueDeg
      : (value) => {
          const parsed = Number.parseInt(value, 10);
          return Number.isFinite(parsed) ? parsed : 0;
        };
    const clampCardThemeSaturationPercent = typeof opts.clampCardThemeSaturationPercent === "function"
      ? opts.clampCardThemeSaturationPercent
      : (value) => {
          const parsed = Number.parseInt(value, 10);
          return Number.isFinite(parsed) ? parsed : 100;
        };
    const clampCardThemeBrightnessPercent = typeof opts.clampCardThemeBrightnessPercent === "function"
      ? opts.clampCardThemeBrightnessPercent
      : (value) => {
          const parsed = Number.parseInt(value, 10);
          return Number.isFinite(parsed) ? parsed : 100;
        };
    const resolveCardThemeLimits = typeof opts.resolveCardThemeLimits === "function"
      ? opts.resolveCardThemeLimits
      : (() => FALLBACK_LIMITS);
    const rootStyle = documentRef.documentElement.style;

    function resolveDefaults() {
      const limits = resolveCardThemeLimits();
      return {
        hueDeg: limits && limits.hueDeg && Number.isFinite(Number(limits.hueDeg.defaultValue))
          ? Number(limits.hueDeg.defaultValue)
          : FALLBACK_LIMITS.hueDeg.defaultValue,
        saturationPercent: limits && limits.saturationPercent
          && Number.isFinite(Number(limits.saturationPercent.defaultValue))
          ? Number(limits.saturationPercent.defaultValue)
          : FALLBACK_LIMITS.saturationPercent.defaultValue,
        brightnessPercent: limits && limits.brightnessPercent
          && Number.isFinite(Number(limits.brightnessPercent.defaultValue))
          ? Number(limits.brightnessPercent.defaultValue)
          : FALLBACK_LIMITS.brightnessPercent.defaultValue
      };
    }

    function normalizeTransform(rawPrefs) {
      const prefs = rawPrefs && typeof rawPrefs === "object" ? rawPrefs : {};
      const defaults = resolveDefaults();
      return {
        hueDeg: clampCardThemeHueDeg(
          prefs.cardThemeHueDeg !== undefined ? prefs.cardThemeHueDeg : defaults.hueDeg
        ),
        saturationPercent: clampCardThemeSaturationPercent(
          prefs.cardThemeSaturationPercent !== undefined
            ? prefs.cardThemeSaturationPercent
            : defaults.saturationPercent
        ),
        brightnessPercent: clampCardThemeBrightnessPercent(
          prefs.cardThemeBrightnessPercent !== undefined
            ? prefs.cardThemeBrightnessPercent
            : defaults.brightnessPercent
        )
      };
    }

    function isDefaultTransform(transform) {
      const defaults = resolveDefaults();
      return transform.hueDeg === defaults.hueDeg
        && transform.saturationPercent === defaults.saturationPercent
        && transform.brightnessPercent === defaults.brightnessPercent;
    }

    function clearCardTheme() {
      Object.keys(BASE_CARD_THEME_TOKENS).forEach((token) => {
        rootStyle.removeProperty(token);
      });
    }

    function applyCardThemeFromPrefs(rawPrefs) {
      const transform = normalizeTransform(rawPrefs);
      if (isDefaultTransform(transform)) {
        clearCardTheme();
        return transform;
      }
      Object.entries(BASE_CARD_THEME_TOKENS).forEach(([token, baseColor]) => {
        rootStyle.setProperty(token, transformColor(baseColor, transform));
      });
      return transform;
    }

    return {
      normalizeTransform,
      applyCardThemeFromPrefs,
      clearCardTheme
    };
  }

  root.optionsProfileBackgroundCardThemeManager = {
    createManager
  };
})();
