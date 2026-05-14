(() => {
  if (typeof RulesManager !== "function") {
    return;
  }

  RulesManager.prototype._getProfileLanguagePrefs = function _getProfileLanguagePrefs(items, profileId) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    if (this.settingsManager && typeof this.settingsManager.getProfileLanguagePrefs === "function") {
      return this.settingsManager.getProfileLanguagePrefs(items, { profileId: resolvedProfileId });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    const raw = this._isObject(profileEntry.languagePrefs) ? profileEntry.languagePrefs : {};
    const sourceLanguage = String(raw.sourceLanguage || (items && items.sourceLanguage) || "en").trim() || "en";
    const targetLanguage = String(raw.targetLanguage || (items && items.targetLanguage) || "en").trim() || "en";
    const srsPair = this._normalizePairKey(raw.srsPair, sourceLanguage, targetLanguage);
    return {
      profileId: resolvedProfileId,
      sourceLanguage,
      targetLanguage,
      srsPairAuto: raw.srsPairAuto !== false,
      srsPair,
      targetScriptPrefs: this._isObject(raw.targetScriptPrefs) ? raw.targetScriptPrefs : {}
    };
  };

  RulesManager.prototype._getProfileUiPrefs = function _getProfileUiPrefs(items, profileId) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    if (this.settingsManager && typeof this.settingsManager.getProfileUiPrefs === "function") {
      return this.settingsManager.getProfileUiPrefs(items, { profileId: resolvedProfileId });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    return this._isObject(profileEntry.uiPrefs) ? profileEntry.uiPrefs : {};
  };

  RulesManager.prototype._getProfileModulePrefs = function _getProfileModulePrefs(items, profileId, targetLanguage) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    const resolvedTargetLanguage = String(targetLanguage || "").trim() || "en";
    if (this.settingsManager && typeof this.settingsManager.getProfileModulePrefs === "function") {
      return this.settingsManager.getProfileModulePrefs(items, {
        profileId: resolvedProfileId,
        targetLanguage: resolvedTargetLanguage
      });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    const raw = this._isObject(profileEntry.modulePrefs) ? profileEntry.modulePrefs : {};
    return {
      profileId: resolvedProfileId,
      targetLanguage: resolvedTargetLanguage,
      byId: this._isObject(raw.byId) ? raw.byId : {},
      order: Array.isArray(raw.order) ? raw.order : []
    };
  };

  RulesManager.prototype._pickAppearanceThemeFields = function _pickAppearanceThemeFields(source) {
    const input = this._isObject(source) ? source : {};
    return this._pickFields(input, [
      "backgroundBackdropColor",
      "backgroundOpacity",
      "backgroundPositionX",
      "backgroundPositionY",
      "cardThemeHueDeg",
      "cardThemeSaturationPercent",
      "cardThemeBrightnessPercent",
      "cardThemeTransparencyPercent"
    ]);
  };

  RulesManager.prototype._resolveSrsPairShareData = async function _resolveSrsPairShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const pair = this._normalizePairKey(
      opts.srsPair || opts.pair || languagePrefs.srsPair,
      languagePrefs.sourceLanguage,
      languagePrefs.targetLanguage
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const srsByPair = this._isObject(profileEntry.srsByPair) ? profileEntry.srsByPair : {};
    const srsProfile = this._isObject(srsByPair[pair]) ? srsByPair[pair] : {};
    const srsSignalsByPair = this._isObject(profileEntry.srsSignalsByPair)
      ? profileEntry.srsSignalsByPair
      : {};
    const srsSignals = this._isObject(srsSignalsByPair[pair]) ? srsSignalsByPair[pair] : {};
    const importedSnapshotsByPair = this._isObject(items && items.importedSrsPairSnapshots)
      ? items.importedSrsPairSnapshots
      : {};
    const importedPairSnapshot = this._isObject(importedSnapshotsByPair[`${profileId}:${pair}`])
      ? importedSnapshotsByPair[`${profileId}:${pair}`]
      : null;
    let helperSnapshot = importedPairSnapshot && this._isObject(importedPairSnapshot.helperSnapshot)
      ? importedPairSnapshot.helperSnapshot
      : null;
    let helperRuleset = importedPairSnapshot && this._isObject(importedPairSnapshot.helperRuleset)
      ? importedPairSnapshot.helperRuleset
      : null;

    const helperManager = opts.helperManager;
    if (helperManager && typeof helperManager.getClient === "function") {
      const client = helperManager.getClient();
      if (client && typeof client.getSnapshot === "function") {
        try {
          const response = await client.getSnapshot(pair, profileId);
          if (response && response.ok === true && this._isObject(response.data)) {
            helperSnapshot = response.data;
          }
        } catch (_err) {
          // Keep local imported snapshot fallback when helper is unavailable.
        }
      }
      if (client && typeof client.getRuleset === "function") {
        try {
          const response = await client.getRuleset(pair, profileId);
          if (response && response.ok === true && this._isObject(response.data)) {
            helperRuleset = response.data;
          }
        } catch (_err) {
          // Keep local imported ruleset fallback when helper is unavailable.
        }
      }
    }

    return {
      pair,
      profileId,
      languagePrefs: {
        sourceLanguage: languagePrefs.sourceLanguage,
        targetLanguage: languagePrefs.targetLanguage,
        srsPairAuto: languagePrefs.srsPairAuto !== false,
        srsPair: pair,
        targetScriptPrefs: this._isObject(languagePrefs.targetScriptPrefs)
          ? languagePrefs.targetScriptPrefs
          : {}
      },
      srsProfile: this._isObject(srsProfile) ? srsProfile : {},
      srsSignals: this._isObject(srsSignals) ? srsSignals : {},
      helperSnapshot,
      helperRuleset,
      exportedAt: new Date().toISOString()
    };
  };

  RulesManager.prototype._normalizeImportedSrsPairPayload = function _normalizeImportedSrsPairPayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.srsPair) ? payload.srsPair : payload;
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const rawLanguagePrefs = this._isObject(raw.languagePrefs) ? raw.languagePrefs : {};
    const sourceLanguage = String(rawLanguagePrefs.sourceLanguage || "en").trim() || "en";
    const targetLanguage = String(rawLanguagePrefs.targetLanguage || "en").trim() || "en";
    const pair = this._normalizePairKey(
      raw.pair || rawLanguagePrefs.srsPair,
      sourceLanguage,
      targetLanguage
    );
    return {
      pair,
      languagePrefs: {
        sourceLanguage,
        targetLanguage,
        srsPairAuto: rawLanguagePrefs.srsPairAuto !== false,
        srsPair: pair,
        targetScriptPrefs: this._isObject(rawLanguagePrefs.targetScriptPrefs)
          ? rawLanguagePrefs.targetScriptPrefs
          : {}
      },
      srsProfile: this._isObject(raw.srsProfile) ? raw.srsProfile : {},
      srsSignals: this._isObject(raw.srsSignals) ? raw.srsSignals : {},
      helperSnapshot: this._isObject(raw.helperSnapshot) ? raw.helperSnapshot : null,
      helperRuleset: this._isObject(raw.helperRuleset) ? raw.helperRuleset : null
    };
  };

  RulesManager.prototype._applyImportedSrsPairToProfile = async function _applyImportedSrsPairToProfile(srsPairData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const profilesRoot = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const existingLanguagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const pair = this._normalizePairKey(
      srsPairData && srsPairData.pair,
      srsPairData && srsPairData.languagePrefs && srsPairData.languagePrefs.sourceLanguage,
      srsPairData && srsPairData.languagePrefs && srsPairData.languagePrefs.targetLanguage
    );
    const incomingLanguagePrefs = this._isObject(srsPairData && srsPairData.languagePrefs)
      ? srsPairData.languagePrefs
      : {};
    const mergedLanguagePrefs = {
      ...existingLanguagePrefs,
      ...incomingLanguagePrefs,
      srsPair: pair
    };
    const srsByPair = this._isObject(profileEntry.srsByPair) ? profileEntry.srsByPair : {};
    const srsSignalsByPair = this._isObject(profileEntry.srsSignalsByPair)
      ? profileEntry.srsSignalsByPair
      : {};
    const existingPairProfile = this._isObject(srsByPair[pair]) ? srsByPair[pair] : {};
    const incomingPairProfile = this._isObject(srsPairData && srsPairData.srsProfile)
      ? srsPairData.srsProfile
      : {};
    const existingPairSignals = this._isObject(srsSignalsByPair[pair]) ? srsSignalsByPair[pair] : {};
    const incomingPairSignals = this._isObject(srsPairData && srsPairData.srsSignals)
      ? srsPairData.srsSignals
      : {};
    const nextPairProfile = {
      ...existingPairProfile,
      ...incomingPairProfile
    };
    const nextPairSignals = {
      ...existingPairSignals,
      ...incomingPairSignals
    };
    const nextProfiles = {
      ...profilesRoot,
      [profileId]: {
        ...profileEntry,
        languagePrefs: mergedLanguagePrefs,
        srsByPair: {
          ...srsByPair,
          [pair]: nextPairProfile
        },
        srsSignalsByPair: {
          ...srsSignalsByPair,
          [pair]: nextPairSignals
        }
      }
    };
    const updates = {
      srsProfiles: nextProfiles,
      sourceLanguage: String(mergedLanguagePrefs.sourceLanguage || "en").trim() || "en",
      targetLanguage: String(mergedLanguagePrefs.targetLanguage || "en").trim() || "en",
      srsPairAuto: mergedLanguagePrefs.srsPairAuto !== false,
      srsPair: pair,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId,
      srsEnabled: nextPairProfile.srsEnabled === true,
      srsMaxActive: Number.isFinite(Number(nextPairProfile.srsMaxActive))
        ? Number(nextPairProfile.srsMaxActive)
        : (this.settingsManager.defaults.srsMaxActive || 20),
      srsBootstrapTopN: Number.isFinite(Number(nextPairProfile.srsBootstrapTopN))
        ? Number(nextPairProfile.srsBootstrapTopN)
        : (this.settingsManager.defaults.srsBootstrapTopN || 800),
      srsInitialActiveCount: Number.isFinite(Number(nextPairProfile.srsInitialActiveCount))
        ? Number(nextPairProfile.srsInitialActiveCount)
        : (this.settingsManager.defaults.srsInitialActiveCount || 40),
      srsSoundEnabled: nextPairProfile.srsSoundEnabled !== false,
      srsHighlightColor: String(nextPairProfile.srsHighlightColor || this.settingsManager.defaults.srsHighlightColor || "#2f74d0"),
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
      srsFeedbackSrsEnabled: nextPairProfile.srsFeedbackSrsEnabled !== false,
      srsFeedbackRulesEnabled: nextPairProfile.srsFeedbackRulesEnabled === true,
      srsExposureLoggingEnabled: nextPairProfile.srsExposureLoggingEnabled !== false
    };

    const helperSnapshot = this._isObject(srsPairData && srsPairData.helperSnapshot)
      ? srsPairData.helperSnapshot
      : null;
    const helperRuleset = this._isObject(srsPairData && srsPairData.helperRuleset)
      ? srsPairData.helperRuleset
      : null;
    if (helperSnapshot || helperRuleset) {
      const importedMap = this._isObject(items.importedSrsPairSnapshots)
        ? { ...items.importedSrsPairSnapshots }
        : {};
      importedMap[`${profileId}:${pair}`] = {
        importedAt: new Date().toISOString(),
        helperSnapshot,
        helperRuleset
      };
      updates.importedSrsPairSnapshots = importedMap;
    }

    await this._saveStorage(updates);
    return {
      profileId,
      pair,
      updatedAt: new Date().toISOString(),
      hasHelperData: Boolean(helperSnapshot || helperRuleset)
    };
  };

  RulesManager.prototype._resolveAppearanceShareData = async function _resolveAppearanceShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const uiPrefs = this._getProfileUiPrefs(items, profileId);
    return {
      profileId,
      theme: this._pickAppearanceThemeFields(uiPrefs),
      exportedAt: new Date().toISOString()
    };
  };

  RulesManager.prototype._normalizeImportedAppearancePayload = function _normalizeImportedAppearancePayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.appearanceTheme) ? payload.appearanceTheme : payload;
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const themeSource = this._isObject(raw.theme) ? raw.theme : raw;
    const theme = this._pickAppearanceThemeFields(themeSource);
    if (!Object.keys(theme).length) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    return { theme };
  };

  RulesManager.prototype._applyImportedAppearanceToProfile = async function _applyImportedAppearanceToProfile(appearanceData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const currentUiPrefs = this._getProfileUiPrefs(items, profileId);
    const theme = this._isObject(appearanceData && appearanceData.theme) ? appearanceData.theme : {};
    const nextUiPrefs = {
      ...currentUiPrefs,
      ...theme
    };
    if (this.settingsManager && typeof this.settingsManager.updateProfileUiPrefs === "function") {
      await this.settingsManager.updateProfileUiPrefs(nextUiPrefs, { profileId });
    } else {
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: {
          ...profileEntry,
          uiPrefs: nextUiPrefs
        }
      };
      await this._saveStorage({ srsProfiles: nextProfiles });
    }
    return {
      profileId,
      updatedAt: new Date().toISOString()
    };
  };

})();
