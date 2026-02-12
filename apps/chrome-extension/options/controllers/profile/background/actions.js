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
    const profileBgEnabledInput = opts.profileBgEnabledInput || null;
    const profileBgBackdropColorInput = opts.profileBgBackdropColorInput || null;
    const profileBgOpacityInput = opts.profileBgOpacityInput || null;
    const profileBgFileInput = opts.profileBgFileInput || null;
    const profileBgRemoveButton = opts.profileBgRemoveButton || null;
    const profileBgApplyButton = opts.profileBgApplyButton || null;
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
    const setProfileBgApplyState = typeof opts.setProfileBgApplyState === "function"
      ? opts.setProfileBgApplyState
      : (() => {});
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
    const getPendingFile = typeof opts.getPendingFile === "function" ? opts.getPendingFile : (() => null);
    const setPendingFile = typeof opts.setPendingFile === "function" ? opts.setPendingFile : (() => {});
    const hasPendingApply = typeof opts.hasPendingApply === "function" ? opts.hasPendingApply : (() => false);

    async function onEnabledChange() {
      if (!profileBgEnabledInput) {
        return;
      }
      if (getPendingFile()) {
        setProfileBgApplyState(true, false);
        setStatus("Background toggle staged. Click Apply to commit.", colors.SUCCESS);
        return;
      }
      const state = await loadActiveProfileUiPrefs();
      if (!state.uiPrefs.backgroundAssetId) {
        setProfileBgApplyState(Boolean(getPendingFile()), false);
        setStatus("Choose an image file, then click Apply.", colors.DEFAULT);
        return;
      }
      const nextPrefs = {
        ...state.uiPrefs,
        backgroundEnabled: profileBgEnabledInput.checked === true
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      setStatus("Background toggle saved.", colors.SUCCESS);
    }

    async function onOpacityChange() {
      if (!profileBgOpacityInput) {
        return;
      }
      const percent = Number.parseFloat(profileBgOpacityInput.value);
      updateProfileBgOpacityLabel(percent);
      if (getPendingFile()) {
        setProfileBgApplyState(true, false);
        setStatus("Background opacity staged. Click Apply to commit.", colors.SUCCESS);
        return;
      }
      const state = await loadActiveProfileUiPrefs();
      const nextPrefs = {
        ...state.uiPrefs,
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
      const nextPrefs = {
        ...state.uiPrefs,
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

    function onFileChange() {
      if (!profileBgFileInput) {
        return;
      }
      const file = profileBgFileInput.files && profileBgFileInput.files[0];
      if (!file) {
        setPendingFile(null);
        return;
      }
      if (!String(file.type || "").startsWith("image/")) {
        setPendingFile(null);
        setStatus("Only image files are supported.", colors.ERROR);
        profileBgFileInput.value = "";
        return;
      }
      if (Number(file.size || 0) > maxUploadBytes) {
        setPendingFile(null);
        setStatus(`Image too large. Maximum is ${formatBytes(maxUploadBytes)}.`, colors.ERROR);
        profileBgFileInput.value = "";
        return;
      }
      setPendingFile(file);
      previewManager.setPreviewFromBlob(file);
      if (profileBgEnabledInput) {
        profileBgEnabledInput.checked = true;
      }
      setProfileBgStatus(`Preview ready: ${file.type || "image/*"}, ${formatBytes(file.size || 0)}.`);
      setProfileBgApplyState(true, false);
      setStatus("File selected. Click Apply options page background.", colors.SUCCESS);
    }

    async function onRemove() {
      if (!profileBgRemoveButton) {
        return;
      }
      setPendingFile(null);
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
        const existingAssetId = String(state.uiPrefs.backgroundAssetId || "").trim();
        if (existingAssetId) {
          await profileMediaStore.deleteAsset(existingAssetId);
        }
        const nextPrefs = {
          ...state.uiPrefs,
          backgroundEnabled: false,
          backgroundAssetId: ""
        };
        await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
          profileId: state.profileId,
          publishRuntime: false
        });
        previewManager.clearPreview();
        await applyOptionsPageBackgroundFromPrefs(nextPrefs);
        setProfileBgApplyState(Boolean(getPendingFile()), false);
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
        if (!removed) {
          profileBgRemoveButton.disabled = false;
        }
      }
    }

    async function onApply() {
      if (!profileBgApplyButton) {
        return;
      }
      if (!hasPendingApply()) {
        setStatus("No pending background changes.", colors.DEFAULT);
        return;
      }
      profileBgApplyButton.disabled = true;
      try {
        const state = await loadActiveProfileUiPrefs();
        let finalPrefs = { ...state.uiPrefs };
        let preferredBlob = null;
        if (getPendingFile()) {
          if (!profileMediaStore || typeof profileMediaStore.upsertProfileBackground !== "function") {
            throw new Error("Profile media store is unavailable.");
          }
          const committedFile = getPendingFile();
          const meta = await profileMediaStore.upsertProfileBackground(
            state.profileId,
            committedFile,
            {
              previousAssetId: state.uiPrefs.backgroundAssetId,
              mimeType: committedFile.type || "application/octet-stream"
            }
          );
          finalPrefs = {
            ...state.uiPrefs,
            backgroundAssetId: meta.asset_id,
            backgroundEnabled: profileBgEnabledInput ? profileBgEnabledInput.checked === true : true,
            backgroundOpacity: profileBgOpacityInput
              ? clampProfileBackgroundOpacity(Number(profileBgOpacityInput.value || 18) / 100)
              : (state.uiPrefs.backgroundOpacity || 0.18),
            backgroundBackdropColor: profileBgBackdropColorInput
              ? normalizeProfileBackgroundBackdropColor(profileBgBackdropColorInput.value)
              : normalizeProfileBackgroundBackdropColor(state.uiPrefs.backgroundBackdropColor)
          };
          preferredBlob = committedFile;
          setPendingFile(null);
          if (profileBgFileInput) {
            profileBgFileInput.value = "";
          }
          await saveProfileUiPrefsForCurrentProfile(finalPrefs, {
            profileId: state.profileId,
            publishRuntime: false
          });
          previewManager.setPreviewFromBlob(committedFile);
          setProfileBgStatus(
            `Asset: ${meta.mime_type || committedFile.type || "image/*"}, ${formatBytes(meta.byte_size || committedFile.size || 0)}.`
          );
        }
        await publishProfileUiPrefsForCurrentProfile(finalPrefs, {
          profileId: state.profileId
        });
        await applyOptionsPageBackgroundFromPrefs(finalPrefs, {
          preferredBlob
        });
        setProfileBgApplyState(false, false);
        setStatus("Options page background applied.", colors.SUCCESS);
      } catch (err) {
        setProfileBgApplyState(true, false);
        const msg = err && err.message ? err.message : "Failed to apply profile background.";
        setStatus(msg, colors.ERROR);
      }
    }

    return {
      onEnabledChange,
      onOpacityInput,
      onOpacityChange,
      onBackdropColorChange,
      onFileChange,
      onRemove,
      onApply
    };
  }

  root.optionsProfileBackgroundActions = {
    createActions
  };
})();
