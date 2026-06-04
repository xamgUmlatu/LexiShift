(() => {
  if (typeof RulesManager !== "function") {
    return;
  }

  RulesManager.prototype._resolveModuleShareData = async function _resolveModuleShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const moduleId = String(opts.moduleId || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const targetLanguage = String(opts.targetLanguage || languagePrefs.targetLanguage || "en").trim() || "en";
    const modulePrefs = this._getProfileModulePrefs(items, profileId, targetLanguage);
    const byId = this._isObject(modulePrefs.byId) ? modulePrefs.byId : {};
    const order = Array.isArray(modulePrefs.order) ? modulePrefs.order : [];
    const entry = this._isObject(byId[moduleId]) ? byId[moduleId] : { enabled: true };
    return {
      profileId,
      targetLanguage,
      module: {
        moduleId,
        prefs: entry,
        inOrder: order.includes(moduleId)
      },
      exportedAt: new Date().toISOString()
    };
  };

  RulesManager.prototype._normalizeImportedModulePayload = function _normalizeImportedModulePayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.module)
      ? payload.module
      : (this._isObject(payload.moduleItem) ? payload.moduleItem : payload);
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const moduleId = String(raw.moduleId || raw.id || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    let prefs = this._isObject(raw.prefs) ? raw.prefs : null;
    if (!prefs) {
      const derived = {};
      if (raw.enabled !== undefined) {
        derived.enabled = raw.enabled === true;
      }
      if (this._isObject(raw.config)) {
        derived.config = raw.config;
      }
      if (this._isObject(raw.theme)) {
        derived.theme = raw.theme;
      }
      prefs = Object.keys(derived).length ? derived : { enabled: true };
    }
    return {
      moduleId,
      targetLanguage: String(raw.targetLanguage || payload.targetLanguage || "").trim(),
      prefs
    };
  };

  RulesManager.prototype._applyImportedModuleToProfile = async function _applyImportedModuleToProfile(moduleData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const targetLanguage = String(moduleData && moduleData.targetLanguage || languagePrefs.targetLanguage || "en").trim() || "en";
    const moduleId = String(moduleData && moduleData.moduleId || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const modulePrefs = this._getProfileModulePrefs(items, profileId, targetLanguage);
    const byId = this._isObject(modulePrefs.byId) ? modulePrefs.byId : {};
    const order = Array.isArray(modulePrefs.order) ? modulePrefs.order : [];
    const nextById = {
      ...byId,
      [moduleId]: this._isObject(moduleData && moduleData.prefs)
        ? moduleData.prefs
        : { enabled: true }
    };
    const nextOrder = [...order];
    if (!nextOrder.includes(moduleId)) {
      nextOrder.push(moduleId);
    }
    if (this.settingsManager && typeof this.settingsManager.updateProfileModulePrefs === "function") {
      await this.settingsManager.updateProfileModulePrefs(
        { byId: nextById, order: nextOrder },
        { profileId, targetLanguage }
      );
    } else {
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: {
          ...profileEntry,
          modulePrefs: {
            byId: nextById,
            order: nextOrder
          }
        }
      };
      await this._saveStorage({ srsProfiles: nextProfiles });
    }
    return {
      profileId,
      moduleId,
      targetLanguage,
      updatedAt: new Date().toISOString()
    };
  };
})();
