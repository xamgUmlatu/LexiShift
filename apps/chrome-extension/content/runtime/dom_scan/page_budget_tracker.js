(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function countKeysAtLimit(value, limit) {
    if (!value || typeof value !== "object" || Number(limit || 0) <= 0) return 0;
    return Object.values(value).filter((count) => Number(count || 0) >= Number(limit)).length;
  }

  function attachReplacementBudgetSummary(counter, state) {
    if (!counter || typeof counter !== "object") return counter;
    const budget = state && typeof state === "object" ? state : null;
    const maxTotal = budget ? Number(budget.maxTotal || 0) : 0;
    const maxPerSentence = budget ? Number(budget.maxPerSentence || 0) : 0;
    const maxPerLemma = budget ? Number(budget.maxPerLemma || 0) : 0;
    const usedTotal = budget ? Number(budget.usedTotal || 0) : 0;
    const usedBySentence = budget && budget.usedBySentence
      && typeof budget.usedBySentence === "object" ? budget.usedBySentence : {};
    const usedByLemma = budget && budget.usedByLemma && typeof budget.usedByLemma === "object"
      ? budget.usedByLemma : {};
    Object.assign(counter, {
      replacementBudgetScope: "frame_document",
      replacementBudgetActive: Boolean(budget),
      replacementBudgetMaxTotal: maxTotal,
      replacementBudgetMaxPerSentence: maxPerSentence,
      replacementBudgetMaxPerLemma: maxPerLemma,
      replacementBudgetUsedTotal: usedTotal,
      replacementBudgetTrackedSentenceCount: Object.keys(usedBySentence).length,
      replacementBudgetTrackedLemmaCount: Object.keys(usedByLemma).length,
      replacementBudgetPageExhausted: maxTotal > 0 && usedTotal >= maxTotal,
      replacementBudgetSentenceCapReachedCount: countKeysAtLimit(usedBySentence, maxPerSentence),
      replacementBudgetLemmaCapReachedCount: countKeysAtLimit(usedByLemma, maxPerLemma),
      replacementBudgetRejectedPage: Number(counter.replacementBudgetRejectedPage || 0),
      replacementBudgetRejectedSentence: Number(counter.replacementBudgetRejectedSentence || 0),
      replacementBudgetRejectedLemma: Number(counter.replacementBudgetRejectedLemma || 0)
    });
    return counter;
  }

  function createPageBudgetTracker(options) {
    const opts = options && typeof options === "object" ? options : {};
    const isNonRendered = typeof opts.isNonRendered === "function"
      ? opts.isNonRendered
      : (() => false);
    function toBudgetLimit(value, fallback) {
      const parsed = Number.parseInt(value, 10);
      if (!Number.isFinite(parsed)) {
        return Math.max(0, fallback || 0);
      }
      return Math.max(0, parsed);
    }

    function getBudgetLemmaKey(value) {
      return String(value || "").trim().toLowerCase();
    }

    function getBudgetSentenceKey(value) {
      return String(value || "").trim();
    }

    function normalizeBudgetEntry(value) {
      if (value && typeof value === "object") {
        return {
          lemmaKey: getBudgetLemmaKey(value.lemma || value.replacement || ""),
          sentenceKey: getBudgetSentenceKey(value.sentenceKey || value.sentence_key || "")
        };
      }
      return {
        lemmaKey: getBudgetLemmaKey(value),
        sentenceKey: ""
      };
    }

    function buildPageBudgetState(settings) {
      const maxTotal = toBudgetLimit(settings.maxReplacementsPerPage, 0);
      const maxPerLemma = toBudgetLimit(settings.maxReplacementsPerLemmaPerPage, 0);
      const maxPerSentence = toBudgetLimit(settings.maxReplacementsPerSentence, 0);
      if (maxTotal <= 0 && maxPerLemma <= 0 && maxPerSentence <= 0) {
        return null;
      }
      const state = {
        maxTotal,
        maxPerLemma,
        maxPerSentence,
        usedTotal: 0,
        usedByLemma: Object.create(null),
        usedBySentence: Object.create(null)
      };
      const existing = document.querySelectorAll(".lexishift-replacement");
      for (const span of existing) {
        if (isNonRendered(span)) {
          continue;
        }
        const entry = normalizeBudgetEntry({
          lemma: span.dataset.replacement || span.textContent || "",
          sentenceKey: span.dataset.sentenceKey || ""
        });
        state.usedTotal += 1;
        if (entry.lemmaKey) {
          state.usedByLemma[entry.lemmaKey] = Number(state.usedByLemma[entry.lemmaKey] || 0) + 1;
        }
        if (entry.sentenceKey) {
          state.usedBySentence[entry.sentenceKey] = Number(
            state.usedBySentence[entry.sentenceKey] || 0
          ) + 1;
        }
      }
      return state;
    }

    function updatePageBudgetUsage(state, entries) {
      if (!state || !entries || !entries.length) {
        return;
      }
      for (const value of entries) {
        const entry = normalizeBudgetEntry(value);
        state.usedTotal += 1;
        if (entry.lemmaKey) {
          state.usedByLemma[entry.lemmaKey] = Number(state.usedByLemma[entry.lemmaKey] || 0) + 1;
        }
        if (entry.sentenceKey) {
          state.usedBySentence[entry.sentenceKey] = Number(
            state.usedBySentence[entry.sentenceKey] || 0
          ) + 1;
        }
      }
    }

    return {
      attachReplacementBudgetSummary,
      buildPageBudgetState,
      updatePageBudgetUsage
    };
  }

  root.contentDomScanPageBudgetTracker = {
    createPageBudgetTracker
  };
})();
