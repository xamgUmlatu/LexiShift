(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createHelpers(options = {}) {
    const getRegistry = typeof options.getRegistry === "function"
      ? options.getRegistry
      : (() => null);
    const translate = typeof options.translate === "function"
      ? options.translate
      : ((key, _subs, fallback) => String(fallback || key || ""));
    const getActiveModulePrefs = typeof options.getActiveModulePrefs === "function"
      ? options.getActiveModulePrefs
      : (() => ({ byId: {}, order: [] }));

    function normalizeLanguage(value) {
      return String(value || "").trim().toLowerCase();
    }

    function supportsTargetLanguage(value) {
      const language = normalizeLanguage(value);
      const registry = getRegistry();
      if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
        return language === "ja";
      }
      const visibleModules = registry.resolveVisibleSettingModules(language);
      return Array.isArray(visibleModules) && visibleModules.length > 0;
    }

    function getVisibleModules(language) {
      const registry = getRegistry();
      if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
        return [];
      }
      const visible = registry.resolveVisibleSettingModules(language);
      return Array.isArray(visible) ? visible : [];
    }

    function toFiniteNumber(value) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }

    function getThemeLimits() {
      const registry = getRegistry();
      if (registry && typeof registry.resolveModuleThemeLimits === "function") {
        return registry.resolveModuleThemeLimits();
      }
      return {
        hueDeg: { min: -180, max: 180, step: 1, defaultValue: 0 },
        saturationPercent: { min: 70, max: 450, step: 1, defaultValue: 100 },
        brightnessPercent: { min: 80, max: 200, step: 1, defaultValue: 100 },
        transparencyPercent: { min: 40, max: 100, step: 1, defaultValue: 100 }
      };
    }

    function getThemeDefaults() {
      const registry = getRegistry();
      if (registry && typeof registry.resolveModuleThemeDefaults === "function") {
        return registry.resolveModuleThemeDefaults();
      }
      const limits = getThemeLimits();
      return {
        hueDeg: Number(limits.hueDeg.defaultValue || 0),
        saturationPercent: Number(limits.saturationPercent.defaultValue || 100),
        brightnessPercent: Number(limits.brightnessPercent.defaultValue || 100),
        transparencyPercent: Number(limits.transparencyPercent.defaultValue || 100)
      };
    }

    function normalizeTheme(theme, fallbackTheme) {
      const registry = getRegistry();
      if (registry && typeof registry.normalizeModuleThemeConfig === "function") {
        return registry.normalizeModuleThemeConfig(theme, fallbackTheme);
      }
      const limits = getThemeLimits();
      const fallback = fallbackTheme && typeof fallbackTheme === "object"
        ? fallbackTheme
        : getThemeDefaults();
      function normalizeValue(limit, value, fallbackValue) {
        const lower = toFiniteNumber(limit.min);
        const upper = toFiniteNumber(limit.max);
        const defaultValue = toFiniteNumber(limit.defaultValue);
        const resolvedFallback = toFiniteNumber(fallbackValue);
        const parsed = Number.parseInt(value, 10);
        const base = Number.isFinite(parsed)
          ? parsed
          : (
              resolvedFallback !== null
                ? resolvedFallback
                : (defaultValue !== null ? defaultValue : 0)
            );
        const boundedLow = lower !== null ? Math.max(lower, base) : base;
        return upper !== null ? Math.min(upper, boundedLow) : boundedLow;
      }
      const source = theme && typeof theme === "object" ? theme : {};
      return {
        hueDeg: normalizeValue(limits.hueDeg, source.hueDeg, fallback.hueDeg),
        saturationPercent: normalizeValue(
          limits.saturationPercent,
          source.saturationPercent,
          fallback.saturationPercent
        ),
        brightnessPercent: normalizeValue(
          limits.brightnessPercent,
          source.brightnessPercent,
          fallback.brightnessPercent
        ),
        transparencyPercent: normalizeValue(
          limits.transparencyPercent,
          source.transparencyPercent,
          fallback.transparencyPercent
        )
      };
    }

    function supportsThemeTuning(definition) {
      if (!definition || !definition.id) {
        return false;
      }
      const registry = getRegistry();
      if (registry && typeof registry.supportsThemeTuning === "function") {
        return registry.supportsThemeTuning(definition.id);
      }
      return definition.themeEnabled === true;
    }

    function cloneModulePrefs(modulePrefs) {
      const source = modulePrefs && typeof modulePrefs === "object" ? modulePrefs : {};
      const byId = source.byId && typeof source.byId === "object" ? source.byId : {};
      const nextById = {};
      for (const [key, value] of Object.entries(byId)) {
        const entry = value && typeof value === "object" ? value : {};
        nextById[key] = {
          ...entry,
          config: entry.config && typeof entry.config === "object" ? { ...entry.config } : undefined
        };
      }
      const order = Array.isArray(source.order)
        ? source.order.map((moduleId) => String(moduleId || "").trim()).filter(Boolean)
        : [];
      return { byId: nextById, order };
    }

    function ensureModuleEntry(modulePrefs, moduleId) {
      if (!modulePrefs.byId || typeof modulePrefs.byId !== "object") {
        modulePrefs.byId = {};
      }
      if (!modulePrefs.byId[moduleId] || typeof modulePrefs.byId[moduleId] !== "object") {
        modulePrefs.byId[moduleId] = { enabled: true };
      }
      return modulePrefs.byId[moduleId];
    }

    function resolveModuleCardDefinitions(visibleModules) {
      if (!Array.isArray(visibleModules)) {
        return [];
      }
      return visibleModules.filter((definition) => definition && definition.id !== "ja-primary-display-script");
    }

    function normalizeCardModuleOrder(orderIds, definitions) {
      const ordered = [];
      const seen = new Set();
      const definitionIds = Array.isArray(definitions)
        ? definitions.map((definition) => String(definition && definition.id || "").trim()).filter(Boolean)
        : [];
      const allowed = new Set(definitionIds);
      const sourceIds = Array.isArray(orderIds) ? orderIds : [];
      for (const rawId of sourceIds) {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || !allowed.has(moduleId) || seen.has(moduleId)) {
          continue;
        }
        seen.add(moduleId);
        ordered.push(moduleId);
      }
      for (const moduleId of definitionIds) {
        if (seen.has(moduleId)) {
          continue;
        }
        seen.add(moduleId);
        ordered.push(moduleId);
      }
      return ordered;
    }

    function resolveOrderedCardDefinitions(visibleModules, modulePrefs) {
      const cardDefinitions = resolveModuleCardDefinitions(visibleModules);
      const definitionsById = new Map(
        cardDefinitions.map((definition) => [String(definition.id || "").trim(), definition])
      );
      const normalizedOrder = normalizeCardModuleOrder(
        modulePrefs && typeof modulePrefs === "object" ? modulePrefs.order : null,
        cardDefinitions
      );
      return normalizedOrder
        .map((moduleId) => definitionsById.get(moduleId))
        .filter((definition) => Boolean(definition));
    }

    function getModuleLabel(definition) {
      return translate(
        definition.labelKey,
        null,
        definition.labelFallback || definition.id
      );
    }

    function getModuleDescription(definition) {
      if (!definition) {
        return "";
      }
      const fallback = String(definition.descriptionFallback || "").trim();
      const key = String(definition.descriptionKey || "").trim();
      if (!key && !fallback) {
        return "";
      }
      return translate(key, null, fallback);
    }

    function getToggleStateLabel(enabled) {
      return translate(
        enabled ? "module_toggle_on" : "module_toggle_off",
        null,
        enabled ? "On" : "Off"
      );
    }

    function getThemeSliderDefinitions() {
      const limits = getThemeLimits();
      return [
        {
          key: "hueDeg",
          field: "config.theme.hueDeg",
          labelKey: "label_profile_card_theme_hue",
          labelFallback: "Hue",
          suffix: "°",
          limit: limits.hueDeg
        },
        {
          key: "saturationPercent",
          field: "config.theme.saturationPercent",
          labelKey: "label_profile_card_theme_saturation",
          labelFallback: "Saturation",
          suffix: "%",
          limit: limits.saturationPercent
        },
        {
          key: "brightnessPercent",
          field: "config.theme.brightnessPercent",
          labelKey: "label_profile_card_theme_brightness",
          labelFallback: "Brightness",
          suffix: "%",
          limit: limits.brightnessPercent
        },
        {
          key: "transparencyPercent",
          field: "config.theme.transparencyPercent",
          labelKey: "label_profile_card_theme_transparency",
          labelFallback: "Transparency",
          suffix: "%",
          limit: limits.transparencyPercent
        }
      ];
    }

    function formatThemeValue(key, value) {
      const numeric = Number.parseInt(value, 10);
      if (!Number.isFinite(numeric)) {
        return "";
      }
      if (key === "hueDeg") {
        return `${numeric}°`;
      }
      return `${numeric}%`;
    }

    function resolveEntryTheme(entry) {
      const config = entry && entry.config && typeof entry.config === "object"
        ? entry.config
        : {};
      return normalizeTheme(config.theme, getThemeDefaults());
    }

    function buildThemePreviewFilter(theme) {
      const normalized = normalizeTheme(theme, getThemeDefaults());
      const saturation = Math.max(0, normalized.saturationPercent / 100);
      const brightness = Math.max(0, normalized.brightnessPercent / 100);
      const opacity = Math.max(0, Math.min(1, normalized.transparencyPercent / 100));
      return `hue-rotate(${normalized.hueDeg}deg) saturate(${saturation}) brightness(${brightness}) opacity(${opacity})`;
    }

    function getModuleEntryById(moduleId) {
      const normalizedId = String(moduleId || "").trim();
      if (!normalizedId) {
        return {};
      }
      const activeModulePrefs = getActiveModulePrefs();
      const byId = activeModulePrefs && typeof activeModulePrefs === "object"
        && activeModulePrefs.byId
        && typeof activeModulePrefs.byId === "object"
        ? activeModulePrefs.byId
        : {};
      const entry = byId[normalizedId];
      return entry && typeof entry === "object" ? entry : {};
    }

    function resolveThemeFromCardInputs(moduleId, card) {
      const entry = getModuleEntryById(moduleId);
      const fallbackTheme = resolveEntryTheme(entry);
      if (!(card instanceof HTMLElement)) {
        return fallbackTheme;
      }
      const nextTheme = { ...fallbackTheme };
      for (const sliderDef of getThemeSliderDefinitions()) {
        const slider = card.querySelector(
          `input[type="range"][data-module-id="${moduleId}"][data-theme-key="${sliderDef.key}"]`
        );
        if (slider instanceof HTMLInputElement) {
          nextTheme[sliderDef.key] = Number.parseInt(slider.value, 10);
        }
      }
      return normalizeTheme(nextTheme, fallbackTheme);
    }

    function applyThemePreviewToCard(card, theme) {
      if (!(card instanceof HTMLElement)) {
        return;
      }
      const filterValue = buildThemePreviewFilter(theme);
      const swatch = card.querySelector(".language-module-color-trigger-swatch");
      if (swatch instanceof HTMLElement) {
        swatch.style.filter = filterValue;
      }
      const panel = card.querySelector(".language-module-color-panel");
      if (panel instanceof HTMLElement) {
        panel.style.filter = filterValue;
      }
    }

    return {
      normalizeLanguage,
      supportsTargetLanguage,
      getVisibleModules,
      getThemeLimits,
      getThemeDefaults,
      normalizeTheme,
      supportsThemeTuning,
      cloneModulePrefs,
      ensureModuleEntry,
      resolveModuleCardDefinitions,
      normalizeCardModuleOrder,
      resolveOrderedCardDefinitions,
      getModuleLabel,
      getModuleDescription,
      getToggleStateLabel,
      getThemeSliderDefinitions,
      formatThemeValue,
      resolveEntryTheme,
      buildThemePreviewFilter,
      getModuleEntryById,
      resolveThemeFromCardInputs,
      applyThemePreviewToCard
    };
  }

  root.optionsTargetLanguageModalUtils = {
    createHelpers
  };
})();
