(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installSrsProfileMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype.resolveSrsSetSizing = function resolveSrsSetSizing(profile, items) {
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
    };

    SettingsManager.prototype.getSrsProfile = function getSrsProfile(items, pairKey, options) {
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
    };

    SettingsManager.prototype.buildSrsPlanContext = function buildSrsPlanContext(items, pairKey, options) {
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
    };
  }

  root.optionsSettingsInstallSrsProfileMethods = installSrsProfileMethods;
})();
