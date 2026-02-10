(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const translate = typeof opts.t === "function"
      ? opts.t
      : ((_key, _subs, fallback) => fallback || "");
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const highlightEnabledInput = elements.highlightEnabledInput || null;
    const highlightColorInput = elements.highlightColorInput || null;
    const debugEnabledInput = elements.debugEnabledInput || null;
    const debugFocusInput = elements.debugFocusInput || null;
    const maxOnePerBlockInput = elements.maxOnePerBlockInput || null;
    const allowAdjacentInput = elements.allowAdjacentInput || null;
    const maxReplacementsPerPageInput = elements.maxReplacementsPerPageInput || null;
    const maxReplacementsPerLemmaPageInput = elements.maxReplacementsPerLemmaPageInput || null;

    function saveDisplaySettings() {
      if (!settingsManager || !highlightEnabledInput || !highlightColorInput || !debugEnabledInput || !debugFocusInput) {
        return;
      }
      const highlightEnabled = highlightEnabledInput.checked;
      const highlightColor = highlightColorInput.value || settingsManager.defaults.highlightColor;
      const debugEnabled = debugEnabledInput.checked;
      const debugFocusWord = debugFocusInput.value.trim();
      chrome.storage.local.set({ highlightEnabled, highlightColor, debugEnabled, debugFocusWord }, () => {
        setStatus(translate("status_display_saved", null, "Display settings saved."), colors.SUCCESS);
      });
    }

    function saveReplacementSettings() {
      if (!settingsManager || !maxOnePerBlockInput || !allowAdjacentInput) {
        return;
      }
      const maxOnePerTextBlock = maxOnePerBlockInput.checked;
      const allowAdjacentReplacements = allowAdjacentInput.checked;
      const maxPerPageRaw = maxReplacementsPerPageInput
        ? parseInt(maxReplacementsPerPageInput.value, 10)
        : settingsManager.defaults.maxReplacementsPerPage;
      const maxPerLemmaRaw = maxReplacementsPerLemmaPageInput
        ? parseInt(maxReplacementsPerLemmaPageInput.value, 10)
        : settingsManager.defaults.maxReplacementsPerLemmaPerPage;
      const maxReplacementsPerPage = Number.isFinite(maxPerPageRaw)
        ? Math.max(0, maxPerPageRaw)
        : (settingsManager.defaults.maxReplacementsPerPage || 0);
      const maxReplacementsPerLemmaPerPage = Number.isFinite(maxPerLemmaRaw)
        ? Math.max(0, maxPerLemmaRaw)
        : (settingsManager.defaults.maxReplacementsPerLemmaPerPage || 0);
      if (maxReplacementsPerPageInput) {
        maxReplacementsPerPageInput.value = String(maxReplacementsPerPage);
      }
      if (maxReplacementsPerLemmaPageInput) {
        maxReplacementsPerLemmaPageInput.value = String(maxReplacementsPerLemmaPerPage);
      }
      chrome.storage.local.set({
        maxOnePerTextBlock,
        allowAdjacentReplacements,
        maxReplacementsPerPage,
        maxReplacementsPerLemmaPerPage
      }, () => {
        setStatus(translate("status_replacement_saved", null, "Replacement settings saved."), colors.SUCCESS);
      });
    }

    return {
      saveDisplaySettings,
      saveReplacementSettings
    };
  }

  root.optionsDisplayReplacement = {
    createController
  };
})();
