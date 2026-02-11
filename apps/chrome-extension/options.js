const settingsManager = new SettingsManager();

const i18n = new LocalizationService();
const t = (k, s, f) => i18n.t(k, s, f);
const rulesManager = new RulesManager(settingsManager, i18n);
const ui = new UIManager(i18n);
const uiBridgeFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsUiBridge
  && typeof globalThis.LexiShift.optionsUiBridge.createUiBridge === "function"
  ? globalThis.LexiShift.optionsUiBridge.createUiBridge
  : null;
const uiBridge = uiBridgeFactory
  ? uiBridgeFactory({ ui })
  : {
      setStatus: (message, color) => ui.setStatus(message, color),
      setHelperStatus: (status, lastSync) => ui.setHelperStatus(status, lastSync),
      updateRulesMeta: (rules, updatedAt) => ui.updateRulesMeta(rules, updatedAt),
      updateRulesSourceUI: (source) => ui.updateRulesSourceUI(source)
    };
const controllerFactoryResolverFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsControllerFactoryResolver
  && typeof globalThis.LexiShift.optionsControllerFactoryResolver.createResolver === "function"
  ? globalThis.LexiShift.optionsControllerFactoryResolver.createResolver
  : null;
const controllerFactoryResolver = controllerFactoryResolverFactory
  ? controllerFactoryResolverFactory()
  : {
      requireControllerFactory: (moduleKey) => {
        const root = globalThis.LexiShift && typeof globalThis.LexiShift === "object"
          ? globalThis.LexiShift
          : null;
        const module = root && root[moduleKey] && typeof root[moduleKey] === "object"
          ? root[moduleKey]
          : null;
        if (!module || typeof module.createController !== "function") {
          throw new Error(`[LexiShift][Options] Missing required controller module: ${moduleKey}`);
        }
        return module.createController;
      }
    };
const requireControllerFactory = controllerFactoryResolver.requireControllerFactory;

function logOptions(...args) {
  console.log("[LexiShift][Options]", ...args);
}
const helperManager = new HelperManager(i18n, logOptions);

function errorMessage(err, fallbackKey, fallbackText) {
  if (err instanceof SyntaxError) {
    return t(fallbackKey, null, fallbackText);
  }
  if (err && err.message) {
    return err.message;
  }
  return t(fallbackKey, null, fallbackText);
}

i18n.apply();

