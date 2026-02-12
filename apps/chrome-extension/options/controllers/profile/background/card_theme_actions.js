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
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const presenter = opts.presenter && typeof opts.presenter === "object"
      ? opts.presenter
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
          readPrefsFromInputs: () => ({
            cardThemeHueDeg: 0,
            cardThemeSaturationPercent: 100,
            cardThemeBrightnessPercent: 100,
            cardThemeTransparencyPercent: 100
          })
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
    const applyOptionsPageBackgroundFromPrefs = typeof opts.applyOptionsPageBackgroundFromPrefs === "function"
      ? opts.applyOptionsPageBackgroundFromPrefs
      : (() => Promise.resolve());

    function onInput() {
      if (!presenter.hasControls()) {
        return;
      }
      presenter.readPrefsFromInputs({});
    }

    async function onChange() {
      if (!presenter.hasControls()) {
        return;
      }
      const state = await loadActiveProfileUiPrefs();
      const nextPrefs = {
        ...state.uiPrefs,
        ...presenter.readPrefsFromInputs(state.uiPrefs)
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      setStatus(translate(
        "status_profile_card_theme_saved",
        null,
        "Card color settings saved."
      ), colors.SUCCESS);
    }

    async function onReset() {
      if (!presenter.hasControls()) {
        return;
      }
      const defaults = presenter.resolveDefaultUiPrefs();
      presenter.updateLabels(defaults);
      const state = await loadActiveProfileUiPrefs();
      const nextPrefs = {
        ...state.uiPrefs,
        ...defaults
      };
      await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      await applyOptionsPageBackgroundFromPrefs(nextPrefs);
      setStatus(translate(
        "status_profile_card_theme_reset",
        null,
        "Card color settings reset."
      ), colors.SUCCESS);
    }

    return {
      onInput,
      onChange,
      onReset
    };
  }

  root.optionsProfileBackgroundCardThemeActions = {
    createActions
  };
})();
