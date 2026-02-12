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

  function resolveDisplayPayload(rule, sourceWords, settings) {
    const casePolicy = (rule && rule.case_policy) || "match";
    const canonicalReplacement = String((rule && rule.replacement) || "").trim();
    const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    const languagePair = String(metadata.language_pair || "").trim();
    const targetLanguage = targetLanguageFromPair(languagePair)
      || String((settings && settings.targetLanguage) || "").trim().toLowerCase();
    const scriptForms = normalizeScriptForms(metadata.script_forms);

    if (targetLanguage !== "ja" || !scriptForms) {
      return {
        canonicalReplacement,
        displayReplacement: applyCase(canonicalReplacement, sourceWords, casePolicy),
        displayScript: "",
        scriptForms: null
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
      scriptForms: caseAdjustedForms
    };
  }

  function createReplacementSpan(originalText, displayPayload, rule, highlightEnabled, origin) {
    const payload = displayPayload && typeof displayPayload === "object"
      ? displayPayload
      : {
          canonicalReplacement: String((rule && rule.replacement) || ""),
          displayReplacement: String((rule && rule.replacement) || ""),
          displayScript: "",
          scriptForms: null
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

  function applyPageBudget(matches, budget) {
    if (!budget || !matches.length) {
      return matches;
    }
    const maxTotal = Number.isFinite(Number(budget.maxTotal)) ? Math.max(0, Number(budget.maxTotal)) : 0;
    const maxPerLemma = Number.isFinite(Number(budget.maxPerLemma)) ? Math.max(0, Number(budget.maxPerLemma)) : 0;
    const bounded = [];
    const localByLemma = Object.create(null);
    let usedTotal = Number.isFinite(Number(budget.usedTotal)) ? Number(budget.usedTotal) : 0;

    for (const match of matches) {
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
    return bounded;
  }

  function filterMatches(matches, settings, gapOk, budget) {
    if (!matches.length) {
      return matches;
    }
    let filtered = matches;
    if (settings.maxOnePerTextBlock) {
      filtered = filtered.slice(0, 1);
    }
    if (settings.allowAdjacentReplacements === false) {
      const nonAdjacent = [];
      let lastEnd = null;
      for (const match of filtered) {
        if (lastEnd !== null && match.startWordIndex === lastEnd + 1 && gapOk[lastEnd]) {
          continue;
        }
        nonAdjacent.push(match);
        lastEnd = match.endWordIndex;
      }
      filtered = nonAdjacent;
    }
    return applyPageBudget(filtered, budget);
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

    const finalMatches = filterMatches(matches, settings, gapOk, budget);
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
          language_pair: match.rule.metadata ? match.rule.metadata.language_pair : ""
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
