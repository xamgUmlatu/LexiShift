(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createResolvePlanningState(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const resolveEffectiveSrsPlanningState = typeof opts.resolveEffectiveSrsPlanningState === "function"
      ? opts.resolveEffectiveSrsPlanningState
      : null;

    return function resolvePlanningState(items, pairKey, profileId) {
      if (resolveEffectiveSrsPlanningState) {
        const resolved = resolveEffectiveSrsPlanningState(items, pairKey, { profileId });
        if (resolved && typeof resolved === "object") {
          return resolved;
        }
      }
      const profile = settingsManager.getSrsProfile(items, pairKey, { profileId });
      return {
        profileId: profile.profileId || profileId || "default",
        profile,
        signals: settingsManager.getSrsProfileSignals(items, pairKey, {
          profileId: profile.profileId || profileId
        }),
        profileContext: settingsManager.buildSrsPlanContext(items, pairKey, {
          profileId: profile.profileId || profileId
        }),
        contextMeta: {
          source: "saved_profile",
          pendingOverrides: []
        }
      };
    };
  }

  root.optionsSrsActionPlanningState = {
    createResolvePlanningState
  };
})();
