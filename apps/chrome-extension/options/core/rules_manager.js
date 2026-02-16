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
    if (normalized === "bundle" || normalized === "profile_bundle" || normalized === "selection_bundle") {
      return "bundle";
    }
    if (normalized === "srs_pair" || normalized === "srs-pair" || normalized === "pair_progress") {
      return "srs_pair";
    }
    if (normalized === "appearance_theme" || normalized === "appearance" || normalized === "theme_colors") {
      return "appearance_theme";
    }
    if (normalized === "module_item" || normalized === "module" || normalized === "module_pref") {
      return "module_item";
    }
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
    try {
      const parsed = JSON.parse(cleaned);
      if (this._isObject(parsed) || Array.isArray(parsed)) {
        return parsed;
      }
    } catch (_jsonError) {
      // Not raw JSON payload text; continue with compressed share code decoding.
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

  _normalizePairKey(pair, sourceLanguage, targetLanguage) {
    const source = String(sourceLanguage || "").trim() || "en";
    const target = String(targetLanguage || "").trim() || "en";
    const fallback = `${source}-${target}`;
    if (this.settingsManager && typeof this.settingsManager._normalizePairKey === "function") {
      return this.settingsManager._normalizePairKey(pair || fallback);
    }
    const normalized = String(pair || fallback).trim();
    return normalized || fallback;
  }

  _getProfileLanguagePrefs(items, profileId) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    if (this.settingsManager && typeof this.settingsManager.getProfileLanguagePrefs === "function") {
      return this.settingsManager.getProfileLanguagePrefs(items, { profileId: resolvedProfileId });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    const raw = this._isObject(profileEntry.languagePrefs) ? profileEntry.languagePrefs : {};
    const sourceLanguage = String(raw.sourceLanguage || (items && items.sourceLanguage) || "en").trim() || "en";
    const targetLanguage = String(raw.targetLanguage || (items && items.targetLanguage) || "en").trim() || "en";
    const srsPair = this._normalizePairKey(raw.srsPair, sourceLanguage, targetLanguage);
    return {
      profileId: resolvedProfileId,
      sourceLanguage,
      targetLanguage,
      srsPairAuto: raw.srsPairAuto !== false,
      srsPair,
      targetScriptPrefs: this._isObject(raw.targetScriptPrefs) ? raw.targetScriptPrefs : {}
    };
  }

  _getProfileUiPrefs(items, profileId) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    if (this.settingsManager && typeof this.settingsManager.getProfileUiPrefs === "function") {
      return this.settingsManager.getProfileUiPrefs(items, { profileId: resolvedProfileId });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    return this._isObject(profileEntry.uiPrefs) ? profileEntry.uiPrefs : {};
  }

  _getProfileModulePrefs(items, profileId, targetLanguage) {
    const resolvedProfileId = this._normalizeProfileId(profileId);
    const resolvedTargetLanguage = String(targetLanguage || "").trim() || "en";
    if (this.settingsManager && typeof this.settingsManager.getProfileModulePrefs === "function") {
      return this.settingsManager.getProfileModulePrefs(items, {
        profileId: resolvedProfileId,
        targetLanguage: resolvedTargetLanguage
      });
    }
    const profileEntry = this._getProfileEntry(items, resolvedProfileId);
    const raw = this._isObject(profileEntry.modulePrefs) ? profileEntry.modulePrefs : {};
    return {
      profileId: resolvedProfileId,
      targetLanguage: resolvedTargetLanguage,
      byId: this._isObject(raw.byId) ? raw.byId : {},
      order: Array.isArray(raw.order) ? raw.order : []
    };
  }

  _pickAppearanceThemeFields(source) {
    const input = this._isObject(source) ? source : {};
    return this._pickFields(input, [
      "backgroundBackdropColor",
      "backgroundOpacity",
      "backgroundPositionX",
      "backgroundPositionY",
      "cardThemeHueDeg",
      "cardThemeSaturationPercent",
      "cardThemeBrightnessPercent",
      "cardThemeTransparencyPercent"
    ]);
  }

  async _resolveSrsPairShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const pair = this._normalizePairKey(
      opts.srsPair || opts.pair || languagePrefs.srsPair,
      languagePrefs.sourceLanguage,
      languagePrefs.targetLanguage
    );
    const profileEntry = this._getProfileEntry(items, profileId);
    const srsByPair = this._isObject(profileEntry.srsByPair) ? profileEntry.srsByPair : {};
    const srsProfile = this._isObject(srsByPair[pair]) ? srsByPair[pair] : {};
    const srsSignalsByPair = this._isObject(profileEntry.srsSignalsByPair)
      ? profileEntry.srsSignalsByPair
      : {};
    const srsSignals = this._isObject(srsSignalsByPair[pair]) ? srsSignalsByPair[pair] : {};
    const importedSnapshotsByPair = this._isObject(items && items.importedSrsPairSnapshots)
      ? items.importedSrsPairSnapshots
      : {};
    const importedPairSnapshot = this._isObject(importedSnapshotsByPair[`${profileId}:${pair}`])
      ? importedSnapshotsByPair[`${profileId}:${pair}`]
      : null;
    let helperSnapshot = importedPairSnapshot && this._isObject(importedPairSnapshot.helperSnapshot)
      ? importedPairSnapshot.helperSnapshot
      : null;
    let helperRuleset = importedPairSnapshot && this._isObject(importedPairSnapshot.helperRuleset)
      ? importedPairSnapshot.helperRuleset
      : null;

    const helperManager = opts.helperManager;
    if (helperManager && typeof helperManager.getClient === "function") {
      const client = helperManager.getClient();
      if (client && typeof client.getSnapshot === "function") {
        try {
          const response = await client.getSnapshot(pair, profileId);
          if (response && response.ok === true && this._isObject(response.data)) {
            helperSnapshot = response.data;
          }
        } catch (_err) {
          // Keep local imported snapshot fallback when helper is unavailable.
        }
      }
      if (client && typeof client.getRuleset === "function") {
        try {
          const response = await client.getRuleset(pair, profileId);
          if (response && response.ok === true && this._isObject(response.data)) {
            helperRuleset = response.data;
          }
        } catch (_err) {
          // Keep local imported ruleset fallback when helper is unavailable.
        }
      }
    }

    return {
      pair,
      profileId,
      languagePrefs: {
        sourceLanguage: languagePrefs.sourceLanguage,
        targetLanguage: languagePrefs.targetLanguage,
        srsPairAuto: languagePrefs.srsPairAuto !== false,
        srsPair: pair,
        targetScriptPrefs: this._isObject(languagePrefs.targetScriptPrefs)
          ? languagePrefs.targetScriptPrefs
          : {}
      },
      srsProfile: this._isObject(srsProfile) ? srsProfile : {},
      srsSignals: this._isObject(srsSignals) ? srsSignals : {},
      helperSnapshot,
      helperRuleset,
      exportedAt: new Date().toISOString()
    };
  }

  _normalizeImportedSrsPairPayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.srsPair) ? payload.srsPair : payload;
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const rawLanguagePrefs = this._isObject(raw.languagePrefs) ? raw.languagePrefs : {};
    const sourceLanguage = String(rawLanguagePrefs.sourceLanguage || "en").trim() || "en";
    const targetLanguage = String(rawLanguagePrefs.targetLanguage || "en").trim() || "en";
    const pair = this._normalizePairKey(
      raw.pair || rawLanguagePrefs.srsPair,
      sourceLanguage,
      targetLanguage
    );
    return {
      pair,
      languagePrefs: {
        sourceLanguage,
        targetLanguage,
        srsPairAuto: rawLanguagePrefs.srsPairAuto !== false,
        srsPair: pair,
        targetScriptPrefs: this._isObject(rawLanguagePrefs.targetScriptPrefs)
          ? rawLanguagePrefs.targetScriptPrefs
          : {}
      },
      srsProfile: this._isObject(raw.srsProfile) ? raw.srsProfile : {},
      srsSignals: this._isObject(raw.srsSignals) ? raw.srsSignals : {},
      helperSnapshot: this._isObject(raw.helperSnapshot) ? raw.helperSnapshot : null,
      helperRuleset: this._isObject(raw.helperRuleset) ? raw.helperRuleset : null
    };
  }

  async _applyImportedSrsPairToProfile(srsPairData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const profilesRoot = this._getProfilesRoot(items);
    const profileEntry = this._getProfileEntry(items, profileId);
    const existingLanguagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const pair = this._normalizePairKey(
      srsPairData && srsPairData.pair,
      srsPairData && srsPairData.languagePrefs && srsPairData.languagePrefs.sourceLanguage,
      srsPairData && srsPairData.languagePrefs && srsPairData.languagePrefs.targetLanguage
    );
    const incomingLanguagePrefs = this._isObject(srsPairData && srsPairData.languagePrefs)
      ? srsPairData.languagePrefs
      : {};
    const mergedLanguagePrefs = {
      ...existingLanguagePrefs,
      ...incomingLanguagePrefs,
      srsPair: pair
    };
    const srsByPair = this._isObject(profileEntry.srsByPair) ? profileEntry.srsByPair : {};
    const srsSignalsByPair = this._isObject(profileEntry.srsSignalsByPair)
      ? profileEntry.srsSignalsByPair
      : {};
    const existingPairProfile = this._isObject(srsByPair[pair]) ? srsByPair[pair] : {};
    const incomingPairProfile = this._isObject(srsPairData && srsPairData.srsProfile)
      ? srsPairData.srsProfile
      : {};
    const existingPairSignals = this._isObject(srsSignalsByPair[pair]) ? srsSignalsByPair[pair] : {};
    const incomingPairSignals = this._isObject(srsPairData && srsPairData.srsSignals)
      ? srsPairData.srsSignals
      : {};
    const nextPairProfile = {
      ...existingPairProfile,
      ...incomingPairProfile
    };
    const nextPairSignals = {
      ...existingPairSignals,
      ...incomingPairSignals
    };
    const nextProfiles = {
      ...profilesRoot,
      [profileId]: {
        ...profileEntry,
        languagePrefs: mergedLanguagePrefs,
        srsByPair: {
          ...srsByPair,
          [pair]: nextPairProfile
        },
        srsSignalsByPair: {
          ...srsSignalsByPair,
          [pair]: nextPairSignals
        }
      }
    };
    const updates = {
      srsProfiles: nextProfiles,
      sourceLanguage: String(mergedLanguagePrefs.sourceLanguage || "en").trim() || "en",
      targetLanguage: String(mergedLanguagePrefs.targetLanguage || "en").trim() || "en",
      srsPairAuto: mergedLanguagePrefs.srsPairAuto !== false,
      srsPair: pair,
      srsSelectedProfileId: profileId,
      srsProfileId: profileId,
      srsEnabled: nextPairProfile.srsEnabled === true,
      srsMaxActive: Number.isFinite(Number(nextPairProfile.srsMaxActive))
        ? Number(nextPairProfile.srsMaxActive)
        : (this.settingsManager.defaults.srsMaxActive || 20),
      srsBootstrapTopN: Number.isFinite(Number(nextPairProfile.srsBootstrapTopN))
        ? Number(nextPairProfile.srsBootstrapTopN)
        : (this.settingsManager.defaults.srsBootstrapTopN || 800),
      srsInitialActiveCount: Number.isFinite(Number(nextPairProfile.srsInitialActiveCount))
        ? Number(nextPairProfile.srsInitialActiveCount)
        : (this.settingsManager.defaults.srsInitialActiveCount || 40),
      srsSoundEnabled: nextPairProfile.srsSoundEnabled !== false,
      srsHighlightColor: String(nextPairProfile.srsHighlightColor || this.settingsManager.defaults.srsHighlightColor || "#2f74d0"),
      srsFeedbackSrsEnabled: nextPairProfile.srsFeedbackSrsEnabled !== false,
      srsFeedbackRulesEnabled: nextPairProfile.srsFeedbackRulesEnabled === true,
      srsExposureLoggingEnabled: nextPairProfile.srsExposureLoggingEnabled !== false
    };

    const helperSnapshot = this._isObject(srsPairData && srsPairData.helperSnapshot)
      ? srsPairData.helperSnapshot
      : null;
    const helperRuleset = this._isObject(srsPairData && srsPairData.helperRuleset)
      ? srsPairData.helperRuleset
      : null;
    if (helperSnapshot || helperRuleset) {
      const importedMap = this._isObject(items.importedSrsPairSnapshots)
        ? { ...items.importedSrsPairSnapshots }
        : {};
      importedMap[`${profileId}:${pair}`] = {
        importedAt: new Date().toISOString(),
        helperSnapshot,
        helperRuleset
      };
      updates.importedSrsPairSnapshots = importedMap;
    }

    await this._saveStorage(updates);
    return {
      profileId,
      pair,
      updatedAt: new Date().toISOString(),
      hasHelperData: Boolean(helperSnapshot || helperRuleset)
    };
  }

  async _resolveAppearanceShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const uiPrefs = this._getProfileUiPrefs(items, profileId);
    return {
      profileId,
      theme: this._pickAppearanceThemeFields(uiPrefs),
      exportedAt: new Date().toISOString()
    };
  }

  _normalizeImportedAppearancePayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.appearanceTheme) ? payload.appearanceTheme : payload;
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const themeSource = this._isObject(raw.theme) ? raw.theme : raw;
    const theme = this._pickAppearanceThemeFields(themeSource);
    if (!Object.keys(theme).length) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    return { theme };
  }

  async _applyImportedAppearanceToProfile(appearanceData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const currentUiPrefs = this._getProfileUiPrefs(items, profileId);
    const theme = this._isObject(appearanceData && appearanceData.theme) ? appearanceData.theme : {};
    const nextUiPrefs = {
      ...currentUiPrefs,
      ...theme
    };
    if (this.settingsManager && typeof this.settingsManager.updateProfileUiPrefs === "function") {
      await this.settingsManager.updateProfileUiPrefs(nextUiPrefs, { profileId });
    } else {
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: {
          ...profileEntry,
          uiPrefs: nextUiPrefs
        }
      };
      await this._saveStorage({ srsProfiles: nextProfiles });
    }
    return {
      profileId,
      updatedAt: new Date().toISOString()
    };
  }

  async _resolveModuleShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const moduleId = String(opts.moduleId || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const targetLanguage = String(opts.targetLanguage || languagePrefs.targetLanguage || "en").trim() || "en";
    const modulePrefs = this._getProfileModulePrefs(items, profileId, targetLanguage);
    const byId = this._isObject(modulePrefs.byId) ? modulePrefs.byId : {};
    const order = Array.isArray(modulePrefs.order) ? modulePrefs.order : [];
    const entry = this._isObject(byId[moduleId]) ? byId[moduleId] : { enabled: true };
    return {
      profileId,
      targetLanguage,
      module: {
        moduleId,
        prefs: entry,
        inOrder: order.includes(moduleId)
      },
      exportedAt: new Date().toISOString()
    };
  }

  _normalizeImportedModulePayload(data) {
    const payload = this._isObject(data) ? data : {};
    const raw = this._isObject(payload.module)
      ? payload.module
      : (this._isObject(payload.moduleItem) ? payload.moduleItem : payload);
    if (!this._isObject(raw)) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const moduleId = String(raw.moduleId || raw.id || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    let prefs = this._isObject(raw.prefs) ? raw.prefs : null;
    if (!prefs) {
      const derived = {};
      if (raw.enabled !== undefined) {
        derived.enabled = raw.enabled === true;
      }
      if (this._isObject(raw.config)) {
        derived.config = raw.config;
      }
      if (this._isObject(raw.theme)) {
        derived.theme = raw.theme;
      }
      prefs = Object.keys(derived).length ? derived : { enabled: true };
    }
    return {
      moduleId,
      targetLanguage: String(raw.targetLanguage || payload.targetLanguage || "").trim(),
      prefs
    };
  }

  async _applyImportedModuleToProfile(moduleData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const items = this._isObject(opts.items) ? opts.items : await this.settingsManager.load();
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const languagePrefs = this._getProfileLanguagePrefs(items, profileId);
    const targetLanguage = String(moduleData && moduleData.targetLanguage || languagePrefs.targetLanguage || "en").trim() || "en";
    const moduleId = String(moduleData && moduleData.moduleId || "").trim();
    if (!moduleId) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    const modulePrefs = this._getProfileModulePrefs(items, profileId, targetLanguage);
    const byId = this._isObject(modulePrefs.byId) ? modulePrefs.byId : {};
    const order = Array.isArray(modulePrefs.order) ? modulePrefs.order : [];
    const nextById = {
      ...byId,
      [moduleId]: this._isObject(moduleData && moduleData.prefs)
        ? moduleData.prefs
        : { enabled: true }
    };
    const nextOrder = [...order];
    if (!nextOrder.includes(moduleId)) {
      nextOrder.push(moduleId);
    }
    if (this.settingsManager && typeof this.settingsManager.updateProfileModulePrefs === "function") {
      await this.settingsManager.updateProfileModulePrefs(
        { byId: nextById, order: nextOrder },
        { profileId, targetLanguage }
      );
    } else {
      const profilesRoot = this._getProfilesRoot(items);
      const profileEntry = this._getProfileEntry(items, profileId);
      const nextProfiles = {
        ...profilesRoot,
        [profileId]: {
          ...profileEntry,
          modulePrefs: {
            byId: nextById,
            order: nextOrder
          }
        }
      };
      await this._saveStorage({ srsProfiles: nextProfiles });
    }
    return {
      profileId,
      moduleId,
      targetLanguage,
      updatedAt: new Date().toISOString()
    };
  }

  _normalizeBundleTargetKind(rawKind) {
    const normalized = String(rawKind || "").trim().toLowerCase();
    if (!normalized) {
      return "";
    }
    if (normalized === "profile_settings" || normalized === "profile-settings" || normalized === "srs") {
      return "profile_settings";
    }
    if (normalized === "srs_pair" || normalized === "srs-pair" || normalized === "pair_progress") {
      return "srs_pair";
    }
    if (normalized === "appearance_theme" || normalized === "appearance" || normalized === "theme_colors") {
      return "appearance_theme";
    }
    if (normalized === "ruleset" || normalized === "ruleset_item" || normalized === "ruleset-item") {
      return "ruleset";
    }
    if (normalized === "module_item" || normalized === "module" || normalized === "module_pref") {
      return "module_item";
    }
    return "";
  }

  _normalizeBundleTargets(rawTargets) {
    const input = Array.isArray(rawTargets) ? rawTargets : [];
    const normalized = [];
    const seen = new Set();
    const seenSrsPairKeys = new Set();
    const seenRulesetPaths = new Set();
    const seenModuleKeys = new Set();

    input.forEach((rawTarget) => {
      const target = this._isObject(rawTarget) ? rawTarget : {};
      const kind = this._normalizeBundleTargetKind(target.kind || target.type || target.id);
      if (kind === "profile_settings") {
        if (seen.has("profile_settings")) {
          return;
        }
        seen.add("profile_settings");
        normalized.push({ kind: "profile_settings" });
        return;
      }
      if (kind === "srs_pair") {
        const pair = String(target.pair || target.srsPair || "").trim();
        const dedupeKey = pair || "__default__";
        if (seenSrsPairKeys.has(dedupeKey)) {
          return;
        }
        seenSrsPairKeys.add(dedupeKey);
        normalized.push({
          kind: "srs_pair",
          pair
        });
        return;
      }
      if (kind === "appearance_theme") {
        if (seen.has("appearance_theme")) {
          return;
        }
        seen.add("appearance_theme");
        normalized.push({ kind: "appearance_theme" });
        return;
      }
      if (kind === "ruleset") {
        const rulesetPath = this._normalizePath(target.rulesetPath || target.path);
        if (!rulesetPath || seenRulesetPaths.has(rulesetPath)) {
          return;
        }
        seenRulesetPaths.add(rulesetPath);
        normalized.push({
          kind: "ruleset",
          rulesetPath,
          rulesetName: String(target.rulesetName || target.name || "").trim()
        });
        return;
      }
      if (kind === "module_item") {
        const moduleId = String(target.moduleId || target.id || "").trim();
        if (!moduleId) {
          return;
        }
        const targetLanguage = String(target.targetLanguage || "").trim();
        const key = `${moduleId}::${targetLanguage}`;
        if (seenModuleKeys.has(key)) {
          return;
        }
        seenModuleKeys.add(key);
        normalized.push({
          kind: "module_item",
          moduleId,
          targetLanguage
        });
      }
    });
    return normalized;
  }

  async _resolveBundleShareData(options, items) {
    const opts = this._isObject(options) ? options : {};
    const targets = this._normalizeBundleTargets(opts.bundleTargets);
    if (!targets.length) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    const profileId = this._getSelectedProfileId(items, opts.profileId);
    const output = {
      exportedAt: new Date().toISOString(),
      profileId,
      profileSettings: null,
      srsPair: null,
      srsPairs: [],
      appearanceTheme: null,
      modules: [],
      rulesets: []
    };
    for (const target of targets) {
      if (target.kind === "profile_settings") {
        output.profileSettings = this._pickFields(items, this._getSrsShareKeys());
        continue;
      }
      if (target.kind === "srs_pair") {
        const srsPairData = await this._resolveSrsPairShareData({
          ...opts,
          profileId,
          srsPair: target.pair
        }, items);
        output.srsPairs.push(srsPairData);
        if (!output.srsPair) {
          output.srsPair = srsPairData;
        }
        continue;
      }
      if (target.kind === "appearance_theme") {
        output.appearanceTheme = await this._resolveAppearanceShareData({
          ...opts,
          profileId
        }, items);
        continue;
      }
      if (target.kind === "module_item") {
        const moduleData = await this._resolveModuleShareData({
          ...opts,
          profileId,
          moduleId: target.moduleId,
          targetLanguage: target.targetLanguage
        }, items);
        output.modules.push(moduleData);
        continue;
      }
      if (target.kind === "ruleset") {
        const ruleset = await this._resolveRulesetShareData({
          ...opts,
          profileId,
          rulesetPath: target.rulesetPath,
          rulesetName: target.rulesetName
        }, items);
        output.rulesets.push(ruleset);
      }
    }
    const hasProfileSettings = this._isObject(output.profileSettings) && Object.keys(output.profileSettings).length > 0;
    const hasSrsPairs = Array.isArray(output.srsPairs) && output.srsPairs.length > 0;
    const hasSrsPair = (
      hasSrsPairs
      || (this._isObject(output.srsPair) && Object.keys(output.srsPair).length > 0)
    );
    const hasAppearanceTheme = this._isObject(output.appearanceTheme) && Object.keys(output.appearanceTheme).length > 0;
    const hasModules = Array.isArray(output.modules) && output.modules.length > 0;
    const hasRulesets = Array.isArray(output.rulesets) && output.rulesets.length > 0;
    if (!hasProfileSettings && !hasSrsPair && !hasAppearanceTheme && !hasModules && !hasRulesets) {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    return output;
  }

  _normalizeImportedBundlePayload(data) {
    const payload = this._isObject(data) ? data : {};
    const profileSettings = this._isObject(payload.profileSettings)
      ? this._pickFields(payload.profileSettings, this._getSrsShareKeys())
      : {};
    const rawSrsPairs = Array.isArray(payload.srsPairs)
      ? payload.srsPairs
      : (Array.isArray(payload.srs_pairs) ? payload.srs_pairs : []);
    const srsPairs = rawSrsPairs
      .map((rawPair) => this._normalizeImportedSrsPairPayload(rawPair));
    const rawSrsPair = this._isObject(payload.srsPair)
      ? payload.srsPair
      : (this._isObject(payload.srs_pair) ? payload.srs_pair : null);
    if (rawSrsPair && srsPairs.length === 0) {
      srsPairs.push(this._normalizeImportedSrsPairPayload(rawSrsPair));
    }
    const rawAppearance = this._isObject(payload.appearanceTheme)
      ? payload.appearanceTheme
      : (this._isObject(payload.appearance_theme) ? payload.appearance_theme : null);
    const appearanceTheme = rawAppearance ? this._normalizeImportedAppearancePayload(rawAppearance) : null;
    const rawModules = Array.isArray(payload.modules) ? payload.modules : [];
    const modules = rawModules.map((rawModule) => this._normalizeImportedModulePayload(rawModule));
    const rawRulesets = Array.isArray(payload.rulesets) ? payload.rulesets : [];
    const rulesets = rawRulesets.map((rawRuleset) => this._normalizeImportedRulesetPayload(rawRuleset));
    return {
      profileSettings,
      srsPairs,
      appearanceTheme,
      modules,
      rulesets
    };
  }

  async _applyImportedBundle(bundleData, optionsArg) {
    const opts = this._isObject(optionsArg) ? optionsArg : {};
    const normalizedBundle = this._isObject(bundleData)
      ? bundleData
      : {
          profileSettings: {},
          srsPairs: [],
          appearanceTheme: null,
          modules: [],
          rulesets: []
        };
    const appliedRulesets = [];
    const appliedModules = [];
    const appliedSrsPairs = [];
    let appliedAppearanceTheme = null;
    const profileSettings = this._isObject(normalizedBundle.profileSettings)
      ? normalizedBundle.profileSettings
      : {};
    const srsPairsRaw = Array.isArray(normalizedBundle.srsPairs) ? normalizedBundle.srsPairs : [];
    const srsPairs = srsPairsRaw.filter((entry) => this._isObject(entry));
    const appearanceTheme = this._isObject(normalizedBundle.appearanceTheme)
      ? normalizedBundle.appearanceTheme
      : null;
    const modules = Array.isArray(normalizedBundle.modules) ? normalizedBundle.modules : [];
    const rulesets = Array.isArray(normalizedBundle.rulesets) ? normalizedBundle.rulesets : [];
    const appliedProfileSettings = Object.keys(profileSettings).length > 0;

    if (appliedProfileSettings) {
      await this._saveStorage(profileSettings);
    }

    for (const srsPairData of srsPairs) {
      const applyResult = await this._applyImportedSrsPairToProfile(srsPairData, {
        profileId: opts.profileId
      });
      appliedSrsPairs.push(applyResult);
    }

    if (appearanceTheme) {
      appliedAppearanceTheme = await this._applyImportedAppearanceToProfile(appearanceTheme, {
        profileId: opts.profileId
      });
    }

    for (const moduleData of modules) {
      const applyResult = await this._applyImportedModuleToProfile(moduleData, {
        profileId: opts.profileId
      });
      appliedModules.push({
        moduleId: applyResult.moduleId,
        targetLanguage: applyResult.targetLanguage,
        profileId: applyResult.profileId
      });
    }

    for (const rulesetData of rulesets) {
      const applyResult = await this._applyImportedRulesetToProfile(rulesetData, {
        profileId: opts.profileId
      });
      appliedRulesets.push({
        name: rulesetData.name,
        path: applyResult.path,
        rulesCount: applyResult.rulesCount,
        profileId: applyResult.profileId
      });
    }

    return {
      appliedProfileSettings,
      srsPair: appliedSrsPairs.length ? appliedSrsPairs[0] : null,
      srsPairs: appliedSrsPairs,
      appearanceTheme: appliedAppearanceTheme,
      modules: appliedModules,
      rulesets: appliedRulesets,
      requiresReload: (
        appliedProfileSettings === true
        || appliedSrsPairs.length > 0
        || Boolean(appliedAppearanceTheme)
      )
    };
  }

  async generateSharePayload(options, editorValueArg, isEditorDisabledArg) {
    const opts = this._isObject(options)
      ? options
      : {
          useCjk: options === true,
          editorValue: editorValueArg,
          isEditorDisabled: isEditorDisabledArg
        };
    const scope = this._resolveShareScope(opts.scope);
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
      } else if (scope === "srs_pair") {
        data = {
          srsPair: await this._resolveSrsPairShareData(opts, items)
        };
        version = 2;
      } else if (scope === "appearance_theme") {
        data = {
          appearanceTheme: await this._resolveAppearanceShareData(opts, items)
        };
        version = 2;
      } else if (scope === "module_item") {
        data = {
          module: await this._resolveModuleShareData(opts, items)
        };
        version = 2;
      } else if (scope === "bundle") {
        data = await this._resolveBundleShareData(opts, items);
        version = 3;
      } else if (scope === "ruleset") {
        data = {
          ruleset: await this._resolveRulesetShareData(opts, items)
        };
        version = 2;
      } else {
        data = this._isObject(items) ? items : {};
      }
    }

    return this._createShareEnvelope(scope, data, version);
  }

  async generateShareCode(options, editorValueArg, isEditorDisabledArg) {
    const opts = this._isObject(options)
      ? options
      : {
          useCjk: options === true,
          editorValue: editorValueArg,
          isEditorDisabled: isEditorDisabledArg
        };
    const useCjk = opts.useCjk === true;
    const envelope = await this.generateSharePayload(opts);
    const code = this._encodePayload(envelope, useCjk);
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

    if (imported.scope === "srs_pair") {
      const srsPairData = this._normalizeImportedSrsPairPayload(imported.data);
      const applyResult = await this._applyImportedSrsPairToProfile(srsPairData, {
        profileId: options.profileId
      });
      return {
        scope: "srs_pair",
        updatedAt: applyResult.updatedAt,
        profileId: applyResult.profileId,
        pair: applyResult.pair,
        hasHelperData: applyResult.hasHelperData === true,
        requiresReload: true
      };
    }

    if (imported.scope === "appearance_theme") {
      const appearanceData = this._normalizeImportedAppearancePayload(imported.data);
      const applyResult = await this._applyImportedAppearanceToProfile(appearanceData, {
        profileId: options.profileId
      });
      return {
        scope: "appearance_theme",
        updatedAt: applyResult.updatedAt,
        profileId: applyResult.profileId,
        requiresReload: true
      };
    }

    if (imported.scope === "module_item") {
      const moduleData = this._normalizeImportedModulePayload(imported.data);
      const applyResult = await this._applyImportedModuleToProfile(moduleData, {
        profileId: options.profileId
      });
      return {
        scope: "module_item",
        updatedAt: applyResult.updatedAt,
        profileId: applyResult.profileId,
        module: {
          moduleId: applyResult.moduleId,
          targetLanguage: applyResult.targetLanguage
        }
      };
    }

    if (imported.scope === "bundle") {
      const bundleData = this._normalizeImportedBundlePayload(imported.data);
      const applyResult = await this._applyImportedBundle(bundleData, {
        profileId: options.profileId
      });
      return {
        scope: "bundle",
        updatedAt,
        appliedProfileSettings: applyResult.appliedProfileSettings === true,
        srsPair: applyResult.srsPair || null,
        srsPairs: Array.isArray(applyResult.srsPairs) ? applyResult.srsPairs : [],
        appearanceTheme: applyResult.appearanceTheme || null,
        modules: Array.isArray(applyResult.modules) ? applyResult.modules : [],
        requiresReload: applyResult.requiresReload === true,
        rulesets: Array.isArray(applyResult.rulesets) ? applyResult.rulesets : []
      };
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
