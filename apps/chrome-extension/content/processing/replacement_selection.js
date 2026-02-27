(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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

  root.replacementSelection = {
    createSelectionSeed,
    filterMatches
  };
})();
