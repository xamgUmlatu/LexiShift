(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_THEME_VAR_KEYS = Object.freeze([
    "--lexishift-module-bg",
    "--lexishift-module-text",
    "--lexishift-module-label",
    "--lexishift-module-line",
    "--lexishift-module-quote-text",
    "--lexishift-module-quote-border",
    "--lexishift-module-shadow"
  ]);
  const DEFAULT_THEME_BASE_COLORS = Object.freeze({
    bg: "rgba(28,26,23,0.94)",
    text: "#f7f4ef",
    label: "rgba(247,244,239,0.72)",
    line: "rgba(247,244,239,0.9)",
    quoteText: "rgba(247,244,239,0.86)",
    quoteBorder: "rgba(247,244,239,0.35)",
    shadow: "rgba(0,0,0,0.18)"
  });
  const DEFAULT_THEME_FALLBACK_LIMITS = Object.freeze({
    hueDeg: Object.freeze({
      min: -180,
      max: 180,
      defaultValue: 0
    }),
    saturationPercent: Object.freeze({
      min: 70,
      max: 450,
      defaultValue: 100
    }),
    brightnessPercent: Object.freeze({
      min: 80,
      max: 200,
      defaultValue: 100
    }),
    transparencyPercent: Object.freeze({
      min: 40,
      max: 100,
      defaultValue: 100
    })
  });

  function normalizeLanguage(value) {
    return String(value || "").trim().toLowerCase();
  }

  function clamp01(value) {
    return Math.min(1, Math.max(0, value));
  }

  function wrapHue(value) {
    const wrapped = value % 360;
    return wrapped < 0 ? wrapped + 360 : wrapped;
  }

  function toFiniteNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function normalizeThemeValue(limit, value, fallback) {
    const lower = toFiniteNumber(limit && limit.min);
    const upper = toFiniteNumber(limit && limit.max);
    const defaultValue = toFiniteNumber(limit && limit.defaultValue);
    const fallbackValue = toFiniteNumber(fallback);
    const parsed = Number.parseInt(value, 10);
    const base = Number.isFinite(parsed)
      ? parsed
      : (
          fallbackValue !== null
            ? fallbackValue
            : (defaultValue !== null ? defaultValue : 0)
        );
    const lowerBounded = lower !== null ? Math.max(lower, base) : base;
    return upper !== null ? Math.min(upper, lowerBounded) : lowerBounded;
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
    const roundedAlpha = a.toFixed(3).replace(/0+$/, "").replace(/\.$/, "") || "0";
    return `rgba(${r}, ${g}, ${b}, ${roundedAlpha})`;
  }

  function transformColor(value, transform) {
    const parsed = parseColor(value);
    if (!parsed) {
      return value;
    }
    const hsl = rgbToHsl(parsed);
    const transformedHsl = {
      h: wrapHue(hsl.h + Number(transform && transform.hueDeg)),
      s: clamp01(hsl.s * (Number(transform && transform.saturationPercent) / 100)),
      l: clamp01(hsl.l * (Number(transform && transform.brightnessPercent) / 100))
    };
    const rgb = hslToRgb(transformedHsl);
    const alphaScale = clamp01((Number(transform && transform.transparencyPercent) || 100) / 100);
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

  function createThemeManager(options = {}) {
    const popupModulesRegistry = options.popupModulesRegistry && typeof options.popupModulesRegistry === "object"
      ? options.popupModulesRegistry
      : null;
    const getActivePopupModulePrefs = typeof options.getActivePopupModulePrefs === "function"
      ? options.getActivePopupModulePrefs
      : (() => ({ byId: {}, order: [] }));
    const runtimeThemeModuleIdMap = options.runtimeThemeModuleIdMap && typeof options.runtimeThemeModuleIdMap === "object"
      ? options.runtimeThemeModuleIdMap
      : {};
    const themeVarKeys = Array.isArray(options.moduleThemeVarKeys) && options.moduleThemeVarKeys.length
      ? options.moduleThemeVarKeys
      : DEFAULT_THEME_VAR_KEYS;
    const themeBaseColors = options.moduleThemeBaseColors && typeof options.moduleThemeBaseColors === "object"
      ? options.moduleThemeBaseColors
      : DEFAULT_THEME_BASE_COLORS;
    const themeFallbackLimits = options.moduleThemeFallbackLimits && typeof options.moduleThemeFallbackLimits === "object"
      ? options.moduleThemeFallbackLimits
      : DEFAULT_THEME_FALLBACK_LIMITS;

    function resolveModuleThemeLimits() {
      if (popupModulesRegistry && typeof popupModulesRegistry.resolveModuleThemeLimits === "function") {
        return popupModulesRegistry.resolveModuleThemeLimits();
      }
      return themeFallbackLimits;
    }

    function resolveModuleThemeDefaults() {
      if (popupModulesRegistry && typeof popupModulesRegistry.resolveModuleThemeDefaults === "function") {
        return popupModulesRegistry.resolveModuleThemeDefaults();
      }
      return {
        hueDeg: themeFallbackLimits.hueDeg.defaultValue,
        saturationPercent: themeFallbackLimits.saturationPercent.defaultValue,
        brightnessPercent: themeFallbackLimits.brightnessPercent.defaultValue,
        transparencyPercent: themeFallbackLimits.transparencyPercent.defaultValue
      };
    }

    function normalizeModuleThemeConfig(rawTheme, fallbackTheme) {
      if (popupModulesRegistry && typeof popupModulesRegistry.normalizeModuleThemeConfig === "function") {
        return popupModulesRegistry.normalizeModuleThemeConfig(rawTheme, fallbackTheme);
      }
      const fallback = fallbackTheme && typeof fallbackTheme === "object"
        ? fallbackTheme
        : resolveModuleThemeDefaults();
      const source = rawTheme && typeof rawTheme === "object" ? rawTheme : {};
      const limits = resolveModuleThemeLimits();
      return {
        hueDeg: normalizeThemeValue(limits.hueDeg, source.hueDeg, fallback.hueDeg),
        saturationPercent: normalizeThemeValue(
          limits.saturationPercent,
          source.saturationPercent,
          fallback.saturationPercent
        ),
        brightnessPercent: normalizeThemeValue(
          limits.brightnessPercent,
          source.brightnessPercent,
          fallback.brightnessPercent
        ),
        transparencyPercent: normalizeThemeValue(
          limits.transparencyPercent,
          source.transparencyPercent,
          fallback.transparencyPercent
        )
      };
    }

    function resolveThemePrefsModuleId(runtimeModuleId) {
      const moduleId = String(runtimeModuleId || "").trim();
      if (!moduleId) {
        return "";
      }
      return runtimeThemeModuleIdMap[moduleId] || moduleId;
    }

    function supportsModuleTheme(prefModuleId) {
      if (!prefModuleId) {
        return false;
      }
      if (popupModulesRegistry && typeof popupModulesRegistry.supportsThemeTuning === "function") {
        return popupModulesRegistry.supportsThemeTuning(prefModuleId);
      }
      return prefModuleId === "ja-script-forms"
        || prefModuleId === "feedback-history"
        || prefModuleId === "encounter-history";
    }

    function getModuleThemeConfig(prefModuleId) {
      const prefs = getActivePopupModulePrefs();
      const byId = prefs && typeof prefs === "object"
        && prefs.byId
        && typeof prefs.byId === "object"
        ? prefs.byId
        : {};
      const entry = byId[prefModuleId] && typeof byId[prefModuleId] === "object"
        ? byId[prefModuleId]
        : {};
      const config = entry.config && typeof entry.config === "object" ? entry.config : {};
      return config.theme && typeof config.theme === "object" ? config.theme : null;
    }

    function isDefaultModuleTheme(theme, defaults) {
      return Number(theme && theme.hueDeg) === Number(defaults && defaults.hueDeg)
        && Number(theme && theme.saturationPercent) === Number(defaults && defaults.saturationPercent)
        && Number(theme && theme.brightnessPercent) === Number(defaults && defaults.brightnessPercent)
        && Number(theme && theme.transparencyPercent) === Number(defaults && defaults.transparencyPercent);
    }

    function clearPopupModuleTheme(node) {
      if (!(node instanceof HTMLElement)) {
        return;
      }
      themeVarKeys.forEach((tokenKey) => {
        node.style.removeProperty(tokenKey);
      });
    }

    function applyPopupModuleTheme(runtimeModuleId, node) {
      if (!(node instanceof HTMLElement)) {
        return;
      }
      const prefModuleId = resolveThemePrefsModuleId(runtimeModuleId);
      if (!supportsModuleTheme(prefModuleId)) {
        clearPopupModuleTheme(node);
        return;
      }
      const defaults = resolveModuleThemeDefaults();
      const normalizedTheme = normalizeModuleThemeConfig(
        getModuleThemeConfig(prefModuleId),
        defaults
      );
      if (isDefaultModuleTheme(normalizedTheme, defaults)) {
        clearPopupModuleTheme(node);
        return;
      }
      node.style.setProperty("--lexishift-module-bg", transformColor(themeBaseColors.bg, normalizedTheme));
      node.style.setProperty("--lexishift-module-text", transformColor(themeBaseColors.text, normalizedTheme));
      node.style.setProperty("--lexishift-module-label", transformColor(themeBaseColors.label, normalizedTheme));
      node.style.setProperty("--lexishift-module-line", transformColor(themeBaseColors.line, normalizedTheme));
      node.style.setProperty(
        "--lexishift-module-quote-text",
        transformColor(themeBaseColors.quoteText, normalizedTheme)
      );
      node.style.setProperty(
        "--lexishift-module-quote-border",
        transformColor(themeBaseColors.quoteBorder, normalizedTheme)
      );
      node.style.setProperty("--lexishift-module-shadow", transformColor(themeBaseColors.shadow, normalizedTheme));
    }

    return {
      applyPopupModuleTheme,
      clearPopupModuleTheme
    };
  }

  function resolveRuntimePopupModuleOrder(options = {}) {
    const configuredOrder = Array.isArray(options.configuredOrder) ? options.configuredOrder : [];
    const prefToRuntimeModuleIdMap = options.prefToRuntimeModuleIdMap && typeof options.prefToRuntimeModuleIdMap === "object"
      ? options.prefToRuntimeModuleIdMap
      : {};
    const defaultRuntimeModuleOrder = Array.isArray(options.defaultRuntimeModuleOrder)
      ? options.defaultRuntimeModuleOrder
      : [];
    const descriptorsById = options.descriptorsById && typeof options.descriptorsById === "object"
      ? options.descriptorsById
      : {};
    const orderedRuntimeIds = [];
    const seen = new Set();
    function appendRuntimeId(runtimeModuleId) {
      const normalized = String(runtimeModuleId || "").trim();
      if (!normalized || seen.has(normalized) || !descriptorsById[normalized]) {
        return;
      }
      seen.add(normalized);
      orderedRuntimeIds.push(normalized);
    }
    for (const rawPrefModuleId of configuredOrder) {
      const prefModuleId = String(rawPrefModuleId || "").trim();
      if (!prefModuleId) {
        continue;
      }
      appendRuntimeId(prefToRuntimeModuleIdMap[prefModuleId] || prefModuleId);
    }
    for (const runtimeModuleId of defaultRuntimeModuleOrder) {
      appendRuntimeId(runtimeModuleId);
    }
    for (const runtimeModuleId of Object.keys(descriptorsById)) {
      appendRuntimeId(runtimeModuleId);
    }
    return orderedRuntimeIds;
  }

  root.uiPopupHelpers = {
    normalizeLanguage,
    createThemeManager,
    resolveRuntimePopupModuleOrder
  };
})();
