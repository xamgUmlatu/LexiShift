(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  async function syncDeletedStoryState(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const loadSrsProfileForPair = typeof opts.loadSrsProfileForPair === "function"
      ? opts.loadSrsProfileForPair
      : null;
    const srsPair = String(opts.srsPair || "").trim();
    const profileId = String(opts.profileId || "").trim();
    const items = opts.items && typeof opts.items === "object" ? opts.items : {};

    if (!settingsManager || !srsPair || !profileId) {
      return;
    }

    if (typeof settingsManager.deleteSrsProfilePair === "function") {
      await settingsManager.deleteSrsProfilePair(srsPair, { profileId });
    } else if (typeof settingsManager.updateSrsProfile === "function") {
      const currentProfile = typeof settingsManager.getSrsProfile === "function"
        ? settingsManager.getSrsProfile(items, srsPair, { profileId })
        : {};
      await settingsManager.updateSrsProfile(srsPair, {
        ...currentProfile,
        srsEnabled: false
      }, {
        srsSelectedProfileId: profileId,
        srsPairAuto: true
      }, {
        profileId
      });
    }

    if (typeof settingsManager.publishSrsRuntimeProfile === "function") {
      await settingsManager.publishSrsRuntimeProfile(srsPair, {
        srsEnabled: false
      }, {
        srsSelectedProfileId: profileId
      }, {
        profileId
      });
    }

    if (loadSrsProfileForPair && typeof settingsManager.load === "function") {
      const refreshedItems = await settingsManager.load();
      await loadSrsProfileForPair(refreshedItems, srsPair, {
        profileId,
        forceHelperRefresh: true
      });
    }
  }

  root.optionsSrsDeleteStoryState = {
    syncDeletedStoryState
  };
})();
