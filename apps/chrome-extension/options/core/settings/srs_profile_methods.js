(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_SEMANTIC_FALLBACK_POLICY = "abstain_on_unavailable";
  const SEMANTIC_FALLBACK_POLICIES = new Set([
    "legacy_on_unavailable",
    "abstain_on_unavailable",
    "soft_affordance_on_unavailable"
  ]);
  const DISPLAYABLE_SRS_STORY_PAIRS = new Set([
    "de-de",
    "de-en",
    "en-de",
    "en-en",
    "en-es",
    "en-ja",
    "es-en",
    "es-es",
    "ja-ja"
  ]);

  function installSrsProfileMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype.resolveSrsSetSizing = function resolveSrsSetSizing(profile, items) {
      const fallbackItems = items || {};
      const source = profile || {};
      const maxActive = this._normalizeInt(
        source.srsMaxActive,
        fallbackItems.srsMaxActive || this.defaults.srsMaxActive,
        1
      );
      const initialActiveCount = this._normalizeInt(
        source.srsInitialActiveCount,
        maxActive || this.defaults.srsInitialActiveCount,
        1
      );
      return {
        srsBootstrapTopN: null,
        srsInitialActiveCount: initialActiveCount
      };
    };

    SettingsManager.prototype._normalizeSrsSemanticFallbackPolicy = function _normalizeSrsSemanticFallbackPolicy(rawPolicy) {
      const normalized = String(rawPolicy || DEFAULT_SEMANTIC_FALLBACK_POLICY).trim()
        || DEFAULT_SEMANTIC_FALLBACK_POLICY;
      if (SEMANTIC_FALLBACK_POLICIES.has(normalized)) {
        return normalized;
      }
      return DEFAULT_SEMANTIC_FALLBACK_POLICY;
    };

    SettingsManager.prototype.getSrsProfile = function getSrsProfile(items, pairKey, options) {
      const opts = options && typeof options === "object" ? options : {};
      const resolvedPair = this._normalizePairKey(pairKey);
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profileEntry = this._getProfileEntry(items, profileId);
      const srsStoryExists = this._isObject(profileEntry.srsByPair[resolvedPair]);
      const rawProfile = srsStoryExists
        ? profileEntry.srsByPair[resolvedPair]
        : {};
      const srsPairCount = Object.keys(profileEntry.srsByPair).length;

      const srsMaxActive = this._normalizeInt(
        rawProfile.srsMaxActive,
        this.defaults.srsMaxActive,
        1
      );
      const sizing = this.resolveSrsSetSizing(
        {
          ...rawProfile,
          srsMaxActive
        },
        this.defaults
      );
      const autoRefreshMinGoodEasy = this._normalizeInt(
        rawProfile.srsAutoRefreshMinGoodEasy,
        this.defaults.srsAutoRefreshMinGoodEasy,
        1
      );
      const autoRefreshRepeatMinGoodEasy = Math.max(
        autoRefreshMinGoodEasy,
        this._normalizeInt(
          rawProfile.srsAutoRefreshRepeatMinGoodEasy,
          this.defaults.srsAutoRefreshRepeatMinGoodEasy,
          1
        )
      );

      return {
        profileId,
        srsPairCount,
        srsStoryExists,
        srsEnabled: rawProfile.srsEnabled === true,
        srsMaxActive,
        srsBootstrapTopN: sizing.srsBootstrapTopN,
        srsInitialActiveCount: sizing.srsInitialActiveCount,
        srsSoundEnabled: rawProfile.srsSoundEnabled !== undefined
          ? rawProfile.srsSoundEnabled === true
          : (this.defaults.srsSoundEnabled !== false),
        srsHighlightColor: rawProfile.srsHighlightColor || this.defaults.srsHighlightColor,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: DEFAULT_SEMANTIC_FALLBACK_POLICY,
        srsFeedbackSrsEnabled: true,
        srsFeedbackRulesEnabled: false,
        srsExposureLoggingEnabled: rawProfile.srsExposureLoggingEnabled !== undefined
          ? rawProfile.srsExposureLoggingEnabled === true
          : (this.defaults.srsExposureLoggingEnabled !== false),
        srsAutoRefreshEnabled: true,
        srsAutoRefreshMinFeedbackEvents: this._normalizeInt(
          rawProfile.srsAutoRefreshMinFeedbackEvents,
          this.defaults.srsAutoRefreshMinFeedbackEvents,
          1
        ),
        srsAutoRefreshMinGoodEasy: autoRefreshMinGoodEasy,
        srsAutoRefreshRepeatMinGoodEasy: autoRefreshRepeatMinGoodEasy,
        srsAutoRefreshCooldownMinutes: this._normalizeInt(
          rawProfile.srsAutoRefreshCooldownMinutes,
          this.defaults.srsAutoRefreshCooldownMinutes,
          0
        )
      };
    };

    SettingsManager.prototype.listSrsProfilePairs = function listSrsProfilePairs(items, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const activePair = this._normalizePairKey(
        opts.activePair !== undefined
          ? opts.activePair
          : (items && items.srsPair)
      );
      const profileEntry = this._getProfileEntry(items, profileId);
      return Object.entries(profileEntry.srsByPair)
        .map(([pairKey, rawProfile], creationIndex) => {
          if (!pairKey || !this._isObject(rawProfile)) {
            return null;
          }
          const resolvedPair = this._normalizePairKey(pairKey);
          if (!this.isDisplayableSrsStoryPair(resolvedPair)) {
            return null;
          }
          const [sourceLanguage = "", targetLanguage = ""] = resolvedPair.split("-");
          const srsEnabled = rawProfile.srsEnabled === true;
          return {
            pairKey: resolvedPair,
            sourceLanguage,
            targetLanguage,
            profileId,
            srsEnabled,
            isActive: resolvedPair === activePair,
            creationIndex,
            srsMaxActive: this._normalizeInt(
              rawProfile.srsMaxActive,
              this.defaults.srsMaxActive,
              1
            )
          };
        })
        .filter(Boolean);
    };

    SettingsManager.prototype.isDisplayableSrsStoryPair = function isDisplayableSrsStoryPair(pairKey) {
      return DISPLAYABLE_SRS_STORY_PAIRS.has(this._normalizePairKey(pairKey));
    };

    SettingsManager.prototype._selectSrsRuntimePairAfterDelete = function _selectSrsRuntimePairAfterDelete(
      nextSrsByPair,
      deletedPair,
      items,
      profileEntry
    ) {
      const remainingEntries = Object.entries(nextSrsByPair)
        .filter(([pairKey, rawProfile]) => pairKey && this._isObject(rawProfile))
        .map(([pairKey, rawProfile]) => ({
          pairKey: this._normalizePairKey(pairKey),
          srsEnabled: rawProfile.srsEnabled === true,
          rawProfile
        }))
        .filter((entry) => (
          entry.pairKey
          && entry.pairKey !== deletedPair
          && this.isDisplayableSrsStoryPair(entry.pairKey)
        ));
      if (!remainingEntries.length) {
        return null;
      }
      const currentPair = this._normalizePairKey(
        (items && items.srsPair)
        || (profileEntry.languagePrefs && profileEntry.languagePrefs.srsPair)
        || ""
      );
      const currentEntry = remainingEntries.find((entry) => entry.pairKey === currentPair);
      if (currentEntry) {
        return currentEntry;
      }
      return [...remainingEntries].sort((left, right) => {
        if (left.srsEnabled !== right.srsEnabled) {
          return left.srsEnabled ? -1 : 1;
        }
        return left.pairKey.localeCompare(right.pairKey);
      })[0];
    };

    SettingsManager.prototype.updateSrsProfile = async function updateSrsProfile(pairKey, profile, globalUpdates, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const resolvedPair = this._normalizePairKey(pairKey);
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
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
        ...profilesRoot,
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
    };

    SettingsManager.prototype.activateSrsProfilePair = async function activateSrsProfilePair(pairKey, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const resolvedPair = this._normalizePairKey(pairKey);
      const [sourceLanguage = "", targetLanguage = ""] = resolvedPair.split("-");
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const activeProfile = this._isObject(profileEntry.srsByPair[resolvedPair])
        ? profileEntry.srsByPair[resolvedPair]
        : {};
      const nextSrsByPair = Object.entries(profileEntry.srsByPair)
        .reduce((accumulator, [entryPairKey, rawProfile]) => {
          if (!entryPairKey || !this._isObject(rawProfile)) {
            return accumulator;
          }
          accumulator[entryPairKey] = {
            ...rawProfile,
            srsEnabled: this._normalizePairKey(entryPairKey) === resolvedPair
          };
          return accumulator;
        }, {});
      nextSrsByPair[resolvedPair] = {
        ...activeProfile,
        srsEnabled: true
      };

      const requestedLanguagePrefs = {
        ...profileEntry.languagePrefs,
        sourceLanguage,
        targetLanguage,
        srsPairAuto: true,
        srsPair: resolvedPair
      };
      const fallbackLanguagePrefs = typeof this.getProfileLanguagePrefs === "function"
        ? this.getProfileLanguagePrefs(items, { profileId })
        : profileEntry.languagePrefs;
      const languagePrefs = typeof this._normalizeProfileLanguagePrefs === "function"
        ? this._normalizeProfileLanguagePrefs(requestedLanguagePrefs, fallbackLanguagePrefs)
        : requestedLanguagePrefs;
      let normalizedModulePrefs = null;
      if (typeof this.getProfileModulePrefs === "function") {
        normalizedModulePrefs = this.getProfileModulePrefs(items, {
          profileId,
          targetLanguage: languagePrefs.targetLanguage
        });
      }
      const nextProfileEntry = {
        ...profileEntry,
        languagePrefs,
        srsByPair: nextSrsByPair
      };
      const savePayload = {
        srsProfiles: {
          ...profilesRoot,
          [profileId]: nextProfileEntry
        },
        sourceLanguage: languagePrefs.sourceLanguage,
        targetLanguage: languagePrefs.targetLanguage,
        targetDisplayScript: typeof this._resolveTargetDisplayScript === "function"
          ? this._resolveTargetDisplayScript(languagePrefs, normalizedModulePrefs)
          : (items && items.targetDisplayScript) || this.defaults.targetDisplayScript || "kanji",
        srsPairAuto: languagePrefs.srsPairAuto,
        srsPair: languagePrefs.srsPair,
        srsEnabled: true,
        srsSelectedProfileId: profileId,
        srsProfileId: profileId
      };
      if (this._isObject(normalizedModulePrefs)) {
        savePayload.popupModulePrefs = normalizedModulePrefs;
      }
      await this.save(savePayload);
      return {
        pairKey: resolvedPair,
        profileId,
        sourceLanguage: languagePrefs.sourceLanguage,
        targetLanguage: languagePrefs.targetLanguage
      };
    };

    SettingsManager.prototype.deleteSrsProfilePair = async function deleteSrsProfilePair(pairKey, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const resolvedPair = this._normalizePairKey(pairKey);
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const nextSrsByPair = { ...profileEntry.srsByPair };
      const nextSignalsByPair = { ...profileEntry.srsSignalsByPair };
      delete nextSrsByPair[resolvedPair];
      delete nextSignalsByPair[resolvedPair];
      const nextRuntimeEntry = this._selectSrsRuntimePairAfterDelete(
        nextSrsByPair,
        resolvedPair,
        items,
        profileEntry
      );
      const nextRuntimePair = nextRuntimeEntry ? nextRuntimeEntry.pairKey : "";
      const nextLanguagePrefs = nextRuntimePair
        ? {
            ...profileEntry.languagePrefs,
            sourceLanguage: nextRuntimePair.split("-")[0] || "",
            targetLanguage: nextRuntimePair.split("-")[1] || "",
            srsPairAuto: true,
            srsPair: nextRuntimePair
          }
        : profileEntry.languagePrefs;
      const nextProfileEntry = {
        ...profileEntry,
        languagePrefs: nextLanguagePrefs,
        srsByPair: nextSrsByPair,
        srsSignalsByPair: nextSignalsByPair
      };
      const savePayload = {
        srsProfiles: {
          ...profilesRoot,
          [profileId]: nextProfileEntry
        },
        srsSelectedProfileId: profileId,
        srsProfileId: profileId,
        srsPair: nextRuntimePair || resolvedPair,
        srsEnabled: nextRuntimeEntry ? nextRuntimeEntry.srsEnabled === true : false
      };
      if (nextRuntimePair) {
        savePayload.sourceLanguage = nextLanguagePrefs.sourceLanguage;
        savePayload.targetLanguage = nextLanguagePrefs.targetLanguage;
        savePayload.srsPairAuto = true;
      }
      await this.save({
        ...savePayload
      });
      return {
        pairKey: resolvedPair,
        profileId,
        nextPairKey: nextRuntimePair || null,
        remainingPairCount: Object.keys(nextSrsByPair).length
      };
    };

    SettingsManager.prototype.publishSrsRuntimeProfile = async function publishSrsRuntimeProfile(pairKey, profile, extraUpdates, options) {
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
        srsMaxActive: runtimeProfile.srsMaxActive || this.defaults.srsMaxActive,
        srsBootstrapTopN: null,
        srsInitialActiveCount: runtimeProfile.srsInitialActiveCount || this.defaults.srsInitialActiveCount,
        srsSoundEnabled: runtimeProfile.srsSoundEnabled !== false,
        srsHighlightColor: runtimeProfile.srsHighlightColor || this.defaults.srsHighlightColor,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: DEFAULT_SEMANTIC_FALLBACK_POLICY,
        srsFeedbackSrsEnabled: true,
        srsFeedbackRulesEnabled: false,
        srsExposureLoggingEnabled: runtimeProfile.srsExposureLoggingEnabled !== false,
        srsAutoRefreshEnabled: true,
        srsAutoRefreshMinFeedbackEvents: runtimeProfile.srsAutoRefreshMinFeedbackEvents
          || this.defaults.srsAutoRefreshMinFeedbackEvents,
        srsAutoRefreshMinGoodEasy: runtimeProfile.srsAutoRefreshMinGoodEasy
          || this.defaults.srsAutoRefreshMinGoodEasy,
        srsAutoRefreshRepeatMinGoodEasy: runtimeProfile.srsAutoRefreshRepeatMinGoodEasy
          || this.defaults.srsAutoRefreshRepeatMinGoodEasy,
        srsAutoRefreshCooldownMinutes: runtimeProfile.srsAutoRefreshCooldownMinutes
          ?? this.defaults.srsAutoRefreshCooldownMinutes,
        ...(this._isObject(extraUpdates) ? extraUpdates : {})
      };
      await this.save(updates);
      return updates;
    };

    SettingsManager.prototype.composeSrsPlanContext = function composeSrsPlanContext(pairKey, profile, signals, options) {
      const opts = options && typeof options === "object" ? options : {};
      const runtimeProfile = this._isObject(profile) ? profile : {};
      const normalizedSignals = this._normalizeSignals(signals);
      const resolvedPair = this._normalizePairKey(pairKey);
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : runtimeProfile.profileId
      );
      return {
        pair: resolvedPair,
        profile_id: profileId || this.DEFAULT_PROFILE_ID,
        interests: normalizedSignals.interests,
        objectives: normalizedSignals.objectives,
        proficiency: normalizedSignals.proficiency,
        difficulty_preferences: normalizedSignals.difficultyPreferences,
        empirical_trends: normalizedSignals.empiricalTrends,
        source_preferences: normalizedSignals.sourcePreferences,
        constraints: {
          max_active_items: runtimeProfile.srsMaxActive
        },
        sizing: {
          bootstrap_top_n: null,
          initial_active_count: runtimeProfile.srsInitialActiveCount
        }
      };
    };

    SettingsManager.prototype.buildSrsPlanContext = function buildSrsPlanContext(items, pairKey, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profile = this.getSrsProfile(items, pairKey, {
        profileId: opts.profileId
      });
      const signals = this.getSrsProfileSignals(items, pairKey, {
        profileId: profile.profileId
      });
      return this.composeSrsPlanContext(pairKey, profile, signals, {
        profileId: profile.profileId
      });
    };
  }

  root.optionsSettingsInstallSrsProfileMethods = installSrsProfileMethods;
})();
