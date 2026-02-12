(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const themePrefs = root.profileUiThemePrefs && typeof root.profileUiThemePrefs === "object"
    ? root.profileUiThemePrefs
    : {};
  const resolveCardThemeDefaults = typeof themePrefs.resolveCardThemeDefaults === "function"
    ? themePrefs.resolveCardThemeDefaults
    : () => ({
        hueDeg: 0,
        saturationPercent: 100,
        brightnessPercent: 100,
        transparencyPercent: 100
      });
  const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
    ? themePrefs.normalizeCardThemePrefs
    : () => ({
        cardThemeHueDeg: 0,
        cardThemeSaturationPercent: 100,
        cardThemeBrightnessPercent: 100,
        cardThemeTransparencyPercent: 100
      });

  function resolveDefaultThemePrefsFromSettings(settingsDefaults) {
    const defaults = settingsDefaults && typeof settingsDefaults === "object"
      ? settingsDefaults
      : {};
    const resolved = resolveCardThemeDefaults({
      defaults: {
        cardThemeHueDeg: defaults.profileCardThemeHueDeg,
        cardThemeSaturationPercent: defaults.profileCardThemeSaturationPercent,
        cardThemeBrightnessPercent: defaults.profileCardThemeBrightnessPercent,
        cardThemeTransparencyPercent: defaults.profileCardThemeTransparencyPercent
      }
    });
    return {
      cardThemeHueDeg: resolved.hueDeg,
      cardThemeSaturationPercent: resolved.saturationPercent,
      cardThemeBrightnessPercent: resolved.brightnessPercent,
      cardThemeTransparencyPercent: resolved.transparencyPercent
    };
  }

  function installUiPrefsMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._normalizeProfileUiPrefs = function _normalizeProfileUiPrefs(rawPrefs, fallback) {
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
      const backgroundPositionX = this._normalizeFloat(
        raw.backgroundPositionX !== undefined ? raw.backgroundPositionX : base.backgroundPositionX,
        this.defaults.profileBackgroundPositionX || 50,
        0,
        100
      );
      const backgroundPositionY = this._normalizeFloat(
        raw.backgroundPositionY !== undefined ? raw.backgroundPositionY : base.backgroundPositionY,
        this.defaults.profileBackgroundPositionY || 50,
        0,
        100
      );
      const themeDefaults = resolveDefaultThemePrefsFromSettings(this.defaults);
      const normalizedCardTheme = normalizeCardThemePrefs(raw, {
        fallback: base,
        defaults: themeDefaults
      });
      return {
        backgroundEnabled: requestedEnabled && Boolean(backgroundAssetId),
        backgroundAssetId,
        backgroundOpacity,
        backgroundBackdropColor,
        backgroundPositionX,
        backgroundPositionY,
        cardThemeHueDeg: normalizedCardTheme.cardThemeHueDeg,
        cardThemeSaturationPercent: normalizedCardTheme.cardThemeSaturationPercent,
        cardThemeBrightnessPercent: normalizedCardTheme.cardThemeBrightnessPercent,
        cardThemeTransparencyPercent: normalizedCardTheme.cardThemeTransparencyPercent
      };
    };

    SettingsManager.prototype.getProfileUiPrefs = function getProfileUiPrefs(items, options) {
      const themeDefaults = resolveDefaultThemePrefsFromSettings(this.defaults);
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedUiProfileId(items)
      );
      const profileEntry = this._getProfileEntry(items, profileId);
      const normalized = this._normalizeProfileUiPrefs(profileEntry.uiPrefs, {
        backgroundEnabled: false,
        backgroundAssetId: "",
        backgroundOpacity: this.defaults.profileBackgroundOpacity || 0.18,
        backgroundBackdropColor: this.defaults.profileBackgroundBackdropColor || "#fbf7f0",
        backgroundPositionX: this.defaults.profileBackgroundPositionX || 50,
        backgroundPositionY: this.defaults.profileBackgroundPositionY || 50,
        cardThemeHueDeg: themeDefaults.cardThemeHueDeg,
        cardThemeSaturationPercent: themeDefaults.cardThemeSaturationPercent,
        cardThemeBrightnessPercent: themeDefaults.cardThemeBrightnessPercent,
        cardThemeTransparencyPercent: themeDefaults.cardThemeTransparencyPercent
      });
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.publishProfileUiPrefs = async function publishProfileUiPrefs(uiPrefs, options) {
      const themeDefaults = resolveDefaultThemePrefsFromSettings(this.defaults);
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
      );
      const normalized = this._normalizeProfileUiPrefs(uiPrefs, {
        backgroundEnabled: false,
        backgroundAssetId: "",
        backgroundOpacity: this.defaults.profileBackgroundOpacity || 0.18,
        backgroundBackdropColor: this.defaults.profileBackgroundBackdropColor || "#fbf7f0",
        backgroundPositionX: this.defaults.profileBackgroundPositionX || 50,
        backgroundPositionY: this.defaults.profileBackgroundPositionY || 50,
        cardThemeHueDeg: themeDefaults.cardThemeHueDeg,
        cardThemeSaturationPercent: themeDefaults.cardThemeSaturationPercent,
        cardThemeBrightnessPercent: themeDefaults.cardThemeBrightnessPercent,
        cardThemeTransparencyPercent: themeDefaults.cardThemeTransparencyPercent
      });
      const updates = {
        profileBackgroundEnabled: normalized.backgroundEnabled,
        profileBackgroundAssetId: normalized.backgroundAssetId,
        profileBackgroundOpacity: normalized.backgroundOpacity,
        profileBackgroundBackdropColor: normalized.backgroundBackdropColor,
        profileBackgroundPositionX: normalized.backgroundPositionX,
        profileBackgroundPositionY: normalized.backgroundPositionY,
        profileCardThemeHueDeg: normalized.cardThemeHueDeg,
        profileCardThemeSaturationPercent: normalized.cardThemeSaturationPercent,
        profileCardThemeBrightnessPercent: normalized.cardThemeBrightnessPercent,
        profileCardThemeTransparencyPercent: normalized.cardThemeTransparencyPercent,
        optionsSelectedProfileId: profileId
      };
      await this.save(updates);
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.updateProfileUiPrefs = async function updateProfileUiPrefs(uiPrefs, options) {
      const items = await this.load();
      const opts = options && typeof options === "object" ? options : {};
      const publishRuntime = opts.publishRuntime !== false;
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedUiProfileId(items)
      );
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const fallback = this.getProfileUiPrefs(items, { profileId });
      const normalized = this._normalizeProfileUiPrefs(uiPrefs, fallback);
      const nextProfileEntry = {
        ...profileEntry,
        uiPrefs: normalized
      };
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: nextProfileEntry
      };
      await this.save({
        srsProfiles: nextProfiles,
        optionsSelectedProfileId: profileId
      });
      if (publishRuntime) {
        await this.publishProfileUiPrefs(normalized, { profileId });
      }
      return {
        profileId,
        ...normalized,
        publishedRuntime: publishRuntime
      };
    };
  }

  root.optionsSettingsInstallUiPrefsMethods = installUiPrefsMethods;
})();
