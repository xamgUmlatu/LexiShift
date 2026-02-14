(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installBaseMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._isObject = function _isObject(value) {
      return Boolean(value) && typeof value === "object" && !Array.isArray(value);
    };

    SettingsManager.prototype._normalizePairKey = function _normalizePairKey(pairKey) {
      const normalized = String(pairKey || "").trim();
      if (normalized) {
        return normalized;
      }
      return String(this.defaults.srsPair || "en-en");
    };

    SettingsManager.prototype._normalizeLanguageCode = function _normalizeLanguageCode(value, fallback) {
      const normalized = String(value || "").trim();
      if (normalized) {
        return normalized;
      }
      return String(fallback || "").trim() || "en";
    };

    SettingsManager.prototype._normalizePrimaryDisplayScript = function _normalizePrimaryDisplayScript(value, fallback) {
      const allowed = new Set(["kanji", "kana", "romaji"]);
      const candidate = String(value || "").trim().toLowerCase();
      if (allowed.has(candidate)) {
        return candidate;
      }
      const fallbackValue = String(fallback || "").trim().toLowerCase();
      if (allowed.has(fallbackValue)) {
        return fallbackValue;
      }
      return "kanji";
    };

    SettingsManager.prototype.normalizeSrsProfileId = function normalizeSrsProfileId(profileId) {
      const normalized = String(profileId || "").trim();
      return normalized || this.DEFAULT_PROFILE_ID;
    };

    SettingsManager.prototype.getSelectedSrsProfileId = function getSelectedSrsProfileId(items) {
      if (!this._isObject(items)) {
        return this.DEFAULT_PROFILE_ID;
      }
      const configured = items.srsSelectedProfileId !== undefined
        ? items.srsSelectedProfileId
        : items.srsProfileId;
      return this.normalizeSrsProfileId(configured);
    };

    SettingsManager.prototype.updateSelectedSrsProfileId = async function updateSelectedSrsProfileId(profileId) {
      const resolvedProfileId = this.normalizeSrsProfileId(profileId);
      await this.save({
        srsSelectedProfileId: resolvedProfileId,
        // Runtime readers (content script) consume this key directly.
        srsProfileId: resolvedProfileId
      });
      return resolvedProfileId;
    };

    SettingsManager.prototype.getSelectedUiProfileId = function getSelectedUiProfileId(items) {
      if (!this._isObject(items)) {
        return this.DEFAULT_PROFILE_ID;
      }
      const configured = items.optionsSelectedProfileId !== undefined
        ? items.optionsSelectedProfileId
        : this.getSelectedSrsProfileId(items);
      return this.normalizeSrsProfileId(configured);
    };

    SettingsManager.prototype.updateSelectedUiProfileId = async function updateSelectedUiProfileId(profileId) {
      const resolvedProfileId = this.normalizeSrsProfileId(profileId);
      await this.save({
        optionsSelectedProfileId: resolvedProfileId
      });
      return resolvedProfileId;
    };

    SettingsManager.prototype._getProfilesRoot = function _getProfilesRoot(items) {
      return this._isObject(items && items.srsProfiles) ? items.srsProfiles : {};
    };

    SettingsManager.prototype._getProfileEntry = function _getProfileEntry(items, profileId) {
      const profilesRoot = this._getProfilesRoot(items);
      const resolvedProfileId = this.normalizeSrsProfileId(profileId);
      const raw = this._isObject(profilesRoot[resolvedProfileId]) ? profilesRoot[resolvedProfileId] : {};
      return {
        ...raw,
        srsByPair: this._isObject(raw.srsByPair) ? raw.srsByPair : {},
        srsSignalsByPair: this._isObject(raw.srsSignalsByPair) ? raw.srsSignalsByPair : {},
        languagePrefs: this._isObject(raw.languagePrefs) ? raw.languagePrefs : {},
        uiPrefs: this._isObject(raw.uiPrefs) ? raw.uiPrefs : {},
        modulePrefs: this._isObject(raw.modulePrefs) ? raw.modulePrefs : {},
        manualRulesets: this._isObject(raw.manualRulesets) ? raw.manualRulesets : {}
      };
    };

    SettingsManager.prototype._normalizeInt = function _normalizeInt(value, fallback, minimum, maximum = null) {
      const parsed = Number.parseInt(value, 10);
      const base = Number.isFinite(parsed) ? parsed : fallback;
      const lowerBounded = Math.max(minimum, base);
      if (maximum === null || maximum === undefined) {
        return lowerBounded;
      }
      return Math.min(maximum, lowerBounded);
    };

    SettingsManager.prototype._normalizeFloat = function _normalizeFloat(value, fallback, minimum, maximum = null) {
      const parsed = Number.parseFloat(value);
      const base = Number.isFinite(parsed) ? parsed : fallback;
      const lowerBounded = Math.max(minimum, base);
      if (maximum === null || maximum === undefined) {
        return lowerBounded;
      }
      return Math.min(maximum, lowerBounded);
    };

    SettingsManager.prototype._normalizeHexColor = function _normalizeHexColor(value, fallback) {
      const fallbackColor = String(fallback || "#fbf7f0").trim();
      const resolvedFallback = /^#[0-9a-fA-F]{6}$/.test(fallbackColor)
        ? fallbackColor.toLowerCase()
        : "#fbf7f0";
      const candidate = String(value || "").trim();
      if (/^#[0-9a-fA-F]{6}$/.test(candidate)) {
        return candidate.toLowerCase();
      }
      return resolvedFallback;
    };
  }

  root.optionsSettingsInstallBaseMethods = installBaseMethods;
})();
