(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const contextFactory = root.optionsProfileBackgroundControllerContext
      && typeof root.optionsProfileBackgroundControllerContext.createControllerContext === "function"
      ? root.optionsProfileBackgroundControllerContext.createControllerContext
      : null;
    const context = contextFactory ? contextFactory(options) : null;
    if (!context || typeof context !== "object") {
      return {
        syncForLoadedPrefs: () => Promise.resolve(),
        renderProfileBgStatus: () => {},
        onEnabledChange: () => Promise.resolve(),
        onOpacityInput: () => {},
        onOpacityChange: () => Promise.resolve(),
        onBackdropColorChange: () => Promise.resolve(),
        onFileChange: () => {},
        onRemove: () => Promise.resolve(),
        onApply: () => Promise.resolve(),
        onPositionReset: () => Promise.resolve(),
        onCardThemeInput: () => {},
        onCardThemeChange: () => Promise.resolve(),
        onCardThemeReset: () => Promise.resolve(),
        onBeforeUnload: () => {}
      };
    }

    const {
      translate,
      settingsManager,
      ui,
      profileMediaStore,
      setStatus,
      colors,
      maxUploadBytes,
      profileBgBackdropColorInput,
      profileBgEnabledInput,
      profileBgOpacityInput,
      profileBgOpacityValueOutput,
      profileBgFileInput,
      profileBgRemoveButton,
      profileBgApplyButton,
      profileBgStatusOutput,
      profileBgPositionResetButton,
      profileCardThemeResetButton,
      clampProfileBackgroundOpacity,
      normalizeProfileBackgroundBackdropColor,
      formatBytes,
      defaultBackgroundPositionX,
      defaultBackgroundPositionY,
      normalizeProfileBackgroundPosition,
      prefsServiceFactory,
      runtimeBridgeFactory,
      backgroundActionsFactory,
      cardThemeActionsFactory,
      cardThemePresenter,
      previewManager,
      pageBackgroundManager,
      cardThemeManager
    } = context;

    let profileBgPendingFile = null;
    let profileBgHasPendingApply = false;

    function updateProfileBgOpacityLabel(value) {
      if (!profileBgOpacityValueOutput) {
        return;
      }
      const numeric = Number.isFinite(Number(value)) ? Number(value) : 18;
      profileBgOpacityValueOutput.textContent = `${Math.round(numeric)}%`;
    }

    let profileBgStatusState = {
      mode: "i18n",
      key: "hint_profile_bg_status_empty",
      substitutions: null,
      fallback: "No options page background image configured for this profile."
    };

    function renderProfileBgStatus() {
      if (!profileBgStatusOutput) {
        return;
      }
      if (profileBgStatusState.mode === "message") {
        profileBgStatusOutput.textContent = String(profileBgStatusState.message || "");
        return;
      }
      profileBgStatusOutput.textContent = translate(
        profileBgStatusState.key || "hint_profile_bg_status_empty",
        profileBgStatusState.substitutions || null,
        profileBgStatusState.fallback || "No options page background image configured for this profile."
      );
    }

    function setProfileBgStatus(message) {
      profileBgStatusState = {
        mode: "message",
        message: String(message || "")
      };
      renderProfileBgStatus();
    }

    function setProfileBgStatusLocalized(key, substitutions, fallback) {
      profileBgStatusState = {
        mode: "i18n",
        key: String(key || "").trim() || "hint_profile_bg_status_empty",
        substitutions: substitutions === undefined ? null : substitutions,
        fallback: String(fallback || "No options page background image configured for this profile.")
      };
      renderProfileBgStatus();
    }

    function setProfileBgApplyState(hasPendingApply, forceDisable) {
      profileBgHasPendingApply = hasPendingApply === true;
      if (!profileBgApplyButton) {
        return;
      }
      if (forceDisable === true) {
        profileBgApplyButton.disabled = true;
        return;
      }
      profileBgApplyButton.disabled = !profileBgHasPendingApply;
    }

    const prefsService = prefsServiceFactory
      ? prefsServiceFactory({
          settingsManager,
          ui,
          updateOpacityLabel: updateProfileBgOpacityLabel,
          setApplyState: (hasPendingApply, forceDisable) => {
            setProfileBgApplyState(hasPendingApply, forceDisable);
          },
          hasPendingApply: () => profileBgPendingFile
        })
      : null;

    const runtimeBridge = runtimeBridgeFactory
      ? runtimeBridgeFactory({
          translate,
          settingsManager,
          ui,
          profileMediaStore,
          previewManager,
          pageBackgroundManager,
          cardThemeManager,
          prefsService,
          formatBytes,
          normalizeProfileBackgroundBackdropColor,
          normalizeProfileBackgroundPosition,
          updateProfileBgOpacityLabel,
          updateProfileCardThemeLabels: (values) => cardThemePresenter.updateLabels(values),
          setProfileBgStatus,
          setProfileBgStatusLocalized,
          setProfileBgApplyState,
          getPendingFile: () => profileBgPendingFile,
          setPendingFile: (file) => {
            profileBgPendingFile = file;
          },
          clearFileInput: () => {
            if (profileBgFileInput) {
              profileBgFileInput.value = "";
            }
          },
          defaultOpacity: 0.18
        })
      : {
          loadActiveProfileUiPrefs: () => Promise.resolve({
            profileId: "default",
            uiPrefs: {},
            items: {}
          }),
          saveProfileUiPrefsForCurrentProfile: (nextPrefs) => Promise.resolve(
            nextPrefs && typeof nextPrefs === "object" ? { ...nextPrefs } : {}
          ),
          publishProfileUiPrefsForCurrentProfile: () => Promise.resolve(),
          applyOptionsPageBackgroundFromPrefs: () => Promise.resolve(),
          syncForLoadedPrefs: () => Promise.resolve()
        };

    const loadActiveProfileUiPrefs = typeof runtimeBridge.loadActiveProfileUiPrefs === "function"
      ? runtimeBridge.loadActiveProfileUiPrefs
      : (() => Promise.resolve({
          profileId: "default",
          uiPrefs: {},
          items: {}
        }));
    const saveProfileUiPrefsForCurrentProfile = typeof runtimeBridge.saveProfileUiPrefsForCurrentProfile === "function"
      ? runtimeBridge.saveProfileUiPrefsForCurrentProfile
      : ((nextPrefs) => Promise.resolve(nextPrefs && typeof nextPrefs === "object" ? { ...nextPrefs } : {}));
    const publishProfileUiPrefsForCurrentProfile = typeof runtimeBridge.publishProfileUiPrefsForCurrentProfile === "function"
      ? runtimeBridge.publishProfileUiPrefsForCurrentProfile
      : (() => Promise.resolve());
    const applyOptionsPageBackgroundFromPrefs = typeof runtimeBridge.applyOptionsPageBackgroundFromPrefs === "function"
      ? runtimeBridge.applyOptionsPageBackgroundFromPrefs
      : (() => Promise.resolve());
    const syncForLoadedPrefs = typeof runtimeBridge.syncForLoadedPrefs === "function"
      ? runtimeBridge.syncForLoadedPrefs
      : (() => Promise.resolve());

    function resolveBackgroundPositionFromSource(sourcePrefs) {
      const source = sourcePrefs && typeof sourcePrefs === "object" ? sourcePrefs : {};
      const fallback = normalizeProfileBackgroundPosition(
        source.backgroundPositionX,
        source.backgroundPositionY
      );
      if (previewManager && typeof previewManager.getPreviewPosition === "function") {
        const current = previewManager.getPreviewPosition();
        return normalizeProfileBackgroundPosition(current.x, current.y, fallback);
      }
      return fallback;
    }

    async function persistBackgroundPosition(position) {
      const state = await loadActiveProfileUiPrefs();
      const normalized = normalizeProfileBackgroundPosition(
        position && position.x,
        position && position.y,
        {
          x: state.uiPrefs.backgroundPositionX,
          y: state.uiPrefs.backgroundPositionY
        }
      );
      const existingX = Number(state.uiPrefs.backgroundPositionX);
      const existingY = Number(state.uiPrefs.backgroundPositionY);
      const unchanged = Number.isFinite(existingX)
        && Number.isFinite(existingY)
        && Math.abs(existingX - normalized.x) < 0.001
        && Math.abs(existingY - normalized.y) < 0.001;
      if (unchanged) {
        return {
          profileId: state.profileId,
          uiPrefs: state.uiPrefs,
          position: normalized
        };
      }
      const nextPrefs = {
        ...state.uiPrefs,
        backgroundPositionX: normalized.x,
        backgroundPositionY: normalized.y
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      return {
        profileId: state.profileId,
        uiPrefs: nextPrefs,
        position: normalized
      };
    }

    let backgroundPositionSaveChain = Promise.resolve();

    function queueBackgroundPositionSave(position) {
      backgroundPositionSaveChain = backgroundPositionSaveChain
        .catch(() => {})
        .then(() => persistBackgroundPosition(position));
      return backgroundPositionSaveChain;
    }

    function onPreviewPositionInput(position) {
      const normalized = normalizeProfileBackgroundPosition(position && position.x, position && position.y);
      if (pageBackgroundManager && typeof pageBackgroundManager.setBackgroundPosition === "function") {
        pageBackgroundManager.setBackgroundPosition(normalized.x, normalized.y);
      }
    }

    function onPreviewPositionCommit(position) {
      queueBackgroundPositionSave(position).catch((err) => {
        const message = err && err.message ? err.message : "Failed to save background image position.";
        setStatus(message, colors.ERROR);
      });
    }

    if (previewManager && typeof previewManager.bindPositionInteractions === "function") {
      previewManager.bindPositionInteractions({
        onInput: onPreviewPositionInput,
        onCommit: onPreviewPositionCommit
      });
    }

    const backgroundActions = backgroundActionsFactory
      ? backgroundActionsFactory({
          translate,
          colors,
          maxUploadBytes,
          profileBgEnabledInput,
          profileBgBackdropColorInput,
          profileBgOpacityInput,
          profileBgFileInput,
          profileBgRemoveButton,
          profileBgApplyButton,
          profileMediaStore,
          setStatus,
          setProfileBgStatus,
          setProfileBgStatusLocalized,
          setProfileBgApplyState,
          updateProfileBgOpacityLabel,
          clampProfileBackgroundOpacity,
          normalizeProfileBackgroundBackdropColor,
          formatBytes,
          previewManager,
          loadActiveProfileUiPrefs,
          saveProfileUiPrefsForCurrentProfile,
          publishProfileUiPrefsForCurrentProfile,
          applyOptionsPageBackgroundFromPrefs,
          resolveBackgroundPositionFromSource,
          getPendingFile: () => profileBgPendingFile,
          setPendingFile: (file) => {
            profileBgPendingFile = file;
          },
          hasPendingApply: () => profileBgHasPendingApply
        })
      : {
          onEnabledChange: () => Promise.resolve(),
          onOpacityInput: () => {},
          onOpacityChange: () => Promise.resolve(),
          onBackdropColorChange: () => Promise.resolve(),
          onFileChange: () => {},
          onRemove: () => Promise.resolve(),
          onApply: () => Promise.resolve()
        };

    const cardThemeActions = cardThemeActionsFactory
      ? cardThemeActionsFactory({
          translate,
          colors,
          setStatus,
          presenter: cardThemePresenter,
          loadActiveProfileUiPrefs,
          saveProfileUiPrefsForCurrentProfile,
          applyOptionsPageBackgroundFromPrefs
        })
      : {
          onInput: () => {},
          onChange: () => Promise.resolve(),
          onReset: () => Promise.resolve()
        };

    cardThemePresenter.configureInputs();
    if (profileCardThemeResetButton) {
      profileCardThemeResetButton.disabled = false;
    }
    if (profileBgPositionResetButton) {
      profileBgPositionResetButton.disabled = false;
    }

    async function onPositionReset() {
      const normalized = previewManager && typeof previewManager.setPreviewPosition === "function"
        ? previewManager.setPreviewPosition(defaultBackgroundPositionX, defaultBackgroundPositionY)
        : {
            x: defaultBackgroundPositionX,
            y: defaultBackgroundPositionY
          };
      if (pageBackgroundManager && typeof pageBackgroundManager.setBackgroundPosition === "function") {
        pageBackgroundManager.setBackgroundPosition(normalized.x, normalized.y);
      }
      await queueBackgroundPositionSave(normalized);
      setStatus(
        translate("status_profile_bg_position_reset", null, "Background image position reset."),
        colors.SUCCESS
      );
    }

    function onBeforeUnload() {
      previewManager.dispose();
      pageBackgroundManager.dispose();
    }

    return {
      syncForLoadedPrefs,
      applyOptionsPageBackgroundFromPrefs,
      renderProfileBgStatus,
      onEnabledChange: backgroundActions.onEnabledChange,
      onOpacityInput: backgroundActions.onOpacityInput,
      onOpacityChange: backgroundActions.onOpacityChange,
      onBackdropColorChange: backgroundActions.onBackdropColorChange,
      onFileChange: backgroundActions.onFileChange,
      onRemove: backgroundActions.onRemove,
      onApply: backgroundActions.onApply,
      onPositionReset,
      onCardThemeInput: cardThemeActions.onInput,
      onCardThemeChange: cardThemeActions.onChange,
      onCardThemeReset: cardThemeActions.onReset,
      onBeforeUnload
    };
  }

  root.optionsProfileBackground = {
    createController
  };
})();
