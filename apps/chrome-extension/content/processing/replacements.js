(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { tokenize, computeGapOk } = root.tokenizer || {};
  const { findLongestMatch, applyCase } = root.matcher || {};
  const replacementSelection = root.replacementSelection || {};
  const RULE_ORIGIN_SRS = "srs";
  const MAX_CONTEXT_WORDS = 15;
  const createSelectionSeed = typeof replacementSelection.createSelectionSeed === "function"
    ? replacementSelection.createSelectionSeed
    : (() => 0);
  const filterMatchesByPolicy = typeof replacementSelection.filterMatches === "function"
    ? replacementSelection.filterMatches
    : ((matches) => matches);

  function normalizeDisplayScript(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized === "kana" || normalized === "romaji") {
      return normalized;
    }
    return "kanji";
  }

  function targetLanguageFromPair(pair) {
    const normalized = String(pair || "").trim().toLowerCase();
    if (!normalized) {
      return "";
    }
    const parts = normalized.split("-", 2);
    if (parts.length < 2) {
      return "";
    }
    return String(parts[1] || "").trim().toLowerCase();
  }

  function targetLanguageFromTag(tag) {
    const normalized = String(tag || "").trim().toLowerCase();
    if (!normalized) {
      return "";
    }
    const [base] = normalized.split("-", 1);
    return String(base || "").trim().toLowerCase();
  }

  function normalizeScriptForms(value) {
    if (!value || typeof value !== "object") {
      return null;
    }
    const scripts = ["kanji", "kana", "romaji"];
    const normalized = {};
    for (const script of scripts) {
      const text = String(value[script] || "").trim();
      if (text) {
        normalized[script] = text;
      }
    }
    return Object.keys(normalized).length ? normalized : null;
  }

  function normalizeWordPackage(value) {
    if (!value || typeof value !== "object") {
      return null;
    }
    const version = Number(value.version || 1);
    if (!Number.isFinite(version) || version < 1) {
      return null;
    }
    const surface = String(value.surface || "").trim();
    const languageTag = String(value.language_tag || "").trim().toLowerCase();
    const source = value.source && typeof value.source === "object" ? value.source : null;
    const provider = source ? String(source.provider || "").trim() : "";
    if (!surface || !languageTag || !provider) {
      return null;
    }
    const scriptForms = normalizeScriptForms(value.script_forms);
    const reading = String(value.reading || "").trim();
    if (!scriptForms || !reading) {
      return null;
    }
    const normalized = {
      version: 1,
      language_tag: languageTag,
      surface,
      reading,
      script_forms: scriptForms,
      source: {
        provider
      }
    };
    const passthrough = ["pos", "wtype", "sublemma", "core_rank", "pmw", "lform_raw", "row_index", "row_rank"];
    for (const key of passthrough) {
      if (value[key] === undefined || value[key] === null || value[key] === "") {
        continue;
      }
      normalized[key] = value[key];
    }
    return normalized;
  }

  function resolveDisplayPayload(rule, sourceWords, settings) {
    const casePolicy = (rule && rule.case_policy) || "match";
    const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    const morphology = metadata && metadata.morphology && typeof metadata.morphology === "object"
      ? metadata.morphology
      : null;
    const canonicalReplacement = String((rule && rule.replacement) || "").trim();
    const surfaceReplacement = morphology
      ? String(morphology.target_surface || "").trim()
      : "";
    const displayBaseReplacement = surfaceReplacement || canonicalReplacement;
    const languagePair = String(metadata.language_pair || "").trim();
    const wordPackage = normalizeWordPackage(metadata.word_package);
    const packageScriptForms = normalizeScriptForms(wordPackage && wordPackage.script_forms);
    const legacyScriptForms = normalizeScriptForms(metadata.script_forms);
    const scriptForms = packageScriptForms || legacyScriptForms;
    const targetLanguage = targetLanguageFromTag(wordPackage && wordPackage.language_tag)
      || targetLanguageFromPair(languagePair)
      || String((settings && settings.targetLanguage) || "").trim().toLowerCase();
    const effectiveWordPackage = wordPackage
      ? {
          ...wordPackage,
          script_forms: scriptForms || wordPackage.script_forms
        }
      : null;

    if (targetLanguage !== "ja" || !scriptForms) {
      return {
        canonicalReplacement,
        displayReplacement: applyCase(displayBaseReplacement, sourceWords, casePolicy),
        displayScript: "",
        scriptForms: null,
        wordPackage: effectiveWordPackage,
        morphology
      };
    }

    const caseAdjustedForms = {};
    for (const [script, value] of Object.entries(scriptForms)) {
      caseAdjustedForms[script] = applyCase(String(value), sourceWords, casePolicy);
    }
    const preferredScript = normalizeDisplayScript(settings && settings.targetDisplayScript);
    const availableScripts = Object.keys(caseAdjustedForms);
    const displayScript = caseAdjustedForms[preferredScript]
      ? preferredScript
      : availableScripts[0];
    return {
      canonicalReplacement,
      displayReplacement: caseAdjustedForms[displayScript] || applyCase(canonicalReplacement, sourceWords, casePolicy),
      displayScript,
      scriptForms: caseAdjustedForms,
      wordPackage: effectiveWordPackage,
      morphology
    };
  }

  function normalizeSemanticReasonCodes(reasonCodes) {
    return Array.isArray(reasonCodes)
      ? reasonCodes.map((code) => String(code || "")).filter(Boolean)
      : [];
  }

  function buildSemanticDebugMetadata(semanticAdmission, semanticDecision) {
    if (!semanticAdmission && !semanticDecision) {
      return null;
    }
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
      reason_codes: normalizeSemanticReasonCodes(semanticDecision && semanticDecision.reason_codes),
      sense_id: semanticDecision ? String(semanticDecision.sense_id || "") : "",
      competition_set_id: semanticDecision ? String(semanticDecision.competition_set_id || "") : "",
      score_margin: semanticDecision && Number.isFinite(Number(semanticDecision.score_margin)) ? Number(semanticDecision.score_margin) : null,
      active_score: semanticDecision && Number.isFinite(Number(semanticDecision.active_score)) ? Number(semanticDecision.active_score) : null,
      top_shadow_score: semanticDecision && Number.isFinite(Number(semanticDecision.top_shadow_score)) ? Number(semanticDecision.top_shadow_score) : null,
      phrase_preempted: semanticDecision ? semanticDecision.phrase_preempted === true : false
    };
  }

  function copySemanticDecision(semanticDecision) {
    if (!semanticDecision) {
      return null;
    }
    return {
      decision: String(semanticDecision.decision || ""),
      decision_source: String(semanticDecision.decision_source || ""),
      effective_decision: String(semanticDecision.effective_decision || ""),
      effective_decision_source: String(semanticDecision.effective_decision_source || ""),
      debug_override: String(semanticDecision.debug_override || ""),
      debug_original_decision: String(semanticDecision.debug_original_decision || ""),
      debug_original_decision_source: String(semanticDecision.debug_original_decision_source || ""),
      reason_codes: normalizeSemanticReasonCodes(semanticDecision.reason_codes),
      sense_id: String(semanticDecision.sense_id || ""),
      competition_set_id: String(semanticDecision.competition_set_id || ""),
      score_margin: Number.isFinite(Number(semanticDecision.score_margin)) ? Number(semanticDecision.score_margin) : null,
      active_score: Number.isFinite(Number(semanticDecision.active_score)) ? Number(semanticDecision.active_score) : null,
      top_shadow_score: Number.isFinite(Number(semanticDecision.top_shadow_score)) ? Number(semanticDecision.top_shadow_score) : null,
      phrase_preempted: semanticDecision.phrase_preempted === true
    };
  }

  function applySemanticDebugMetadata(span, metadata) {
    if (!span || !metadata || typeof metadata !== "object") {
      return;
    }
    const mappings = [["status", "semanticStatus"], ["decision", "semanticDecision"], ["decision_source", "semanticDecisionSource"], ["effective_decision", "semanticEffectiveDecision"], ["effective_decision_source", "semanticEffectiveDecisionSource"], ["debug_override", "semanticDebugOverride"], ["debug_original_decision", "semanticDebugOriginalDecision"], ["debug_original_decision_source", "semanticDebugOriginalDecisionSource"], ["sense_id", "semanticSenseId"], ["competition_set_id", "semanticCompetitionSetId"], ["phrase_set_id", "semanticPhraseSetId"], ["trigger_id", "semanticTriggerId"]];
    for (const [sourceKey, datasetKey] of mappings) {
      if (metadata[sourceKey]) {
        span.dataset[datasetKey] = String(metadata[sourceKey]);
      }
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

  function createReplacementSpan(originalText, displayPayload, rule, highlightEnabled, origin, debugMetadata) {
    const payload = displayPayload && typeof displayPayload === "object"
      ? displayPayload
      : {
          canonicalReplacement: String((rule && rule.replacement) || ""),
          displayReplacement: String((rule && rule.replacement) || ""),
          displayScript: "",
          scriptForms: null,
          wordPackage: null
        };
    const span = document.createElement("span");
    span.className = "lexishift-replacement";
    if (highlightEnabled) {
      span.classList.add("lexishift-highlight");
    }
    span.textContent = payload.displayReplacement;
    span.dataset.original = originalText;
    span.dataset.replacement = payload.canonicalReplacement;
    span.dataset.displayReplacement = payload.displayReplacement;
    span.dataset.displayScript = payload.displayScript || "";
    span.dataset.state = "replacement";
    if (payload.scriptForms) {
      span.dataset.scriptForms = JSON.stringify(payload.scriptForms);
      span.dataset.hasScriptVariants = Object.keys(payload.scriptForms).length > 1 ? "true" : "false";
    }
    if (payload.wordPackage) {
      span.dataset.wordPackage = JSON.stringify(payload.wordPackage);
      if (payload.wordPackage.language_tag) {
        span.dataset.languageTag = String(payload.wordPackage.language_tag);
      }
    }
    if (origin) {
      const normalizedOrigin = String(origin).trim().toLowerCase();
      span.dataset.origin = normalizedOrigin;
      if (normalizedOrigin === RULE_ORIGIN_SRS) {
        span.classList.add("lexishift-srs");
      }
    }
    if (rule) {
      if (rule.source_phrase) {
        span.dataset.source = String(rule.source_phrase);
      }
      if (rule.metadata && rule.metadata.language_pair) {
        span.dataset.languagePair = String(rule.metadata.language_pair);
      }
    }
    const metadata = debugMetadata && typeof debugMetadata === "object" ? debugMetadata : null;
    if (metadata) {
      applySemanticDebugMetadata(span, metadata);
    }

    let tooltip = "Click to toggle original";
    if (payload.scriptForms && Object.keys(payload.scriptForms).length > 1) {
      tooltip = "Click to toggle original. Right-click (or Ctrl+Click on macOS) for details and feedback.";
    }
    if (rule && rule.metadata && rule.metadata.description) {
      tooltip = `${rule.metadata.description}\n\n(Original: ${originalText})`;
      if (payload.scriptForms && Object.keys(payload.scriptForms).length > 1) {
        tooltip += "\n(Right-click or Ctrl+Click on macOS for details and feedback.)";
      }
    }
    span.title = tooltip;
    return span;
  }

  function normalizeWhitespace(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function buildContextExcerpt(text, focusText) {
    const normalizedText = normalizeWhitespace(text);
    if (!normalizedText) {
      return "";
    }
    const words = normalizedText.split(" ").filter(Boolean);
    if (!words.length) {
      return "";
    }
    let focusWordIndex = 0;
    const focus = normalizeWhitespace(focusText);
    if (focus) {
      const loweredText = normalizedText.toLowerCase();
      const loweredFocus = focus.toLowerCase();
      const charIndex = loweredText.indexOf(loweredFocus);
      if (charIndex >= 0) {
        const before = loweredText.slice(0, charIndex).trim();
        focusWordIndex = before ? before.split(/\s+/).length : 0;
      }
    }
    const halfWindow = Math.floor(MAX_CONTEXT_WORDS / 2);
    let start = Math.max(0, focusWordIndex - halfWindow);
    let end = Math.min(words.length, start + MAX_CONTEXT_WORDS);
    if (end - start < MAX_CONTEXT_WORDS) {
      start = Math.max(0, end - MAX_CONTEXT_WORDS);
    }
    const excerptWords = words.slice(start, end);
    if (!excerptWords.length) {
      return "";
    }
    return `... ${excerptWords.join(" ")} ...`;
  }

  async function buildReplacementFragment(
    text,
    trie,
    settings,
    onTextNode,
    originResolver,
    budget,
    semanticGateRuntime
  ) {
    const trackDetails = settings.debugEnabled === true;
    const details = trackDetails ? [] : null;
    const budgetKeys = budget ? [] : null;
    const tokens = tokenize(text);
    const wordPositions = [];
    const wordTexts = [];
    tokens.forEach((token, idx) => {
      if (token.kind === "word") {
        wordPositions.push(idx);
        wordTexts.push(token.text);
      }
    });
    if (!wordPositions.length) {
      return null;
    }
    const gapOk = computeGapOk(tokens, wordPositions);
    const matches = [];
    let wordIndex = 0;
    while (wordIndex < wordTexts.length) {
      const match = findLongestMatch(trie, wordTexts, gapOk, wordIndex);
      if (match) {
        matches.push(match);
        wordIndex = match.endWordIndex + 1;
      } else {
        wordIndex += 1;
      }
    }

    const selectionSeed = createSelectionSeed(text, settings);
    let finalMatches = filterMatchesByPolicy(matches, settings, gapOk, budget, selectionSeed);
    let semanticDecisionMap = null;
    let semanticSummary = null;
    if (
      semanticGateRuntime
      && typeof semanticGateRuntime.admitMatches === "function"
      && finalMatches.length
    ) {
      const semanticResult = await semanticGateRuntime.admitMatches({
        text,
        tokens,
        wordPositions,
        matches: finalMatches,
        settings
      });
      if (semanticResult && Array.isArray(semanticResult.matches)) {
        finalMatches = semanticResult.matches;
        semanticDecisionMap = semanticResult.decisionMap instanceof Map
          ? semanticResult.decisionMap
          : null;
        semanticSummary = semanticResult.summary && typeof semanticResult.summary === "object"
          ? semanticResult.summary
          : null;
      }
    }
    if (!finalMatches.length) {
      if (!semanticSummary) {
        return null;
      }
      return {
        fragment: null,
        replacements: 0,
        details,
        budgetKeys,
        semanticSummary
      };
    }

    const fragment = document.createDocumentFragment();
    let tokenCursor = 0;
    for (const match of finalMatches) {
      const startTokenIdx = wordPositions[match.startWordIndex];
      const endTokenIdx = wordPositions[match.endWordIndex];
      if (startTokenIdx > tokenCursor) {
        const chunk = tokens.slice(tokenCursor, startTokenIdx).map((t) => t.text).join("");
        if (chunk) {
          const textNode = document.createTextNode(chunk);
          fragment.appendChild(textNode);
          if (onTextNode) onTextNode(textNode);
        }
      }
      const sourceWords = wordTexts.slice(match.startWordIndex, match.endWordIndex + 1);
      const originalText = tokens.slice(startTokenIdx, endTokenIdx + 1).map((t) => t.text).join("");
      const displayPayload = resolveDisplayPayload(match.rule, sourceWords, settings);
      const origin = originResolver
        ? originResolver(match.rule, displayPayload.displayReplacement)
        : null;
      const semanticDecision = semanticDecisionMap ? semanticDecisionMap.get(match) : null;
      const semanticAdmission = (
        match.rule
        && match.rule.metadata
        && typeof match.rule.metadata === "object"
        && match.rule.metadata.semantic_admission
        && typeof match.rule.metadata.semantic_admission === "object"
      )
        ? match.rule.metadata.semantic_admission
        : null;
      const semanticDebugMetadata = settings.debugEnabled === true
        ? buildSemanticDebugMetadata(semanticAdmission, semanticDecision)
        : null;
      if (budgetKeys) {
        budgetKeys.push(displayPayload.canonicalReplacement);
      }
      fragment.appendChild(createReplacementSpan(
        originalText,
        displayPayload,
        match.rule,
        settings.highlightEnabled,
        origin,
        semanticDebugMetadata
      ));
      if (details) {
        details.push({
          original: originalText,
          replacement: displayPayload.canonicalReplacement,
          display_replacement: displayPayload.displayReplacement,
          context_excerpt: buildContextExcerpt(text, originalText),
          display_script: displayPayload.displayScript || "",
          origin: origin || "ruleset",
          source: match.rule.source_phrase || "",
          priority: match.rule.priority,
          case_policy: match.rule.case_policy || "match",
          language_pair: match.rule.metadata ? match.rule.metadata.language_pair : "",
          language_tag: displayPayload.wordPackage
            ? String(displayPayload.wordPackage.language_tag || "")
            : "",
          word_package: displayPayload.wordPackage || null,
          semantic_decision: copySemanticDecision(semanticDecision)
        });
      }
      tokenCursor = endTokenIdx + 1;
    }
    if (tokenCursor < tokens.length) {
      const tail = tokens.slice(tokenCursor).map((t) => t.text).join("");
      if (tail) {
        const textNode = document.createTextNode(tail);
        fragment.appendChild(textNode);
        if (onTextNode) onTextNode(textNode);
      }
    }
    return {
      fragment,
      replacements: finalMatches.length,
      details,
      budgetKeys,
      semanticSummary
    };
  }

  root.replacements = { buildReplacementFragment, createReplacementSpan };
})();
