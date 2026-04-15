(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createControllerGraph(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const i18n = opts.i18n && typeof opts.i18n === "object" ? opts.i18n : null;
    const t = root.optionsTranslateResolver.resolveTranslate(opts.t);
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
      : (() => {
          throw new Error("[LexiShift][Options] Missing language preferences adapter factory.");
        });
    const controllerAdaptersFactory = typeof opts.controllerAdaptersFactory === "function"
      ? opts.controllerAdaptersFactory
      : null;
    const errorMessage = typeof opts.errorMessage === "function"
      ? opts.errorMessage
      : ((_err, _key, fallback) => fallback || "");
    const logOptions = typeof opts.logOptions === "function" ? opts.logOptions : (() => {});
    const dom = opts.dom && typeof opts.dom === "object" ? opts.dom : {};
    const graphElements = root.optionsControllerGraphElements
      && typeof root.optionsControllerGraphElements.buildElements === "function"
      ? root.optionsControllerGraphElements.buildElements(dom)
      : null;
    if (!graphElements) {
      throw new Error("[LexiShift][Options] Missing controller graph elements bootstrap module.");
    }

    let languagePrefsAdapter = languagePrefsAdapterFactory({
      settingsManager,
      sourceLanguageInput: dom.sourceLanguageInput,
      targetLanguageInput: dom.targetLanguageInput,
      updateTargetLanguagePrefsModalVisibility: () => {}
    });

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
      settingsManager,
      resolveTargetLanguage: languagePrefsAdapter.resolveCurrentTargetLanguage,
      resolveSelectedProfileId: (items) => {
        if (settingsManager && typeof settingsManager.getSelectedSrsProfileId === "function") {
          return settingsManager.getSelectedSrsProfileId(items);
        }
        return "default";
      },
      optionsMainContent: dom.optionsMainContent,
      triggerButton: dom.targetLanguageGearButton,
      modalBackdrop: dom.targetLanguagePrefsModalBackdrop,
      modalRoot: dom.targetLanguagePrefsModal,
      modulesList: dom.targetLanguageModulesList
    });
    languagePrefsAdapter = languagePrefsAdapterFactory({
      settingsManager,
      sourceLanguageInput: dom.sourceLanguageInput,
      targetLanguageInput: dom.targetLanguageInput,
      updateTargetLanguagePrefsModalVisibility: (targetLanguage) => {
        targetLanguageModalController.syncVisibility(targetLanguage);
      }
    });

    const profileBackgroundController = requireControllerFactory("optionsProfileBackground")({
      t,
      settingsManager,
      ui,
      profileMediaStore: globalThis.LexiShift && globalThis.LexiShift.profileMediaStore,
      setStatus: uiBridge.setStatus,
      colors: ui.COLORS,
      maxUploadBytes: 8 * 1024 * 1024,
      elements: graphElements.profileBackground
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
        await targetLanguageModalController.refreshModulePrefs({
          items,
          profileId,
          targetLanguage: languagePrefs.targetLanguage
        });
      },
      cacheTtlMs: 10_000
    });

    let shareCenterController = null;
    const profileRulesetsController = requireControllerFactory("optionsProfileRulesets")({
      settingsManager,
      helperManager,
      t,
      setStatus: uiBridge.setStatus,
      log: logOptions,
      colors: ui.COLORS,
      onRulesetsUpdated: (event) => {
        if (!shareCenterController || typeof shareCenterController.syncForProfile !== "function") {
          return null;
        }
        return shareCenterController.syncForProfile(event);
      },
      elements: graphElements.profileRulesets
    });

    const rulesShareController = requireControllerFactory("optionsRulesShare")({
      rulesManager,
      t,
      setStatus: uiBridge.setStatus,
      updateRulesSourceUI: uiBridge.updateRulesSourceUI,
      updateRulesMeta: uiBridge.updateRulesMeta,
      errorMessage,
      colors: ui.COLORS,
      elements: graphElements.rulesShare
    });

    shareCenterController = requireControllerFactory("optionsShareCenter")({
      settingsManager,
      helperManager,
      rulesShareController,
      t,
      setStatus: uiBridge.setStatus,
      log: logOptions,
      colors: ui.COLORS,
      elements: graphElements.shareCenter
    });

    const helperActionsController = requireControllerFactory("optionsHelperActions")({
      helperManager,
      t,
      setHelperStatus: uiBridge.setHelperStatus,
      elements: graphElements.helperActions
    });

    const srsProfileRuntimeController = requireControllerFactory("optionsSrsProfileRuntime")({
      settingsManager,
      ui,
      t,
      setStatus: uiBridge.setStatus,
      resolvePair: languagePrefsAdapter.resolvePairFromInputs,
      applyLanguagePrefsToInputs: languagePrefsAdapter.applyLanguagePrefsToInputs,
      syncSelectedProfile: (items, options) => srsProfileSelectorController.syncSelected(items, options),
      syncProfileRulesetsForProfile: (optionsArg) => profileRulesetsController.syncForProfile(optionsArg),
      syncShareCenterForProfile: (optionsArg) => (shareCenterController
        ? shareCenterController.syncForProfile(optionsArg)
        : Promise.resolve()),
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
      elements: graphElements.srsProfileRuntime
    });

    const srsActionsController = requireControllerFactory("optionsSrsActions")({
      settingsManager,
      helperManager,
      t,
      setStatus: uiBridge.setStatus,
      resolvePair: languagePrefsAdapter.resolvePairFromInputs,
      syncSelectedProfile: (items, options) => srsProfileSelectorController.syncSelected(items, options),
      resolveEffectiveSrsPlanningState: (items, pairKey, options) => (
        srsProfileRuntimeController.resolveEffectiveSrsPlanningState(items, pairKey, options)
      ),
      log: logOptions,
      confirm: (message) => globalThis.confirm(message),
      colors: ui.COLORS,
      elements: graphElements.srsActions
    });

    const displayReplacementController = requireControllerFactory("optionsDisplayReplacement")({
      settingsManager,
      t,
      setStatus: uiBridge.setStatus,
      colors: ui.COLORS,
      elements: graphElements.displayReplacement
    });

    if (!controllerAdaptersFactory) {
      throw new Error("[LexiShift][Options] Missing required bootstrap module: optionsControllerAdapters");
    }
    const controllerAdapters = controllerAdaptersFactory({
      profileStatusController,
      targetLanguageModalController,
      profileBackgroundController,
      displayReplacementController,
      srsProfileRuntimeController
    });

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
      renderProfileBackgroundStatus: controllerAdapters.renderProfileBackgroundStatus,
      setSrsProfileStatusLocalized: controllerAdapters.setSrsProfileStatusLocalized,
      elements: graphElements.pageInit
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
      resolveEffectiveSrsPlanningState: controllerAdapters.resolveEffectiveSrsPlanningState,
      applyTargetLanguagePrefsLocalization: controllerAdapters.applyTargetLanguagePrefsLocalization,
      renderSrsProfileStatus: controllerAdapters.renderSrsProfileStatus,
      renderProfileBackgroundStatus: controllerAdapters.renderProfileBackgroundStatus,
      updateTargetLanguagePrefsModalVisibility: controllerAdapters.updateTargetLanguagePrefsModalVisibility,
      setTargetLanguagePrefsModalOpen: controllerAdapters.setTargetLanguagePrefsModalOpen,
      elements: graphElements.eventWiring
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
