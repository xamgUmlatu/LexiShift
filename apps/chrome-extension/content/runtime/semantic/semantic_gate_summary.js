(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createSummary(fallbackPolicy) {
    return {
      enabled: true,
      fallbackPolicy,
      eligible: 0,
      ready: 0,
      policyReplaces: 0,
      policyAbstains: 0,
      policySoftAffordances: 0,
      fallbackReplaces: 0,
      fallbackAbstains: 0,
      fallbackSoftAffordances: 0,
      inventorySource: "none",
      inventoryError: "",
      helperError: "",
      decisionPolicyId: "",
      policyDecisionTotal: 0,
      fallbackDecisionTotal: 0,
      overallDecisionTotal: 0,
      policyAbstainRate: null,
      fallbackAbstainRate: null,
      overallAbstainRate: null,
      debugDecisionOverride: "",
      debugOverrideApplied: 0,
      inventoryLookupCalls: 0,
      inventoryLookupLatencyMsTotal: 0,
      inventoryLookupLatencyMsMax: 0,
      inventoryLookupLatencyMsAvg: null,
      helperBatchCalls: 0,
      helperRequestCount: 0,
      helperBatchMinSize: null,
      helperBatchMaxSize: 0,
      helperLatencyMsTotal: 0,
      helperLatencyMsMax: 0,
      helperLatencyMsAvg: null
    };
  }

  function summarizeDecision(summary, decisionRecord, admission) {
    if (!summary || !decisionRecord) return;
    summary.eligible += 1;
    const status = String(admission && admission.status ? admission.status : "").trim();
    if (status === "ready") summary.ready += 1;
    const source = String(decisionRecord.decision_source || "");
    const decision = String(decisionRecord.decision || "");
    if (source === "policy") {
      if (decision === "replace") summary.policyReplaces += 1;
      else if (decision === "soft_affordance") summary.policySoftAffordances += 1;
      else summary.policyAbstains += 1;
      return;
    }
    if (decision === "replace") summary.fallbackReplaces += 1;
    else if (decision === "soft_affordance") summary.fallbackSoftAffordances += 1;
    else summary.fallbackAbstains += 1;
  }

  function normalizeRate(numerator, denominator) {
    return Number(denominator) > 0 ? Number(numerator) / Number(denominator) : null;
  }

  function normalizeDurationMs(value) {
    return Number.isFinite(Number(value)) && Number(value) >= 0 ? Number(value) : 0;
  }

  function summarizeInventoryLookup(summary, latencyMs) {
    if (!summary || typeof summary !== "object") return;
    const duration = normalizeDurationMs(latencyMs);
    summary.inventoryLookupCalls += 1;
    summary.inventoryLookupLatencyMsTotal += duration;
    summary.inventoryLookupLatencyMsMax = Math.max(summary.inventoryLookupLatencyMsMax, duration);
  }

  function summarizeHelperBatch(summary, requestCount, latencyMs) {
    if (!summary || typeof summary !== "object") return;
    const size = Number.isFinite(Number(requestCount)) && Number(requestCount) > 0
      ? Number(requestCount)
      : 0;
    const duration = normalizeDurationMs(latencyMs);
    summary.helperBatchCalls += 1;
    summary.helperRequestCount += size;
    summary.helperBatchMinSize = summary.helperBatchMinSize === null
      ? size
      : Math.min(summary.helperBatchMinSize, size);
    summary.helperBatchMaxSize = Math.max(summary.helperBatchMaxSize, size);
    summary.helperLatencyMsTotal += duration;
    summary.helperLatencyMsMax = Math.max(summary.helperLatencyMsMax, duration);
  }

  function finalizeSummary(summary, debugDecisionOverride, debugOverrideApplied) {
    if (!summary || typeof summary !== "object") return;
    const policyDecisionTotal = (
      Number(summary.policyReplaces || 0)
      + Number(summary.policyAbstains || 0)
      + Number(summary.policySoftAffordances || 0)
    );
    const fallbackDecisionTotal = (
      Number(summary.fallbackReplaces || 0)
      + Number(summary.fallbackAbstains || 0)
      + Number(summary.fallbackSoftAffordances || 0)
    );
    const overallDecisionTotal = Number(summary.eligible || 0);
    summary.policyDecisionTotal = policyDecisionTotal;
    summary.fallbackDecisionTotal = fallbackDecisionTotal;
    summary.overallDecisionTotal = overallDecisionTotal;
    summary.policyAbstainRate = normalizeRate(summary.policyAbstains || 0, policyDecisionTotal);
    summary.fallbackAbstainRate = normalizeRate(summary.fallbackAbstains || 0, fallbackDecisionTotal);
    summary.overallAbstainRate = normalizeRate(
      Number(summary.policyAbstains || 0) + Number(summary.fallbackAbstains || 0),
      overallDecisionTotal
    );
    summary.debugDecisionOverride = debugDecisionOverride || "";
    summary.debugOverrideApplied = Number(debugOverrideApplied || 0);
    summary.inventoryLookupLatencyMsAvg = normalizeRate(
      summary.inventoryLookupLatencyMsTotal || 0,
      summary.inventoryLookupCalls || 0
    );
    summary.helperLatencyMsAvg = normalizeRate(
      summary.helperLatencyMsTotal || 0,
      summary.helperBatchCalls || 0
    );
  }

  root.contentSemanticGateSummary = {
    createSummary,
    finalizeSummary,
    summarizeHelperBatch,
    summarizeInventoryLookup,
    summarizeDecision
  };
})();
