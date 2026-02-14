(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const i18n = opts.i18n && typeof opts.i18n === "object" ? opts.i18n : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setHelperStatus = typeof opts.setHelperStatus === "function"
      ? opts.setHelperStatus
      : (() => {});
    const helperActionsController = opts.helperActionsController && typeof opts.helperActionsController === "object"
      ? opts.helperActionsController
      : null;
    const applyLanguagePrefsToInputs = typeof opts.applyLanguagePrefsToInputs === "function"
      ? opts.applyLanguagePrefsToInputs
      : (() => "en-en");
    const loadSrsProfileForPair = typeof opts.loadSrsProfileForPair === "function"
      ? opts.loadSrsProfileForPair
      : (() => Promise.resolve());
    const updateRulesSourceUI = typeof opts.updateRulesSourceUI === "function"
      ? opts.updateRulesSourceUI
      : (() => {});
    const updateRulesMeta = typeof opts.updateRulesMeta === "function"
      ? opts.updateRulesMeta
      : (() => {});
    const applyTargetLanguagePrefsLocalization = typeof opts.applyTargetLanguagePrefsLocalization === "function"
      ? opts.applyTargetLanguagePrefsLocalization
      : (() => {});
    const renderSrsProfileStatus = typeof opts.renderSrsProfileStatus === "function"
      ? opts.renderSrsProfileStatus
      : (() => {});
    const renderProfileBackgroundStatus = typeof opts.renderProfileBackgroundStatus === "function"
      ? opts.renderProfileBackgroundStatus
      : (() => {});
    const setSrsProfileStatusLocalized = typeof opts.setSrsProfileStatusLocalized === "function"
      ? opts.setSrsProfileStatusLocalized
      : (() => {});
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const enabledInput = elements.enabledInput || null;
    const highlightEnabledInput = elements.highlightEnabledInput || null;
    const highlightColorInput = elements.highlightColorInput || null;
    const highlightColorText = elements.highlightColorText || null;
    const maxOnePerBlockInput = elements.maxOnePerBlockInput || null;
    const allowAdjacentInput = elements.allowAdjacentInput || null;
    const maxReplacementsPerPageInput = elements.maxReplacementsPerPageInput || null;
    const maxReplacementsPerLemmaPageInput = elements.maxReplacementsPerLemmaPageInput || null;
    const debugEnabledInput = elements.debugEnabledInput || null;
    const debugFocusInput = elements.debugFocusInput || null;
    const srsRulegenOutput = elements.srsRulegenOutput || null;
    const debugHelperTestOutput = elements.debugHelperTestOutput || null;
    const debugOpenDataDirOutput = elements.debugOpenDataDirOutput || null;
    const languageSelect = elements.languageSelect || null;
    const rulesInput = elements.rulesInput || null;
    const fileStatus = elements.fileStatus || null;
    const customRulesetEnabledInput = elements.customRulesetEnabledInput || null;

    async function load() {
      if (!settingsManager) {
        return;
      }
      setSrsProfileStatusLocalized("hint_profile_loading", null, "Loading profiles…");
      const items = await settingsManager.load();
      if (enabledInput) {
        enabledInput.checked = items.enabled;
      }
      highlightEnabledInput.checked = items.highlightEnabled !== false;
      highlightColorInput.value = items.highlightColor || settingsManager.defaults.highlightColor;
      highlightColorText.value = highlightColorInput.value;
      highlightColorInput.disabled = !highlightEnabledInput.checked;
      highlightColorText.disabled = !highlightEnabledInput.checked;
      maxOnePerBlockInput.checked = items.maxOnePerTextBlock === true;
      allowAdjacentInput.checked = items.allowAdjacentReplacements !== false;
      if (maxReplacementsPerPageInput) {
        const maxPerPage = Number.isFinite(Number(items.maxReplacementsPerPage))
          ? Math.max(0, Number(items.maxReplacementsPerPage))
          : (settingsManager.defaults.maxReplacementsPerPage || 0);
        maxReplacementsPerPageInput.value = String(maxPerPage);
      }
      if (maxReplacementsPerLemmaPageInput) {
        const maxPerLemma = Number.isFinite(Number(items.maxReplacementsPerLemmaPerPage))
          ? Math.max(0, Number(items.maxReplacementsPerLemmaPerPage))
          : (settingsManager.defaults.maxReplacementsPerLemmaPerPage || 0);
        maxReplacementsPerLemmaPageInput.value = String(maxPerLemma);
      }
      debugEnabledInput.checked = items.debugEnabled === true;
      debugFocusInput.value = items.debugFocusWord || "";
      debugFocusInput.disabled = !debugEnabledInput.checked;
      const selectedProfileId = settingsManager.getSelectedSrsProfileId(items);
      const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId: selectedProfileId });
      const pairKey = applyLanguagePrefsToInputs(languagePrefs);
      await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId: selectedProfileId });
      await loadSrsProfileForPair(items, pairKey);
      if (srsRulegenOutput) {
        srsRulegenOutput.textContent = "";
      }
      if (debugHelperTestOutput) {
        debugHelperTestOutput.textContent = "";
      }
      if (debugOpenDataDirOutput) {
        debugOpenDataDirOutput.textContent = "";
      }
      setHelperStatus("", "");
      if (helperActionsController && typeof helperActionsController.refreshStatus === "function") {
        await helperActionsController.refreshStatus();
      }
      if (languageSelect) {
        languageSelect.value = items.uiLanguage || "system";
      }
      settingsManager.currentRules = items.rules || [];
      if (customRulesetEnabledInput) {
        customRulesetEnabledInput.checked = items.customRulesetEnabled !== false;
      }
      rulesInput.value = JSON.stringify(settingsManager.currentRules, null, 2);
      updateRulesSourceUI(items.rulesSource || "editor");
      fileStatus.textContent = items.rulesFileName
        ? translate(
            "file_status_last_imported",
            items.rulesFileName,
            `Last imported: ${items.rulesFileName}`
          )
        : translate(
            "file_status_empty",
            null,
            "No file imported yet. Re-import after changes."
          );
      updateRulesMeta(settingsManager.currentRules, items.rulesUpdatedAt);
      if (i18n && typeof i18n.load === "function") {
        await i18n.load(items.uiLanguage || "system");
      }
      applyTargetLanguagePrefsLocalization();
      renderProfileBackgroundStatus();
      renderSrsProfileStatus();
    }

    return {
      load
    };
  }

  root.optionsPageInit = {
    createController
  };
})();
