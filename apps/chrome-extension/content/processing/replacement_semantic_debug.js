(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizeReasonCodes(reasonCodes) {
    return Array.isArray(reasonCodes)
      ? reasonCodes.map((code) => String(code || "")).filter(Boolean)
      : [];
  }

  function buildMetadata(semanticAdmission, semanticDecision) {
    if (!semanticAdmission && !semanticDecision) return null;
    return {
      status: semanticAdmission ? String(semanticAdmission.status || "") : "",
      trigger_id: semanticAdmission ? String(semanticAdmission.trigger_id || "") : "",
      phrase_set_id: semanticAdmission ? String(semanticAdmission.phrase_set_id || "") : "",
      decision: semanticDecision ? String(semanticDecision.decision || "") : "",
      decision_source: semanticDecision ? String(semanticDecision.decision_source || "") : "",
      effective_decision: semanticDecision ? String(semanticDecision.effective_decision || "") : "",
      effective_decision_source: semanticDecision ? String(semanticDecision.effective_decision_source || "") : "",
      debug_override: semanticDecision ? String(semanticDecision.debug_override || "") : "",
      debug_original_decision: semanticDecision ? String(semanticDecision.debug_original_decision || "") : "",
      debug_original_decision_source: semanticDecision ? String(semanticDecision.debug_original_decision_source || "") : "",
      reason_codes: normalizeReasonCodes(semanticDecision && semanticDecision.reason_codes),
      sense_id: semanticDecision ? String(semanticDecision.sense_id || "") : "",
      competition_set_id: semanticDecision ? String(semanticDecision.competition_set_id || "") : "",
      score_margin: semanticDecision && Number.isFinite(Number(semanticDecision.score_margin)) ? Number(semanticDecision.score_margin) : null,
      active_score: semanticDecision && Number.isFinite(Number(semanticDecision.active_score)) ? Number(semanticDecision.active_score) : null,
      top_shadow_score: semanticDecision && Number.isFinite(Number(semanticDecision.top_shadow_score)) ? Number(semanticDecision.top_shadow_score) : null,
      phrase_preempted: semanticDecision ? semanticDecision.phrase_preempted === true : false
    };
  }

  function copyDecision(semanticDecision) {
    if (!semanticDecision) return null;
    return {
      decision: String(semanticDecision.decision || ""),
      decision_source: String(semanticDecision.decision_source || ""),
      effective_decision: String(semanticDecision.effective_decision || ""),
      effective_decision_source: String(semanticDecision.effective_decision_source || ""),
      debug_override: String(semanticDecision.debug_override || ""),
      debug_original_decision: String(semanticDecision.debug_original_decision || ""),
      debug_original_decision_source: String(semanticDecision.debug_original_decision_source || ""),
      reason_codes: normalizeReasonCodes(semanticDecision.reason_codes),
      sense_id: String(semanticDecision.sense_id || ""),
      competition_set_id: String(semanticDecision.competition_set_id || ""),
      score_margin: Number.isFinite(Number(semanticDecision.score_margin)) ? Number(semanticDecision.score_margin) : null,
      active_score: Number.isFinite(Number(semanticDecision.active_score)) ? Number(semanticDecision.active_score) : null,
      top_shadow_score: Number.isFinite(Number(semanticDecision.top_shadow_score)) ? Number(semanticDecision.top_shadow_score) : null,
      phrase_preempted: semanticDecision.phrase_preempted === true
    };
  }

  function applyToSpan(span, metadata) {
    if (!span || !metadata || typeof metadata !== "object") return;
    const mappings = [["status", "semanticStatus"], ["decision", "semanticDecision"], ["decision_source", "semanticDecisionSource"], ["effective_decision", "semanticEffectiveDecision"], ["effective_decision_source", "semanticEffectiveDecisionSource"], ["debug_override", "semanticDebugOverride"], ["debug_original_decision", "semanticDebugOriginalDecision"], ["debug_original_decision_source", "semanticDebugOriginalDecisionSource"], ["sense_id", "semanticSenseId"], ["competition_set_id", "semanticCompetitionSetId"], ["phrase_set_id", "semanticPhraseSetId"], ["trigger_id", "semanticTriggerId"]];
    for (const [sourceKey, datasetKey] of mappings) {
      if (metadata[sourceKey]) span.dataset[datasetKey] = String(metadata[sourceKey]);
    }
    if (Array.isArray(metadata.reason_codes) && metadata.reason_codes.length) {
      span.dataset.semanticReasonCodes = metadata.reason_codes
        .map((code) => String(code || "").trim())
        .filter(Boolean)
        .join(",");
    }
    if (Number.isFinite(Number(metadata.score_margin))) {
      span.dataset.semanticScoreMargin = String(Number(metadata.score_margin));
    }
    if (Number.isFinite(Number(metadata.active_score))) {
      span.dataset.semanticActiveScore = String(Number(metadata.active_score));
    }
    if (Number.isFinite(Number(metadata.top_shadow_score))) {
      span.dataset.semanticTopShadowScore = String(Number(metadata.top_shadow_score));
    }
    if (metadata.phrase_preempted === true) {
      span.dataset.semanticPhrasePreempted = "true";
    }
  }

  root.replacementSemanticDebug = {
    applyToSpan,
    buildMetadata,
    copyDecision
  };
})();
