(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
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
    if (!settings || !settings.srsEnabled) {
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
    const activeLemmas = new Set(
      srsRules
        .map((rule) => String(rule.replacement || "").toLowerCase())
        .filter(Boolean)
    );
    if (log) {
      const sample = Array.from(activeLemmas).slice(0, 5);
      log(`SRS gate mode=helper_ruleset; active SRS lemmas sample: ${sample.join(", ")}`);
    }
    return {
      activeRules: [...nonSrsRules, ...srsRules],
      activeLemmas,
      stats: {
        total: srsRules.length,
        filtered: srsRules.length,
        nonSrsCount: nonSrsRules.length,
        srsCount: srsRules.length,
        srsActiveCount: srsRules.length,
        datasetLoaded: false,
        mode: "helper_ruleset"
      },
      enabled: true
    };
  }

  root.srsGate = { buildSrsGate };
})();
