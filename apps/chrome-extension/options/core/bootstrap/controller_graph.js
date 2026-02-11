(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createControllerGraph(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const i18n = opts.i18n && typeof opts.i18n === "object" ? opts.i18n : null;
    const t = typeof opts.t === "function" ? opts.t : ((_k, _s, f) => f || "");
    const rulesManager = opts.rulesManager && typeof opts.rulesManager === "object"
      ? opts.rulesManager
      : null;
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const uiBridge = opts.uiBridge && typeof opts.uiBridge === "object" ? opts.uiBridge : {};
    const requireControllerFactory = typeof opts.requireControllerFactory === "function"
      ? opts.requireControllerFactory
      : (() => {
          throw new Error("[LexiShift][Options] Missing controller factory resolver.");
        });
    const languagePrefsAdapterFactory = typeof opts.languagePrefsAdapterFactory === "function"
      ? opts.languagePrefsAdapterFactory
      : null;
    const errorMessage = typeof opts.errorMessage === "function"
      ? opts.errorMessage
      : ((_err, _key, fallback) => fallback || "");
    const logOptions = typeof opts.logOptions === "function" ? opts.logOptions : (() => {});
    const dom = opts.dom && typeof opts.dom === "object" ? opts.dom : {};

    let languagePrefsAdapter = languagePrefsAdapterFactory
      ? languagePrefsAdapterFactory({
          settingsManager,
          sourceLanguageInput: dom.sourceLanguageInput,
          targetLanguageInput: dom.targetLanguageInput,
          jaPrimaryDisplayScriptInput: dom.jaPrimaryDisplayScriptInput,
          updateTargetLanguagePrefsModalVisibility: () => {}
        })
      : {
          resolveCurrentTargetLanguage: () => (
            dom.targetLanguageInput
              ? (dom.targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
              : (settingsManager.defaults.targetLanguage || "en")
          ),
          normalizePrimaryDisplayScript: (value) => {
            const allowed = new Set(["kanji", "kana", "romaji"]);
            const candidate = String(value || "").trim().toLowerCase();
            return allowed.has(candidate) ? candidate : "kanji";
          },
          resolveTargetScriptPrefs: (_prefs) => ({ ja: { primaryDisplayScript: "kanji" } }),
          resolvePairFromInputs: () => {
            const sourceLanguage = dom.sourceLanguageInput
              ? (dom.sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
              : (settingsManager.defaults.sourceLanguage || "en");
            const targetLanguage = dom.targetLanguageInput
              ? (dom.targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
              : (settingsManager.defaults.targetLanguage || "en");
            return `${sourceLanguage}-${targetLanguage}`;
          },
          applyLanguagePrefsToInputs: (_prefs) => ""
        };

    const profileStatusController = requireControllerFactory("optionsProfileStatus")({
      output: dom.srsProfileStatusOutput,
      t,
      initialState: {
        mode: "i18n",
        key: "hint_profile_loading",
        substitutions: null,
        fallback: "Loading profiles…"
      }
    });

    const targetLanguageModalController = requireControllerFactory("optionsTargetLanguageModal")({
      t,
      resolveTargetLanguage: languagePrefsAdapter.resolveCurrentTargetLanguage,
      optionsMainContent: dom.optionsMainContent,
      triggerButton: dom.targetLanguageGearButton,
      modalBackdrop: dom.targetLanguagePrefsModalBackdrop,
      modalRoot: dom.targetLanguagePrefsModal
    });
    if (languagePrefsAdapterFactory) {
      languagePrefsAdapter = languagePrefsAdapterFactory({
        settingsManager,
        sourceLanguageInput: dom.sourceLanguageInput,
        targetLanguageInput: dom.targetLanguageInput,
        jaPrimaryDisplayScriptInput: dom.jaPrimaryDisplayScriptInput,
        updateTargetLanguagePrefsModalVisibility: (targetLanguage) => {
          targetLanguageModalController.syncVisibility(targetLanguage);
        }
      });
    }

    const profileBackgroundController = requireControllerFactory("optionsProfileBackground")({
      t,
      settingsManager,
      ui,
      profileMediaStore: globalThis.LexiShift && globalThis.LexiShift.profileMediaStore,
      setStatus: uiBridge.setStatus,
      colors: ui.COLORS,
      maxUploadBytes: 8 * 1024 * 1024,
      elements: {
        profileBgBackdropColorInput: dom.profileBgBackdropColorInput,
        profileBgEnabledInput: dom.profileBgEnabledInput,
        profileBgOpacityInput: dom.profileBgOpacityInput,
        profileBgOpacityValueOutput: dom.profileBgOpacityValueOutput,
        profileBgFileInput: dom.profileBgFileInput,
        profileBgRemoveButton: dom.profileBgRemoveButton,
        profileBgApplyButton: dom.profileBgApplyButton,
        profileBgStatusOutput: dom.profileBgStatusOutput,
        profileBgPreviewWrap: dom.profileBgPreviewWrap,
        profileBgPreviewImage: dom.profileBgPreviewImage
      }
    });

    const srsProfileSelectorController = requireControllerFactory("optionsSrsProfileSelector")({
      settingsManager,
      helperManager,
      profileSelect: dom.srsProfileIdInput,
      setProfileStatusLocalized: (key, substitutions, fallback) => {
        profileStatusController.setLocalized(key, substitutions, fallback);
      },
      onProfileLanguagePrefsSync: async ({ items, profileId }) => {
        const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
        languagePrefsAdapter.applyLanguagePrefsToInputs(languagePrefs);
        await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId });
      },
      cacheTtlMs: 10_000
    });

    const srsActionsController = requireControllerFactory("optionsSrsActions")({
      settingsManager,
      helperManager,
      t,
      setStatus: uiBridge.setStatus,
      resolvePair: languagePrefsAdapter.resolvePairFromInputs,
      syncSelectedProfile: (items, options) => srsProfileSelectorController.syncSelected(items, options),
      log: logOptions,
      confirm: (message) => globalThis.confirm(message),
      colors: ui.COLORS,
      elements: {
        output: dom.srsRulegenOutput,
        initializeButton: dom.srsInitializeSetButton,
        refreshButton: dom.srsRefreshSetButton,
        diagnosticsButton: dom.srsRuntimeDiagnosticsButton,
        sampledButton: dom.srsRulegenSampledButton,
        resetButton: dom.srsResetButton
      }
    });

    const rulesShareController = requireControllerFactory("optionsRulesShare")({
      rulesManager,
      t,
      setStatus: uiBridge.setStatus,
      updateRulesSourceUI: uiBridge.updateRulesSourceUI,
      updateRulesMeta: uiBridge.updateRulesMeta,
      errorMessage,
      colors: ui.COLORS,
      elements: {
        rulesInput: dom.rulesInput,
        rulesFileInput: dom.rulesFileInput,
        fileStatus: dom.fileStatus,
        shareCodeInput: dom.shareCodeInput,
        shareCodeCjk: dom.shareCodeCjk
      }
    });

    const helperActionsController = requireControllerFactory("optionsHelperActions")({
      helperManager,
      t,
      setHelperStatus: uiBridge.setHelperStatus,
      elements: {
        debugHelperTestButton: dom.debugHelperTestButton,
        debugHelperTestOutput: dom.debugHelperTestOutput,
        debugOpenDataDirButton: dom.debugOpenDataDirButton,
        debugOpenDataDirOutput: dom.debugOpenDataDirOutput
      }
    });

    const srsProfileRuntimeController = requireControllerFactory("optionsSrsProfileRuntime")({
      settingsManager,
      ui,
      t,
      setStatus: uiBridge.setStatus,
      resolvePair: languagePrefsAdapter.resolvePairFromInputs,
      applyLanguagePrefsToInputs: languagePrefsAdapter.applyLanguagePrefsToInputs,
      resolveTargetScriptPrefs: languagePrefsAdapter.resolveTargetScriptPrefs,
      normalizePrimaryDisplayScript: languagePrefsAdapter.normalizePrimaryDisplayScript,
      syncSelectedProfile: (items, options) => srsProfileSelectorController.syncSelected(items, options),
      clearProfileCache: () => srsProfileSelectorController.clearCache(),
      syncProfileBackgroundForPrefs: (uiPrefs) => profileBackgroundController.syncForLoadedPrefs(uiPrefs),
      setProfileStatusLocalized: (key, substitutions, fallback) => {
        profileStatusController.setLocalized(key, substitutions, fallback);
      },
      setProfileStatusMessage: (message) => {
        profileStatusController.setMessage(message);
      },
      log: logOptions,
      colors: ui.COLORS,
      elements: {
        sourceLanguageInput: dom.sourceLanguageInput,
        targetLanguageInput: dom.targetLanguageInput,
        jaPrimaryDisplayScriptInput: dom.jaPrimaryDisplayScriptInput,
        srsEnabledInput: dom.srsEnabledInput,
        srsMaxActiveInput: dom.srsMaxActiveInput,
        srsBootstrapTopNInput: dom.srsBootstrapTopNInput,
        srsInitialActiveCountInput: dom.srsInitialActiveCountInput,
        srsSoundInput: dom.srsSoundInput,
        srsHighlightInput: dom.srsHighlightInput,
        srsHighlightTextInput: dom.srsHighlightTextInput,
        srsFeedbackSrsInput: dom.srsFeedbackSrsInput,
        srsFeedbackRulesInput: dom.srsFeedbackRulesInput,
        srsExposureLoggingInput: dom.srsExposureLoggingInput,
        srsProfileIdInput: dom.srsProfileIdInput,
        srsProfileRefreshButton: dom.srsProfileRefreshButton
      }
    });

    const displayReplacementController = requireControllerFactory("optionsDisplayReplacement")({
      settingsManager,
      t,
      setStatus: uiBridge.setStatus,
      colors: ui.COLORS,
      elements: {
        highlightEnabledInput: dom.highlightEnabledInput,
        highlightColorInput: dom.highlightColorInput,
        debugEnabledInput: dom.debugEnabledInput,
        debugFocusInput: dom.debugFocusInput,
        maxOnePerBlockInput: dom.maxOnePerBlockInput,
        allowAdjacentInput: dom.allowAdjacentInput,
        maxReplacementsPerPageInput: dom.maxReplacementsPerPageInput,
        maxReplacementsPerLemmaPageInput: dom.maxReplacementsPerLemmaPageInput
      }
    });

    const controllerAdaptersFactory = root.optionsControllerAdapters
      && typeof root.optionsControllerAdapters.createControllerAdapters === "function"
      ? root.optionsControllerAdapters.createControllerAdapters
      : null;
    const controllerAdapters = controllerAdaptersFactory
      ? controllerAdaptersFactory({
          profileStatusController,
          targetLanguageModalController,
          displayReplacementController,
          srsProfileRuntimeController
        })
      : {
          renderSrsProfileStatus: () => profileStatusController.render(),
          setSrsProfileStatusLocalized: (key, substitutions, fallback) => {
            profileStatusController.setLocalized(key, substitutions, fallback);
          },
          setSrsProfileStatusMessage: (message) => {
            profileStatusController.setMessage(message);
          },
          applyTargetLanguagePrefsLocalization: () => targetLanguageModalController.applyLocalization(),
          updateTargetLanguagePrefsModalVisibility: (targetLanguage) => {
            targetLanguageModalController.syncVisibility(targetLanguage);
          },
          setTargetLanguagePrefsModalOpen: (open) => {
            targetLanguageModalController.setOpen(open);
          },
          loadSrsProfileForPair: async (items, pairKey, options) =>
            srsProfileRuntimeController.loadSrsProfileForPair(items, pairKey, options),
          saveDisplaySettings: () => displayReplacementController.saveDisplaySettings(),
          saveReplacementSettings: () => displayReplacementController.saveReplacementSettings(),
          saveSrsSettings: async () => srsProfileRuntimeController.saveSrsSettings(),
          saveLanguageSettings: async () => srsProfileRuntimeController.saveLanguageSettings(),
          saveSrsProfileId: async () => srsProfileRuntimeController.saveSrsProfileId(),
          refreshSrsProfiles: async () => srsProfileRuntimeController.refreshSrsProfiles()
        };

    const pageInitController = requireControllerFactory("optionsPageInit")({
      settingsManager,
      i18n,
      t,
      setHelperStatus: uiBridge.setHelperStatus,
      helperActionsController,
      applyLanguagePrefsToInputs: languagePrefsAdapter.applyLanguagePrefsToInputs,
      loadSrsProfileForPair: controllerAdapters.loadSrsProfileForPair,
      updateRulesSourceUI: uiBridge.updateRulesSourceUI,
      updateRulesMeta: uiBridge.updateRulesMeta,
      applyTargetLanguagePrefsLocalization: controllerAdapters.applyTargetLanguagePrefsLocalization,
      renderSrsProfileStatus: controllerAdapters.renderSrsProfileStatus,
      setSrsProfileStatusLocalized: controllerAdapters.setSrsProfileStatusLocalized,
      elements: {
        enabledInput: dom.enabledInput,
        highlightEnabledInput: dom.highlightEnabledInput,
        highlightColorInput: dom.highlightColorInput,
        highlightColorText: dom.highlightColorText,
        maxOnePerBlockInput: dom.maxOnePerBlockInput,
        allowAdjacentInput: dom.allowAdjacentInput,
        maxReplacementsPerPageInput: dom.maxReplacementsPerPageInput,
        maxReplacementsPerLemmaPageInput: dom.maxReplacementsPerLemmaPageInput,
        debugEnabledInput: dom.debugEnabledInput,
        debugFocusInput: dom.debugFocusInput,
        srsRulegenOutput: dom.srsRulegenOutput,
        debugHelperTestOutput: dom.debugHelperTestOutput,
        debugOpenDataDirOutput: dom.debugOpenDataDirOutput,
        languageSelect: dom.languageSelect,
        rulesInput: dom.rulesInput,
        fileStatus: dom.fileStatus
      }
    });

    const eventWiringController = requireControllerFactory("optionsEventWiring")({
      t,
      setStatus: uiBridge.setStatus,
      log: logOptions,
      i18n,
      ui,
      rulesShareController,
      profileBackgroundController,
      srsActionsController,
      helperActionsController,
      targetLanguageModalController,
      updateRulesSourceUI: uiBridge.updateRulesSourceUI,
      saveDisplaySettings: controllerAdapters.saveDisplaySettings,
      saveReplacementSettings: controllerAdapters.saveReplacementSettings,
      saveSrsSettings: controllerAdapters.saveSrsSettings,
      saveLanguageSettings: controllerAdapters.saveLanguageSettings,
      saveSrsProfileId: controllerAdapters.saveSrsProfileId,
      refreshSrsProfiles: controllerAdapters.refreshSrsProfiles,
      applyTargetLanguagePrefsLocalization: controllerAdapters.applyTargetLanguagePrefsLocalization,
      renderSrsProfileStatus: controllerAdapters.renderSrsProfileStatus,
      updateTargetLanguagePrefsModalVisibility: controllerAdapters.updateTargetLanguagePrefsModalVisibility,
      setTargetLanguagePrefsModalOpen: controllerAdapters.setTargetLanguagePrefsModalOpen,
      elements: {
        saveButton: dom.saveButton,
        importFileButton: dom.importFileButton,
        exportFileButton: dom.exportFileButton,
        rulesSourceInputs: dom.rulesSourceInputs,
        highlightEnabledInput: dom.highlightEnabledInput,
        highlightColorInput: dom.highlightColorInput,
        highlightColorText: dom.highlightColorText,
        maxOnePerBlockInput: dom.maxOnePerBlockInput,
        allowAdjacentInput: dom.allowAdjacentInput,
        maxReplacementsPerPageInput: dom.maxReplacementsPerPageInput,
        maxReplacementsPerLemmaPageInput: dom.maxReplacementsPerLemmaPageInput,
        srsEnabledInput: dom.srsEnabledInput,
        srsProfileIdInput: dom.srsProfileIdInput,
        srsProfileRefreshButton: dom.srsProfileRefreshButton,
        profileBgEnabledInput: dom.profileBgEnabledInput,
        profileBgBackdropColorInput: dom.profileBgBackdropColorInput,
        profileBgOpacityInput: dom.profileBgOpacityInput,
        profileBgFileInput: dom.profileBgFileInput,
        profileBgRemoveButton: dom.profileBgRemoveButton,
        profileBgApplyButton: dom.profileBgApplyButton,
        srsMaxActiveInput: dom.srsMaxActiveInput,
        srsBootstrapTopNInput: dom.srsBootstrapTopNInput,
        srsInitialActiveCountInput: dom.srsInitialActiveCountInput,
        srsSoundInput: dom.srsSoundInput,
        srsHighlightInput: dom.srsHighlightInput,
        srsHighlightTextInput: dom.srsHighlightTextInput,
        srsFeedbackSrsInput: dom.srsFeedbackSrsInput,
        srsFeedbackRulesInput: dom.srsFeedbackRulesInput,
        srsExposureLoggingInput: dom.srsExposureLoggingInput,
        srsInitializeSetButton: dom.srsInitializeSetButton,
        srsRefreshSetButton: dom.srsRefreshSetButton,
        srsRuntimeDiagnosticsButton: dom.srsRuntimeDiagnosticsButton,
        srsRulegenSampledButton: dom.srsRulegenSampledButton,
        srsResetButton: dom.srsResetButton,
        debugHelperTestButton: dom.debugHelperTestButton,
        debugOpenDataDirButton: dom.debugOpenDataDirButton,
        debugEnabledInput: dom.debugEnabledInput,
        debugFocusInput: dom.debugFocusInput,
        enabledInput: dom.enabledInput,
        languageSelect: dom.languageSelect,
        sourceLanguageInput: dom.sourceLanguageInput,
        targetLanguageInput: dom.targetLanguageInput,
        targetLanguageGearButton: dom.targetLanguageGearButton,
        jaPrimaryDisplayScriptInput: dom.jaPrimaryDisplayScriptInput,
        targetLanguagePrefsModalBackdrop: dom.targetLanguagePrefsModalBackdrop,
        targetLanguagePrefsModalOkButton: dom.targetLanguagePrefsModalOkButton,
        openDesktopAppButton: dom.openDesktopAppButton,
        openBdPluginButton: dom.openBdPluginButton,
        generateCodeButton: dom.generateCodeButton,
        importCodeButton: dom.importCodeButton,
        copyCodeButton: dom.copyCodeButton,
        srsRulegenOutput: dom.srsRulegenOutput
      }
    });

    return {
      eventWiringController,
      pageInitController
    };
  }

  root.optionsControllerGraph = {
    createControllerGraph
  };
})();
