(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createActions(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const maxUploadBytes = Number.isFinite(Number(opts.maxUploadBytes))
      ? Math.max(1, Number(opts.maxUploadBytes))
      : (8 * 1024 * 1024);
    const profileBgBackdropColorInput = opts.profileBgBackdropColorInput || null;
    const profileBgOpacityInput = opts.profileBgOpacityInput || null;
    const profileBgFileInput = opts.profileBgFileInput || null;
    const profileBgRemoveButton = opts.profileBgRemoveButton || null;
    const profileMediaStore = opts.profileMediaStore && typeof opts.profileMediaStore === "object"
      ? opts.profileMediaStore
      : null;
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const setProfileBgStatus = typeof opts.setProfileBgStatus === "function"
      ? opts.setProfileBgStatus
      : (() => {});
    const setProfileBgStatusLocalized = typeof opts.setProfileBgStatusLocalized === "function"
      ? opts.setProfileBgStatusLocalized
      : (key, substitutions, fallback) => {
          setProfileBgStatus(translate(key, substitutions, fallback || ""));
        };
    const updateProfileBgOpacityLabel = typeof opts.updateProfileBgOpacityLabel === "function"
      ? opts.updateProfileBgOpacityLabel
      : (() => {});
    const clampProfileBackgroundOpacity = typeof opts.clampProfileBackgroundOpacity === "function"
      ? opts.clampProfileBackgroundOpacity
      : (value) => Number(value);
    const normalizeProfileBackgroundBackdropColor = typeof opts.normalizeProfileBackgroundBackdropColor === "function"
      ? opts.normalizeProfileBackgroundBackdropColor
      : (value) => String(value || "").trim();
    const formatBytes = typeof opts.formatBytes === "function"
      ? opts.formatBytes
      : (bytes) => `${bytes || 0} B`;
    const previewManager = opts.previewManager && typeof opts.previewManager === "object"
      ? opts.previewManager
      : {
          clearPreview: () => {},
          setPreviewFromBlob: () => {}
        };
    const loadActiveProfileUiPrefs = typeof opts.loadActiveProfileUiPrefs === "function"
      ? opts.loadActiveProfileUiPrefs
      : (() => Promise.resolve({
          profileId: "default",
          uiPrefs: {}
        }));
    const saveProfileUiPrefsForCurrentProfile = typeof opts.saveProfileUiPrefsForCurrentProfile === "function"
      ? opts.saveProfileUiPrefsForCurrentProfile
      : ((nextPrefs) => Promise.resolve(nextPrefs && typeof nextPrefs === "object" ? { ...nextPrefs } : {}));
    const publishProfileUiPrefsForCurrentProfile = typeof opts.publishProfileUiPrefsForCurrentProfile === "function"
      ? opts.publishProfileUiPrefsForCurrentProfile
      : (() => Promise.resolve());
    const applyOptionsPageBackgroundFromPrefs = typeof opts.applyOptionsPageBackgroundFromPrefs === "function"
      ? opts.applyOptionsPageBackgroundFromPrefs
      : (() => Promise.resolve());
    const resolveBackgroundPositionFromSource = typeof opts.resolveBackgroundPositionFromSource === "function"
      ? opts.resolveBackgroundPositionFromSource
      : (sourcePrefs) => {
          const source = sourcePrefs && typeof sourcePrefs === "object" ? sourcePrefs : {};
          const fallbackX = Number.isFinite(Number(source.backgroundPositionX))
            ? Number(source.backgroundPositionX)
            : 50;
          const fallbackY = Number.isFinite(Number(source.backgroundPositionY))
            ? Number(source.backgroundPositionY)
            : 50;
          return {
            x: Math.min(100, Math.max(0, fallbackX)),
            y: Math.min(100, Math.max(0, fallbackY))
          };
        };
    async function onOpacityChange() {
      if (!profileBgOpacityInput) {
        return;
      }
      const percent = Number.parseFloat(profileBgOpacityInput.value);
      updateProfileBgOpacityLabel(percent);
      const state = await loadActiveProfileUiPrefs();
      const currentPrefs = state.uiPrefs && typeof state.uiPrefs === "object" ? state.uiPrefs : {};
      const nextPrefs = {
        ...currentPrefs,
        backgroundOpacity: clampProfileBackgroundOpacity(percent / 100)
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      setStatus("Background opacity saved.", colors.SUCCESS);
    }

    async function onBackdropColorChange() {
      if (!profileBgBackdropColorInput) {
        return;
      }
      const color = normalizeProfileBackgroundBackdropColor(profileBgBackdropColorInput.value);
      profileBgBackdropColorInput.value = color;
      const state = await loadActiveProfileUiPrefs();
      const currentPrefs = state.uiPrefs && typeof state.uiPrefs === "object" ? state.uiPrefs : {};
      const nextPrefs = {
        ...currentPrefs,
        backgroundBackdropColor: color
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      setStatus("Backdrop color saved.", colors.SUCCESS);
    }

    function onOpacityInput() {
      if (!profileBgOpacityInput) {
        return;
      }
      updateProfileBgOpacityLabel(profileBgOpacityInput.value);
    }

    async function onFileChange() {
      if (!profileBgFileInput) {
        return;
      }
      const file = profileBgFileInput.files && profileBgFileInput.files[0];
      if (!file) {
        return;
      }
      if (!String(file.type || "").startsWith("image/")) {
        setProfileBgStatus("Only image files are supported.");
        setStatus("Only image files are supported.", colors.ERROR);
        profileBgFileInput.value = "";
        return;
      }
      if (Number(file.size || 0) > maxUploadBytes) {
        const message = `Image too large. Maximum is ${formatBytes(maxUploadBytes)}.`;
        setProfileBgStatus(message);
        setStatus(message, colors.ERROR);
        profileBgFileInput.value = "";
        return;
      }
      if (!profileMediaStore || typeof profileMediaStore.upsertProfileBackground !== "function") {
        const message = "Profile media store is unavailable.";
        setProfileBgStatus(message);
        setStatus(message, colors.ERROR);
        profileBgFileInput.value = "";
        return;
      }

      profileBgFileInput.disabled = true;
      setProfileBgStatus(`Saving: ${file.type || "image/*"}, ${formatBytes(file.size || 0)}.`);
      setStatus("Saving options page background image.", colors.DEFAULT);
      try {
        const state = await loadActiveProfileUiPrefs();
        const currentPrefs = state.uiPrefs && typeof state.uiPrefs === "object" ? state.uiPrefs : {};
        const previewPosition = resolveBackgroundPositionFromSource(currentPrefs);
        const meta = await profileMediaStore.upsertProfileBackground(
          state.profileId,
          file,
          {
            previousAssetId: currentPrefs.backgroundAssetId,
            mimeType: file.type || "application/octet-stream"
          }
        );
        const finalPrefs = {
          ...currentPrefs,
          backgroundAssetId: meta.asset_id,
          backgroundEnabled: true,
          backgroundOpacity: profileBgOpacityInput
            ? clampProfileBackgroundOpacity(Number(profileBgOpacityInput.value || 18) / 100)
            : (currentPrefs.backgroundOpacity || 0.18),
          backgroundBackdropColor: profileBgBackdropColorInput
            ? normalizeProfileBackgroundBackdropColor(profileBgBackdropColorInput.value)
            : normalizeProfileBackgroundBackdropColor(currentPrefs.backgroundBackdropColor),
          backgroundPositionX: previewPosition.x,
          backgroundPositionY: previewPosition.y
        };
        await saveProfileUiPrefsForCurrentProfile(finalPrefs, {
          profileId: state.profileId,
          publishRuntime: false
        });
        await publishProfileUiPrefsForCurrentProfile(finalPrefs, {
          profileId: state.profileId
        });
        previewManager.setPreviewFromBlob(file);
        if (typeof previewManager.setPreviewPosition === "function") {
          previewManager.setPreviewPosition(previewPosition.x, previewPosition.y);
        }
        await applyOptionsPageBackgroundFromPrefs(finalPrefs, {
          preferredBlob: file
        });
        setProfileBgStatus(
          `Asset: ${meta.mime_type || file.type || "image/*"}, ${formatBytes(meta.byte_size || file.size || 0)}.`
        );
        setStatus("Options page background image saved.", colors.SUCCESS);
      } catch (err) {
        const msg = err && err.message ? err.message : "Failed to save profile background image.";
        setProfileBgStatus(msg);
        setStatus(msg, colors.ERROR);
      } finally {
        profileBgFileInput.disabled = false;
        profileBgFileInput.value = "";
      }
    }

    async function onRemove() {
      if (!profileBgRemoveButton) {
        return;
      }
      if (profileBgFileInput) {
        profileBgFileInput.value = "";
      }
      if (!profileMediaStore || typeof profileMediaStore.deleteAsset !== "function") {
        setStatus("Profile media store is unavailable.", colors.ERROR);
        return;
      }
      profileBgRemoveButton.disabled = true;
      let removed = false;
      try {
        const state = await loadActiveProfileUiPrefs();
        const currentPrefs = state.uiPrefs && typeof state.uiPrefs === "object" ? state.uiPrefs : {};
        const existingAssetId = String(currentPrefs.backgroundAssetId || "").trim();
        if (existingAssetId) {
          await profileMediaStore.deleteAsset(existingAssetId);
        }
        const nextPrefs = {
          ...currentPrefs,
          backgroundEnabled: false,
          backgroundAssetId: ""
        };
        await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
          profileId: state.profileId,
          publishRuntime: false
        });
        previewManager.clearPreview();
        await applyOptionsPageBackgroundFromPrefs(nextPrefs);
        setProfileBgStatusLocalized(
          "hint_profile_bg_status_empty",
          null,
          "No options page background image configured for this profile."
        );
        setStatus("Options page background image removed.", colors.SUCCESS);
        removed = true;
      } catch (err) {
        const msg = err && err.message ? err.message : "Failed to remove profile background image.";
        setStatus(msg, colors.ERROR);
      } finally {
        profileBgRemoveButton.disabled = removed;
      }
    }

    return {
      onOpacityInput,
      onOpacityChange,
      onBackdropColorChange,
      onFileChange,
      onRemove
    };
  }

  root.optionsProfileBackgroundActions = {
    createActions
  };
})();
