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
  targetLanguageGear: targetLanguageGearButton,
  targetLanguagePrefsModalBackdrop: targetLanguagePrefsModalBackdrop,
  targetLanguagePrefsModalOk: targetLanguagePrefsModalOkButton,
  jaPrimaryDisplayScript: jaPrimaryDisplayScriptInput,
  srsProfileId: srsProfileIdInput,
  srsProfileRefresh: srsProfileRefreshButton,
  srsProfileStatus: srsProfileStatusOutput,
  profileBgBackdropColor: profileBgBackdropColorInput,
  profileBgEnabled: profileBgEnabledInput,
  profileBgOpacity: profileBgOpacityInput,
  profileBgOpacityValue: profileBgOpacityValueOutput,
  profileBgFile: profileBgFileInput,
  profileBgRemove: profileBgRemoveButton,
  profileBgApply: profileBgApplyButton,
  profileBgStatus: profileBgStatusOutput,
  profileBgPreviewWrap: profileBgPreviewWrap,
  profileBgPreview: profileBgPreviewImage,
  srsMaxActive: srsMaxActiveInput,
  srsBootstrapTopN: srsBootstrapTopNInput,
  srsInitialActiveCount: srsInitialActiveCountInput,
  srsSoundEnabled: srsSoundInput,
  srsHighlightColor: srsHighlightInput,
  srsHighlightColorText: srsHighlightTextInput,
  srsFeedbackSrsEnabled: srsFeedbackSrsInput,
  srsFeedbackRulesEnabled: srsFeedbackRulesInput,
  srsExposureLoggingEnabled: srsExposureLoggingInput,
  srsInitializeSet: srsInitializeSetButton,
  srsRefreshSet: srsRefreshSetButton,
  srsRuntimeDiagnostics: srsRuntimeDiagnosticsButton,
  srsRulegenSampledPreview: srsRulegenSampledButton,
  srsRulegenOutput: srsRulegenOutput,
  srsReset: srsResetButton,
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
let profileBgPreviewObjectUrl = "";
let profileBgAppliedObjectUrl = "";
let profileBgPendingFile = null;
let profileBgHasPendingApply = false;
let targetLanguagePrefsModalOpen = false;
const PROFILE_BG_MAX_UPLOAD_BYTES = 8 * 1024 * 1024;
const profileMediaStore = globalThis.LexiShift && globalThis.LexiShift.profileMediaStore;

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

function applyTargetLanguagePrefsLocalization() {
  const label = t(
    "title_language_specific_preferences",
    null,
    "Language-specific preferences"
  );
  if (targetLanguageGearButton) {
    targetLanguageGearButton.setAttribute("aria-label", label);
    targetLanguageGearButton.setAttribute("title", label);
  }
}

function clampProfileBackgroundOpacity(value) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return 0.18;
  }
  return Math.min(1, Math.max(0, parsed));
}

function normalizeProfileBackgroundBackdropColor(value) {
  const candidate = String(value || "").trim();
  if (/^#[0-9a-fA-F]{6}$/.test(candidate)) {
    return candidate.toLowerCase();
  }
  return "#fbf7f0";
}

function hexColorToRgb(value) {
  const normalized = normalizeProfileBackgroundBackdropColor(value).slice(1);
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16)
  };
}

function updateProfileBgOpacityLabel(value) {
  if (!profileBgOpacityValueOutput) {
    return;
  }
  const numeric = Number.isFinite(Number(value)) ? Number(value) : 18;
  profileBgOpacityValueOutput.textContent = `${Math.round(numeric)}%`;
}

function revokeProfileBgPreviewUrl() {
  if (!profileBgPreviewObjectUrl) {
    return;
  }
  URL.revokeObjectURL(profileBgPreviewObjectUrl);
  profileBgPreviewObjectUrl = "";
}

function clearProfileBgPreview() {
  revokeProfileBgPreviewUrl();
  if (profileBgPreviewImage) {
    profileBgPreviewImage.removeAttribute("src");
  }
  if (profileBgPreviewWrap) {
    profileBgPreviewWrap.classList.add("hidden");
  }
}

function revokeProfileBgAppliedUrl() {
  if (!profileBgAppliedObjectUrl) {
    return;
  }
  URL.revokeObjectURL(profileBgAppliedObjectUrl);
  profileBgAppliedObjectUrl = "";
}

function clearOptionsPageBackground() {
  clearOptionsPageBackgroundImageLayer();
  document.body.style.removeProperty("background-color");
}

function applyOptionsPageBackdropColor(backdropColor) {
  document.body.style.backgroundColor = normalizeProfileBackgroundBackdropColor(backdropColor);
}

function clearOptionsPageBackgroundImageLayer() {
  revokeProfileBgAppliedUrl();
  document.body.style.removeProperty("background-image");
  document.body.style.removeProperty("background-size");
  document.body.style.removeProperty("background-position");
  document.body.style.removeProperty("background-attachment");
}

