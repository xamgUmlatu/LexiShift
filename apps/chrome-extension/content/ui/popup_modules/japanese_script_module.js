(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const SCRIPT_FORM_ORDER = ["kanji", "kana", "romaji"];
  const SCRIPT_MODULE_ORDER = ["kana", "kanji", "romaji"];

  function t(key, substitutions, fallback) {
    try {
      if (typeof chrome !== "undefined"
        && chrome.i18n
        && typeof chrome.i18n.getMessage === "function") {
        const message = chrome.i18n.getMessage(key, substitutions);
        if (message) {
          return message;
        }
      }
    } catch (_error) {
      // Ignore i18n runtime errors and return fallback.
    }
    return String(fallback || key || "");
  }

  function summarizeTarget(target) {
    if (!target || !target.dataset) {
      return null;
    }
    return {
      origin: String(target.dataset.origin || "ruleset"),
      languagePair: String(target.dataset.languagePair || ""),
      displayScript: String(target.dataset.displayScript || ""),
      hasScriptForms: Boolean(String(target.dataset.scriptForms || "").trim()),
      displayReplacement: String(target.dataset.displayReplacement || "").slice(0, 80),
      replacement: String(target.dataset.replacement || "").slice(0, 80)
    };
  }

  function scriptLabel(script) {
    if (script === "kana") {
      return t("option_ja_script_kana", null, "Kana");
    }
    if (script === "romaji") {
      return t("option_ja_script_romaji", null, "Romaji");
    }
    return t("option_ja_script_kanji", null, "Kanji");
  }

  function parseScriptForms(target, debugLog) {
    const payload = target && target.dataset ? target.dataset.scriptForms : "";
    if (!payload) {
      if (typeof debugLog === "function") {
        debugLog("No script forms payload on target.", summarizeTarget(target));
      }
      return null;
    }
    try {
      const parsed = JSON.parse(payload);
      if (!parsed || typeof parsed !== "object") {
        if (typeof debugLog === "function") {
          debugLog("Script forms payload parsed to non-object.", {
            payloadPreview: String(payload).slice(0, 120)
          });
        }
        return null;
      }
      const normalized = {};
      for (const script of SCRIPT_FORM_ORDER) {
        const value = String(parsed[script] || "").trim();
        if (value) {
          normalized[script] = value;
        }
      }
      if (!Object.keys(normalized).length) {
        if (typeof debugLog === "function") {
          debugLog("Script forms object had no supported script values.", {
            keys: Object.keys(parsed)
          });
        }
        return null;
      }
      if (typeof debugLog === "function") {
        debugLog("Parsed script forms.", {
          scripts: Object.keys(normalized),
          target: summarizeTarget(target)
        });
      }
      return normalized;
    } catch (error) {
      if (typeof debugLog === "function") {
        debugLog("Failed to parse script forms payload.", {
          message: error && error.message ? error.message : String(error),
          payloadPreview: String(payload).slice(0, 120)
        });
      }
      return null;
    }
  }

  function resolvePrimaryScript(target, scriptForms) {
    const current = String(target.dataset.displayScript || "").trim().toLowerCase();
    if (current && scriptForms[current]) {
      return current;
    }
    for (const script of SCRIPT_FORM_ORDER) {
      if (scriptForms[script]) {
        return script;
      }
    }
    return "";
  }

  function build(target, debugLog) {
    if (typeof debugLog === "function") {
      debugLog("Building Japanese script module.", summarizeTarget(target));
    }
    const scriptForms = parseScriptForms(target, debugLog);
    if (!scriptForms) {
      if (typeof debugLog === "function") {
        debugLog("Skipping Japanese script module: no parsed script forms.", summarizeTarget(target));
      }
      return null;
    }
    const availableScripts = SCRIPT_FORM_ORDER.filter((script) => Boolean(scriptForms[script]));
    if (availableScripts.length < 2) {
      if (typeof debugLog === "function") {
        debugLog("Skipping Japanese script module: fewer than two scripts available.", {
          availableScripts,
          target: summarizeTarget(target)
        });
      }
      return null;
    }
    const primaryScript = resolvePrimaryScript(target, scriptForms);
    const alternatives = SCRIPT_MODULE_ORDER.filter(
      (script) => script !== primaryScript && Boolean(scriptForms[script])
    );
    if (!alternatives.length) {
      if (typeof debugLog === "function") {
        debugLog("Skipping Japanese script module: no alternatives after primary resolution.", {
          primaryScript,
          availableScripts,
          target: summarizeTarget(target)
        });
      }
      return null;
    }
    const moduleEl = document.createElement("section");
    moduleEl.className = "lexishift-popup-module lexishift-script-module";

    for (const script of alternatives) {
      const row = document.createElement("div");
      row.className = "lexishift-script-module-row";
      const label = document.createElement("span");
      label.className = "lexishift-script-module-label";
      label.textContent = scriptLabel(script);
      const value = document.createElement("span");
      value.className = "lexishift-script-module-value";
      value.textContent = scriptForms[script];
      row.appendChild(label);
      row.appendChild(value);
      moduleEl.appendChild(row);
    }

    if (typeof debugLog === "function") {
      debugLog("Built Japanese script module.", {
        primaryScript,
        alternatives,
        target: summarizeTarget(target)
      });
    }
    return moduleEl;
  }

  root.uiJapaneseScriptModule = {
    build,
    summarizeTarget
  };
})();
