(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;
  const scriptModule = root.uiJapaneseScriptModule && typeof root.uiJapaneseScriptModule === "object"
    ? root.uiJapaneseScriptModule
    : null;
  const feedbackHistoryModule = root.uiFeedbackHistoryModule && typeof root.uiFeedbackHistoryModule === "object"
    ? root.uiFeedbackHistoryModule
    : null;
  const encounterHistoryModule = root.uiEncounterHistoryModule && typeof root.uiEncounterHistoryModule === "object"
    ? root.uiEncounterHistoryModule
    : null;
  const popupModulesRegistry = root.popupModulesRegistry && typeof root.popupModulesRegistry === "object"
    ? root.popupModulesRegistry
    : null;
  const popupHistoryStore = root.popupModuleHistoryStore && typeof root.popupModuleHistoryStore === "object"
    ? root.popupModuleHistoryStore
    : null;
  const lemmatize = root.lemmatizer && typeof root.lemmatizer.lemmatize === "function"
    ? root.lemmatizer.lemmatize
    : null;
  const popupModuleRegistryFactory = root.uiPopupModuleRegistry
    && typeof root.uiPopupModuleRegistry.createRegistry === "function"
    ? root.uiPopupModuleRegistry.createRegistry
    : null;
  const RUNTIME_THEME_MODULE_ID_MAP = Object.freeze({
    "japanese-script": "ja-script-forms",
    "feedback-history": "feedback-history",
    "encounter-history": "encounter-history"
  });
  const PREF_TO_RUNTIME_MODULE_ID_MAP = Object.freeze({
    "ja-script-forms": "japanese-script",
    "feedback-history": "feedback-history",
    "encounter-history": "encounter-history"
  });
  const DEFAULT_RUNTIME_MODULE_ORDER = Object.freeze([
    "japanese-script",
    "feedback-history",
    "encounter-history"
  ]);
  const MODULE_THEME_VAR_KEYS = Object.freeze([
    "--lexishift-module-bg",
    "--lexishift-module-text",
    "--lexishift-module-label",
    "--lexishift-module-line",
    "--lexishift-module-quote-text",
    "--lexishift-module-quote-border",
    "--lexishift-module-shadow"
  ]);
  const MODULE_THEME_BASE_COLORS = Object.freeze({
    bg: "rgba(28,26,23,0.94)",
    text: "#f7f4ef",
    label: "rgba(247,244,239,0.72)",
    line: "rgba(247,244,239,0.9)",
    quoteText: "rgba(247,244,239,0.86)",
    quoteBorder: "rgba(247,244,239,0.35)",
    shadow: "rgba(0,0,0,0.18)"
  });
  const MODULE_THEME_FALLBACK_LIMITS = Object.freeze({
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
  let activePopupModulePrefs = { byId: {}, order: [] };
  let activePopupProfileId = "default";
  let activeTargetLanguage = "en";

  function normalizeLanguage(value) {
    return String(value || "").trim().toLowerCase();
  }

  function targetLanguageFromPair(pair) {
    const normalized = String(pair || "").trim().toLowerCase();
    if (!normalized) {
      return "";
    }
    const parts = normalized.split("-", 2);
    if (parts.length < 2) {
      return "";
    }
    return String(parts[1] || "").trim().toLowerCase();
  }

  function resolveTargetLanguage(target) {
    const pair = target && target.dataset ? String(target.dataset.languagePair || "") : "";
    return targetLanguageFromPair(pair) || activeTargetLanguage || "en";
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

  function resolveModuleThemeLimits() {
    if (popupModulesRegistry && typeof popupModulesRegistry.resolveModuleThemeLimits === "function") {
      return popupModulesRegistry.resolveModuleThemeLimits();
    }
    return MODULE_THEME_FALLBACK_LIMITS;
  }

  function resolveModuleThemeDefaults() {
    if (popupModulesRegistry && typeof popupModulesRegistry.resolveModuleThemeDefaults === "function") {
      return popupModulesRegistry.resolveModuleThemeDefaults();
    }
    return {
      hueDeg: MODULE_THEME_FALLBACK_LIMITS.hueDeg.defaultValue,
      saturationPercent: MODULE_THEME_FALLBACK_LIMITS.saturationPercent.defaultValue,
      brightnessPercent: MODULE_THEME_FALLBACK_LIMITS.brightnessPercent.defaultValue,
      transparencyPercent: MODULE_THEME_FALLBACK_LIMITS.transparencyPercent.defaultValue
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
    return RUNTIME_THEME_MODULE_ID_MAP[moduleId] || moduleId;
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
    const byId = activePopupModulePrefs && typeof activePopupModulePrefs === "object"
      && activePopupModulePrefs.byId
      && typeof activePopupModulePrefs.byId === "object"
      ? activePopupModulePrefs.byId
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

  function clearPopupModuleTheme(node) {
    if (!(node instanceof HTMLElement)) {
      return;
    }
    MODULE_THEME_VAR_KEYS.forEach((tokenKey) => {
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
    node.style.setProperty("--lexishift-module-bg", transformColor(MODULE_THEME_BASE_COLORS.bg, normalizedTheme));
    node.style.setProperty("--lexishift-module-text", transformColor(MODULE_THEME_BASE_COLORS.text, normalizedTheme));
    node.style.setProperty("--lexishift-module-label", transformColor(MODULE_THEME_BASE_COLORS.label, normalizedTheme));
    node.style.setProperty("--lexishift-module-line", transformColor(MODULE_THEME_BASE_COLORS.line, normalizedTheme));
    node.style.setProperty(
      "--lexishift-module-quote-text",
      transformColor(MODULE_THEME_BASE_COLORS.quoteText, normalizedTheme)
    );
    node.style.setProperty(
      "--lexishift-module-quote-border",
      transformColor(MODULE_THEME_BASE_COLORS.quoteBorder, normalizedTheme)
    );
    node.style.setProperty("--lexishift-module-shadow", transformColor(MODULE_THEME_BASE_COLORS.shadow, normalizedTheme));
  }

  function isPopupModuleEnabled(moduleId, targetLanguage) {
    if (!popupModulesRegistry || typeof popupModulesRegistry.isEnabledForTarget !== "function") {
      return false;
    }
    return popupModulesRegistry.isEnabledForTarget(
      activePopupModulePrefs,
      moduleId,
      normalizeLanguage(targetLanguage)
    );
  }

  function historyModuleContext() {
    return {
      historyStore: popupHistoryStore,
      profileId: activePopupProfileId,
      lemmatize
    };
  }

  const popupModuleDescriptorsById = {
    "japanese-script": {
      id: "japanese-script",
      build: (target, debugLog) => {
        if (!scriptModule || typeof scriptModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("ja-script-forms", targetLanguage)) {
          return null;
        }
        return scriptModule.build(target, debugLog);
      }
    },
    "feedback-history": {
      id: "feedback-history",
      build: (target, debugLog) => {
        if (!feedbackHistoryModule || typeof feedbackHistoryModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("feedback-history", targetLanguage)) {
          return null;
        }
        return feedbackHistoryModule.build(target, debugLog, historyModuleContext());
      }
    },
    "encounter-history": {
      id: "encounter-history",
      build: (target, debugLog) => {
        if (!encounterHistoryModule || typeof encounterHistoryModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("encounter-history", targetLanguage)) {
          return null;
        }
        return encounterHistoryModule.build(target, debugLog, historyModuleContext());
      }
    }
  };

  function resolveRuntimePopupModuleOrder() {
    const configuredOrder = activePopupModulePrefs
      && typeof activePopupModulePrefs === "object"
      && Array.isArray(activePopupModulePrefs.order)
      ? activePopupModulePrefs.order
      : [];
    const orderedRuntimeIds = [];
    const seen = new Set();
    function appendRuntimeId(runtimeModuleId) {
      const normalized = String(runtimeModuleId || "").trim();
      if (!normalized || seen.has(normalized) || !popupModuleDescriptorsById[normalized]) {
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
      appendRuntimeId(PREF_TO_RUNTIME_MODULE_ID_MAP[prefModuleId] || prefModuleId);
    }
    for (const runtimeModuleId of DEFAULT_RUNTIME_MODULE_ORDER) {
      appendRuntimeId(runtimeModuleId);
    }
    for (const runtimeModuleId of Object.keys(popupModuleDescriptorsById)) {
      appendRuntimeId(runtimeModuleId);
    }
    return orderedRuntimeIds;
  }

  function resolvePopupModuleDescriptors() {
    return resolveRuntimePopupModuleOrder()
      .map((runtimeModuleId) => popupModuleDescriptorsById[runtimeModuleId])
      .filter((descriptor) => descriptor && typeof descriptor === "object");
  }

  const popupModuleRegistry = popupModuleRegistryFactory
    ? popupModuleRegistryFactory({
        resolveModules: resolvePopupModuleDescriptors
      })
    : null;
  const feedbackPopupFactory = root.uiFeedbackPopupController
    && typeof root.uiFeedbackPopupController.createController === "function"
    ? root.uiFeedbackPopupController.createController
    : null;
  const feedbackController = feedbackPopupFactory
    ? feedbackPopupFactory({
        popupModuleRegistry,
        applyModuleTheme: applyPopupModuleTheme,
        summarizeTarget: scriptModule && typeof scriptModule.summarizeTarget === "function"
          ? scriptModule.summarizeTarget
          : undefined
      })
    : {
        closeFeedbackPopup: () => {},
        attachFeedbackListener: () => {},
        setDebugEnabled: () => {},
        setFeedbackSoundEnabled: () => {}
      };

  function ensureStyle(color, srsColor) {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      const parent = document.head || document.documentElement;
      if (parent) {
        parent.appendChild(style);
      }
    }
    const srs = srsColor || color;
    style.textContent = `
      :root{--lexishift-highlight-color:${color};--lexishift-srs-highlight-color:${srs};}
      .lexishift-replacement{cursor:pointer;transition:color 120ms ease;}
      .lexishift-replacement.lexishift-highlight{color:var(--lexishift-highlight-color);}
      .lexishift-replacement.lexishift-highlight.lexishift-srs{color:var(--lexishift-srs-highlight-color);}
      .lexishift-feedback-popup{position:absolute;display:flex;flex-direction:column;gap:6px;
        align-items:flex-start;transform:translateY(6px) scale(0.92);opacity:0;
        transition:transform 140ms ease, opacity 140ms ease;z-index:2147483647;
        pointer-events:none;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-feedback-popup.lexishift-open{transform:translateY(0) scale(1);opacity:1;pointer-events:auto;}
      .lexishift-feedback-modules{display:flex;flex-direction:column;gap:6px;align-items:stretch;
        width:100%;}
      .lexishift-feedback-modules:empty{display:none;}
      .lexishift-popup-module{padding:8px 10px;border-radius:10px;
        background:var(--lexishift-module-bg, rgba(28,26,23,0.94));
        color:var(--lexishift-module-text, #f7f4ef);
        box-shadow:0 10px 24px var(--lexishift-module-shadow, rgba(0,0,0,0.18));min-width:140px;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-script-module-row{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:start;}
      .lexishift-script-module-row + .lexishift-script-module-row{margin-top:4px;}
      .lexishift-script-module-label{font-size:10px;line-height:1.3;letter-spacing:0.06em;
        text-transform:uppercase;color:var(--lexishift-module-label, rgba(247,244,239,0.72));}
      .lexishift-script-module-value{font-size:13px;line-height:1.35;font-weight:600;word-break:break-word;}
      .lexishift-popup-module-toggle{display:inline-flex;align-items:center;justify-content:flex-start;
        width:100%;padding:0;border:0;background:transparent;color:inherit;cursor:pointer;
        font-size:12px;line-height:1.35;font-weight:700;letter-spacing:0.03em;}
      .lexishift-popup-module-toggle-centered{justify-content:center;text-align:center;}
      .lexishift-popup-module-toggle:disabled{opacity:0.65;cursor:default;}
      .lexishift-popup-module-details{display:flex;flex-direction:column;gap:4px;margin-top:6px;}
      .lexishift-popup-module-details.hidden{display:none;}
      .lexishift-popup-module-line{font-size:11px;line-height:1.35;
        color:var(--lexishift-module-line, rgba(247,244,239,0.9));}
      .lexishift-popup-module-quote{padding-left:6px;
        border-left:2px solid var(--lexishift-module-quote-border, rgba(247,244,239,0.35));
        font-style:italic;color:var(--lexishift-module-quote-text, rgba(247,244,239,0.86));}
      .lexishift-feedback-bar{display:flex;gap:6px;align-items:center;padding:6px 8px;
        border-radius:999px;background:rgba(28,26,23,0.9);box-shadow:0 10px 24px rgba(0,0,0,0.18);}
      .lexishift-feedback-option{width:22px;height:22px;border-radius:999px;border:0;cursor:pointer;
        display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;
        transition:transform 120ms ease, box-shadow 120ms ease;}
      .lexishift-feedback-option.lexishift-selected{transform:scale(1.15);
        box-shadow:0 0 0 3px rgba(255,255,255,0.45);}
      .lexishift-feedback-option[data-rating="again"]{background:#D64545;}
      .lexishift-feedback-option[data-rating="hard"]{background:#E07B39;}
      .lexishift-feedback-option[data-rating="good"]{background:#E0B84B;color:#2c2a26;}
      .lexishift-feedback-option[data-rating="easy"]{background:#2F74D0;}
    `;
  }

  function applyHighlightToDom(enabled) {
    const highlight = enabled !== false;
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      if (highlight) {
        node.classList.add("lexishift-highlight");
      } else {
        node.classList.remove("lexishift-highlight");
      }
      if (node.dataset.origin === "srs") {
        node.classList.add("lexishift-srs");
      } else {
        node.classList.remove("lexishift-srs");
      }
    });
  }

  function clearReplacements() {
    feedbackController.closeFeedbackPopup();
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      const original = node.dataset.original || node.textContent || "";
      node.replaceWith(document.createTextNode(original));
    });
  }

  function attachClickListener() {
    if (clickListenerAttached) {
      return;
    }
    document.addEventListener("click", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      feedbackController.closeFeedbackPopup();
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.displayReplacement || target.dataset.replacement || target.textContent;
        target.dataset.state = "replacement";
      }
    });
    clickListenerAttached = true;
  }

  function attachFeedbackListener(handler, options = {}) {
    feedbackController.attachFeedbackListener(handler, options);
  }

  function setPopupModulePrefs(prefs, metadata = {}) {
    activePopupModulePrefs = prefs && typeof prefs === "object"
      ? prefs
      : { byId: {}, order: [] };
    if (metadata && metadata.profileId !== undefined) {
      const profileId = String(metadata.profileId || "").trim();
      activePopupProfileId = profileId || "default";
    }
    if (metadata && metadata.targetLanguage !== undefined) {
      activeTargetLanguage = normalizeLanguage(metadata.targetLanguage) || activeTargetLanguage;
    }
  }

  function setDebugEnabled(enabled) {
    feedbackController.setDebugEnabled(enabled === true);
  }

  function setFeedbackSoundEnabled(enabled) {
    feedbackController.setFeedbackSoundEnabled(enabled);
  }

  root.ui = {
    ensureStyle,
    applyHighlightToDom,
    clearReplacements,
    attachClickListener,
    attachFeedbackListener,
    setPopupModulePrefs,
    setDebugEnabled,
    setFeedbackSoundEnabled
  };
})();
