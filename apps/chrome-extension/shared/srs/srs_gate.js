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

  function getSrsServingMetadata(rule) {
    const metadata = rule && rule.metadata && typeof rule.metadata === "object"
      ? rule.metadata
      : null;
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

  function isRuleDue(rule, nowMs) {
    const srs = getSrsServingMetadata(rule);
    if (!srs) {
      return true;
    }
    const nextDue = String(srs.next_due || srs.nextDue || "").trim();
    if (nextDue) {
      const parsed = Date.parse(nextDue);
      if (!Number.isNaN(parsed)) {
        return parsed <= nowMs;
      }
    }
    if (typeof srs.in_due === "boolean") {
      return srs.in_due;
    }
    if (typeof srs.inDue === "boolean") {
      return srs.inDue;
    }
    return true;
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
    const nowMs = Date.now();
    const activeSrsRules = srsRules.filter((rule) => isRuleDue(rule, nowMs));
    const activeLemmas = new Set(
      activeSrsRules
        .map((rule) => String(rule.replacement || "").toLowerCase())
        .filter(Boolean)
    );
    if (log) {
      const sample = Array.from(activeLemmas).slice(0, 5);
      log(`SRS gate mode=helper_ruleset; active SRS lemmas sample: ${sample.join(", ")}`);
    }
    return {
      activeRules: [...nonSrsRules, ...activeSrsRules],
      activeLemmas,
      stats: {
        total: srsRules.length,
        filtered: activeSrsRules.length,
        nonSrsCount: nonSrsRules.length,
        srsCount: srsRules.length,
        srsActiveCount: activeSrsRules.length,
        srsDueFilteredCount: srsRules.length - activeSrsRules.length,
        datasetLoaded: false,
        mode: "helper_ruleset",
        servingMode: "due_metadata"
      },
      enabled: true
    };
  }

  root.srsGate = { buildSrsGate };
})();
