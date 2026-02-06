const settingsManager = new SettingsManager();

const i18n = new LocalizationService();
const t = (k, s, f) => i18n.t(k, s, f);
const rulesManager = new RulesManager(settingsManager, i18n);
const ui = new UIManager(i18n);

function logOptions(...args) {
  console.log("[LexiShift][Options]", ...args);
}
const helperManager = new HelperManager(i18n, logOptions);

function errorMessage(err, fallbackKey, fallbackText) {
  if (err instanceof SyntaxError) {
    return t(fallbackKey, null, fallbackText);
  }
  if (err && err.message) {
    return err.message;
  }
  return t(fallbackKey, null, fallbackText);
}

i18n.apply();

// Map UIManager elements to local variables to minimize diff churn
const {
  enabled: enabledInput,
  highlightEnabled: highlightEnabledInput,
  highlightColor: highlightColorInput,
  highlightColorText: highlightColorText,
  maxOnePerBlock: maxOnePerBlockInput,
  allowAdjacent: allowAdjacentInput,
  debugEnabled: debugEnabledInput,
  debugFocusWord: debugFocusInput,
  srsEnabled: srsEnabledInput,
  sourceLanguage: sourceLanguageInput,
  targetLanguage: targetLanguageInput,
  srsMaxActive: srsMaxActiveInput,
  srsSoundEnabled: srsSoundInput,
  srsHighlightColor: srsHighlightInput,
  srsHighlightColorText: srsHighlightTextInput,
  srsFeedbackSrsEnabled: srsFeedbackSrsInput,
  srsFeedbackRulesEnabled: srsFeedbackRulesInput,
  srsExposureLoggingEnabled: srsExposureLoggingInput,
  srsSample: srsSampleButton,
  srsSampleOutput: srsSampleOutput,
  srsInitializeSet: srsInitializeSetButton,
  srsRulegenPreview: srsRulegenButton,
  srsRulegenOutput: srsRulegenOutput,
  srsReset: srsResetButton,
  helperRefresh: helperRefreshButton,
  debugHelperTest: debugHelperTestButton,
  debugHelperTestOutput: debugHelperTestOutput,
  debugOpenDataDir: debugOpenDataDirButton,
  debugOpenDataDirOutput: debugOpenDataDirOutput,
  uiLanguage: languageSelect,
  rules: rulesInput,
  save: saveButton,
  rulesSourceInputs: rulesSourceInputs,
  rulesFile: rulesFileInput,
  importFile: importFileButton,
  exportFile: exportFileButton,
  fileStatus: fileStatus,
  shareCode: shareCodeInput,
  shareCodeCjk: shareCodeCjk,
  generateCode: generateCodeButton,
  importCode: importCodeButton,
  copyCode: copyCodeButton,
  openDesktopApp: openDesktopAppButton,
  openBdPlugin: openBdPluginButton
} = ui.dom;

function setStatus(message, color) {
  ui.setStatus(message, color);
}

function setHelperStatus(status, lastSync) {
  ui.setHelperStatus(status, lastSync);
}

function updateRulesMeta(rules, updatedAt) {
  ui.updateRulesMeta(rules, updatedAt);
}

function updateRulesSourceUI(source) {
  ui.updateRulesSourceUI(source);
}

function resolvePairFromInputs() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  const prefs = globalThis.LexiShift && globalThis.LexiShift.languagePrefs;
  if (prefs && typeof prefs.resolveLanguagePair === "function") {
    return prefs.resolveLanguagePair({
      sourceLanguage,
      targetLanguage,
      srsPairAuto: true,
      srsPair: settingsManager.defaults.srsPair || "en-en"
    });
  }
  return `${sourceLanguage}-${targetLanguage}`;
}

function loadSrsProfileForPair(items, pairKey) {
  const profile = settingsManager.getSrsProfile(items, pairKey);
  ui.updateSrsInputs(profile);
}

function saveDisplaySettings() {
  const highlightEnabled = highlightEnabledInput.checked;
  const highlightColor = highlightColorInput.value || settingsManager.defaults.highlightColor;
  const debugEnabled = debugEnabledInput.checked;
  const debugFocusWord = debugFocusInput.value.trim();
  chrome.storage.local.set({ highlightEnabled, highlightColor, debugEnabled, debugFocusWord }, () => {
    setStatus(t("status_display_saved", null, "Display settings saved."), ui.COLORS.SUCCESS);
  });
}

