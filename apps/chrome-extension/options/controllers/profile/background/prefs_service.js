(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createService(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;
    const updateOpacityLabel = typeof opts.updateOpacityLabel === "function"
      ? opts.updateOpacityLabel
      : (() => {});
    const setApplyState = typeof opts.setApplyState === "function"
      ? opts.setApplyState
      : (() => {});
    const hasPendingApply = typeof opts.hasPendingApply === "function"
      ? opts.hasPendingApply
      : (() => false);

    async function loadActiveProfileUiPrefs() {
      if (!settingsManager || typeof settingsManager.load !== "function") {
        return {
          profileId: "default",
          uiPrefs: {},
          items: {}
        };
      }
      const items = await settingsManager.load();
      const profileId = settingsManager.getSelectedSrsProfileId(items);
      const uiPrefs = settingsManager.getProfileUiPrefs(items, { profileId });
      return { profileId, uiPrefs, items };
    }

    async function saveProfileUiPrefsForCurrentProfile(nextPrefs, options) {
      if (!settingsManager || typeof settingsManager.updateProfileUiPrefs !== "function") {
        return nextPrefs && typeof nextPrefs === "object" ? { ...nextPrefs } : {};
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const profileId = String(localOptions.profileId || "").trim()
        || settingsManager.DEFAULT_PROFILE_ID
        || "default";
      const publishRuntime = localOptions.publishRuntime === true;
      const normalized = await settingsManager.updateProfileUiPrefs(nextPrefs, {
        profileId,
        publishRuntime
      });
      if (ui && typeof ui.updateProfileBackgroundInputs === "function") {
        ui.updateProfileBackgroundInputs(normalized);
      }
      updateOpacityLabel((normalized.backgroundOpacity || 0.18) * 100);
      // Apply button is only for committing pending file uploads.
      setApplyState(Boolean(hasPendingApply()), false);
      return normalized;
    }

    async function publishProfileUiPrefs(uiPrefs, options) {
      if (!settingsManager || typeof settingsManager.publishProfileUiPrefs !== "function") {
        return;
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const profileId = String(localOptions.profileId || "").trim()
        || settingsManager.DEFAULT_PROFILE_ID
        || "default";
      await settingsManager.publishProfileUiPrefs(uiPrefs, { profileId });
    }

    return {
      loadActiveProfileUiPrefs,
      saveProfileUiPrefsForCurrentProfile,
      publishProfileUiPrefs
    };
  }

  root.optionsProfileBackgroundPrefsService = {
    createService
  };
})();
