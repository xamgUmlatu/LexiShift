(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function normalizePath(value) {
    const normalized = String(value || "").trim();
    return normalized || "";
  }

  function normalizeRulesArray(rules) {
    if (!Array.isArray(rules)) {
      return [];
    }
    return rules.filter((rule) => isObject(rule));
  }

  function normalizeRulesetCache(rawCache) {
    const raw = isObject(rawCache) ? rawCache : {};
    const normalized = {};
    Object.entries(raw).forEach(([rawPath, rawEntry]) => {
      const pathKey = normalizePath(rawPath);
      if (!pathKey || !isObject(rawEntry)) {
        return;
      }
      const rules = normalizeRulesArray(rawEntry.rules);
      normalized[pathKey] = {
        rules,
        rulesCount: Number.isFinite(Number(rawEntry.rulesCount))
          ? Number(rawEntry.rulesCount)
          : rules.length,
        exists: rawEntry.exists !== false,
        error: normalizePath(rawEntry.error),
        loadedAt: normalizePath(rawEntry.loadedAt),
        displayPath: normalizePath(rawEntry.displayPath) || pathKey
      };
    });
    return normalized;
  }

  function normalizeManualRulesetsState(rawState) {
    const raw = isObject(rawState) ? rawState : {};
    const rawOrder = Array.isArray(raw.order) ? raw.order : [];
    const rawEnabledByPath = isObject(raw.enabledByPath) ? raw.enabledByPath : {};
    const order = [];
    const seen = new Set();
    rawOrder.forEach((rawPath) => {
      const pathKey = normalizePath(rawPath);
      if (!pathKey || seen.has(pathKey)) {
        return;
      }
      seen.add(pathKey);
      order.push(pathKey);
    });
    const enabledByPath = {};
    order.forEach((pathKey) => {
      if (Object.prototype.hasOwnProperty.call(rawEnabledByPath, pathKey)) {
        enabledByPath[pathKey] = rawEnabledByPath[pathKey] !== false;
      }
    });
    return {
      order,
      enabledByPath
    };
  }

  function resolveExistingEnabled(state, pathKey, legacyPathKey) {
    if (Object.prototype.hasOwnProperty.call(state.enabledByPath, pathKey)) {
      return state.enabledByPath[pathKey] !== false;
    }
    if (legacyPathKey && Object.prototype.hasOwnProperty.call(state.enabledByPath, legacyPathKey)) {
      return state.enabledByPath[legacyPathKey] !== false;
    }
    return true;
  }

  function normalizeHelperRulesets(payload) {
    const rawItems = payload && Array.isArray(payload.rulesets) ? payload.rulesets : [];
    const items = [];
    const seen = new Set();
    rawItems.forEach((rawItem) => {
      const item = isObject(rawItem) ? rawItem : {};
      const pathKey = normalizePath(item.resolved_path || item.path);
      const displayPath = normalizePath(item.path) || pathKey;
      if (!pathKey || seen.has(pathKey)) {
        return;
      }
      seen.add(pathKey);
      const rules = normalizeRulesArray(item.rules);
      items.push({
        pathKey,
        displayPath,
        exists: item.exists === true,
        rules,
        rulesCount: Number.isFinite(Number(item.rules_count)) ? Number(item.rules_count) : rules.length,
        error: normalizePath(item.error)
      });
    });
    return items;
  }

  function mergeManualStateFromHelper(existingState, helperRulesets) {
    const order = [];
    const enabledByPath = {};
    helperRulesets.forEach((ruleset) => {
      order.push(ruleset.pathKey);
      enabledByPath[ruleset.pathKey] = resolveExistingEnabled(
        existingState,
        ruleset.pathKey,
        ruleset.displayPath
      );
    });
    existingState.order.forEach((pathKey) => {
      if (order.includes(pathKey)) {
        return;
      }
      order.push(pathKey);
      enabledByPath[pathKey] = resolveExistingEnabled(existingState, pathKey, null);
    });
    return {
      order,
      enabledByPath
    };
  }

  function mergeCacheFromHelper(existingCache, helperRulesets) {
    const nextCache = {
      ...existingCache
    };
    const loadedAt = new Date().toISOString();
    helperRulesets.forEach((ruleset) => {
      nextCache[ruleset.pathKey] = {
        rules: ruleset.rules,
        rulesCount: ruleset.rulesCount,
        exists: ruleset.exists,
        error: ruleset.error,
        loadedAt,
        displayPath: ruleset.displayPath
      };
    });
    return nextCache;
  }

  function buildProfileRules(manualState, cache) {
    const rules = [];
    manualState.order.forEach((pathKey) => {
      if (manualState.enabledByPath[pathKey] === false) {
        return;
      }
      const entry = cache[pathKey];
      if (!entry || !Array.isArray(entry.rules)) {
        return;
      }
      entry.rules.forEach((rule) => {
        rules.push(rule);
      });
    });
    return rules;
  }

  function summarize(manualState, cache, profileRules) {
    const total = manualState.order.length;
    const enabled = manualState.order.filter((pathKey) => manualState.enabledByPath[pathKey] !== false).length;
    const missing = manualState.order.filter((pathKey) => cache[pathKey] && cache[pathKey].exists !== true).length;
    const rulesCount = Array.isArray(profileRules) ? profileRules.length : 0;
    let summary = `Enabled ${enabled}/${total} profile rulesets`;
    if (missing > 0) {
      summary += ` (${missing} missing)`;
    }
    summary += `, ${rulesCount} profile rules.`;
    return summary;
  }

  function pathBasename(path) {
    const normalized = normalizePath(path);
    if (!normalized) {
      return "(unknown)";
    }
    const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
    return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
  }

  root.optionsProfileRulesetsState = {
    isObject,
    normalizePath,
    normalizeRulesetCache,
    normalizeManualRulesetsState,
    normalizeHelperRulesets,
    mergeManualStateFromHelper,
    mergeCacheFromHelper,
    buildProfileRules,
    summarize,
    pathBasename
  };
})();
