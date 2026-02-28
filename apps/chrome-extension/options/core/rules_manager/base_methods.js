(() => {
  if (typeof RulesManager !== "function") {
    return;
  }

  RulesManager.prototype._isObject = function _isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  };

  RulesManager.prototype._resolveShareScope = function _resolveShareScope(rawScope) {
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
  };

  RulesManager.prototype._createShareEnvelope = function _createShareEnvelope(scope, data, versionArg) {
    const versionRaw = Number.parseInt(versionArg, 10);
    const version = Number.isFinite(versionRaw) && versionRaw >= 1 ? versionRaw : 1;
    return {
      lexishift_share: {
        version,
        scope
      },
      data
    };
  };

  RulesManager.prototype._unwrapShareEnvelope = function _unwrapShareEnvelope(decoded) {
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
  };

  RulesManager.prototype._requireLz = function _requireLz() {
    if (typeof getLZString !== "function") {
      throw new Error(this.i18n.t("status_generate_failed", null, "Failed to generate code."));
    }
    return getLZString();
  };

  RulesManager.prototype._encodePayload = function _encodePayload(payload, useCjk) {
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
  };

  RulesManager.prototype._decodePayloadSafe = function _decodePayloadSafe(code) {
    const lz = this._requireLz();
    const json = lz.decompressFromEncodedURIComponent(code);
    if (!json) {
      throw new Error(this.i18n.t("status_invalid_code", null, "Invalid code."));
    }
    return JSON.parse(json);
  };

  RulesManager.prototype._decodePayloadCjk = function _decodePayloadCjk(code) {
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
  };

  RulesManager.prototype._decodePayload = function _decodePayload(code, preferCjk) {
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
  };

  RulesManager.prototype._getSrsShareKeys = function _getSrsShareKeys() {
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
  };

  RulesManager.prototype._pickFields = function _pickFields(source, keys) {
    const input = this._isObject(source) ? source : {};
    const output = {};
    keys.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(input, key)) {
        output[key] = input[key];
      }
    });
    return output;
  };

  RulesManager.prototype._saveStorage = function _saveStorage(data) {
    const payload = this._isObject(data) ? data : {};
    return new Promise((resolve) => {
      chrome.storage.local.set(payload, resolve);
    });
  };

  RulesManager.prototype._normalizeProfileId = function _normalizeProfileId(profileId) {
    if (this.settingsManager && typeof this.settingsManager.normalizeSrsProfileId === "function") {
      return this.settingsManager.normalizeSrsProfileId(profileId);
    }
    const normalized = String(profileId || "").trim();
    return normalized || "default";
  };

  RulesManager.prototype._normalizePath = function _normalizePath(pathValue) {
    const normalized = String(pathValue || "").trim();
    return normalized || "";
  };

  RulesManager.prototype._pathBasename = function _pathBasename(pathValue) {
    const normalized = this._normalizePath(pathValue);
    if (!normalized) {
      return "(unknown)";
    }
    const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
    return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
  };

  RulesManager.prototype._normalizePairKey = function _normalizePairKey(pair, sourceLanguage, targetLanguage) {
    const source = String(sourceLanguage || "").trim() || "en";
    const target = String(targetLanguage || "").trim() || "en";
    const fallback = `${source}-${target}`;
    if (this.settingsManager && typeof this.settingsManager._normalizePairKey === "function") {
      return this.settingsManager._normalizePairKey(pair || fallback);
    }
    const normalized = String(pair || fallback).trim();
    return normalized || fallback;
  };

  RulesManager.prototype._normalizeBundleTargetKind = function _normalizeBundleTargetKind(rawKind) {
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
  };
})();
