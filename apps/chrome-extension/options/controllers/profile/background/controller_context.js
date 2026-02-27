(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createControllerContext(options) {
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

    return {
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
    };
  }

  root.optionsProfileBackgroundControllerContext = {
    createControllerContext
  };
})();
