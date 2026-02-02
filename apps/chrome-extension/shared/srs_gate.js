(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const selector = root.srsSelector;

  async function buildSrsGate(settings, enabledRules, log) {
    if (!settings || !settings.srsEnabled || !selector || typeof selector.selectActiveItems !== "function") {
      return {
        activeRules: enabledRules,
        activeLemmas: null,
        stats: null,
        enabled: false
      };
    }
    try {
      const result = await selector.selectActiveItems(settings);
      const stats = result && result.stats ? result.stats : null;
      const total = stats && Number.isFinite(stats.total) ? stats.total : 0;
      if (!total) {
        if (log) {
          log("SRS dataset unavailable; falling back to full rules.");
        }
        return { activeRules: enabledRules, activeLemmas: null, stats, enabled: true };
      }
      const activeLemmas = new Set(
        (result && result.lemmas ? result.lemmas : []).map((lemma) => String(lemma).toLowerCase())
      );
      const activeRules = activeLemmas.size
        ? enabledRules.filter((rule) =>
            activeLemmas.has(String(rule.replacement || "").toLowerCase())
          )
        : [];
      if (log && activeLemmas.size) {
        const sample = Array.from(activeLemmas).slice(0, 5);
        log(`SRS active lemmas (sample): ${sample.join(", ")}`);
      }
      return { activeRules, activeLemmas, stats, enabled: true };
    } catch (err) {
      if (log) {
        log("SRS selection failed; falling back to full rules.", err);
      }
      return { activeRules: enabledRules, activeLemmas: null, stats: null, enabled: true };
    }
  }

  root.srsGate = { buildSrsGate };
})();
