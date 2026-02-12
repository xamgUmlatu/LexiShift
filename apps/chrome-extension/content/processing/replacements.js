(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { tokenize, computeGapOk } = root.tokenizer || {};
  const { findLongestMatch, applyCase } = root.matcher || {};
  const RULE_ORIGIN_SRS = "srs";
  const MAX_CONTEXT_WORDS = 15;

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
    const canonicalReplacement = String((rule && rule.replacement) || "").trim();
    const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
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
        displayReplacement: applyCase(canonicalReplacement, sourceWords, casePolicy),
        displayScript: "",
        scriptForms: null,
        wordPackage: effectiveWordPackage
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
      wordPackage: effectiveWordPackage
    };
  }

  function createReplacementSpan(originalText, displayPayload, rule, highlightEnabled, origin) {
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

  function getBudgetLemmaKey(match) {
    if (!match || !match.rule) {
      return "";
    }
    return String(match.rule.replacement || "").trim().toLowerCase();
  }

  function getBudgetUsageForLemma(budget, key) {
    if (!budget || !budget.usedByLemma || !key) {
      return 0;
    }
    return Number(budget.usedByLemma[key] || 0);
  }

  function hash32(value) {
    const text = String(value || "");
    let hash = 0x811c9dc5;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 0x01000193);
    }
    return hash >>> 0;
  }

  function mix32(value) {
    let mixed = Number(value) >>> 0;
    mixed ^= mixed >>> 16;
    mixed = Math.imul(mixed, 0x7feb352d);
    mixed ^= mixed >>> 15;
    mixed = Math.imul(mixed, 0x846ca68b);
    mixed ^= mixed >>> 16;
    return mixed >>> 0;
  }

  function getPageSeed(settings) {
    let locationKey = "";
    try {
      if (globalThis.location) {
        locationKey = `${globalThis.location.origin || ""}${globalThis.location.pathname || ""}`;
      }
    } catch (_error) {
      locationKey = "";
    }
    const profileId = String(settings && settings.srsProfileId || "").trim();
    return hash32(`${locationKey}|${profileId}`);
  }

  function createSelectionSeed(text, settings) {
    const pageSeed = getPageSeed(settings);
    const textSeed = hash32(text);
    return mix32(pageSeed ^ textSeed ^ 0x9e3779b9);
  }

  function computeMatchScore(match, selectionSeed, ordinal) {
    const rule = match && match.rule && typeof match.rule === "object" ? match.rule : {};
    const metadata = rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    const ruleSeed = hash32(
      `${rule.source_phrase || ""}|${rule.replacement || ""}|${metadata.language_pair || ""}|${metadata.lexishift_origin || ""}`
    );
    let mixed = selectionSeed ^ ruleSeed;
    mixed ^= Math.imul((Number(match.startWordIndex) + 1) >>> 0, 0x9e3779b1);
    mixed ^= Math.imul((Number(match.endWordIndex) + 1) >>> 0, 0x85ebca6b);
    mixed ^= Math.imul((ordinal + 1) >>> 0, 0xc2b2ae35);
    return mix32(mixed);
  }

  function rankMatchesDeterministically(matches, selectionSeed) {
    return matches
      .map((match, ordinal) => ({
        match,
        ordinal,
        score: computeMatchScore(match, selectionSeed, ordinal)
      }))
      .sort((a, b) => {
        if (a.score !== b.score) {
          return a.score - b.score;
        }
        return a.ordinal - b.ordinal;
      })
      .map((entry) => entry.match);
  }

  function sortMatchesByStart(matches) {
    return [...matches].sort((left, right) => {
      const startDiff = Number(left.startWordIndex || 0) - Number(right.startWordIndex || 0);
      if (startDiff !== 0) {
        return startDiff;
      }
      return Number(left.endWordIndex || 0) - Number(right.endWordIndex || 0);
    });
  }

  function applyPageBudget(matches, budget, selectionSeed) {
    if (!budget || !matches.length) {
      return matches;
    }
    const maxTotal = Number.isFinite(Number(budget.maxTotal)) ? Math.max(0, Number(budget.maxTotal)) : 0;
    const maxPerLemma = Number.isFinite(Number(budget.maxPerLemma)) ? Math.max(0, Number(budget.maxPerLemma)) : 0;
    if (maxTotal <= 0 && maxPerLemma <= 0) {
      return matches;
    }
    const ranked = rankMatchesDeterministically(matches, mix32(selectionSeed ^ 0x6d2b79f5));
    const bounded = [];
    const localByLemma = Object.create(null);
    let usedTotal = Number.isFinite(Number(budget.usedTotal)) ? Number(budget.usedTotal) : 0;

    for (const match of ranked) {
      if (maxTotal > 0 && usedTotal >= maxTotal) {
        break;
      }
      const key = getBudgetLemmaKey(match);
      if (maxPerLemma > 0 && key) {
        const used = getBudgetUsageForLemma(budget, key) + Number(localByLemma[key] || 0);
        if (used >= maxPerLemma) {
          continue;
        }
        localByLemma[key] = Number(localByLemma[key] || 0) + 1;
      }
      bounded.push(match);
      usedTotal += 1;
    }
    return sortMatchesByStart(bounded);
  }

  function chooseSingleMatch(matches, selectionSeed) {
    if (matches.length <= 1) {
      return matches;
    }
    const ranked = rankMatchesDeterministically(matches, mix32(selectionSeed ^ 0x27d4eb2d));
    return ranked.length ? [ranked[0]] : [];
  }

  function chooseNonAdjacentMatches(matches, gapOk, selectionSeed) {
    if (matches.length <= 1) {
      return matches;
    }
    const chosen = [];
    let cluster = [];
    let lastEnd = null;
    let clusterIndex = 0;

    function flushCluster() {
      if (!cluster.length) {
        return;
      }
      if (cluster.length === 1) {
        chosen.push(cluster[0]);
      } else {
        const clusterSeed = mix32(
          selectionSeed ^ Math.imul((clusterIndex + 1) >>> 0, 0x9e3779b1)
        );
        const rankedCluster = rankMatchesDeterministically(cluster, clusterSeed);
        if (rankedCluster.length) {
          chosen.push(rankedCluster[0]);
        }
      }
      cluster = [];
      clusterIndex += 1;
    }

    for (const match of matches) {
      if (!cluster.length) {
        cluster.push(match);
        lastEnd = match.endWordIndex;
        continue;
      }
      const adjacent = lastEnd !== null
        && match.startWordIndex === lastEnd + 1
        && gapOk[lastEnd];
      if (adjacent) {
        cluster.push(match);
      } else {
        flushCluster();
        cluster.push(match);
      }
      lastEnd = match.endWordIndex;
    }
    flushCluster();
    return sortMatchesByStart(chosen);
  }

  function filterMatches(matches, settings, gapOk, budget, selectionSeed) {
    if (!matches.length) {
      return matches;
    }
    let filtered = matches;
    if (settings.maxOnePerTextBlock) {
      filtered = chooseSingleMatch(filtered, selectionSeed);
    }
    if (settings.allowAdjacentReplacements === false) {
      filtered = chooseNonAdjacentMatches(filtered, gapOk, selectionSeed);
    }
    return applyPageBudget(filtered, budget, selectionSeed);
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

  function buildReplacementFragment(text, trie, settings, onTextNode, originResolver, budget) {
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
    const finalMatches = filterMatches(matches, settings, gapOk, budget, selectionSeed);
    if (!finalMatches.length) {
      return null;
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
      if (budgetKeys) {
        budgetKeys.push(displayPayload.canonicalReplacement);
      }
      fragment.appendChild(
        createReplacementSpan(originalText, displayPayload, match.rule, settings.highlightEnabled, origin)
      );
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
          word_package: displayPayload.wordPackage || null
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
    return { fragment, replacements: finalMatches.length, details, budgetKeys };
  }

  root.replacements = { buildReplacementFragment, createReplacementSpan };
})();
