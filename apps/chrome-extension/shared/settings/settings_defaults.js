(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const profileUiTheme = root.profileUiTheme && typeof root.profileUiTheme === "object"
    ? root.profileUiTheme
    : {};
  const cardThemeLimits = profileUiTheme.CARD_THEME_LIMITS && typeof profileUiTheme.CARD_THEME_LIMITS === "object"
    ? profileUiTheme.CARD_THEME_LIMITS
    : {};
  const hueDefaults = cardThemeLimits.hueDeg && typeof cardThemeLimits.hueDeg === "object"
    ? cardThemeLimits.hueDeg
    : { defaultValue: 0 };
  const saturationDefaults = cardThemeLimits.saturationPercent && typeof cardThemeLimits.saturationPercent === "object"
    ? cardThemeLimits.saturationPercent
    : { defaultValue: 100 };
  const brightnessDefaults = cardThemeLimits.brightnessPercent && typeof cardThemeLimits.brightnessPercent === "object"
    ? cardThemeLimits.brightnessPercent
    : { defaultValue: 100 };

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
    profileCardThemeHueDeg: Number.isFinite(Number(hueDefaults.defaultValue))
      ? Number(hueDefaults.defaultValue)
      : 0,
    profileCardThemeSaturationPercent: Number.isFinite(Number(saturationDefaults.defaultValue))
      ? Number(saturationDefaults.defaultValue)
      : 100,
    profileCardThemeBrightnessPercent: Number.isFinite(Number(brightnessDefaults.defaultValue))
      ? Number(brightnessDefaults.defaultValue)
      : 100,
    srsRulesetUpdatedAt: ""
  };
})();
