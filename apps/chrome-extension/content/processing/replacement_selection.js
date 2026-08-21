(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const RULE_ORIGIN_SRS = "srs";
  const SRS_MATURE_STABILITY_DAYS = 14;
  const SRS_LONG_STABILITY_DAYS = 28;

  function buildTokenOffsets(tokens) {
    const offsets = [];
    let cursor = 0;
    for (const token of tokens || []) {
      offsets.push(cursor);
      cursor += String(token && token.text || "").length;
    }
    return offsets;
  }

  function assignSentenceKeys(
    matches,
    tokens,
    wordPositions,
    semanticContextResolver,
    fallbackKey
  ) {
    const list = Array.isArray(matches) ? matches : [];
    const normalizedFallback = String(fallbackKey || "").trim();
    if (!list.length) return list;
    const tokenOffsets = buildTokenOffsets(tokens);
    for (const match of list) {
      const startTokenIdx = Number(wordPositions[match.startWordIndex]);
      const endTokenIdx = Number(wordPositions[match.endWordIndex]);
      const matchStart = Number.isFinite(startTokenIdx)
        ? Number(tokenOffsets[startTokenIdx] || 0)
        : 0;
      const endToken = tokens[endTokenIdx] && typeof tokens[endTokenIdx] === "object"
        ? tokens[endTokenIdx]
        : { text: "" };
      const matchEnd = Number.isFinite(endTokenIdx)
        ? Number(tokenOffsets[endTokenIdx] || matchStart) + String(endToken.text || "").length
        : matchStart;
      let resolved = null;
      if (typeof semanticContextResolver === "function" && matchEnd > matchStart) {
        try {
          resolved = semanticContextResolver({ match, matchStart, matchEnd });
        } catch (_error) {
          resolved = null;
        }
      }
      match.sentenceKey = String(resolved && resolved.sentenceKey || normalizedFallback).trim();
    }
    return list;
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

  function getBudgetSentenceKey(match) {
    return String(match && match.sentenceKey || "").trim();
  }

  function getBudgetUsageForSentence(budget, key) {
    if (!budget || !budget.usedBySentence || !key) {
      return 0;
    }
    return Number(budget.usedBySentence[key] || 0);
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

  function getRuleMetadata(match) {
    const rule = match && match.rule && typeof match.rule === "object" ? match.rule : null;
    return rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : null;
  }

  function getRuleOrigin(match) {
    const metadata = getRuleMetadata(match);
    return String(metadata && metadata.lexishift_origin || "").trim().toLowerCase();
  }

  function getSrsServingMetadata(match) {
    const metadata = getRuleMetadata(match);
    if (!metadata) {
      return null;
    }
    const rulegen = metadata.rulegen && typeof metadata.rulegen === "object"
      ? metadata.rulegen
      : null;
    const srs = rulegen && rulegen.srs && typeof rulegen.srs === "object"
      ? rulegen.srs
      : null;
    if (srs) {
      return srs;
    }
    if (
      Object.prototype.hasOwnProperty.call(metadata, "next_due")
      || Object.prototype.hasOwnProperty.call(metadata, "in_due")
    ) {
      return metadata;
    }
    return null;
  }

  function finiteNumber(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function normalizeSrsState(value) {
    return String(value || "").trim().toLowerCase().replace(/-/g, "_");
  }

  function isFutureDue(srs, nowMs) {
    if (!srs || typeof srs !== "object") {
      return false;
    }
    const nextDue = String(srs.next_due || srs.nextDue || "").trim();
    if (nextDue) {
      const parsed = Date.parse(nextDue);
      if (!Number.isNaN(parsed)) {
        return parsed > nowMs;
      }
    }
    if (typeof srs.in_due === "boolean") {
      return !srs.in_due;
    }
    if (typeof srs.inDue === "boolean") {
      return !srs.inDue;
    }
    return false;
  }

  function getReplacementLoadTier(match, nowMs) {
    if (getRuleOrigin(match) !== RULE_ORIGIN_SRS) {
      return 40;
    }
    const srs = getSrsServingMetadata(match);
    if (!srs) {
      return 30;
    }
    if (isFutureDue(srs, nowMs)) {
      return 80;
    }
    const state = normalizeSrsState(srs.scheduler_state || srs.schedulerState);
    if (!state || state === "new" || state === "learning" || state === "relearning") {
      return 0;
    }
    if (state === "review") {
      const stability = finiteNumber(srs.stability);
      if (stability !== null && stability >= SRS_LONG_STABILITY_DAYS) {
        return 24;
      }
      if (stability !== null && stability >= SRS_MATURE_STABILITY_DAYS) {
        return 18;
      }
      return 8;
    }
    return 12;
  }

  function getReplacementLoadNowMs(settings) {
    const injected = finiteNumber(settings && settings.srsReplacementNowMs);
    return injected === null ? Date.now() : injected;
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

  function rankMatchesForReplacementLoad(matches, selectionSeed, settings) {
    const nowMs = getReplacementLoadNowMs(settings);
    return matches
      .map((match, ordinal) => ({
        match,
        ordinal,
        loadTier: getReplacementLoadTier(match, nowMs),
        score: computeMatchScore(match, selectionSeed, ordinal)
      }))
      .sort((a, b) => {
        if (a.loadTier !== b.loadTier) {
          return a.loadTier - b.loadTier;
        }
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

  function recordBudgetRejection(diagnostics, reason, count = 1) {
    if (!diagnostics || !reason || count <= 0) {
      return;
    }
    diagnostics[reason] = Number(diagnostics[reason] || 0) + count;
  }

  function applyReplacementBudget(matches, budget, selectionSeed, settings, diagnostics) {
    if (!budget || !matches.length) {
      return matches;
    }
    const maxTotal = Number.isFinite(Number(budget.maxTotal)) ? Math.max(0, Number(budget.maxTotal)) : 0;
    const maxPerLemma = Number.isFinite(Number(budget.maxPerLemma)) ? Math.max(0, Number(budget.maxPerLemma)) : 0;
    const maxPerSentence = Number.isFinite(Number(budget.maxPerSentence))
      ? Math.max(0, Number(budget.maxPerSentence))
      : 0;
    if (maxTotal <= 0 && maxPerLemma <= 0 && maxPerSentence <= 0) {
      return matches;
    }
    const ranked = rankMatchesForReplacementLoad(
      matches,
      mix32(selectionSeed ^ 0x6d2b79f5),
      settings
    );
    const bounded = [];
    const localByLemma = Object.create(null);
    const localBySentence = Object.create(null);
    let usedTotal = Number.isFinite(Number(budget.usedTotal)) ? Number(budget.usedTotal) : 0;

    for (let index = 0; index < ranked.length; index += 1) {
      const match = ranked[index];
      if (maxTotal > 0 && usedTotal >= maxTotal) {
        recordBudgetRejection(diagnostics, "page", ranked.length - index);
        break;
      }
      const key = getBudgetLemmaKey(match);
      if (maxPerLemma > 0 && key) {
        const used = getBudgetUsageForLemma(budget, key) + Number(localByLemma[key] || 0);
        if (used >= maxPerLemma) {
          recordBudgetRejection(diagnostics, "lemma");
          continue;
        }
      }
      const sentenceKey = getBudgetSentenceKey(match);
      if (maxPerSentence > 0 && sentenceKey) {
        const used = getBudgetUsageForSentence(budget, sentenceKey)
          + Number(localBySentence[sentenceKey] || 0);
        if (used >= maxPerSentence) {
          recordBudgetRejection(diagnostics, "sentence");
          continue;
        }
      }
      if (maxPerLemma > 0 && key) {
        localByLemma[key] = Number(localByLemma[key] || 0) + 1;
      }
      if (maxPerSentence > 0 && sentenceKey) {
        localBySentence[sentenceKey] = Number(localBySentence[sentenceKey] || 0) + 1;
      }
      bounded.push(match);
      usedTotal += 1;
    }
    return sortMatchesByStart(bounded);
  }

  function chooseSingleMatch(matches, selectionSeed, settings) {
    if (matches.length <= 1) {
      return matches;
    }
    const ranked = rankMatchesForReplacementLoad(
      matches,
      mix32(selectionSeed ^ 0x27d4eb2d),
      settings
    );
    return ranked.length ? [ranked[0]] : [];
  }

  function chooseNonAdjacentMatches(matches, gapOk, selectionSeed, settings) {
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
        const rankedCluster = rankMatchesForReplacementLoad(cluster, clusterSeed, settings);
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

  function filterMatches(matches, settings, gapOk, budget, selectionSeed, budgetDiagnostics) {
    if (!matches.length) {
      return matches;
    }
    let filtered = matches;
    if (settings.maxOnePerTextBlock) {
      filtered = chooseSingleMatch(filtered, selectionSeed, settings);
    }
    if (settings.allowAdjacentReplacements === false) {
      filtered = chooseNonAdjacentMatches(filtered, gapOk, selectionSeed, settings);
    }
    return applyReplacementBudget(filtered, budget, selectionSeed, settings, budgetDiagnostics);
  }

  root.replacementSelection = {
    assignSentenceKeys,
    createSelectionSeed,
    getReplacementLoadTier,
    applyReplacementBudget,
    filterMatches
  };
})();
