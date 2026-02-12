(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const FALLBACK_CARD_THEME_LIMITS = Object.freeze({
    hueDeg: Object.freeze({
      min: -180,
      max: 180,
      step: 1,
      defaultValue: 0
    }),
    saturationPercent: Object.freeze({
      min: 70,
      max: 140,
      step: 1,
      defaultValue: 100
    }),
    brightnessPercent: Object.freeze({
      min: 80,
      max: 125,
      step: 1,
      defaultValue: 100
    })
  });

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function toFiniteNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function resolveCardThemeLimits() {
    const profileUiTheme = root.profileUiTheme && isObject(root.profileUiTheme)
      ? root.profileUiTheme
      : {};
    const configured = profileUiTheme.CARD_THEME_LIMITS && isObject(profileUiTheme.CARD_THEME_LIMITS)
      ? profileUiTheme.CARD_THEME_LIMITS
      : {};
    const hueDeg = configured.hueDeg && isObject(configured.hueDeg)
      ? configured.hueDeg
      : FALLBACK_CARD_THEME_LIMITS.hueDeg;
    const saturationPercent = configured.saturationPercent && isObject(configured.saturationPercent)
      ? configured.saturationPercent
      : FALLBACK_CARD_THEME_LIMITS.saturationPercent;
    const brightnessPercent = configured.brightnessPercent && isObject(configured.brightnessPercent)
      ? configured.brightnessPercent
      : FALLBACK_CARD_THEME_LIMITS.brightnessPercent;
    return {
      hueDeg,
      saturationPercent,
      brightnessPercent
    };
  }

  function clampThemeValue(limit, value, fallback) {
    const lower = toFiniteNumber(limit.min);
    const upper = toFiniteNumber(limit.max);
    const defaultValue = toFiniteNumber(limit.defaultValue);
    const resolvedFallback = toFiniteNumber(fallback);
    const parsed = Number.parseInt(value, 10);
    const base = Number.isFinite(parsed)
      ? parsed
      : (resolvedFallback !== null ? resolvedFallback : (defaultValue !== null ? defaultValue : 0));
    const boundedLow = lower !== null ? Math.max(lower, base) : base;
    return upper !== null ? Math.min(upper, boundedLow) : boundedLow;
  }

  function resolveCardThemeDefaults(options) {
    const opts = isObject(options) ? options : {};
    const rawDefaults = isObject(opts.defaults) ? opts.defaults : {};
    const limits = resolveCardThemeLimits();
    const hueRaw = rawDefaults.cardThemeHueDeg !== undefined
      ? rawDefaults.cardThemeHueDeg
      : rawDefaults.hueDeg;
    const saturationRaw = rawDefaults.cardThemeSaturationPercent !== undefined
      ? rawDefaults.cardThemeSaturationPercent
      : rawDefaults.saturationPercent;
    const brightnessRaw = rawDefaults.cardThemeBrightnessPercent !== undefined
      ? rawDefaults.cardThemeBrightnessPercent
      : rawDefaults.brightnessPercent;
    return {
      hueDeg: clampThemeValue(limits.hueDeg, hueRaw, limits.hueDeg.defaultValue),
      saturationPercent: clampThemeValue(
        limits.saturationPercent,
        saturationRaw,
        limits.saturationPercent.defaultValue
      ),
      brightnessPercent: clampThemeValue(
        limits.brightnessPercent,
        brightnessRaw,
        limits.brightnessPercent.defaultValue
      )
    };
  }

  function clampCardThemeHueDeg(value, fallback) {
    const limits = resolveCardThemeLimits();
    return clampThemeValue(limits.hueDeg, value, fallback);
  }

  function clampCardThemeSaturationPercent(value, fallback) {
    const limits = resolveCardThemeLimits();
    return clampThemeValue(limits.saturationPercent, value, fallback);
  }

  function clampCardThemeBrightnessPercent(value, fallback) {
    const limits = resolveCardThemeLimits();
    return clampThemeValue(limits.brightnessPercent, value, fallback);
  }

  function resolveValue(raw, fallback, directKey, alternateKey) {
    if (raw && raw[directKey] !== undefined) {
      return raw[directKey];
    }
    if (alternateKey && raw && raw[alternateKey] !== undefined) {
      return raw[alternateKey];
    }
    if (fallback && fallback[directKey] !== undefined) {
      return fallback[directKey];
    }
    if (alternateKey && fallback && fallback[alternateKey] !== undefined) {
      return fallback[alternateKey];
    }
    return undefined;
  }

  function normalizeCardThemePrefs(rawPrefs, options) {
    const raw = isObject(rawPrefs) ? rawPrefs : {};
    const opts = isObject(options) ? options : {};
    const fallback = isObject(opts.fallback) ? opts.fallback : {};
    const defaults = resolveCardThemeDefaults({
      defaults: opts.defaults
    });
    const hueValue = resolveValue(raw, fallback, "cardThemeHueDeg", "hueDeg");
    const saturationValue = resolveValue(raw, fallback, "cardThemeSaturationPercent", "saturationPercent");
    const brightnessValue = resolveValue(raw, fallback, "cardThemeBrightnessPercent", "brightnessPercent");
    return {
      cardThemeHueDeg: clampCardThemeHueDeg(hueValue, defaults.hueDeg),
      cardThemeSaturationPercent: clampCardThemeSaturationPercent(saturationValue, defaults.saturationPercent),
      cardThemeBrightnessPercent: clampCardThemeBrightnessPercent(brightnessValue, defaults.brightnessPercent)
    };
  }

  function toTransformValues(rawPrefs, options) {
    const normalized = normalizeCardThemePrefs(rawPrefs, options);
    return {
      hueDeg: normalized.cardThemeHueDeg,
      saturationPercent: normalized.cardThemeSaturationPercent,
      brightnessPercent: normalized.cardThemeBrightnessPercent
    };
  }

  root.profileUiThemePrefs = {
    resolveCardThemeLimits,
    resolveCardThemeDefaults,
    clampCardThemeHueDeg,
    clampCardThemeSaturationPercent,
    clampCardThemeBrightnessPercent,
    normalizeCardThemePrefs,
    toTransformValues
  };
})();
