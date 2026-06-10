(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function resolveBackgroundUtils() {
    const utils = isObject(root.optionsProfileBackgroundUtils)
      ? root.optionsProfileBackgroundUtils
      : {};
    const normalizeBackdropColor = typeof utils.normalizeBackdropColor === "function"
      ? utils.normalizeBackdropColor
      : (value) => {
          const candidate = String(value || "").trim();
          return /^#[0-9a-fA-F]{6}$/.test(candidate) ? candidate.toLowerCase() : "#fbf7f0";
        };
    return {
      clampOpacity: typeof utils.clampOpacity === "function"
        ? utils.clampOpacity
        : (value) => Math.min(1, Math.max(0, Number.parseFloat(value) || 0.18)),
      clampPositionPercent: typeof utils.clampPositionPercent === "function"
        ? utils.clampPositionPercent
        : (value, fallback) => {
            const parsed = Number.parseFloat(value);
            const base = Number.isFinite(parsed) ? parsed : Number(fallback || 50);
            return Math.min(100, Math.max(0, base));
          },
      hexColorToRgb: typeof utils.hexColorToRgb === "function"
        ? utils.hexColorToRgb
        : (value) => {
            const normalized = normalizeBackdropColor(value).slice(1);
            return {
              r: Number.parseInt(normalized.slice(0, 2), 16),
              g: Number.parseInt(normalized.slice(2, 4), 16),
              b: Number.parseInt(normalized.slice(4, 6), 16)
            };
          },
      normalizeBackdropColor
    };
  }

  function createThemeApplier(options) {
    const opts = isObject(options) ? options : {};
    const documentRef = opts.documentRef && opts.documentRef.body ? opts.documentRef : document;
    const settingsManager = isObject(opts.settingsManager) ? opts.settingsManager : null;
    const mediaStore = isObject(opts.profileMediaStore) ? opts.profileMediaStore : root.profileMediaStore;
    const utils = resolveBackgroundUtils();
    const pageBackgroundFactory = root.optionsProfileBackgroundPageBackgroundManager;
    const cardThemeFactory = root.optionsProfileBackgroundCardThemeManager;
    const pageBackgroundManager = pageBackgroundFactory
      && typeof pageBackgroundFactory.createManager === "function"
      ? pageBackgroundFactory.createManager({
          documentRef,
          normalizeBackdropColor: utils.normalizeBackdropColor,
          clampOpacity: utils.clampOpacity,
          clampPositionPercent: utils.clampPositionPercent,
          hexColorToRgb: utils.hexColorToRgb,
          urlApi: URL
        })
      : null;
    const cardThemeManager = cardThemeFactory
      && typeof cardThemeFactory.createManager === "function"
      ? cardThemeFactory.createManager({
          documentRef,
          defaults: settingsManager && settingsManager.defaults
            ? {
                cardThemeHueDeg: settingsManager.defaults.profileCardThemeHueDeg,
                cardThemeSaturationPercent: settingsManager.defaults.profileCardThemeSaturationPercent,
                cardThemeBrightnessPercent: settingsManager.defaults.profileCardThemeBrightnessPercent,
                cardThemeTransparencyPercent: settingsManager.defaults.profileCardThemeTransparencyPercent
              }
            : {}
        })
      : null;

    async function applyTheme(config) {
      if (!settingsManager || typeof settingsManager.getProfileUiPrefs !== "function") {
        return { profileId: "default", applied: false };
      }
      const cfg = isObject(config) ? config : {};
      const items = isObject(cfg.items) ? cfg.items : await settingsManager.load();
      const profileId = typeof settingsManager.getSelectedSrsProfileId === "function"
        ? settingsManager.getSelectedSrsProfileId(items)
        : "default";
      const prefs = settingsManager.getProfileUiPrefs(items, { profileId });
      if (cardThemeManager && typeof cardThemeManager.applyCardThemeFromPrefs === "function") {
        cardThemeManager.applyCardThemeFromPrefs(prefs);
      }
      await applyBackground(prefs);
      return { profileId, applied: true };
    }

    async function applyBackground(rawPrefs) {
      if (!pageBackgroundManager) {
        return;
      }
      const prefs = isObject(rawPrefs) ? rawPrefs : {};
      const backdropColor = utils.normalizeBackdropColor(prefs.backgroundBackdropColor);
      const assetId = String(prefs.backgroundAssetId || "").trim();
      if (!assetId || !mediaStore || typeof mediaStore.getAsset !== "function") {
        pageBackgroundManager.applyBackdropOnly(backdropColor);
        return;
      }
      try {
        const record = await mediaStore.getAsset(assetId);
        if (!record || typeof Blob !== "function" || !(record.blob instanceof Blob)) {
          pageBackgroundManager.applyBackdropOnly(backdropColor);
          return;
        }
        pageBackgroundManager.applyBackgroundFromBlob(
          record.blob,
          prefs.backgroundOpacity,
          backdropColor,
          prefs.backgroundPositionX,
          prefs.backgroundPositionY
        );
      } catch (_error) {
        pageBackgroundManager.applyBackdropOnly(backdropColor);
      }
    }

    return { applyTheme };
  }

  root.learningDashboardTheme = {
    createThemeApplier
  };
})();
