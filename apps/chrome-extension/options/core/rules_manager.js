class RulesManager {
  constructor(settingsManager, i18n) {
    this.settingsManager = settingsManager;
    this.i18n = i18n;
  }

  extractRules(input) {
    if (Array.isArray(input)) return input;
    if (input && typeof input === "object" && Array.isArray(input.rules)) return input.rules;
    throw new Error(
      this.i18n.t(
        "error_rules_expected_array",
        null,
        "Expected a JSON array or an object with a rules array."
      )
    );
  }

  parseFromEditor(jsonString) {
    const parsed = JSON.parse(jsonString || "[]");
    return this.extractRules(parsed);
  }

  async saveFromEditor(jsonString) {
    const rules = this.parseFromEditor(jsonString);
    this.settingsManager.currentRules = rules;
    const updatedAt = new Date().toISOString();
    return new Promise((resolve) => {
      chrome.storage.local.set({ rules, rulesSource: "editor", rulesUpdatedAt: updatedAt }, () => {
        resolve({ rules, updatedAt });
      });
    });
  }

  async importFromFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(reader.result);
          const rules = this.extractRules(parsed);
          this.settingsManager.currentRules = rules;
          const updatedAt = new Date().toISOString();
          chrome.storage.local.set(
            { rules, rulesSource: "file", rulesFileName: file.name, rulesUpdatedAt: updatedAt },
            () => {
              resolve({ rules, updatedAt, fileName: file.name });
            }
          );
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = () => {
        reject(new Error(this.i18n.t("status_read_failed", null, "Failed to read file.")));
      };
      reader.readAsText(file);
    });
  }

  exportToFile() {
    const payload = JSON.stringify(this.settingsManager.currentRules || [], null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "lexishift-rules.json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  _isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  _resolveShareScope(rawScope) {
    const normalized = String(rawScope || "rules").trim().toLowerCase();
    if (normalized === "ruleset" || normalized === "manual_ruleset" || normalized === "single_ruleset") {
      return "ruleset";
    }
    if (normalized === "srs" || normalized === "srs_status") {
      return "srs";
    }
    if (normalized === "profile" || normalized === "full_profile" || normalized === "full-profile") {
      return "profile";
    }
    return "rules";
  }

  _createShareEnvelope(scope, data, versionArg) {
    const versionRaw = Number.parseInt(versionArg, 10);
    const version = Number.isFinite(versionRaw) && versionRaw >= 1 ? versionRaw : 1;
    return {
      lexishift_share: {
        version,
        scope
      },
      data
    };
  }

  _unwrapShareEnvelope(decoded) {
    if (this._isObject(decoded)
      && this._isObject(decoded.lexishift_share)
      && typeof decoded.lexishift_share.scope === "string"
      && Object.prototype.hasOwnProperty.call(decoded, "data")) {
      const rawVersion = Number.parseInt(decoded.lexishift_share.version, 10);
      return {
        scope: this._resolveShareScope(decoded.lexishift_share.scope),
        data: decoded.data,
        version: Number.isFinite(rawVersion) && rawVersion >= 1 ? rawVersion : 1
      };
    }
    return {
      scope: "rules",
      data: decoded,
      version: 1
    };
  }

  _requireLz() {
    if (typeof getLZString !== "function") {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    return getLZString();
  }

  _encodePayload(payload, useCjk) {
    const lz = this._requireLz();
    const json = JSON.stringify(payload);
    if (useCjk === true) {
      if (typeof encodeBase16384 !== "function"
        || typeof stringToBytes !== "function") {
        throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
      }
      const compressed = lz.compress(json);
      if (!compressed) {
        throw new Error(this.i18n.t("error_generated_code_empty", null, "Generated code is empty."));
      }
      return encodeBase16384(stringToBytes(compressed));
    }
    const encoded = lz.compressToEncodedURIComponent(json);
    if (!encoded) {
      throw new Error(this.i18n.t("error_generated_code_empty", null, "Generated code is empty."));
    }
    return encoded;
  }

  _decodePayloadSafe(code) {
    const lz = this._requireLz();
    const json = lz.decompressFromEncodedURIComponent(code);
    if (!json) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    return JSON.parse(json);
  }

  _decodePayloadCjk(code) {
    if (typeof decodeBase16384 !== "function" || typeof bytesToString !== "function") {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const lz = this._requireLz();
    const bytes = decodeBase16384(code);
    const compressed = bytesToString(bytes);
    const json = lz.decompress(compressed);
    if (!json) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    return JSON.parse(json);
  }

  _decodePayload(code, preferCjk) {
    const cleaned = String(code || "").trim();
    if (!cleaned) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }

    const trySafeThenCjk = () => {
      try {
        return this._decodePayloadSafe(cleaned);
      } catch (_safeError) {
        return this._decodePayloadCjk(cleaned);
      }
    };

    const tryCjkThenSafe = () => {
      try {
        return this._decodePayloadCjk(cleaned);
      } catch (_cjkError) {
        return this._decodePayloadSafe(cleaned);
      }
    };

    if (preferCjk === true) {
      return tryCjkThenSafe();
    }
    if (typeof isCjkCode === "function" && isCjkCode(cleaned)) {
      return tryCjkThenSafe();
    }
    return trySafeThenCjk();
  }

  _getSrsShareKeys() {
    return [
      "sourceLanguage",
      "targetLanguage",
      "targetDisplayScript",
      "srsPairAuto",
      "srsPair",
      "srsSelectedProfileId",
      "srsProfileId",
      "srsEnabled",
      "srsMaxActive",
      "srsBootstrapTopN",
      "srsInitialActiveCount",
      "srsSoundEnabled",
      "srsHighlightColor",
      "srsFeedbackSrsEnabled",
      "srsFeedbackRulesEnabled",
      "srsExposureLoggingEnabled",
      "profileRules",
      "profileRulesUpdatedAt",
      "manualRulesetCacheByPath",
      "srsProfiles",
      "popupModulePrefs",
      "optionsSelectedProfileId",
      "srsRulesetUpdatedAt"
    ];
  }

  _pickFields(source, keys) {
    const input = this._isObject(source) ? source : {};
    const output = {};
    keys.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(input, key)) {
        output[key] = input[key];
      }
    });
    return output;
  }

  _saveStorage(data) {
    const payload = this._isObject(data) ? data : {};
    return new Promise((resolve) => {
      chrome.storage.local.set(payload, resolve);
    });
  }

  _normalizeProfileId(profileId) {
    if (this.settingsManager && typeof this.settingsManager.normalizeSrsProfileId === "function") {
      return this.settingsManager.normalizeSrsProfileId(profileId);
    }
    const normalized = String(profileId || "").trim();
    return normalized || "default";
  }

  _normalizePath(pathValue) {
    const normalized = String(pathValue || "").trim();
    return normalized || "";
  }

  _pathBasename(pathValue) {
    const normalized = this._normalizePath(pathValue);
    if (!normalized) {
      return "(unknown)";
    }
    const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
    return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
  }

  _getSelectedProfileId(items, fallbackProfileId) {
    if (fallbackProfileId !== undefined && fallbackProfileId !== null && String(fallbackProfileId).trim()) {
      return this._normalizeProfileId(fallbackProfileId);
    }
    if (this.settingsManager && typeof this.settingsManager.getSelectedSrsProfileId === "function") {
      return this._normalizeProfileId(this.settingsManager.getSelectedSrsProfileId(items));
    }
    return this._normalizeProfileId(null);
  }

  _getProfilesRoot(items) {
    return this._isObject(items && items.srsProfiles) ? items.srsProfiles : {};
  }

  _getProfileEntry(items, profileId) {
    const profilesRoot = this._getProfilesRoot(items);
    const resolvedProfileId = this._normalizeProfileId(profileId);
    return this._isObject(profilesRoot[resolvedProfileId]) ? profilesRoot[resolvedProfileId] : {};
  }

  _normalizeManualRulesetsState(rawState) {
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
  }

  _normalizeRulesetCache(rawCache) {
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
  }

  _buildProfileRules(manualState, cache) {
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
  }

  _slugifyRulesetName(name) {
    const normalized = String(name || "").trim().toLowerCase();
    const slug = normalized
      .replace(/\.json$/i, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || "ruleset";
  }

  _createImportedRulesetPath(name, manualState, cache) {
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
  }

  async _resolveRulesetFromHelper(helperManager, profileId, rulesetPath) {
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
  }

  async _resolveRulesetShareData(options, items) {
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
    let cacheEntry = cache[rulesetPath];
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
  }

  _normalizeImportedRulesetPayload(data) {
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
  }

  async _applyImportedRulesetToProfile(rulesetData, optionsArg) {
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
  }

  async generateShareCode(options, editorValueArg, isEditorDisabledArg) {
    const opts = this._isObject(options)
      ? options
      : {
          useCjk: options === true,
          editorValue: editorValueArg,
          isEditorDisabled: isEditorDisabledArg
        };
    const scope = this._resolveShareScope(opts.scope);
    const useCjk = opts.useCjk === true;
    let data;
    let version = 1;
    if (scope === "rules") {
      if (opts.isEditorDisabled !== true) {
        data = this.parseFromEditor(opts.editorValue);
      } else {
        data = this.settingsManager.currentRules || [];
      }
    } else {
      const items = await this.settingsManager.load();
      if (scope === "srs") {
        data = this._pickFields(items, this._getSrsShareKeys());
      } else if (scope === "ruleset") {
        data = {
          ruleset: await this._resolveRulesetShareData(opts, items)
        };
        version = 2;
      } else {
        data = this._isObject(items) ? items : {};
      }
    }
    const code = this._encodePayload(this._createShareEnvelope(scope, data, version), useCjk);
    if (!code) {
      throw new Error(this.i18n.t("error_generated_code_empty", null, "Generated code is empty."));
    }
    return code;
  }

  async importShareCode(code, useCjk, optionsArg) {
    const options = this._isObject(optionsArg) ? optionsArg : {};
    const decoded = this._decodePayload(code || "", useCjk === true);
    const imported = this._unwrapShareEnvelope(decoded);
    const updatedAt = new Date().toISOString();

    if (imported.scope === "rules") {
      const decodedRules = this.extractRules(imported.data);
      if (!decodedRules.length) {
        throw new Error(this.i18n.t("error_decoded_empty", null, "Decoded rules are empty."));
      }
      this.settingsManager.currentRules = decodedRules;
      await this._saveStorage({
        rules: decodedRules,
        rulesSource: "editor",
        rulesUpdatedAt: updatedAt
      });
      return { scope: "rules", rules: decodedRules, updatedAt };
    }

    if (imported.scope === "srs") {
      const srsData = this._pickFields(imported.data, this._getSrsShareKeys());
      if (!Object.keys(srsData).length) {
        throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
      }
      await this._saveStorage(srsData);
      return { scope: "srs", updatedAt };
    }

    if (imported.scope === "ruleset") {
      const rulesetData = this._normalizeImportedRulesetPayload(imported.data);
      const applyResult = await this._applyImportedRulesetToProfile(rulesetData, {
        profileId: options.profileId
      });
      return {
        scope: "ruleset",
        updatedAt: applyResult.updatedAt,
        profileId: applyResult.profileId,
        ruleset: {
          name: rulesetData.name,
          path: applyResult.path,
          rulesCount: applyResult.rulesCount,
          metadata: rulesetData.metadata
        }
      };
    }

    if (!this._isObject(imported.data)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    await this._saveStorage(imported.data);
    if (Array.isArray(imported.data.rules)) {
      this.settingsManager.currentRules = imported.data.rules;
    }
    return { scope: "profile", updatedAt };
  }
}
