(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const selector = root.srsSelector;
  const RULE_ORIGIN_SRS = "srs";

  function normalizeOrigin(origin) {
    return String(origin || "").toLowerCase() === RULE_ORIGIN_SRS ? RULE_ORIGIN_SRS : "ruleset";
  }

  function getRuleOrigin(rule) {
    return normalizeOrigin(rule && rule.metadata ? rule.metadata.lexishift_origin : "");
  }

  function splitRulesByOrigin(rules) {
    const srsRules = [];
    const nonSrsRules = [];
    for (const rule of rules || []) {
      if (getRuleOrigin(rule) === RULE_ORIGIN_SRS) {
        srsRules.push(rule);
      } else {
        nonSrsRules.push(rule);
      }
    }
    return { srsRules, nonSrsRules };
  }

  async function buildSrsGate(settings, enabledRules, log) {
    if (!settings || !settings.srsEnabled || !selector || typeof selector.selectActiveItems !== "function") {
      return {
        activeRules: enabledRules,
        activeLemmas: null,
        stats: null,
        enabled: false
      };
    }
    const { srsRules, nonSrsRules } = splitRulesByOrigin(enabledRules);
    if (!srsRules.length) {
      return {
        activeRules: nonSrsRules,
        activeLemmas: null,
        stats: {
          total: 0,
          filtered: 0,
          nonSrsCount: nonSrsRules.length,
          srsCount: 0,
          srsActiveCount: 0,
          datasetLoaded: true
        },
        enabled: true
      };
    }
    try {
      const result = await selector.selectActiveItems(settings);
      const stats = result && result.stats ? result.stats : null;
      const total = stats && Number.isFinite(stats.total) ? stats.total : 0;
      if (!total) {
        if (log) {
          log("SRS dataset unavailable; using all SRS-tagged rules.");
        }
        return {
          activeRules: [...nonSrsRules, ...srsRules],
          activeLemmas: null,
          stats: {
            ...(stats || {}),
            nonSrsCount: nonSrsRules.length,
            srsCount: srsRules.length,
            srsActiveCount: srsRules.length
          },
          enabled: true
        };
      }
      const activeLemmas = new Set(
        (result && result.lemmas ? result.lemmas : []).map((lemma) => String(lemma).toLowerCase())
      );
      const activeSrsRules = activeLemmas.size
        ? srsRules.filter((rule) =>
            activeLemmas.has(String(rule.replacement || "").toLowerCase())
          )
        : [];
      if (log && activeLemmas.size) {
        const sample = Array.from(activeLemmas).slice(0, 5);
        log(`SRS active lemmas (sample): ${sample.join(", ")}`);
      }
      return {
        activeRules: [...nonSrsRules, ...activeSrsRules],
        activeLemmas,
        stats: {
          ...(stats || {}),
          nonSrsCount: nonSrsRules.length,
          srsCount: srsRules.length,
          srsActiveCount: activeSrsRules.length
        },
        enabled: true
      };
    } catch (err) {
      if (log) {
        log("SRS selection failed; using all SRS-tagged rules.", err);
      }
      return {
        activeRules: [...nonSrsRules, ...srsRules],
        activeLemmas: null,
        stats: {
          nonSrsCount: nonSrsRules.length,
          srsCount: srsRules.length,
          srsActiveCount: srsRules.length,
          datasetLoaded: false
        },
        enabled: true
      };
    }
  }

  root.srsGate = { buildSrsGate };
})();
