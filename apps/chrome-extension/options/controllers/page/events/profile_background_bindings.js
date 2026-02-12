(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const bindAsyncListener = typeof opts.bindAsyncListener === "function"
      ? opts.bindAsyncListener
      : (() => {});
    const profileBackgroundController = opts.profileBackgroundController && typeof opts.profileBackgroundController === "object"
      ? opts.profileBackgroundController
      : null;
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const profileBgEnabledInput = elements.profileBgEnabledInput || null;
    const profileBgBackdropColorInput = elements.profileBgBackdropColorInput || null;
    const profileBgOpacityInput = elements.profileBgOpacityInput || null;
    const profileBgFileInput = elements.profileBgFileInput || null;
    const profileBgRemoveButton = elements.profileBgRemoveButton || null;
    const profileBgApplyButton = elements.profileBgApplyButton || null;
    const profileBgPositionResetButton = elements.profileBgPositionResetButton || null;
    const profileCardThemeHueInput = elements.profileCardThemeHueInput || null;
    const profileCardThemeSaturationInput = elements.profileCardThemeSaturationInput || null;
    const profileCardThemeBrightnessInput = elements.profileCardThemeBrightnessInput || null;
    const profileCardThemeTransparencyInput = elements.profileCardThemeTransparencyInput || null;
    const profileCardThemeResetButton = elements.profileCardThemeResetButton || null;

    bindAsyncListener(profileBgEnabledInput, "change", () => profileBackgroundController.onEnabledChange(), {
      fallbackMessage: "Failed to save profile background setting.",
      logMessage: "Profile background enable save failed."
    });
    bindAsyncListener(profileBgBackdropColorInput, "change", () => profileBackgroundController.onBackdropColorChange(), {
      fallbackMessage: "Failed to save backdrop color.",
      logMessage: "Profile background backdrop color save failed."
    });
    if (profileBgOpacityInput) {
      profileBgOpacityInput.addEventListener("input", () => {
        profileBackgroundController.onOpacityInput();
      });
      bindAsyncListener(profileBgOpacityInput, "change", () => profileBackgroundController.onOpacityChange(), {
        fallbackMessage: "Failed to save profile background opacity.",
        logMessage: "Profile background opacity save failed."
      });
    }
    if (profileBgFileInput) {
      profileBgFileInput.addEventListener("change", () => {
        profileBackgroundController.onFileChange();
      });
    }
    bindAsyncListener(profileBgRemoveButton, "click", () => profileBackgroundController.onRemove(), {
      fallbackMessage: "Failed to remove profile background image.",
      logMessage: "Profile background removal failed."
    });
    bindAsyncListener(profileBgApplyButton, "click", () => profileBackgroundController.onApply(), {
      fallbackMessage: "Failed to apply profile background.",
      logMessage: "Profile background apply failed."
    });
    bindAsyncListener(profileBgPositionResetButton, "click", () => profileBackgroundController.onPositionReset(), {
      fallbackMessage: "Failed to reset image position.",
      logMessage: "Profile background image position reset failed."
    });
    if (profileCardThemeHueInput) {
      profileCardThemeHueInput.addEventListener("input", () => {
        profileBackgroundController.onCardThemeInput();
      });
      bindAsyncListener(profileCardThemeHueInput, "change", () => profileBackgroundController.onCardThemeChange(), {
        fallbackMessage: "Failed to save card color settings.",
        logMessage: "Card color settings save failed (hue)."
      });
    }
    if (profileCardThemeSaturationInput) {
      profileCardThemeSaturationInput.addEventListener("input", () => {
        profileBackgroundController.onCardThemeInput();
      });
      bindAsyncListener(
        profileCardThemeSaturationInput,
        "change",
        () => profileBackgroundController.onCardThemeChange(),
        {
          fallbackMessage: "Failed to save card color settings.",
          logMessage: "Card color settings save failed (saturation)."
        }
      );
    }
    if (profileCardThemeBrightnessInput) {
      profileCardThemeBrightnessInput.addEventListener("input", () => {
        profileBackgroundController.onCardThemeInput();
      });
      bindAsyncListener(
        profileCardThemeBrightnessInput,
        "change",
        () => profileBackgroundController.onCardThemeChange(),
        {
          fallbackMessage: "Failed to save card color settings.",
          logMessage: "Card color settings save failed (brightness)."
        }
      );
    }
    if (profileCardThemeTransparencyInput) {
      profileCardThemeTransparencyInput.addEventListener("input", () => {
        profileBackgroundController.onCardThemeInput();
      });
      bindAsyncListener(
        profileCardThemeTransparencyInput,
        "change",
        () => profileBackgroundController.onCardThemeChange(),
        {
          fallbackMessage: "Failed to save card color settings.",
          logMessage: "Card color settings save failed (transparency)."
        }
      );
    }
    bindAsyncListener(profileCardThemeResetButton, "click", () => profileBackgroundController.onCardThemeReset(), {
      fallbackMessage: "Failed to reset card color settings.",
      logMessage: "Card color settings reset failed."
    });

    window.addEventListener("beforeunload", () => {
      profileBackgroundController.onBeforeUnload();
    });
  }

  root.optionsEventProfileBackgroundBindings = {
    bind
  };
})();
