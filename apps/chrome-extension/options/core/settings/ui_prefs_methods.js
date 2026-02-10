(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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
      return {
        backgroundEnabled: requestedEnabled && Boolean(backgroundAssetId),
        backgroundAssetId,
        backgroundOpacity,
        backgroundBackdropColor
      };
    };

    SettingsManager.prototype.getProfileUiPrefs = function getProfileUiPrefs(items, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.getSelectedUiProfileId(items)
      );
      const profileEntry = this._getProfileEntry(items, profileId);
      const hasStoredUiPrefs = this._isObject(profileEntry.uiPrefs)
        && Object.keys(profileEntry.uiPrefs).length > 0;
      // Compatibility bridge for older installs that only persisted runtime root keys.
      const useLegacyRuntimeFallback = !hasStoredUiPrefs
        && items
        && items.optionsSelectedProfileId === undefined;
      const fallback = {
        backgroundEnabled: useLegacyRuntimeFallback && items.profileBackgroundEnabled === true,
        backgroundAssetId: useLegacyRuntimeFallback
          ? String(items.profileBackgroundAssetId || "").trim()
          : "",
        backgroundOpacity: this._normalizeFloat(
          useLegacyRuntimeFallback ? items.profileBackgroundOpacity : null,
          this.defaults.profileBackgroundOpacity || 0.18,
          0,
          1
        ),
        backgroundBackdropColor: this._normalizeHexColor(
          useLegacyRuntimeFallback ? items.profileBackgroundBackdropColor : null,
          this.defaults.profileBackgroundBackdropColor || "#fbf7f0"
        )
      };
      const normalized = this._normalizeProfileUiPrefs(profileEntry.uiPrefs, fallback);
      return {
        profileId,
        ...normalized
      };
    };

    SettingsManager.prototype.publishProfileUiPrefs = async function publishProfileUiPrefs(uiPrefs, options) {
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeSrsProfileId(
        opts.profileId !== undefined ? opts.profileId : this.DEFAULT_PROFILE_ID
      );
      const normalized = this._normalizeProfileUiPrefs(uiPrefs, {
        backgroundEnabled: false,
        backgroundAssetId: "",
        backgroundOpacity: this.defaults.profileBackgroundOpacity || 0.18,
        backgroundBackdropColor: this.defaults.profileBackgroundBackdropColor || "#fbf7f0"
      });
      const updates = {
        profileBackgroundEnabled: normalized.backgroundEnabled,
        profileBackgroundAssetId: normalized.backgroundAssetId,
        profileBackgroundOpacity: normalized.backgroundOpacity,
        profileBackgroundBackdropColor: normalized.backgroundBackdropColor,
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
