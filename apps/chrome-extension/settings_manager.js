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
      srsPairAuto: true,
      srsSelectedProfileId: "default",
      srsProfileId: "default",
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

  async save(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, resolve);
    });
  }

  _isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  _normalizePairKey(pairKey) {
    const normalized = String(pairKey || "").trim();
    if (normalized) {
      return normalized;
    }
    return String(this.defaults.srsPair || "en-en");
  }

  _normalizeLanguageCode(value, fallback) {
    const normalized = String(value || "").trim();
    if (normalized) {
      return normalized;
    }
    return String(fallback || "").trim() || "en";
  }

  _resolvePairFromLanguages(sourceLanguage, targetLanguage) {
    const source = this._normalizeLanguageCode(sourceLanguage, this.defaults.sourceLanguage || "en");
    const target = this._normalizeLanguageCode(targetLanguage, this.defaults.targetLanguage || "en");
    return `${source}-${target}`;
  }

  normalizeSrsProfileId(profileId) {
    const normalized = String(profileId || "").trim();
    return normalized || this.DEFAULT_PROFILE_ID;
  }

  getSelectedSrsProfileId(items) {
    if (!this._isObject(items)) {
      return this.DEFAULT_PROFILE_ID;
    }
    const configured = items.srsSelectedProfileId !== undefined
      ? items.srsSelectedProfileId
      : items.srsProfileId;
    return this.normalizeSrsProfileId(configured);
  }

  async updateSelectedSrsProfileId(profileId) {
    const resolvedProfileId = this.normalizeSrsProfileId(profileId);
    await this.save({
      srsSelectedProfileId: resolvedProfileId,
      // Runtime readers (content script) consume this key directly.
      srsProfileId: resolvedProfileId
    });
    return resolvedProfileId;
  }

  getProfileLanguagePrefs(items, options) {
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const fallback = {
      sourceLanguage: this._normalizeLanguageCode(
        items && items.sourceLanguage,
        this.defaults.sourceLanguage || "en"
      ),
      targetLanguage: this._normalizeLanguageCode(
        items && items.targetLanguage,
        this.defaults.targetLanguage || "en"
      ),
      srsPairAuto: items && items.srsPairAuto !== undefined ? items.srsPairAuto === true : true,
      srsPair: this._normalizePairKey(
        (items && items.srsPair) || this._resolvePairFromLanguages(
          items && items.sourceLanguage,
          items && items.targetLanguage
        )
      )
    };
    const normalized = this._normalizeProfileLanguagePrefs(profileEntry.languagePrefs, fallback);
    return {
      profileId,
      ...normalized
    };
  }

  async publishProfileLanguagePrefs(languagePrefs, options) {
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
    );
    const normalized = this._normalizeProfileLanguagePrefs(languagePrefs, {
      sourceLanguage: this.defaults.sourceLanguage || "en",
      targetLanguage: this.defaults.targetLanguage || "en",
      srsPairAuto: true,
      srsPair: this.defaults.srsPair || "en-en"
    });
    const updates = {
      sourceLanguage: normalized.sourceLanguage,
      targetLanguage: normalized.targetLanguage,
      srsPairAuto: normalized.srsPairAuto,
      srsPair: normalized.srsPair,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId
    };
    await this.save(updates);
    return {
      profileId,
      ...normalized
    };
  }

  async updateProfileLanguagePrefs(languagePrefs, options) {
    const items = await this.load();
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const root = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const fallback = this.getProfileLanguagePrefs(items, { profileId });
    const normalized = this._normalizeProfileLanguagePrefs(languagePrefs, fallback);

    const nextProfileEntry = {
      ...profileEntry,
      languagePrefs: normalized
    };
    const nextProfiles = {
      ...root,
      [profileId]: nextProfileEntry
    };
    await this.save({
      srsProfiles: nextProfiles
    });
    await this.publishProfileLanguagePrefs(normalized, { profileId });
    return {
      profileId,
      ...normalized
    };
  }

  _getProfilesRoot(items) {
    return this._isObject(items && items.srsProfiles) ? items.srsProfiles : {};
  }

  _getProfileEntry(items, profileId) {
    const root = this._getProfilesRoot(items);
    const resolvedProfileId = this.normalizeSrsProfileId(profileId);
    const raw = this._isObject(root[resolvedProfileId]) ? root[resolvedProfileId] : {};
    return {
      srsByPair: this._isObject(raw.srsByPair) ? raw.srsByPair : {},
      srsSignalsByPair: this._isObject(raw.srsSignalsByPair) ? raw.srsSignalsByPair : {},
      languagePrefs: this._isObject(raw.languagePrefs) ? raw.languagePrefs : {},
      uiPrefs: this._isObject(raw.uiPrefs) ? raw.uiPrefs : {}
    };
  }

  _normalizeProfileLanguagePrefs(rawPrefs, fallback) {
    const raw = this._isObject(rawPrefs) ? rawPrefs : {};
    const base = this._isObject(fallback) ? fallback : {};
    const sourceLanguage = this._normalizeLanguageCode(
      raw.sourceLanguage,
      base.sourceLanguage || this.defaults.sourceLanguage || "en"
    );
    const targetLanguage = this._normalizeLanguageCode(
      raw.targetLanguage,
      base.targetLanguage || this.defaults.targetLanguage || "en"
    );
    const srsPairAuto = raw.srsPairAuto !== undefined
      ? (raw.srsPairAuto === true)
      : (base.srsPairAuto !== undefined ? base.srsPairAuto === true : true);
    const fallbackPair = this._resolvePairFromLanguages(sourceLanguage, targetLanguage);
    const srsPair = this._normalizePairKey(raw.srsPair || base.srsPair || fallbackPair);
    return {
      sourceLanguage,
      targetLanguage,
      srsPairAuto,
      srsPair
    };
  }

  _normalizeProfileUiPrefs(rawPrefs, fallback) {
    const raw = this._isObject(rawPrefs) ? rawPrefs : {};
    const base = this._isObject(fallback) ? fallback : {};
    const backgroundAssetId = String(
      raw.backgroundAssetId !== undefined ? raw.backgroundAssetId : (base.backgroundAssetId || "")
    ).trim();
    const requestedEnabled = raw.backgroundEnabled !== undefined
      ? raw.backgroundEnabled === true
      : (base.backgroundEnabled === true);
    const backgroundOpacity = this._normalizeFloat(
      raw.backgroundOpacity !== undefined ? raw.backgroundOpacity : base.backgroundOpacity,
      this.defaults.profileBackgroundOpacity || 0.18,
      0,
      1
    );
    const backgroundBackdropColor = this._normalizeHexColor(
      raw.backgroundBackdropColor !== undefined
        ? raw.backgroundBackdropColor
        : base.backgroundBackdropColor,
      this.defaults.profileBackgroundBackdropColor || "#fbf7f0"
    );
    return {
      backgroundEnabled: requestedEnabled && Boolean(backgroundAssetId),
      backgroundAssetId,
      backgroundOpacity,
      backgroundBackdropColor
    };
  }

  getProfileUiPrefs(items, options) {
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const fallback = {
      backgroundEnabled: items && items.profileBackgroundEnabled === true,
      backgroundAssetId: String(items && items.profileBackgroundAssetId || "").trim(),
      backgroundOpacity: this._normalizeFloat(
        items && items.profileBackgroundOpacity,
        this.defaults.profileBackgroundOpacity || 0.18,
        0,
        1
      ),
      backgroundBackdropColor: this._normalizeHexColor(
        items && items.profileBackgroundBackdropColor,
        this.defaults.profileBackgroundBackdropColor || "#fbf7f0"
      )
    };
    const normalized = this._normalizeProfileUiPrefs(profileEntry.uiPrefs, fallback);
    return {
      profileId,
      ...normalized
    };
  }

  async publishProfileUiPrefs(uiPrefs, options) {
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
    );
    const normalized = this._normalizeProfileUiPrefs(uiPrefs, {
      backgroundEnabled: false,
      backgroundAssetId: "",
      backgroundOpacity: this.defaults.profileBackgroundOpacity || 0.18,
      backgroundBackdropColor: this.defaults.profileBackgroundBackdropColor || "#fbf7f0"
    });
    const updates = {
      profileBackgroundEnabled: normalized.backgroundEnabled,
      profileBackgroundAssetId: normalized.backgroundAssetId,
      profileBackgroundOpacity: normalized.backgroundOpacity,
      profileBackgroundBackdropColor: normalized.backgroundBackdropColor,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId
    };
    await this.save(updates);
    return {
      profileId,
      ...normalized
    };
  }

  async updateProfileUiPrefs(uiPrefs, options) {
    const items = await this.load();
    const opts = options && typeof options === "object" ? options : {};
    const publishRuntime = opts.publishRuntime !== false;
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const root = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const fallback = this.getProfileUiPrefs(items, { profileId });
    const normalized = this._normalizeProfileUiPrefs(uiPrefs, fallback);
    const nextProfileEntry = {
      ...profileEntry,
      uiPrefs: normalized
    };
    const nextProfiles = {
      ...root,
      [profileId]: nextProfileEntry
    };
    await this.save({
      srsProfiles: nextProfiles,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId
    });
    if (publishRuntime) {
      await this.publishProfileUiPrefs(normalized, { profileId });
    }
    return {
      profileId,
      ...normalized,
      publishedRuntime: publishRuntime
    };
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

  _normalizeFloat(value, fallback, minimum, maximum = null) {
    const parsed = Number.parseFloat(value);
    const base = Number.isFinite(parsed) ? parsed : fallback;
    const lowerBounded = Math.max(minimum, base);
    if (maximum === null || maximum === undefined) {
      return lowerBounded;
    }
    return Math.min(maximum, lowerBounded);
  }

  _normalizeHexColor(value, fallback) {
    const fallbackColor = String(fallback || "#fbf7f0").trim();
    const resolvedFallback = /^#[0-9a-fA-F]{6}$/.test(fallbackColor)
      ? fallbackColor.toLowerCase()
      : "#fbf7f0";
    const candidate = String(value || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(candidate)) {
      return candidate.toLowerCase();
    }
    return resolvedFallback;
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

  getSrsProfile(items, pairKey, options) {
    const opts = options && typeof options === "object" ? options : {};
    const resolvedPair = this._normalizePairKey(pairKey);
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const rawProfile = this._isObject(profileEntry.srsByPair[resolvedPair])
      ? profileEntry.srsByPair[resolvedPair]
      : {};

    const srsMaxActive = this._normalizeInt(
      rawProfile.srsMaxActive,
      this.defaults.srsMaxActive || 20,
      1
    );
    const sizing = this.resolveSrsSetSizing(
      {
        ...rawProfile,
        srsMaxActive
      },
      this.defaults
    );

    return {
      profileId,
      srsEnabled: rawProfile.srsEnabled === true,
      srsMaxActive,
      srsBootstrapTopN: sizing.srsBootstrapTopN,
      srsInitialActiveCount: sizing.srsInitialActiveCount,
      srsSoundEnabled: rawProfile.srsSoundEnabled !== undefined
        ? rawProfile.srsSoundEnabled === true
        : (this.defaults.srsSoundEnabled !== false),
      srsHighlightColor: rawProfile.srsHighlightColor || this.defaults.srsHighlightColor || "#2F74D0",
      srsFeedbackSrsEnabled: rawProfile.srsFeedbackSrsEnabled !== undefined
        ? rawProfile.srsFeedbackSrsEnabled === true
        : (this.defaults.srsFeedbackSrsEnabled !== false),
      srsFeedbackRulesEnabled: rawProfile.srsFeedbackRulesEnabled === true,
      srsExposureLoggingEnabled: rawProfile.srsExposureLoggingEnabled !== undefined
        ? rawProfile.srsExposureLoggingEnabled === true
        : (this.defaults.srsExposureLoggingEnabled !== false)
    };
  }

  _normalizeSignals(rawSignals) {
    const raw = this._isObject(rawSignals) ? rawSignals : {};
    return {
      interests: Array.isArray(raw.interests) ? raw.interests : [],
      objectives: Array.isArray(raw.objectives) ? raw.objectives : [],
      proficiency: this._isObject(raw.proficiency) ? raw.proficiency : {},
      empiricalTrends: this._isObject(raw.empiricalTrends) ? raw.empiricalTrends : {},
      sourcePreferences: this._isObject(raw.sourcePreferences) ? raw.sourcePreferences : {}
    };
  }

  getSrsProfileSignals(items, pairKey, options) {
    const opts = options && typeof options === "object" ? options : {};
    const resolvedPair = this._normalizePairKey(pairKey);
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const signals = this._normalizeSignals(profileEntry.srsSignalsByPair[resolvedPair]);
    return {
      profileId,
      resolvedProfileId: profileId,
      interests: signals.interests,
      objectives: signals.objectives,
      proficiency: signals.proficiency,
      empiricalTrends: signals.empiricalTrends,
      sourcePreferences: signals.sourcePreferences
    };
  }

  async updateSrsProfileSignals(pairKey, updates, options) {
    const items = await this.load();
    const opts = options && typeof options === "object" ? options : {};
    const resolvedPair = this._normalizePairKey(pairKey);
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const root = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const existingSignals = this._normalizeSignals(profileEntry.srsSignalsByPair[resolvedPair]);
    const rawUpdates = this._isObject(updates) ? updates : {};
    const nextSignals = this._normalizeSignals({
      ...existingSignals,
      ...rawUpdates
    });

    const nextProfileEntry = {
      ...profileEntry,
      srsSignalsByPair: {
        ...profileEntry.srsSignalsByPair,
        [resolvedPair]: nextSignals
      }
    };
    const nextProfiles = {
      ...root,
      [profileId]: nextProfileEntry
    };
    await this.save({
      srsProfiles: nextProfiles,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId
    });
    return {
      pairKey: resolvedPair,
      profileId,
      resolvedProfileId: profileId
    };
  }

  async updateSrsProfile(pairKey, profile, globalUpdates, options) {
    const items = await this.load();
    const opts = options && typeof options === "object" ? options : {};
    const resolvedPair = this._normalizePairKey(pairKey);
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
    );
    const root = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const globalPrefs = this._isObject(globalUpdates) ? globalUpdates : {};
    const languagePrefs = this._normalizeProfileLanguagePrefs(
      {
        sourceLanguage: globalPrefs.sourceLanguage,
        targetLanguage: globalPrefs.targetLanguage,
        srsPairAuto: globalPrefs.srsPairAuto,
        srsPair: resolvedPair
      },
      profileEntry.languagePrefs
    );
    const nextProfileEntry = {
      ...profileEntry,
      languagePrefs,
      srsByPair: {
        ...profileEntry.srsByPair,
        [resolvedPair]: this._isObject(profile) ? { ...profile } : {}
      }
    };
    const newProfiles = {
      ...root,
      [profileId]: nextProfileEntry
    };
    const toSave = {
      ...(this._isObject(globalUpdates) ? globalUpdates : {}),
      srsProfiles: newProfiles,
      srsPair: resolvedPair,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId
    };
    await this.save(toSave);
    return { pairKey: resolvedPair, profileId };
  }

  async publishSrsRuntimeProfile(pairKey, profile, extraUpdates, options) {
    const opts = options && typeof options === "object" ? options : {};
    const runtimeProfile = this._isObject(profile) ? profile : {};
    const resolvedPair = this._normalizePairKey(pairKey);
    const profileId = this.normalizeSrsProfileId(
      opts.profileId !== undefined ? opts.profileId : runtimeProfile.profileId
    );
    const updates = {
      srsPair: resolvedPair,
      srsProfileId: profileId,
      srsEnabled: runtimeProfile.srsEnabled === true,
      srsMaxActive: runtimeProfile.srsMaxActive || this.defaults.srsMaxActive || 40,
      srsBootstrapTopN: runtimeProfile.srsBootstrapTopN || this.defaults.srsBootstrapTopN || 800,
      srsInitialActiveCount: runtimeProfile.srsInitialActiveCount || this.defaults.srsInitialActiveCount || 40,
      srsSoundEnabled: runtimeProfile.srsSoundEnabled !== false,
      srsHighlightColor: runtimeProfile.srsHighlightColor || this.defaults.srsHighlightColor || "#2F74D0",
      srsFeedbackSrsEnabled: runtimeProfile.srsFeedbackSrsEnabled !== false,
      srsFeedbackRulesEnabled: runtimeProfile.srsFeedbackRulesEnabled === true,
      srsExposureLoggingEnabled: runtimeProfile.srsExposureLoggingEnabled !== false,
      ...(this._isObject(extraUpdates) ? extraUpdates : {})
    };
    await this.save(updates);
    return updates;
  }

  buildSrsPlanContext(items, pairKey, options) {
    const opts = options && typeof options === "object" ? options : {};
    const profile = this.getSrsProfile(items, pairKey, {
      profileId: opts.profileId
    });
    const signals = this.getSrsProfileSignals(items, pairKey, {
      profileId: profile.profileId
    });
    return {
      pair: this._normalizePairKey(pairKey),
      profile_id: profile.profileId || this.DEFAULT_PROFILE_ID,
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
