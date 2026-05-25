(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const themePrefs = root.profileUiThemePrefs && typeof root.profileUiThemePrefs === "object"
    ? root.profileUiThemePrefs
    : {};
  const resolveCardThemeDefaults = typeof themePrefs.resolveCardThemeDefaults === "function"
    ? themePrefs.resolveCardThemeDefaults
    : () => ({
        hueDeg: 0,
        saturationPercent: 100,
        brightnessPercent: 100,
        transparencyPercent: 100
      });
  const cardThemeDefaults = resolveCardThemeDefaults();
  const replacementDensityDefaults = Object.freeze({
    standard: Object.freeze({
      maxOnePerTextBlock: false,
      allowAdjacentReplacements: false,
      maxReplacementsPerPage: 20,
      maxReplacementsPerLemmaPerPage: 2
    })
  });
  const standardReplacementDensity = replacementDensityDefaults.standard;

  root.replacementDensityDefaults = replacementDensityDefaults;
  root.defaults = {
    enabled: true,
    rules: [],
    customRulesetEnabled: true,
    profileRules: [],
    profileRulesUpdatedAt: "",
    manualRulesetCacheByPath: {},
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: standardReplacementDensity.maxOnePerTextBlock,
    allowAdjacentReplacements: standardReplacementDensity.allowAdjacentReplacements,
    maxReplacementsPerPage: standardReplacementDensity.maxReplacementsPerPage,
    maxReplacementsPerLemmaPerPage: standardReplacementDensity.maxReplacementsPerLemmaPerPage,
    debugEnabled: false,
    debugFocusWord: "",
    debugSemanticDecisionOverride: "",
    debugSemanticScanNodeBatchSize: 96,
    debugSemanticHelperBatchFlushMs: 0,
    uiLanguage: "system",
    rulesSource: "editor",
    rulesFileName: "",
    rulesUpdatedAt: "",
    sourceLanguage: "en",
    targetLanguage: "en",
    targetDisplayScript: "kanji",
    popupModulePrefs: {
      byId: {},
      order: []
    },
    srsPairAuto: true,
    srsSelectedProfileId: "default",
    srsProfileId: "default",
    optionsSelectedProfileId: "default",
    srsProfiles: {},
    srsEnabled: false,
    srsPair: "en-en",
    srsMaxActive: 40,
    srsBootstrapTopN: 800,
    srsInitialActiveCount: 40,
    srsSoundEnabled: true,
    srsHighlightColor: "#2F74D0",
    srsFeedbackSrsEnabled: true,
    srsFeedbackRulesEnabled: false,
    srsExposureLoggingEnabled: true,
    srsBrowsingAdmissionSignalsEnabled: false,
    srsSemanticAdmissionEnabled: true,
    srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
    profileBackgroundEnabled: false,
    profileBackgroundAssetId: "",
    profileBackgroundOpacity: 0.18,
    profileBackgroundBackdropColor: "#fbf7f0",
    profileBackgroundPositionX: 50,
    profileBackgroundPositionY: 50,
    profileCardThemeHueDeg: Number.isFinite(Number(cardThemeDefaults.hueDeg))
      ? Number(cardThemeDefaults.hueDeg)
      : 0,
    profileCardThemeSaturationPercent: Number.isFinite(Number(cardThemeDefaults.saturationPercent))
      ? Number(cardThemeDefaults.saturationPercent)
      : 100,
    profileCardThemeBrightnessPercent: Number.isFinite(Number(cardThemeDefaults.brightnessPercent))
      ? Number(cardThemeDefaults.brightnessPercent)
      : 100,
    profileCardThemeTransparencyPercent: Number.isFinite(Number(cardThemeDefaults.transparencyPercent))
      ? Number(cardThemeDefaults.transparencyPercent)
      : 100,
    srsRulesetUpdatedAt: ""
  };
})();
