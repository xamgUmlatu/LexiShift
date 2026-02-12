(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installModulePrefsMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._getPopupModulesRegistry = function _getPopupModulesRegistry() {
      const registry = root.popupModulesRegistry;
      return registry && typeof registry === "object" ? registry : null;
    };

    SettingsManager.prototype._normalizeModulePrefs = function _normalizeModulePrefs(rawPrefs, fallback, targetLanguage) {
      const registry = this._getPopupModulesRegistry();
      if (registry && typeof registry.normalizeModulePrefs === "function") {
        return registry.normalizeModulePrefs(rawPrefs, {
          fallback,
          targetLanguage
        });
      }
      const source = rawPrefs && typeof rawPrefs === "object" ? rawPrefs : {};
      const fallbackSource = fallback && typeof fallback === "object" ? fallback : {};
      const sourceById = source.byId && typeof source.byId === "object" ? source.byId : {};
      const fallbackById = fallbackSource.byId && typeof fallbackSource.byId === "object"
        ? fallbackSource.byId
        : {};
      return {
        byId: {
          ...fallbackById,
          ...sourceById
        }
      };
    };

    SettingsManager.prototype.resolveTargetDisplayScriptFromModulePrefs = function resolveTargetDisplayScriptFromModulePrefs(modulePrefs, targetLanguage) {
      const registry = this._getPopupModulesRegistry();
      if (registry && typeof registry.resolveTargetDisplayScript === "function") {
        return registry.resolveTargetDisplayScript(modulePrefs, targetLanguage);
      }
      return this._normalizePrimaryDisplayScript(
        modulePrefs
          && modulePrefs.byId
          && modulePrefs.byId["ja-primary-display-script"]
          && modulePrefs.byId["ja-primary-display-script"].config
          ? modulePrefs.byId["ja-primary-display-script"].config.primary
          : null,
        this.defaults.targetDisplayScript || "kanji"
      );
    };

    SettingsManager.prototype.getProfileModulePrefs = function getProfileModulePrefs(items, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profileEntry = this._getProfileEntry(items, profileId);
      const targetLanguage = this._normalizeLanguageCode(
        opts.targetLanguage,
        this.defaults.targetLanguage || "en"
      );
      const fallbackRoot = this._isObject(this.defaults.popupModulePrefs)
        ? this.defaults.popupModulePrefs
        : { byId: {} };
      const normalized = this._normalizeModulePrefs(
        profileEntry.modulePrefs,
        fallbackRoot,
        targetLanguage
      );
      return {
        profileId,
        targetLanguage,
        ...normalized
      };
    };

    SettingsManager.prototype.publishProfileModulePrefs = async function publishProfileModulePrefs(modulePrefs, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
      );
      const targetLanguage = this._normalizeLanguageCode(
        opts.targetLanguage,
        this.defaults.targetLanguage || "en"
      );
      const normalized = this._normalizeModulePrefs(modulePrefs, null, targetLanguage);
      const targetDisplayScript = this.resolveTargetDisplayScriptFromModulePrefs(
        normalized,
        targetLanguage
      );
      await this.save({
        popupModulePrefs: normalized,
        targetDisplayScript,
        srsSelectedProfileId: profileId,
        srsProfileId: profileId
      });
      return {
        profileId,
        targetLanguage,
        targetDisplayScript,
        ...normalized
      };
    };

    SettingsManager.prototype.updateProfileModulePrefs = async function updateProfileModulePrefs(modulePrefs, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const targetLanguage = this._normalizeLanguageCode(
        opts.targetLanguage,
        this.defaults.targetLanguage || "en"
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const fallback = this.getProfileModulePrefs(items, {
        profileId,
        targetLanguage
      });
      const normalized = this._normalizeModulePrefs(modulePrefs, fallback, targetLanguage);
      const nextProfileEntry = {
        ...profileEntry,
        modulePrefs: normalized
      };
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: nextProfileEntry
      };
      await this.save({
        srsProfiles: nextProfiles
      });
      const published = await this.publishProfileModulePrefs(normalized, {
        profileId,
        targetLanguage
      });
      return {
        profileId,
        targetLanguage,
        ...published
      };
    };
  }

  root.optionsSettingsInstallModulePrefsMethods = installModulePrefsMethods;
})();
