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
    const helperSemanticInventoryCache = new Map();

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

    function cacheSemanticInventory(pair, inventory, profileId) {
      const key = rulesCacheKey(pair, profileId);
      if (!key || !inventory || typeof inventory !== "object") {
        return;
      }
      const normalizedProfileId = normalizeProfileId(profileId);
      helperSemanticInventoryCache.set(key, inventory);
      if (helperCache && typeof helperCache.saveSemanticInventory === "function") {
        helperCache.saveSemanticInventory(pair, inventory, { profileId: normalizedProfileId });
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

    async function fetchSemanticInventory(pair, profileId) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.getSemanticInventory !== "function") {
        return { inventory: null, error: "Helper client unavailable." };
      }
      const response = await helperClient.getSemanticInventory(pair, profileId);
      if (!response || response.ok === false) {
        const message = response && response.error && response.error.message
          ? response.error.message
          : "Failed to load helper semantic inventory.";
        return { inventory: null, error: message };
      }
      return { inventory: response.data || null, error: null };
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

    async function loadCachedSemanticInventory(pair, profileId) {
      const key = rulesCacheKey(pair, profileId);
      if (!key) {
        return null;
      }
      const cachedInMemory = helperSemanticInventoryCache.get(key);
      if (cachedInMemory && typeof cachedInMemory === "object") {
        return cachedInMemory;
      }
      if (helperCache && typeof helperCache.loadSemanticInventory === "function") {
        const cachedPersisted = await helperCache.loadSemanticInventory(
          pair,
          { profileId: normalizeProfileId(profileId) }
        );
        if (cachedPersisted && typeof cachedPersisted === "object") {
          return cachedPersisted;
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

    async function resolveSemanticInventory(pair, profileId) {
      const normalizedPair = String(pair || "").trim();
      const normalizedProfileId = normalizeProfileId(profileId);
      if (!normalizedPair) {
        return { inventory: null, source: "none", error: null };
      }

      let inventory = null;
      let inventoryError = null;
      let source = "none";

      try {
        const helperFetch = await fetchSemanticInventory(normalizedPair, normalizedProfileId);
        const helperInventory = helperFetch && typeof helperFetch === "object"
          ? helperFetch.inventory
          : null;
        inventoryError = helperFetch && typeof helperFetch === "object"
          ? helperFetch.error
          : null;
        if (helperInventory && typeof helperInventory === "object") {
          inventory = helperInventory;
          source = "helper";
          cacheSemanticInventory(normalizedPair, helperInventory, normalizedProfileId);
        } else {
          const fallback = await loadCachedSemanticInventory(normalizedPair, normalizedProfileId);
          if (fallback && typeof fallback === "object") {
            inventory = fallback;
            source = "helper-cache";
          }
        }
      } catch (error) {
        inventoryError = error && error.message
          ? error.message
          : "Failed to fetch helper semantic inventory.";
        const fallback = await loadCachedSemanticInventory(normalizedPair, normalizedProfileId);
        if (fallback && typeof fallback === "object") {
          inventory = fallback;
          source = "helper-cache";
        }
      }

      return {
        inventory,
        source,
        error: inventoryError
      };
    }

    return {
      resolveHelperRules,
      resolveSemanticInventory
    };
  }

  root.contentHelperRulesRuntime = {
    createRuntime
  };
})();
