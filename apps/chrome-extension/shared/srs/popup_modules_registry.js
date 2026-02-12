(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const SCRIPT_VALUES = new Set(["kanji", "kana", "romaji"]);

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
      targetLanguages: ["ja"],
      labelKey: "module_ja_script_forms",
      labelFallback: "Japanese script forms",
      descriptionKey: "module_ja_script_forms_desc",
      descriptionFallback: "Show alternate Japanese scripts in the popup."
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
      targetLanguages: null,
      labelKey: "module_feedback_history",
      labelFallback: "Feedback history",
      descriptionKey: "module_feedback_history_desc",
      descriptionFallback: "Store and display your SRS rating history for this word."
    },
    {
      id: "encounter-history",
      control: "toggle",
      defaultEnabled: true,
      targetLanguages: null,
      labelKey: "module_encounter_history",
      labelFallback: "Encounter history",
      descriptionKey: "module_encounter_history_desc",
      descriptionFallback: "Track encounter counts and the latest sentence excerpt."
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
    return merged;
  }

  function normalizeModulePrefs(rawPrefs, options) {
    const opts = options && typeof options === "object" ? options : {};
    const fallback = opts.fallback && typeof opts.fallback === "object" ? opts.fallback : {};
    const rawById = rawPrefs && typeof rawPrefs === "object" && rawPrefs.byId && typeof rawPrefs.byId === "object"
      ? rawPrefs.byId
      : {};
    const fallbackById = fallback.byId && typeof fallback.byId === "object" ? fallback.byId : {};

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
    return { byId: normalizedById };
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
    normalizePrimaryDisplayScript
  };
})();
