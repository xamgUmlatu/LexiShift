class SettingsManager {
  constructor() {
    this.defaults = (globalThis.LexiShift && globalThis.LexiShift.defaults) || {
      enabled: true,
      rules: [],
      highlightEnabled: true,
      highlightColor: "#9AA0A6",
      maxOnePerTextBlock: false,
      allowAdjacentReplacements: true,
      debugEnabled: false,
      debugFocusWord: "",
      uiLanguage: "system",
      rulesSource: "editor",
      rulesFileName: "",
      rulesUpdatedAt: "",
      sourceLanguage: "en",
      targetLanguage: "en",
      srsPairAuto: true,
      srsProfiles: {},
      srsEnabled: false,
      srsPair: "en-en",
      srsMaxActive: 20,
      srsSoundEnabled: true,
      srsHighlightColor: "#2F74D0",
      srsFeedbackSrsEnabled: true,
      srsFeedbackRulesEnabled: false,
      srsExposureLoggingEnabled: true
    };
    this.currentRules = [];
  }

  async load() {
    return new Promise((resolve) => {
      chrome.storage.local.get(this.defaults, resolve);
    });
  }

  async save(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, resolve);
    });
  }

  async updateSrsProfile(pairKey, profile, globalUpdates) {
    const items = await this.load();
    const profiles = items.srsProfiles || {};
    const newProfiles = { ...profiles, [pairKey]: profile };
    const toSave = {
      ...globalUpdates,
      srsProfiles: newProfiles,
      srsPair: pairKey
    };
    await this.save(toSave);
  }

  getSrsProfile(items, pairKey) {
    const profiles = items.srsProfiles || {};
    const profile = profiles[pairKey] || {};
    return {
      srsMaxActive: profile.srsMaxActive || items.srsMaxActive || this.defaults.srsMaxActive || 20,
      srsSoundEnabled: profile.srsSoundEnabled !== undefined ? profile.srsSoundEnabled : (items.srsSoundEnabled !== false),
      srsHighlightColor: profile.srsHighlightColor || items.srsHighlightColor || this.defaults.srsHighlightColor || "#2F74D0",
      srsFeedbackSrsEnabled: profile.srsFeedbackSrsEnabled !== undefined ? profile.srsFeedbackSrsEnabled : (items.srsFeedbackSrsEnabled !== false),
      srsFeedbackRulesEnabled: profile.srsFeedbackRulesEnabled !== undefined ? profile.srsFeedbackRulesEnabled : (items.srsFeedbackRulesEnabled === true),
      srsExposureLoggingEnabled: profile.srsExposureLoggingEnabled !== undefined ? profile.srsExposureLoggingEnabled : (items.srsExposureLoggingEnabled !== false)
    };
  }
}