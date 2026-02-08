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
  maxReplacementsPerPage: maxReplacementsPerPageInput,
  maxReplacementsPerLemmaPage: maxReplacementsPerLemmaPageInput,
  debugEnabled: debugEnabledInput,
  debugFocusWord: debugFocusInput,
  srsEnabled: srsEnabledInput,
  sourceLanguage: sourceLanguageInput,
  targetLanguage: targetLanguageInput,
  srsProfileId: srsProfileIdInput,
  srsProfileRefresh: srsProfileRefreshButton,
  srsProfileStatus: srsProfileStatusOutput,
  srsMaxActive: srsMaxActiveInput,
  srsBootstrapTopN: srsBootstrapTopNInput,
  srsInitialActiveCount: srsInitialActiveCountInput,
  srsSoundEnabled: srsSoundInput,
  srsHighlightColor: srsHighlightInput,
  srsHighlightColorText: srsHighlightTextInput,
  srsFeedbackSrsEnabled: srsFeedbackSrsInput,
  srsFeedbackRulesEnabled: srsFeedbackRulesInput,
  srsExposureLoggingEnabled: srsExposureLoggingInput,
  srsSample: srsSampleButton,
  srsSampleOutput: srsSampleOutput,
  srsInitializeSet: srsInitializeSetButton,
  srsRefreshSet: srsRefreshSetButton,
  srsRuntimeDiagnostics: srsRuntimeDiagnosticsButton,
  srsRulegenPreview: srsRulegenButton,
  srsRulegenSampledPreview: srsRulegenSampledButton,
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

let helperProfilesCache = null;
let helperProfilesCacheTs = 0;

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

function applyLanguagePrefsToInputs(languagePrefs) {
  const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
  const sourceLanguage = String(prefs.sourceLanguage || settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = String(prefs.targetLanguage || settingsManager.defaults.targetLanguage || "en");
  if (sourceLanguageInput) {
    sourceLanguageInput.value = sourceLanguage;
  }
  if (targetLanguageInput) {
    targetLanguageInput.value = targetLanguage;
  }
  const pair = String(prefs.srsPair || "").trim();
  return pair || resolvePairFromInputs();
}

function resolveHelperProfileItems(payload) {
  const profiles = payload && Array.isArray(payload.profiles) ? payload.profiles : [];
  return profiles
    .map((profile) => {
      if (!profile || typeof profile !== "object") {
        return null;
      }
      const profileId = String(profile.profile_id || "").trim();
      if (!profileId) {
        return null;
      }
      return {
        profileId,
        name: String(profile.name || profileId).trim() || profileId
      };
    })
    .filter(Boolean);
}

function renderSrsProfileControls(selectedProfileId, helperProfilesPayload) {
  const resolvedProfileId = String(selectedProfileId || "default").trim() || "default";
  const helperItems = resolveHelperProfileItems(helperProfilesPayload);
  const fallbackIds = [resolvedProfileId, "default"]
    .map((value) => String(value || "").trim())
    .filter(Boolean);
  const merged = [];
  const seen = new Set();
  for (const item of helperItems) {
    if (seen.has(item.profileId)) {
      continue;
    }
    seen.add(item.profileId);
    merged.push(item);
  }
  for (const profileId of fallbackIds) {
    if (seen.has(profileId)) {
      continue;
    }
    seen.add(profileId);
    merged.push({ profileId, name: profileId });
  }

  if (srsProfileIdInput) {
    const previousValue = srsProfileIdInput.value;
    srsProfileIdInput.innerHTML = "";
    merged.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.profileId;
      option.textContent = `${item.name} (${item.profileId})`;
      srsProfileIdInput.appendChild(option);
    });
    const fallbackValue = merged.length ? merged[0].profileId : "default";
    const nextValue = merged.some((item) => item.profileId === resolvedProfileId)
      ? resolvedProfileId
      : (merged.some((item) => item.profileId === previousValue) ? previousValue : fallbackValue);
    srsProfileIdInput.value = nextValue || "default";
    srsProfileIdInput.disabled = merged.length === 0;
  }
  if (srsProfileStatusOutput) {
    srsProfileStatusOutput.textContent = t(
      "status_srs_profile_selected",
      [resolvedProfileId],
      `Selected SRS profile: ${resolvedProfileId}.`
    );
  }
}

async function fetchHelperProfiles(options) {
  const opts = options && typeof options === "object" ? options : {};
  const force = opts.force === true;
  const now = Date.now();
  if (!force && helperProfilesCache && now - helperProfilesCacheTs < 10_000) {
    return helperProfilesCache;
  }
  const result = await helperManager.getProfiles();
  if (result && result.ok) {
    helperProfilesCache = result.data || null;
    helperProfilesCacheTs = now;
  }
  return result && result.ok ? (result.data || null) : null;
}

