(() => {
  if (typeof RulesManager !== "function") {
    return;
  }

  RulesManager.prototype._normalizeBundleTargets = function _normalizeBundleTargets(rawTargets) {
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
  };

  RulesManager.prototype._resolveBundleShareData = async function _resolveBundleShareData(options, items) {
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
  };

  RulesManager.prototype._normalizeImportedBundlePayload = function _normalizeImportedBundlePayload(data) {
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
  };

  RulesManager.prototype._applyImportedBundle = async function _applyImportedBundle(bundleData, optionsArg) {
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
  };
})();
