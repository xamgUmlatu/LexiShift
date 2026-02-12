(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function createPresenter(options) {
    const opts = isObject(options) ? options : {};
    const profileCardThemeHueInput = opts.profileCardThemeHueInput || null;
    const profileCardThemeHueValueOutput = opts.profileCardThemeHueValueOutput || null;
    const profileCardThemeSaturationInput = opts.profileCardThemeSaturationInput || null;
    const profileCardThemeSaturationValueOutput = opts.profileCardThemeSaturationValueOutput || null;
    const profileCardThemeBrightnessInput = opts.profileCardThemeBrightnessInput || null;
    const profileCardThemeBrightnessValueOutput = opts.profileCardThemeBrightnessValueOutput || null;
    const profileCardThemeTransparencyInput = opts.profileCardThemeTransparencyInput || null;
    const profileCardThemeTransparencyValueOutput = opts.profileCardThemeTransparencyValueOutput || null;
    const themePrefs = opts.themePrefs && isObject(opts.themePrefs)
      ? opts.themePrefs
      : (root.profileUiThemePrefs && isObject(root.profileUiThemePrefs) ? root.profileUiThemePrefs : {});
    const resolveCardThemeLimits = typeof themePrefs.resolveCardThemeLimits === "function"
      ? themePrefs.resolveCardThemeLimits
      : () => ({
          hueDeg: { min: -180, max: 180, step: 1, defaultValue: 0 },
          saturationPercent: { min: 70, max: 140, step: 1, defaultValue: 100 },
          brightnessPercent: { min: 80, max: 125, step: 1, defaultValue: 100 },
          transparencyPercent: { min: 40, max: 100, step: 1, defaultValue: 100 }
        });
    const resolveCardThemeDefaults = typeof themePrefs.resolveCardThemeDefaults === "function"
      ? themePrefs.resolveCardThemeDefaults
      : () => ({
          hueDeg: 0,
          saturationPercent: 100,
          brightnessPercent: 100,
          transparencyPercent: 100
        });
    const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
      ? themePrefs.normalizeCardThemePrefs
      : () => ({
          cardThemeHueDeg: 0,
          cardThemeSaturationPercent: 100,
          cardThemeBrightnessPercent: 100,
          cardThemeTransparencyPercent: 100
        });

    function hasControls() {
      return Boolean(
        profileCardThemeHueInput
        || profileCardThemeSaturationInput
        || profileCardThemeBrightnessInput
        || profileCardThemeTransparencyInput
      );
    }

    function resolveDefaultUiPrefs() {
      const defaults = resolveCardThemeDefaults({
        defaults: opts.defaults
      });
      return {
        cardThemeHueDeg: defaults.hueDeg,
        cardThemeSaturationPercent: defaults.saturationPercent,
        cardThemeBrightnessPercent: defaults.brightnessPercent,
        cardThemeTransparencyPercent: defaults.transparencyPercent
      };
    }

    function normalizeValues(values, fallback) {
      const source = isObject(values) ? values : {};
      const resolvedFallback = isObject(fallback) ? fallback : resolveDefaultUiPrefs();
      return normalizeCardThemePrefs({
        cardThemeHueDeg: source.cardThemeHueDeg !== undefined ? source.cardThemeHueDeg : source.hueDeg,
        cardThemeSaturationPercent: source.cardThemeSaturationPercent !== undefined
          ? source.cardThemeSaturationPercent
          : source.saturationPercent,
        cardThemeBrightnessPercent: source.cardThemeBrightnessPercent !== undefined
          ? source.cardThemeBrightnessPercent
          : source.brightnessPercent,
        cardThemeTransparencyPercent: source.cardThemeTransparencyPercent !== undefined
          ? source.cardThemeTransparencyPercent
          : source.transparencyPercent
      }, {
        fallback: resolvedFallback,
        defaults: resolveDefaultUiPrefs()
      });
    }

    function updateLabels(values) {
      const fallbackFromInputs = {
        cardThemeHueDeg: profileCardThemeHueInput ? profileCardThemeHueInput.value : undefined,
        cardThemeSaturationPercent: profileCardThemeSaturationInput ? profileCardThemeSaturationInput.value : undefined,
        cardThemeBrightnessPercent: profileCardThemeBrightnessInput ? profileCardThemeBrightnessInput.value : undefined,
        cardThemeTransparencyPercent: profileCardThemeTransparencyInput
          ? profileCardThemeTransparencyInput.value
          : undefined
      };
      const normalized = normalizeValues(values, fallbackFromInputs);
      if (profileCardThemeHueInput) {
        profileCardThemeHueInput.value = String(normalized.cardThemeHueDeg);
      }
      if (profileCardThemeHueValueOutput) {
        profileCardThemeHueValueOutput.textContent = `${Math.round(normalized.cardThemeHueDeg)}°`;
      }
      if (profileCardThemeSaturationInput) {
        profileCardThemeSaturationInput.value = String(normalized.cardThemeSaturationPercent);
      }
      if (profileCardThemeSaturationValueOutput) {
        profileCardThemeSaturationValueOutput.textContent = `${Math.round(normalized.cardThemeSaturationPercent)}%`;
      }
      if (profileCardThemeBrightnessInput) {
        profileCardThemeBrightnessInput.value = String(normalized.cardThemeBrightnessPercent);
      }
      if (profileCardThemeBrightnessValueOutput) {
        profileCardThemeBrightnessValueOutput.textContent = `${Math.round(normalized.cardThemeBrightnessPercent)}%`;
      }
      if (profileCardThemeTransparencyInput) {
        profileCardThemeTransparencyInput.value = String(normalized.cardThemeTransparencyPercent);
      }
      if (profileCardThemeTransparencyValueOutput) {
        profileCardThemeTransparencyValueOutput.textContent = `${Math.round(normalized.cardThemeTransparencyPercent)}%`;
      }
      return {
        hueDeg: normalized.cardThemeHueDeg,
        saturationPercent: normalized.cardThemeSaturationPercent,
        brightnessPercent: normalized.cardThemeBrightnessPercent,
        transparencyPercent: normalized.cardThemeTransparencyPercent
      };
    }

    function configureInputs() {
      const limits = resolveCardThemeLimits();
      if (profileCardThemeHueInput) {
        profileCardThemeHueInput.min = String(limits.hueDeg.min);
        profileCardThemeHueInput.max = String(limits.hueDeg.max);
        profileCardThemeHueInput.step = String(limits.hueDeg.step || 1);
      }
      if (profileCardThemeSaturationInput) {
        profileCardThemeSaturationInput.min = String(limits.saturationPercent.min);
        profileCardThemeSaturationInput.max = String(limits.saturationPercent.max);
        profileCardThemeSaturationInput.step = String(limits.saturationPercent.step || 1);
      }
      if (profileCardThemeBrightnessInput) {
        profileCardThemeBrightnessInput.min = String(limits.brightnessPercent.min);
        profileCardThemeBrightnessInput.max = String(limits.brightnessPercent.max);
        profileCardThemeBrightnessInput.step = String(limits.brightnessPercent.step || 1);
      }
      if (profileCardThemeTransparencyInput) {
        profileCardThemeTransparencyInput.min = String(limits.transparencyPercent.min);
        profileCardThemeTransparencyInput.max = String(limits.transparencyPercent.max);
        profileCardThemeTransparencyInput.step = String(limits.transparencyPercent.step || 1);
      }
      updateLabels(resolveDefaultUiPrefs());
    }

    function readPrefsFromInputs(currentPrefs) {
      const fallback = isObject(currentPrefs) ? currentPrefs : resolveDefaultUiPrefs();
      const normalized = normalizeCardThemePrefs({
        cardThemeHueDeg: profileCardThemeHueInput ? profileCardThemeHueInput.value : undefined,
        cardThemeSaturationPercent: profileCardThemeSaturationInput
          ? profileCardThemeSaturationInput.value
          : undefined,
        cardThemeBrightnessPercent: profileCardThemeBrightnessInput
          ? profileCardThemeBrightnessInput.value
          : undefined,
        cardThemeTransparencyPercent: profileCardThemeTransparencyInput
          ? profileCardThemeTransparencyInput.value
          : undefined
      }, {
        fallback,
        defaults: resolveDefaultUiPrefs()
      });
      updateLabels({
        cardThemeHueDeg: normalized.cardThemeHueDeg,
        cardThemeSaturationPercent: normalized.cardThemeSaturationPercent,
        cardThemeBrightnessPercent: normalized.cardThemeBrightnessPercent,
        cardThemeTransparencyPercent: normalized.cardThemeTransparencyPercent
      });
      return normalized;
    }

    return {
      hasControls,
      resolveDefaultUiPrefs,
      updateLabels,
      configureInputs,
      readPrefsFromInputs
    };
  }

  root.optionsProfileBackgroundCardThemePresenter = {
    createPresenter
  };
})();
