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