async function syncSelectedSrsProfile(items, options) {
  const opts = options && typeof options === "object" ? options : {};
  const forceHelperRefresh = opts.forceHelperRefresh === true;
  let workingItems = items;
  let selectedProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
  const helperProfilesPayload = await fetchHelperProfiles({ force: forceHelperRefresh });
  const helperProfileItems = resolveHelperProfileItems(helperProfilesPayload);
  const helperProfileIds = helperProfileItems.map((item) => item.profileId);
  const hasSelectedProfile = helperProfileIds.length
    ? helperProfileIds.includes(selectedProfileId)
    : true;

  if (!hasSelectedProfile) {
    const nextProfileId = helperProfileIds.includes("default")
      ? "default"
      : (helperProfileIds[0] || settingsManager.DEFAULT_PROFILE_ID);
    if (nextProfileId && nextProfileId !== selectedProfileId) {
      await settingsManager.updateSelectedSrsProfileId(nextProfileId);
      workingItems = await settingsManager.load();
      selectedProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
      const languagePrefs = settingsManager.getProfileLanguagePrefs(workingItems, { profileId: selectedProfileId });
      applyLanguagePrefsToInputs(languagePrefs);
      await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId: selectedProfileId });
    }
  }

  renderSrsProfileControls(selectedProfileId, helperProfilesPayload);
  return {
    items: workingItems,
    profileId: selectedProfileId,
    helperProfilesPayload
  };
}

async function loadSrsProfileForPair(items, pairKey, options) {
  const synced = await syncSelectedSrsProfile(items, options);
  const profile = settingsManager.getSrsProfile(synced.items, pairKey, {
    profileId: synced.profileId
  });
  ui.updateSrsInputs(profile);
  if (srsEnabledInput) {
    srsEnabledInput.checked = profile.srsEnabled === true;
  }
  await settingsManager.publishSrsRuntimeProfile(pairKey, profile, {
    sourceLanguage: sourceLanguageInput
      ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
      : (settingsManager.defaults.sourceLanguage || "en"),
    targetLanguage: targetLanguageInput
      ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
      : (settingsManager.defaults.targetLanguage || "en"),
    srsPairAuto: true,
    srsSelectedProfileId: synced.profileId
  }, {
    profileId: synced.profileId
  });
  logOptions("Loaded SRS profile settings.", {
    pair: pairKey,
    profileId: synced.profileId
  });
  return { profile, profileId: synced.profileId, items: synced.items };
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
  const maxPerPageRaw = maxReplacementsPerPageInput
    ? parseInt(maxReplacementsPerPageInput.value, 10)
    : settingsManager.defaults.maxReplacementsPerPage;
  const maxPerLemmaRaw = maxReplacementsPerLemmaPageInput
    ? parseInt(maxReplacementsPerLemmaPageInput.value, 10)
    : settingsManager.defaults.maxReplacementsPerLemmaPerPage;
  const maxReplacementsPerPage = Number.isFinite(maxPerPageRaw)
    ? Math.max(0, maxPerPageRaw)
    : (settingsManager.defaults.maxReplacementsPerPage || 0);
  const maxReplacementsPerLemmaPerPage = Number.isFinite(maxPerLemmaRaw)
    ? Math.max(0, maxPerLemmaRaw)
    : (settingsManager.defaults.maxReplacementsPerLemmaPerPage || 0);
  if (maxReplacementsPerPageInput) {
    maxReplacementsPerPageInput.value = String(maxReplacementsPerPage);
  }
  if (maxReplacementsPerLemmaPageInput) {
    maxReplacementsPerLemmaPageInput.value = String(maxReplacementsPerLemmaPerPage);
  }
  chrome.storage.local.set({
    maxOnePerTextBlock,
    allowAdjacentReplacements,
    maxReplacementsPerPage,
    maxReplacementsPerLemmaPerPage
  }, () => {
    setStatus(t("status_replacement_saved", null, "Replacement settings saved."), ui.COLORS.SUCCESS);
  });
}

