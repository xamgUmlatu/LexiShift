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
    const srsChallengeTargetInput = elements.srsChallengeTargetInput || null;
    const srsSoundInput = elements.srsSoundInput || null;
    const srsHighlightInput = elements.srsHighlightInput || null;
    const srsHighlightTextInput = elements.srsHighlightTextInput || null;
    const srsFeedbackSrsInput = elements.srsFeedbackSrsInput || null;
    const srsFeedbackRulesInput = elements.srsFeedbackRulesInput || null;
    const srsAutoRefreshEnabledInput = elements.srsAutoRefreshEnabledInput || null;
    const srsAutoRefreshMinFeedbackInput = elements.srsAutoRefreshMinFeedbackInput || null;
    const srsAutoRefreshMinGoodEasyInput = elements.srsAutoRefreshMinGoodEasyInput || null;
    const srsAutoRefreshRepeatMinGoodEasyInput = elements.srsAutoRefreshRepeatMinGoodEasyInput || null;
    const srsAutoRefreshCooldownInput = elements.srsAutoRefreshCooldownInput || null;
    const srsExposureLoggingInput = elements.srsExposureLoggingInput || null;
    const srsAdmissionPreviewButton = elements.srsAdmissionPreviewButton || null;
    const srsInitializeSetButton = elements.srsInitializeSetButton || null;
    const srsRebalancePreviewButton = elements.srsRebalancePreviewButton || null;
    const srsRebalanceApplyButton = elements.srsRebalanceApplyButton || null;
    const srsRefreshSetButton = elements.srsRefreshSetButton || null;
    const srsRuntimeDiagnosticsButton = elements.srsRuntimeDiagnosticsButton || null;
    const srsRulegenSampledButton = elements.srsRulegenSampledButton || null;
    const srsResetButton = elements.srsResetButton || null;
    const srsWordsRefreshButton = elements.srsWordsRefreshButton || null;
    const srsWordsAdvancedInput = elements.srsWordsAdvancedInput || null;
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
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save SRS settings."),
        logMessage: "SRS settings save failed."
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

    function updateProficiencyDisplay(markActive, updateSaved) {
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
      if (updateSaved && srsProficiencyEstimateSavedOutput) {
        srsProficiencyEstimateSavedOutput.textContent = formatProficiencyValue(
          srsProficiencyEstimateInput.value,
          hasValue
        );
      }
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
        return saveSrsSettings();
      }, {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save SRS settings."),
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
    bindSrsSettingsChange(srsMaxActiveInput);
    bindSrsSettingsChange(srsBootstrapTopNInput);
    bindSrsSettingsChange(srsInitialActiveCountInput);
    bindSrsSettingsChange(srsTopicInterestsInput, () => {
      setTopicInterests(srsTopicInterestsInput ? srsTopicInterestsInput.value : "");
    });
    if (srsTopicInterestsInput) {
      srsTopicInterestsInput.addEventListener("input", () => {
        syncTopicInterestChips();
      });
    }
    srsTopicInterestChipButtons.forEach(bindTopicInterestChip);
    syncTopicInterestChips();
    if (srsProficiencyEstimateInput) {
      srsProficiencyEstimateInput.addEventListener("input", () => {
        updateProficiencyDisplay(true);
      });
      bindAsyncListener(srsProficiencyEstimateInput, "change", () => {
        updateProficiencyDisplay(true);
        return Promise.resolve(saveSrsSettings()).then(() => {
          updateProficiencyDisplay(false, true);
        });
      }, {
        fallbackMessage: () => translate("status_srs_save_failed", null, "Failed to save SRS settings."),
        logMessage: "SRS settings save failed."
      });
    }
    updateProficiencyDisplay(false);
    bindSrsSettingsChange(srsChallengeTargetInput);
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
    bindSrsSettingsChange(srsFeedbackSrsInput);
    bindSrsSettingsChange(srsFeedbackRulesInput);
    bindSrsSettingsChange(srsAutoRefreshEnabledInput);
    bindSrsSettingsChange(srsAutoRefreshMinFeedbackInput);
    bindSrsSettingsChange(srsAutoRefreshMinGoodEasyInput);
    bindSrsSettingsChange(srsAutoRefreshRepeatMinGoodEasyInput);
    bindSrsSettingsChange(srsAutoRefreshCooldownInput);
    bindSrsSettingsChange(srsExposureLoggingInput);
    bindAsyncListener(srsInitializeSetButton, "click", () => srsActionsController.initializeSet(), {
      fallbackMessage: () => translate("status_srs_set_init_failed", null, "Story setup failed."),
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
      fallbackMessage: () => translate("status_srs_reset_failed", null, "SRS reset failed."),
      logMessage: "[Reset] Failed:"
    });
    bindAsyncListener(srsWordsRefreshButton, "click", () => srsActionsController.refreshWordsDashboard(), {
      fallbackMessage: () => translate("status_srs_items_list_failed", null, "Failed to load SRS words."),
      logMessage: "SRS words dashboard refresh failed."
    });
    if (srsWordsAdvancedInput) {
      srsWordsAdvancedInput.addEventListener("change", () => {
        if (!srsActionsController || typeof srsActionsController.setWordsDashboardAdvanced !== "function") {
          return;
        }
        srsActionsController.setWordsDashboardAdvanced(srsWordsAdvancedInput.checked);
      });
    }
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
