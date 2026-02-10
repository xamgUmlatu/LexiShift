class SettingsManager {
  constructor() {
    this.DEFAULT_PROFILE_ID = "default";
    this.defaults = (globalThis.LexiShift && globalThis.LexiShift.defaults) || {
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
      srsPairAuto: true,
      srsSelectedProfileId: "default",
      srsProfileId: "default",
      optionsSelectedProfileId: "default",
      srsProfiles: {},
      srsEnabled: false,
      srsPair: "en-en",
      srsMaxActive: 20,
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
      profileBackgroundBackdropColor: "#fbf7f0"
    };
    this.currentRules = [];
  }

  async load() {
    return new Promise((resolve) => {
      chrome.storage.local.get(this.defaults, resolve);
    });
  }

  async loadRaw() {
    return new Promise((resolve) => {
      chrome.storage.local.get(null, resolve);
    });
  }

  async save(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, resolve);
    });
  }
}

(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const installers = [
    root.optionsSettingsInstallBaseMethods,
    root.optionsSettingsInstallLanguageMethods,
    root.optionsSettingsInstallUiPrefsMethods,
    root.optionsSettingsInstallSignalsMethods,
    root.optionsSettingsInstallSrsProfileMethods
  ];
  for (const install of installers) {
    if (typeof install === "function") {
      install(SettingsManager);
    } else {
      console.warn("[LexiShift][Options] Missing SettingsManager installer.");
    }
  }
})();
