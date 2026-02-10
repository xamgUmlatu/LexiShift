(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.t === "function"
      ? opts.t
      : ((_key, _subs, fallback) => fallback || "");
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
    const previewManagerFactory = root.optionsProfileBackgroundPreviewManager
      && typeof root.optionsProfileBackgroundPreviewManager.createManager === "function"
      ? root.optionsProfileBackgroundPreviewManager.createManager
      : null;
    const pageBackgroundManagerFactory = root.optionsProfileBackgroundPageBackgroundManager
      && typeof root.optionsProfileBackgroundPageBackgroundManager.createManager === "function"
      ? root.optionsProfileBackgroundPageBackgroundManager.createManager
      : null;
    const prefsServiceFactory = root.optionsProfileBackgroundPrefsService
      && typeof root.optionsProfileBackgroundPrefsService.createService === "function"
      ? root.optionsProfileBackgroundPrefsService.createService
      : null;
    const runtimeBridgeFactory = root.optionsProfileBackgroundRuntimeBridge
      && typeof root.optionsProfileBackgroundRuntimeBridge.createBridge === "function"
      ? root.optionsProfileBackgroundRuntimeBridge.createBridge
      : null;
    const actionsFactory = root.optionsProfileBackgroundActions
      && typeof root.optionsProfileBackgroundActions.createActions === "function"
      ? root.optionsProfileBackgroundActions.createActions
      : null;

    function updateProfileBgOpacityLabel(value) {
      if (!profileBgOpacityValueOutput) {
        return;
      }
      const numeric = Number.isFinite(Number(value)) ? Number(value) : 18;
      profileBgOpacityValueOutput.textContent = `${Math.round(numeric)}%`;
    }

    const previewManager = previewManagerFactory
      ? previewManagerFactory({
          previewImage: profileBgPreviewImage,
          previewWrap: profileBgPreviewWrap,
          urlApi: URL
        })
      : {
          clearPreview: () => {},
          setPreviewFromBlob: () => {},
          dispose: () => {}
        };
    const pageBackgroundManager = pageBackgroundManagerFactory
      ? pageBackgroundManagerFactory({
          documentRef: document,
          normalizeBackdropColor: normalizeProfileBackgroundBackdropColor,
          clampOpacity: clampProfileBackgroundOpacity,
          hexColorToRgb,
          urlApi: URL
        })
      : {
          applyBackdropOnly: () => {},
          applyBackgroundFromBlob: () => {},
          dispose: () => {}
        };

    function setProfileBgStatus(message) {
      if (!profileBgStatusOutput) {
        return;
      }
      profileBgStatusOutput.textContent = message;
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
          prefsService,
          formatBytes,
          normalizeProfileBackgroundBackdropColor,
          updateProfileBgOpacityLabel,
          setProfileBgStatus,
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

    const backgroundActions = actionsFactory
      ? actionsFactory({
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

    function onBeforeUnload() {
      previewManager.dispose();
      pageBackgroundManager.dispose();
    }

    return {
      syncForLoadedPrefs,
      onEnabledChange: backgroundActions.onEnabledChange,
      onOpacityInput: backgroundActions.onOpacityInput,
      onOpacityChange: backgroundActions.onOpacityChange,
      onBackdropColorChange: backgroundActions.onBackdropColorChange,
      onFileChange: backgroundActions.onFileChange,
      onRemove: backgroundActions.onRemove,
      onApply: backgroundActions.onApply,
      onBeforeUnload
    };
  }

  root.optionsProfileBackground = {
    createController
  };
})();
