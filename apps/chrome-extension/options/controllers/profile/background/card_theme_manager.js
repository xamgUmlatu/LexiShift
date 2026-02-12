(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const FALLBACK_TOKEN_KEYS = Object.freeze([
    "--ls-card-surface",
    "--ls-card-border",
    "--ls-card-shadow",
    "--ls-card-accent-start",
    "--ls-card-accent-end",
    "--ls-modal-surface",
    "--ls-modal-border",
    "--ls-modal-shadow",
    "--ls-module-card-border",
    "--ls-module-card-bg-start",
    "--ls-module-card-bg-end",
    "--ls-module-card-shadow",
    "--ls-profile-panel-border",
    "--ls-profile-panel-bg",
    "--ls-profile-preview-border",
    "--ls-profile-preview-bg",
    "--ls-srs-preview-border",
    "--ls-srs-preview-bg",
    "--ls-helper-status-border",
    "--ls-helper-status-bg",
    "--ls-advanced-border",
    "--ls-advanced-bg"
  ]);

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

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
    const rawTransparencyPercent = Number(transform.transparencyPercent);
    const alphaScale = clamp01((Number.isFinite(rawTransparencyPercent) ? rawTransparencyPercent : 100) / 100);
    const alpha = clamp01(parsed.a * alphaScale);
    if (parsed.format === "hex") {
      if (alphaScale < 1) {
        return toRgba(rgb, alpha);
      }
      return toHex(rgb);
    }
    if (parsed.format === "rgb") {
      if (alphaScale < 1) {
        return toRgba(rgb, alpha);
      }
      return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
    }
    return toRgba(rgb, alpha);
  }

  function createManager(options) {
    const opts = isObject(options) ? options : {};
    const documentRef = opts.documentRef && opts.documentRef.documentElement
      ? opts.documentRef
      : document;
    const profileUiTheme = root.profileUiTheme && isObject(root.profileUiTheme)
      ? root.profileUiTheme
      : {};
    const themePrefs = root.profileUiThemePrefs && isObject(root.profileUiThemePrefs)
      ? root.profileUiThemePrefs
      : {};
    const tokenKeys = Array.isArray(opts.tokenKeys) && opts.tokenKeys.length
      ? opts.tokenKeys
      : (Array.isArray(profileUiTheme.CARD_THEME_TOKEN_KEYS) && profileUiTheme.CARD_THEME_TOKEN_KEYS.length
        ? profileUiTheme.CARD_THEME_TOKEN_KEYS
        : FALLBACK_TOKEN_KEYS);
    const resolveCardThemeDefaults = typeof themePrefs.resolveCardThemeDefaults === "function"
      ? themePrefs.resolveCardThemeDefaults
      : () => ({
          hueDeg: 0,
          saturationPercent: 100,
          brightnessPercent: 100,
          transparencyPercent: 100
        });
    const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
      ? themePrefs.normalizeCardThemePrefs
      : () => ({
          cardThemeHueDeg: 0,
          cardThemeSaturationPercent: 100,
          cardThemeBrightnessPercent: 100,
          cardThemeTransparencyPercent: 100
        });
    const toTransformValues = typeof themePrefs.toTransformValues === "function"
      ? themePrefs.toTransformValues
      : (rawPrefs) => ({
          hueDeg: Number(rawPrefs && rawPrefs.cardThemeHueDeg) || 0,
          saturationPercent: Number(rawPrefs && rawPrefs.cardThemeSaturationPercent) || 100,
          brightnessPercent: Number(rawPrefs && rawPrefs.cardThemeBrightnessPercent) || 100,
          transparencyPercent: Number(rawPrefs && rawPrefs.cardThemeTransparencyPercent) || 100
        });
    const rootStyle = documentRef.documentElement.style;
    let baseTokenMap = null;

    function resolveDefaultThemePrefs() {
      const defaults = resolveCardThemeDefaults({
        defaults: opts.defaults
      });
      return {
        cardThemeHueDeg: defaults.hueDeg,
        cardThemeSaturationPercent: defaults.saturationPercent,
        cardThemeBrightnessPercent: defaults.brightnessPercent,
        cardThemeTransparencyPercent: defaults.transparencyPercent
      };
    }

    function readBaseTokenMap() {
      const computedStyle = globalThis.getComputedStyle(documentRef.documentElement);
      const map = {};
      tokenKeys.forEach((tokenKey) => {
        const baseValue = String(computedStyle.getPropertyValue(tokenKey) || "").trim();
        if (baseValue) {
          map[tokenKey] = baseValue;
        }
      });
      return map;
    }

    function ensureBaseTokenMap() {
      if (!baseTokenMap) {
        baseTokenMap = readBaseTokenMap();
      }
      return baseTokenMap;
    }

    function normalizeTransform(rawPrefs) {
      const defaults = resolveDefaultThemePrefs();
      return toTransformValues(
        normalizeCardThemePrefs(rawPrefs, {
          fallback: defaults,
          defaults
        })
      );
    }

    function isDefaultTransform(transform) {
      const defaults = resolveCardThemeDefaults({
        defaults: opts.defaults
      });
      return transform.hueDeg === defaults.hueDeg
        && transform.saturationPercent === defaults.saturationPercent
        && transform.brightnessPercent === defaults.brightnessPercent
        && transform.transparencyPercent === defaults.transparencyPercent;
    }

    function clearCardTheme() {
      tokenKeys.forEach((tokenKey) => {
        rootStyle.removeProperty(tokenKey);
      });
    }

    function applyCardThemeFromPrefs(rawPrefs) {
      const transform = normalizeTransform(rawPrefs);
      if (isDefaultTransform(transform)) {
        clearCardTheme();
        return transform;
      }
      const tokens = ensureBaseTokenMap();
      Object.entries(tokens).forEach(([tokenKey, baseColor]) => {
        const transformed = transformColor(baseColor, transform);
        rootStyle.setProperty(tokenKey, transformed);
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
