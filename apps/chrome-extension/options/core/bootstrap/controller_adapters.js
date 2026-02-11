(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createControllerAdapters(options) {
    const opts = options && typeof options === "object" ? options : {};
    const profileStatusController = opts.profileStatusController && typeof opts.profileStatusController === "object"
      ? opts.profileStatusController
      : null;
    const targetLanguageModalController = opts.targetLanguageModalController
      && typeof opts.targetLanguageModalController === "object"
      ? opts.targetLanguageModalController
      : null;
    const displayReplacementController = opts.displayReplacementController
      && typeof opts.displayReplacementController === "object"
      ? opts.displayReplacementController
      : null;
    const srsProfileRuntimeController = opts.srsProfileRuntimeController
      && typeof opts.srsProfileRuntimeController === "object"
      ? opts.srsProfileRuntimeController
      : null;

    function renderSrsProfileStatus() {
      if (!profileStatusController || typeof profileStatusController.render !== "function") {
        return;
      }
      profileStatusController.render();
    }

    function setSrsProfileStatusLocalized(key, substitutions, fallback) {
      if (!profileStatusController || typeof profileStatusController.setLocalized !== "function") {
        return;
      }
      profileStatusController.setLocalized(key, substitutions, fallback);
    }

    function setSrsProfileStatusMessage(message) {
      if (!profileStatusController || typeof profileStatusController.setMessage !== "function") {
        return;
      }
      profileStatusController.setMessage(message);
    }

    function applyTargetLanguagePrefsLocalization() {
      if (!targetLanguageModalController || typeof targetLanguageModalController.applyLocalization !== "function") {
        return;
      }
      targetLanguageModalController.applyLocalization();
    }

    function updateTargetLanguagePrefsModalVisibility(targetLanguage) {
      if (!targetLanguageModalController || typeof targetLanguageModalController.syncVisibility !== "function") {
        return;
      }
      targetLanguageModalController.syncVisibility(targetLanguage);
    }

    function setTargetLanguagePrefsModalOpen(open) {
      if (!targetLanguageModalController || typeof targetLanguageModalController.setOpen !== "function") {
        return;
      }
      targetLanguageModalController.setOpen(open);
    }

    async function loadSrsProfileForPair(items, pairKey, options) {
      if (!srsProfileRuntimeController || typeof srsProfileRuntimeController.loadSrsProfileForPair !== "function") {
        return null;
      }
      return srsProfileRuntimeController.loadSrsProfileForPair(items, pairKey, options);
    }

    function saveDisplaySettings() {
      if (!displayReplacementController || typeof displayReplacementController.saveDisplaySettings !== "function") {
        return;
      }
      displayReplacementController.saveDisplaySettings();
    }

    function saveReplacementSettings() {
      if (!displayReplacementController || typeof displayReplacementController.saveReplacementSettings !== "function") {
        return;
      }
      displayReplacementController.saveReplacementSettings();
    }

    async function saveSrsSettings() {
      if (!srsProfileRuntimeController || typeof srsProfileRuntimeController.saveSrsSettings !== "function") {
        return null;
      }
      return srsProfileRuntimeController.saveSrsSettings();
    }

    async function saveLanguageSettings() {
      if (!srsProfileRuntimeController || typeof srsProfileRuntimeController.saveLanguageSettings !== "function") {
        return null;
      }
      return srsProfileRuntimeController.saveLanguageSettings();
    }

    async function saveSrsProfileId() {
      if (!srsProfileRuntimeController || typeof srsProfileRuntimeController.saveSrsProfileId !== "function") {
        return null;
      }
      return srsProfileRuntimeController.saveSrsProfileId();
    }

    async function refreshSrsProfiles() {
      if (!srsProfileRuntimeController || typeof srsProfileRuntimeController.refreshSrsProfiles !== "function") {
        return null;
      }
      return srsProfileRuntimeController.refreshSrsProfiles();
    }

    return {
      renderSrsProfileStatus,
      setSrsProfileStatusLocalized,
      setSrsProfileStatusMessage,
      applyTargetLanguagePrefsLocalization,
      updateTargetLanguagePrefsModalVisibility,
      setTargetLanguagePrefsModalOpen,
      loadSrsProfileForPair,
      saveDisplaySettings,
      saveReplacementSettings,
      saveSrsSettings,
      saveLanguageSettings,
      saveSrsProfileId,
      refreshSrsProfiles
    };
  }

  root.optionsControllerAdapters = {
    createControllerAdapters
  };
})();
