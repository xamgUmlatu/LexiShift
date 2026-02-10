(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRuntime(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getHelperClient = typeof opts.getHelperClient === "function"
      ? opts.getHelperClient
      : (() => null);
    const helperCache = opts.helperCache && typeof opts.helperCache === "object"
      ? opts.helperCache
      : null;
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";
    const tagRulesWithOrigin = typeof opts.tagRulesWithOrigin === "function"
      ? opts.tagRulesWithOrigin
      : (rules) => (Array.isArray(rules) ? rules : []);
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const helperRulesCache = new Map();

    function rulesCacheKey(pair, profileId) {
      const normalizedPair = String(pair || "").trim();
      if (!normalizedPair) {
        return "";
      }
      return `${normalizeProfileId(profileId)}::${normalizedPair}`;
    }

    function cacheHelperRules(pair, rules, profileId) {
      const key = rulesCacheKey(pair, profileId);
      if (!key) {
        return;
      }
      const payload = Array.isArray(rules) ? rules : [];
      const normalizedProfileId = normalizeProfileId(profileId);
      helperRulesCache.set(key, payload);
      if (helperCache && typeof helperCache.saveRuleset === "function") {
        helperCache.saveRuleset(pair, { rules: payload }, { profileId: normalizedProfileId });
      }
    }

    async function fetchHelperRules(pair, profileId) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.getRuleset !== "function") {
        return { ruleset: null, error: "Helper client unavailable." };
      }
      const response = await helperClient.getRuleset(pair, profileId);
      if (!response || response.ok === false) {
        const message = response && response.error && response.error.message
          ? response.error.message
          : "Failed to load helper ruleset.";
        return { ruleset: null, error: message };
      }
      return { ruleset: response.data || null, error: null };
    }

    async function loadCachedRules(pair, profileId) {
      const key = rulesCacheKey(pair, profileId);
      if (!key) {
        return null;
      }
      const cachedInMemory = helperRulesCache.get(key);
      if (Array.isArray(cachedInMemory)) {
        return cachedInMemory;
      }
      if (helperCache && typeof helperCache.loadRuleset === "function") {
        const cachedPersisted = await helperCache.loadRuleset(pair, { profileId: normalizeProfileId(profileId) });
        if (cachedPersisted && Array.isArray(cachedPersisted.rules)) {
          return cachedPersisted.rules;
        }
      }
      return null;
    }

    async function resolveHelperRules(pair, profileId) {
      const normalizedPair = String(pair || "").trim();
      const normalizedProfileId = normalizeProfileId(profileId);
      if (!normalizedPair) {
        return { rules: [], source: "none", error: null };
      }

      let helperRules = [];
      let helperRulesError = null;
      let source = "none";

      try {
        const helperFetch = await fetchHelperRules(normalizedPair, normalizedProfileId);
        const helperRuleset = helperFetch && typeof helperFetch === "object" ? helperFetch.ruleset : null;
        helperRulesError = helperFetch && typeof helperFetch === "object" ? helperFetch.error : null;
        if (helperRuleset && Array.isArray(helperRuleset.rules)) {
          helperRules = tagRulesWithOrigin(helperRuleset.rules, ruleOriginSrs);
          source = "helper";
          cacheHelperRules(normalizedPair, helperRuleset.rules, normalizedProfileId);
        } else {
          const fallback = await loadCachedRules(normalizedPair, normalizedProfileId);
          if (fallback) {
            helperRules = tagRulesWithOrigin(fallback, ruleOriginSrs);
            source = "helper-cache";
          }
        }
      } catch (error) {
        helperRulesError = error && error.message ? error.message : "Failed to fetch helper rules.";
        const fallback = await loadCachedRules(normalizedPair, normalizedProfileId);
        if (fallback) {
          helperRules = tagRulesWithOrigin(fallback, ruleOriginSrs);
          source = "helper-cache";
        }
      }

      return {
        rules: helperRules,
        source,
        error: helperRulesError
      };
    }

    return {
      resolveHelperRules
    };
  }

  root.contentHelperRulesRuntime = {
    createRuntime
  };
})();
