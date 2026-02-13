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
    if (normalized === "srs" || normalized === "srs_status") {
      return "srs";
    }
    if (normalized === "profile" || normalized === "full_profile" || normalized === "full-profile") {
      return "profile";
    }
    return "rules";
  }

  _createShareEnvelope(scope, data) {
    return {
      lexishift_share: {
        version: 1,
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
      return {
        scope: this._resolveShareScope(decoded.lexishift_share.scope),
        data: decoded.data
      };
    }
    return {
      scope: "rules",
      data: decoded
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
      } else {
        data = this._isObject(items) ? items : {};
      }
    }
    const code = this._encodePayload(this._createShareEnvelope(scope, data), useCjk);
    if (!code) {
      throw new Error(this.i18n.t("error_generated_code_empty", null, "Generated code is empty."));
    }
    return code;
  }

  async importShareCode(code, useCjk) {
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
