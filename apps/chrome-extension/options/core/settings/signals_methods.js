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
        empiricalTrends: this._isObject(raw.empiricalTrends) ? raw.empiricalTrends : {},
        sourcePreferences: this._isObject(raw.sourcePreferences) ? raw.sourcePreferences : {}
      };
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
