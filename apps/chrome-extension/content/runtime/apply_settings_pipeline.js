(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createPipeline(options) {
    const opts = options && typeof options === "object" ? options : {};
    const defaults = opts.defaults && typeof opts.defaults === "object" ? opts.defaults : {};
    const applyLanguagePrefs = typeof opts.applyLanguagePrefs === "function"
      ? opts.applyLanguagePrefs
      : ((settings) => settings);
    const setDebugEnabled = typeof opts.setDebugEnabled === "function"
      ? opts.setDebugEnabled
      : null;
    const setCurrentSettings = typeof opts.setCurrentSettings === "function"
      ? opts.setCurrentSettings
      : (() => {});
    const resetProcessedNodes = typeof opts.resetProcessedNodes === "function"
      ? opts.resetProcessedNodes
      : (() => {});
    const activeRulesRuntime = opts.activeRulesRuntime && typeof opts.activeRulesRuntime === "object"
      ? opts.activeRulesRuntime
      : null;
    const getHelperClientAvailable = typeof opts.getHelperClientAvailable === "function"
      ? opts.getHelperClientAvailable
      : (() => false);
    const getFocusWord = typeof opts.getFocusWord === "function"
      ? opts.getFocusWord
      : ((_settings) => "");
    const applyDiagnosticsReporter = opts.applyDiagnosticsReporter && typeof opts.applyDiagnosticsReporter === "object"
      ? opts.applyDiagnosticsReporter
      : null;
    const applyRuntimeActions = opts.applyRuntimeActions && typeof opts.applyRuntimeActions === "object"
      ? opts.applyRuntimeActions
      : null;
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const ruleOriginRuleset = String(opts.ruleOriginRuleset || "ruleset");

    function normalizeOriginCounts(value) {
      const counts = value && typeof value === "object" ? value : {};
      return {
        [ruleOriginRuleset]: Number(counts[ruleOriginRuleset] || 0),
        [ruleOriginSrs]: Number(counts[ruleOriginSrs] || 0)
      };
    }

    async function run(settings, context) {
      const rawSettings = settings && typeof settings === "object" ? settings : {};
      const runtimeContext = context && typeof context === "object" ? context : {};
      const isTokenCurrent = typeof runtimeContext.isTokenCurrent === "function"
        ? runtimeContext.isTokenCurrent
        : (() => true);

      let nextSettings = { ...defaults, ...rawSettings };
      nextSettings = applyLanguagePrefs(nextSettings);
      if (setDebugEnabled) {
        setDebugEnabled(nextSettings.debugEnabled === true);
      }
      const hasNewFeedbackFlags = typeof rawSettings.srsFeedbackSrsEnabled === "boolean"
        || typeof rawSettings.srsFeedbackRulesEnabled === "boolean";
      if (!hasNewFeedbackFlags && typeof rawSettings.srsFeedbackEnabled === "boolean") {
        nextSettings.srsFeedbackSrsEnabled = true;
        nextSettings.srsFeedbackRulesEnabled = !rawSettings.srsFeedbackEnabled;
      }
      setCurrentSettings(nextSettings);
      resetProcessedNodes();

      const activeRulesState = activeRulesRuntime && typeof activeRulesRuntime.resolveActiveRules === "function"
        ? await activeRulesRuntime.resolveActiveRules(
            nextSettings,
            nextSettings.debugEnabled ? runtimeContext.log : null,
            { helperAvailable: getHelperClientAvailable() }
          )
        : null;
      const srsProfileId = activeRulesState && activeRulesState.srsProfileId
        ? activeRulesState.srsProfileId
        : String(nextSettings.srsProfileId || "default");
      const rulesSource = activeRulesState && activeRulesState.rulesSource
        ? activeRulesState.rulesSource
        : "local";
      const helperRulesError = activeRulesState && activeRulesState.helperRulesError
        ? activeRulesState.helperRulesError
        : null;
      const normalizedRules = activeRulesState && Array.isArray(activeRulesState.normalizedRules)
        ? activeRulesState.normalizedRules
        : [];
      const enabledRules = activeRulesState && Array.isArray(activeRulesState.enabledRules)
        ? activeRulesState.enabledRules
        : [];
      const originCounts = normalizeOriginCounts(activeRulesState && activeRulesState.originCounts);
      const activeRules = activeRulesState && Array.isArray(activeRulesState.activeRules)
        ? activeRulesState.activeRules
        : enabledRules;
      nextSettings._srsActiveLemmas = activeRulesState && activeRulesState.srsActiveLemmas
        ? activeRulesState.srsActiveLemmas
        : null;
      const srsStats = activeRulesState && activeRulesState.srsStats
        ? activeRulesState.srsStats
        : null;
      const activeOriginCounts = normalizeOriginCounts(activeRulesState && activeRulesState.activeOriginCounts);

      if (!isTokenCurrent()) {
        return { stale: true };
      }

      const focusWord = getFocusWord(nextSettings);
      const focusRulesCount = focusWord
        ? enabledRules.filter((rule) => String(rule.source_phrase || "").toLowerCase() === focusWord).length
        : 0;
      if (applyDiagnosticsReporter && typeof applyDiagnosticsReporter.report === "function") {
        applyDiagnosticsReporter.report({
          currentSettings: nextSettings,
          normalizedRules,
          enabledRules,
          activeRules,
          originCounts,
          activeOriginCounts,
          rulesSource,
          helperRulesError,
          srsProfileId,
          srsStats,
          focusWord,
          focusRulesCount
        });
      }
      if (applyRuntimeActions && typeof applyRuntimeActions.run === "function") {
        applyRuntimeActions.run({
          currentSettings: nextSettings,
          activeRules,
          focusWord
        });
      }

      return {
        stale: false
      };
    }

    return {
      run
    };
  }

  root.contentApplySettingsPipeline = {
    createPipeline
  };
})();
