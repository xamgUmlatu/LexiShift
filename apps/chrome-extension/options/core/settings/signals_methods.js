(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installSignalsMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._normalizeSignals = function _normalizeSignals(rawSignals) {
      const raw = this._isObject(rawSignals) ? rawSignals : {};
      return {
        interests: Array.isArray(raw.interests) ? raw.interests : [],
        objectives: Array.isArray(raw.objectives) ? raw.objectives : [],
        proficiency: this._isObject(raw.proficiency) ? raw.proficiency : {},
        difficultyPreferences: this._isObject(raw.difficultyPreferences)
          ? raw.difficultyPreferences
          : {},
        empiricalTrends: this._isObject(raw.empiricalTrends) ? raw.empiricalTrends : {},
        sourcePreferences: this._isObject(raw.sourcePreferences) ? raw.sourcePreferences : {}
      };
    };

    SettingsManager.prototype._pruneSignals = function _pruneSignals(rawSignals) {
      const normalized = this._normalizeSignals(rawSignals);
      const pruneObject = (value) => {
        if (!this._isObject(value)) {
          return undefined;
        }
        const entries = Object.entries(value).filter((entry) => {
          const key = String(entry[0] || "").trim();
          const entryValue = entry[1];
          if (!key) {
            return false;
          }
          if (Array.isArray(entryValue)) {
            return entryValue.length > 0;
          }
          if (this._isObject(entryValue)) {
            return Object.keys(entryValue).length > 0;
          }
          return entryValue !== undefined && entryValue !== null && entryValue !== "";
        });
        return entries.length ? Object.fromEntries(entries) : undefined;
      };
      const nextSignals = {};
      if (normalized.interests.length) {
        nextSignals.interests = [...normalized.interests];
      }
      if (normalized.objectives.length) {
        nextSignals.objectives = [...normalized.objectives];
      }
      const proficiency = pruneObject(normalized.proficiency);
      if (proficiency) {
        nextSignals.proficiency = proficiency;
      }
      const difficultyPreferences = pruneObject(normalized.difficultyPreferences);
      if (difficultyPreferences) {
        nextSignals.difficultyPreferences = difficultyPreferences;
      }
      const empiricalTrends = pruneObject(normalized.empiricalTrends);
      if (empiricalTrends) {
        nextSignals.empiricalTrends = empiricalTrends;
      }
      const sourcePreferences = pruneObject(normalized.sourcePreferences);
      if (sourcePreferences) {
        nextSignals.sourcePreferences = sourcePreferences;
      }
      return nextSignals;
    };

    SettingsManager.prototype.getSrsProfileSignals = function getSrsProfileSignals(items, pairKey, options) {
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
        difficultyPreferences: signals.difficultyPreferences,
        empiricalTrends: signals.empiricalTrends,
        sourcePreferences: signals.sourcePreferences
      };
    };

    SettingsManager.prototype.updateSrsProfileSignals = async function updateSrsProfileSignals(pairKey, updates, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const resolvedPair = this._normalizePairKey(pairKey);
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const existingSignals = this._normalizeSignals(profileEntry.srsSignalsByPair[resolvedPair]);
      const rawUpdates = this._isObject(updates) ? updates : {};
      const nextSignals = this._pruneSignals({
        ...existingSignals,
        ...rawUpdates
      });
      const nextSignalsByPair = {
        ...profileEntry.srsSignalsByPair
      };
      if (Object.keys(nextSignals).length) {
        nextSignalsByPair[resolvedPair] = nextSignals;
      } else {
        delete nextSignalsByPair[resolvedPair];
      }

      const nextProfileEntry = {
        ...profileEntry,
        srsSignalsByPair: nextSignalsByPair
      };
      const nextProfiles = {
        ...profilesRoot,
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
    };
  }

  root.optionsSettingsInstallSignalsMethods = installSignalsMethods;
})();
