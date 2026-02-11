(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const defaults = root.defaults || {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    maxReplacementsPerPage: 0,
    maxReplacementsPerLemmaPerPage: 0,
    debugEnabled: false,
    debugFocusWord: "",
    sourceLanguage: "en",
    targetLanguage: "en",
    targetDisplayScript: "kanji",
    srsFeedbackSrsEnabled: true,
    srsFeedbackRulesEnabled: false,
    srsExposureLoggingEnabled: true,
    srsProfileId: "default",
    srsRulesetUpdatedAt: ""
  };

  if (!root.tokenizer || !root.matcher || !root.replacements || !root.ui || !root.utils) {
    console.warn("[LexiShift] Content modules not loaded.");
    return;
  }

  const { textHasToken } = root.tokenizer;
  const { buildTrie, normalizeRules } = root.matcher;
  const { buildReplacementFragment } = root.replacements;
  const {
    ensureStyle,
    applyHighlightToDom,
    clearReplacements,
    attachClickListener,
    attachFeedbackListener,
    setDebugEnabled,
    setFeedbackSoundEnabled
  } = root.ui;
  const { describeElement, shorten, describeCodepoints, countOccurrences, collectTextNodes } = root.utils;
  const srsGate = root.srsGate;
  const srsFeedback = root.srsFeedback;
  const lemmatizer = root.lemmatizer;
  const srsMetrics = root.srsMetrics;
  const HelperClient = root.helperClient;
  const helperFeedbackSyncModule = root.helperFeedbackSync;
  const helperTransport = root.helperTransportExtension;
  const helperCache = root.helperCache;
  const runtimeDiagnostics = root.srsRuntimeDiagnostics;
  const RULE_ORIGIN_SRS = "srs";
  const RULE_ORIGIN_RULESET = "ruleset";

  let processedNodes = new WeakMap();
  let currentSettings = { ...defaults };
  let currentTrie = null;
  let applyingChanges = false;
  let applyToken = 0;
  let helperClient = HelperClient && helperTransport ? new HelperClient(helperTransport) : null;

  function normalizeProfileId(value) {
    const normalized = String(value || "").trim();
    return normalized || "default";
  }

  function normalizeRuleOrigin(origin) {
    return String(origin || "").toLowerCase() === RULE_ORIGIN_SRS
      ? RULE_ORIGIN_SRS
      : RULE_ORIGIN_RULESET;
  }

  function getRuleOrigin(rule) {
    return normalizeRuleOrigin(rule && rule.metadata ? rule.metadata.lexishift_origin : "");
  }

  function tagRulesWithOrigin(rules, origin) {
    const taggedOrigin = normalizeRuleOrigin(origin);
    if (!Array.isArray(rules) || !rules.length) {
      return [];
    }
    return rules.map((rule) => {
      const source = rule && typeof rule === "object" ? rule : {};
      const metadata = source.metadata && typeof source.metadata === "object" ? source.metadata : null;
      return {
        ...source,
        metadata: {
          ...(metadata || {}),
          lexishift_origin: taggedOrigin
        }
      };
    });
  }

  function persistRuntimeState(payload) {
    if (!isTopFrameWindow()) {
      return;
    }
    if (!runtimeDiagnostics || typeof runtimeDiagnostics.saveLastState !== "function") {
      return;
    }
    runtimeDiagnostics.saveLastState(payload).catch(() => {});
  }

  function log(...args) {
    if (!currentSettings.debugEnabled) {
      return;
    }
    console.log("[LexiShift]", ...args);
  }

  function getFrameInfo() {
    let frameType = "top";
    try {
      if (window.top && window.top !== window) {
        frameType = "iframe";
      }
    } catch (error) {
      frameType = "iframe";
    }
    let topHref = "";
    try {
      topHref = window.top ? window.top.location.href : "";
    } catch (error) {
      topHref = "[cross-origin]";
    }
    return {
      frameType,
      href: window.location ? window.location.href : "",
      topHref
    };
  }

  function isTopFrameWindow() {
    try {
      return window.top === window;
    } catch (_error) {
      return false;
    }
  }

  function getFocusWord(settings) {
    const raw = settings && settings.debugFocusWord ? String(settings.debugFocusWord).trim() : "";
    return raw ? raw.toLowerCase() : "";
  }

  function getFocusInfo(text, focusWord) {
    if (!focusWord || !text) {
      return { substring: false, token: false, index: -1 };
    }
    const lower = text.toLowerCase();
    const index = lower.indexOf(focusWord);
    if (index === -1) {
      return { substring: false, token: false, index: -1 };
    }
    return { substring: true, token: textHasToken(text, focusWord), index };
  }

  const domScanRuntimeFactory = root.contentDomScanRuntime
    && typeof root.contentDomScanRuntime.createRuntime === "function"
    ? root.contentDomScanRuntime.createRuntime
    : null;
  const domScanRuntime = domScanRuntimeFactory
    ? domScanRuntimeFactory({
        getCurrentSettings: () => currentSettings,
        getCurrentTrie: () => currentTrie,
        getProcessedNodes: () => processedNodes,
        setProcessedNodes: (next) => {
          processedNodes = next;
        },
        isApplyingChanges: () => applyingChanges === true,
        getFocusWord,
        getFocusInfo,
        normalizeRuleOrigin,
        buildReplacementFragment,
        describeElement,
        shorten,
        describeCodepoints,
        countOccurrences,
        collectTextNodes,
        srsMetrics,
        lemmatizer,
        log
      })
    : {
        processDocument: () => {},
        observeChanges: () => {},
        rescanDocument: () => {},
        ensureObserver: () => {},
        clearBudgetState: () => {},
        disconnect: () => {}
      };
  const helperRulesRuntimeFactory = root.contentHelperRulesRuntime
    && typeof root.contentHelperRulesRuntime.createRuntime === "function"
    ? root.contentHelperRulesRuntime.createRuntime
    : null;
  const helperRulesRuntime = helperRulesRuntimeFactory
    ? helperRulesRuntimeFactory({
        getHelperClient: () => helperClient,
        helperCache,
        normalizeProfileId,
        tagRulesWithOrigin,
        ruleOriginSrs: RULE_ORIGIN_SRS
      })
    : {
        resolveHelperRules: async () => ({ rules: [], source: "none", error: null })
      };
  const activeRulesRuntimeFactory = root.contentActiveRulesRuntime
    && typeof root.contentActiveRulesRuntime.createRuntime === "function"
    ? root.contentActiveRulesRuntime.createRuntime
    : null;
  const activeRulesRuntime = activeRulesRuntimeFactory
    ? activeRulesRuntimeFactory({
        normalizeRules,
        tagRulesWithOrigin,
        normalizeProfileId,
        helperRulesRuntime,
        srsGate,
        getRuleOrigin,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        ruleOriginRuleset: RULE_ORIGIN_RULESET
      })
    : {
        resolveActiveRules: async (settings) => {
          const nextSettings = settings && typeof settings === "object" ? settings : {};
          const normalizedRules = normalizeRules(tagRulesWithOrigin(nextSettings.rules, RULE_ORIGIN_RULESET));
          const enabledRules = normalizedRules.filter((rule) => rule.enabled !== false);
          const originCounts = {
            [RULE_ORIGIN_RULESET]: 0,
            [RULE_ORIGIN_SRS]: 0
          };
          for (const rule of enabledRules) {
            const origin = getRuleOrigin(rule);
            originCounts[origin] = Number(originCounts[origin] || 0) + 1;
          }
          return {
            srsProfileId: normalizeProfileId(nextSettings.srsProfileId),
            rulesSource: "local",
            helperRulesError: null,
            normalizedRules,
            enabledRules,
            originCounts,
            activeRules: enabledRules,
            activeOriginCounts: { ...originCounts },
            srsActiveLemmas: null,
            srsStats: null
          };
        },
        countRulesWithScriptForms: () => 0
      };
  const applyDiagnosticsReporterFactory = root.contentApplyDiagnosticsReporter
    && typeof root.contentApplyDiagnosticsReporter.createReporter === "function"
    ? root.contentApplyDiagnosticsReporter.createReporter
    : null;
  const applyDiagnosticsReporter = applyDiagnosticsReporterFactory
    ? applyDiagnosticsReporterFactory({
        log,
        getRuleOrigin,
        countRulesWithScriptForms: (rules) => activeRulesRuntime.countRulesWithScriptForms(rules),
        persistRuntimeState,
        getFrameInfo,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        ruleOriginRuleset: RULE_ORIGIN_RULESET
      })
    : {
        report: () => {}
      };
  const feedbackRuntimeFactory = root.contentFeedbackRuntimeController
    && typeof root.contentFeedbackRuntimeController.createController === "function"
    ? root.contentFeedbackRuntimeController.createController
    : null;
  const feedbackRuntime = feedbackRuntimeFactory
    ? feedbackRuntimeFactory({
        srsFeedback,
        lemmatizer,
        helperFeedbackSyncModule,
        getHelperClient: () => helperClient,
        getCurrentSettings: () => currentSettings,
        normalizeProfileId,
        normalizeRuleOrigin,
        isTopFrameWindow,
        log,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        ruleOriginRuleset: RULE_ORIGIN_RULESET
      })
    : {
        ensureSync: () => null,
        handleFeedback: () => {},
        stop: () => {}
      };
  const applyRuntimeActionsFactory = root.contentApplyRuntimeActions
    && typeof root.contentApplyRuntimeActions.createRunner === "function"
    ? root.contentApplyRuntimeActions.createRunner
    : null;
  const applyRuntimeActions = applyRuntimeActionsFactory
    ? applyRuntimeActionsFactory({
        ensureStyle,
        setFeedbackSoundEnabled,
        attachClickListener,
        attachFeedbackListener,
        applyHighlightToDom,
        clearReplacements,
        buildTrie,
        domScanRuntime,
        feedbackRuntime,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        defaults,
        setCurrentTrie: (nextTrie) => {
          currentTrie = nextTrie;
        },
        setApplyingChanges: (next) => {
          applyingChanges = next === true;
        },
        log
      })
    : {
        run: () => {}
      };
  const applySettingsPipelineFactory = root.contentApplySettingsPipeline
    && typeof root.contentApplySettingsPipeline.createPipeline === "function"
    ? root.contentApplySettingsPipeline.createPipeline
    : null;
  const applySettingsPipeline = applySettingsPipelineFactory
    ? applySettingsPipelineFactory({
        defaults,
        applyLanguagePrefs: (nextSettings) => {
          if (root.languagePrefs && typeof root.languagePrefs.applyLanguagePrefs === "function") {
            return root.languagePrefs.applyLanguagePrefs(nextSettings);
          }
          return nextSettings;
        },
        setDebugEnabled,
        setCurrentSettings: (nextSettings) => {
          currentSettings = nextSettings && typeof nextSettings === "object"
            ? nextSettings
            : currentSettings;
        },
        resetProcessedNodes: () => {
          processedNodes = new WeakMap();
        },
        activeRulesRuntime,
        getHelperClientAvailable: () => Boolean(helperClient),
        getFocusWord,
        applyDiagnosticsReporter,
        applyRuntimeActions,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        ruleOriginRuleset: RULE_ORIGIN_RULESET
      })
    : {
        run: async () => ({ stale: false })
      };
  const settingsChangeRouterFactory = root.contentSettingsChangeRouter
    && typeof root.contentSettingsChangeRouter.createRouter === "function"
    ? root.contentSettingsChangeRouter.createRouter
    : null;
  const settingsChangeRouter = settingsChangeRouterFactory
    ? settingsChangeRouterFactory({
        defaults,
        ruleOriginSrs: RULE_ORIGIN_SRS,
        getCurrentSettings: () => currentSettings,
        setCurrentSettings: (next) => {
          currentSettings = next && typeof next === "object" ? { ...next } : currentSettings;
        },
        getFocusWord,
        log,
        setDebugEnabled,
        setFeedbackSoundEnabled,
        ensureStyle,
        applyHighlightToDom,
        attachFeedbackListener,
        onFeedback: (payload, focusWord) => {
          feedbackRuntime.handleFeedback(payload, focusWord);
        },
        applySettings: (nextSettings) => {
          applySettings(nextSettings);
        }
      })
    : {
        handleStorageChange: () => {}
      };

  async function applySettings(settings) {
    const token = (applyToken += 1);
    await applySettingsPipeline.run(settings, {
      isTokenCurrent: () => token === applyToken,
      log
    });
  }

  function loadSettings() {
    return new Promise((resolve) => {
      chrome.storage.local.get(defaults, (items) => resolve(items));
    });
  }

  async function boot() {
    feedbackRuntime.ensureSync();
    const settings = await loadSettings();
    await applySettings(settings);
    domScanRuntime.observeChanges();
    window.addEventListener("load", () => {
      domScanRuntime.ensureObserver();
      domScanRuntime.rescanDocument("window load");
    });
    setTimeout(() => {
      domScanRuntime.ensureObserver();
      domScanRuntime.rescanDocument("post-load timeout");
    }, 1500);
    window.addEventListener("beforeunload", () => {
      feedbackRuntime.stop();
      domScanRuntime.disconnect();
    });
  }

  boot();

  chrome.storage.onChanged.addListener((changes, area) => {
    settingsChangeRouter.handleStorageChange(changes, area);
  });
})();
