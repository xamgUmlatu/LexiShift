(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const ui = opts.ui && typeof opts.ui === "object"
      ? opts.ui
      : {
          COLORS: {
            SUCCESS: "#3c5a2a",
            ERROR: "#b42318",
            DEFAULT: "#6c675f"
          }
        };
    const saveDisplaySettings = typeof opts.saveDisplaySettings === "function"
      ? opts.saveDisplaySettings
      : (() => {});
    const saveReplacementSettings = typeof opts.saveReplacementSettings === "function"
      ? opts.saveReplacementSettings
      : (() => {});
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const highlightEnabledInput = elements.highlightEnabledInput || null;
    const highlightColorInput = elements.highlightColorInput || null;
    const highlightColorText = elements.highlightColorText || null;
    const maxOnePerBlockInput = elements.maxOnePerBlockInput || null;
    const allowAdjacentInput = elements.allowAdjacentInput || null;
    const maxReplacementsPerPageInput = elements.maxReplacementsPerPageInput || null;
    const maxReplacementsPerLemmaPageInput = elements.maxReplacementsPerLemmaPageInput || null;
    const debugEnabledInput = elements.debugEnabledInput || null;
    const debugFocusInput = elements.debugFocusInput || null;
    const enabledInput = elements.enabledInput || null;

    if (highlightEnabledInput) {
      highlightEnabledInput.addEventListener("change", () => {
        if (highlightColorInput) {
          highlightColorInput.disabled = !highlightEnabledInput.checked;
        }
        if (highlightColorText) {
          highlightColorText.disabled = !highlightEnabledInput.checked;
        }
        saveDisplaySettings();
      });
    }

    if (highlightColorInput) {
      highlightColorInput.addEventListener("change", () => {
        if (highlightColorText) {
          highlightColorText.value = highlightColorInput.value;
        }
        saveDisplaySettings();
      });
    }

    if (highlightColorText) {
      highlightColorText.addEventListener("change", () => {
        const value = highlightColorText.value.trim();
        if (value) {
          if (highlightColorInput) {
            highlightColorInput.value = value;
          }
          saveDisplaySettings();
        }
      });
    }

    if (maxOnePerBlockInput) {
      maxOnePerBlockInput.addEventListener("change", () => {
        saveReplacementSettings();
      });
    }

    if (allowAdjacentInput) {
      allowAdjacentInput.addEventListener("change", () => {
        saveReplacementSettings();
      });
    }
    if (maxReplacementsPerPageInput) {
      maxReplacementsPerPageInput.addEventListener("change", saveReplacementSettings);
    }
    if (maxReplacementsPerLemmaPageInput) {
      maxReplacementsPerLemmaPageInput.addEventListener("change", saveReplacementSettings);
    }

    if (debugEnabledInput) {
      debugEnabledInput.addEventListener("change", () => {
        if (debugFocusInput) {
          debugFocusInput.disabled = !debugEnabledInput.checked;
        }
        saveDisplaySettings();
      });
    }

    if (debugFocusInput) {
      debugFocusInput.addEventListener("change", () => {
        saveDisplaySettings();
      });
    }

    if (enabledInput) {
      enabledInput.addEventListener("change", () => {
        chrome.storage.local.set({ enabled: enabledInput.checked }, () => {
          setStatus(translate("status_extension_updated", null, "Extension updated."), ui.COLORS.SUCCESS);
        });
      });
    }
  }

  root.optionsEventGeneralDisplayBindings = {
    bind
  };
})();
