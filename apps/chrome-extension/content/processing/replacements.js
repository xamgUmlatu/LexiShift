(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { tokenize, computeGapOk } = root.tokenizer || {};
  const { findLongestMatch, applyCase } = root.matcher || {};
  const replacementSelection = root.replacementSelection || {};
  const semanticDebug = root.replacementSemanticDebug || {
    applyToSpan: () => {},
    buildMetadata: () => null,
    copyDecision: () => null
  };
  const semanticOverride = root.replacementSemanticOverride || {
    buildDecisionBySignature: () => new Map(),
    buildResultOverride: () => ({ allowedMatchSignatures: new Set(), decisionBySignature: new Map() }),
    getAdmission: () => null,
    getMatchSignature: () => "",
    normalizeResultOverride: () => null
  };
  const RULE_ORIGIN_SRS = "srs";
  const assignSentenceKeys = typeof replacementSelection.assignSentenceKeys === "function"
    ? replacementSelection.assignSentenceKeys
    : ((matches) => matches);
  const createSelectionSeed = typeof replacementSelection.createSelectionSeed === "function"
    ? replacementSelection.createSelectionSeed
    : (() => 0);
  const filterMatchesByPolicy = typeof replacementSelection.filterMatches === "function"
    ? replacementSelection.filterMatches
    : ((matches) => matches);
  const buildContextExcerpt = typeof semanticDebug.buildContextExcerpt === "function"
    ? semanticDebug.buildContextExcerpt
    : (() => "");

  function translateMessage(key, substitutions, fallback) {
    try {
      if (typeof chrome !== "undefined"
        && chrome.i18n
        && typeof chrome.i18n.getMessage === "function") {
        const message = chrome.i18n.getMessage(key, substitutions);
        if (message) {
          return message;
        }
      }
    } catch (_error) {
      // Ignore i18n runtime errors and use the stable fallback text.
    }
    return String(fallback || "");
  }

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
    span.dataset.lexishiftScanSkip = "true";
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
      semanticDebug.applyToSpan(span, metadata);
    }

    const toggleTooltip = translateMessage(
      "replacement_tooltip_toggle_original",
      null,
      "Click to toggle original"
    );
    const detailsTooltip = translateMessage(
      "replacement_tooltip_details_feedback",
      null,
      "Right-click (or Ctrl+Click on macOS) for details and feedback."
    );
    const toggleWithDetailsTooltip = translateMessage(
      "replacement_tooltip_toggle_original_with_details",
      null,
      `${toggleTooltip}. ${detailsTooltip}`
    );
    const originalTooltip = translateMessage(
      "replacement_tooltip_original",
      [originalText],
      `Original: ${originalText}`
    );
    let tooltip = toggleTooltip;
    if (payload.scriptForms && Object.keys(payload.scriptForms).length > 1) {
      tooltip = toggleWithDetailsTooltip;
    }
    if (rule && rule.metadata && rule.metadata.description) {
      tooltip = `${rule.metadata.description}\n\n(${originalTooltip})`;
      if (payload.scriptForms && Object.keys(payload.scriptForms).length > 1) {
        tooltip += `\n(${detailsTooltip})`;
      }
    }
    span.title = tooltip;
    return span;
  }

  async function buildReplacementFragment(
    text,
    trie,
    settings,
    onTextNode,
    originResolver,
    budget,
    semanticGateRuntime, semanticContextResolver, options
  ) {
    const buildOptions = options && typeof options === "object" ? options : {};
    const dryRun = buildOptions.dryRun === true;
    const semanticResultOverride = semanticOverride.normalizeResultOverride(buildOptions.semanticResultOverride);
    const trackDetails = settings.debugEnabled === true;
    const details = trackDetails ? [] : null;
    const budgetKeys = budget ? [] : null;
    const budgetEntries = budget ? [] : null;
    const budgetRejections = budget
      ? { page: 0, sentence: 0, lemma: 0 }
      : null;
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
    let finalMatches = matches;
    let semanticDecisionMap = null;
    let semanticDecisionBySignature = semanticResultOverride
      ? semanticResultOverride.decisionBySignature
      : null;
    let semanticSummary = null;
    if (semanticResultOverride) {
      finalMatches = finalMatches.filter((match) =>
        semanticResultOverride.allowedMatchSignatures.has(semanticOverride.getMatchSignature(match))
      );
    } else if (
      semanticGateRuntime
      && typeof semanticGateRuntime.admitMatches === "function"
      && finalMatches.length
    ) {
      const semanticResult = await semanticGateRuntime.admitMatches({
        text,
        tokens,
        wordPositions,
        matches: finalMatches,
        settings, semanticContextResolver
      });
      if (semanticResult && Array.isArray(semanticResult.matches)) {
        finalMatches = semanticResult.matches;
        semanticDecisionMap = semanticResult.decisionMap instanceof Map
          ? semanticResult.decisionMap
          : null;
        semanticDecisionBySignature = semanticOverride.buildDecisionBySignature(semanticDecisionMap);
        semanticSummary = semanticResult.summary && typeof semanticResult.summary === "object"
          ? semanticResult.summary
          : null;
      }
    }
    if (dryRun) {
      return {
        fragment: null,
        replacements: finalMatches.length,
        details,
        budgetKeys,
        semanticSummary,
        semanticResultOverride: semanticOverride.buildResultOverride(finalMatches, semanticDecisionMap)
      };
    }
    if (budget && Number(budget.maxPerSentence || 0) > 0) {
      assignSentenceKeys(
        finalMatches,
        tokens,
        wordPositions,
        semanticContextResolver,
        buildOptions.sentenceFallbackKey
      );
    }
    finalMatches = filterMatchesByPolicy(
      finalMatches,
      settings,
      gapOk,
      budget,
      selectionSeed,
      budgetRejections
    );
    if (!finalMatches.length) {
      const hasBudgetRejections = budgetRejections && (
        budgetRejections.page > 0
        || budgetRejections.sentence > 0
        || budgetRejections.lemma > 0
      );
      if (!semanticSummary && !hasBudgetRejections) {
        return null;
      }
      return {
        fragment: null,
        replacements: 0,
        details,
        budgetKeys,
        budgetRejections,
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
      const semanticDecision = semanticDecisionMap
        ? semanticDecisionMap.get(match)
        : (semanticDecisionBySignature
          ? semanticDecisionBySignature.get(semanticOverride.getMatchSignature(match))
          : null);
      const semanticAdmission = semanticOverride.getAdmission(match.rule);
      const semanticDebugMetadata = settings.debugEnabled === true
        ? semanticDebug.buildMetadata(semanticAdmission, semanticDecision)
        : null;
      if (budgetKeys) {
        budgetKeys.push(displayPayload.canonicalReplacement);
      }
      if (budgetEntries) {
        budgetEntries.push({
          lemma: displayPayload.canonicalReplacement,
          sentenceKey: String(match.sentenceKey || "").trim()
        });
      }
      const replacementSpan = createReplacementSpan(
        originalText,
        displayPayload,
        match.rule,
        settings.highlightEnabled,
        origin,
        semanticDebugMetadata
      );
      if (match.sentenceKey) {
        replacementSpan.dataset.sentenceKey = String(match.sentenceKey);
      }
      fragment.appendChild(replacementSpan);
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
          sentence_key: String(match.sentenceKey || ""),
          semantic_decision: semanticDebug.copyDecision(semanticDecision)
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
      budgetEntries,
      budgetRejections,
      semanticSummary
    };
  }

  root.replacements = { buildReplacementFragment, createReplacementSpan };
})();
