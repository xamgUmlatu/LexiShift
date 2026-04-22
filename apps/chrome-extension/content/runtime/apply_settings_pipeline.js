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
    const nowMs = typeof opts.nowMs === "function"
      ? opts.nowMs
      : (() => (
          globalThis.performance && typeof globalThis.performance.now === "function"
            ? globalThis.performance.now()
            : Date.now()
        ));
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
      const pipelineStartedAtMs = nowMs();
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

      const activeRulesResolveStartedAtMs = nowMs();
      const activeRulesState = activeRulesRuntime && typeof activeRulesRuntime.resolveActiveRules === "function"
        ? await activeRulesRuntime.resolveActiveRules(
            nextSettings,
            nextSettings.debugEnabled ? runtimeContext.log : null,
            { helperAvailable: getHelperClientAvailable() }
          )
        : null;
      const activeRulesResolveMs = nowMs() - activeRulesResolveStartedAtMs;
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
      const semanticAdmissionEnabled = activeRulesState && activeRulesState.semanticAdmissionEnabled === true;
      const semanticFallbackPolicy = activeRulesState && activeRulesState.semanticFallbackPolicy
        ? activeRulesState.semanticFallbackPolicy
        : "legacy_on_unavailable";
      const semanticRuntimeCapability = activeRulesState && activeRulesState.semanticRuntimeCapability
        ? activeRulesState.semanticRuntimeCapability
        : "unavailable";
      const semanticRuntimeReasonCode = activeRulesState && activeRulesState.semanticRuntimeReasonCode
        ? activeRulesState.semanticRuntimeReasonCode
        : "no_semantic_rules";
      const semanticPointerRuleCount = activeRulesState
        && Number.isFinite(Number(activeRulesState.semanticPointerRuleCount))
        ? Number(activeRulesState.semanticPointerRuleCount)
        : 0;
      const semanticReadyRuleCount = activeRulesState
        && Number.isFinite(Number(activeRulesState.semanticReadyRuleCount))
        ? Number(activeRulesState.semanticReadyRuleCount)
        : 0;
      const semanticInventoryLoaded = activeRulesState && activeRulesState.semanticInventoryLoaded === true;
      const semanticInventorySource = activeRulesState && activeRulesState.semanticInventorySource
        ? activeRulesState.semanticInventorySource
        : "none";
      const semanticInventoryError = activeRulesState && activeRulesState.semanticInventoryError
        ? activeRulesState.semanticInventoryError
        : null;
      nextSettings.srsSemanticAdmissionEnabled = semanticAdmissionEnabled;
      nextSettings.srsSemanticAdmissionFallbackPolicy = semanticFallbackPolicy;
      nextSettings.semanticRuntimeCapability = semanticRuntimeCapability;
      nextSettings.semanticRuntimeReasonCode = semanticRuntimeReasonCode;
      setCurrentSettings(nextSettings);

      if (!isTokenCurrent()) {
        return { stale: true };
      }

      const focusWord = getFocusWord(nextSettings);
      const focusRulesCount = focusWord
        ? enabledRules.filter((rule) => String(rule.source_phrase || "").toLowerCase() === focusWord).length
        : 0;
      let runtimeApplyResult = null;
      let runtimeApplyStartedAtMs = null;
      if (applyRuntimeActions && typeof applyRuntimeActions.run === "function") {
        runtimeApplyStartedAtMs = nowMs();
        runtimeApplyResult = await applyRuntimeActions.run({
          currentSettings: nextSettings,
          activeRules,
          focusWord
        });
      }

      if (!isTokenCurrent()) {
        return { stale: true };
      }

      if (applyDiagnosticsReporter && typeof applyDiagnosticsReporter.report === "function") {
        const activeRulesTimings = (
          activeRulesState
          && activeRulesState.timings
          && typeof activeRulesState.timings === "object"
        )
          ? activeRulesState.timings
          : null;
        const runtimeApplyTimings = (
          runtimeApplyResult
          && runtimeApplyResult.timings
          && typeof runtimeApplyResult.timings === "object"
        )
          ? runtimeApplyResult.timings
          : null;
        const firstReplacementLatencyMs = (
          runtimeApplyTimings
          && Number.isFinite(Number(runtimeApplyTimings.firstReplacementMs))
          && Number.isFinite(Number(runtimeApplyStartedAtMs))
        )
          ? (runtimeApplyStartedAtMs - pipelineStartedAtMs) + Number(runtimeApplyTimings.firstReplacementMs)
          : null;
        const firstVisibleReplacementLatencyMs = (
          runtimeApplyTimings
          && Number.isFinite(Number(runtimeApplyTimings.firstVisibleReplacementMs))
          && Number.isFinite(Number(runtimeApplyStartedAtMs))
        )
          ? (runtimeApplyStartedAtMs - pipelineStartedAtMs) + Number(runtimeApplyTimings.firstVisibleReplacementMs)
          : null;
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
          focusRulesCount,
          semanticAdmissionEnabled,
          semanticFallbackPolicy,
          semanticRuntimeCapability,
          semanticRuntimeReasonCode,
          semanticPointerRuleCount,
          semanticReadyRuleCount,
          semanticInventoryLoaded,
          semanticInventorySource,
          semanticInventoryError,
          timings: {
            applyTotalMs: nowMs() - pipelineStartedAtMs,
            activeRulesResolveMs,
            helperRulesResolveMs: activeRulesTimings ? activeRulesTimings.helperRulesResolveMs : null,
            srsGateMs: activeRulesTimings ? activeRulesTimings.srsGateMs : null,
            semanticInventoryResolveMs: activeRulesTimings
              ? activeRulesTimings.semanticInventoryResolveMs
              : null,
            runtimeApplyMs: runtimeApplyTimings ? runtimeApplyTimings.runtimeApplyMs : null,
            scanMs: runtimeApplyTimings ? runtimeApplyTimings.scanMs : null,
            firstReplacementLatencyMs,
            firstVisibleReplacementLatencyMs
          },
          scanSummary: runtimeApplyResult && runtimeApplyResult.scanSummary
            ? runtimeApplyResult.scanSummary
            : null
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
