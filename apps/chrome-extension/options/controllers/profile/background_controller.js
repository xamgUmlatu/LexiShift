(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;
    const profileMediaStore = opts.profileMediaStore && typeof opts.profileMediaStore === "object"
      ? opts.profileMediaStore
      : null;
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
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
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const profileBgBackdropColorInput = elements.profileBgBackdropColorInput || null;
    const profileBgEnabledInput = elements.profileBgEnabledInput || null;
    const profileBgOpacityInput = elements.profileBgOpacityInput || null;
    const profileBgOpacityValueOutput = elements.profileBgOpacityValueOutput || null;
    const profileBgFileInput = elements.profileBgFileInput || null;
    const profileBgRemoveButton = elements.profileBgRemoveButton || null;
    const profileBgApplyButton = elements.profileBgApplyButton || null;
    const profileBgStatusOutput = elements.profileBgStatusOutput || null;
    const profileBgPreviewWrap = elements.profileBgPreviewWrap || null;
    const profileBgPreviewImage = elements.profileBgPreviewImage || null;
    const profileBgFocalMarker = elements.profileBgFocalMarker || null;
    const profileBgPositionResetButton = elements.profileBgPositionResetButton || null;
    const profileCardThemeHueInput = elements.profileCardThemeHueInput || null;
    const profileCardThemeHueValueOutput = elements.profileCardThemeHueValueOutput || null;
    const profileCardThemeSaturationInput = elements.profileCardThemeSaturationInput || null;
    const profileCardThemeSaturationValueOutput = elements.profileCardThemeSaturationValueOutput || null;
    const profileCardThemeBrightnessInput = elements.profileCardThemeBrightnessInput || null;
    const profileCardThemeBrightnessValueOutput = elements.profileCardThemeBrightnessValueOutput || null;
    const profileCardThemeTransparencyInput = elements.profileCardThemeTransparencyInput || null;
    const profileCardThemeTransparencyValueOutput = elements.profileCardThemeTransparencyValueOutput || null;
    const profileCardThemeResetButton = elements.profileCardThemeResetButton || null;

    let profileBgPendingFile = null;
    let profileBgHasPendingApply = false;

    const backgroundUtils = root.optionsProfileBackgroundUtils
      && typeof root.optionsProfileBackgroundUtils === "object"
      ? root.optionsProfileBackgroundUtils
      : {};
    const clampProfileBackgroundOpacity = typeof backgroundUtils.clampOpacity === "function"
      ? backgroundUtils.clampOpacity
      : (value) => {
          const parsed = Number.parseFloat(value);
          if (!Number.isFinite(parsed)) {
            return 0.18;
          }
          return Math.min(1, Math.max(0, parsed));
        };
    const normalizeProfileBackgroundBackdropColor = typeof backgroundUtils.normalizeBackdropColor === "function"
      ? backgroundUtils.normalizeBackdropColor
      : (value) => {
          const candidate = String(value || "").trim();
          if (/^#[0-9a-fA-F]{6}$/.test(candidate)) {
            return candidate.toLowerCase();
          }
          return "#fbf7f0";
        };
    const hexColorToRgb = typeof backgroundUtils.hexColorToRgb === "function"
      ? backgroundUtils.hexColorToRgb
      : (value) => {
          const normalized = normalizeProfileBackgroundBackdropColor(value).slice(1);
          return {
            r: Number.parseInt(normalized.slice(0, 2), 16),
            g: Number.parseInt(normalized.slice(2, 4), 16),
            b: Number.parseInt(normalized.slice(4, 6), 16)
          };
        };
    const formatBytes = typeof backgroundUtils.formatBytes === "function"
      ? backgroundUtils.formatBytes
      : (bytes) => {
          const value = Number(bytes);
          if (!Number.isFinite(value) || value <= 0) {
            return "0 B";
          }
          if (value < 1024) {
            return `${Math.round(value)} B`;
          }
          if (value < 1024 * 1024) {
            return `${(value / 1024).toFixed(1)} KB`;
          }
          return `${(value / (1024 * 1024)).toFixed(2)} MB`;
        };
    const clampProfileBackgroundPositionPercent = typeof backgroundUtils.clampPositionPercent === "function"
      ? backgroundUtils.clampPositionPercent
      : (value, fallback) => {
          const parsed = Number.parseFloat(value);
          const fallbackValue = Number.isFinite(Number(fallback)) ? Number(fallback) : 50;
          const base = Number.isFinite(parsed) ? parsed : fallbackValue;
          return Math.min(100, Math.max(0, base));
        };
    const defaultBackgroundPositionX = settingsManager && settingsManager.defaults
      ? clampProfileBackgroundPositionPercent(settingsManager.defaults.profileBackgroundPositionX, 50)
      : 50;
    const defaultBackgroundPositionY = settingsManager && settingsManager.defaults
      ? clampProfileBackgroundPositionPercent(settingsManager.defaults.profileBackgroundPositionY, 50)
      : 50;

    function normalizeProfileBackgroundPosition(nextX, nextY, fallback) {
      const base = fallback && typeof fallback === "object" ? fallback : {};
      const fallbackX = Number.isFinite(Number(base.x))
        ? Number(base.x)
        : defaultBackgroundPositionX;
      const fallbackY = Number.isFinite(Number(base.y))
        ? Number(base.y)
        : defaultBackgroundPositionY;
      return {
        x: clampProfileBackgroundPositionPercent(nextX, fallbackX),
        y: clampProfileBackgroundPositionPercent(nextY, fallbackY)
      };
    }

    const previewManagerFactory = root.optionsProfileBackgroundPreviewManager
      && typeof root.optionsProfileBackgroundPreviewManager.createManager === "function"
      ? root.optionsProfileBackgroundPreviewManager.createManager
      : null;
    const pageBackgroundManagerFactory = root.optionsProfileBackgroundPageBackgroundManager
      && typeof root.optionsProfileBackgroundPageBackgroundManager.createManager === "function"
      ? root.optionsProfileBackgroundPageBackgroundManager.createManager
      : null;
    const cardThemeManagerFactory = root.optionsProfileBackgroundCardThemeManager
      && typeof root.optionsProfileBackgroundCardThemeManager.createManager === "function"
      ? root.optionsProfileBackgroundCardThemeManager.createManager
      : null;
    const cardThemePresenterFactory = root.optionsProfileBackgroundCardThemePresenter
      && typeof root.optionsProfileBackgroundCardThemePresenter.createPresenter === "function"
      ? root.optionsProfileBackgroundCardThemePresenter.createPresenter
      : null;
    const prefsServiceFactory = root.optionsProfileBackgroundPrefsService
      && typeof root.optionsProfileBackgroundPrefsService.createService === "function"
      ? root.optionsProfileBackgroundPrefsService.createService
      : null;
    const runtimeBridgeFactory = root.optionsProfileBackgroundRuntimeBridge
      && typeof root.optionsProfileBackgroundRuntimeBridge.createBridge === "function"
      ? root.optionsProfileBackgroundRuntimeBridge.createBridge
      : null;
    const backgroundActionsFactory = root.optionsProfileBackgroundActions
      && typeof root.optionsProfileBackgroundActions.createActions === "function"
      ? root.optionsProfileBackgroundActions.createActions
      : null;
    const cardThemeActionsFactory = root.optionsProfileBackgroundCardThemeActions
      && typeof root.optionsProfileBackgroundCardThemeActions.createActions === "function"
      ? root.optionsProfileBackgroundCardThemeActions.createActions
      : null;

    function updateProfileBgOpacityLabel(value) {
      if (!profileBgOpacityValueOutput) {
        return;
      }
      const numeric = Number.isFinite(Number(value)) ? Number(value) : 18;
      profileBgOpacityValueOutput.textContent = `${Math.round(numeric)}%`;
    }

    const cardThemePresenter = cardThemePresenterFactory
      ? cardThemePresenterFactory({
          profileCardThemeHueInput,
          profileCardThemeHueValueOutput,
          profileCardThemeSaturationInput,
          profileCardThemeSaturationValueOutput,
          profileCardThemeBrightnessInput,
          profileCardThemeBrightnessValueOutput,
          profileCardThemeTransparencyInput,
          profileCardThemeTransparencyValueOutput,
          defaults: settingsManager && settingsManager.defaults
            ? {
                cardThemeHueDeg: settingsManager.defaults.profileCardThemeHueDeg,
                cardThemeSaturationPercent: settingsManager.defaults.profileCardThemeSaturationPercent,
                cardThemeBrightnessPercent: settingsManager.defaults.profileCardThemeBrightnessPercent,
                cardThemeTransparencyPercent: settingsManager.defaults.profileCardThemeTransparencyPercent
              }
            : {}
        })
      : {
          hasControls: () => false,
          resolveDefaultUiPrefs: () => ({
            cardThemeHueDeg: 0,
            cardThemeSaturationPercent: 100,
            cardThemeBrightnessPercent: 100,
            cardThemeTransparencyPercent: 100
          }),
          updateLabels: () => ({
            hueDeg: 0,
            saturationPercent: 100,
            brightnessPercent: 100,
            transparencyPercent: 100
          }),
          configureInputs: () => {},
          readPrefsFromInputs: () => ({
            cardThemeHueDeg: 0,
            cardThemeSaturationPercent: 100,
            cardThemeBrightnessPercent: 100,
            cardThemeTransparencyPercent: 100
          })
        };

    const previewManager = previewManagerFactory
      ? previewManagerFactory({
          previewImage: profileBgPreviewImage,
          previewWrap: profileBgPreviewWrap,
          previewMarker: profileBgFocalMarker,
          clampPositionPercent: clampProfileBackgroundPositionPercent,
          urlApi: URL
        })
      : {
          clearPreview: () => {},
          setPreviewFromBlob: () => {},
          setPreviewPosition: () => ({ x: defaultBackgroundPositionX, y: defaultBackgroundPositionY }),
          getPreviewPosition: () => ({ x: defaultBackgroundPositionX, y: defaultBackgroundPositionY }),
          bindPositionInteractions: () => {},
          dispose: () => {}
        };
    const pageBackgroundManager = pageBackgroundManagerFactory
      ? pageBackgroundManagerFactory({
          documentRef: document,
          normalizeBackdropColor: normalizeProfileBackgroundBackdropColor,
          clampOpacity: clampProfileBackgroundOpacity,
          clampPositionPercent: clampProfileBackgroundPositionPercent,
          hexColorToRgb,
          urlApi: URL
        })
      : {
          applyBackdropOnly: () => {},
          applyBackgroundFromBlob: () => {},
          setBackgroundPosition: () => {},
          dispose: () => {}
        };
    const cardThemeManager = cardThemeManagerFactory
      ? cardThemeManagerFactory({
          documentRef: document,
          defaults: settingsManager && settingsManager.defaults
            ? {
                cardThemeHueDeg: settingsManager.defaults.profileCardThemeHueDeg,
                cardThemeSaturationPercent: settingsManager.defaults.profileCardThemeSaturationPercent,
                cardThemeBrightnessPercent: settingsManager.defaults.profileCardThemeBrightnessPercent,
                cardThemeTransparencyPercent: settingsManager.defaults.profileCardThemeTransparencyPercent
              }
            : {}
        })
      : {
          applyCardThemeFromPrefs: () => ({
            hueDeg: 0,
            saturationPercent: 100,
            brightnessPercent: 100,
            transparencyPercent: 100
          }),
          clearCardTheme: () => {}
        };

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
