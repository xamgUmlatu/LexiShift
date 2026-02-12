(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installLanguageMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._normalizeTargetScriptPrefs = function _normalizeTargetScriptPrefs(rawPrefs, fallback) {
      const raw = this._isObject(rawPrefs) ? rawPrefs : {};
      const base = this._isObject(fallback) ? fallback : {};
      const rawJa = this._isObject(raw.ja) ? raw.ja : {};
      const baseJa = this._isObject(base.ja) ? base.ja : {};
      return {
        ja: {
          primaryDisplayScript: this._normalizePrimaryDisplayScript(
            rawJa.primaryDisplayScript,
            baseJa.primaryDisplayScript || this.defaults.targetDisplayScript || "kanji"
          )
        }
      };
    };

    SettingsManager.prototype._resolveTargetDisplayScript = function _resolveTargetDisplayScript(languagePrefs, modulePrefs) {
      const prefs = this._isObject(languagePrefs) ? languagePrefs : {};
      const targetLanguage = this._normalizeLanguageCode(
        prefs.targetLanguage,
        this.defaults.targetLanguage || "en"
      );
      const targetScriptPrefs = this._normalizeTargetScriptPrefs(
        prefs.targetScriptPrefs,
        null
      );
      if (targetLanguage === "ja") {
        if (typeof this.resolveTargetDisplayScriptFromModulePrefs === "function"
          && this._isObject(modulePrefs)) {
          return this.resolveTargetDisplayScriptFromModulePrefs(modulePrefs, targetLanguage);
        }
        return targetScriptPrefs.ja.primaryDisplayScript;
      }
      return "kanji";
    };

    SettingsManager.prototype._resolvePairFromLanguages = function _resolvePairFromLanguages(sourceLanguage, targetLanguage) {
      const source = this._normalizeLanguageCode(sourceLanguage, this.defaults.sourceLanguage || "en");
      const target = this._normalizeLanguageCode(targetLanguage, this.defaults.targetLanguage || "en");
      return `${source}-${target}`;
    };

    SettingsManager.prototype._normalizeProfileLanguagePrefs = function _normalizeProfileLanguagePrefs(rawPrefs, fallback) {
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
      const targetScriptPrefs = this._normalizeTargetScriptPrefs(
        raw.targetScriptPrefs,
        base.targetScriptPrefs
      );
      return {
        sourceLanguage,
        targetLanguage,
        srsPairAuto,
        srsPair,
        targetScriptPrefs
      };
    };

    SettingsManager.prototype.getProfileLanguagePrefs = function getProfileLanguagePrefs(items, options) {
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
        ),
        targetScriptPrefs: {
          ja: {
            primaryDisplayScript: this._normalizePrimaryDisplayScript(
              items && items.targetDisplayScript,
              this.defaults.targetDisplayScript || "kanji"
            )
          }
        }
      };
      const normalized = this._normalizeProfileLanguagePrefs(profileEntry.languagePrefs, fallback);
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.publishProfileLanguagePrefs = async function publishProfileLanguagePrefs(languagePrefs, options) {
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
      let modulePrefs = this._isObject(opts.modulePrefs) ? opts.modulePrefs : null;
      if (!modulePrefs && typeof this.getProfileModulePrefs === "function") {
        const items = await this.load();
        modulePrefs = this.getProfileModulePrefs(items, {
          profileId,
          targetLanguage: normalized.targetLanguage
        });
      }
      const normalizedModulePrefs = typeof this._normalizeModulePrefs === "function"
        ? this._normalizeModulePrefs(modulePrefs, null, normalized.targetLanguage)
        : null;
      const updates = {
        sourceLanguage: normalized.sourceLanguage,
        targetLanguage: normalized.targetLanguage,
        targetDisplayScript: this._resolveTargetDisplayScript(normalized, normalizedModulePrefs),
        srsPairAuto: normalized.srsPairAuto,
        srsPair: normalized.srsPair,
        srsSelectedProfileId: profileId,
        srsProfileId: profileId
      };
      if (normalizedModulePrefs) {
        updates.popupModulePrefs = normalizedModulePrefs;
      }
      await this.save(updates);
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.updateProfileLanguagePrefs = async function updateProfileLanguagePrefs(languagePrefs, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedSrsProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const fallback = this.getProfileLanguagePrefs(items, { profileId });
      const normalized = this._normalizeProfileLanguagePrefs(languagePrefs, fallback);

      const nextProfileEntry = {
        ...profileEntry,
        languagePrefs: normalized
      };
      const nextProfiles = {
        ...profilesRoot,
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
    };
  }

  root.optionsSettingsInstallLanguageMethods = installLanguageMethods;
})();
