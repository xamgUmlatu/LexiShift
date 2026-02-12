(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createBridge(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;
    const profileMediaStore = opts.profileMediaStore && typeof opts.profileMediaStore === "object"
      ? opts.profileMediaStore
      : null;
    const previewManager = opts.previewManager && typeof opts.previewManager === "object"
      ? opts.previewManager
      : {
          clearPreview: () => {},
          setPreviewFromBlob: () => {}
        };
    const pageBackgroundManager = opts.pageBackgroundManager && typeof opts.pageBackgroundManager === "object"
      ? opts.pageBackgroundManager
      : {
          applyBackdropOnly: () => {},
          applyBackgroundFromBlob: () => {}
        };
    const cardThemeManager = opts.cardThemeManager && typeof opts.cardThemeManager === "object"
      ? opts.cardThemeManager
      : {
          applyCardThemeFromPrefs: () => ({
            hueDeg: 0,
            saturationPercent: 100,
            brightnessPercent: 100
          })
        };
    const prefsService = opts.prefsService && typeof opts.prefsService === "object" ? opts.prefsService : null;
    const formatBytes = typeof opts.formatBytes === "function"
      ? opts.formatBytes
      : (bytes) => `${bytes || 0} B`;
    const normalizeProfileBackgroundBackdropColor = typeof opts.normalizeProfileBackgroundBackdropColor === "function"
      ? opts.normalizeProfileBackgroundBackdropColor
      : (value) => String(value || "").trim();
    const updateProfileBgOpacityLabel = typeof opts.updateProfileBgOpacityLabel === "function"
      ? opts.updateProfileBgOpacityLabel
      : (() => {});
    const setProfileBgStatus = typeof opts.setProfileBgStatus === "function"
      ? opts.setProfileBgStatus
      : (() => {});
    const setProfileBgStatusLocalized = typeof opts.setProfileBgStatusLocalized === "function"
      ? opts.setProfileBgStatusLocalized
      : (key, substitutions, fallback) => {
          setProfileBgStatus(translate(key, substitutions, fallback || ""));
        };
    const setProfileBgApplyState = typeof opts.setProfileBgApplyState === "function"
      ? opts.setProfileBgApplyState
      : (() => {});
    const updateProfileCardThemeLabels = typeof opts.updateProfileCardThemeLabels === "function"
      ? opts.updateProfileCardThemeLabels
      : (() => {});
    const getPendingFile = typeof opts.getPendingFile === "function" ? opts.getPendingFile : (() => null);
    const setPendingFile = typeof opts.setPendingFile === "function" ? opts.setPendingFile : (() => {});
    const clearFileInput = typeof opts.clearFileInput === "function" ? opts.clearFileInput : (() => {});
    const defaultOpacity = Number.isFinite(Number(opts.defaultOpacity))
      ? Number(opts.defaultOpacity)
      : 0.18;

    async function refreshProfileBackgroundPreview(uiPrefs) {
      const prefs = uiPrefs && typeof uiPrefs === "object" ? uiPrefs : {};
      const assetId = String(prefs.backgroundAssetId || "").trim();
      if (!assetId) {
        previewManager.clearPreview();
        setProfileBgStatusLocalized(
          "hint_profile_bg_status_empty",
          null,
          "No background image configured for this profile."
        );
        return;
      }
      if (!profileMediaStore || typeof profileMediaStore.getAsset !== "function") {
        previewManager.clearPreview();
        setProfileBgStatus("Background preview unavailable: media store missing.");
        return;
      }
      try {
        const record = await profileMediaStore.getAsset(assetId);
        if (!record || !(record.blob instanceof Blob)) {
          previewManager.clearPreview();
          setProfileBgStatus("Background asset not found. Upload again for this profile.");
          return;
        }
        previewManager.setPreviewFromBlob(record.blob);
        const type = String(record.mime_type || record.blob.type || "image/*");
        const size = Number(record.byte_size || record.blob.size || 0);
        setProfileBgStatus(`Asset: ${type}, ${formatBytes(size)}.`);
      } catch (err) {
        previewManager.clearPreview();
        const msg = err && err.message ? err.message : "Failed to load background preview.";
        setProfileBgStatus(msg);
      }
    }

    async function applyOptionsPageBackgroundFromPrefs(uiPrefs, options) {
      const prefs = uiPrefs && typeof uiPrefs === "object" ? uiPrefs : {};
      cardThemeManager.applyCardThemeFromPrefs(prefs);
      const localOptions = options && typeof options === "object" ? options : {};
      const enabled = prefs.backgroundEnabled === true;
      const assetId = String(prefs.backgroundAssetId || "").trim();
      const backdropColor = normalizeProfileBackgroundBackdropColor(prefs.backgroundBackdropColor);
      const preferredBlob = localOptions.preferredBlob instanceof Blob ? localOptions.preferredBlob : null;
      if (!enabled || !assetId) {
        pageBackgroundManager.applyBackdropOnly(backdropColor);
        return;
      }
      if (preferredBlob) {
        pageBackgroundManager.applyBackgroundFromBlob(preferredBlob, prefs.backgroundOpacity, backdropColor);
        return;
      }
      if (!profileMediaStore || typeof profileMediaStore.getAsset !== "function") {
        pageBackgroundManager.applyBackdropOnly(backdropColor);
        return;
      }
      try {
        const record = await profileMediaStore.getAsset(assetId);
        if (!record || !(record.blob instanceof Blob)) {
          pageBackgroundManager.applyBackdropOnly(backdropColor);
          return;
        }
        pageBackgroundManager.applyBackgroundFromBlob(record.blob, prefs.backgroundOpacity, backdropColor);
      } catch (_err) {
        pageBackgroundManager.applyBackdropOnly(backdropColor);
      }
    }

    async function loadActiveProfileUiPrefs() {
      if (prefsService && typeof prefsService.loadActiveProfileUiPrefs === "function") {
        return prefsService.loadActiveProfileUiPrefs();
      }
      if (!settingsManager || typeof settingsManager.load !== "function") {
        return {
          profileId: "default",
          uiPrefs: {},
          items: {}
        };
      }
      const items = await settingsManager.load();
      const profileId = settingsManager.getSelectedSrsProfileId(items);
      const uiPrefs = settingsManager.getProfileUiPrefs(items, { profileId });
      return { profileId, uiPrefs, items };
    }

    async function saveProfileUiPrefsForCurrentProfile(nextPrefs, options) {
      if (prefsService && typeof prefsService.saveProfileUiPrefsForCurrentProfile === "function") {
        return prefsService.saveProfileUiPrefsForCurrentProfile(nextPrefs, options);
      }
      if (!settingsManager || typeof settingsManager.updateProfileUiPrefs !== "function") {
        return nextPrefs && typeof nextPrefs === "object" ? { ...nextPrefs } : {};
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const profileId = String(localOptions.profileId || "").trim()
        || settingsManager.DEFAULT_PROFILE_ID
        || "default";
      const publishRuntime = localOptions.publishRuntime === true;
      const normalized = await settingsManager.updateProfileUiPrefs(nextPrefs, {
        profileId,
        publishRuntime
      });
      if (ui && typeof ui.updateProfileBackgroundInputs === "function") {
        ui.updateProfileBackgroundInputs(normalized);
      }
      updateProfileBgOpacityLabel((normalized.backgroundOpacity || defaultOpacity) * 100);
      updateProfileCardThemeLabels({
        hueDeg: normalized.cardThemeHueDeg,
        saturationPercent: normalized.cardThemeSaturationPercent,
        brightnessPercent: normalized.cardThemeBrightnessPercent
      });
      // Apply button is only for committing pending file uploads.
      setProfileBgApplyState(Boolean(getPendingFile()), false);
      return normalized;
    }

    async function publishProfileUiPrefsForCurrentProfile(uiPrefs, options) {
      if (prefsService && typeof prefsService.publishProfileUiPrefs === "function") {
        await prefsService.publishProfileUiPrefs(uiPrefs, options);
        return;
      }
      if (!settingsManager || typeof settingsManager.publishProfileUiPrefs !== "function") {
        return;
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const profileId = String(localOptions.profileId || "").trim()
        || settingsManager.DEFAULT_PROFILE_ID
        || "default";
      await settingsManager.publishProfileUiPrefs(uiPrefs, { profileId });
    }

    async function syncForLoadedPrefs(uiPrefs) {
      setPendingFile(null);
      clearFileInput();
      const prefs = uiPrefs && typeof uiPrefs === "object" ? uiPrefs : {};
      updateProfileBgOpacityLabel((prefs.backgroundOpacity || defaultOpacity) * 100);
      updateProfileCardThemeLabels({
        hueDeg: prefs.cardThemeHueDeg,
        saturationPercent: prefs.cardThemeSaturationPercent,
        brightnessPercent: prefs.cardThemeBrightnessPercent
      });
      await refreshProfileBackgroundPreview(prefs);
      // Always render the selected profile's saved UI prefs on options page load/switch.
      setProfileBgApplyState(Boolean(getPendingFile()), false);
      await applyOptionsPageBackgroundFromPrefs(prefs);
    }

    return {
      loadActiveProfileUiPrefs,
      saveProfileUiPrefsForCurrentProfile,
      publishProfileUiPrefsForCurrentProfile,
      refreshProfileBackgroundPreview,
      applyOptionsPageBackgroundFromPrefs,
      syncForLoadedPrefs
    };
  }

  root.optionsProfileBackgroundRuntimeBridge = {
    createBridge
  };
})();
