class SettingsManager {
  constructor() {
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
      srsPairAuto: true,
      srsProfiles: {},
      srsProfileSignals: {},
      srsEnabled: false,
      srsPair: "en-en",
      srsMaxActive: 20,
      srsBootstrapTopN: 800,
      srsInitialActiveCount: 40,
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

  _normalizeInt(value, fallback, minimum, maximum = null) {
    const parsed = Number.parseInt(value, 10);
    const base = Number.isFinite(parsed) ? parsed : fallback;
    const lowerBounded = Math.max(minimum, base);
    if (maximum === null || maximum === undefined) {
      return lowerBounded;
    }
    return Math.min(maximum, lowerBounded);
  }

  resolveSrsSetSizing(profile, items) {
    const fallbackItems = items || {};
    const source = profile || {};
    const maxActive = this._normalizeInt(
      source.srsMaxActive,
      fallbackItems.srsMaxActive || this.defaults.srsMaxActive || 20,
      1
    );
    const bootstrapTopN = this._normalizeInt(
      source.srsBootstrapTopN,
      fallbackItems.srsBootstrapTopN || this.defaults.srsBootstrapTopN || 800,
      200
    );
    const initialActiveCount = this._normalizeInt(
      source.srsInitialActiveCount,
      maxActive || this.defaults.srsInitialActiveCount || 40,
      1,
      bootstrapTopN
    );
    return {
      srsBootstrapTopN: bootstrapTopN,
      srsInitialActiveCount: initialActiveCount
    };
  }

  getSrsProfile(items, pairKey) {
    const profiles = items.srsProfiles || {};
    const profile = profiles[pairKey] || {};
    const srsMaxActive = this._normalizeInt(
      profile.srsMaxActive,
      items.srsMaxActive || this.defaults.srsMaxActive || 20,
      1
    );
    const sizing = this.resolveSrsSetSizing({ ...profile, srsMaxActive }, items);
    return {
      srsMaxActive,
      srsBootstrapTopN: sizing.srsBootstrapTopN,
      srsInitialActiveCount: sizing.srsInitialActiveCount,
      srsSoundEnabled: profile.srsSoundEnabled !== undefined ? profile.srsSoundEnabled : (items.srsSoundEnabled !== false),
      srsHighlightColor: profile.srsHighlightColor || items.srsHighlightColor || this.defaults.srsHighlightColor || "#2F74D0",
      srsFeedbackSrsEnabled: profile.srsFeedbackSrsEnabled !== undefined ? profile.srsFeedbackSrsEnabled : (items.srsFeedbackSrsEnabled !== false),
      srsFeedbackRulesEnabled: profile.srsFeedbackRulesEnabled !== undefined ? profile.srsFeedbackRulesEnabled : (items.srsFeedbackRulesEnabled === true),
      srsExposureLoggingEnabled: profile.srsExposureLoggingEnabled !== undefined ? profile.srsExposureLoggingEnabled : (items.srsExposureLoggingEnabled !== false)
    };
  }

  getSrsProfileSignals(items, pairKey) {
    const signalMap = items.srsProfileSignals || {};
    const profileSignals = signalMap[pairKey] || {};
    const interests = Array.isArray(profileSignals.interests) ? profileSignals.interests : [];
    const objectives = Array.isArray(profileSignals.objectives) ? profileSignals.objectives : [];
    const proficiency = profileSignals.proficiency && typeof profileSignals.proficiency === "object"
      ? profileSignals.proficiency
      : {};
    const empiricalTrends = profileSignals.empiricalTrends && typeof profileSignals.empiricalTrends === "object"
      ? profileSignals.empiricalTrends
      : {};
    const sourcePreferences = profileSignals.sourcePreferences && typeof profileSignals.sourcePreferences === "object"
      ? profileSignals.sourcePreferences
      : {};
    return {
      profileId: typeof profileSignals.profileId === "string" && profileSignals.profileId
        ? profileSignals.profileId
        : "default",
      interests,
      objectives,
      proficiency,
      empiricalTrends,
      sourcePreferences
    };
  }

  buildSrsPlanContext(items, pairKey) {
    const profile = this.getSrsProfile(items, pairKey);
    const signals = this.getSrsProfileSignals(items, pairKey);
    return {
      pair: pairKey,
      profile_id: signals.profileId,
      interests: signals.interests,
      objectives: signals.objectives,
      proficiency: signals.proficiency,
      empirical_trends: signals.empiricalTrends,
      source_preferences: signals.sourcePreferences,
      constraints: {
        max_active_items: profile.srsMaxActive
      },
      sizing: {
        bootstrap_top_n: profile.srsBootstrapTopN,
        initial_active_count: profile.srsInitialActiveCount
      }
    };
  }
}
