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
        brightnessPercent: 100
      });
  const cardThemeDefaults = resolveCardThemeDefaults();

  root.defaults = {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    maxReplacementsPerPage: 0,
    maxReplacementsPerLemmaPerPage: 0,
    debugEnabled: false,
    debugFocusWord: "",
    uiLanguage: "system",
    rulesSource: "editor",
    rulesFileName: "",
    rulesUpdatedAt: "",
    sourceLanguage: "en",
    targetLanguage: "en",
    targetDisplayScript: "kanji",
    popupModulePrefs: {
      byId: {}
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
    profileBackgroundEnabled: false,
    profileBackgroundAssetId: "",
    profileBackgroundOpacity: 0.18,
    profileBackgroundBackdropColor: "#fbf7f0",
    profileCardThemeHueDeg: Number.isFinite(Number(cardThemeDefaults.hueDeg))
      ? Number(cardThemeDefaults.hueDeg)
      : 0,
    profileCardThemeSaturationPercent: Number.isFinite(Number(cardThemeDefaults.saturationPercent))
      ? Number(cardThemeDefaults.saturationPercent)
      : 100,
    profileCardThemeBrightnessPercent: Number.isFinite(Number(cardThemeDefaults.brightnessPercent))
      ? Number(cardThemeDefaults.brightnessPercent)
      : 100,
    srsRulesetUpdatedAt: ""
  };
})();
