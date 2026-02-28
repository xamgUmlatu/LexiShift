(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createSyncHelpers(context) {
    const ctx = context && typeof context === "object" ? context : {};
    const settingsManager = ctx.settingsManager && typeof ctx.settingsManager === "object"
      ? ctx.settingsManager
      : null;
    const isObject = typeof ctx.isObject === "function"
      ? ctx.isObject
      : ((value) => Boolean(value) && typeof value === "object" && !Array.isArray(value));
    const normalizePath = typeof ctx.normalizePath === "function"
      ? ctx.normalizePath
      : ((value) => String(value || "").trim());
    const renderSrsPairItems = typeof ctx.renderSrsPairItems === "function"
      ? ctx.renderSrsPairItems
      : (() => {});
    const renderRulesetItems = typeof ctx.renderRulesetItems === "function"
      ? ctx.renderRulesetItems
      : (() => {});
    const renderModuleItems = typeof ctx.renderModuleItems === "function"
      ? ctx.renderModuleItems
      : (() => {});
    const applyExportModeUI = typeof ctx.applyExportModeUI === "function"
      ? ctx.applyExportModeUI
      : (() => {});
    const updateAllParentStates = typeof ctx.updateAllParentStates === "function"
      ? ctx.updateAllParentStates
      : (() => {});
    const updateSummary = typeof ctx.updateSummary === "function"
      ? ctx.updateSummary
      : (() => {});
    const setCurrentProfileId = typeof ctx.setCurrentProfileId === "function"
      ? ctx.setCurrentProfileId
      : (() => {});
    const getDynamicSrsPairIds = typeof ctx.getDynamicSrsPairIds === "function"
      ? ctx.getDynamicSrsPairIds
      : (() => []);
    const getDynamicRulesetIds = typeof ctx.getDynamicRulesetIds === "function"
      ? ctx.getDynamicRulesetIds
      : (() => []);
    const getDynamicModuleIds = typeof ctx.getDynamicModuleIds === "function"
      ? ctx.getDynamicModuleIds
      : (() => []);

    async function syncForProfile(optionsArg) {
      if (!settingsManager) {
        return null;
      }
      const options = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const items = isObject(options.items) ? options.items : await settingsManager.load();
      const selectedProfileId = options.profileId !== undefined
        ? options.profileId
        : (settingsManager.getSelectedSrsProfileId
          ? settingsManager.getSelectedSrsProfileId(items)
          : "default");
      const profileId = settingsManager && typeof settingsManager.normalizeSrsProfileId === "function"
        ? settingsManager.normalizeSrsProfileId(selectedProfileId)
        : (String(selectedProfileId || "").trim() || "default");
      const profilesRoot = isObject(items.srsProfiles) ? items.srsProfiles : {};
      const profileEntry = isObject(profilesRoot[profileId]) ? profilesRoot[profileId] : {};
      const manualStateRoot = isObject(profileEntry.manualRulesets) ? profileEntry.manualRulesets : {};
      const manualState = {
        order: Array.isArray(manualStateRoot.order)
          ? manualStateRoot.order
          : [],
        enabledByPath: isObject(manualStateRoot.enabledByPath)
          ? manualStateRoot.enabledByPath
          : {}
      };
      const cacheRaw = isObject(items.manualRulesetCacheByPath) ? items.manualRulesetCacheByPath : {};
      const cache = {};
      Object.entries(cacheRaw).forEach(([cachePath, cacheEntry]) => {
        const key = normalizePath(cachePath);
        if (!key || !isObject(cacheEntry)) {
          return;
        }
        cache[key] = {
          rules: Array.isArray(cacheEntry.rules) ? cacheEntry.rules : [],
          rulesCount: Number.isFinite(Number(cacheEntry.rulesCount))
            ? Number(cacheEntry.rulesCount)
            : (Array.isArray(cacheEntry.rules) ? cacheEntry.rules.length : 0),
          displayPath: normalizePath(cacheEntry.displayPath) || key
        };
      });

      setCurrentProfileId(profileId);
      renderSrsPairItems(items, profileId);
      renderRulesetItems(profileId, manualState, cache);
      renderModuleItems(items, profileId);
      applyExportModeUI();
      updateAllParentStates();
      updateSummary();
      return {
        profileId,
        srsPairLeafIds: [...getDynamicSrsPairIds()],
        rulesetLeafIds: [...getDynamicRulesetIds()],
        moduleLeafIds: [...getDynamicModuleIds()]
      };
    }

    return {
      syncForProfile
    };
  }

  root.optionsShareCenterSync = {
    createSyncHelpers
  };
})();
