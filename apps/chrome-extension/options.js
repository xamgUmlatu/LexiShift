const settingsManager = new SettingsManager();

const i18n = new LocalizationService();
const t = (k, s, f) => i18n.t(k, s, f);
const rulesManager = new RulesManager(settingsManager, i18n);
const ui = new UIManager(i18n);

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

function resolveCurrentTargetLanguage() {
  return targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
}

function requireControllerFactory(moduleKey) {
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
  resolveTargetLanguage: resolveCurrentTargetLanguage,
  optionsMainContent,
  triggerButton: targetLanguageGearButton,
  modalBackdrop: targetLanguagePrefsModalBackdrop,
  modalRoot: targetLanguagePrefsModal
});

const profileBackgroundController = requireControllerFactory("optionsProfileBackground")({
  t,
  settingsManager,
  ui,
  profileMediaStore: globalThis.LexiShift && globalThis.LexiShift.profileMediaStore,
  setStatus,
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
  setProfileStatusLocalized: setSrsProfileStatusLocalized,
  onProfileLanguagePrefsSync: async ({ items, profileId }) => {
    const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
    applyLanguagePrefsToInputs(languagePrefs);
    await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId });
  },
  cacheTtlMs: 10_000
});

const srsActionsController = requireControllerFactory("optionsSrsActions")({
  settingsManager,
  helperManager,
  t,
  setStatus,
  resolvePair: resolvePairFromInputs,
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
  setStatus,
  updateRulesSourceUI,
  updateRulesMeta,
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
  setHelperStatus,
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
  setStatus,
  resolvePair: resolvePairFromInputs,
  applyLanguagePrefsToInputs,
  resolveTargetScriptPrefs,
  normalizePrimaryDisplayScript,
  syncSelectedProfile: (items, options) => srsProfileSelectorController.syncSelected(items, options),
  clearProfileCache: () => srsProfileSelectorController.clearCache(),
  syncProfileBackgroundForPrefs: (uiPrefs) => profileBackgroundController.syncForLoadedPrefs(uiPrefs),
  setProfileStatusLocalized: setSrsProfileStatusLocalized,
  setProfileStatusMessage: setSrsProfileStatusMessage,
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

const pageInitController = requireControllerFactory("optionsPageInit")({
  settingsManager,
  i18n,
  t,
  setHelperStatus,
  helperActionsController,
  applyLanguagePrefsToInputs,
  loadSrsProfileForPair,
  updateRulesSourceUI,
  updateRulesMeta,
  applyTargetLanguagePrefsLocalization,
  renderSrsProfileStatus,
  setSrsProfileStatusLocalized,
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
  setStatus,
  log: logOptions,
  i18n,
  ui,
  rulesShareController,
  profileBackgroundController,
  srsActionsController,
  helperActionsController,
  targetLanguageModalController,
  updateRulesSourceUI,
  saveDisplaySettings,
  saveReplacementSettings,
  saveSrsSettings,
  saveLanguageSettings,
  saveSrsProfileId,
  refreshSrsProfiles,
  applyTargetLanguagePrefsLocalization,
  renderSrsProfileStatus,
  updateTargetLanguagePrefsModalVisibility,
  setTargetLanguagePrefsModalOpen,
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

const displayReplacementController = requireControllerFactory("optionsDisplayReplacement")({
  settingsManager,
  t,
  setStatus,
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

function setStatus(message, color) {
  ui.setStatus(message, color);
}

function setHelperStatus(status, lastSync) {
  ui.setHelperStatus(status, lastSync);
}

function updateRulesMeta(rules, updatedAt) {
  ui.updateRulesMeta(rules, updatedAt);
}

function updateRulesSourceUI(source) {
  ui.updateRulesSourceUI(source);
}

function renderSrsProfileStatus() {
  profileStatusController.render();
}

function setSrsProfileStatusLocalized(key, substitutions, fallback) {
  profileStatusController.setLocalized(key, substitutions, fallback);
}

function setSrsProfileStatusMessage(message) {
  profileStatusController.setMessage(message);
}

function applyTargetLanguagePrefsLocalization() {
  targetLanguageModalController.applyLocalization();
}

function resolvePairFromInputs() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  const prefs = globalThis.LexiShift && globalThis.LexiShift.languagePrefs;
  if (prefs && typeof prefs.resolveLanguagePair === "function") {
    return prefs.resolveLanguagePair({
      sourceLanguage,
      targetLanguage,
      srsPairAuto: true,
      srsPair: settingsManager.defaults.srsPair || "en-en"
    });
  }
  return `${sourceLanguage}-${targetLanguage}`;
}

function normalizePrimaryDisplayScript(value) {
  const allowed = new Set(["kanji", "kana", "romaji"]);
  const candidate = String(value || "").trim().toLowerCase();
  if (allowed.has(candidate)) {
    return candidate;
  }
  return "kanji";
}

function resolveTargetScriptPrefs(languagePrefs) {
  const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
  const rawTargetScriptPrefs = prefs.targetScriptPrefs && typeof prefs.targetScriptPrefs === "object"
    ? prefs.targetScriptPrefs
    : {};
  const rawJaPrefs = rawTargetScriptPrefs.ja && typeof rawTargetScriptPrefs.ja === "object"
    ? rawTargetScriptPrefs.ja
    : {};
  return {
    ja: {
      primaryDisplayScript: normalizePrimaryDisplayScript(rawJaPrefs.primaryDisplayScript)
    }
  };
}

function updateTargetLanguagePrefsModalVisibility(targetLanguage) {
  targetLanguageModalController.syncVisibility(targetLanguage);
}

function setTargetLanguagePrefsModalOpen(open) {
  targetLanguageModalController.setOpen(open);
}

function applyLanguagePrefsToInputs(languagePrefs) {
  const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
  const sourceLanguage = String(prefs.sourceLanguage || settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = String(prefs.targetLanguage || settingsManager.defaults.targetLanguage || "en");
  const targetScriptPrefs = resolveTargetScriptPrefs(prefs);
  if (sourceLanguageInput) {
    sourceLanguageInput.value = sourceLanguage;
  }
  if (targetLanguageInput) {
    targetLanguageInput.value = targetLanguage;
  }
  if (jaPrimaryDisplayScriptInput) {
    jaPrimaryDisplayScriptInput.value = targetScriptPrefs.ja.primaryDisplayScript;
  }
  updateTargetLanguagePrefsModalVisibility(targetLanguage);
  const pair = String(prefs.srsPair || "").trim();
  return pair || resolvePairFromInputs();
}

async function loadSrsProfileForPair(items, pairKey, options) {
  return srsProfileRuntimeController.loadSrsProfileForPair(items, pairKey, options);
}

function saveDisplaySettings() {
  displayReplacementController.saveDisplaySettings();
}

function saveReplacementSettings() {
  displayReplacementController.saveReplacementSettings();
}

async function saveSrsSettings() {
  return srsProfileRuntimeController.saveSrsSettings();
}

async function saveLanguageSettings() {
  return srsProfileRuntimeController.saveLanguageSettings();
}

async function saveSrsProfileId() {
  return srsProfileRuntimeController.saveSrsProfileId();
}

async function refreshSrsProfiles() {
  return srsProfileRuntimeController.refreshSrsProfiles();
}

eventWiringController.bind();
pageInitController.load();
