(() => {
  if (typeof RulesManager !== "function") {
    return;
  }

  RulesManager.prototype._getSelectedProfileId = function _getSelectedProfileId(items, fallbackProfileId) {
    if (fallbackProfileId !== undefined && fallbackProfileId !== null && String(fallbackProfileId).trim()) {
      return this._normalizeProfileId(fallbackProfileId);
    }
    if (this.settingsManager && typeof this.settingsManager.getSelectedSrsProfileId === "function") {
      return this._normalizeProfileId(this.settingsManager.getSelectedSrsProfileId(items));
    }
    return this._normalizeProfileId(null);
  };

  RulesManager.prototype._getProfilesRoot = function _getProfilesRoot(items) {
    return this._isObject(items && items.srsProfiles) ? items.srsProfiles : {};
  };

  RulesManager.prototype._getProfileEntry = function _getProfileEntry(items, profileId) {
    const profilesRoot = this._getProfilesRoot(items);
    const resolvedProfileId = this._normalizeProfileId(profileId);
    return this._isObject(profilesRoot[resolvedProfileId]) ? profilesRoot[resolvedProfileId] : {};
  };

  RulesManager.prototype._normalizeManualRulesetsState = function _normalizeManualRulesetsState(rawState) {
    const raw = this._isObject(rawState) ? rawState : {};
    const rawOrder = Array.isArray(raw.order) ? raw.order : [];
    const rawEnabledByPath = this._isObject(raw.enabledByPath) ? raw.enabledByPath : {};
    const order = [];
    const seen = new Set();
    rawOrder.forEach((rawPath) => {
      const pathKey = this._normalizePath(rawPath);
      if (!pathKey || seen.has(pathKey)) {
        return;
      }
      seen.add(pathKey);
      order.push(pathKey);
    });
    Object.keys(rawEnabledByPath).forEach((rawPath) => {
      const pathKey = this._normalizePath(rawPath);
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
      } else {
        enabledByPath[pathKey] = true;
      }
    });
    return {
      order,
      enabledByPath
    };
  };

  RulesManager.prototype._normalizeRulesetCache = function _normalizeRulesetCache(rawCache) {
    const raw = this._isObject(rawCache) ? rawCache : {};
    const normalized = {};
    Object.entries(raw).forEach(([rawPath, rawEntry]) => {
      const pathKey = this._normalizePath(rawPath);
      if (!pathKey || !this._isObject(rawEntry)) {
        return;
      }
      const rules = Array.isArray(rawEntry.rules) ? rawEntry.rules.filter((rule) => this._isObject(rule)) : [];
      normalized[pathKey] = {
        rules,
        rulesCount: Number.isFinite(Number(rawEntry.rulesCount))
          ? Number(rawEntry.rulesCount)
          : rules.length,
        exists: rawEntry.exists !== false,
        error: this._normalizePath(rawEntry.error),
        loadedAt: this._normalizePath(rawEntry.loadedAt),
        displayPath: this._normalizePath(rawEntry.displayPath) || pathKey
      };
    });
    return normalized;
  };

  RulesManager.prototype._buildProfileRules = function _buildProfileRules(manualState, cache) {
    const state = this._isObject(manualState) ? manualState : { order: [], enabledByPath: {} };
    const cacheMap = this._isObject(cache) ? cache : {};
    const rules = [];
    (Array.isArray(state.order) ? state.order : []).forEach((pathKey) => {
      if (state.enabledByPath && state.enabledByPath[pathKey] === false) {
        return;
      }
      const entry = cacheMap[pathKey];
      if (!entry || !Array.isArray(entry.rules)) {
        return;
      }
      entry.rules.forEach((rule) => {
        if (this._isObject(rule)) {
          rules.push(rule);
        }
      });
    });
    return rules;
  };

  RulesManager.prototype._slugifyRulesetName = function _slugifyRulesetName(name) {
    const normalized = String(name || "").trim().toLowerCase();
    const slug = normalized
      .replace(/\.json$/i, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || "ruleset";
  };

  RulesManager.prototype._createImportedRulesetPath = function _createImportedRulesetPath(name, manualState, cache) {
    const baseSlug = this._slugifyRulesetName(name);
    const taken = new Set();
    (Array.isArray(manualState && manualState.order) ? manualState.order : []).forEach((pathKey) => {
      const normalized = this._normalizePath(pathKey);
      if (normalized) {
        taken.add(normalized);
      }
    });
    Object.keys(this._isObject(cache) ? cache : {}).forEach((pathKey) => {
      const normalized = this._normalizePath(pathKey);
      if (normalized) {
        taken.add(normalized);
      }
    });
    let candidate = `shared/imported/${baseSlug}.json`;
    let index = 2;
    while (taken.has(candidate)) {
      candidate = `shared/imported/${baseSlug}-${index}.json`;
      index += 1;
    }
    return candidate;
  };

  RulesManager.prototype._resolveRulesetFromHelper = async function _resolveRulesetFromHelper(
    helperManager,
    profileId,
    rulesetPath
  ) {
    if (!helperManager || typeof helperManager.getProfileRulesets !== "function") {
      return null;
    }
    const result = await helperManager.getProfileRulesets(profileId);
    if (!result || result.ok !== true) {
      return null;
    }
    const rawItems = result.data && Array.isArray(result.data.rulesets) ? result.data.rulesets : [];
    for (const rawItem of rawItems) {
      if (!this._isObject(rawItem)) {
        continue;
      }
      const pathKey = this._normalizePath(rawItem.resolved_path || rawItem.path);
      const displayPath = this._normalizePath(rawItem.path || rawItem.resolved_path);
      if (pathKey !== rulesetPath && displayPath !== rulesetPath) {
        continue;
      }
      const rules = Array.isArray(rawItem.rules)
        ? rawItem.rules.filter((rule) => this._isObject(rule))
        : [];
      if (!rules.length) {
        continue;
      }
      return {
        rules,
        displayPath: displayPath || pathKey
      };
    }
    return null;
  };

  RulesManager.prototype._resolveRulesetShareData = async function _resolveRulesetShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const rulesetPath = this._normalizePath(opts.rulesetPath);
    if (!rulesetPath) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    const profileEntry = this._getProfileEntry(items, profileId);
    const manualState = this._normalizeManualRulesetsState(profileEntry.manualRulesets);
    if (!manualState.order.includes(rulesetPath)) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    const cache = this._normalizeRulesetCache(items && items.manualRulesetCacheByPath);
    const cacheEntry = cache[rulesetPath];
    let rules = cacheEntry && Array.isArray(cacheEntry.rules) ? cacheEntry.rules.filter((rule) => this._isObject(rule)) : [];
    let displayPath = cacheEntry ? cacheEntry.displayPath : rulesetPath;

    if (!rules.length) {
      const helperResult = await this._resolveRulesetFromHelper(opts.helperManager, profileId, rulesetPath);
      if (helperResult && Array.isArray(helperResult.rules) && helperResult.rules.length) {
        rules = helperResult.rules;
        displayPath = helperResult.displayPath || displayPath;
      }
    }

    if (!rules.length) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }

    const name = String(opts.rulesetName || this._pathBasename(displayPath || rulesetPath)).trim() || "ruleset";
    const metadataSeed = this._isObject(opts.rulesetMetadata) ? opts.rulesetMetadata : {};
    const metadata = {
      ...metadataSeed,
      exportedAt: new Date().toISOString(),
      rulesCount: rules.length
    };
    delete metadata.path;
    delete metadata.displayPath;

    return {
      name,
      rules,
      metadata
    };
  };

  RulesManager.prototype._normalizeImportedRulesetPayload = function _normalizeImportedRulesetPayload(data) {
    const payload = this._isObject(data) ? data : {};
    const rawRuleset = this._isObject(payload.ruleset) ? payload.ruleset : payload;
    if (!this._isObject(rawRuleset)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const name = String(rawRuleset.name || "Imported ruleset").trim() || "Imported ruleset";
    const rulesSource = Object.prototype.hasOwnProperty.call(rawRuleset, "rules")
      ? rawRuleset.rules
      : rawRuleset;
    const rules = this.extractRules(rulesSource);
    if (!rules.length) {
      throw new Error(this.i18n.t("error_decoded_empty", null, "Decoded rules are empty."));
    }
    const metadata = this._isObject(rawRuleset.metadata) ? rawRuleset.metadata : {};
    return {
      name,
      rules,
      metadata
    };
  };

  RulesManager.prototype._applyImportedRulesetToProfile = async function _applyImportedRulesetToProfile(rulesetData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const profilesRoot = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const manualState = this._normalizeManualRulesetsState(profileEntry.manualRulesets);
    const cache = this._normalizeRulesetCache(items.manualRulesetCacheByPath);
    const importedAt = new Date().toISOString();
    const rulesetPath = this._createImportedRulesetPath(rulesetData.name, manualState, cache);

    manualState.order.push(rulesetPath);
    manualState.enabledByPath[rulesetPath] = true;
    cache[rulesetPath] = {
      rules: rulesetData.rules,
      rulesCount: rulesetData.rules.length,
      exists: true,
      error: "",
      loadedAt: importedAt,
      displayPath: rulesetPath
    };

    const nextProfiles = {
      ...profilesRoot,
      [profileId]: {
        ...profileEntry,
        manualRulesets: {
          order: [...manualState.order],
          enabledByPath: {
            ...manualState.enabledByPath
          }
        }
      }
    };
    const profileRules = this._buildProfileRules(manualState, cache);

    await this._saveStorage({
      srsProfiles: nextProfiles,
      manualRulesetCacheByPath: cache,
      profileRules,
      profileRulesUpdatedAt: importedAt,
      srsRulesetUpdatedAt: importedAt
    });

    return {
      profileId,
      path: rulesetPath,
      updatedAt: importedAt,
      rulesCount: rulesetData.rules.length
    };
  };
})();
