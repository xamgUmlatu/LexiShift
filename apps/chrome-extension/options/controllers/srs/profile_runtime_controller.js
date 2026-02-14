(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const applyLanguagePrefsToInputs = typeof opts.applyLanguagePrefsToInputs === "function"
      ? opts.applyLanguagePrefsToInputs
      : (() => resolvePair());
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({ items, profileId: "default" }));
    const syncProfileRulesetsForProfile = typeof opts.syncProfileRulesetsForProfile === "function"
      ? opts.syncProfileRulesetsForProfile
      : (() => Promise.resolve());
    const clearProfileCache = typeof opts.clearProfileCache === "function"
      ? opts.clearProfileCache
      : (() => {});
    const syncProfileBackgroundForPrefs = typeof opts.syncProfileBackgroundForPrefs === "function"
      ? opts.syncProfileBackgroundForPrefs
      : (() => Promise.resolve());
    const setProfileStatusLocalized = typeof opts.setProfileStatusLocalized === "function"
      ? opts.setProfileStatusLocalized
      : (() => {});
    const setProfileStatusMessage = typeof opts.setProfileStatusMessage === "function"
      ? opts.setProfileStatusMessage
      : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const sourceLanguageInput = elements.sourceLanguageInput || null;
    const targetLanguageInput = elements.targetLanguageInput || null;
    const srsEnabledInput = elements.srsEnabledInput || null;
    const srsMaxActiveInput = elements.srsMaxActiveInput || null;
    const srsBootstrapTopNInput = elements.srsBootstrapTopNInput || null;
    const srsInitialActiveCountInput = elements.srsInitialActiveCountInput || null;
    const srsSoundInput = elements.srsSoundInput || null;
    const srsHighlightInput = elements.srsHighlightInput || null;
    const srsHighlightTextInput = elements.srsHighlightTextInput || null;
    const srsFeedbackSrsInput = elements.srsFeedbackSrsInput || null;
    const srsFeedbackRulesInput = elements.srsFeedbackRulesInput || null;
    const srsExposureLoggingInput = elements.srsExposureLoggingInput || null;
    const srsProfileIdInput = elements.srsProfileIdInput || null;
    const srsProfileRefreshButton = elements.srsProfileRefreshButton || null;

    function currentSourceLanguage() {
      return sourceLanguageInput
        ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
        : (settingsManager.defaults.sourceLanguage || "en");
    }

    function currentTargetLanguage() {
      return targetLanguageInput
        ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
        : (settingsManager.defaults.targetLanguage || "en");
    }

    async function loadSrsProfileForPair(items, pairKey, options) {
      const synced = await syncSelectedProfile(items, options);
      const profile = settingsManager.getSrsProfile(synced.items, pairKey, {
        profileId: synced.profileId
      });
      const uiPrefs = settingsManager.getProfileUiPrefs(synced.items, {
        profileId: synced.profileId
      });
      ui.updateSrsInputs(profile);
      ui.updateProfileBackgroundInputs(uiPrefs);
      await syncProfileBackgroundForPrefs(uiPrefs);
      if (srsEnabledInput) {
        srsEnabledInput.checked = profile.srsEnabled === true;
      }
      await settingsManager.publishSrsRuntimeProfile(pairKey, profile, {
        sourceLanguage: currentSourceLanguage(),
        targetLanguage: currentTargetLanguage(),
        srsPairAuto: true,
        srsSelectedProfileId: synced.profileId
      }, {
        profileId: synced.profileId
      });
      await syncProfileRulesetsForProfile({
        items: synced.items,
        profileId: synced.profileId,
        helperProfilesPayload: synced.helperProfilesPayload
      });
      log("Loaded SRS profile settings.", {
        pair: pairKey,
        profileId: synced.profileId,
        profileUiPrefs: uiPrefs
      });
      return { profile, uiPrefs, profileId: synced.profileId, items: synced.items };
    }

    async function saveSrsSettings() {
      if (!srsEnabledInput || !srsMaxActiveInput) {
        return;
      }
      const srsEnabled = srsEnabledInput.checked;
      const pairKey = resolvePair();
      const items = await settingsManager.load();
      const syncedProfileState = await syncSelectedProfile(items);
      const selectedProfileId = syncedProfileState.profileId;
      const maxActiveRaw = parseInt(srsMaxActiveInput.value, 10);
      const srsMaxActive = Number.isFinite(maxActiveRaw)
        ? Math.max(1, maxActiveRaw)
        : (settingsManager.defaults.srsMaxActive || 20);
      const srsSoundEnabled = srsSoundInput ? srsSoundInput.checked : true;
      const srsHighlightColor = srsHighlightInput
        ? (srsHighlightInput.value || settingsManager.defaults.srsHighlightColor || "#2F74D0")
        : (settingsManager.defaults.srsHighlightColor || "#2F74D0");
      const srsFeedbackSrsEnabled = srsFeedbackSrsInput ? srsFeedbackSrsInput.checked : true;
      const srsFeedbackRulesEnabled = srsFeedbackRulesInput ? srsFeedbackRulesInput.checked : false;
      const srsExposureLoggingEnabled = srsExposureLoggingInput
        ? srsExposureLoggingInput.checked
        : true;
      const sizing = settingsManager.resolveSrsSetSizing(
        {
          srsMaxActive,
          srsBootstrapTopN: srsBootstrapTopNInput ? srsBootstrapTopNInput.value : undefined,
          srsInitialActiveCount: srsInitialActiveCountInput ? srsInitialActiveCountInput.value : undefined
        },
        settingsManager.defaults
      );
      const profile = {
        srsEnabled,
        srsMaxActive,
        srsBootstrapTopN: sizing.srsBootstrapTopN,
        srsInitialActiveCount: sizing.srsInitialActiveCount,
        srsSoundEnabled,
        srsHighlightColor,
        srsFeedbackSrsEnabled,
        srsFeedbackRulesEnabled,
        srsExposureLoggingEnabled
      };
      const sourceLanguage = currentSourceLanguage();
      const targetLanguage = currentTargetLanguage();
      srsMaxActiveInput.value = String(srsMaxActive);
      if (srsBootstrapTopNInput) {
        srsBootstrapTopNInput.value = String(sizing.srsBootstrapTopN);
      }
      if (srsInitialActiveCountInput) {
        srsInitialActiveCountInput.value = String(sizing.srsInitialActiveCount);
      }
      if (srsHighlightInput) {
        srsHighlightInput.value = srsHighlightColor;
      }
      if (srsHighlightTextInput) {
        srsHighlightTextInput.value = srsHighlightColor;
      }

      const updateResult = await settingsManager.updateSrsProfile(pairKey, profile, {
        sourceLanguage,
        targetLanguage,
        srsPairAuto: true,
        srsSelectedProfileId: selectedProfileId
      }, {
        profileId: selectedProfileId
      });
      await settingsManager.publishSrsRuntimeProfile(pairKey, profile, {
        sourceLanguage,
        targetLanguage,
        srsPairAuto: true,
        srsSelectedProfileId: selectedProfileId
      }, {
        profileId: selectedProfileId
      });

      setStatus(translate("status_srs_saved", null, "SRS settings saved."), colors.SUCCESS);
      log("SRS settings saved.", {
        pair: pairKey,
        profileId: updateResult && updateResult.profileId ? updateResult.profileId : "default",
        sourceLanguage,
        targetLanguage,
        srsEnabled,
        srsMaxActive,
        srsBootstrapTopN: sizing.srsBootstrapTopN,
        srsInitialActiveCount: sizing.srsInitialActiveCount,
        srsSoundEnabled,
        srsHighlightColor,
        srsFeedbackSrsEnabled,
        srsFeedbackRulesEnabled,
        srsExposureLoggingEnabled
      });
    }

    async function saveLanguageSettings() {
      const sourceLanguage = currentSourceLanguage();
      const targetLanguage = currentTargetLanguage();
      const pairKey = resolvePair();
      try {
        const items = await settingsManager.load();
        const profileId = settingsManager.getSelectedSrsProfileId(items);
        await settingsManager.updateProfileLanguagePrefs({
          sourceLanguage,
          targetLanguage,
          srsPairAuto: true,
          srsPair: pairKey
        }, {
          profileId
        });
        const refreshed = await settingsManager.load();
        const refreshedPrefs = settingsManager.getProfileLanguagePrefs(refreshed, { profileId });
        applyLanguagePrefsToInputs(refreshedPrefs);
        await loadSrsProfileForPair(refreshed, pairKey);
        setStatus(translate("status_language_updated", null, "Language updated."), colors.SUCCESS);
      } catch (err) {
        const msg = err && err.message ? err.message : translate("status_language_updated", null, "Language updated.");
        setStatus(msg, colors.ERROR);
        log("Language update failed during SRS profile reload.", err);
      }
    }

    async function saveSrsProfileId() {
      if (!srsProfileIdInput) {
        return;
      }
      const beforeItems = await settingsManager.load();
      const previousProfileId = settingsManager.getSelectedSrsProfileId(beforeItems);
      const previousPair = resolvePair();
      const previousSourceLanguage = currentSourceLanguage();
      const previousTargetLanguage = currentTargetLanguage();
      await settingsManager.updateProfileLanguagePrefs({
        sourceLanguage: previousSourceLanguage,
        targetLanguage: previousTargetLanguage,
        srsPairAuto: true,
        srsPair: previousPair
      }, {
        profileId: previousProfileId
      });

      const profileId = String(srsProfileIdInput.value || "").trim() || settingsManager.DEFAULT_PROFILE_ID;
      await settingsManager.updateSelectedSrsProfileId(profileId);
      await settingsManager.updateSelectedUiProfileId(profileId);
      const items = await settingsManager.load();
      const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
      const pairKey = applyLanguagePrefsToInputs(languagePrefs);
      await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId });
      const refreshed = await settingsManager.load();
      await loadSrsProfileForPair(refreshed, pairKey);
      setStatus(translate("status_profile_saved", null, "Profile selection saved."), colors.SUCCESS);
    }

    async function refreshSrsProfiles() {
      const pairKey = resolvePair();
      if (srsProfileRefreshButton) {
        srsProfileRefreshButton.disabled = true;
      }
      setProfileStatusLocalized("hint_profile_loading", null, "Loading profiles…");
      try {
        clearProfileCache();
        const items = await settingsManager.load();
        await loadSrsProfileForPair(items, pairKey, { forceHelperRefresh: true });
        setStatus(translate("status_srs_profile_refreshed", null, "Helper profiles refreshed."), colors.SUCCESS);
      } catch (err) {
        const msg = err && err.message ? err.message : translate("status_srs_profile_refresh_failed", null, "Failed to refresh helper profiles.");
        setProfileStatusMessage(msg);
        setStatus(msg, colors.ERROR);
      } finally {
        if (srsProfileRefreshButton) {
          srsProfileRefreshButton.disabled = false;
        }
      }
    }

    return {
      loadSrsProfileForPair,
      saveSrsSettings,
      saveLanguageSettings,
      saveSrsProfileId,
      refreshSrsProfiles
    };
  }

  root.optionsSrsProfileRuntime = {
    createController
  };
})();