// Map UIManager elements to local variables to minimize diff churn
const {
  optionsMainContent,
  enabled: enabledInput,
  highlightEnabled: highlightEnabledInput,
  highlightColor: highlightColorInput,
  highlightColorText: highlightColorText,
  maxOnePerBlock: maxOnePerBlockInput,
  allowAdjacent: allowAdjacentInput,
  maxReplacementsPerPage: maxReplacementsPerPageInput,
  maxReplacementsPerLemmaPage: maxReplacementsPerLemmaPageInput,
  debugEnabled: debugEnabledInput,
  debugFocusWord: debugFocusInput,
  srsEnabled: srsEnabledInput,
  sourceLanguage: sourceLanguageInput,
  targetLanguage: targetLanguageInput,
  targetLanguageGear: targetLanguageGearButton,
  targetLanguagePrefsModalBackdrop: targetLanguagePrefsModalBackdrop,
  targetLanguagePrefsModal: targetLanguagePrefsModal,
  targetLanguagePrefsModalOk: targetLanguagePrefsModalOkButton,
  jaPrimaryDisplayScript: jaPrimaryDisplayScriptInput,
  srsProfileId: srsProfileIdInput,
  srsProfileRefresh: srsProfileRefreshButton,
  srsProfileStatus: srsProfileStatusOutput,
  profileBgBackdropColor: profileBgBackdropColorInput,
  profileBgEnabled: profileBgEnabledInput,
  profileBgOpacity: profileBgOpacityInput,
  profileBgOpacityValue: profileBgOpacityValueOutput,
  profileBgFile: profileBgFileInput,
  profileBgRemove: profileBgRemoveButton,
  profileBgApply: profileBgApplyButton,
  profileBgStatus: profileBgStatusOutput,
  profileBgPreviewWrap: profileBgPreviewWrap,
  profileBgPreview: profileBgPreviewImage,
  srsMaxActive: srsMaxActiveInput,
  srsBootstrapTopN: srsBootstrapTopNInput,
  srsInitialActiveCount: srsInitialActiveCountInput,
  srsSoundEnabled: srsSoundInput,
  srsHighlightColor: srsHighlightInput,
  srsHighlightColorText: srsHighlightTextInput,
  srsFeedbackSrsEnabled: srsFeedbackSrsInput,
  srsFeedbackRulesEnabled: srsFeedbackRulesInput,
  srsExposureLoggingEnabled: srsExposureLoggingInput,
  srsInitializeSet: srsInitializeSetButton,
  srsRefreshSet: srsRefreshSetButton,
  srsRuntimeDiagnostics: srsRuntimeDiagnosticsButton,
  srsRulegenSampledPreview: srsRulegenSampledButton,
  srsRulegenOutput: srsRulegenOutput,
  srsReset: srsResetButton,
  debugHelperTest: debugHelperTestButton,
  debugHelperTestOutput: debugHelperTestOutput,
  debugOpenDataDir: debugOpenDataDirButton,
  debugOpenDataDirOutput: debugOpenDataDirOutput,
  uiLanguage: languageSelect,
  rules: rulesInput,
  save: saveButton,
  rulesSourceInputs: rulesSourceInputs,
  rulesFile: rulesFileInput,
  importFile: importFileButton,
  exportFile: exportFileButton,
  fileStatus: fileStatus,
  shareCode: shareCodeInput,
  shareCodeCjk: shareCodeCjk,
  generateCode: generateCodeButton,
  importCode: importCodeButton,
  copyCode: copyCodeButton,
  openDesktopApp: openDesktopAppButton,
  openBdPlugin: openBdPluginButton
} = ui.dom;
const languagePrefsAdapterFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsLanguagePrefsAdapter
  && typeof globalThis.LexiShift.optionsLanguagePrefsAdapter.createAdapter === "function"
  ? globalThis.LexiShift.optionsLanguagePrefsAdapter.createAdapter
  : null;
let languagePrefsAdapter = languagePrefsAdapterFactory
  ? languagePrefsAdapterFactory({
      settingsManager,
      sourceLanguageInput,
      targetLanguageInput,
      jaPrimaryDisplayScriptInput,
      updateTargetLanguagePrefsModalVisibility: () => {}
    })
  : {
      resolveCurrentTargetLanguage: () => (
        targetLanguageInput
          ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
          : (settingsManager.defaults.targetLanguage || "en")
      ),
      normalizePrimaryDisplayScript: (value) => {
        const allowed = new Set(["kanji", "kana", "romaji"]);
        const candidate = String(value || "").trim().toLowerCase();
        return allowed.has(candidate) ? candidate : "kanji";
      },
      resolveTargetScriptPrefs: (_prefs) => ({ ja: { primaryDisplayScript: "kanji" } }),
      resolvePairFromInputs: () => {
        const sourceLanguage = sourceLanguageInput
          ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
          : (settingsManager.defaults.sourceLanguage || "en");
        const targetLanguage = targetLanguageInput
          ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
          : (settingsManager.defaults.targetLanguage || "en");
        return `${sourceLanguage}-${targetLanguage}`;
      },
      applyLanguagePrefsToInputs: (_prefs) => ""
    };

const profileStatusController = requireControllerFactory("optionsProfileStatus")({
  output: srsProfileStatusOutput,
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
  optionsMainContent,
  triggerButton: targetLanguageGearButton,
  modalBackdrop: targetLanguagePrefsModalBackdrop,
  modalRoot: targetLanguagePrefsModal
});
if (languagePrefsAdapterFactory) {
  languagePrefsAdapter = languagePrefsAdapterFactory({
    settingsManager,
    sourceLanguageInput,
    targetLanguageInput,
    jaPrimaryDisplayScriptInput,
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
    profileBgBackdropColorInput,
    profileBgEnabledInput,
    profileBgOpacityInput,
    profileBgOpacityValueOutput,
    profileBgFileInput,
    profileBgRemoveButton,
    profileBgApplyButton,
    profileBgStatusOutput,
    profileBgPreviewWrap,
    profileBgPreviewImage
  }
});

