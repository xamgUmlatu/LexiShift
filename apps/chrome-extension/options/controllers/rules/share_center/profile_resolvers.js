(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createProfileResolverHelpers(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const translate = typeof opts.translate === "function" ? opts.translate : (() => "");
    const labels = opts.labels && typeof opts.labels === "object" ? opts.labels : {};
    const isObject = typeof opts.isObject === "function"
      ? opts.isObject
      : ((value) => Boolean(value) && typeof value === "object" && !Array.isArray(value));
    const normalizeSrsPairKey = typeof opts.normalizeSrsPairKey === "function"
      ? opts.normalizeSrsPairKey
      : ((value) => String(value || "").trim().toLowerCase());
    const hasMeaningfulValue = typeof opts.hasMeaningfulValue === "function"
      ? opts.hasMeaningfulValue
      : ((value) => value != null);
    const shareCenterDataResolvers = opts.shareCenterDataResolvers && typeof opts.shareCenterDataResolvers === "object"
      ? opts.shareCenterDataResolvers
      : null;
    if (!shareCenterDataResolvers) {
      throw new Error("Share Center data resolvers are missing.");
    }

    function resolveProfileModules(items, profileId) {
      return shareCenterDataResolvers.resolveProfileModules({
        settingsManager,
        translate,
        labels,
        getPopupModulesRegistry: () => {
          const registry = root.popupModulesRegistry;
          return registry && typeof registry === "object" ? registry : null;
        },
        isObject
      }, items, profileId);
    }

    function resolveProfileSrsPairs(items, profileId) {
      return shareCenterDataResolvers.resolveProfileSrsPairs({
        settingsManager,
        isObject,
        normalizeSrsPairKey,
        hasMeaningfulValue
      }, items, profileId);
    }

    return {
      resolveProfileModules,
      resolveProfileSrsPairs
    };
  }

  root.optionsShareCenterProfileResolvers = {
    createProfileResolverHelpers
  };
})();