function saveReplacementSettings() {
  const maxOnePerTextBlock = maxOnePerBlockInput.checked;
  const allowAdjacentReplacements = allowAdjacentInput.checked;
  chrome.storage.local.set({ maxOnePerTextBlock, allowAdjacentReplacements }, () => {
    setStatus(t("status_replacement_saved", null, "Replacement settings saved."), ui.COLORS.SUCCESS);
  });
}

async function saveSrsSettings() {
  if (!srsEnabledInput || !srsMaxActiveInput) {
    return;
  }
  const srsEnabled = srsEnabledInput.checked;
  const pairKey = resolvePairFromInputs();
  const maxActiveRaw = parseInt(srsMaxActiveInput.value, 10);
  const srsMaxActive = Number.isFinite(maxActiveRaw)
    ? Math.max(1, maxActiveRaw)
    : (settingsManager.defaults.srsMaxActive || 20);
  const srsSoundEnabled = srsSoundInput ? srsSoundInput.checked : true;
  const srsHighlightColor = srsHighlightInput
    ? (srsHighlightInput.value || settingsManager.defaults.srsHighlightColor || "#2F74D0")
    : (settingsManager.defaults.srsHighlightColor || "#2F74D0");
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
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  srsMaxActiveInput.value = String(srsMaxActive);
  if (srsHighlightInput) {
    srsHighlightInput.value = srsHighlightColor;
  }
  if (srsHighlightTextInput) {
    srsHighlightTextInput.value = srsHighlightColor;
  }

  await settingsManager.updateSrsProfile(pairKey, profile, {
    sourceLanguage,
    targetLanguage,
    srsPairAuto: true,
    srsEnabled
  });

  setStatus(t("status_srs_saved", null, "SRS settings saved."), ui.COLORS.SUCCESS);
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

function saveLanguageSettings() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  const pairKey = resolvePairFromInputs();
  chrome.storage.local.get(settingsManager.defaults, (items) => {
    chrome.storage.local.set(
      { sourceLanguage, targetLanguage, srsPairAuto: true, srsPair: pairKey },
      () => {
        loadSrsProfileForPair(items, pairKey);
        setStatus(t("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
      }
    );
  });
}

async function saveRules() {
  if (rulesInput.disabled) {
    setStatus(
      t("status_switch_edit_json", null, "Switch to Edit JSON to save changes."),
      ui.COLORS.ERROR
    );
    return;
  }
  try {
    const { rules, updatedAt } = await rulesManager.saveFromEditor(rulesInput.value);
    updateRulesSourceUI("editor");
    updateRulesMeta(rules, updatedAt);
    setStatus(t("status_rules_saved", null, "Rules saved."), ui.COLORS.SUCCESS);
  } catch (err) {
    setStatus(errorMessage(err, "status_invalid_json", "Invalid JSON file."), ui.COLORS.ERROR);
  }
}

async function importFromFile() {
  const file = rulesFileInput.files && rulesFileInput.files[0];
  if (!file) {
    setStatus(t("status_choose_json_file", null, "Choose a JSON file first."), "#b42318");
    return;
  }
  try {
    const { rules, updatedAt, fileName } = await rulesManager.importFromFile(file);
    rulesInput.value = JSON.stringify(rules, null, 2);
    updateRulesSourceUI("file");
    updateRulesMeta(rules, updatedAt);
    fileStatus.textContent = t("file_status_last_imported", fileName, `Last imported: ${fileName}`);
    setStatus(t("status_imported_rules", String(rules.length), `Imported ${rules.length} rules.`), ui.COLORS.SUCCESS);
  } catch (err) {
    setStatus(errorMessage(err, "status_invalid_json", "Invalid JSON file."), ui.COLORS.ERROR);
  }
}

function exportToFile() {
  rulesManager.exportToFile();
  setStatus(t("status_exported_rules", null, "Exported rules."), ui.COLORS.SUCCESS);
}

function generateShareCode() {
  try {
    const code = rulesManager.generateShareCode(shareCodeCjk.checked, rulesInput.value, rulesInput.disabled);
    shareCodeInput.value = code;
    setStatus(
      t(
        "status_generated_code",
        String(shareCodeInput.value.length),
        `Code generated (${shareCodeInput.value.length} chars).`
      ),
      ui.COLORS.SUCCESS
    );
  } catch (err) {
    setStatus(
      err && err.message ? err.message : t("status_generate_failed", null, "Failed to generate code."),
      ui.COLORS.ERROR
    );
  }
}

async function importShareCode() {
  try {
    const { rules, updatedAt } = await rulesManager.importShareCode(shareCodeInput.value, shareCodeCjk.checked);
    rulesInput.value = JSON.stringify(rules, null, 2);
    updateRulesSourceUI("editor");
    updateRulesMeta(rules, updatedAt);
    setStatus(t("status_code_imported", null, "Code imported."), ui.COLORS.SUCCESS);
  } catch (err) {
    setStatus(
      err && err.message ? err.message : t("status_invalid_code", null, "Invalid code."),
      ui.COLORS.ERROR
    );
  }
}

function copyShareCode() {
  if (!shareCodeInput.value) {
    return;
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(shareCodeInput.value).then(() => {
      setStatus(t("status_copied", null, "Copied."), ui.COLORS.SUCCESS);
    });
    return;
  }
  shareCodeInput.select();
  document.execCommand("copy");
  setStatus(t("status_copied", null, "Copied."), ui.COLORS.SUCCESS);
}

async function load() {
  const items = await settingsManager.load();
    enabledInput.checked = items.enabled;
    highlightEnabledInput.checked = items.highlightEnabled !== false;
    highlightColorInput.value = items.highlightColor || settingsManager.defaults.highlightColor;
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
      sourceLanguageInput.value = items.sourceLanguage || settingsManager.defaults.sourceLanguage || "en";
    }
    if (targetLanguageInput) {
      targetLanguageInput.value = items.targetLanguage || settingsManager.defaults.targetLanguage || "en";
    }
    const pairKey = resolvePairFromInputs();
    loadSrsProfileForPair(items, pairKey);
    if (srsSampleOutput) {
      srsSampleOutput.textContent = "";
    }
    if (srsRulegenOutput) {
      srsRulegenOutput.textContent = "";
    }
    if (debugHelperTestOutput) {
      debugHelperTestOutput.textContent = "";
    }
    if (debugOpenDataDirOutput) {
      debugOpenDataDirOutput.textContent = "";
    }
    setHelperStatus("", "");
    if (languageSelect) {
      languageSelect.value = items.uiLanguage || "system";
    }
    settingsManager.currentRules = items.rules || [];
    rulesInput.value = JSON.stringify(settingsManager.currentRules, null, 2);
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
    updateRulesMeta(settingsManager.currentRules, items.rulesUpdatedAt);
    i18n.load(items.uiLanguage || "system");
}

async function refreshHelperStatus() {
  setHelperStatus(t("status_helper_connecting", null, "Connecting…"), "");
  const result = await helperManager.getStatus();
  setHelperStatus(result.message, result.lastRun);
}

async function testHelperConnection() {
  if (!debugHelperTestButton || !debugHelperTestOutput) {
    return;
  }
  debugHelperTestButton.disabled = true;
  debugHelperTestOutput.textContent = t("status_helper_connecting", null, "Connecting…");
  const message = await helperManager.testConnection();
  debugHelperTestOutput.textContent = message;
  debugHelperTestButton.disabled = false;
}

async function openHelperDataDir() {
  if (!debugOpenDataDirButton || !debugOpenDataDirOutput) {
    return;
  }
  debugOpenDataDirButton.disabled = true;
  debugOpenDataDirOutput.textContent = t("status_helper_connecting", null, "Connecting…");
  const message = await helperManager.openDataDir();
  debugOpenDataDirOutput.textContent = message;
  debugOpenDataDirButton.disabled = false;
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
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
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

async function initializeSrsSet() {
  if (!srsInitializeSetButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  const maxActiveRaw = parseInt(srsMaxActiveInput.value, 10);
  const srsMaxActive = Number.isFinite(maxActiveRaw)
    ? Math.max(1, maxActiveRaw)
    : (settingsManager.defaults.srsMaxActive || 20);
  const setTopN = Math.max(200, srsMaxActive * 20);

  srsInitializeSetButton.disabled = true;
  srsRulegenOutput.textContent = t("status_srs_set_init_running", null, "Initializing S…");

  try {
    const items = await settingsManager.load();
    const profileContext = settingsManager.buildSrsPlanContext(items, srsPair);
    const planOptions = {
      strategy: "profile_bootstrap",
      objective: "bootstrap",
      trigger: "options_initialize_button",
      profileContext
    };
    const result = await helperManager.initializeSrsSet(srsPair, setTopN, planOptions);
    const total = Number(result.total_items_for_pair || 0);
    const added = Number(result.added_items || 0);
    const applied = result.applied !== false;
    const plan = result.plan && typeof result.plan === "object" ? result.plan : {};
    const notes = Array.isArray(plan.notes) ? plan.notes : [];
    const noteLines = notes.length ? notes.map((note) => `- ${note}`) : [];
    const header = applied
      ? t(
          "status_srs_set_init_result",
          [added, total, srsPair],
          `S initialized for ${srsPair}: +${added} items (total ${total}).`
        )
      : t(
          "status_srs_set_plan_result",
          [srsPair],
          `S planning completed for ${srsPair}.`
        );
    srsRulegenOutput.textContent = [
      header,
      `- applied: ${applied}`,
      `- strategy_requested: ${plan.strategy_requested || "n/a"}`,
      `- strategy_effective: ${plan.strategy_effective || "n/a"}`,
      `- set_top_n: ${result.set_top_n ?? setTopN}`,
      `- source_type: ${result.source_type || "initial_set"}`,
      `- store_path: ${result.store_path || "n/a"}`,
      noteLines.length ? "" : null,
      noteLines.length ? "Plan notes:" : null,
      ...noteLines
    ].filter(Boolean).join("\n");
    const statusMessage = applied
      ? t("status_srs_set_init_success", [srsPair], `S initialized for ${srsPair}.`)
      : t("status_srs_set_plan_only", [srsPair], `S planning completed for ${srsPair}; no changes were applied.`);
    setStatus(statusMessage, applied ? ui.COLORS.SUCCESS : ui.COLORS.DEFAULT);
    logOptions("SRS set initialized", {
      pair: srsPair,
      setTopN,
      applied,
      plan,
      profileContext
    });
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_srs_set_init_failed", null, "S initialization failed.");
    srsRulegenOutput.textContent = msg;
    setStatus(msg, ui.COLORS.ERROR);
    logOptions("SRS set init failed.", err);
  } finally {
    srsInitializeSetButton.disabled = false;
  }
}

async function previewSrsRulegen() {
  if (!srsRulegenButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  const maxActiveRaw = parseInt(srsMaxActiveInput.value, 10);
  const srsMaxActive = Number.isFinite(maxActiveRaw)
    ? Math.max(1, maxActiveRaw)
    : (settingsManager.defaults.srsMaxActive || 20);
  srsRulegenButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_rulegen_running",
    null,
    "Running rulegen…"
  );

  try {
      const { rulegenData, snapshot, duration } = await helperManager.runRulegenPreview(srsPair, srsMaxActive);
      const rulegenTargets = Number(rulegenData.targets || 0);
      const rulegenRules = Number(rulegenData.rules || 0);
      const targets = snapshot && Array.isArray(snapshot.targets) ? snapshot.targets : [];
      const header = t(
        "status_srs_rulegen_result_header",
        [rulegenTargets, rulegenRules, duration],
        `Rulegen: ${rulegenTargets} targets, ${rulegenRules} rules (${duration}s)`
      );
      if (!targets.length) {
        const diag = rulegenData.diagnostics || {};
        const missingInputs = Array.isArray(diag.missing_inputs) ? diag.missing_inputs : [];
        const guidanceLines = [];
        if (diag.set_source_db && diag.set_source_db_exists === false) {
          guidanceLines.push(
            t("diag_missing_freq_pack", null, "Missing frequency pack for target language."),
            t("diag_expected_path", [diag.set_source_db], `Expected: ${diag.set_source_db}`),
            t("diag_fix_freq_pack", null, "Fix: open LexiShift App → Settings → Frequency Packs and download the target pack.")
          );
        }
        if (diag.jmdict_path && diag.jmdict_exists === false) {
          guidanceLines.push(
            t("diag_missing_jmdict", null, "Missing JMDict language pack."),
            t("diag_expected_path", [diag.jmdict_path], `Expected: ${diag.jmdict_path}`),
            t("diag_fix_jmdict", null, "Fix: open LexiShift App → Settings → Language Packs and download JMDict.")
          );
        }
        if (!guidanceLines.length && missingInputs.length) {
          guidanceLines.push(t("diag_missing_inputs", null, "Missing inputs:"), ...missingInputs.map((item) => `- ${item.type}: ${item.path}`));
        }
        const diagLines = [
          t("diag_header", null, "Diagnostics:"),
          `- ${t("label_pair", null, "pair")}: ${diag.pair || srsPair}`,
          `- jmdict: ${diag.jmdict_path || "n/a"} (exists=${diag.jmdict_exists})`,
          `- set_source_db: ${diag.set_source_db || "n/a"} (exists=${diag.set_source_db_exists})`,
          `- store_items: ${diag.store_items ?? "n/a"}`,
          `- store_items_for_pair: ${diag.store_items_for_pair ?? "n/a"}`,
          `- store_sample: ${(Array.isArray(diag.store_sample) ? diag.store_sample.join(", ") : "n/a")}`
        ];
        if (guidanceLines.length) {
          diagLines.push("", t("label_fix", null, "Fix:"), ...guidanceLines);
        }
        srsRulegenOutput.textContent = [
          header,
          t("status_srs_rulegen_empty", null, "No rules found for current active words."),
          "",
          ...diagLines
        ].join("\n");
      } else {
        // Ensure targets are sorted by lemma for consistent display
        const sortedTargets = [...targets].sort((a, b) => {
          const lemmaA = String(a.lemma || "");
          const lemmaB = String(b.lemma || "");
          return lemmaA.localeCompare(lemmaB);
        });

        const lines = sortedTargets.map((entry) => {
          const lemma = String(entry.lemma || "").trim();
          const sources = Array.isArray(entry.sources) ? entry.sources : [];
          if (!lemma) return null;
          if (!sources.length) {
            return t(
              "status_srs_rulegen_line_no_rules",
              [lemma],
              `${lemma} → (no rules)`
            );
          }
          return t(
            "status_srs_rulegen_line_rules",
            [lemma, sources.join(", ")],
            `${lemma} → ${sources.join(", ")}`
          );
        }).filter(Boolean);
        srsRulegenOutput.textContent = [header, "", ...lines].join("\n");
      }
      logOptions("SRS rulegen preview (helper)", {
        pair: srsPair,
        targets: targets.length,
        diagnostics: rulegenData.diagnostics || null
      });
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_srs_rulegen_failed", null, "Rule preview failed.");
    srsRulegenOutput.textContent = msg;
    logOptions("SRS rulegen preview failed.", err);
  } finally {
    srsRulegenButton.disabled = false;
  }
}

async function resetSrsData() {
  if (!srsResetButton) return;

  // Confirmation 1
  if (!confirm(t("confirm_srs_reset_1", null, "Are you sure you want to reset all SRS progress for this language pair? This cannot be undone."))) {
    return;
  }

  // Confirmation 2
  if (!confirm(t("confirm_srs_reset_2", null, "Really delete all learning history and start over for this pair?"))) {
    return;
  }

  const srsPair = resolvePairFromInputs();
  logOptions(`[Reset] User confirmed reset for pair: ${srsPair}`);
  srsResetButton.disabled = true;
  setStatus(t("status_srs_resetting", null, "Resetting SRS data…"), ui.COLORS.DEFAULT);

  try {
    await helperManager.resetSrs(srsPair);
    logOptions("[Reset] Helper returned success.");
    setStatus(t("status_srs_reset_success", null, "SRS data reset successfully."), ui.COLORS.SUCCESS);
    if (srsRulegenOutput) srsRulegenOutput.textContent = "";
    if (srsSampleOutput) srsSampleOutput.textContent = "";
  } catch (err) {
    logOptions("[Reset] Failed:", err);
    let msg = err && err.message ? err.message : t("status_srs_reset_failed", null, "SRS reset failed.");
    if (msg.includes("Unknown command")) {
      msg = t("status_srs_reset_outdated", null, "Helper outdated: command not found. Restart helper?");
    }
    setStatus(msg, ui.COLORS.ERROR);
  } finally {
    srsResetButton.disabled = false;
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
      setStatus(t("status_rules_source_updated", null, "Rules source updated."), ui.COLORS.SUCCESS);
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
if (srsInitializeSetButton) {
  srsInitializeSetButton.addEventListener("click", initializeSrsSet);
}
if (srsRulegenButton) {
  srsRulegenButton.addEventListener("click", previewSrsRulegen);
}
if (srsResetButton) {
  srsResetButton.addEventListener("click", resetSrsData);
}
if (helperRefreshButton) {
  helperRefreshButton.addEventListener("click", refreshHelperStatus);
}
if (debugHelperTestButton) {
  debugHelperTestButton.addEventListener("click", testHelperConnection);
}
if (debugOpenDataDirButton) {
  debugOpenDataDirButton.addEventListener("click", openHelperDataDir);
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
    setStatus(t("status_extension_updated", null, "Extension updated."), ui.COLORS.SUCCESS);
  });
});

if (languageSelect) {
  languageSelect.addEventListener("change", () => {
    const value = languageSelect.value || "system";
    chrome.storage.local.set({ uiLanguage: value }, () => {
      i18n.load(value);
      setStatus(t("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
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
    window.open(ui.LINKS.app, "_blank", "noopener");
  });
}

if (openBdPluginButton) {
  openBdPluginButton.addEventListener("click", () => {
    window.open(ui.LINKS.plugin, "_blank", "noopener");
  });
}

generateCodeButton.addEventListener("click", generateShareCode);
importCodeButton.addEventListener("click", importShareCode);
copyCodeButton.addEventListener("click", copyShareCode);

load();
refreshHelperStatus();