const srsProfileSelectorController = requireControllerFactory("optionsSrsProfileSelector")({
  settingsManager,
  helperManager,
  profileSelect: srsProfileIdInput,
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
  confirm: (message) => confirm(message),
  colors: ui.COLORS,
  elements: {
    output: srsRulegenOutput,
    initializeButton: srsInitializeSetButton,
    refreshButton: srsRefreshSetButton,
    diagnosticsButton: srsRuntimeDiagnosticsButton,
    sampledButton: srsRulegenSampledButton,
    resetButton: srsResetButton
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
    rulesInput,
    rulesFileInput,
    fileStatus,
    shareCodeInput,
    shareCodeCjk
  }
});

const helperActionsController = requireControllerFactory("optionsHelperActions")({
  helperManager,
  t,
  setHelperStatus: uiBridge.setHelperStatus,
  elements: {
    debugHelperTestButton,
    debugHelperTestOutput,
    debugOpenDataDirButton,
    debugOpenDataDirOutput
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
    sourceLanguageInput,
    targetLanguageInput,
    jaPrimaryDisplayScriptInput,
    srsEnabledInput,
    srsMaxActiveInput,
    srsBootstrapTopNInput,
    srsInitialActiveCountInput,
    srsSoundInput,
    srsHighlightInput,
    srsHighlightTextInput,
    srsFeedbackSrsInput,
    srsFeedbackRulesInput,
    srsExposureLoggingInput,
    srsProfileIdInput,
    srsProfileRefreshButton
  }
});

const displayReplacementController = requireControllerFactory("optionsDisplayReplacement")({
  settingsManager,
  t,
  setStatus: uiBridge.setStatus,
  colors: ui.COLORS,
  elements: {
    highlightEnabledInput,
    highlightColorInput,
    debugEnabledInput,
    debugFocusInput,
    maxOnePerBlockInput,
    allowAdjacentInput,
    maxReplacementsPerPageInput,
    maxReplacementsPerLemmaPageInput
  }
});

const controllerAdaptersFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsControllerAdapters
  && typeof globalThis.LexiShift.optionsControllerAdapters.createControllerAdapters === "function"
  ? globalThis.LexiShift.optionsControllerAdapters.createControllerAdapters
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
    enabledInput,
    highlightEnabledInput,
    highlightColorInput,
    highlightColorText,
    maxOnePerBlockInput,
    allowAdjacentInput,
    maxReplacementsPerPageInput,
    maxReplacementsPerLemmaPageInput,
    debugEnabledInput,
    debugFocusInput,
    srsRulegenOutput,
    debugHelperTestOutput,
    debugOpenDataDirOutput,
    languageSelect,
    rulesInput,
    fileStatus
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
    saveButton,
    importFileButton,
    exportFileButton,
    rulesSourceInputs,
    highlightEnabledInput,
    highlightColorInput,
    highlightColorText,
    maxOnePerBlockInput,
    allowAdjacentInput,
    maxReplacementsPerPageInput,
    maxReplacementsPerLemmaPageInput,
    srsEnabledInput,
    srsProfileIdInput,
    srsProfileRefreshButton,
    profileBgEnabledInput,
    profileBgBackdropColorInput,
    profileBgOpacityInput,
    profileBgFileInput,
    profileBgRemoveButton,
    profileBgApplyButton,
    srsMaxActiveInput,
    srsBootstrapTopNInput,
    srsInitialActiveCountInput,
    srsSoundInput,
    srsHighlightInput,
    srsHighlightTextInput,
    srsFeedbackSrsInput,
    srsFeedbackRulesInput,
    srsExposureLoggingInput,
    srsInitializeSetButton,
    srsRefreshSetButton,
    srsRuntimeDiagnosticsButton,
    srsRulegenSampledButton,
    srsResetButton,
    debugHelperTestButton,
    debugOpenDataDirButton,
    debugEnabledInput,
    debugFocusInput,
    enabledInput,
    languageSelect,
    sourceLanguageInput,
    targetLanguageInput,
    targetLanguageGearButton,
    jaPrimaryDisplayScriptInput,
    targetLanguagePrefsModalBackdrop,
    targetLanguagePrefsModalOkButton,
    openDesktopAppButton,
    openBdPluginButton,
    generateCodeButton,
    importCodeButton,
    copyCodeButton,
    srsRulegenOutput
  }
});

eventWiringController.bind();
pageInitController.load();
