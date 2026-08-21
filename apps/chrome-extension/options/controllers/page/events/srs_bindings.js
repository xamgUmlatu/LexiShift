(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const bindAsyncListener = typeof opts.bindAsyncListener === "function"
      ? opts.bindAsyncListener
      : (() => {});
    const helperActionsController = opts.helperActionsController && typeof opts.helperActionsController === "object"
      ? opts.helperActionsController
      : null;
    const srsActionsController = opts.srsActionsController && typeof opts.srsActionsController === "object"
      ? opts.srsActionsController
      : null;
    const saveSrsSettings = typeof opts.saveSrsSettings === "function"
      ? opts.saveSrsSettings
      : (() => Promise.resolve());
    const saveSrsBrowsingAdmissionSignalsSetting = typeof opts.saveSrsBrowsingAdmissionSignalsSetting === "function"
      ? opts.saveSrsBrowsingAdmissionSignalsSetting
      : (() => Promise.resolve());
    const saveSrsProfileId = typeof opts.saveSrsProfileId === "function"
      ? opts.saveSrsProfileId
      : (() => Promise.resolve());
    const refreshSrsProfiles = typeof opts.refreshSrsProfiles === "function"
      ? opts.refreshSrsProfiles
      : (() => Promise.resolve());
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const srsEnabledInput = elements.srsEnabledInput || null;
    const srsProfileIdInput = elements.srsProfileIdInput || null;
    const srsProfileRefreshButton = elements.srsProfileRefreshButton || null;
    const srsMaxActiveInput = elements.srsMaxActiveInput || null;
    const srsBootstrapTopNInput = elements.srsBootstrapTopNInput || null;
    const srsInitialActiveCountInput = elements.srsInitialActiveCountInput || null;
    const srsTopicInterestsInput = elements.srsTopicInterestsInput || null;
    const srsTopicInterestChipButtons = Array.isArray(elements.srsTopicInterestChipButtons)
      ? elements.srsTopicInterestChipButtons
      : [];
    const srsProficiencyEstimateInput = elements.srsProficiencyEstimateInput || null;
    const srsProficiencyEstimateValueOutput = elements.srsProficiencyEstimateValueOutput || null;
    const srsProficiencyEstimateSavedOutput = elements.srsProficiencyEstimateSavedOutput || null;
    const srsProficiencyEstimateRestoreButton = elements.srsProficiencyEstimateRestoreButton || null;
    const srsChallengeTargetInput = elements.srsChallengeTargetInput || null;
    const srsSavePreferencesButton = elements.srsSavePreferencesButton || null;
    const srsPreferencesSaveStatusOutput = elements.srsPreferencesSaveStatusOutput || null;
    const srsSoundInput = elements.srsSoundInput || null;
    const srsHighlightInput = elements.srsHighlightInput || null;
    const srsHighlightTextInput = elements.srsHighlightTextInput || null;
    const srsAutoRefreshMinFeedbackInput = elements.srsAutoRefreshMinFeedbackInput || null;
    const srsAutoRefreshMinGoodEasyInput = elements.srsAutoRefreshMinGoodEasyInput || null;
    const srsAutoRefreshRepeatMinGoodEasyInput = elements.srsAutoRefreshRepeatMinGoodEasyInput || null;
    const srsAutoRefreshCooldownInput = elements.srsAutoRefreshCooldownInput || null;
    const srsExposureLoggingInput = elements.srsExposureLoggingInput || null;
    const srsBrowsingAdmissionSignalsInput = elements.srsBrowsingAdmissionSignalsInput || null;
    const srsAdmissionPreviewButton = elements.srsAdmissionPreviewButton || null;
    const srsInitializeSetButton = elements.srsInitializeSetButton || null;
    const srsRebalancePreviewButton = elements.srsRebalancePreviewButton || null;
    const srsRebalanceApplyButton = elements.srsRebalanceApplyButton || null;
    const srsRefreshSetButton = elements.srsRefreshSetButton || null;
    const srsRuntimeDiagnosticsButton = elements.srsRuntimeDiagnosticsButton || null;
    const srsRulegenSampledButton = elements.srsRulegenSampledButton || null;
    const srsResetButton = elements.srsResetButton || null;
    const semanticPackInstallButton = elements.semanticPackInstallButton || null;
    const srsAdmissionPreviewOutput = elements.srsAdmissionPreviewOutput || null;
    const srsRulegenSampledOutput = elements.srsRulegenSampledOutput || null;
    const debugHelperTestButton = elements.debugHelperTestButton || null;
    const debugOpenDataDirButton = elements.debugOpenDataDirButton || null;
    const srsRulegenOutput = elements.srsRulegenOutput || null;

    function bindSrsSettingsChange(element, beforeSave) {
      if (!element) {
        return;
      }
      bindAsyncListener(element, "change", () => {
        if (typeof beforeSave === "function" && beforeSave() === false) {
          return Promise.resolve();
        }
        return saveSrsSettings();
      }, {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save practice settings."),
        logMessage: "SRS settings save failed."
      });
    }

    function setSrsPreferenceDirty(isDirty) {
      if (srsSavePreferencesButton) {
        srsSavePreferencesButton.disabled = !isDirty;
      }
      if (srsPreferencesSaveStatusOutput) {
        srsPreferencesSaveStatusOutput.textContent = isDirty
          ? translate("status_srs_preferences_unsaved", null, "Unsaved changes.")
          : translate("status_srs_preferences_saved", null, "Preferences saved.");
        if (srsPreferencesSaveStatusOutput.classList
          && typeof srsPreferencesSaveStatusOutput.classList.toggle === "function") {
          srsPreferencesSaveStatusOutput.classList.toggle("is-dirty", isDirty);
        }
      }
    }

    function markSrsPreferencesDirty() {
      setSrsPreferenceDirty(true);
    }

    function bindSrsPreferenceDraftChange(element, beforeMarkDirty) {
      if (!element || typeof element.addEventListener !== "function") {
        return;
      }
      element.addEventListener("change", () => {
        if (typeof beforeMarkDirty === "function" && beforeMarkDirty() === false) {
          return;
        }
        markSrsPreferencesDirty();
      });
    }

    function normalizeInterestList(value) {
      const source = Array.isArray(value)
        ? value
        : String(value || "").split(",");
      const seen = new Set();
      return source
        .map((entry) => String(entry || "").trim())
        .filter((entry) => {
          if (!entry || seen.has(entry)) {
            return false;
          }
          seen.add(entry);
          return true;
        });
    }

    function syncTopicInterestChips() {
      if (!srsTopicInterestChipButtons.length) {
        return;
      }
      const interests = new Set(normalizeInterestList(srsTopicInterestsInput ? srsTopicInterestsInput.value : ""));
      srsTopicInterestChipButtons.forEach((button) => {
        const topic = String(button.getAttribute("data-srs-topic-interest") || "").trim();
        const selected = Boolean(topic && interests.has(topic));
        if (button.classList && typeof button.classList.toggle === "function") {
          button.classList.toggle("is-selected", selected);
        }
        if (typeof button.setAttribute === "function") {
          button.setAttribute("aria-pressed", selected ? "true" : "false");
        }
      });
    }

    function setTopicInterests(interests) {
      if (!srsTopicInterestsInput) {
        return;
      }
      srsTopicInterestsInput.value = normalizeInterestList(interests).join(", ");
      syncTopicInterestChips();
    }

    function formatProficiencyValue(value, hasValue) {
      if (!hasValue) {
        return "Not set";
      }
      const numeric = Number(value);
      if (!Number.isFinite(numeric)) {
        return "Not set";
      }
      return `${Math.round(Math.min(100, Math.max(0, numeric)))}%`;
    }

    function ensureDataset(input) {
      if (!input.dataset) {
        input.dataset = {};
      }
      return input.dataset;
    }

    function updateProficiencyDisplay(markActive) {
      if (!srsProficiencyEstimateInput) {
        return;
      }
      const dataset = ensureDataset(srsProficiencyEstimateInput);
      if (markActive) {
        dataset.srsHasValue = "true";
      }
      const hasValue = dataset.srsHasValue !== "false";
      if (srsProficiencyEstimateValueOutput) {
        srsProficiencyEstimateValueOutput.textContent = formatProficiencyValue(
          srsProficiencyEstimateInput.value,
          hasValue
        );
      }
    }

    function updateSavedProficiencyDisplayFromCurrent() {
      if (!srsProficiencyEstimateInput || !srsProficiencyEstimateSavedOutput) {
        return;
      }
      const dataset = ensureDataset(srsProficiencyEstimateInput);
      const hasValue = dataset.srsHasValue !== "false";
      const text = formatProficiencyValue(srsProficiencyEstimateInput.value, hasValue);
      const savedDataset = ensureDataset(srsProficiencyEstimateSavedOutput);
      srsProficiencyEstimateSavedOutput.textContent = text;
      savedDataset.srsSavedHasValue = hasValue ? "true" : "false";
      savedDataset.srsSavedValue = hasValue
        ? String(Math.round(Math.min(100, Math.max(0, Number(srsProficiencyEstimateInput.value)))))
        : "";
      if (srsProficiencyEstimateRestoreButton) {
        srsProficiencyEstimateRestoreButton.disabled = !hasValue;
      }
    }

    function restoreSavedProficiencyDisplay() {
      if (!srsProficiencyEstimateInput || !srsProficiencyEstimateSavedOutput) {
        return;
      }
      const savedDataset = ensureDataset(srsProficiencyEstimateSavedOutput);
      if (savedDataset.srsSavedHasValue === "false") {
        return;
      }
      const savedValue = Number(savedDataset.srsSavedValue);
      if (!Number.isFinite(savedValue)) {
        return;
      }
      srsProficiencyEstimateInput.value = String(Math.round(Math.min(100, Math.max(0, savedValue))));
      ensureDataset(srsProficiencyEstimateInput).srsHasValue = "true";
      updateProficiencyDisplay(false);
      markSrsPreferencesDirty();
    }

    function bindTopicInterestChip(button) {
      if (!button || !srsTopicInterestsInput) {
        return;
      }
      bindAsyncListener(button, "click", () => {
        const topic = String(button.getAttribute("data-srs-topic-interest") || "").trim();
        if (!topic) {
          return Promise.resolve();
        }
        const interests = normalizeInterestList(srsTopicInterestsInput.value);
        const nextInterests = interests.includes(topic)
          ? interests.filter((entry) => entry !== topic)
          : [...interests, topic];
        setTopicInterests(nextInterests);
        markSrsPreferencesDirty();
        return Promise.resolve();
      }, {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save practice settings."),
        logMessage: "SRS settings save failed."
      });
    }

    bindSrsSettingsChange(srsEnabledInput);
    bindAsyncListener(srsProfileIdInput, "change", () => saveSrsProfileId(), {
      fallbackMessage: () => translate("status_srs_profile_save_failed", null, "Failed to save SRS profile selection."),
      logMessage: "SRS profile id save failed."
    });
    bindAsyncListener(srsProfileRefreshButton, "click", () => refreshSrsProfiles(), {
      fallbackMessage: () => translate("status_srs_profile_refresh_failed", null, "Failed to refresh helper profiles."),
      logMessage: "SRS profile refresh failed."
    });
    bindSrsPreferenceDraftChange(srsMaxActiveInput);
    bindSrsPreferenceDraftChange(srsBootstrapTopNInput);
    bindSrsPreferenceDraftChange(srsInitialActiveCountInput);
    bindSrsPreferenceDraftChange(srsTopicInterestsInput, () => {
      setTopicInterests(srsTopicInterestsInput ? srsTopicInterestsInput.value : "");
    });
    if (srsTopicInterestsInput) {
      srsTopicInterestsInput.addEventListener("input", () => {
        syncTopicInterestChips();
        markSrsPreferencesDirty();
      });
    }
    srsTopicInterestChipButtons.forEach(bindTopicInterestChip);
    syncTopicInterestChips();
    if (srsProficiencyEstimateInput) {
      srsProficiencyEstimateInput.addEventListener("input", () => {
        updateProficiencyDisplay(true);
        markSrsPreferencesDirty();
      });
      srsProficiencyEstimateInput.addEventListener("change", () => {
        updateProficiencyDisplay(true);
        markSrsPreferencesDirty();
      });
    }
    updateProficiencyDisplay(false);
    setSrsPreferenceDirty(false);
    bindAsyncListener(srsProficiencyEstimateRestoreButton, "click", () => {
      restoreSavedProficiencyDisplay();
      return Promise.resolve();
    }, {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save practice settings."),
      logMessage: "SRS proficiency restore failed."
    });
    bindSrsPreferenceDraftChange(srsChallengeTargetInput);
    bindSrsSettingsChange(srsSoundInput);
    bindSrsSettingsChange(srsHighlightInput, () => {
      if (srsHighlightTextInput) {
        srsHighlightTextInput.value = srsHighlightInput.value;
      }
    });
    bindSrsSettingsChange(srsHighlightTextInput, () => {
      const value = srsHighlightTextInput.value.trim();
      if (!value) {
        return false;
      }
      if (srsHighlightInput) {
        srsHighlightInput.value = value;
      }
      return true;
    });
    bindSrsSettingsChange(srsAutoRefreshMinFeedbackInput);
    bindSrsSettingsChange(srsAutoRefreshMinGoodEasyInput);
    bindSrsSettingsChange(srsAutoRefreshRepeatMinGoodEasyInput);
    bindSrsSettingsChange(srsAutoRefreshCooldownInput);
    bindSrsSettingsChange(srsExposureLoggingInput);
    bindAsyncListener(srsBrowsingAdmissionSignalsInput, "change", () => saveSrsBrowsingAdmissionSignalsSetting(), {
      fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save practice settings."),
      logMessage: "SRS browsing admission setting save failed."
    });
    bindAsyncListener(srsSavePreferencesButton, "click", () =>
      Promise.resolve(saveSrsSettings()).then(() => {
        updateProficiencyDisplay(false);
        updateSavedProficiencyDisplayFromCurrent();
        setSrsPreferenceDirty(false);
      }), {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save practice settings."),
      logMessage: "SRS settings save failed."
    });
    bindAsyncListener(srsInitializeSetButton, "click", () => srsActionsController.initializeSet(), {
      fallbackMessage: () => translate("status_srs_set_init_failed", null, "Practice setup failed."),
      logMessage: "SRS set init failed."
    });
    bindAsyncListener(srsAdmissionPreviewButton, "click", () => srsActionsController.previewAdmission(), {
      fallbackMessage: () => translate("status_srs_admission_preview_failed", null, "Word sample failed."),
      logMessage: "SRS admission preview failed.",
      onError: (message) => {
        if (srsAdmissionPreviewOutput) {
          srsAdmissionPreviewOutput.textContent = message;
          return;
        }
        if (srsRulegenOutput) {
          srsRulegenOutput.textContent = message;
        }
      }
    });
    bindAsyncListener(srsRebalancePreviewButton, "click", () => srsActionsController.previewRebalance(), {
      fallbackMessage: () => translate("status_srs_rebalance_preview_failed", null, "SRS rebalance preview failed."),
      logMessage: "SRS rebalance preview failed.",
      onError: (message) => {
        if (srsRulegenOutput) {
          srsRulegenOutput.textContent = message;
        }
      }
    });
    bindAsyncListener(srsRebalanceApplyButton, "click", () => srsActionsController.applyRebalance(), {
      fallbackMessage: () => translate("status_srs_rebalance_apply_failed", null, "SRS rebalance apply failed."),
      logMessage: "SRS rebalance apply failed.",
      onError: (message) => {
        if (srsRulegenOutput) {
          srsRulegenOutput.textContent = message;
        }
      }
    });
    bindAsyncListener(srsRefreshSetButton, "click", () => srsActionsController.refreshSetNow(), {
      fallbackMessage: () => translate("status_srs_refresh_failed", null, "Learning words refresh failed."),
      logMessage: "SRS set refresh failed."
    });
    bindAsyncListener(srsRuntimeDiagnosticsButton, "click", () => srsActionsController.runRuntimeDiagnostics(), {
      fallbackMessage: () => translate("status_srs_diagnostics_failed", null, "Failed to collect SRS diagnostics."),
      logMessage: "SRS runtime diagnostics failed."
    });
    bindAsyncListener(srsRulegenSampledButton, "click", () => srsActionsController.previewSampledRulegen(), {
      fallbackMessage: () => translate("status_srs_rulegen_failed", null, "Rule preview failed."),
      logMessage: "SRS sampled rulegen preview failed.",
      onError: (message) => {
        if (srsRulegenSampledOutput) {
          srsRulegenSampledOutput.textContent = message;
          return;
        }
        if (srsRulegenOutput) {
          srsRulegenOutput.textContent = message;
        }
      }
    });
    bindAsyncListener(semanticPackInstallButton, "click", () => srsActionsController.installSemanticPack(), {
      fallbackMessage: () => translate("status_semantic_pack_install_failed", null, "Semantic pack install failed."),
      logMessage: "Semantic pack install failed."
    });
    bindAsyncListener(srsResetButton, "click", () => srsActionsController.resetSrsData(), {
      fallbackMessage: () => translate("status_srs_reset_failed", null, "This Vocabulary Practice deletion failed."),
      logMessage: "[DeleteStory] Failed:"
    });
    if (debugHelperTestButton) {
      debugHelperTestButton.addEventListener("click", () => {
        helperActionsController.testConnection();
      });
    }
    if (debugOpenDataDirButton) {
      debugOpenDataDirButton.addEventListener("click", () => {
        helperActionsController.openDataDir();
      });
    }
  }

  root.optionsEventSrsBindings = {
    bind
  };
})();