async function saveSrsSettings() {
  if (!srsEnabledInput || !srsMaxActiveInput) {
    return;
  }
  const srsEnabled = srsEnabledInput.checked;
  const pairKey = resolvePairFromInputs();
  const items = await settingsManager.load();
  const syncedProfileState = await syncSelectedSrsProfile(items);
  const selectedProfileId = syncedProfileState.profileId;
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
  const sizing = settingsManager.resolveSrsSetSizing(
    {
      srsMaxActive,
      srsBootstrapTopN: srsBootstrapTopNInput ? srsBootstrapTopNInput.value : undefined,
      srsInitialActiveCount: srsInitialActiveCountInput ? srsInitialActiveCountInput.value : undefined
    },
    settingsManager.defaults
  );
  const profile = {
    srsEnabled,
    srsMaxActive,
    srsBootstrapTopN: sizing.srsBootstrapTopN,
    srsInitialActiveCount: sizing.srsInitialActiveCount,
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
  if (srsBootstrapTopNInput) {
    srsBootstrapTopNInput.value = String(sizing.srsBootstrapTopN);
  }
  if (srsInitialActiveCountInput) {
    srsInitialActiveCountInput.value = String(sizing.srsInitialActiveCount);
  }
  if (srsHighlightInput) {
    srsHighlightInput.value = srsHighlightColor;
  }
  if (srsHighlightTextInput) {
    srsHighlightTextInput.value = srsHighlightColor;
  }

  const updateResult = await settingsManager.updateSrsProfile(pairKey, profile, {
    sourceLanguage,
    targetLanguage,
    srsPairAuto: true,
    srsSelectedProfileId: selectedProfileId
  }, {
    profileId: selectedProfileId
  });
  await settingsManager.publishSrsRuntimeProfile(pairKey, profile, {
    sourceLanguage,
    targetLanguage,
    srsPairAuto: true,
    srsSelectedProfileId: selectedProfileId
  }, {
    profileId: selectedProfileId
  });

  setStatus(t("status_srs_saved", null, "SRS settings saved."), ui.COLORS.SUCCESS);
  logOptions("SRS settings saved.", {
    pair: pairKey,
    profileId: updateResult && updateResult.profileId ? updateResult.profileId : "default",
    sourceLanguage,
    targetLanguage,
    srsEnabled,
    srsMaxActive,
    srsBootstrapTopN: sizing.srsBootstrapTopN,
    srsInitialActiveCount: sizing.srsInitialActiveCount,
    srsSoundEnabled,
    srsHighlightColor,
    srsFeedbackSrsEnabled,
    srsFeedbackRulesEnabled,
    srsExposureLoggingEnabled
  });
}

async function saveLanguageSettings() {
  const sourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  const pairKey = resolvePairFromInputs();
  try {
    const items = await settingsManager.load();
    const profileId = settingsManager.getSelectedSrsProfileId(items);
    await settingsManager.updateProfileLanguagePrefs({
      sourceLanguage,
      targetLanguage,
      srsPairAuto: true,
      srsPair: pairKey
    }, {
      profileId
    });
    const refreshed = await settingsManager.load();
    await loadSrsProfileForPair(refreshed, pairKey);
    setStatus(t("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_language_updated", null, "Language updated.");
    setStatus(msg, ui.COLORS.ERROR);
    logOptions("Language update failed during SRS profile reload.", err);
  }
}

async function saveSrsProfileId() {
  if (!srsProfileIdInput) {
    return;
  }
  const beforeItems = await settingsManager.load();
  const previousProfileId = settingsManager.getSelectedSrsProfileId(beforeItems);
  const previousPair = resolvePairFromInputs();
  const previousSourceLanguage = sourceLanguageInput
    ? (sourceLanguageInput.value || settingsManager.defaults.sourceLanguage || "en")
    : (settingsManager.defaults.sourceLanguage || "en");
  const previousTargetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  await settingsManager.updateProfileLanguagePrefs({
    sourceLanguage: previousSourceLanguage,
    targetLanguage: previousTargetLanguage,
    srsPairAuto: true,
    srsPair: previousPair
  }, {
    profileId: previousProfileId
  });

  const profileId = String(srsProfileIdInput.value || "").trim() || settingsManager.DEFAULT_PROFILE_ID;
  await settingsManager.updateSelectedSrsProfileId(profileId);
  const items = await settingsManager.load();
  const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
  const pairKey = applyLanguagePrefsToInputs(languagePrefs);
  await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId });
  const refreshed = await settingsManager.load();
  await loadSrsProfileForPair(refreshed, pairKey);
  setStatus(t("status_srs_profile_saved", null, "SRS profile selection saved."), ui.COLORS.SUCCESS);
}