function applyOptionsPageBackdropOnly(backdropColor) {
  clearOptionsPageBackgroundImageLayer();
  applyOptionsPageBackdropColor(backdropColor);
  // Override CSS default radial gradient when only a solid backdrop is desired.
  document.body.style.backgroundImage = "none";
}

function applyOptionsPageBackgroundFromBlob(blob, opacity, backdropColor) {
  if (!(blob instanceof Blob)) {
    clearOptionsPageBackground();
    return;
  }
  revokeProfileBgAppliedUrl();
  profileBgAppliedObjectUrl = URL.createObjectURL(blob);
  const clamped = clampProfileBackgroundOpacity(opacity);
  const color = normalizeProfileBackgroundBackdropColor(backdropColor);
  const rgb = hexColorToRgb(color);
  const wash = Math.max(0, Math.min(1, 1 - clamped));
  document.body.style.backgroundColor = color;
  document.body.style.backgroundImage = `linear-gradient(rgba(${rgb.r},${rgb.g},${rgb.b},${wash}), rgba(${rgb.r},${rgb.g},${rgb.b},${wash})), url("${profileBgAppliedObjectUrl}")`;
  document.body.style.backgroundSize = "cover";
  document.body.style.backgroundPosition = "center center";
  document.body.style.backgroundAttachment = "fixed";
}

function setProfileBgPreviewFromBlob(blob) {
  if (!(blob instanceof Blob) || !profileBgPreviewImage || !profileBgPreviewWrap) {
    clearProfileBgPreview();
    return;
  }
  revokeProfileBgPreviewUrl();
  profileBgPreviewObjectUrl = URL.createObjectURL(blob);
  profileBgPreviewImage.src = profileBgPreviewObjectUrl;
  profileBgPreviewWrap.classList.remove("hidden");
}

