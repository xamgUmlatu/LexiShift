(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function getAdmission(rule) {
    return (
      rule
      && rule.metadata
      && typeof rule.metadata === "object"
      && rule.metadata.semantic_admission
      && typeof rule.metadata.semantic_admission === "object"
    )
      ? rule.metadata.semantic_admission
      : null;
  }

  function getMatchSignature(match) {
    const rule = match && match.rule && typeof match.rule === "object" ? match.rule : {};
    const metadata = rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    const admission = getAdmission(rule) || {};
    return JSON.stringify([
      Number(match && match.startWordIndex || 0),
      Number(match && match.endWordIndex || 0),
      String(rule.source_phrase || ""),
      String(rule.replacement || ""),
      String(metadata.language_pair || ""),
      String(admission.trigger_id || ""),
      String(admission.phrase_set_id || ""),
      String(admission.sense_id || ""),
      String(admission.competition_set_id || "")
    ]);
  }

  function buildDecisionBySignature(decisionMap) {
    const bySignature = new Map();
    if (!(decisionMap instanceof Map)) {
      return bySignature;
    }
    for (const [match, decision] of decisionMap.entries()) {
      bySignature.set(getMatchSignature(match), decision);
    }
    return bySignature;
  }

  function normalizeResultOverride(value) {
    if (!value || typeof value !== "object") {
      return null;
    }
    const rawAllowed = value.allowedMatchSignatures;
    const allowedMatchSignatures = rawAllowed instanceof Set
      ? rawAllowed
      : new Set(Array.isArray(rawAllowed) ? rawAllowed.map((entry) => String(entry || "")) : []);
    const rawDecisionBySignature = value.decisionBySignature;
    const decisionBySignature = rawDecisionBySignature instanceof Map
      ? rawDecisionBySignature
      : new Map();
    return { allowedMatchSignatures, decisionBySignature };
  }

  function buildResultOverride(matches, decisionMap) {
    const allowedMatchSignatures = new Set(
      Array.isArray(matches) ? matches.map((match) => getMatchSignature(match)) : []
    );
    return {
      allowedMatchSignatures,
      decisionBySignature: buildDecisionBySignature(decisionMap)
    };
  }

  root.replacementSemanticOverride = {
    buildDecisionBySignature,
    buildResultOverride,
    getAdmission,
    getMatchSignature,
    normalizeResultOverride
  };
})();
