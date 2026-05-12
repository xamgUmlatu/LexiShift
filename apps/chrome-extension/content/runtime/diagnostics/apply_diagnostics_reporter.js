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

    function normalizeRate(numerator, denominator) {
      return Number(denominator) > 0
        ? Number(numerator) / Number(denominator)
        : null;
    }

    function isFiniteMetric(value) {
      return value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
    }

    function buildSemanticDecisionMetrics(scanSummary) {
      const summary = scanSummary && typeof scanSummary === "object" ? scanSummary : {};
      const policyDecisionTotal = (
        Number(summary.semanticPolicyReplaces || 0)
        + Number(summary.semanticPolicyAbstains || 0)
        + Number(summary.semanticPolicySoftAffordances || 0)
      );
      const fallbackDecisionTotal = (
        Number(summary.semanticFallbackReplaces || 0)
        + Number(summary.semanticFallbackAbstains || 0)
        + Number(summary.semanticFallbackSoftAffordances || 0)
      );
      const overallDecisionTotal = Number(summary.semanticEligible || 0);
      return {
        policyDecisionTotal,
        fallbackDecisionTotal,
        overallDecisionTotal,
        policyAbstainRate: normalizeRate(summary.semanticPolicyAbstains || 0, policyDecisionTotal),
        fallbackAbstainRate: normalizeRate(summary.semanticFallbackAbstains || 0, fallbackDecisionTotal),
        overallAbstainRate: normalizeRate(
          Number(summary.semanticPolicyAbstains || 0) + Number(summary.semanticFallbackAbstains || 0),
          overallDecisionTotal
        )
      };
    }

    function buildSemanticPerformanceMetrics(scanSummary) {
      const summary = scanSummary && typeof scanSummary === "object" ? scanSummary : {};
      const contextStats = summary.semanticContextCacheStats
        && typeof summary.semanticContextCacheStats === "object"
        ? summary.semanticContextCacheStats
        : {};
      const inventoryLookupCalls = Number(summary.semanticInventoryLookupCalls || 0);
      const helperBatchCalls = Number(summary.semanticHelperBatchCalls || 0);
      const helperRequestCount = Number(summary.semanticHelperRequestCount || 0);
      return {
        inventoryLookupCalls,
        inventoryLookupLatencyMsTotal: Number(summary.semanticInventoryLookupLatencyMsTotal || 0),
        inventoryLookupLatencyMsMax: Number(summary.semanticInventoryLookupLatencyMsMax || 0),
        inventoryLookupLatencyMsAvg: normalizeRate(
          summary.semanticInventoryLookupLatencyMsTotal || 0,
          inventoryLookupCalls
        ),
        helperBatchCalls,
        helperRequestCount,
        helperBatchMinSize: isFiniteMetric(summary.semanticHelperBatchMinSize)
          ? Number(summary.semanticHelperBatchMinSize)
          : null,
        helperBatchMaxSize: Number(summary.semanticHelperBatchMaxSize || 0),
        helperBatchAvgSize: normalizeRate(helperRequestCount, helperBatchCalls),
        helperLatencyMsTotal: Number(summary.semanticHelperLatencyMsTotal || 0),
        helperLatencyMsMax: Number(summary.semanticHelperLatencyMsMax || 0),
        helperLatencyMsAvg: normalizeRate(summary.semanticHelperLatencyMsTotal || 0, helperBatchCalls),
        scanNodeBatchCalls: Number(summary.semanticScanNodeBatchCalls || 0),
        scanNodeCount: Number(summary.semanticScanNodeCount || 0),
        scanNodeBatchMinSize: isFiniteMetric(summary.semanticScanNodeBatchMinSize)
          ? Number(summary.semanticScanNodeBatchMinSize)
          : null,
        scanNodeBatchMaxSize: Number(summary.semanticScanNodeBatchMaxSize || 0),
        scanNodeBatchAvgSize: normalizeRate(
          summary.semanticScanNodeCount || 0,
          summary.semanticScanNodeBatchCalls || 0
        ),
        scanNodeConcurrentBatches: Number(summary.semanticScanNodeConcurrentBatches || 0),
        scanNodeSerialBatches: Number(summary.semanticScanNodeSerialBatches || 0),
        scanNodeSerialBudgetBatches: Number(summary.semanticScanNodeSerialBudgetBatches || 0),
        contextCacheContainerBuilds: Number(contextStats.containerBuilds || 0),
        contextCacheRecordReuses: Number(contextStats.recordReuses || 0),
        contextCacheUsableReuses: Number(contextStats.usableReuses || 0),
        contextCacheBypasses: Number(contextStats.bypasses || 0)
      };
    }

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
      const semanticAdmissionEnabled = state.semanticAdmissionEnabled === true;
      const semanticFallbackPolicy = String(state.semanticFallbackPolicy || "legacy_on_unavailable");
      const semanticRuntimeCapability = String(state.semanticRuntimeCapability || "unavailable");
      const semanticRuntimeReasonCode = String(state.semanticRuntimeReasonCode || "no_semantic_rules");
      const semanticPointerRuleCount = Number.isFinite(Number(state.semanticPointerRuleCount))
        ? Number(state.semanticPointerRuleCount)
        : 0;
      const semanticReadyRuleCount = Number.isFinite(Number(state.semanticReadyRuleCount))
        ? Number(state.semanticReadyRuleCount)
        : 0;
      const semanticInventoryLoaded = state.semanticInventoryLoaded === true;
      const semanticInventorySource = String(state.semanticInventorySource || "none");
      const semanticInventoryError = state.semanticInventoryError || null;
      const timings = state.timings && typeof state.timings === "object"
        ? state.timings
        : {};
      const normalizeTiming = (value) => Number.isFinite(Number(value))
        ? Number(value)
        : null;
      const applyTotalMs = normalizeTiming(timings.applyTotalMs);
      const activeRulesResolveMs = normalizeTiming(timings.activeRulesResolveMs);
      const helperRulesResolveMs = normalizeTiming(timings.helperRulesResolveMs);
      const srsGateMs = normalizeTiming(timings.srsGateMs);
      const semanticInventoryResolveMs = normalizeTiming(timings.semanticInventoryResolveMs);
      const runtimeApplyMs = normalizeTiming(timings.runtimeApplyMs);
      const scanMs = normalizeTiming(timings.scanMs);
      const firstReplacementLatencyMs = normalizeTiming(timings.firstReplacementLatencyMs);
      const firstVisibleReplacementLatencyMs = normalizeTiming(timings.firstVisibleReplacementLatencyMs);
      const scanSummary = state.scanSummary && typeof state.scanSummary === "object"
        ? state.scanSummary
        : null;
      const semanticDecisionMetrics = buildSemanticDecisionMetrics(scanSummary);
      const semanticPerformanceMetrics = buildSemanticPerformanceMetrics(scanSummary);
      let srsRulesWithScriptForms = 0;
      let activeSrsRulesWithScriptForms = 0;
      let srsRulesWithWordPackage = 0;
      let activeSrsRulesWithWordPackage = 0;

      if (currentSettings.debugEnabled) {
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
          semanticAdmissionEnabled,
          semanticRuntimeCapability,
          semanticRuntimeReasonCode,
          semanticPointerRuleCount,
          semanticReadyRuleCount,
          semanticFallbackPolicy,
          debugEnabled: currentSettings.debugEnabled,
          debugFocusWord: focusWord || ""
        });
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
      if (currentSettings.debugEnabled && currentSettings.srsEnabled && originCounts[ruleOriginSrs] === 0) {
        log(
          "SRS enabled but helper SRS rules are not loaded (rulesSrsEnabled=0). Runtime is local-rules only."
        );
        if (helperRulesError) {
          log("Helper SRS fetch error:", helperRulesError);
        }
      }
      if (currentSettings.debugEnabled && semanticAdmissionEnabled) {
        log("Semantic admission runtime:", {
          capability: semanticRuntimeCapability,
          reasonCode: semanticRuntimeReasonCode,
          pointerRuleCount: semanticPointerRuleCount,
          readyRuleCount: semanticReadyRuleCount,
          fallbackPolicy: semanticFallbackPolicy,
          inventoryLoaded: semanticInventoryLoaded,
          inventorySource: semanticInventorySource,
          inventoryError: semanticInventoryError || ""
        });
      } else if (currentSettings.debugEnabled && currentSettings.srsEnabled && semanticPointerRuleCount > 0) {
        log("Semantic admission capability:", {
          capability: semanticRuntimeCapability,
          reasonCode: semanticRuntimeReasonCode,
          pointerRuleCount: semanticPointerRuleCount,
          readyRuleCount: semanticReadyRuleCount
        });
      }
      if (
        currentSettings.debugEnabled
        && semanticAdmissionEnabled
        && scanSummary
        && Number(scanSummary.semanticEligible || 0) > 0
      ) {
        log("Semantic admission apply summary:", {
          eligible: Number(scanSummary.semanticEligible || 0),
          ready: Number(scanSummary.semanticReady || 0),
          policyReplaces: Number(scanSummary.semanticPolicyReplaces || 0),
          policyAbstains: Number(scanSummary.semanticPolicyAbstains || 0),
          policySoftAffordances: Number(scanSummary.semanticPolicySoftAffordances || 0),
          fallbackReplaces: Number(scanSummary.semanticFallbackReplaces || 0),
          fallbackAbstains: Number(scanSummary.semanticFallbackAbstains || 0),
          fallbackSoftAffordances: Number(scanSummary.semanticFallbackSoftAffordances || 0),
          decisionPolicyId: String(scanSummary.semanticDecisionPolicyId || ""),
          policyAbstainRate: semanticDecisionMetrics.policyAbstainRate,
          fallbackAbstainRate: semanticDecisionMetrics.fallbackAbstainRate,
          overallAbstainRate: semanticDecisionMetrics.overallAbstainRate,
          debugDecisionOverride: String(scanSummary.semanticDebugDecisionOverride || ""),
          debugOverrideApplied: Number(scanSummary.semanticDebugOverrideApplied || 0)
        });
        log("Semantic admission performance summary:", semanticPerformanceMetrics);
      }
      if (currentSettings.debugEnabled) {
        log("Apply timing:", {
          applyTotalMs,
          activeRulesResolveMs,
          helperRulesResolveMs,
          srsGateMs,
          semanticInventoryResolveMs,
          runtimeApplyMs,
          scanMs,
          firstReplacementLatencyMs,
          firstVisibleReplacementLatencyMs
        });
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
          semantic_admission_enabled: semanticAdmissionEnabled,
          semantic_runtime_capability: semanticRuntimeCapability,
          semantic_runtime_reason_code: semanticRuntimeReasonCode,
          semantic_pointer_rule_count: semanticPointerRuleCount,
          semantic_ready_rule_count: semanticReadyRuleCount,
          semantic_fallback_policy: semanticFallbackPolicy,
          semantic_inventory_loaded: semanticInventoryLoaded,
          semantic_inventory_source: semanticInventorySource,
          semantic_inventory_error: semanticInventoryError || "",
          semantic_matches_eligible: scanSummary ? Number(scanSummary.semanticEligible || 0) : 0,
          semantic_matches_ready: scanSummary ? Number(scanSummary.semanticReady || 0) : 0,
          semantic_policy_replaces: scanSummary ? Number(scanSummary.semanticPolicyReplaces || 0) : 0,
          semantic_policy_abstains: scanSummary ? Number(scanSummary.semanticPolicyAbstains || 0) : 0,
          semantic_policy_soft_affordances: scanSummary
            ? Number(scanSummary.semanticPolicySoftAffordances || 0)
            : 0,
          semantic_fallback_replaces: scanSummary ? Number(scanSummary.semanticFallbackReplaces || 0) : 0,
          semantic_fallback_abstains: scanSummary ? Number(scanSummary.semanticFallbackAbstains || 0) : 0,
          semantic_fallback_soft_affordances: scanSummary
            ? Number(scanSummary.semanticFallbackSoftAffordances || 0)
            : 0,
          semantic_policy_decision_total: semanticDecisionMetrics.policyDecisionTotal,
          semantic_fallback_decision_total: semanticDecisionMetrics.fallbackDecisionTotal,
          semantic_overall_decision_total: semanticDecisionMetrics.overallDecisionTotal,
          semantic_policy_abstain_rate: semanticDecisionMetrics.policyAbstainRate,
          semantic_fallback_abstain_rate: semanticDecisionMetrics.fallbackAbstainRate,
          semantic_overall_abstain_rate: semanticDecisionMetrics.overallAbstainRate,
          semantic_decision_policy_id: scanSummary
            ? String(scanSummary.semanticDecisionPolicyId || "")
            : "",
          semantic_debug_decision_override: scanSummary
            ? String(scanSummary.semanticDebugDecisionOverride || "")
            : "",
          semantic_debug_override_applied: scanSummary
            ? Number(scanSummary.semanticDebugOverrideApplied || 0)
            : 0,
          semantic_inventory_lookup_calls: semanticPerformanceMetrics.inventoryLookupCalls,
          semantic_inventory_lookup_latency_ms_total: semanticPerformanceMetrics.inventoryLookupLatencyMsTotal,
          semantic_inventory_lookup_latency_ms_max: semanticPerformanceMetrics.inventoryLookupLatencyMsMax,
          semantic_inventory_lookup_latency_ms_avg: semanticPerformanceMetrics.inventoryLookupLatencyMsAvg,
          semantic_helper_batch_calls: semanticPerformanceMetrics.helperBatchCalls,
          semantic_helper_request_count: semanticPerformanceMetrics.helperRequestCount,
          semantic_helper_batch_min_size: semanticPerformanceMetrics.helperBatchMinSize,
          semantic_helper_batch_max_size: semanticPerformanceMetrics.helperBatchMaxSize,
          semantic_helper_batch_avg_size: semanticPerformanceMetrics.helperBatchAvgSize,
          semantic_helper_latency_ms_total: semanticPerformanceMetrics.helperLatencyMsTotal,
          semantic_helper_latency_ms_max: semanticPerformanceMetrics.helperLatencyMsMax,
          semantic_helper_latency_ms_avg: semanticPerformanceMetrics.helperLatencyMsAvg,
          semantic_scan_node_batch_calls: semanticPerformanceMetrics.scanNodeBatchCalls,
          semantic_scan_node_count: semanticPerformanceMetrics.scanNodeCount,
          semantic_scan_node_batch_min_size: semanticPerformanceMetrics.scanNodeBatchMinSize,
          semantic_scan_node_batch_max_size: semanticPerformanceMetrics.scanNodeBatchMaxSize,
          semantic_scan_node_batch_avg_size: semanticPerformanceMetrics.scanNodeBatchAvgSize,
          semantic_scan_node_concurrent_batches: semanticPerformanceMetrics.scanNodeConcurrentBatches,
          semantic_scan_node_serial_batches: semanticPerformanceMetrics.scanNodeSerialBatches,
          semantic_scan_node_serial_budget_batches: semanticPerformanceMetrics.scanNodeSerialBudgetBatches,
          semantic_context_cache_container_builds: semanticPerformanceMetrics.contextCacheContainerBuilds,
          semantic_context_cache_record_reuses: semanticPerformanceMetrics.contextCacheRecordReuses,
          semantic_context_cache_usable_reuses: semanticPerformanceMetrics.contextCacheUsableReuses,
          semantic_context_cache_bypasses: semanticPerformanceMetrics.contextCacheBypasses,
          apply_total_ms: applyTotalMs,
          active_rules_resolve_ms: activeRulesResolveMs,
          helper_rules_resolve_ms: helperRulesResolveMs,
          srs_gate_ms: srsGateMs,
          semantic_inventory_resolve_ms: semanticInventoryResolveMs,
          runtime_apply_ms: runtimeApplyMs,
          scan_ms: scanMs,
          first_replacement_latency_ms: firstReplacementLatencyMs,
          first_visible_replacement_latency_ms: firstVisibleReplacementLatencyMs,
          srs_stats: srsStats || null,
          helper_rules_error: helperRulesError || "",
          page_url: window.location ? window.location.href : "",
          frame_type: getFrameInfo().frameType
        });
      }
      if (currentSettings.debugEnabled) {
        log("Context info:", Object.assign({ readyState: document.readyState }, getFrameInfo()));
        if (document.body) {
          log("Body info:", {
            childElements: document.body.childElementCount,
            textLength: document.body.innerText ? document.body.innerText.length : 0
          });
        }
      }
      if (currentSettings.debugEnabled && !normalizedRules.length) {
        log("No rules loaded.");
      }
      if (currentSettings.debugEnabled && focusWord && focusRulesCount === 0) {
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
