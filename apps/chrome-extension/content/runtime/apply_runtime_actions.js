(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRunner(options) {
    const opts = options && typeof options === "object" ? options : {};
    const ensureStyle = typeof opts.ensureStyle === "function" ? opts.ensureStyle : null;
    const setFeedbackSoundEnabled = typeof opts.setFeedbackSoundEnabled === "function"
      ? opts.setFeedbackSoundEnabled
      : null;
    const setPopupModulePrefs = typeof opts.setPopupModulePrefs === "function"
      ? opts.setPopupModulePrefs
      : null;
    const attachClickListener = typeof opts.attachClickListener === "function"
      ? opts.attachClickListener
      : null;
    const attachFeedbackListener = typeof opts.attachFeedbackListener === "function"
      ? opts.attachFeedbackListener
      : null;
    const applyHighlightToDom = typeof opts.applyHighlightToDom === "function"
      ? opts.applyHighlightToDom
      : null;
    const clearReplacements = typeof opts.clearReplacements === "function"
      ? opts.clearReplacements
      : null;
    const buildTrie = typeof opts.buildTrie === "function"
      ? opts.buildTrie
      : null;
    const domScanRuntime = opts.domScanRuntime && typeof opts.domScanRuntime === "object"
      ? opts.domScanRuntime
      : null;
    const feedbackRuntime = opts.feedbackRuntime && typeof opts.feedbackRuntime === "object"
      ? opts.feedbackRuntime
      : null;
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const defaults = opts.defaults && typeof opts.defaults === "object"
      ? opts.defaults
      : { highlightColor: "#9AA0A6" };
    const setCurrentTrie = typeof opts.setCurrentTrie === "function"
      ? opts.setCurrentTrie
      : (() => {});
    const setApplyingChanges = typeof opts.setApplyingChanges === "function"
      ? opts.setApplyingChanges
      : (() => {});
    const nowMs = typeof opts.nowMs === "function"
      ? opts.nowMs
      : (() => (
          globalThis.performance && typeof globalThis.performance.now === "function"
            ? globalThis.performance.now()
            : Date.now()
        ));
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    async function run(context) {
      const startedAtMs = nowMs();
      const ctx = context && typeof context === "object" ? context : {};
      const currentSettings = ctx.currentSettings && typeof ctx.currentSettings === "object"
        ? ctx.currentSettings
        : {};
      const activeRules = Array.isArray(ctx.activeRules) ? ctx.activeRules : [];
      const focusWord = String(ctx.focusWord || "");
      let scanSummary = null;
      let processDocumentStartedAtMs = null;

      if (ensureStyle) {
        ensureStyle(
          currentSettings.highlightColor || defaults.highlightColor,
          currentSettings.srsHighlightColor || currentSettings.highlightColor || defaults.highlightColor
        );
      }
      if (setFeedbackSoundEnabled) {
        setFeedbackSoundEnabled(currentSettings.srsSoundEnabled);
      }
      if (setPopupModulePrefs) {
        setPopupModulePrefs(currentSettings.popupModulePrefs, {
          profileId: currentSettings.srsProfileId,
          targetLanguage: currentSettings.targetLanguage,
          languagePair: currentSettings.srsPair,
          uiLanguage: currentSettings.uiLanguage
        });
      }
      if (attachClickListener) {
        attachClickListener();
      }
      if (attachFeedbackListener) {
        const feedbackOrigins = currentSettings.srsFeedbackSrsEnabled === false ? [] : [ruleOriginSrs];
        attachFeedbackListener((payload) => {
          if (feedbackRuntime && typeof feedbackRuntime.handleFeedback === "function") {
            feedbackRuntime.handleFeedback(payload, focusWord);
          }
        }, {
          allowOrigins: feedbackOrigins
        });
      }
      if (applyHighlightToDom) {
        applyHighlightToDom(currentSettings.highlightEnabled);
      }

      setApplyingChanges(true);
      try {
        if (clearReplacements) {
          clearReplacements();
        }
        if (!currentSettings.enabled) {
          if (domScanRuntime && typeof domScanRuntime.clearBudgetState === "function") {
            domScanRuntime.clearBudgetState();
          }
          setCurrentTrie(null);
          log("Replacements are disabled.");
          return;
        }
        const nextTrie = buildTrie ? buildTrie(activeRules) : null;
        setCurrentTrie(nextTrie);
        if (domScanRuntime && typeof domScanRuntime.processDocument === "function") {
          processDocumentStartedAtMs = nowMs();
          scanSummary = await domScanRuntime.processDocument();
        }
      } finally {
        setApplyingChanges(false);
      }

      const runtimeApplyMs = nowMs() - startedAtMs;
      const scanMs = scanSummary && Number.isFinite(Number(scanSummary.scanDurationMs))
        ? Number(scanSummary.scanDurationMs)
        : null;
      const firstReplacementMs = (
        scanSummary
        && Number.isFinite(Number(scanSummary.firstReplacementLatencyMs))
        && Number.isFinite(Number(processDocumentStartedAtMs))
      )
        ? (processDocumentStartedAtMs - startedAtMs) + Number(scanSummary.firstReplacementLatencyMs)
        : null;

      return {
        scanSummary,
        timings: {
          runtimeApplyMs,
          scanMs,
          firstReplacementMs
        }
      };
    }

    return {
      run
    };
  }

  root.contentApplyRuntimeActions = {
    createRunner
  };
})();
