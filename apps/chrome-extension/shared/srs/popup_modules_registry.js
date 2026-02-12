(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const SCRIPT_VALUES = new Set(["kanji", "kana", "romaji"]);
  const MODULE_THEME_LIMITS = Object.freeze({
    hueDeg: Object.freeze({
      min: -180,
      max: 180,
      step: 1,
      defaultValue: 0
    }),
    saturationPercent: Object.freeze({
      min: 70,
      max: 450,
      step: 1,
      defaultValue: 100
    }),
    brightnessPercent: Object.freeze({
      min: 80,
      max: 200,
      step: 1,
      defaultValue: 100
    }),
    transparencyPercent: Object.freeze({
      min: 40,
      max: 100,
      step: 1,
      defaultValue: 100
    })
  });
  const MODULE_THEME_DEFAULTS = Object.freeze({
    hueDeg: MODULE_THEME_LIMITS.hueDeg.defaultValue,
    saturationPercent: MODULE_THEME_LIMITS.saturationPercent.defaultValue,
    brightnessPercent: MODULE_THEME_LIMITS.brightnessPercent.defaultValue,
    transparencyPercent: MODULE_THEME_LIMITS.transparencyPercent.defaultValue
  });

  const MODULE_DEFINITIONS = [
    {
      id: "feedback-core",
      control: "hidden",
      defaultEnabled: true,
      targetLanguages: null,
      runtimeOnly: true
    },
    {
      id: "ja-script-forms",
      control: "toggle",
      defaultEnabled: true,
      themeEnabled: true,
      targetLanguages: ["ja"],
      labelKey: "module_ja_script_forms",
      labelFallback: "Japanese script forms",
      descriptionKey: "module_ja_script_forms_desc",
      descriptionFallback: "Show alternate Japanese scripts in the popup.",
      defaultConfig: {
        theme: MODULE_THEME_DEFAULTS
      }
    },
    {
      id: "ja-primary-display-script",
      control: "select",
      defaultEnabled: true,
      targetLanguages: ["ja"],
      labelKey: "module_ja_primary_display_script",
      labelFallback: "Primary display script",
      options: [
        {
          value: "kanji",
          labelKey: "option_ja_script_kanji",
          labelFallback: "Kanji"
        },
        {
          value: "kana",
          labelKey: "option_ja_script_kana",
          labelFallback: "Kana"
        },
        {
          value: "romaji",
          labelKey: "option_ja_script_romaji",
          labelFallback: "Romaji"
        }
      ],
      defaultConfig: {
        primary: "kanji"
      }
    },
    {
      id: "feedback-history",
      control: "toggle",
      defaultEnabled: true,
      themeEnabled: true,
      targetLanguages: null,
      labelKey: "module_feedback_history",
      labelFallback: "Feedback history",
      descriptionKey: "module_feedback_history_desc",
      descriptionFallback: "Store and display your SRS rating history for this word.",
      defaultConfig: {
        theme: MODULE_THEME_DEFAULTS
      }
    },
    {
      id: "encounter-history",
      control: "toggle",
      defaultEnabled: true,
      themeEnabled: true,
      targetLanguages: null,
      labelKey: "module_encounter_history",
      labelFallback: "Encounter history",
      descriptionKey: "module_encounter_history_desc",
      descriptionFallback: "Track encounter counts and the latest sentence excerpt.",
      defaultConfig: {
        theme: MODULE_THEME_DEFAULTS
      }
    }
  ];

  function normalizeLanguage(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizePrimaryDisplayScript(value, fallback) {
    const candidate = String(value || "").trim().toLowerCase();
    if (SCRIPT_VALUES.has(candidate)) {
      return candidate;
    }
    const fallbackValue = String(fallback || "").trim().toLowerCase();
    if (SCRIPT_VALUES.has(fallbackValue)) {
      return fallbackValue;
    }
    return "kanji";
  }

  function toFiniteNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function normalizeThemeValue(limit, value, fallback) {
    const lower = toFiniteNumber(limit && limit.min);
    const upper = toFiniteNumber(limit && limit.max);
    const defaultValue = toFiniteNumber(limit && limit.defaultValue);
    const resolvedFallback = toFiniteNumber(fallback);
    const parsed = Number.parseInt(value, 10);
    const base = Number.isFinite(parsed)
      ? parsed
      : (
          resolvedFallback !== null
            ? resolvedFallback
            : (defaultValue !== null ? defaultValue : 0)
        );
    const lowerBounded = lower !== null ? Math.max(lower, base) : base;
    return upper !== null ? Math.min(upper, lowerBounded) : lowerBounded;
  }

  function normalizeModuleThemeConfig(rawTheme, fallbackTheme) {
    const raw = rawTheme && typeof rawTheme === "object" ? rawTheme : {};
    const fallback = fallbackTheme && typeof fallbackTheme === "object"
      ? fallbackTheme
      : MODULE_THEME_DEFAULTS;
    return {
      hueDeg: normalizeThemeValue(
        MODULE_THEME_LIMITS.hueDeg,
        raw.hueDeg,
        fallback.hueDeg
      ),
      saturationPercent: normalizeThemeValue(
        MODULE_THEME_LIMITS.saturationPercent,
        raw.saturationPercent,
        fallback.saturationPercent
      ),
      brightnessPercent: normalizeThemeValue(
        MODULE_THEME_LIMITS.brightnessPercent,
        raw.brightnessPercent,
        fallback.brightnessPercent
      ),
      transparencyPercent: normalizeThemeValue(
        MODULE_THEME_LIMITS.transparencyPercent,
        raw.transparencyPercent,
        fallback.transparencyPercent
      )
    };
  }

  function getModuleDefinitions() {
    return MODULE_DEFINITIONS.slice();
  }

  function getModuleDefinition(moduleId) {
    const normalized = String(moduleId || "").trim();
    if (!normalized) {
      return null;
    }
    return MODULE_DEFINITIONS.find((def) => def.id === normalized) || null;
  }

  function supportsTargetLanguage(moduleDef, targetLanguage) {
    if (!moduleDef || !Array.isArray(moduleDef.targetLanguages) || !moduleDef.targetLanguages.length) {
      return true;
    }
    const normalizedTarget = normalizeLanguage(targetLanguage);
    return moduleDef.targetLanguages.includes(normalizedTarget);
  }

  function cloneConfig(config, defaultConfig) {
    const base = defaultConfig && typeof defaultConfig === "object" ? defaultConfig : {};
    const source = config && typeof config === "object" ? config : {};
    const merged = { ...base, ...source };
    if (Object.prototype.hasOwnProperty.call(merged, "primary")) {
      merged.primary = normalizePrimaryDisplayScript(merged.primary, base.primary || "kanji");
    }
    if (Object.prototype.hasOwnProperty.call(base, "theme")
      || Object.prototype.hasOwnProperty.call(source, "theme")
      || Object.prototype.hasOwnProperty.call(merged, "theme")) {
      merged.theme = normalizeModuleThemeConfig(source.theme, base.theme);
    }
    return merged;
  }

  function resolveOrderableModuleIds() {
    return MODULE_DEFINITIONS
      .filter((definition) => {
        if (!definition || definition.runtimeOnly === true) {
          return false;
        }
        return definition.control !== "hidden";
      })
      .map((definition) => String(definition.id || "").trim())
      .filter((moduleId) => moduleId.length > 0);
  }

  function normalizeModuleOrder(rawOrder, fallbackOrder, allowedModuleIds) {
    const allowed = new Set(
      Array.isArray(allowedModuleIds)
        ? allowedModuleIds.map((moduleId) => String(moduleId || "").trim()).filter(Boolean)
        : []
    );
    const normalized = [];
    const seen = new Set();
    function append(source) {
      if (!Array.isArray(source)) {
        return;
      }
      for (const rawId of source) {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || !allowed.has(moduleId) || seen.has(moduleId)) {
          continue;
        }
        seen.add(moduleId);
        normalized.push(moduleId);
      }
    }
    append(rawOrder);
    append(fallbackOrder);
    append(Array.from(allowed));
    return normalized;
  }

  function normalizeModulePrefs(rawPrefs, options) {
    const opts = options && typeof options === "object" ? options : {};
    const fallback = opts.fallback && typeof opts.fallback === "object" ? opts.fallback : {};
    const rawById = rawPrefs && typeof rawPrefs === "object" && rawPrefs.byId && typeof rawPrefs.byId === "object"
      ? rawPrefs.byId
      : {};
    const fallbackById = fallback.byId && typeof fallback.byId === "object" ? fallback.byId : {};
    const orderableIds = resolveOrderableModuleIds();
    const rawOrder = rawPrefs && typeof rawPrefs === "object" ? rawPrefs.order : null;
    const fallbackOrder = fallback.order;

    const normalizedById = {};
    for (const definition of MODULE_DEFINITIONS) {
      const rawEntry = rawById[definition.id] && typeof rawById[definition.id] === "object"
        ? rawById[definition.id]
        : {};
      const fallbackEntry = fallbackById[definition.id] && typeof fallbackById[definition.id] === "object"
        ? fallbackById[definition.id]
        : {};
      const enabled = rawEntry.enabled !== undefined
        ? rawEntry.enabled === true
        : (
            fallbackEntry.enabled !== undefined
              ? fallbackEntry.enabled === true
              : definition.defaultEnabled !== false
          );
      const normalizedEntry = { enabled };
      if (definition.defaultConfig && typeof definition.defaultConfig === "object") {
        normalizedEntry.config = cloneConfig(
          rawEntry.config,
          cloneConfig(fallbackEntry.config, definition.defaultConfig)
        );
      }
      normalizedById[definition.id] = normalizedEntry;
    }
    return {
      byId: normalizedById,
      order: normalizeModuleOrder(rawOrder, fallbackOrder, orderableIds)
    };
  }

  function isEnabledForTarget(modulePrefs, moduleId, targetLanguage) {
    const definition = getModuleDefinition(moduleId);
    if (!definition || !supportsTargetLanguage(definition, targetLanguage)) {
      return false;
    }
    const normalized = normalizeModulePrefs(modulePrefs, {});
    const entry = normalized.byId && normalized.byId[moduleId] && typeof normalized.byId[moduleId] === "object"
      ? normalized.byId[moduleId]
      : null;
    if (!entry) {
      return definition.defaultEnabled !== false;
    }
    return entry.enabled !== false;
  }

  function resolveVisibleSettingModules(targetLanguage) {
    return MODULE_DEFINITIONS.filter((definition) => {
      if (!definition || definition.runtimeOnly === true) {
        return false;
      }
      if (definition.control === "hidden") {
        return false;
      }
      return supportsTargetLanguage(definition, targetLanguage);
    });
  }

  function supportsThemeTuning(moduleId) {
    const definition = getModuleDefinition(moduleId);
    return Boolean(definition && definition.themeEnabled === true);
  }

  function resolveModuleThemeLimits() {
    return MODULE_THEME_LIMITS;
  }

  function resolveModuleThemeDefaults() {
    return {
      hueDeg: MODULE_THEME_DEFAULTS.hueDeg,
      saturationPercent: MODULE_THEME_DEFAULTS.saturationPercent,
      brightnessPercent: MODULE_THEME_DEFAULTS.brightnessPercent,
      transparencyPercent: MODULE_THEME_DEFAULTS.transparencyPercent
    };
  }

  function resolveTargetDisplayScript(modulePrefs, targetLanguage) {
    const target = normalizeLanguage(targetLanguage);
    if (target !== "ja") {
      return "kanji";
    }
    const normalized = normalizeModulePrefs(modulePrefs, {});
    const entry = normalized.byId["ja-primary-display-script"] || {};
    const config = entry.config && typeof entry.config === "object" ? entry.config : {};
    return normalizePrimaryDisplayScript(config.primary, "kanji");
  }

  root.popupModulesRegistry = {
    getModuleDefinitions,
    getModuleDefinition,
    supportsTargetLanguage,
    normalizeModulePrefs,
    isEnabledForTarget,
    resolveVisibleSettingModules,
    resolveTargetDisplayScript,
    normalizePrimaryDisplayScript,
    supportsThemeTuning,
    normalizeModuleThemeConfig,
    resolveModuleThemeLimits,
    resolveModuleThemeDefaults
  };
})();
