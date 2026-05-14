(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function isFiniteMetric(value) {
    return value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
  }

  function mergeNullableMin(currentValue, nextValue) {
    if (!isFiniteMetric(nextValue)) return currentValue;
    if (!isFiniteMetric(currentValue)) return Number(nextValue);
    return Math.min(Number(currentValue), Number(nextValue));
  }

  function createCounterDefaults() {
    return {
      semanticEligible: 0,
      semanticReady: 0,
      semanticPolicyReplaces: 0,
      semanticPolicyAbstains: 0,
      semanticPolicySoftAffordances: 0,
      semanticFallbackReplaces: 0,
      semanticFallbackAbstains: 0,
      semanticFallbackSoftAffordances: 0,
      semanticFallbackReasonCounts: {},
      semanticDecisionPolicyId: "",
      semanticDebugDecisionOverride: "",
      semanticDebugOverrideApplied: 0,
      semanticInventoryLookupCalls: 0,
      semanticInventoryLookupLatencyMsTotal: 0,
      semanticInventoryLookupLatencyMsMax: 0,
      semanticHelperBatchCalls: 0,
      semanticHelperRequestCount: 0,
      semanticHelperBatchMinSize: null,
      semanticHelperBatchMaxSize: 0,
      semanticHelperLatencyMsTotal: 0,
      semanticHelperLatencyMsMax: 0,
      semanticScanNodeBatchCalls: 0,
      semanticScanNodeCount: 0,
      semanticScanNodeBatchMinSize: null,
      semanticScanNodeBatchMaxSize: 0,
      semanticScanNodeConcurrentBatches: 0,
      semanticScanNodeSerialBatches: 0,
      semanticScanNodeSerialBudgetBatches: 0,
      semanticContextCacheStats: null
    };
  }

  function mergeCountMap(currentCounts, nextCounts) {
    const merged = currentCounts && typeof currentCounts === "object" ? currentCounts : {};
    const source = nextCounts && typeof nextCounts === "object" ? nextCounts : {};
    for (const [rawKey, rawValue] of Object.entries(source)) {
      const key = String(rawKey || "").trim();
      const value = Number(rawValue || 0);
      if (!key || !Number.isFinite(value) || value <= 0) continue;
      merged[key] = Number(merged[key] || 0) + value;
    }
    return merged;
  }

  function createFallbackScanCounters(options) {
    const opts = options && typeof options === "object" ? options : {};
    const nowMs = typeof opts.nowMs === "function" ? opts.nowMs : (() => Date.now());
    const getFocusWord = typeof opts.getFocusWord === "function" ? opts.getFocusWord : (() => "");
    function buildCounter(currentSettings, detailLimit, focusDetailLimit) {
      return {
        scanStartedAtMs: nowMs(),
        firstReplacementLatencyMs: null,
        firstVisibleReplacementLatencyMs: null,
        scanDurationMs: null,
        yieldCount: 0,
        totalNodes: 0, emptyNodes: 0, whitespaceNodes: 0, replacements: 0, nodes: 0, scanned: 0,
        skippedEditable: 0, skippedExcluded: 0, skippedLexi: 0, skippedCached: 0,
        detailLogs: 0, detailLimit, detailTruncated: false,
        focusWord: currentSettings.debugEnabled ? getFocusWord(currentSettings) : "",
        focusSubstringNodes: 0, focusTokenNodes: 0, focusReplaced: 0, focusUnmatched: 0,
        focusSkippedEditable: 0, focusSkippedExcluded: 0, focusSkippedLexi: 0, focusSkippedCached: 0,
        focusSubstringNoToken: 0, focusDetailLogs: 0, focusDetailLimit, focusDetailTruncated: false,
        ...createCounterDefaults()
      };
    }
    return {
      createFullScanCounter: (settings) => buildCounter(settings, 40, 30),
      createMutationCounter: (settings) => buildCounter(settings, 20, 15)
    };
  }

  function ensureCounterDefaults(counter) {
    const defaults = createCounterDefaults();
    for (const [key, value] of Object.entries(defaults)) {
      if (counter[key] === undefined) {
        counter[key] = value;
      }
    }
  }

  function mergeSummaryIntoCounter(counter, summary) {
    if (!counter || !summary || typeof summary !== "object") {
      return;
    }
    ensureCounterDefaults(counter);
    const nextDecisionPolicyId = String(summary.decisionPolicyId || "").trim();
    counter.semanticEligible += Number(summary.eligible || 0);
    counter.semanticReady += Number(summary.ready || 0);
    counter.semanticPolicyReplaces += Number(summary.policyReplaces || 0);
    counter.semanticPolicyAbstains += Number(summary.policyAbstains || 0);
    counter.semanticPolicySoftAffordances += Number(summary.policySoftAffordances || 0);
    counter.semanticFallbackReplaces += Number(summary.fallbackReplaces || 0);
    counter.semanticFallbackAbstains += Number(summary.fallbackAbstains || 0);
    counter.semanticFallbackSoftAffordances += Number(summary.fallbackSoftAffordances || 0);
    counter.semanticFallbackReasonCounts = mergeCountMap(
      counter.semanticFallbackReasonCounts,
      summary.fallbackReasonCounts
    );
    counter.semanticDebugOverrideApplied += Number(summary.debugOverrideApplied || 0);
    counter.semanticInventoryLookupCalls += Number(summary.inventoryLookupCalls || 0);
    counter.semanticInventoryLookupLatencyMsTotal += Number(summary.inventoryLookupLatencyMsTotal || 0);
    counter.semanticInventoryLookupLatencyMsMax = Math.max(
      Number(counter.semanticInventoryLookupLatencyMsMax || 0),
      Number(summary.inventoryLookupLatencyMsMax || 0)
    );
    counter.semanticHelperBatchCalls += Number(summary.helperBatchCalls || 0);
    counter.semanticHelperRequestCount += Number(summary.helperRequestCount || 0);
    counter.semanticHelperBatchMinSize = mergeNullableMin(
      counter.semanticHelperBatchMinSize,
      summary.helperBatchMinSize
    );
    counter.semanticHelperBatchMaxSize = Math.max(
      Number(counter.semanticHelperBatchMaxSize || 0),
      Number(summary.helperBatchMaxSize || 0)
    );
    counter.semanticHelperLatencyMsTotal += Number(summary.helperLatencyMsTotal || 0);
    counter.semanticHelperLatencyMsMax = Math.max(
      Number(counter.semanticHelperLatencyMsMax || 0),
      Number(summary.helperLatencyMsMax || 0)
    );

    const nextDebugDecisionOverride = String(summary.debugDecisionOverride || "").trim();
    if (nextDecisionPolicyId) {
      if (!counter.semanticDecisionPolicyId) {
        counter.semanticDecisionPolicyId = nextDecisionPolicyId;
      } else if (counter.semanticDecisionPolicyId !== nextDecisionPolicyId) {
        counter.semanticDecisionPolicyId = "mixed";
      }
    }
    if (nextDebugDecisionOverride) {
      if (!counter.semanticDebugDecisionOverride) {
        counter.semanticDebugDecisionOverride = nextDebugDecisionOverride;
      } else if (counter.semanticDebugDecisionOverride !== nextDebugDecisionOverride) {
        counter.semanticDebugDecisionOverride = "mixed";
      }
    }
  }

  function recordScanNodeBatch(counter, size, concurrent, reason) {
    if (!counter || !Number.isFinite(Number(size)) || Number(size) <= 0) {
      return;
    }
    ensureCounterDefaults(counter);
    const batchSize = Number(size);
    counter.semanticScanNodeBatchCalls = Number(counter.semanticScanNodeBatchCalls || 0) + 1;
    counter.semanticScanNodeCount = Number(counter.semanticScanNodeCount || 0) + batchSize;
    counter.semanticScanNodeBatchMinSize = isFiniteMetric(counter.semanticScanNodeBatchMinSize)
      ? Math.min(Number(counter.semanticScanNodeBatchMinSize), batchSize)
      : batchSize;
    counter.semanticScanNodeBatchMaxSize = Math.max(
      Number(counter.semanticScanNodeBatchMaxSize || 0),
      batchSize
    );
    if (concurrent) {
      counter.semanticScanNodeConcurrentBatches = Number(counter.semanticScanNodeConcurrentBatches || 0) + 1;
    } else {
      counter.semanticScanNodeSerialBatches = Number(counter.semanticScanNodeSerialBatches || 0) + 1;
      if (reason === "page_budget") {
        counter.semanticScanNodeSerialBudgetBatches = Number(counter.semanticScanNodeSerialBudgetBatches || 0) + 1;
      }
    }
  }

  async function maybeYieldDuringScan(counter, deadlineMs, hasRemaining, nowMs, yieldToPage) {
    if (!hasRemaining || !counter || !Number.isFinite(Number(deadlineMs)) || deadlineMs <= 0) {
      return deadlineMs;
    }
    const currentMs = nowMs();
    if ((currentMs - Number(counter.scanStartedAtMs || currentMs)) < deadlineMs) {
      return deadlineMs;
    }
    counter.yieldCount += 1;
    await yieldToPage();
    return nowMs();
  }

  function buildSummary(counter) {
    const inventoryLookupCalls = Number(counter && counter.semanticInventoryLookupCalls || 0);
    const helperBatchCalls = Number(counter && counter.semanticHelperBatchCalls || 0);
    const helperRequestCount = Number(counter && counter.semanticHelperRequestCount || 0);
    const scanNodeBatchCalls = Number(counter && counter.semanticScanNodeBatchCalls || 0);
    const scanNodeCount = Number(counter && counter.semanticScanNodeCount || 0);
    const contextStats = counter && counter.semanticContextCacheStats
      && typeof counter.semanticContextCacheStats === "object"
      ? counter.semanticContextCacheStats
      : {};
    return {
      inventoryLookupCalls,
      inventoryLookupLatencyMsTotal: Number(counter && counter.semanticInventoryLookupLatencyMsTotal || 0),
      inventoryLookupLatencyMsMax: Number(counter && counter.semanticInventoryLookupLatencyMsMax || 0),
      inventoryLookupLatencyMsAvg: inventoryLookupCalls > 0
        ? Number(counter.semanticInventoryLookupLatencyMsTotal || 0) / inventoryLookupCalls
        : null,
      helperBatchCalls,
      helperRequestCount,
      helperBatchMinSize: isFiniteMetric(counter ? counter.semanticHelperBatchMinSize : null)
        ? Number(counter.semanticHelperBatchMinSize)
        : null,
      helperBatchMaxSize: Number(counter && counter.semanticHelperBatchMaxSize || 0),
      helperBatchAvgSize: helperBatchCalls > 0 ? helperRequestCount / helperBatchCalls : null,
      helperLatencyMsTotal: Number(counter && counter.semanticHelperLatencyMsTotal || 0),
      helperLatencyMsMax: Number(counter && counter.semanticHelperLatencyMsMax || 0),
      helperLatencyMsAvg: helperBatchCalls > 0
        ? Number(counter.semanticHelperLatencyMsTotal || 0) / helperBatchCalls
        : null,
      scanNodeBatchCalls,
      scanNodeCount,
      scanNodeBatchMinSize: isFiniteMetric(counter ? counter.semanticScanNodeBatchMinSize : null)
        ? Number(counter.semanticScanNodeBatchMinSize)
        : null,
      scanNodeBatchMaxSize: Number(counter && counter.semanticScanNodeBatchMaxSize || 0),
      scanNodeBatchAvgSize: scanNodeBatchCalls > 0 ? scanNodeCount / scanNodeBatchCalls : null,
      scanNodeConcurrentBatches: Number(counter && counter.semanticScanNodeConcurrentBatches || 0),
      scanNodeSerialBatches: Number(counter && counter.semanticScanNodeSerialBatches || 0),
      scanNodeSerialBudgetBatches: Number(counter && counter.semanticScanNodeSerialBudgetBatches || 0),
      contextCacheContainerBuilds: Number(contextStats.containerBuilds || 0),
      contextCacheRecordReuses: Number(contextStats.recordReuses || 0),
      contextCacheUsableReuses: Number(contextStats.usableReuses || 0),
      contextCacheBypasses: Number(contextStats.bypasses || 0)
    };
  }

  function buildAdmissionLogSummary(counter) {
    return {
      eligible: counter.semanticEligible,
      ready: counter.semanticReady,
      policyReplaces: counter.semanticPolicyReplaces,
      policyAbstains: counter.semanticPolicyAbstains,
      policySoftAffordances: counter.semanticPolicySoftAffordances,
      fallbackReplaces: counter.semanticFallbackReplaces,
      fallbackAbstains: counter.semanticFallbackAbstains,
      fallbackSoftAffordances: counter.semanticFallbackSoftAffordances,
      fallbackReasonCounts: { ...(counter.semanticFallbackReasonCounts || {}) },
      decisionPolicyId: counter.semanticDecisionPolicyId || "",
      debugDecisionOverride: counter.semanticDebugDecisionOverride || "",
      debugOverrideApplied: counter.semanticDebugOverrideApplied || 0
    };
  }

  root.contentDomScanSemanticPerformanceMetrics = {
    buildAdmissionLogSummary,
    buildSummary,
    createCounterDefaults,
    createFallbackScanCounters,
    mergeSummaryIntoCounter,
    maybeYieldDuringScan,
    recordScanNodeBatch
  };
})();
