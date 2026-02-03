const DEFAULT_SETTINGS =
  (globalThis.LexiShift && globalThis.LexiShift.defaults) || {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    debugEnabled: false,
    debugFocusWord: "",
    uiLanguage: "system",
    rulesSource: "editor",
    rulesFileName: "",
    rulesUpdatedAt: "",
    sourceLanguage: "en",
    targetLanguage: "en",
    srsPairAuto: true,
    srsProfiles: {},
    srsEnabled: false,
    srsPair: "en-en",
    srsMaxActive: 40,
    srsSoundEnabled: true,
    srsHighlightColor: "#2F74D0",
    srsFeedbackSrsEnabled: true,
    srsFeedbackRulesEnabled: false,
    srsExposureLoggingEnabled: true
  };

let localeMessages = null;
let activeLocale = "system";

function t(key, substitutions, fallback) {
  if (localeMessages && localeMessages[key] && localeMessages[key].message) {
    return formatMessage(localeMessages[key].message, substitutions);
  }
  if (globalThis.chrome && chrome.i18n) {
    const message = chrome.i18n.getMessage(key, substitutions);
    if (message) {
      return message;
    }
  }
  return fallback || key;
}

function formatMessage(message, substitutions) {
  if (!substitutions) {
    return message;
  }
  const values = Array.isArray(substitutions) ? substitutions : [substitutions];
  return message.replace(/\$([1-9]\d*)/g, (match, index) => {
    const value = values[Number(index) - 1];
    return value !== undefined ? String(value) : match;
  });
}

function logOptions(...args) {
  console.log("[LexiShift][Options]", ...args);
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (!key) return;
    const message = t(key, null, "");
    if (message) {
      node.textContent = message;
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    if (!key) return;
    const message = t(key, null, "");
    if (message) {
      node.setAttribute("placeholder", message);
    }
  });
  const title = t("options_title", null, "");
  if (title) {
    document.title = title;
  }
}

function resolveLocale(value) {
  if (!value || value === "system") {
    const systemLocale = (globalThis.chrome && chrome.i18n && chrome.i18n.getUILanguage())
      || navigator.language
      || "en";
    value = systemLocale.toLowerCase();
  }
  const normalized = value.toLowerCase();
  if (normalized.startsWith("ja")) return "ja";
  if (normalized.startsWith("zh")) return "zh";
  if (normalized.startsWith("de")) return "de";
  return "en";
}

