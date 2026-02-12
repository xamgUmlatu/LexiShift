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
    const srsSoundInput = elements.srsSoundInput || null;
    const srsHighlightInput = elements.srsHighlightInput || null;
    const srsHighlightTextInput = elements.srsHighlightTextInput || null;
    const srsFeedbackSrsInput = elements.srsFeedbackSrsInput || null;
    const srsFeedbackRulesInput = elements.srsFeedbackRulesInput || null;
    const srsExposureLoggingInput = elements.srsExposureLoggingInput || null;
    const srsInitializeSetButton = elements.srsInitializeSetButton || null;
    const srsRefreshSetButton = elements.srsRefreshSetButton || null;
    const srsRuntimeDiagnosticsButton = elements.srsRuntimeDiagnosticsButton || null;
    const srsRulegenSampledButton = elements.srsRulegenSampledButton || null;
    const srsResetButton = elements.srsResetButton || null;
    const debugHelperTestButton = elements.debugHelperTestButton || null;
    const debugOpenDataDirButton = elements.debugOpenDataDirButton || null;
    const srsRulegenOutput = elements.srsRulegenOutput || null;

    if (srsEnabledInput) {
      srsEnabledInput.addEventListener("change", saveSrsSettings);
    }
    bindAsyncListener(srsProfileIdInput, "change", () => saveSrsProfileId(), {
      fallbackMessage: () => translate("status_srs_profile_save_failed", null, "Failed to save SRS profile selection."),
      logMessage: "SRS profile id save failed."
    });
    bindAsyncListener(srsProfileRefreshButton, "click", () => refreshSrsProfiles(), {
      fallbackMessage: () => translate("status_srs_profile_refresh_failed", null, "Failed to refresh helper profiles."),
      logMessage: "SRS profile refresh failed."
    });
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
    bindAsyncListener(srsInitializeSetButton, "click", () => srsActionsController.initializeSet(), {
      fallbackMessage: () => translate("status_srs_set_init_failed", null, "S initialization failed."),
      logMessage: "SRS set init failed."
    });
    bindAsyncListener(srsRefreshSetButton, "click", () => srsActionsController.refreshSetNow(), {
      fallbackMessage: () => translate("status_srs_refresh_failed", null, "S refresh failed."),
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
        if (srsRulegenOutput) {
          srsRulegenOutput.textContent = message;
        }
      }
    });
    bindAsyncListener(srsResetButton, "click", () => srsActionsController.resetSrsData(), {
      fallbackMessage: () => translate("status_srs_reset_failed", null, "SRS reset failed."),
      logMessage: "[Reset] Failed:"
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
