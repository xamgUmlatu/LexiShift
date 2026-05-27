(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createSupport(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : { defaults: {} };
    const defaults = settingsManager.defaults || {};
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const sourceLanguageInput = elements.sourceLanguageInput || null;
    const targetLanguageInput = elements.targetLanguageInput || null;

    function currentSourceLanguage() {
      return sourceLanguageInput
        ? (sourceLanguageInput.value || defaults.sourceLanguage || "en")
        : (defaults.sourceLanguage || "en");
    }

    function currentTargetLanguage() {
      return targetLanguageInput
        ? (targetLanguageInput.value || defaults.targetLanguage || "en")
        : (defaults.targetLanguage || "en");
    }

    function parseInterestList(rawValue) {
      const seen = new Set();
      return String(rawValue || "")
        .split(",")
        .map((entry) => entry.trim())
        .filter((entry) => {
          if (!entry || seen.has(entry)) {
            return false;
          }
          seen.add(entry);
          return true;
        });
    }

    function parseOptionalPercent(rawValue) {
      const trimmed = String(rawValue || "").trim();
      if (!trimmed) return null;
      const parsed = Number.parseFloat(trimmed);
      if (!Number.isFinite(parsed)) return null;
      return Math.min(100, Math.max(0, parsed)) / 100;
    }

    function formatOptionalPercentValue(normalizedValue) {
      if (!Number.isFinite(Number(normalizedValue))) return "";
      return String(Math.round(Math.min(1, Math.max(0, Number(normalizedValue))) * 100));
    }

    return {
      currentSourceLanguage,
      currentTargetLanguage,
      formatOptionalPercentValue,
      parseInterestList,
      parseOptionalPercent
    };
  }

  root.optionsSrsProfileRuntimeValues = {
    createSupport
  };
})();