async function loadLocaleMessages(locale) {
  activeLocale = locale || "system";
  if (activeLocale === "system") {
    localeMessages = null;
    applyI18n();
    return;
  }
  const resolved = resolveLocale(activeLocale);
  try {
    const url = chrome.runtime.getURL(`_locales/${resolved}/messages.json`);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load locale: ${resolved}`);
    }
    localeMessages = await response.json();
  } catch (err) {
    localeMessages = null;
  }
  applyI18n();
}

function errorMessage(err, fallbackKey, fallbackText) {
  if (err instanceof SyntaxError) {
    return t(fallbackKey, null, fallbackText);
  }
  if (err && err.message) {
    return err.message;
  }
  return t(fallbackKey, null, fallbackText);
}

applyI18n();

const enabledInput = document.getElementById("enabled");
const highlightEnabledInput = document.getElementById("highlight-enabled");
const highlightColorInput = document.getElementById("highlight-color");
const highlightColorText = document.getElementById("highlight-color-text");
const maxOnePerBlockInput = document.getElementById("max-one-per-block");
const allowAdjacentInput = document.getElementById("allow-adjacent");
const debugEnabledInput = document.getElementById("debug-enabled");
const debugFocusInput = document.getElementById("debug-focus-word");
const srsEnabledInput = document.getElementById("srs-enabled");
const sourceLanguageInput = document.getElementById("source-language");
const targetLanguageInput = document.getElementById("target-language");
const srsMaxActiveInput = document.getElementById("srs-max-active");
const srsSoundInput = document.getElementById("srs-sound-enabled");
const srsHighlightInput = document.getElementById("srs-highlight-color");
const srsHighlightTextInput = document.getElementById("srs-highlight-color-text");
const srsFeedbackSrsInput = document.getElementById("srs-feedback-srs-enabled");
const srsFeedbackRulesInput = document.getElementById("srs-feedback-rules-enabled");
const srsExposureLoggingInput = document.getElementById("srs-exposure-logging-enabled");
const srsSampleButton = document.getElementById("srs-sample");
const srsSampleOutput = document.getElementById("srs-sample-output");
const srsRulegenButton = document.getElementById("srs-rulegen-preview");
const srsRulegenOutput = document.getElementById("srs-rulegen-output");
const languageSelect = document.getElementById("ui-language");
const rulesInput = document.getElementById("rules");
const saveButton = document.getElementById("save");
const status = document.getElementById("status");
const rulesSourceInputs = Array.from(document.querySelectorAll("input[name='rules-source']"));
const rulesFileInput = document.getElementById("rules-file");
const importFileButton = document.getElementById("import-file");
const exportFileButton = document.getElementById("export-file");
const fileStatus = document.getElementById("file-status");
const rulesUpdated = document.getElementById("rules-updated");
const rulesCount = document.getElementById("rules-count");
const shareCodeInput = document.getElementById("share-code");
const shareCodeCjk = document.getElementById("share-code-cjk");
const generateCodeButton = document.getElementById("generate-code");
const importCodeButton = document.getElementById("import-code");
const copyCodeButton = document.getElementById("copy-code");
const openDesktopAppButton = document.getElementById("open-desktop-app");
const openBdPluginButton = document.getElementById("open-bd-plugin");

const INTEGRATION_LINKS = {
  app: "https://lexishift.app/download",
  plugin: "https://lexishift.app/betterdiscord"
};

let currentRules = [];

function extractRules(input) {
  if (Array.isArray(input)) return input;
  if (input && typeof input === "object" && Array.isArray(input.rules)) return input.rules;
  throw new Error(
    t(
      "error_rules_expected_array",
      null,
      "Expected a JSON array or an object with a rules array."
    )
  );
}

function setStatus(message, color) {
  status.textContent = message;
  status.style.color = color || "#6c675f";
  if (message) {
    setTimeout(() => {
      if (status.textContent === message) {
        status.textContent = "";
      }
    }, 2000);
  }
}

function formatTimestamp(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString();
}

function updateRulesMeta(rules, updatedAt) {
  if (rulesCount) {
    rulesCount.textContent = Array.isArray(rules) ? String(rules.length) : "0";
  }
  if (rulesUpdated) {
    rulesUpdated.textContent = formatTimestamp(updatedAt);
  }
}

function updateRulesSourceUI(source) {
  rulesSourceInputs.forEach((input) => {
    input.checked = input.value === source;
  });
  const isFile = source === "file";
  rulesInput.disabled = isFile;
  saveButton.disabled = isFile;
}

function resolvePairFromInputs() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || DEFAULT_SETTINGS.sourceLanguage || "en")
    : (DEFAULT_SETTINGS.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || DEFAULT_SETTINGS.targetLanguage || "en")
    : (DEFAULT_SETTINGS.targetLanguage || "en");
  const prefs = globalThis.LexiShift && globalThis.LexiShift.languagePrefs;
  if (prefs && typeof prefs.resolveLanguagePair === "function") {
    return prefs.resolveLanguagePair({
      sourceLanguage,
      targetLanguage,
      srsPairAuto: true,
      srsPair: DEFAULT_SETTINGS.srsPair || "en-en"
    });
  }
  return `${sourceLanguage}-${targetLanguage}`;
}

function getSrsProfiles(items) {
  if (items && items.srsProfiles && typeof items.srsProfiles === "object") {
    return items.srsProfiles;
  }
  return {};
}

function buildLegacySrsProfile(items) {
  return {
    srsMaxActive: items.srsMaxActive || DEFAULT_SETTINGS.srsMaxActive || 40,
    srsSoundEnabled: items.srsSoundEnabled !== false,
    srsHighlightColor: items.srsHighlightColor || DEFAULT_SETTINGS.srsHighlightColor || "#2F74D0",
    srsFeedbackSrsEnabled: items.srsFeedbackSrsEnabled !== false,
    srsFeedbackRulesEnabled: items.srsFeedbackRulesEnabled === true,
    srsExposureLoggingEnabled: items.srsExposureLoggingEnabled !== false
  };
}

function applySrsProfile(profile) {
  if (srsMaxActiveInput) {
    srsMaxActiveInput.value = String(profile.srsMaxActive || DEFAULT_SETTINGS.srsMaxActive || 40);
  }
  if (srsSoundInput) {
    srsSoundInput.checked = profile.srsSoundEnabled !== false;
  }
  if (srsHighlightInput) {
    srsHighlightInput.value = profile.srsHighlightColor || DEFAULT_SETTINGS.srsHighlightColor || "#2F74D0";
  }
  if (srsHighlightTextInput) {
    srsHighlightTextInput.value = srsHighlightInput ? srsHighlightInput.value : "#2F74D0";
  }
  const hasNewFeedbackFlags = typeof profile.srsFeedbackSrsEnabled === "boolean"
    || typeof profile.srsFeedbackRulesEnabled === "boolean";
  if (srsFeedbackSrsInput) {
    srsFeedbackSrsInput.checked = hasNewFeedbackFlags
      ? profile.srsFeedbackSrsEnabled !== false
      : true;
  }
  if (srsFeedbackRulesInput) {
    srsFeedbackRulesInput.checked = hasNewFeedbackFlags
      ? profile.srsFeedbackRulesEnabled === true
      : false;
  }
  if (srsExposureLoggingInput) {
    srsExposureLoggingInput.checked = profile.srsExposureLoggingEnabled !== false;
  }
}

function loadSrsProfileForPair(items, pairKey) {
  const profiles = getSrsProfiles(items);
  const profile = profiles[pairKey] || buildLegacySrsProfile(items);
  applySrsProfile(profile);
}

function saveDisplaySettings() {
  const highlightEnabled = highlightEnabledInput.checked;
  const highlightColor = highlightColorInput.value || DEFAULT_SETTINGS.highlightColor;
  const debugEnabled = debugEnabledInput.checked;
  const debugFocusWord = debugFocusInput.value.trim();
  chrome.storage.local.set({ highlightEnabled, highlightColor, debugEnabled, debugFocusWord }, () => {
    setStatus(t("status_display_saved", null, "Display settings saved."), "#3c5a2a");
  });
}

function saveReplacementSettings() {
  const maxOnePerTextBlock = maxOnePerBlockInput.checked;
  const allowAdjacentReplacements = allowAdjacentInput.checked;
  chrome.storage.local.set({ maxOnePerTextBlock, allowAdjacentReplacements }, () => {
    setStatus(t("status_replacement_saved", null, "Replacement settings saved."), "#3c5a2a");
  });
}

function saveSrsSettings() {
  if (!srsEnabledInput || !srsMaxActiveInput) {
    return;
  }
  const srsEnabled = srsEnabledInput.checked;
  const pairKey = resolvePairFromInputs();
  const maxActiveRaw = parseInt(srsMaxActiveInput.value, 10);
  const srsMaxActive = Number.isFinite(maxActiveRaw)
    ? Math.max(1, maxActiveRaw)
    : (DEFAULT_SETTINGS.srsMaxActive || 40);
  const srsSoundEnabled = srsSoundInput ? srsSoundInput.checked : true;
  const srsHighlightColor = srsHighlightInput
    ? (srsHighlightInput.value || DEFAULT_SETTINGS.srsHighlightColor || "#2F74D0")
    : (DEFAULT_SETTINGS.srsHighlightColor || "#2F74D0");
  const srsFeedbackSrsEnabled = srsFeedbackSrsInput ? srsFeedbackSrsInput.checked : true;
  const srsFeedbackRulesEnabled = srsFeedbackRulesInput ? srsFeedbackRulesInput.checked : false;
  const srsExposureLoggingEnabled = srsExposureLoggingInput
    ? srsExposureLoggingInput.checked
    : true;
  const profile = {
    srsMaxActive,
    srsSoundEnabled,
    srsHighlightColor,
    srsFeedbackSrsEnabled,
    srsFeedbackRulesEnabled,
    srsExposureLoggingEnabled
  };
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || DEFAULT_SETTINGS.sourceLanguage || "en")
    : (DEFAULT_SETTINGS.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || DEFAULT_SETTINGS.targetLanguage || "en")
    : (DEFAULT_SETTINGS.targetLanguage || "en");
  srsMaxActiveInput.value = String(srsMaxActive);
  if (srsHighlightInput) {
    srsHighlightInput.value = srsHighlightColor;
  }
  if (srsHighlightTextInput) {
    srsHighlightTextInput.value = srsHighlightColor;
  }
  chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
    const profiles = { ...getSrsProfiles(items), [pairKey]: profile };
    chrome.storage.local.set(
      {
        sourceLanguage,
        targetLanguage,
        srsPairAuto: true,
        srsEnabled,
        srsPair: pairKey,
        srsProfiles: profiles
      },
      () => {
        setStatus(t("status_srs_saved", null, "SRS settings saved."), "#3c5a2a");
        logOptions("SRS settings saved.", {
          pair: pairKey,
          sourceLanguage,
          targetLanguage,
          srsEnabled,
          srsMaxActive,
          srsSoundEnabled,
          srsHighlightColor,
          srsFeedbackSrsEnabled,
          srsFeedbackRulesEnabled,
          srsExposureLoggingEnabled
        });
      }
    );
  });
}

function saveLanguageSettings() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || DEFAULT_SETTINGS.sourceLanguage || "en")
    : (DEFAULT_SETTINGS.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || DEFAULT_SETTINGS.targetLanguage || "en")
    : (DEFAULT_SETTINGS.targetLanguage || "en");
  const pairKey = resolvePairFromInputs();
  chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
    chrome.storage.local.set(
      { sourceLanguage, targetLanguage, srsPairAuto: true, srsPair: pairKey },
      () => {
        loadSrsProfileForPair(items, pairKey);
        setStatus(t("status_language_updated", null, "Language updated."), "#3c5a2a");
      }
    );
  });
}

function parseRulesFromEditor() {
  const parsed = JSON.parse(rulesInput.value || "[]");
  return extractRules(parsed);
}

function saveRules() {
  if (rulesInput.disabled) {
    setStatus(
      t("status_switch_edit_json", null, "Switch to Edit JSON to save changes."),
      "#b42318"
    );
    return;
  }
  let rules;
  try {
    rules = parseRulesFromEditor();
  } catch (err) {
    setStatus(errorMessage(err, "status_invalid_json", "Invalid JSON file."), "#b42318");
    return;
  }
  currentRules = rules;
  const updatedAt = new Date().toISOString();
  chrome.storage.local.set({ rules, rulesSource: "editor", rulesUpdatedAt: updatedAt }, () => {
    updateRulesSourceUI("editor");
    updateRulesMeta(rules, updatedAt);
    setStatus(t("status_rules_saved", null, "Rules saved."), "#3c5a2a");
  });
}

function importFromFile() {
  const file = rulesFileInput.files && rulesFileInput.files[0];
  if (!file) {
    setStatus(t("status_choose_json_file", null, "Choose a JSON file first."), "#b42318");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      const rules = extractRules(parsed);
      currentRules = rules;
      rulesInput.value = JSON.stringify(rules, null, 2);
      const updatedAt = new Date().toISOString();
      chrome.storage.local.set(
        { rules, rulesSource: "file", rulesFileName: file.name, rulesUpdatedAt: updatedAt },
        () => {
          updateRulesSourceUI("file");
          updateRulesMeta(rules, updatedAt);
          fileStatus.textContent = t(
            "file_status_last_imported",
            file.name,
            `Last imported: ${file.name}`
          );
          setStatus(
            t("status_imported_rules", String(rules.length), `Imported ${rules.length} rules.`),
            "#3c5a2a"
          );
        }
      );
    } catch (err) {
      setStatus(
        errorMessage(err, "status_invalid_json", "Invalid JSON file."),
        "#b42318"
      );
    }
  };
  reader.onerror = () => {
    setStatus(t("status_read_failed", null, "Failed to read file."), "#b42318");
  };
  reader.readAsText(file);
}

function exportToFile() {
  const payload = JSON.stringify(currentRules || [], null, 2);
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "lexishift-rules.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  setStatus(t("status_exported_rules", null, "Exported rules."), "#3c5a2a");
}

function getActiveRulesForCode() {
  if (!rulesInput.disabled) {
    return parseRulesFromEditor();
  }
  return currentRules || [];
}

function generateShareCode() {
  try {
    const rules = getActiveRulesForCode();
    const useCjk = shareCodeCjk.checked;
    shareCodeInput.value = encodeRulesCode(rules, useCjk);
    if (!shareCodeInput.value) {
      throw new Error(t("error_generated_code_empty", null, "Generated code is empty."));
    }
    setStatus(
      t(
        "status_generated_code",
        String(shareCodeInput.value.length),
        `Code generated (${shareCodeInput.value.length} chars).`
      ),
      "#3c5a2a"
    );
  } catch (err) {
    setStatus(
      err && err.message ? err.message : t("status_generate_failed", null, "Failed to generate code."),
      "#b42318"
    );
  }
}

function importShareCode() {
  try {
    const decodedRules = decodeRulesCode(shareCodeInput.value || "", shareCodeCjk.checked);
    if (!Array.isArray(decodedRules)) {
      throw new Error(t("error_decoded_not_list", null, "Decoded rules are not a list."));
    }
    if (!decodedRules.length) {
      throw new Error(t("error_decoded_empty", null, "Decoded rules are empty."));
    }
    currentRules = decodedRules;
    rulesInput.value = JSON.stringify(decodedRules, null, 2);
    const updatedAt = new Date().toISOString();
    chrome.storage.local.set({ rules: decodedRules, rulesSource: "editor", rulesUpdatedAt: updatedAt }, () => {
      updateRulesSourceUI("editor");
      updateRulesMeta(decodedRules, updatedAt);
      setStatus(t("status_code_imported", null, "Code imported."), "#3c5a2a");
    });
  } catch (err) {
    setStatus(
      err && err.message ? err.message : t("status_invalid_code", null, "Invalid code."),
      "#b42318"
    );
  }
}

function copyShareCode() {
  if (!shareCodeInput.value) {
    return;
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(shareCodeInput.value).then(() => {
      setStatus(t("status_copied", null, "Copied."), "#3c5a2a");
    });
    return;
  }
  shareCodeInput.select();
  document.execCommand("copy");
  setStatus(t("status_copied", null, "Copied."), "#3c5a2a");
}

function load() {
  chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
    enabledInput.checked = items.enabled;
    highlightEnabledInput.checked = items.highlightEnabled !== false;
    highlightColorInput.value = items.highlightColor || DEFAULT_SETTINGS.highlightColor;
    highlightColorText.value = highlightColorInput.value;
    highlightColorInput.disabled = !highlightEnabledInput.checked;
    highlightColorText.disabled = !highlightEnabledInput.checked;
    maxOnePerBlockInput.checked = items.maxOnePerTextBlock === true;
    allowAdjacentInput.checked = items.allowAdjacentReplacements !== false;
    debugEnabledInput.checked = items.debugEnabled === true;
    debugFocusInput.value = items.debugFocusWord || "";
    debugFocusInput.disabled = !debugEnabledInput.checked;
    if (srsEnabledInput) {
      srsEnabledInput.checked = items.srsEnabled === true;
    }
    if (sourceLanguageInput) {
      sourceLanguageInput.value = items.sourceLanguage || DEFAULT_SETTINGS.sourceLanguage || "en";
    }
    if (targetLanguageInput) {
      targetLanguageInput.value = items.targetLanguage || DEFAULT_SETTINGS.targetLanguage || "en";
    }
    const pairKey = resolvePairFromInputs();
    loadSrsProfileForPair(items, pairKey);
    if (srsSampleOutput) {
      srsSampleOutput.textContent = "";
    }
    if (srsRulegenOutput) {
      srsRulegenOutput.textContent = "";
    }
    if (languageSelect) {
      languageSelect.value = items.uiLanguage || "system";
    }
    currentRules = items.rules || [];
    rulesInput.value = JSON.stringify(currentRules, null, 2);
    updateRulesSourceUI(items.rulesSource || "editor");
    fileStatus.textContent = items.rulesFileName
      ? t(
          "file_status_last_imported",
          items.rulesFileName,
          `Last imported: ${items.rulesFileName}`
        )
      : t(
          "file_status_empty",
          null,
          "No file imported yet. Re-import after changes."
        );
    updateRulesMeta(currentRules, items.rulesUpdatedAt);
    loadLocaleMessages(items.uiLanguage || "system");
  });
}

function buildRuleIndex(rules) {
  const index = new Map();
  (rules || []).forEach((rule) => {
    const replacement = String(rule.replacement || "").trim();
    const source = String(rule.source_phrase || "").trim();
    if (!replacement || !source) {
      return;
    }
    const key = replacement.toLowerCase();
    let bucket = index.get(key);
    if (!bucket) {
      bucket = new Set();
      index.set(key, bucket);
    }
    bucket.add(source);
  });
  return index;
}

function formatRulegenPreview(lemmas, ruleIndex, limit = 12, maxSources = 6) {
  const total = Array.isArray(lemmas) ? lemmas.length : 0;
  if (!total) {
    return "";
  }
  const lines = [];
  const capped = lemmas.slice(0, limit);
  capped.forEach((lemma) => {
    const key = String(lemma || "").trim();
    if (!key) {
      return;
    }
    const sources = ruleIndex.get(key.toLowerCase());
    if (!sources || sources.size === 0) {
      lines.push(`${key} → (no rules)`);
      return;
    }
    const list = Array.from(sources);
    list.sort();
    const shown = list.slice(0, maxSources);
    const remainder = list.length - shown.length;
    const suffix = remainder > 0 ? ` (+${remainder})` : "";
    lines.push(`${key} → ${shown.join(", ")}${suffix}`);
  });
  if (total > limit) {
    lines.push(`… +${total - limit} more`);
  }
  return lines.join("\n");
}

async function sampleActiveWords() {
  if (!srsSampleButton || !srsSampleOutput) {
    return;
  }
  const selector = globalThis.LexiShift && globalThis.LexiShift.srsSelector;
  if (!selector || typeof selector.selectSampledItems !== "function") {
    srsSampleOutput.textContent = t("status_srs_sample_failed", null, "SRS selector not available.");
    return;
  }
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || DEFAULT_SETTINGS.sourceLanguage || "en")
    : (DEFAULT_SETTINGS.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || DEFAULT_SETTINGS.targetLanguage || "en")
    : (DEFAULT_SETTINGS.targetLanguage || "en");
  const srsPair = resolvePairFromInputs();
  srsSampleButton.disabled = true;
  srsSampleOutput.textContent = t("status_srs_sampling", null, "Sampling…");
  try {
    const result = await selector.selectSampledItems(
      { srsPair, sourceLanguage, targetLanguage, srsPairAuto: true },
      5
    );
    const lemmas = result && result.lemmas ? result.lemmas : [];
    if (!lemmas.length) {
      srsSampleOutput.textContent = t("status_srs_sample_empty", null, "No words available.");
    } else {
      srsSampleOutput.textContent = lemmas.join(", ");
    }
    logOptions("SRS sample", { pair: srsPair, lemmas });
  } catch (err) {
    srsSampleOutput.textContent = t("status_srs_sample_failed", null, "SRS sample failed.");
    logOptions("SRS sample failed.", err);
  } finally {
    srsSampleButton.disabled = false;
  }
}

async function previewSrsRulegen() {
  if (!srsRulegenButton || !srsRulegenOutput) {
    return;
  }
  const selector = globalThis.LexiShift && globalThis.LexiShift.srsSelector;
  if (!selector || typeof selector.selectActiveItems !== "function") {
    srsRulegenOutput.textContent = t(
      "status_srs_rulegen_failed",
      null,
      "Rule preview failed."
    );
    return;
  }
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || DEFAULT_SETTINGS.sourceLanguage || "en")
    : (DEFAULT_SETTINGS.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || DEFAULT_SETTINGS.targetLanguage || "en")
    : (DEFAULT_SETTINGS.targetLanguage || "en");
  const srsPair = resolvePairFromInputs();
  const maxActiveRaw = srsMaxActiveInput ? parseInt(srsMaxActiveInput.value, 10) : NaN;
  const srsMaxActive = Number.isFinite(maxActiveRaw)
    ? Math.max(1, maxActiveRaw)
    : (DEFAULT_SETTINGS.srsMaxActive || 40);
  srsRulegenButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_rulegen_loading",
    null,
    "Building rule preview…"
  );
  try {
    const result = await selector.selectActiveItems(
      { srsPair, sourceLanguage, targetLanguage, srsPairAuto: true, srsMaxActive }
    );
    const lemmas = result && Array.isArray(result.lemmas) ? result.lemmas : [];
    const rules = getActiveRulesForCode();
    const ruleIndex = buildRuleIndex(rules);
    const preview = formatRulegenPreview(lemmas, ruleIndex);
    if (!preview) {
      srsRulegenOutput.textContent = t(
        "status_srs_rulegen_empty",
        null,
        "No rules found for current active words."
      );
    } else {
      srsRulegenOutput.textContent = preview;
    }
    logOptions("SRS rulegen preview", { pair: srsPair, count: lemmas.length });
  } catch (err) {
    srsRulegenOutput.textContent = t(
      "status_srs_rulegen_failed",
      null,
      "Rule preview failed."
    );
    logOptions("SRS rulegen preview failed.", err);
  } finally {
    srsRulegenButton.disabled = false;
  }
}

saveButton.addEventListener("click", saveRules);
importFileButton.addEventListener("click", importFromFile);
exportFileButton.addEventListener("click", exportToFile);

rulesSourceInputs.forEach((input) => {
  input.addEventListener("change", () => {
    const selected = rulesSourceInputs.find((item) => item.checked);
    const value = selected ? selected.value : "editor";
    chrome.storage.local.set({ rulesSource: value }, () => {
      updateRulesSourceUI(value);
      setStatus(t("status_rules_source_updated", null, "Rules source updated."), "#3c5a2a");
    });
  });
});

highlightEnabledInput.addEventListener("change", () => {
  highlightColorInput.disabled = !highlightEnabledInput.checked;
  highlightColorText.disabled = !highlightEnabledInput.checked;
  saveDisplaySettings();
});

highlightColorInput.addEventListener("change", () => {
  highlightColorText.value = highlightColorInput.value;
  saveDisplaySettings();
});

highlightColorText.addEventListener("change", () => {
  const value = highlightColorText.value.trim();
  if (value) {
    highlightColorInput.value = value;
    saveDisplaySettings();
  }
});

maxOnePerBlockInput.addEventListener("change", () => {
  saveReplacementSettings();
});

allowAdjacentInput.addEventListener("change", () => {
  saveReplacementSettings();
});

if (srsEnabledInput) {
  srsEnabledInput.addEventListener("change", saveSrsSettings);
}
if (srsMaxActiveInput) {
  srsMaxActiveInput.addEventListener("change", saveSrsSettings);
}
if (srsSoundInput) {
  srsSoundInput.addEventListener("change", saveSrsSettings);
}
if (srsHighlightInput) {
  srsHighlightInput.addEventListener("change", () => {
    if (srsHighlightTextInput) {
      srsHighlightTextInput.value = srsHighlightInput.value;
    }
    saveSrsSettings();
  });
}
if (srsHighlightTextInput) {
  srsHighlightTextInput.addEventListener("change", () => {
    const value = srsHighlightTextInput.value.trim();
    if (value) {
      srsHighlightInput.value = value;
      saveSrsSettings();
    }
  });
}
if (srsFeedbackSrsInput) {
  srsFeedbackSrsInput.addEventListener("change", saveSrsSettings);
}
if (srsFeedbackRulesInput) {
  srsFeedbackRulesInput.addEventListener("change", saveSrsSettings);
}
if (srsExposureLoggingInput) {
  srsExposureLoggingInput.addEventListener("change", saveSrsSettings);
}
if (srsSampleButton) {
  srsSampleButton.addEventListener("click", sampleActiveWords);
}
if (srsRulegenButton) {
  srsRulegenButton.addEventListener("click", previewSrsRulegen);
}

debugEnabledInput.addEventListener("change", () => {
  debugFocusInput.disabled = !debugEnabledInput.checked;
  saveDisplaySettings();
});

debugFocusInput.addEventListener("change", () => {
  saveDisplaySettings();
});

enabledInput.addEventListener("change", () => {
  chrome.storage.local.set({ enabled: enabledInput.checked }, () => {
    setStatus(t("status_extension_updated", null, "Extension updated."), "#3c5a2a");
  });
});

if (languageSelect) {
  languageSelect.addEventListener("change", () => {
    const value = languageSelect.value || "system";
    chrome.storage.local.set({ uiLanguage: value }, () => {
      loadLocaleMessages(value);
      setStatus(t("status_language_updated", null, "Language updated."), "#3c5a2a");
    });
  });
}

if (sourceLanguageInput) {
  sourceLanguageInput.addEventListener("change", saveLanguageSettings);
}
if (targetLanguageInput) {
  targetLanguageInput.addEventListener("change", saveLanguageSettings);
}

if (openDesktopAppButton) {
  openDesktopAppButton.addEventListener("click", () => {
    window.open(INTEGRATION_LINKS.app, "_blank", "noopener");
  });
}

if (openBdPluginButton) {
  openBdPluginButton.addEventListener("click", () => {
    window.open(INTEGRATION_LINKS.plugin, "_blank", "noopener");
  });
}

generateCodeButton.addEventListener("click", generateShareCode);
importCodeButton.addEventListener("click", importShareCode);
copyCodeButton.addEventListener("click", copyShareCode);

load();
