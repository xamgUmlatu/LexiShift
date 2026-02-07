(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { tokenize, computeGapOk } = root.tokenizer || {};
  const { findLongestMatch, applyCase } = root.matcher || {};

  function createReplacementSpan(originalText, replacementText, rule, highlightEnabled, origin) {
    const span = document.createElement("span");
    span.className = "lexishift-replacement";
    if (highlightEnabled) {
      span.classList.add("lexishift-highlight");
    }
    span.textContent = replacementText;
    span.dataset.original = originalText;
    span.dataset.replacement = replacementText;
    span.dataset.state = "replacement";
    if (origin) {
      span.dataset.origin = origin;
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
    if (rule && rule.metadata && rule.metadata.description) {
      tooltip = `${rule.metadata.description}\n\n(Original: ${originalText})`;
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
      const replacementText = applyCase(match.rule.replacement, sourceWords, match.rule.case_policy || "match");
      const origin = originResolver ? originResolver(match.rule, replacementText) : null;
      if (budgetKeys) {
        budgetKeys.push(replacementText);
      }
      fragment.appendChild(
        createReplacementSpan(originalText, replacementText, match.rule, settings.highlightEnabled, origin)
      );
      if (details) {
        details.push({
          original: originalText,
          replacement: replacementText,
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
