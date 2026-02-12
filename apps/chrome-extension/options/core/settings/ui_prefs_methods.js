(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const FALLBACK_CARD_THEME_LIMITS = Object.freeze({
    hueDeg: Object.freeze({ min: -180, max: 180, defaultValue: 0 }),
    saturationPercent: Object.freeze({ min: 70, max: 140, defaultValue: 100 }),
    brightnessPercent: Object.freeze({ min: 80, max: 125, defaultValue: 100 })
  });

  function resolveCardThemeLimits() {
    const themeRoot = root.profileUiTheme && typeof root.profileUiTheme === "object"
      ? root.profileUiTheme
      : {};
    const configured = themeRoot.CARD_THEME_LIMITS && typeof themeRoot.CARD_THEME_LIMITS === "object"
      ? themeRoot.CARD_THEME_LIMITS
      : {};
    const hueDeg = configured.hueDeg && typeof configured.hueDeg === "object"
      ? configured.hueDeg
      : FALLBACK_CARD_THEME_LIMITS.hueDeg;
    const saturationPercent = configured.saturationPercent && typeof configured.saturationPercent === "object"
      ? configured.saturationPercent
      : FALLBACK_CARD_THEME_LIMITS.saturationPercent;
    const brightnessPercent = configured.brightnessPercent && typeof configured.brightnessPercent === "object"
      ? configured.brightnessPercent
      : FALLBACK_CARD_THEME_LIMITS.brightnessPercent;
    return {
      hueDeg,
      saturationPercent,
      brightnessPercent
    };
  }

  function installUiPrefsMethods(SettingsManager) {
    if (!SettingsManager || !SettingsManager.prototype) {
      return;
    }

    SettingsManager.prototype._normalizeProfileUiPrefs = function _normalizeProfileUiPrefs(rawPrefs, fallback) {
      const cardThemeLimits = resolveCardThemeLimits();
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
      const cardThemeHueDefault = Number.isFinite(Number(this.defaults.profileCardThemeHueDeg))
        ? Number(this.defaults.profileCardThemeHueDeg)
        : cardThemeLimits.hueDeg.defaultValue;
      const cardThemeSaturationDefault = Number.isFinite(Number(this.defaults.profileCardThemeSaturationPercent))
        ? Number(this.defaults.profileCardThemeSaturationPercent)
        : cardThemeLimits.saturationPercent.defaultValue;
      const cardThemeBrightnessDefault = Number.isFinite(Number(this.defaults.profileCardThemeBrightnessPercent))
        ? Number(this.defaults.profileCardThemeBrightnessPercent)
        : cardThemeLimits.brightnessPercent.defaultValue;
      const cardThemeHueDeg = this._normalizeInt(
        raw.cardThemeHueDeg !== undefined ? raw.cardThemeHueDeg : base.cardThemeHueDeg,
        cardThemeHueDefault,
        cardThemeLimits.hueDeg.min,
        cardThemeLimits.hueDeg.max
      );
      const cardThemeSaturationPercent = this._normalizeInt(
        raw.cardThemeSaturationPercent !== undefined
          ? raw.cardThemeSaturationPercent
          : base.cardThemeSaturationPercent,
        cardThemeSaturationDefault,
        cardThemeLimits.saturationPercent.min,
        cardThemeLimits.saturationPercent.max
      );
      const cardThemeBrightnessPercent = this._normalizeInt(
        raw.cardThemeBrightnessPercent !== undefined
          ? raw.cardThemeBrightnessPercent
          : base.cardThemeBrightnessPercent,
        cardThemeBrightnessDefault,
        cardThemeLimits.brightnessPercent.min,
        cardThemeLimits.brightnessPercent.max
      );
      return {
        backgroundEnabled: requestedEnabled && Boolean(backgroundAssetId),
        backgroundAssetId,
        backgroundOpacity,
        backgroundBackdropColor,
        cardThemeHueDeg,
        cardThemeSaturationPercent,
        cardThemeBrightnessPercent
      };
    };

    SettingsManager.prototype.getProfileUiPrefs = function getProfileUiPrefs(items, options) {
      const cardThemeLimits = resolveCardThemeLimits();
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
        cardThemeHueDeg: Number.isFinite(Number(this.defaults.profileCardThemeHueDeg))
          ? Number(this.defaults.profileCardThemeHueDeg)
          : cardThemeLimits.hueDeg.defaultValue,
        cardThemeSaturationPercent: Number.isFinite(Number(this.defaults.profileCardThemeSaturationPercent))
          ? Number(this.defaults.profileCardThemeSaturationPercent)
          : cardThemeLimits.saturationPercent.defaultValue,
        cardThemeBrightnessPercent: Number.isFinite(Number(this.defaults.profileCardThemeBrightnessPercent))
          ? Number(this.defaults.profileCardThemeBrightnessPercent)
          : cardThemeLimits.brightnessPercent.defaultValue
      });
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.publishProfileUiPrefs = async function publishProfileUiPrefs(uiPrefs, options) {
      const cardThemeLimits = resolveCardThemeLimits();
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
      );
      const normalized = this._normalizeProfileUiPrefs(uiPrefs, {
        backgroundEnabled: false,
        backgroundAssetId: "",
        backgroundOpacity: this.defaults.profileBackgroundOpacity || 0.18,
        backgroundBackdropColor: this.defaults.profileBackgroundBackdropColor || "#fbf7f0",
        cardThemeHueDeg: Number.isFinite(Number(this.defaults.profileCardThemeHueDeg))
          ? Number(this.defaults.profileCardThemeHueDeg)
          : cardThemeLimits.hueDeg.defaultValue,
        cardThemeSaturationPercent: Number.isFinite(Number(this.defaults.profileCardThemeSaturationPercent))
          ? Number(this.defaults.profileCardThemeSaturationPercent)
          : cardThemeLimits.saturationPercent.defaultValue,
        cardThemeBrightnessPercent: Number.isFinite(Number(this.defaults.profileCardThemeBrightnessPercent))
          ? Number(this.defaults.profileCardThemeBrightnessPercent)
          : cardThemeLimits.brightnessPercent.defaultValue
      });
      const updates = {
        profileBackgroundEnabled: normalized.backgroundEnabled,
        profileBackgroundAssetId: normalized.backgroundAssetId,
        profileBackgroundOpacity: normalized.backgroundOpacity,
        profileBackgroundBackdropColor: normalized.backgroundBackdropColor,
        profileCardThemeHueDeg: normalized.cardThemeHueDeg,
        profileCardThemeSaturationPercent: normalized.cardThemeSaturationPercent,
        profileCardThemeBrightnessPercent: normalized.cardThemeBrightnessPercent,
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
