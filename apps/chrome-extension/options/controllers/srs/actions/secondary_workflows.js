(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRuntimeDiagnosticsWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const diagnosticsButton = opts.diagnosticsButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const buildRuntimeDiagnosticsOutput = typeof opts.buildRuntimeDiagnosticsOutput === "function"
      ? opts.buildRuntimeDiagnosticsOutput
      : (() => "");
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318" };
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    return async function runRuntimeDiagnostics() {
      if (!diagnosticsButton) {
        return;
      }
      const srsPair = resolvePair();
      diagnosticsButton.disabled = true;
      setOutputText(translate(
        "status_srs_diagnostics_running",
        null,
        "Collecting SRS runtime diagnostics…"
      ));
      try {
        const items = await settingsManager.load();
        const selectedProfileId = settingsManager.getSelectedSrsProfileId(items);
        const diagnostics = await helperManager.getSrsRuntimeDiagnostics(srsPair, {
          profileId: selectedProfileId
        });
        setOutputText(buildRuntimeDiagnosticsOutput({
          translate,
          srsPair,
          selectedProfileId,
          diagnostics
        }));
        setStatus(
          translate("status_srs_diagnostics_ready", null, "SRS runtime diagnostics updated."),
          colors.SUCCESS
        );
        log("SRS runtime diagnostics", diagnostics);
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_diagnostics_failed", null, "Failed to collect SRS diagnostics.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS runtime diagnostics failed.", err);
      } finally {
        diagnosticsButton.disabled = false;
      }
    };
  }

  function createRefreshSetWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({ items, profileId: "default" }));
    const resolvePlanningState = typeof opts.resolvePlanningState === "function"
      ? opts.resolvePlanningState
      : (() => null);
    const preflightSrsPairResources = typeof opts.preflightSrsPairResources === "function"
      ? opts.preflightSrsPairResources
      : (() => Promise.resolve(true));
    const refreshButton = opts.refreshButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const buildRefreshResultOutput = typeof opts.buildRefreshResultOutput === "function"
      ? opts.buildRefreshResultOutput
      : (() => "");
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function"
      ? opts.markRulesetUpdatedNow
      : (() => Promise.resolve());
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318", DEFAULT: "#6c675f" };
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    return async function refreshSetNow() {
      if (!refreshButton) {
        return;
      }
      const srsPair = resolvePair();
      refreshButton.disabled = true;
      setOutputText(translate(
        "status_srs_refresh_running",
        null,
        "Refreshing S and publishing rules…"
      ));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const canProceed = await preflightSrsPairResources(
          srsPair,
          synced.profileId,
          "S refresh"
        );
        if (!canProceed) {
          return;
        }
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const profileContext = planningState.profileContext;
        const result = await helperManager.refreshSrsSet(srsPair, {
          profileId: synced.profileId,
          setTopN: planningState.profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800,
          maxActiveItems: planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
          trigger: "options_refresh_set_button",
          profileContext
        });
        const added = Number(result.added_items || 0);
        const applied = result.applied === true;
        const admission = result.admission_refresh && typeof result.admission_refresh === "object"
          ? result.admission_refresh
          : {};
        const publishedRulegen = result.rulegen && typeof result.rulegen === "object"
          ? result.rulegen
          : null;
        setOutputText(buildRefreshResultOutput({
          translate,
          applied,
          added,
          srsPair,
          result,
          admission,
          publishedRulegen
        }));
        if (publishedRulegen && publishedRulegen.published !== false) {
          await markRulesetUpdatedNow();
        }
        setStatus(
          applied
            ? translate("status_srs_refresh_success", [srsPair, added], `S refreshed for ${srsPair}: +${added} admitted.`)
            : translate("status_srs_refresh_noop", [srsPair], `S refresh for ${srsPair}: no new admissions.`),
          applied ? colors.SUCCESS : colors.DEFAULT
        );
        log("SRS set refreshed", {
          pair: srsPair,
          result,
          requestProfileContextMeta: planningState.contextMeta
        });
      } catch (err) {
        const msg = err && err.message ? err.message : translate("status_srs_refresh_failed", null, "S refresh failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS set refresh failed.", err);
      } finally {
        refreshButton.disabled = false;
      }
    };
  }

  function createSampledRulegenWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const sampledButton = opts.sampledButton || null;
    const setSampledOutputText = typeof opts.setSampledOutputText === "function"
      ? opts.setSampledOutputText
      : (() => {});
    const buildSampledRulegenHeader = typeof opts.buildSampledRulegenHeader === "function"
      ? opts.buildSampledRulegenHeader
      : (() => "");
    const buildSampledRulegenSamplingLines = typeof opts.buildSampledRulegenSamplingLines === "function"
      ? opts.buildSampledRulegenSamplingLines
      : (() => []);
    const buildSampledRulegenEmptyOutput = typeof opts.buildSampledRulegenEmptyOutput === "function"
      ? opts.buildSampledRulegenEmptyOutput
      : (() => "");
    const buildSampledRulegenTargetsOutput = typeof opts.buildSampledRulegenTargetsOutput === "function"
      ? opts.buildSampledRulegenTargetsOutput
      : (() => "");
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    return async function previewSampledRulegen() {
      if (!sampledButton) {
        return;
      }
      const srsPair = resolvePair();
      const sampleCount = 5;
      sampledButton.disabled = true;
      setSampledOutputText(translate(
        "status_srs_rulegen_sampled_running",
        [sampleCount],
        `Running sampled rulegen (${sampleCount})…`
      ));

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
        const header = buildSampledRulegenHeader({
          translate,
          sampledCount,
          rulegenTargets,
          rulegenRules,
          duration
        });
        const samplingLines = buildSampledRulegenSamplingLines({
          sampling,
          sampledLemmas,
          sampleCount,
          sampledCount
        });
        if (!targets.length) {
          setSampledOutputText(buildSampledRulegenEmptyOutput({
            translate,
            header,
            samplingLines,
            diagnostics: rulegenData.diagnostics || {},
            srsPair
          }));
        } else {
          setSampledOutputText(buildSampledRulegenTargetsOutput({
            translate,
            header,
            samplingLines,
            targets
          }));
        }
        log("SRS sampled rulegen preview (helper)", {
          pair: srsPair,
          profileId,
          sampledCount,
          sampledLemmas,
          targets: targets.length,
          diagnostics: rulegenData.diagnostics || null
        });
      } catch (err) {
        const msg = err && err.message ? err.message : translate("status_srs_rulegen_failed", null, "Rule preview failed.");
        setSampledOutputText(msg);
        log("SRS sampled rulegen preview failed.", err);
      } finally {
        sampledButton.disabled = false;
      }
    };
  }

  function createResetSrsDataWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : (message) => globalThis.confirm(message);
    const resetButton = opts.resetButton || null;
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318", DEFAULT: "#6c675f" };
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    return async function resetSrsData() {
      if (!resetButton) {
        return;
      }
      if (!confirmFn(translate("confirm_srs_reset_1", null, "Are you sure you want to reset all SRS progress for this language pair? This cannot be undone."))) {
        return;
      }
      if (!confirmFn(translate("confirm_srs_reset_2", null, "Really delete all learning history and start over for this pair?"))) {
        return;
      }

      const srsPair = resolvePair();
      const items = await settingsManager.load();
      const profileId = settingsManager.getSelectedSrsProfileId(items);
      log(`[Reset] User confirmed reset for pair: ${srsPair} (profile=${profileId})`);
      resetButton.disabled = true;
      setStatus(translate("status_srs_resetting", null, "Resetting SRS data…"), colors.DEFAULT);

      try {
        await helperManager.resetSrs(srsPair, { profileId });
        log("[Reset] Helper returned success.");
        setStatus(translate("status_srs_reset_success", null, "SRS data reset successfully."), colors.SUCCESS);
        setOutputText("");
      } catch (err) {
        log("[Reset] Failed:", err);
        let msg = err && err.message ? err.message : translate("status_srs_reset_failed", null, "SRS reset failed.");
        if (msg.includes("Unknown command")) {
          msg = translate("status_srs_reset_outdated", null, "Helper outdated: command not found. Restart helper?");
        }
        setStatus(msg, colors.ERROR);
      } finally {
        resetButton.disabled = false;
      }
    };
  }

  root.optionsSrsSecondaryWorkflows = {
    createRefreshSetWorkflow,
    createRuntimeDiagnosticsWorkflow,
    createSampledRulegenWorkflow,
    createResetSrsDataWorkflow
  };
})();
