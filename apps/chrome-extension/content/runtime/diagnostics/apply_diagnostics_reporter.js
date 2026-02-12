(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createReporter(options) {
    const opts = options && typeof options === "object" ? options : {};
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const getRuleOrigin = typeof opts.getRuleOrigin === "function"
      ? opts.getRuleOrigin
      : (_rule) => String(opts.ruleOriginRuleset || "ruleset");
    const countRulesWithScriptForms = typeof opts.countRulesWithScriptForms === "function"
      ? opts.countRulesWithScriptForms
      : (_rules) => 0;
    const countRulesWithWordPackage = typeof opts.countRulesWithWordPackage === "function"
      ? opts.countRulesWithWordPackage
      : (_rules) => 0;
    const persistRuntimeState = typeof opts.persistRuntimeState === "function"
      ? opts.persistRuntimeState
      : (_payload) => {};
    const getFrameInfo = typeof opts.getFrameInfo === "function"
      ? opts.getFrameInfo
      : (() => ({ frameType: "top" }));
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const ruleOriginRuleset = String(opts.ruleOriginRuleset || "ruleset");

    function report(context) {
      const state = context && typeof context === "object" ? context : {};
      const currentSettings = state.currentSettings && typeof state.currentSettings === "object"
        ? state.currentSettings
        : {};
      const normalizedRules = Array.isArray(state.normalizedRules) ? state.normalizedRules : [];
      const enabledRules = Array.isArray(state.enabledRules) ? state.enabledRules : [];
      const activeRules = Array.isArray(state.activeRules) ? state.activeRules : [];
      const originCounts = state.originCounts && typeof state.originCounts === "object"
        ? state.originCounts
        : { [ruleOriginRuleset]: 0, [ruleOriginSrs]: 0 };
      const activeOriginCounts = state.activeOriginCounts && typeof state.activeOriginCounts === "object"
        ? state.activeOriginCounts
        : { [ruleOriginRuleset]: 0, [ruleOriginSrs]: 0 };
      const rulesSource = String(state.rulesSource || "local");
      const helperRulesError = state.helperRulesError || null;
      const srsProfileId = String(state.srsProfileId || "default");
      const srsStats = state.srsStats || null;
      const focusWord = String(state.focusWord || "");
      const focusRulesCount = Number(state.focusRulesCount || 0);
      let srsRulesWithScriptForms = 0;
      let activeSrsRulesWithScriptForms = 0;
      let srsRulesWithWordPackage = 0;
      let activeSrsRulesWithWordPackage = 0;

      log("Settings loaded.", {
        enabled: currentSettings.enabled,
        rules: normalizedRules.length,
        enabledRules: enabledRules.length,
        highlightEnabled: currentSettings.highlightEnabled,
        highlightColor: currentSettings.highlightColor,
        maxOnePerTextBlock: currentSettings.maxOnePerTextBlock,
        allowAdjacentReplacements: currentSettings.allowAdjacentReplacements,
        maxReplacementsPerPage: currentSettings.maxReplacementsPerPage,
        maxReplacementsPerLemmaPerPage: currentSettings.maxReplacementsPerLemmaPerPage,
        rulesSource,
        rulesLocalEnabled: originCounts[ruleOriginRuleset],
        rulesSrsEnabled: originCounts[ruleOriginSrs],
        srsEnabled: currentSettings.srsEnabled === true,
        srsPair: currentSettings.srsPair || "",
        targetLanguage: currentSettings.targetLanguage || "",
        targetDisplayScript: currentSettings.targetDisplayScript || "kanji",
        srsProfileId: srsProfileId,
        srsMaxActive: currentSettings.srsMaxActive,
        debugEnabled: currentSettings.debugEnabled,
        debugFocusWord: focusWord || ""
      });
      if (currentSettings.debugEnabled) {
        const srsRulesOnly = enabledRules.filter((rule) => getRuleOrigin(rule) === ruleOriginSrs);
        const activeSrsRules = activeRules.filter((rule) => getRuleOrigin(rule) === ruleOriginSrs);
        srsRulesWithScriptForms = countRulesWithScriptForms(srsRulesOnly);
        activeSrsRulesWithScriptForms = countRulesWithScriptForms(activeSrsRules);
        srsRulesWithWordPackage = countRulesWithWordPackage(srsRulesOnly);
        activeSrsRulesWithWordPackage = countRulesWithWordPackage(activeSrsRules);
        log("SRS script_forms coverage:", {
          rulesSource,
          srsRulesTotal: srsRulesOnly.length,
          srsRulesWithScriptForms,
          srsRulesWithWordPackage,
          activeSrsRulesTotal: activeSrsRules.length,
          activeSrsRulesWithScriptForms,
          activeSrsRulesWithWordPackage
        });
        if (srsRulesOnly.length > 0 && srsRulesWithScriptForms === 0 && srsRulesWithWordPackage === 0) {
          log(
            "SRS rules have no metadata.script_forms or metadata.word_package. Regenerate ruleset with word package metadata."
          );
        }
      }
      if (currentSettings.srsEnabled && currentSettings.debugEnabled) {
        log("SRS selector stats:", srsStats || { total: 0, filtered: 0 });
        log(`SRS rules active: ${activeRules.length}`);
        if (!srsStats || srsStats.datasetLoaded === false) {
          log("SRS dataset not loaded.", srsStats && srsStats.error ? srsStats.error : "");
        } else if (activeRules.length === 0) {
          log("SRS mode active but no matching rules for current dataset/pair.");
        }
      }
      if (currentSettings.srsEnabled && originCounts[ruleOriginSrs] === 0) {
        log(
          "SRS enabled but helper SRS rules are not loaded (rulesSrsEnabled=0). Runtime is local-rules only."
        );
        if (helperRulesError) {
          log("Helper SRS fetch error:", helperRulesError);
        }
      }
      persistRuntimeState({
        ts: new Date().toISOString(),
        pair: currentSettings.srsPair || "",
        profile_id: srsProfileId,
        srs_enabled: currentSettings.srsEnabled === true,
        rules_source: rulesSource,
        rules_enabled_total: enabledRules.length,
        rules_local_enabled: originCounts[ruleOriginRuleset],
        rules_srs_enabled: originCounts[ruleOriginSrs],
        active_rules_total: activeRules.length,
        active_rules_srs: activeOriginCounts[ruleOriginSrs],
        rules_srs_with_script_forms: srsRulesWithScriptForms,
        active_rules_srs_with_script_forms: activeSrsRulesWithScriptForms,
        rules_srs_with_word_package: srsRulesWithWordPackage,
        active_rules_srs_with_word_package: activeSrsRulesWithWordPackage,
        srs_stats: srsStats || null,
        helper_rules_error: helperRulesError || "",
        page_url: window.location ? window.location.href : "",
        frame_type: getFrameInfo().frameType
      });
      if (currentSettings.debugEnabled) {
        log("Context info:", Object.assign({ readyState: document.readyState }, getFrameInfo()));
        if (document.body) {
          log("Body info:", {
            childElements: document.body.childElementCount,
            textLength: document.body.innerText ? document.body.innerText.length : 0
          });
        }
      }
      if (!normalizedRules.length) {
        log("No rules loaded.");
      }
      if (focusWord && focusRulesCount === 0) {
        log(`No enabled rule found for focus word "${focusWord}".`);
      }
    }

    return {
      report
    };
  }

  root.contentApplyDiagnosticsReporter = {
    createReporter
  };
})();
