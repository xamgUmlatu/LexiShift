(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createPageBudgetTracker() {
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

    function buildPageBudgetState(settings) {
      const maxTotal = toBudgetLimit(settings.maxReplacementsPerPage, 0);
      const maxPerLemma = toBudgetLimit(settings.maxReplacementsPerLemmaPerPage, 0);
      if (maxTotal <= 0 && maxPerLemma <= 0) {
        return null;
      }
      const state = {
        maxTotal,
        maxPerLemma,
        usedTotal: 0,
        usedByLemma: Object.create(null)
      };
      const existing = document.querySelectorAll(".lexishift-replacement");
      for (const span of existing) {
        const key = getBudgetLemmaKey(span.dataset.replacement || span.textContent || "");
        if (!key) {
          continue;
        }
        state.usedTotal += 1;
        state.usedByLemma[key] = Number(state.usedByLemma[key] || 0) + 1;
      }
      return state;
    }

    function updatePageBudgetUsage(state, replacements) {
      if (!state || !replacements || !replacements.length) {
        return;
      }
      for (const replacement of replacements) {
        const key = getBudgetLemmaKey(replacement);
        if (!key) {
          continue;
        }
        state.usedTotal += 1;
        state.usedByLemma[key] = Number(state.usedByLemma[key] || 0) + 1;
      }
    }

    return {
      buildPageBudgetState,
      updatePageBudgetUsage
    };
  }

  root.contentDomScanPageBudgetTracker = {
    createPageBudgetTracker
  };
})();
