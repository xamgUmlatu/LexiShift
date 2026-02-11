(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createAdapter(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : { defaults: {} };
    const sourceLanguageInput = opts.sourceLanguageInput || null;
    const targetLanguageInput = opts.targetLanguageInput || null;
    const jaPrimaryDisplayScriptInput = opts.jaPrimaryDisplayScriptInput || null;
    const updateTargetLanguagePrefsModalVisibility = typeof opts.updateTargetLanguagePrefsModalVisibility === "function"
      ? opts.updateTargetLanguagePrefsModalVisibility
      : (() => {});

    function resolveCurrentTargetLanguage() {
      return targetLanguageInput
        ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
        : (settingsManager.defaults.targetLanguage || "en");
    }

    function normalizePrimaryDisplayScript(value) {
      const allowed = new Set(["kanji", "kana", "romaji"]);
      const candidate = String(value || "").trim().toLowerCase();
      if (allowed.has(candidate)) {
        return candidate;
      }
      return "kanji";
    }

    function resolveTargetScriptPrefs(languagePrefs) {
      const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
      const rawTargetScriptPrefs = prefs.targetScriptPrefs && typeof prefs.targetScriptPrefs === "object"
        ? prefs.targetScriptPrefs
        : {};
      const rawJaPrefs = rawTargetScriptPrefs.ja && typeof rawTargetScriptPrefs.ja === "object"
        ? rawTargetScriptPrefs.ja
        : {};
      return {
        ja: {
          primaryDisplayScript: normalizePrimaryDisplayScript(rawJaPrefs.primaryDisplayScript)
        }
      };
    }

    function resolvePairFromInputs() {
      const sourceLanguage = sourceLanguageInput
        ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
        : (settingsManager.defaults.sourceLanguage || "en");
      const targetLanguage = targetLanguageInput
        ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
        : (settingsManager.defaults.targetLanguage || "en");
      const prefs = globalThis.LexiShift && globalThis.LexiShift.languagePrefs;
      if (prefs && typeof prefs.resolveLanguagePair === "function") {
        return prefs.resolveLanguagePair({
          sourceLanguage,
          targetLanguage,
          srsPairAuto: true,
          srsPair: settingsManager.defaults.srsPair || "en-en"
        });
      }
      return `${sourceLanguage}-${targetLanguage}`;
    }

    function applyLanguagePrefsToInputs(languagePrefs) {
      const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
      const sourceLanguage = String(prefs.sourceLanguage || settingsManager.defaults.sourceLanguage || "en");
      const targetLanguage = String(prefs.targetLanguage || settingsManager.defaults.targetLanguage || "en");
      const targetScriptPrefs = resolveTargetScriptPrefs(prefs);
      if (sourceLanguageInput) {
        sourceLanguageInput.value = sourceLanguage;
      }
      if (targetLanguageInput) {
        targetLanguageInput.value = targetLanguage;
      }
      if (jaPrimaryDisplayScriptInput) {
        jaPrimaryDisplayScriptInput.value = targetScriptPrefs.ja.primaryDisplayScript;
      }
      updateTargetLanguagePrefsModalVisibility(targetLanguage);
      const pair = String(prefs.srsPair || "").trim();
      return pair || resolvePairFromInputs();
    }

    return {
      resolveCurrentTargetLanguage,
      normalizePrimaryDisplayScript,
      resolveTargetScriptPrefs,
      resolvePairFromInputs,
      applyLanguagePrefsToInputs
    };
  }

  root.optionsLanguagePrefsAdapter = {
    createAdapter
  };
})();
