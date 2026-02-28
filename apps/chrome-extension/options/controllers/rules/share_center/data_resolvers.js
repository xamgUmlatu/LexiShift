(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resolveProfileModules(context, items, profileId) {
    const ctx = context && typeof context === "object" ? context : {};
    const settingsManager = ctx.settingsManager;
    const translate = typeof ctx.translate === "function" ? ctx.translate : ((key, _subs, fallback) => fallback || key || "");
    const labels = ctx.labels && typeof ctx.labels === "object" ? ctx.labels : {};
    const getPopupModulesRegistry = typeof ctx.getPopupModulesRegistry === "function"
      ? ctx.getPopupModulesRegistry
      : (() => null);
    const isObject = typeof ctx.isObject === "function"
      ? ctx.isObject
      : ((value) => Boolean(value) && typeof value === "object" && !Array.isArray(value));

    const languagePrefs = settingsManager && typeof settingsManager.getProfileLanguagePrefs === "function"
      ? settingsManager.getProfileLanguagePrefs(items, { profileId })
      : { targetLanguage: "en" };
    const targetLanguage = String(languagePrefs && languagePrefs.targetLanguage || "en").trim() || "en";
    const modulePrefs = settingsManager && typeof settingsManager.getProfileModulePrefs === "function"
      ? settingsManager.getProfileModulePrefs(items, { profileId, targetLanguage })
      : { byId: {}, order: [] };
    const byId = isObject(modulePrefs && modulePrefs.byId) ? modulePrefs.byId : {};
    const prefsOrder = Array.isArray(modulePrefs && modulePrefs.order) ? modulePrefs.order : [];

    const registry = getPopupModulesRegistry();
    if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
      const fallbackOrder = [];
      const fallbackSeen = new Set();
      prefsOrder.forEach((rawId) => {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || fallbackSeen.has(moduleId)) {
          return;
        }
        fallbackSeen.add(moduleId);
        fallbackOrder.push(moduleId);
      });
      Object.keys(byId).forEach((rawId) => {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || fallbackSeen.has(moduleId)) {
          return;
        }
        fallbackSeen.add(moduleId);
        fallbackOrder.push(moduleId);
      });
      return {
        targetLanguage,
        modules: fallbackOrder.map((moduleId) => {
          const prefsEntry = isObject(byId[moduleId]) ? byId[moduleId] : {};
          return {
            moduleId,
            label: moduleId,
            description: "",
            enabledInProfile: prefsEntry.enabled !== false
          };
        })
      };
    }

    const visibleDefinitionsRaw = registry.resolveVisibleSettingModules(targetLanguage);
    const visibleDefinitions = Array.isArray(visibleDefinitionsRaw) ? visibleDefinitionsRaw : [];
    const definitionsById = new Map();
    visibleDefinitions.forEach((definition) => {
      const moduleId = String(definition && definition.id || "").trim();
      if (!moduleId) {
        return;
      }
      definitionsById.set(moduleId, definition);
    });

    const order = [];
    const seen = new Set();
    prefsOrder.forEach((rawId) => {
      const moduleId = String(rawId || "").trim();
      if (!moduleId || seen.has(moduleId)) {
        return;
      }
      seen.add(moduleId);
      order.push(moduleId);
    });
    Object.keys(byId).forEach((rawId) => {
      const moduleId = String(rawId || "").trim();
      if (!moduleId || seen.has(moduleId)) {
        return;
      }
      seen.add(moduleId);
      order.push(moduleId);
    });
    visibleDefinitions.forEach((definition) => {
      const moduleId = String(definition && definition.id || "").trim();
      if (!moduleId || seen.has(moduleId)) {
        return;
      }
      seen.add(moduleId);
      order.push(moduleId);
    });

    const modules = order.map((moduleId) => {
      const definition = definitionsById.get(moduleId) || {};
      const prefsEntry = isObject(byId[moduleId]) ? byId[moduleId] : {};
      const moduleEnabled = prefsEntry.enabled !== false;
      const label = translate(
        String(definition.labelKey || ""),
        null,
        String(definition.labelFallback || moduleId)
      );
      const description = translate(
        String(definition.descriptionKey || ""),
        null,
        String(definition.descriptionFallback || "")
      );
      return {
        moduleId,
        label: String(label || moduleId),
        description: String(description || "").trim(),
        enabledInProfile: moduleEnabled
      };
    });
    return {
      targetLanguage,
      modules
    };
  }

  function resolveProfileSrsPairs(context, items, profileId) {
    const ctx = context && typeof context === "object" ? context : {};
    const settingsManager = ctx.settingsManager;
    const isObject = typeof ctx.isObject === "function"
      ? ctx.isObject
      : ((value) => Boolean(value) && typeof value === "object" && !Array.isArray(value));
    const normalizeSrsPairKey = typeof ctx.normalizeSrsPairKey === "function"
      ? ctx.normalizeSrsPairKey
      : ((rawPair, fallbackPair) => String(rawPair || fallbackPair || "en-en").trim() || "en-en");
    const hasMeaningfulValue = typeof ctx.hasMeaningfulValue === "function"
      ? ctx.hasMeaningfulValue
      : ((value) => value !== null && value !== undefined);

    const profilesRoot = isObject(items && items.srsProfiles) ? items.srsProfiles : {};
    const profileEntry = isObject(profilesRoot[profileId]) ? profilesRoot[profileId] : {};
    const srsByPair = isObject(profileEntry.srsByPair) ? profileEntry.srsByPair : {};
    const srsSignalsByPair = isObject(profileEntry.srsSignalsByPair) ? profileEntry.srsSignalsByPair : {};
    const importedSnapshotsByPair = isObject(items && items.importedSrsPairSnapshots)
      ? items.importedSrsPairSnapshots
      : {};
    const languagePrefs = settingsManager && typeof settingsManager.getProfileLanguagePrefs === "function"
      ? settingsManager.getProfileLanguagePrefs(items, { profileId })
      : {
          sourceLanguage: "en",
          targetLanguage: "en",
          srsPair: "en-en"
        };
    const sourceLanguage = String(languagePrefs && languagePrefs.sourceLanguage || "en").trim() || "en";
    const targetLanguage = String(languagePrefs && languagePrefs.targetLanguage || "en").trim() || "en";
    const fallbackPair = `${sourceLanguage}-${targetLanguage}`;
    const currentPair = normalizeSrsPairKey(languagePrefs && languagePrefs.srsPair, fallbackPair);
    const seen = new Set();
    const pairOrder = [];
    const addPair = (rawPair) => {
      const pair = normalizeSrsPairKey(rawPair, fallbackPair);
      if (!pair || seen.has(pair)) {
        return;
      }
      seen.add(pair);
      pairOrder.push(pair);
    };

    addPair(currentPair);
    Object.keys(srsByPair).forEach((pair) => addPair(pair));
    Object.keys(srsSignalsByPair).forEach((pair) => addPair(pair));
    const importedPrefix = `${profileId}:`;
    Object.keys(importedSnapshotsByPair).forEach((key) => {
      if (!String(key).startsWith(importedPrefix)) {
        return;
      }
      addPair(String(key).slice(importedPrefix.length));
    });

    const pairs = [];
    pairOrder.forEach((pair) => {
      const profileData = isObject(srsByPair[pair]) ? srsByPair[pair] : {};
      const signalsData = isObject(srsSignalsByPair[pair]) ? srsSignalsByPair[pair] : {};
      const importedData = isObject(importedSnapshotsByPair[`${profileId}:${pair}`])
        ? importedSnapshotsByPair[`${profileId}:${pair}`]
        : null;
      const helperData = importedData && (
        isObject(importedData.helperSnapshot)
        || isObject(importedData.helperRuleset)
      )
        ? {
            helperSnapshot: importedData.helperSnapshot,
            helperRuleset: importedData.helperRuleset
          }
        : null;
      const hasProfileData = hasMeaningfulValue(profileData, 0);
      const hasSignalsData = hasMeaningfulValue(signalsData, 0);
      const hasImportedHelperData = hasMeaningfulValue(helperData, 0);
      if (!hasProfileData && !hasSignalsData && !hasImportedHelperData) {
        return;
      }
      pairs.push({
        pair,
        isCurrent: pair === currentPair,
        hasProfileData,
        hasSignalsData,
        hasImportedHelperData
      });
    });

    pairs.sort((a, b) => {
      if (a.isCurrent && !b.isCurrent) {
        return -1;
      }
      if (!a.isCurrent && b.isCurrent) {
        return 1;
      }
      return String(a.pair || "").localeCompare(String(b.pair || ""));
    });

    return {
      currentPair,
      pairs
    };
  }

  root.optionsShareCenterDataResolvers = {
    resolveProfileModules,
    resolveProfileSrsPairs
  };
})();