async function refreshSrsProfiles() {
  const pairKey = resolvePairFromInputs();
  if (srsProfileRefreshButton) {
    srsProfileRefreshButton.disabled = true;
  }
  if (srsProfileStatusOutput) {
    srsProfileStatusOutput.textContent = t(
      "hint_srs_profile_loading",
      null,
      "Loading helper profiles…"
    );
  }
  try {
    helperProfilesCache = null;
    helperProfilesCacheTs = 0;
    const items = await settingsManager.load();
    await loadSrsProfileForPair(items, pairKey, { forceHelperRefresh: true });
    setStatus(t("status_srs_profile_refreshed", null, "Helper profiles refreshed."), ui.COLORS.SUCCESS);
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_srs_profile_refresh_failed", null, "Failed to refresh helper profiles.");
    if (srsProfileStatusOutput) {
      srsProfileStatusOutput.textContent = msg;
    }
    setStatus(msg, ui.COLORS.ERROR);
  } finally {
    if (srsProfileRefreshButton) {
      srsProfileRefreshButton.disabled = false;
    }
  }
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
    if (maxReplacementsPerPageInput) {
      const maxPerPage = Number.isFinite(Number(items.maxReplacementsPerPage))
        ? Math.max(0, Number(items.maxReplacementsPerPage))
        : (settingsManager.defaults.maxReplacementsPerPage || 0);
      maxReplacementsPerPageInput.value = String(maxPerPage);
    }
    if (maxReplacementsPerLemmaPageInput) {
      const maxPerLemma = Number.isFinite(Number(items.maxReplacementsPerLemmaPerPage))
        ? Math.max(0, Number(items.maxReplacementsPerLemmaPerPage))
        : (settingsManager.defaults.maxReplacementsPerLemmaPerPage || 0);
      maxReplacementsPerLemmaPageInput.value = String(maxPerLemma);
    }
    debugEnabledInput.checked = items.debugEnabled === true;
    debugFocusInput.value = items.debugFocusWord || "";
    debugFocusInput.disabled = !debugEnabledInput.checked;
    const selectedProfileId = settingsManager.getSelectedSrsProfileId(items);
    const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId: selectedProfileId });
    const pairKey = applyLanguagePrefsToInputs(languagePrefs);
    await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId: selectedProfileId });
    await loadSrsProfileForPair(items, pairKey);
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

  srsInitializeSetButton.disabled = true;
  srsRulegenOutput.textContent = t("status_srs_set_init_running", null, "Initializing S…");

  try {
    const items = await settingsManager.load();
    const synced = await syncSelectedSrsProfile(items);
    const profile = settingsManager.getSrsProfile(synced.items, srsPair, {
      profileId: synced.profileId
    });
    const bootstrapTopN = Number(profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800);
    const initialActiveCount = Number(profile.srsInitialActiveCount || settingsManager.defaults.srsInitialActiveCount || 40);
    const maxActiveItemsHint = Number(profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 20);
    const profileContext = settingsManager.buildSrsPlanContext(synced.items, srsPair, {
      profileId: synced.profileId
    });
    const planOptions = {
      profileId: synced.profileId,
      strategy: "profile_bootstrap",
      objective: "bootstrap",
      trigger: "options_initialize_button",
      initialActiveCount,
      maxActiveItemsHint,
      profileContext
    };
    const result = await helperManager.initializeSrsSet(
      srsPair,
      {
        bootstrapTopN,
        initialActiveCount,
        maxActiveItemsHint
      },
      planOptions
    );
    const total = Number(result.total_items_for_pair || 0);
    const added = Number(result.added_items || 0);
    const applied = result.applied !== false;
    const plan = result.plan && typeof result.plan === "object" ? result.plan : {};
    const bootstrapDiagnostics = result.bootstrap_diagnostics && typeof result.bootstrap_diagnostics === "object"
      ? result.bootstrap_diagnostics
      : {};
    const notes = Array.isArray(plan.notes) ? plan.notes : [];
    const noteLines = notes.length ? notes.map((note) => `- ${note}`) : [];
    const publishedRulegen = result.rulegen && typeof result.rulegen === "object"
      ? result.rulegen
      : null;
    const initialActivePreview = Array.isArray(bootstrapDiagnostics.initial_active_preview)
      ? bootstrapDiagnostics.initial_active_preview
      : [];
    const admissionWeightProfile = bootstrapDiagnostics.admission_weight_profile
      && typeof bootstrapDiagnostics.admission_weight_profile === "object"
      ? bootstrapDiagnostics.admission_weight_profile
      : null;
    const initialActiveWeightPreview = Array.isArray(bootstrapDiagnostics.initial_active_weight_preview)
      ? bootstrapDiagnostics.initial_active_weight_preview
      : [];
    const admissionWeightSummary = admissionWeightProfile
      ? [
          ["noun", admissionWeightProfile.noun],
          ["adjective", admissionWeightProfile.adjective],
          ["verb", admissionWeightProfile.verb],
          ["adverb", admissionWeightProfile.adverb],
          ["other", admissionWeightProfile.other]
        ]
          .filter((entry) => Number.isFinite(Number(entry[1])))
          .map((entry) => `${entry[0]}=${Number(entry[1]).toFixed(2)}`)
          .join(", ")
      : "";
    const weightPreviewSummary = initialActiveWeightPreview.length
      ? initialActiveWeightPreview
        .slice(0, 10)
        .map((entry) => {
          const lemma = entry && entry.lemma ? String(entry.lemma) : "";
          const bucket = entry && entry.pos_bucket ? String(entry.pos_bucket) : "other";
          const score = entry && Number.isFinite(Number(entry.admission_weight))
            ? Number(entry.admission_weight).toFixed(3)
            : "n/a";
          return `${lemma}[${bucket}:${score}]`;
        })
        .join(", ")
      : "";
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
      `- bootstrap_top_n: ${result.bootstrap_top_n ?? result.set_top_n ?? bootstrapTopN}`,
      `- initial_active_count: ${result.initial_active_count ?? initialActiveCount}`,
      `- max_active_items_hint: ${result.max_active_items_hint ?? maxActiveItemsHint}`,
      `- source_type: ${result.source_type || "initial_set"}`,
      `- store_path: ${result.store_path || "n/a"}`,
      `- stopwords_path: ${result.stopwords_path || "n/a"}`,
      applied ? `- rulegen_published: ${publishedRulegen ? publishedRulegen.published !== false : false}` : null,
      applied && publishedRulegen ? `- rulegen_targets: ${publishedRulegen.targets ?? "n/a"}` : null,
      applied && publishedRulegen ? `- rulegen_rules: ${publishedRulegen.rules ?? "n/a"}` : null,
      applied && publishedRulegen ? `- ruleset_path: ${publishedRulegen.ruleset_path || "n/a"}` : null,
      applied ? `- selected_count: ${bootstrapDiagnostics.selected_count ?? "n/a"}` : null,
      applied ? `- selected_unique_count: ${bootstrapDiagnostics.selected_unique_count ?? "n/a"}` : null,
      applied ? `- admitted_count: ${bootstrapDiagnostics.admitted_count ?? "n/a"}` : null,
      applied ? `- inserted_count: ${bootstrapDiagnostics.inserted_count ?? "n/a"}` : null,
      applied ? `- updated_count: ${bootstrapDiagnostics.updated_count ?? "n/a"}` : null,
      applied && admissionWeightSummary ? `- admission_weight_profile: ${admissionWeightSummary}` : null,
      applied && initialActivePreview.length
        ? `- initial_active_preview: ${initialActivePreview.slice(0, 20).join(", ")}`
        : null,
      applied && weightPreviewSummary
        ? `- initial_active_weight_preview: ${weightPreviewSummary}`
        : null,
      noteLines.length ? "" : null,
      noteLines.length ? "Plan notes:" : null,
      ...noteLines
    ].filter(Boolean).join("\n");
    if (applied && publishedRulegen && publishedRulegen.published !== false) {
      await new Promise((resolve) => {
        chrome.storage.local.set(
          { srsRulesetUpdatedAt: new Date().toISOString() },
          () => resolve()
        );
      });
    }
    const statusMessage = applied
      ? t("status_srs_set_init_success", [srsPair], `S initialized for ${srsPair}.`)
      : t("status_srs_set_plan_only", [srsPair], `S planning completed for ${srsPair}; no changes were applied.`);
    setStatus(statusMessage, applied ? ui.COLORS.SUCCESS : ui.COLORS.DEFAULT);
    logOptions("SRS set initialized", {
      pair: srsPair,
      bootstrapTopN,
      initialActiveCount,
      maxActiveItemsHint,
      applied,
      plan,
      bootstrapDiagnostics,
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

async function refreshSrsSetNow() {
  if (!srsRefreshSetButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  srsRefreshSetButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_refresh_running",
    null,
    "Refreshing S and publishing rules…"
  );

  try {
    const items = await settingsManager.load();
    const synced = await syncSelectedSrsProfile(items);
    const profile = settingsManager.getSrsProfile(synced.items, srsPair, {
      profileId: synced.profileId
    });
    const profileContext = settingsManager.buildSrsPlanContext(synced.items, srsPair, {
      profileId: synced.profileId
    });
    const result = await helperManager.refreshSrsSet(srsPair, {
      profileId: synced.profileId,
      setTopN: profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800,
      maxActiveItems: profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
      trigger: "options_refresh_set_button",
      profileContext
    });
    const added = Number(result.added_items || 0);
    const applied = result.applied === true;
    const admission = result.admission_refresh && typeof result.admission_refresh === "object"
      ? result.admission_refresh
      : {};
    const feedbackWindow = admission.feedback_window && typeof admission.feedback_window === "object"
      ? admission.feedback_window
      : {};
    const publishedRulegen = result.rulegen && typeof result.rulegen === "object"
      ? result.rulegen
      : null;
    const header = applied
      ? t(
          "status_srs_refresh_success",
          [srsPair, added],
          `S refreshed for ${srsPair}: +${added} admitted.`
        )
      : t(
          "status_srs_refresh_noop",
          [srsPair],
          `S refresh for ${srsPair}: no new admissions.`
        );
    srsRulegenOutput.textContent = [
      header,
      `- applied: ${applied}`,
      `- added_items: ${added}`,
      `- total_items_for_pair: ${result.total_items_for_pair ?? "n/a"}`,
      `- max_active_items: ${result.max_active_items ?? "n/a"}`,
      `- max_new_items_per_day: ${result.max_new_items_per_day ?? "n/a"}`,
      `- reason_code: ${admission.reason_code || "n/a"}`,
      `- feedback_count: ${feedbackWindow.feedback_count ?? "n/a"}`,
      `- retention_ratio: ${feedbackWindow.retention_ratio ?? "n/a"}`,
      `- rulegen_published: ${publishedRulegen ? publishedRulegen.published !== false : false}`,
      publishedRulegen ? `- rulegen_targets: ${publishedRulegen.targets ?? "n/a"}` : null,
      publishedRulegen ? `- rulegen_rules: ${publishedRulegen.rules ?? "n/a"}` : null,
      publishedRulegen ? `- ruleset_path: ${publishedRulegen.ruleset_path || "n/a"}` : null
    ].filter(Boolean).join("\n");
    if (publishedRulegen && publishedRulegen.published !== false) {
      await new Promise((resolve) => {
        chrome.storage.local.set(
          { srsRulesetUpdatedAt: new Date().toISOString() },
          () => resolve()
        );
      });
    }
    setStatus(
      applied
        ? t("status_srs_refresh_success", [srsPair, added], `S refreshed for ${srsPair}: +${added} admitted.`)
        : t("status_srs_refresh_noop", [srsPair], `S refresh for ${srsPair}: no new admissions.`),
      applied ? ui.COLORS.SUCCESS : ui.COLORS.DEFAULT
    );
    logOptions("SRS set refreshed", { pair: srsPair, result });
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_srs_refresh_failed", null, "S refresh failed.");
    srsRulegenOutput.textContent = msg;
    setStatus(msg, ui.COLORS.ERROR);
    logOptions("SRS set refresh failed.", err);
  } finally {
    srsRefreshSetButton.disabled = false;
  }
}

async function runSrsRuntimeDiagnostics() {
  if (!srsRuntimeDiagnosticsButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  srsRuntimeDiagnosticsButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_diagnostics_running",
    null,
    "Collecting SRS runtime diagnostics…"
  );
  try {
    const items = await settingsManager.load();
    const selectedProfileId = settingsManager.getSelectedSrsProfileId(items);
    const diagnostics = await helperManager.getSrsRuntimeDiagnostics(srsPair, {
      profileId: selectedProfileId
    });
    const helperData = diagnostics.helper && typeof diagnostics.helper === "object"
      ? diagnostics.helper
      : null;
    const runtimeState = diagnostics.runtime_state && typeof diagnostics.runtime_state === "object"
      ? diagnostics.runtime_state
      : null;
    const lines = [
      t(
        "status_srs_diagnostics_header",
        [srsPair],
        `SRS Runtime Diagnostics (${srsPair})`
      ),
      `profile: ${selectedProfileId}`,
      "",
      "Helper (source of truth):",
      helperData
        ? `- store_items_for_pair: ${helperData.store_items_for_pair ?? "n/a"}`
        : `- unavailable: ${diagnostics.helper_error || "unknown"}`,
      helperData ? `- ruleset_rules_count: ${helperData.ruleset_rules_count ?? "n/a"}` : null,
      helperData ? `- snapshot_target_count: ${helperData.snapshot_target_count ?? "n/a"}` : null,
      helperData ? `- store_path: ${helperData.store_path || "n/a"}` : null,
      helperData ? `- ruleset_path: ${helperData.ruleset_path || "n/a"}` : null,
      "",
      "Extension cache:",
      `- cached_ruleset_rules: ${diagnostics.cache.ruleset_rules_count ?? 0}`,
      `- cached_snapshot_targets: ${diagnostics.cache.snapshot_target_count ?? 0}`,
      "",
      "Current tab/runtime (last reported):",
      runtimeState ? `- ts: ${runtimeState.ts || "n/a"}` : "- ts: n/a",
      runtimeState ? `- pair: ${runtimeState.pair || "n/a"}` : "- pair: n/a",
      runtimeState ? `- profile_id: ${runtimeState.profile_id || "n/a"}` : "- profile_id: n/a",
      runtimeState ? `- srs_enabled: ${runtimeState.srs_enabled === true}` : "- srs_enabled: n/a",
      runtimeState ? `- rules_source: ${runtimeState.rules_source || "n/a"}` : "- rules_source: n/a",
      runtimeState ? `- rules_local_enabled: ${runtimeState.rules_local_enabled ?? "n/a"}` : "- rules_local_enabled: n/a",
      runtimeState ? `- rules_srs_enabled: ${runtimeState.rules_srs_enabled ?? "n/a"}` : "- rules_srs_enabled: n/a",
      runtimeState ? `- active_rules_total: ${runtimeState.active_rules_total ?? "n/a"}` : "- active_rules_total: n/a",
      runtimeState ? `- active_rules_srs: ${runtimeState.active_rules_srs ?? "n/a"}` : "- active_rules_srs: n/a",
      runtimeState ? `- helper_rules_error: ${runtimeState.helper_rules_error || "none"}` : "- helper_rules_error: n/a",
      runtimeState ? `- frame_type: ${runtimeState.frame_type || "n/a"}` : "- frame_type: n/a"
    ].filter(Boolean);
    srsRulegenOutput.textContent = lines.join("\n");
    setStatus(
      t("status_srs_diagnostics_ready", null, "SRS runtime diagnostics updated."),
      ui.COLORS.SUCCESS
    );
    logOptions("SRS runtime diagnostics", diagnostics);
  } catch (err) {
    const msg = err && err.message
      ? err.message
      : t("status_srs_diagnostics_failed", null, "Failed to collect SRS diagnostics.");
    srsRulegenOutput.textContent = msg;
    setStatus(msg, ui.COLORS.ERROR);
    logOptions("SRS runtime diagnostics failed.", err);
  } finally {
    srsRuntimeDiagnosticsButton.disabled = false;
  }
}

async function previewSrsRulegen() {
  if (!srsRulegenButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  srsRulegenButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_rulegen_running",
    null,
    "Running rulegen…"
  );

  try {
      const items = await settingsManager.load();
      const profileId = settingsManager.getSelectedSrsProfileId(items);
      const { rulegenData, snapshot, duration } = await helperManager.runRulegenPreview(srsPair, {
        profileId
      });
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
      profileId,
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

async function previewSampledSrsRulegen() {
  if (!srsRulegenSampledButton || !srsRulegenOutput) {
    return;
  }
  const srsPair = resolvePairFromInputs();
  const sampleCount = 5;
  srsRulegenSampledButton.disabled = true;
  srsRulegenOutput.textContent = t(
    "status_srs_rulegen_sampled_running",
    [sampleCount],
    `Running sampled rulegen (${sampleCount})…`
  );

  try {
    const items = await settingsManager.load();
    const profileId = settingsManager.getSelectedSrsProfileId(items);
    const { rulegenData, snapshot, duration } = await helperManager.runSampledRulegenPreview(
      srsPair,
      sampleCount,
      { strategy: "weighted_priority", profileId }
    );
    const sampling = rulegenData.sampling && typeof rulegenData.sampling === "object"
      ? rulegenData.sampling
      : {};
    const sampledLemmas = Array.isArray(sampling.sampled_lemmas) ? sampling.sampled_lemmas : [];
    const sampledCount = Number(sampling.sample_count_effective || sampledLemmas.length || 0);
    const rulegenTargets = Number(rulegenData.targets || 0);
    const rulegenRules = Number(rulegenData.rules || 0);
    const targets = snapshot && Array.isArray(snapshot.targets) ? snapshot.targets : [];
    const header = t(
      "status_srs_rulegen_sampled_result_header",
      [sampledCount, rulegenTargets, rulegenRules, duration],
      `Sampled rulegen: ${sampledCount} words, ${rulegenTargets} targets, ${rulegenRules} rules (${duration}s)`
    );
    const samplingLines = [
      `- strategy_requested: ${sampling.strategy_requested || "n/a"}`,
      `- strategy_effective: ${sampling.strategy_effective || "n/a"}`,
      `- sample_count_requested: ${sampling.sample_count_requested ?? sampleCount}`,
      `- sample_count_effective: ${sampling.sample_count_effective ?? sampledCount}`,
      `- total_items_for_pair: ${sampling.total_items_for_pair ?? "n/a"}`,
      sampledLemmas.length ? `- sampled_lemmas: ${sampledLemmas.join(", ")}` : null
    ].filter(Boolean);
    if (!targets.length) {
      const diag = rulegenData.diagnostics || {};
      const diagLines = [
        t("diag_header", null, "Diagnostics:"),
        `- ${t("label_pair", null, "pair")}: ${diag.pair || srsPair}`,
        `- jmdict: ${diag.jmdict_path || "n/a"} (exists=${diag.jmdict_exists})`,
        `- set_source_db: ${diag.set_source_db || "n/a"} (exists=${diag.set_source_db_exists})`,
        `- store_items: ${diag.store_items ?? "n/a"}`,
        `- store_items_for_pair: ${diag.store_items_for_pair ?? "n/a"}`,
        `- store_sample: ${(Array.isArray(diag.store_sample) ? diag.store_sample.join(", ") : "n/a")}`
      ];
      srsRulegenOutput.textContent = [
        header,
        ...samplingLines,
        "",
        t("status_srs_rulegen_empty", null, "No rules found for current active words."),
        "",
        ...diagLines
      ].join("\n");
    } else {
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
      srsRulegenOutput.textContent = [header, ...samplingLines, "", ...lines].join("\n");
    }
    logOptions("SRS sampled rulegen preview (helper)", {
      pair: srsPair,
      profileId,
      sampledCount,
      sampledLemmas,
      targets: targets.length,
      diagnostics: rulegenData.diagnostics || null
    });
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_srs_rulegen_failed", null, "Rule preview failed.");
    srsRulegenOutput.textContent = msg;
    logOptions("SRS sampled rulegen preview failed.", err);
  } finally {
    srsRulegenSampledButton.disabled = false;
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
  const items = await settingsManager.load();
  const profileId = settingsManager.getSelectedSrsProfileId(items);
  logOptions(`[Reset] User confirmed reset for pair: ${srsPair} (profile=${profileId})`);
  srsResetButton.disabled = true;
  setStatus(t("status_srs_resetting", null, "Resetting SRS data…"), ui.COLORS.DEFAULT);

  try {
    await helperManager.resetSrs(srsPair, { profileId });
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
if (maxReplacementsPerPageInput) {
  maxReplacementsPerPageInput.addEventListener("change", saveReplacementSettings);
}
if (maxReplacementsPerLemmaPageInput) {
  maxReplacementsPerLemmaPageInput.addEventListener("change", saveReplacementSettings);
}

if (srsEnabledInput) {
  srsEnabledInput.addEventListener("change", saveSrsSettings);
}
if (srsProfileIdInput) {
  srsProfileIdInput.addEventListener("change", () => {
    saveSrsProfileId().catch((err) => {
      const msg = err && err.message ? err.message : t("status_srs_profile_save_failed", null, "Failed to save SRS profile selection.");
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("SRS profile id save failed.", err);
    });
  });
}
if (srsProfileRefreshButton) {
  srsProfileRefreshButton.addEventListener("click", () => {
    refreshSrsProfiles().catch((err) => {
      const msg = err && err.message
        ? err.message
        : t("status_srs_profile_refresh_failed", null, "Failed to refresh helper profiles.");
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("SRS profile refresh failed.", err);
    });
  });
}
if (srsMaxActiveInput) {
  srsMaxActiveInput.addEventListener("change", saveSrsSettings);
}
if (srsBootstrapTopNInput) {
  srsBootstrapTopNInput.addEventListener("change", saveSrsSettings);
}
if (srsInitialActiveCountInput) {
  srsInitialActiveCountInput.addEventListener("change", saveSrsSettings);
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
if (srsRefreshSetButton) {
  srsRefreshSetButton.addEventListener("click", refreshSrsSetNow);
}
if (srsRuntimeDiagnosticsButton) {
  srsRuntimeDiagnosticsButton.addEventListener("click", runSrsRuntimeDiagnostics);
}
if (srsRulegenButton) {
  srsRulegenButton.addEventListener("click", previewSrsRulegen);
}
if (srsRulegenSampledButton) {
  srsRulegenSampledButton.addEventListener("click", previewSampledSrsRulegen);
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
