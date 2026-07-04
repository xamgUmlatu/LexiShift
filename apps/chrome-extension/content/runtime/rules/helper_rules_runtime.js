(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const helperErrorCopy = root.helperErrorCopy;
  const sourceIndexCache = root.helperSourceIndexCache;
  const sourceIndexCacheFns = ["requestOptions", "optionsKey", "withMetadata", "isUsable"];
  const missingSourceIndexCache = !sourceIndexCache
    || sourceIndexCacheFns.some((name) => typeof sourceIndexCache[name] !== "function");

  if (
    !helperErrorCopy
    || typeof helperErrorCopy.normalizeHelperErrorMessage !== "function"
    || typeof helperErrorCopy.normalizeHelperThrownErrorMessage !== "function"
    || missingSourceIndexCache
  ) {
    throw new Error("[LexiShift][Content] Missing shared helper runtime dependencies.");
  }

  function createRuntime(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getHelperClient = typeof opts.getHelperClient === "function" ? opts.getHelperClient : (() => null);
    const helperCache = opts.helperCache && typeof opts.helperCache === "object" ? opts.helperCache : null;
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId : (value) => String(value || "").trim() || "default";
    const tagRulesWithOrigin = typeof opts.tagRulesWithOrigin === "function"
      ? opts.tagRulesWithOrigin : (rules) => (Array.isArray(rules) ? rules : []);
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const helperRulesCache = new Map();
    const helperSemanticInventoryCache = new Map();
    const helperBrowsingSourceIndexCache = new Map();

    function normalizeHelperMessage(error, fallbackText) {
      return helperErrorCopy.normalizeHelperErrorMessage(error, { fallbackText });
    }

    function normalizeThrownHelperMessage(error, fallbackText) {
      return helperErrorCopy.normalizeHelperThrownErrorMessage(error, { fallbackText });
    }

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

    function cacheBrowsingSourceIndex(pair, index, profileId, optionsKey) {
      const key = rulesCacheKey(pair, profileId);
      if (!key || !index || typeof index !== "object" || !Array.isArray(index.rules)) {
        return;
      }
      const normalizedProfileId = normalizeProfileId(profileId);
      const payload = sourceIndexCache.withMetadata(index, optionsKey);
      helperBrowsingSourceIndexCache.set(key, payload);
      if (helperCache && typeof helperCache.saveBrowsingSourceIndex === "function") {
        helperCache.saveBrowsingSourceIndex(pair, payload, { profileId: normalizedProfileId });
      }
    }

    async function fetchHelperRules(pair, profileId) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.getRuleset !== "function") {
        return {
          ruleset: null,
          error: normalizeHelperMessage(
            { code: "helper_missing", message: "Helper client unavailable." },
            "Failed to load helper ruleset."
          )
        };
      }
      const response = await helperClient.getRuleset(pair, profileId);
      if (!response || response.ok === false) {
        const message = normalizeHelperMessage(
          response && response.error,
          "Failed to load helper ruleset."
        );
        return { ruleset: null, error: message };
      }
      return { ruleset: response.data || null, error: null };
    }

    async function fetchSemanticInventory(pair, profileId) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.getSemanticInventory !== "function") {
        return {
          inventory: null,
          error: normalizeHelperMessage(
            { code: "helper_missing", message: "Helper client unavailable." },
            "Failed to load helper semantic inventory."
          )
        };
      }
      const response = await helperClient.getSemanticInventory(pair, profileId);
      if (!response || response.ok === false) {
        const message = normalizeHelperMessage(
          response && response.error,
          "Failed to load helper semantic inventory."
        );
        return { inventory: null, error: message };
      }
      return { inventory: response.data || null, error: null };
    }

    async function fetchBrowsingSourceIndex(pair, profileId, options) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.getSrsBrowsingSourceIndex !== "function") {
        return {
          index: null,
          error: normalizeHelperMessage(
            { code: "helper_missing", message: "Helper client unavailable." },
            "Failed to load helper browsing source index."
          )
        };
      }
      const response = await helperClient.getSrsBrowsingSourceIndex(
        pair,
        profileId,
        sourceIndexCache.requestOptions(options)
      );
      if (!response || response.ok === false) {
        const message = normalizeHelperMessage(
          response && response.error,
          "Failed to load helper browsing source index."
        );
        return { index: null, error: message };
      }
      return { index: response.data || null, error: null };
    }

    async function requestSemanticAdmitBatch(payload, timeoutMs) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.semanticAdmitBatch !== "function") {
        return {
          response: null,
          error: normalizeHelperMessage(
            { code: "helper_missing", message: "Helper client unavailable." },
            "Failed to evaluate helper semantic admission batch."
          )
        };
      }
      const response = await helperClient.semanticAdmitBatch(payload, timeoutMs);
      if (!response || response.ok === false) {
        const message = normalizeHelperMessage(
          response && response.error,
          "Failed to evaluate helper semantic admission batch."
        );
        return { response: null, error: message };
      }
      return { response: response.data || null, error: null };
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

    async function loadCachedBrowsingSourceIndex(pair, profileId, options, allowStale) {
      const key = rulesCacheKey(pair, profileId);
      if (!key) {
        return null;
      }
      const optionsKey = sourceIndexCache.optionsKey(options);
      const cachedInMemory = helperBrowsingSourceIndexCache.get(key);
      if (sourceIndexCache.isUsable(cachedInMemory, optionsKey, options, allowStale)) {
        return cachedInMemory;
      }
      if (helperCache && typeof helperCache.loadBrowsingSourceIndex === "function") {
        const cachedPersisted = await helperCache.loadBrowsingSourceIndex(
          pair,
          { profileId: normalizeProfileId(profileId) }
        );
        if (sourceIndexCache.isUsable(cachedPersisted, optionsKey, options, allowStale)) {
          helperBrowsingSourceIndexCache.set(key, cachedPersisted);
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
        helperRulesError = normalizeThrownHelperMessage(
          error,
          "Failed to fetch helper rules."
        );
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
        inventoryError = normalizeThrownHelperMessage(
          error,
          "Failed to fetch helper semantic inventory."
        );
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

    async function resolveBrowsingSourceIndex(pair, profileId, options) {
      const normalizedPair = String(pair || "").trim();
      const normalizedProfileId = normalizeProfileId(profileId);
      if (!normalizedPair) {
        return { rules: [], source: "none", error: null };
      }

      let rules = [];
      let sourceIndexError = null;
      let source = "none";
      const sourceIndexOptions = options && typeof options === "object" ? options : {};
      const optionsKey = sourceIndexCache.optionsKey(sourceIndexOptions);

      const cached = await loadCachedBrowsingSourceIndex(
        normalizedPair,
        normalizedProfileId,
        sourceIndexOptions,
        false
      );
      if (cached && Array.isArray(cached.rules)) {
        return {
          rules: tagRulesWithOrigin(cached.rules, ruleOriginSrs),
          source: "helper-cache",
          error: null
        };
      }

      try {
        const helperFetch = await fetchBrowsingSourceIndex(
          normalizedPair,
          normalizedProfileId,
          sourceIndexOptions,
        );
        const helperIndex = helperFetch && typeof helperFetch === "object"
          ? helperFetch.index
          : null;
        sourceIndexError = helperFetch && typeof helperFetch === "object"
          ? helperFetch.error
          : null;
        if (
          helperIndex
          && helperIndex.status !== "not_ready"
          && Array.isArray(helperIndex.rules)
          && helperIndex.rules.length
        ) {
          rules = tagRulesWithOrigin(helperIndex.rules, ruleOriginSrs);
          source = "helper";
          cacheBrowsingSourceIndex(normalizedPair, helperIndex, normalizedProfileId, optionsKey);
        } else {
          if (helperIndex && helperIndex.status === "not_ready") {
            sourceIndexError = String(helperIndex.reason || "source_index_not_ready");
          }
          const fallback = await loadCachedBrowsingSourceIndex(
            normalizedPair,
            normalizedProfileId,
            sourceIndexOptions,
            true
          );
          if (fallback && Array.isArray(fallback.rules)) {
            rules = tagRulesWithOrigin(fallback.rules, ruleOriginSrs);
            source = "helper-cache";
          }
        }
      } catch (error) {
        sourceIndexError = normalizeThrownHelperMessage(
          error,
          "Failed to fetch helper browsing source index."
        );
        const fallback = await loadCachedBrowsingSourceIndex(
          normalizedPair,
          normalizedProfileId,
          sourceIndexOptions,
          true
        );
        if (fallback && Array.isArray(fallback.rules)) {
          rules = tagRulesWithOrigin(fallback.rules, ruleOriginSrs);
          source = "helper-cache";
        }
      }

      return {
        rules,
        source,
        error: sourceIndexError
      };
    }

    async function semanticAdmitBatch(payload, timeoutMs) {
      try {
        return await requestSemanticAdmitBatch(payload, timeoutMs);
      } catch (error) {
        return {
          response: null,
          error: normalizeThrownHelperMessage(
            error,
            "Failed to evaluate helper semantic admission batch."
          )
        };
      }
    }

    return {
      resolveHelperRules,
      resolveBrowsingSourceIndex,
      resolveSemanticInventory,
      semanticAdmitBatch
    };
  }

  root.contentHelperRulesRuntime = {
    createRuntime
  };
})();