function formatBytes(bytes) {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value <= 0) {
    return "0 B";
  }
  if (value < 1024) {
    return `${Math.round(value)} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

function setProfileBgStatus(message) {
  if (!profileBgStatusOutput) {
    return;
  }
  profileBgStatusOutput.textContent = message;
}

function setProfileBgApplyState(hasPendingApply, forceDisable) {
  profileBgHasPendingApply = hasPendingApply === true;
  if (!profileBgApplyButton) {
    return;
  }
  if (forceDisable === true) {
    profileBgApplyButton.disabled = true;
    return;
  }
  profileBgApplyButton.disabled = !profileBgHasPendingApply;
}

async function refreshProfileBackgroundPreview(uiPrefs) {
  const prefs = uiPrefs && typeof uiPrefs === "object" ? uiPrefs : {};
  const assetId = String(prefs.backgroundAssetId || "").trim();
  if (!assetId) {
    clearProfileBgPreview();
    setProfileBgStatus(t(
      "hint_profile_bg_status_empty",
      null,
      "No background image configured for this profile."
    ));
    return;
  }
  if (!profileMediaStore || typeof profileMediaStore.getAsset !== "function") {
    clearProfileBgPreview();
    setProfileBgStatus("Background preview unavailable: media store missing.");
    return;
  }
  try {
    const record = await profileMediaStore.getAsset(assetId);
    if (!record || !(record.blob instanceof Blob)) {
      clearProfileBgPreview();
      setProfileBgStatus("Background asset not found. Upload again for this profile.");
      return;
    }
    setProfileBgPreviewFromBlob(record.blob);
    const type = String(record.mime_type || record.blob.type || "image/*");
    const size = Number(record.byte_size || record.blob.size || 0);
    setProfileBgStatus(`Asset: ${type}, ${formatBytes(size)}.`);
  } catch (err) {
    clearProfileBgPreview();
    const msg = err && err.message ? err.message : "Failed to load background preview.";
    setProfileBgStatus(msg);
  }
}

async function applyOptionsPageBackgroundFromPrefs(uiPrefs, options) {
  const prefs = uiPrefs && typeof uiPrefs === "object" ? uiPrefs : {};
  const opts = options && typeof options === "object" ? options : {};
  const enabled = prefs.backgroundEnabled === true;
  const assetId = String(prefs.backgroundAssetId || "").trim();
  const backdropColor = normalizeProfileBackgroundBackdropColor(prefs.backgroundBackdropColor);
  const preferredBlob = opts.preferredBlob instanceof Blob ? opts.preferredBlob : null;
  if (!enabled || !assetId) {
    applyOptionsPageBackdropOnly(backdropColor);
    return;
  }
  if (preferredBlob) {
    applyOptionsPageBackgroundFromBlob(preferredBlob, prefs.backgroundOpacity, backdropColor);
    return;
  }
  if (!profileMediaStore || typeof profileMediaStore.getAsset !== "function") {
    applyOptionsPageBackdropOnly(backdropColor);
    return;
  }
  try {
    const record = await profileMediaStore.getAsset(assetId);
    if (!record || !(record.blob instanceof Blob)) {
      applyOptionsPageBackdropOnly(backdropColor);
      return;
    }
    applyOptionsPageBackgroundFromBlob(record.blob, prefs.backgroundOpacity, backdropColor);
  } catch (_err) {
    applyOptionsPageBackdropOnly(backdropColor);
  }
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

function normalizePrimaryDisplayScript(value) {
  const allowed = new Set(["kanji", "kana", "romaji"]);
  const candidate = String(value || "").trim().toLowerCase();
  if (allowed.has(candidate)) {
    return candidate;
  }
  return "kanji";
}

function resolveTargetScriptPrefs(languagePrefs) {
  const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
  const rawTargetScriptPrefs = prefs.targetScriptPrefs && typeof prefs.targetScriptPrefs === "object"
    ? prefs.targetScriptPrefs
    : {};
  const rawJaPrefs = rawTargetScriptPrefs.ja && typeof rawTargetScriptPrefs.ja === "object"
    ? rawTargetScriptPrefs.ja
    : {};
  return {
    ja: {
      primaryDisplayScript: normalizePrimaryDisplayScript(rawJaPrefs.primaryDisplayScript)
    }
  };
}

function updateTargetLanguagePrefsModalVisibility(targetLanguage) {
  const show = String(targetLanguage || "").trim().toLowerCase() === "ja";
  if (targetLanguageGearButton) {
    targetLanguageGearButton.classList.toggle("hidden", !show);
    targetLanguageGearButton.setAttribute("aria-expanded", show && targetLanguagePrefsModalOpen ? "true" : "false");
  }
  if (!show) {
    targetLanguagePrefsModalOpen = false;
  }
  const shouldShowModal = show && targetLanguagePrefsModalOpen;
  if (targetLanguagePrefsModalBackdrop) {
    targetLanguagePrefsModalBackdrop.classList.toggle("hidden", !shouldShowModal);
    targetLanguagePrefsModalBackdrop.setAttribute("aria-hidden", shouldShowModal ? "false" : "true");
  }
  document.body.classList.toggle("modal-open", shouldShowModal);
}

function setTargetLanguagePrefsModalOpen(open) {
  targetLanguagePrefsModalOpen = open === true;
  const targetLanguage = targetLanguageInput
    ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
    : (settingsManager.defaults.targetLanguage || "en");
  updateTargetLanguagePrefsModalVisibility(targetLanguage);
}

function applyLanguagePrefsToInputs(languagePrefs) {
  const prefs = languagePrefs && typeof languagePrefs === "object" ? languagePrefs : {};
  const sourceLanguage = String(prefs.sourceLanguage || settingsManager.defaults.sourceLanguage || "en");
  const targetLanguage = String(prefs.targetLanguage || settingsManager.defaults.targetLanguage || "en");
  const targetScriptPrefs = resolveTargetScriptPrefs(prefs);
  if (sourceLanguageInput) {
    sourceLanguageInput.value = sourceLanguage;
  }
  if (targetLanguageInput) {
    targetLanguageInput.value = targetLanguage;
  }
  if (jaPrimaryDisplayScriptInput) {
    jaPrimaryDisplayScriptInput.value = targetScriptPrefs.ja.primaryDisplayScript;
  }
  updateTargetLanguagePrefsModalVisibility(targetLanguage);
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
      "status_profile_selected",
      [resolvedProfileId],
      `Selected profile: ${resolvedProfileId}.`
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
  let selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
  let selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
  // SRS profile selector is the user-facing source of truth for profile-scoped settings.
  let selectedProfileId = selectedSrsProfileId || selectedUiProfileId;
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
      await settingsManager.updateSelectedUiProfileId(nextProfileId);
      workingItems = await settingsManager.load();
      selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
      selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
      selectedProfileId = selectedSrsProfileId || selectedUiProfileId;
      const languagePrefs = settingsManager.getProfileLanguagePrefs(workingItems, { profileId: selectedSrsProfileId });
      applyLanguagePrefsToInputs(languagePrefs);
      await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId: selectedSrsProfileId });
    }
  }

  if (selectedSrsProfileId !== selectedProfileId) {
    await settingsManager.updateSelectedSrsProfileId(selectedProfileId);
    workingItems = await settingsManager.load();
    selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
    const languagePrefs = settingsManager.getProfileLanguagePrefs(workingItems, { profileId: selectedSrsProfileId });
    applyLanguagePrefsToInputs(languagePrefs);
    await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId: selectedSrsProfileId });
  }
  if (selectedUiProfileId !== selectedProfileId) {
    await settingsManager.updateSelectedUiProfileId(selectedProfileId);
    workingItems = await settingsManager.load();
    selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
  }

  renderSrsProfileControls(selectedProfileId, helperProfilesPayload);
  return {
    items: workingItems,
    profileId: selectedSrsProfileId,
    uiProfileId: selectedUiProfileId,
    helperProfilesPayload
  };
}

async function loadSrsProfileForPair(items, pairKey, options) {
  const synced = await syncSelectedSrsProfile(items, options);
  const profile = settingsManager.getSrsProfile(synced.items, pairKey, {
    profileId: synced.profileId
  });
  const uiPrefs = settingsManager.getProfileUiPrefs(synced.items, {
    profileId: synced.profileId
  });
  profileBgPendingFile = null;
  if (profileBgFileInput) {
    profileBgFileInput.value = "";
  }
  ui.updateSrsInputs(profile);
  ui.updateProfileBackgroundInputs(uiPrefs);
  updateProfileBgOpacityLabel((uiPrefs.backgroundOpacity || 0.18) * 100);
  await refreshProfileBackgroundPreview(uiPrefs);
  // Always render the selected profile's saved UI prefs on options page load/switch.
  setProfileBgApplyState(Boolean(profileBgPendingFile), false);
  await applyOptionsPageBackgroundFromPrefs(uiPrefs);
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
    profileId: synced.profileId,
    profileUiPrefs: uiPrefs
  });
  return { profile, uiPrefs, profileId: synced.profileId, items: synced.items };
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
    const currentPrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
    const targetScriptPrefs = resolveTargetScriptPrefs(currentPrefs);
    targetScriptPrefs.ja.primaryDisplayScript = normalizePrimaryDisplayScript(
      jaPrimaryDisplayScriptInput
        ? jaPrimaryDisplayScriptInput.value
        : targetScriptPrefs.ja.primaryDisplayScript
    );
    await settingsManager.updateProfileLanguagePrefs({
      sourceLanguage,
      targetLanguage,
      srsPairAuto: true,
      srsPair: pairKey,
      targetScriptPrefs
    }, {
      profileId
    });
    const refreshed = await settingsManager.load();
    const refreshedPrefs = settingsManager.getProfileLanguagePrefs(refreshed, { profileId });
    applyLanguagePrefsToInputs(refreshedPrefs);
    await loadSrsProfileForPair(refreshed, pairKey);
    setStatus(t("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
  } catch (err) {
    const msg = err && err.message ? err.message : t("status_language_updated", null, "Language updated.");
    setStatus(msg, ui.COLORS.ERROR);
    logOptions("Language update failed during SRS profile reload.", err);
  }
}

async function loadActiveProfileUiPrefs() {
  const items = await settingsManager.load();
  const profileId = settingsManager.getSelectedSrsProfileId(items);
  const uiPrefs = settingsManager.getProfileUiPrefs(items, { profileId });
  return { profileId, uiPrefs, items };
}

async function saveProfileUiPrefsForCurrentProfile(nextPrefs, options) {
  const opts = options && typeof options === "object" ? options : {};
  const profileId = String(opts.profileId || "").trim() || settingsManager.DEFAULT_PROFILE_ID;
  const publishRuntime = opts.publishRuntime === true;
  const normalized = await settingsManager.updateProfileUiPrefs(nextPrefs, {
    profileId,
    publishRuntime
  });
  ui.updateProfileBackgroundInputs(normalized);
  updateProfileBgOpacityLabel((normalized.backgroundOpacity || 0.18) * 100);
  // Apply button is only for committing pending file uploads.
  setProfileBgApplyState(Boolean(profileBgPendingFile), false);
  return normalized;
}

async function saveProfileBackgroundEnabled() {
  if (!profileBgEnabledInput) {
    return;
  }
  if (profileBgPendingFile) {
    setProfileBgApplyState(true, false);
    setStatus("Background toggle staged. Click Apply to commit.", ui.COLORS.SUCCESS);
    return;
  }
  const state = await loadActiveProfileUiPrefs();
  if (!state.uiPrefs.backgroundAssetId) {
    setProfileBgApplyState(Boolean(profileBgPendingFile), false);
    setStatus("Choose an image file, then click Apply.", ui.COLORS.DEFAULT);
    return;
  }
  const nextPrefs = {
    ...state.uiPrefs,
    backgroundEnabled: profileBgEnabledInput.checked === true
  };
  await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
    profileId: state.profileId,
    publishRuntime: false
  });
  await applyOptionsPageBackgroundFromPrefs(nextPrefs);
  setStatus("Background toggle saved.", ui.COLORS.SUCCESS);
}

async function saveProfileBackgroundOpacity() {
  if (!profileBgOpacityInput) {
    return;
  }
  const percent = Number.parseFloat(profileBgOpacityInput.value);
  updateProfileBgOpacityLabel(percent);
  if (profileBgPendingFile) {
    setProfileBgApplyState(true, false);
    setStatus("Background opacity staged. Click Apply to commit.", ui.COLORS.SUCCESS);
    return;
  }
  const state = await loadActiveProfileUiPrefs();
  const nextPrefs = {
    ...state.uiPrefs,
    backgroundOpacity: clampProfileBackgroundOpacity(percent / 100)
  };
  await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
    profileId: state.profileId,
    publishRuntime: false
  });
  await applyOptionsPageBackgroundFromPrefs(nextPrefs);
  setStatus("Background opacity saved.", ui.COLORS.SUCCESS);
}

async function saveProfileBackgroundBackdropColor() {
  if (!profileBgBackdropColorInput) {
    return;
  }
  const color = normalizeProfileBackgroundBackdropColor(profileBgBackdropColorInput.value);
  profileBgBackdropColorInput.value = color;
  const state = await loadActiveProfileUiPrefs();
  const nextPrefs = {
    ...state.uiPrefs,
    backgroundBackdropColor: color
  };
  await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
    profileId: state.profileId,
    publishRuntime: false
  });
  await applyOptionsPageBackgroundFromPrefs(nextPrefs);
  setStatus("Backdrop color saved.", ui.COLORS.SUCCESS);
}

function handleProfileBackgroundFileChange() {
  if (!profileBgFileInput) {
    return;
  }
  const file = profileBgFileInput.files && profileBgFileInput.files[0];
  if (!file) {
    profileBgPendingFile = null;
    return;
  }
  if (!String(file.type || "").startsWith("image/")) {
    profileBgPendingFile = null;
    setStatus("Only image files are supported.", ui.COLORS.ERROR);
    profileBgFileInput.value = "";
    return;
  }
  if (Number(file.size || 0) > PROFILE_BG_MAX_UPLOAD_BYTES) {
    profileBgPendingFile = null;
    setStatus(`Image too large. Maximum is ${formatBytes(PROFILE_BG_MAX_UPLOAD_BYTES)}.`, ui.COLORS.ERROR);
    profileBgFileInput.value = "";
    return;
  }
  profileBgPendingFile = file;
  setProfileBgPreviewFromBlob(file);
  if (profileBgEnabledInput) {
    profileBgEnabledInput.checked = true;
  }
  setProfileBgStatus(`Preview ready: ${file.type || "image/*"}, ${formatBytes(file.size || 0)}.`);
  setProfileBgApplyState(true, false);
  setStatus("File selected. Click Apply profile background.", ui.COLORS.SUCCESS);
}

async function removeProfileBackgroundImage() {
  if (!profileBgRemoveButton) {
    return;
  }
  profileBgPendingFile = null;
  if (profileBgFileInput) {
    profileBgFileInput.value = "";
  }
  if (!profileMediaStore || typeof profileMediaStore.deleteAsset !== "function") {
    setStatus("Profile media store is unavailable.", ui.COLORS.ERROR);
    return;
  }
  profileBgRemoveButton.disabled = true;
  let removed = false;
  try {
    const state = await loadActiveProfileUiPrefs();
    const existingAssetId = String(state.uiPrefs.backgroundAssetId || "").trim();
    if (existingAssetId) {
      await profileMediaStore.deleteAsset(existingAssetId);
    }
    const nextPrefs = {
      ...state.uiPrefs,
      backgroundEnabled: false,
      backgroundAssetId: ""
    };
    await saveProfileUiPrefsForCurrentProfile(nextPrefs, {
      profileId: state.profileId,
      publishRuntime: false
    });
    clearProfileBgPreview();
    await applyOptionsPageBackgroundFromPrefs(nextPrefs);
    setProfileBgApplyState(Boolean(profileBgPendingFile), false);
    setProfileBgStatus(t(
      "hint_profile_bg_status_empty",
      null,
      "No background image configured for this profile."
    ));
    setStatus("Profile background image removed.", ui.COLORS.SUCCESS);
    removed = true;
  } catch (err) {
    const msg = err && err.message ? err.message : "Failed to remove profile background image.";
    setStatus(msg, ui.COLORS.ERROR);
  } finally {
    if (!removed) {
      profileBgRemoveButton.disabled = false;
    }
  }
}

async function applyProfileBackgroundSettings() {
  if (!profileBgApplyButton) {
    return;
  }
  if (!profileBgHasPendingApply) {
    setStatus("No pending background changes.", ui.COLORS.DEFAULT);
    return;
  }
  profileBgApplyButton.disabled = true;
  try {
    const state = await loadActiveProfileUiPrefs();
    let finalPrefs = { ...state.uiPrefs };
    let preferredBlob = null;
    if (profileBgPendingFile) {
      if (!profileMediaStore || typeof profileMediaStore.upsertProfileBackground !== "function") {
        throw new Error("Profile media store is unavailable.");
      }
      const committedFile = profileBgPendingFile;
      const meta = await profileMediaStore.upsertProfileBackground(
        state.profileId,
        committedFile,
        {
          previousAssetId: state.uiPrefs.backgroundAssetId,
          mimeType: committedFile.type || "application/octet-stream"
        }
      );
      finalPrefs = {
        ...state.uiPrefs,
        backgroundAssetId: meta.asset_id,
        backgroundEnabled: profileBgEnabledInput ? profileBgEnabledInput.checked === true : true,
        backgroundOpacity: profileBgOpacityInput
          ? clampProfileBackgroundOpacity(Number(profileBgOpacityInput.value || 18) / 100)
          : (state.uiPrefs.backgroundOpacity || 0.18),
        backgroundBackdropColor: profileBgBackdropColorInput
          ? normalizeProfileBackgroundBackdropColor(profileBgBackdropColorInput.value)
          : normalizeProfileBackgroundBackdropColor(state.uiPrefs.backgroundBackdropColor)
      };
      preferredBlob = committedFile;
      profileBgPendingFile = null;
      if (profileBgFileInput) {
        profileBgFileInput.value = "";
      }
      await saveProfileUiPrefsForCurrentProfile(finalPrefs, {
        profileId: state.profileId,
        publishRuntime: false
      });
      setProfileBgPreviewFromBlob(committedFile);
      setProfileBgStatus(`Asset: ${meta.mime_type || committedFile.type || "image/*"}, ${formatBytes(meta.byte_size || committedFile.size || 0)}.`);
    }
    await settingsManager.publishProfileUiPrefs(finalPrefs, {
      profileId: state.profileId
    });
    await applyOptionsPageBackgroundFromPrefs(finalPrefs, {
      preferredBlob
    });
    setProfileBgApplyState(false, false);
    setStatus("Profile background applied.", ui.COLORS.SUCCESS);
  } catch (err) {
    setProfileBgApplyState(true, false);
    const msg = err && err.message ? err.message : "Failed to apply profile background.";
    setStatus(msg, ui.COLORS.ERROR);
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
  await settingsManager.updateSelectedUiProfileId(profileId);
  const items = await settingsManager.load();
  const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
  const pairKey = applyLanguagePrefsToInputs(languagePrefs);
  await settingsManager.publishProfileLanguagePrefs(languagePrefs, { profileId });
  const refreshed = await settingsManager.load();
  await loadSrsProfileForPair(refreshed, pairKey);
  setStatus(t("status_profile_saved", null, "Profile selection saved."), ui.COLORS.SUCCESS);
}

async function refreshSrsProfiles() {
  const pairKey = resolvePairFromInputs();
  if (srsProfileRefreshButton) {
    srsProfileRefreshButton.disabled = true;
  }
  if (srsProfileStatusOutput) {
    srsProfileStatusOutput.textContent = t(
      "hint_profile_loading",
      null,
      "Loading profiles…"
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

async function migrateLegacyOptionsProfileStateIfNeeded() {
  if (typeof settingsManager.loadRaw !== "function") {
    return;
  }
  const raw = await settingsManager.loadRaw();
  if (!raw || typeof raw !== "object") {
    return;
  }
  if (raw.optionsSelectedProfileId !== undefined) {
    return;
  }
  const selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(raw);
  const legacyAssetId = String(raw.profileBackgroundAssetId || "").trim();
  const hasLegacyBackgroundData = raw.profileBackgroundEnabled === true
    || Boolean(legacyAssetId)
    || raw.profileBackgroundOpacity !== undefined
    || raw.profileBackgroundBackdropColor !== undefined;

  if (hasLegacyBackgroundData) {
    await settingsManager.updateProfileUiPrefs(
      {
        backgroundEnabled: raw.profileBackgroundEnabled === true,
        backgroundAssetId: legacyAssetId,
        backgroundOpacity: raw.profileBackgroundOpacity,
        backgroundBackdropColor: raw.profileBackgroundBackdropColor
      },
      {
        profileId: selectedSrsProfileId,
        publishRuntime: false
      }
    );
  }
  await settingsManager.updateSelectedUiProfileId(selectedSrsProfileId);
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
  await migrateLegacyOptionsProfileStateIfNeeded();
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
    await refreshHelperStatus();
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
    await i18n.load(items.uiLanguage || "system");
    applyTargetLanguagePrefsLocalization();
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

function formatMissingResourceList(missingInputs) {
  const missing = Array.isArray(missingInputs) ? missingInputs : [];
  if (!missing.length) {
    return "none";
  }
  return missing.map((entry) => {
    if (!entry || typeof entry !== "object") {
      return "unknown";
    }
    const resourceType = String(entry.type || "unknown");
    const resourcePath = typeof entry.path === "string" && entry.path
      ? entry.path
      : "(path unresolved)";
    return `${resourceType}: ${resourcePath}`;
  }).join("; ");
}

function formatPairPolicySummary(pairPolicy) {
  if (!pairPolicy || typeof pairPolicy !== "object") {
    return "n/a";
  }
  return [
    `bootstrap_top_n_default=${pairPolicy.bootstrap_top_n_default ?? "n/a"}`,
    `refresh_top_n_default=${pairPolicy.refresh_top_n_default ?? "n/a"}`,
    `feedback_window_size_default=${pairPolicy.feedback_window_size_default ?? "n/a"}`,
    `initial_active_count_default=${pairPolicy.initial_active_count_default ?? "n/a"}`
  ].join(", ");
}

async function preflightSrsPairResources(pair, profileId, actionLabel) {
  const diagnostics = await helperManager.getSrsRuntimeDiagnostics(pair, { profileId });
  const helperData = diagnostics && diagnostics.helper && typeof diagnostics.helper === "object"
    ? diagnostics.helper
    : null;
  if (!helperData) {
    return true;
  }
  const missingInputs = Array.isArray(helperData.missing_inputs) ? helperData.missing_inputs : [];
  if (!missingInputs.length) {
    return true;
  }
  const requirements = helperData.requirements && typeof helperData.requirements === "object"
    ? helperData.requirements
    : {};
  const pairPolicy = helperData.pair_policy && typeof helperData.pair_policy === "object"
    ? helperData.pair_policy
    : null;
  const lines = [
    `${actionLabel} blocked for ${pair}: required resources are missing.`,
    `profile: ${profileId}`,
    "",
    "LP requirements:",
    `- supports_rulegen: ${requirements.supports_rulegen === true}`,
    `- requires_jmdict_for_seed: ${requirements.requires_jmdict_for_seed === true}`,
    `- requires_jmdict_for_rulegen: ${requirements.requires_jmdict_for_rulegen === true}`,
    `- requires_freedict_de_en_for_rulegen: ${requirements.requires_freedict_de_en_for_rulegen === true}`,
    "",
    "Resolved resources:",
    `- set_source_db: ${helperData.set_source_db || "n/a"} (exists=${helperData.set_source_db_exists === true})`,
    `- jmdict_path: ${helperData.jmdict_path || "n/a"} (exists=${helperData.jmdict_exists === true})`,
    `- freedict_de_en_path: ${helperData.freedict_de_en_path || "n/a"} (exists=${helperData.freedict_de_en_exists === true})`,
    `- stopwords_path: ${helperData.stopwords_path || "n/a"} (exists=${helperData.stopwords_exists === true})`,
    "",
    "Pair policy defaults:",
    `- ${formatPairPolicySummary(pairPolicy)}`,
    "",
    "Missing inputs:",
    ...missingInputs.map((entry) => {
      const resourceType = entry && entry.type ? String(entry.type) : "unknown";
      const resourcePath = entry && entry.path ? String(entry.path) : "(path unresolved)";
      return `- ${resourceType}: ${resourcePath}`;
    })
  ];
  srsRulegenOutput.textContent = lines.join("\n");
  setStatus(
    `Missing resources for ${pair}. Add the required files and try again.`,
    ui.COLORS.ERROR
  );
  logOptions("SRS preflight failed due to missing resources", {
    pair,
    profileId,
    helper: helperData
  });
  return false;
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
    const canProceed = await preflightSrsPairResources(
      srsPair,
      synced.profileId,
      "S initialization"
    );
    if (!canProceed) {
      return;
    }
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
    const canProceed = await preflightSrsPairResources(
      srsPair,
      synced.profileId,
      "S refresh"
    );
    if (!canProceed) {
      return;
    }
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
    const pairPolicy = helperData && helperData.pair_policy && typeof helperData.pair_policy === "object"
      ? helperData.pair_policy
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
      helperData ? `- pair_policy: ${formatPairPolicySummary(pairPolicy)}` : null,
      helperData ? `- set_source_db: ${helperData.set_source_db || "n/a"} (exists=${helperData.set_source_db_exists === true})` : null,
      helperData ? `- jmdict_path: ${helperData.jmdict_path || "n/a"} (exists=${helperData.jmdict_exists === true})` : null,
      helperData ? `- freedict_de_en_path: ${helperData.freedict_de_en_path || "n/a"} (exists=${helperData.freedict_de_en_exists === true})` : null,
      helperData ? `- stopwords_path: ${helperData.stopwords_path || "n/a"} (exists=${helperData.stopwords_exists === true})` : null,
      helperData ? `- missing_inputs: ${formatMissingResourceList(helperData.missing_inputs)}` : null,
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
        `- freedict_de_en: ${diag.freedict_de_en_path || "n/a"} (exists=${diag.freedict_de_en_exists})`,
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
if (profileBgEnabledInput) {
  profileBgEnabledInput.addEventListener("change", () => {
    saveProfileBackgroundEnabled().catch((err) => {
      const msg = err && err.message ? err.message : "Failed to save profile background setting.";
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("Profile background enable save failed.", err);
    });
  });
}
if (profileBgBackdropColorInput) {
  profileBgBackdropColorInput.addEventListener("change", () => {
    saveProfileBackgroundBackdropColor().catch((err) => {
      const msg = err && err.message ? err.message : "Failed to save backdrop color.";
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("Profile background backdrop color save failed.", err);
    });
  });
}
if (profileBgOpacityInput) {
  profileBgOpacityInput.addEventListener("input", () => {
    updateProfileBgOpacityLabel(profileBgOpacityInput.value);
  });
  profileBgOpacityInput.addEventListener("change", () => {
    saveProfileBackgroundOpacity().catch((err) => {
      const msg = err && err.message ? err.message : "Failed to save profile background opacity.";
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("Profile background opacity save failed.", err);
    });
  });
}
if (profileBgFileInput) {
  profileBgFileInput.addEventListener("change", handleProfileBackgroundFileChange);
}
if (profileBgRemoveButton) {
  profileBgRemoveButton.addEventListener("click", () => {
    removeProfileBackgroundImage().catch((err) => {
      const msg = err && err.message ? err.message : "Failed to remove profile background image.";
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("Profile background removal failed.", err);
    });
  });
}
if (profileBgApplyButton) {
  profileBgApplyButton.addEventListener("click", () => {
    applyProfileBackgroundSettings().catch((err) => {
      const msg = err && err.message ? err.message : "Failed to apply profile background.";
      setStatus(msg, ui.COLORS.ERROR);
      logOptions("Profile background apply failed.", err);
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
if (srsInitializeSetButton) {
  srsInitializeSetButton.addEventListener("click", initializeSrsSet);
}
if (srsRefreshSetButton) {
  srsRefreshSetButton.addEventListener("click", refreshSrsSetNow);
}
if (srsRuntimeDiagnosticsButton) {
  srsRuntimeDiagnosticsButton.addEventListener("click", runSrsRuntimeDiagnostics);
}
if (srsRulegenSampledButton) {
  srsRulegenSampledButton.addEventListener("click", previewSampledSrsRulegen);
}
if (srsResetButton) {
  srsResetButton.addEventListener("click", resetSrsData);
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
      Promise.resolve(i18n.load(value)).finally(() => {
        applyTargetLanguagePrefsLocalization();
        setStatus(t("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
      });
    });
  });
}

applyTargetLanguagePrefsLocalization();

if (sourceLanguageInput) {
  sourceLanguageInput.addEventListener("change", saveLanguageSettings);
}
if (targetLanguageInput) {
  targetLanguageInput.addEventListener("change", () => {
    if (String(targetLanguageInput.value || "").trim().toLowerCase() !== "ja") {
      setTargetLanguagePrefsModalOpen(false);
    }
    updateTargetLanguagePrefsModalVisibility(targetLanguageInput.value || "");
    saveLanguageSettings();
  });
}
if (targetLanguageGearButton) {
  targetLanguageGearButton.addEventListener("click", () => {
    const targetLanguage = targetLanguageInput
      ? (targetLanguageInput.value || settingsManager.defaults.targetLanguage || "en")
      : (settingsManager.defaults.targetLanguage || "en");
    if (String(targetLanguage).trim().toLowerCase() !== "ja") {
      return;
    }
    setTargetLanguagePrefsModalOpen(!targetLanguagePrefsModalOpen);
  });
}
if (jaPrimaryDisplayScriptInput) {
  jaPrimaryDisplayScriptInput.addEventListener("change", () => {
    saveLanguageSettings();
  });
}
if (targetLanguagePrefsModalBackdrop) {
  targetLanguagePrefsModalBackdrop.addEventListener("click", (event) => {
    if (event.target === targetLanguagePrefsModalBackdrop) {
      setTargetLanguagePrefsModalOpen(false);
    }
  });
}
if (targetLanguagePrefsModalOkButton) {
  targetLanguagePrefsModalOkButton.addEventListener("click", () => {
    setTargetLanguagePrefsModalOpen(false);
  });
}
document.addEventListener("keydown", (event) => {
  if (!targetLanguagePrefsModalOpen) {
    return;
  }
  if (event.key === "Escape") {
    setTargetLanguagePrefsModalOpen(false);
  }
});

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

window.addEventListener("beforeunload", () => {
  revokeProfileBgPreviewUrl();
  revokeProfileBgAppliedUrl();
});

load();
