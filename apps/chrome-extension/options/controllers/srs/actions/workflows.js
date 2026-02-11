(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createWorkflows(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _substitutions, fallback) => fallback || "");
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({
          items,
          profileId: "default"
        }));
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const output = opts.output || null;
    const initializeButton = opts.initializeButton || null;
    const refreshButton = opts.refreshButton || null;
    const diagnosticsButton = opts.diagnosticsButton || null;
    const sampledButton = opts.sampledButton || null;
    const resetButton = opts.resetButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function"
      ? opts.markRulesetUpdatedNow
      : (() => Promise.resolve());
    const preflightSrsPairResources = typeof opts.preflightSrsPairResources === "function"
      ? opts.preflightSrsPairResources
      : ((_pair, _profileId, _actionLabel) => Promise.resolve(true));
    const buildInitializeResultOutput = typeof opts.buildInitializeResultOutput === "function"
      ? opts.buildInitializeResultOutput
      : (_options) => "";
    const buildRefreshResultOutput = typeof opts.buildRefreshResultOutput === "function"
      ? opts.buildRefreshResultOutput
      : (_options) => "";
    const buildRuntimeDiagnosticsOutput = typeof opts.buildRuntimeDiagnosticsOutput === "function"
      ? opts.buildRuntimeDiagnosticsOutput
      : (_options) => "";
    const buildSampledRulegenSamplingLines = typeof opts.buildSampledRulegenSamplingLines === "function"
      ? opts.buildSampledRulegenSamplingLines
      : (_options) => [];
    const buildSampledRulegenHeader = typeof opts.buildSampledRulegenHeader === "function"
      ? opts.buildSampledRulegenHeader
      : (_options) => "";
    const buildSampledRulegenEmptyOutput = typeof opts.buildSampledRulegenEmptyOutput === "function"
      ? opts.buildSampledRulegenEmptyOutput
      : (_options) => "";
    const buildSampledRulegenTargetsOutput = typeof opts.buildSampledRulegenTargetsOutput === "function"
      ? opts.buildSampledRulegenTargetsOutput
      : (_options) => "";

    async function initializeSet() {
      if (!initializeButton || !output) {
        return;
      }
      const srsPair = resolvePair();
      initializeButton.disabled = true;
      setOutputText(translate("status_srs_set_init_running", null, "Initializing S…"));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
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
        const publishedRulegen = result.rulegen && typeof result.rulegen === "object"
          ? result.rulegen
          : null;
        setOutputText(buildInitializeResultOutput({
          translate,
          applied,
          added,
          total,
          srsPair,
          plan,
          result,
          bootstrapTopN,
          initialActiveCount,
          maxActiveItemsHint,
          bootstrapDiagnostics,
          publishedRulegen
        }));
        if (applied && publishedRulegen && publishedRulegen.published !== false) {
          await markRulesetUpdatedNow();
        }
        const statusMessage = applied
          ? translate("status_srs_set_init_success", [srsPair], `S initialized for ${srsPair}.`)
          : translate("status_srs_set_plan_only", [srsPair], `S planning completed for ${srsPair}; no changes were applied.`);
        setStatus(statusMessage, applied ? colors.SUCCESS : colors.DEFAULT);
        log("SRS set initialized", {
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
        const msg = err && err.message ? err.message : translate("status_srs_set_init_failed", null, "S initialization failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS set init failed.", err);
      } finally {
        initializeButton.disabled = false;
      }
    }

    async function refreshSetNow() {
      if (!refreshButton || !output) {
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
        log("SRS set refreshed", { pair: srsPair, result });
      } catch (err) {
        const msg = err && err.message ? err.message : translate("status_srs_refresh_failed", null, "S refresh failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS set refresh failed.", err);
      } finally {
        refreshButton.disabled = false;
      }
    }

    async function runRuntimeDiagnostics() {
      if (!diagnosticsButton || !output) {
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
    }

    async function previewSampledRulegen() {
      if (!sampledButton || !output) {
        return;
      }
      const srsPair = resolvePair();
      const sampleCount = 5;
      sampledButton.disabled = true;
      setOutputText(translate(
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
          setOutputText(buildSampledRulegenEmptyOutput({
            translate,
            header,
            samplingLines,
            diagnostics: rulegenData.diagnostics || {},
            srsPair
          }));
        } else {
          setOutputText(buildSampledRulegenTargetsOutput({
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
        setOutputText(msg);
        log("SRS sampled rulegen preview failed.", err);
      } finally {
        sampledButton.disabled = false;
      }
    }

    async function resetSrsData() {
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
    }

    return {
      initializeSet,
      refreshSetNow,
      runRuntimeDiagnostics,
      previewSampledRulegen,
      resetSrsData
    };
  }

  root.optionsSrsActionWorkflows = {
    createWorkflows
  };
})();
