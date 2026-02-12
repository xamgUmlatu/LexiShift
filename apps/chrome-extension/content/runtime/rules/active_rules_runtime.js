(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRuntime(options) {
    const opts = options && typeof options === "object" ? options : {};
    const normalizeRules = typeof opts.normalizeRules === "function"
      ? opts.normalizeRules
      : (rules) => (Array.isArray(rules) ? rules : []);
    const tagRulesWithOrigin = typeof opts.tagRulesWithOrigin === "function"
      ? opts.tagRulesWithOrigin
      : (rules) => (Array.isArray(rules) ? rules : []);
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";
    const helperRulesRuntime = opts.helperRulesRuntime && typeof opts.helperRulesRuntime === "object"
      ? opts.helperRulesRuntime
      : null;
    const srsGate = opts.srsGate && typeof opts.srsGate === "object"
      ? opts.srsGate
      : null;
    const getRuleOrigin = typeof opts.getRuleOrigin === "function"
      ? opts.getRuleOrigin
      : (_rule) => String(opts.ruleOriginRuleset || "ruleset");
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const ruleOriginRuleset = String(opts.ruleOriginRuleset || "ruleset");

    function countRulesByOrigin(rules) {
      const counts = {
        [ruleOriginRuleset]: 0,
        [ruleOriginSrs]: 0
      };
      for (const rule of rules || []) {
        const origin = getRuleOrigin(rule);
        counts[origin] = Number(counts[origin] || 0) + 1;
      }
      return counts;
    }

    function countRulesWithScriptForms(rules) {
      let withScriptForms = 0;
      for (const rule of rules || []) {
        const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : null;
        const scriptForms = metadata && typeof metadata.script_forms === "object" ? metadata.script_forms : null;
        if (scriptForms && Object.keys(scriptForms).length > 0) {
          withScriptForms += 1;
        }
      }
      return withScriptForms;
    }

    function countRulesWithWordPackage(rules) {
      let withWordPackage = 0;
      for (const rule of rules || []) {
        const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : null;
        const wordPackage = metadata && typeof metadata.word_package === "object" ? metadata.word_package : null;
        if (wordPackage) {
          withWordPackage += 1;
        }
      }
      return withWordPackage;
    }

    async function resolveActiveRules(settings, gateLogger, runtimeState) {
      const runtime = runtimeState && typeof runtimeState === "object" ? runtimeState : {};
      const helperAvailable = runtime.helperAvailable !== false;
      const currentSettings = settings && typeof settings === "object" ? settings : {};
      const srsProfileId = normalizeProfileId(currentSettings.srsProfileId);

      let rulesSource = "local";
      let helperRulesError = null;
      const localRules = tagRulesWithOrigin(currentSettings.rules, ruleOriginRuleset);
      let helperRules = [];

      if (
        currentSettings.srsEnabled
        && helperAvailable
        && helperRulesRuntime
        && typeof helperRulesRuntime.resolveHelperRules === "function"
      ) {
        const helperResolution = await helperRulesRuntime.resolveHelperRules(
          currentSettings.srsPair,
          srsProfileId
        );
        helperRules = Array.isArray(helperResolution.rules) ? helperResolution.rules : [];
        helperRulesError = helperResolution.error || null;
        if (helperResolution.source === "helper") {
          rulesSource = "local+helper";
        } else if (helperResolution.source === "helper-cache") {
          rulesSource = "local+helper-cache";
        }
      }

      const rawRules = [...localRules, ...helperRules];
      const normalizedRules = normalizeRules(rawRules);
      const enabledRules = normalizedRules.filter((rule) => rule.enabled !== false);
      const originCounts = countRulesByOrigin(enabledRules);

      let activeRules = enabledRules;
      let srsActiveLemmas = null;
      let srsStats = null;
      if (currentSettings.srsEnabled && srsGate && typeof srsGate.buildSrsGate === "function") {
        const gate = await srsGate.buildSrsGate(currentSettings, enabledRules, gateLogger);
        activeRules = gate.activeRules || enabledRules;
        srsActiveLemmas = gate.activeLemmas || null;
        srsStats = gate.stats || null;
      }
      const activeOriginCounts = countRulesByOrigin(activeRules);

      return {
        srsProfileId,
        rulesSource,
        helperRulesError,
        normalizedRules,
        enabledRules,
        originCounts,
        activeRules,
        activeOriginCounts,
        srsActiveLemmas,
        srsStats
      };
    }

    return {
      resolveActiveRules,
      countRulesWithScriptForms,
      countRulesWithWordPackage
    };
  }

  root.contentActiveRulesRuntime = {
    createRuntime
  };
})();
