(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const createResolvePlanningState = root.optionsSrsActionPlanningState && typeof root.optionsSrsActionPlanningState.createResolvePlanningState === "function"
    ? root.optionsSrsActionPlanningState.createResolvePlanningState : null;
  const createAdmissionPreviewWorkflow = root.optionsSrsAdmissionPreviewWorkflow && typeof root.optionsSrsAdmissionPreviewWorkflow.createAdmissionPreviewWorkflow === "function"
    ? root.optionsSrsAdmissionPreviewWorkflow.createAdmissionPreviewWorkflow : null;
  const secondaryWorkflows = root.optionsSrsSecondaryWorkflows && typeof root.optionsSrsSecondaryWorkflows === "object"
    ? root.optionsSrsSecondaryWorkflows : null;

  function createWorkflows(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object" ? opts.settingsManager : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object" ? opts.helperManager : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile : ((items) => Promise.resolve({ items, profileId: "default" }));
    const resolveEffectiveSrsPlanningState = typeof opts.resolveEffectiveSrsPlanningState === "function" ? opts.resolveEffectiveSrsPlanningState : null;
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors : { SUCCESS: "#3c5a2a", ERROR: "#b42318", DEFAULT: "#6c675f" };
    const output = opts.output || null;
    const admissionPreviewButton = opts.admissionPreviewButton || null;
    const initializeButton = opts.initializeButton || null;
    const rebalancePreviewButton = opts.rebalancePreviewButton || null;
    const rebalanceApplyButton = opts.rebalanceApplyButton || null;
    const refreshButton = opts.refreshButton || null;
    const diagnosticsButton = opts.diagnosticsButton || null;
    const sampledButton = opts.sampledButton || null;
    const resetButton = opts.resetButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const setAdmissionPreviewOutputText = typeof opts.setAdmissionPreviewOutputText === "function" ? opts.setAdmissionPreviewOutputText : setOutputText;
    const setSampledOutputText = typeof opts.setSampledOutputText === "function" ? opts.setSampledOutputText : setOutputText;
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function" ? opts.markRulesetUpdatedNow : (() => Promise.resolve());
    const preflightSrsPairResources = typeof opts.preflightSrsPairResources === "function" ? opts.preflightSrsPairResources : ((_pair, _profileId, _actionLabel) => Promise.resolve(true));
    const buildInitializeResultOutput = typeof opts.buildInitializeResultOutput === "function" ? opts.buildInitializeResultOutput : (_options) => "";
    const buildRebalanceResultOutput = typeof opts.buildRebalanceResultOutput === "function" ? opts.buildRebalanceResultOutput : (_options) => "";
    const buildRefreshResultOutput = typeof opts.buildRefreshResultOutput === "function" ? opts.buildRefreshResultOutput : (_options) => "";
    const buildRuntimeDiagnosticsOutput = typeof opts.buildRuntimeDiagnosticsOutput === "function" ? opts.buildRuntimeDiagnosticsOutput : (_options) => "";
    const buildAdmissionPreviewOutput = typeof opts.buildAdmissionPreviewOutput === "function" ? opts.buildAdmissionPreviewOutput : (_options) => "";
    const buildSampledRulegenSamplingLines = typeof opts.buildSampledRulegenSamplingLines === "function" ? opts.buildSampledRulegenSamplingLines : (_options) => [];
    const buildSampledRulegenHeader = typeof opts.buildSampledRulegenHeader === "function" ? opts.buildSampledRulegenHeader : (_options) => "";
    const buildSampledRulegenEmptyOutput = typeof opts.buildSampledRulegenEmptyOutput === "function" ? opts.buildSampledRulegenEmptyOutput : (_options) => "";
    const buildSampledRulegenTargetsOutput = typeof opts.buildSampledRulegenTargetsOutput === "function" ? opts.buildSampledRulegenTargetsOutput : (_options) => "";

    const resolvePlanningState = createResolvePlanningState
      ? createResolvePlanningState({
          settingsManager,
          resolveEffectiveSrsPlanningState
        })
      : (() => null);
    const previewAdmission = createAdmissionPreviewWorkflow
      ? createAdmissionPreviewWorkflow({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          syncSelectedProfile,
          resolvePlanningState,
          preflightSrsPairResources,
          buildAdmissionPreviewOutput,
          admissionPreviewButton,
          setAdmissionPreviewOutputText,
          log
        })
      : (async () => {});
    const runRuntimeDiagnostics = secondaryWorkflows
      && typeof secondaryWorkflows.createRuntimeDiagnosticsWorkflow === "function"
      ? secondaryWorkflows.createRuntimeDiagnosticsWorkflow({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          diagnosticsButton,
          setOutputText,
          setStatus,
          buildRuntimeDiagnosticsOutput,
          colors,
          log
        })
      : (async () => {});
    const refreshSetNow = secondaryWorkflows
      && typeof secondaryWorkflows.createRefreshSetWorkflow === "function"
      ? secondaryWorkflows.createRefreshSetWorkflow({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          syncSelectedProfile,
          resolvePlanningState,
          preflightSrsPairResources,
          refreshButton,
          setOutputText,
          setStatus,
          buildRefreshResultOutput,
          markRulesetUpdatedNow,
          colors,
          log
        })
      : (async () => {});
    const previewSampledRulegen = secondaryWorkflows
      && typeof secondaryWorkflows.createSampledRulegenWorkflow === "function"
      ? secondaryWorkflows.createSampledRulegenWorkflow({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          sampledButton,
          setSampledOutputText,
          buildSampledRulegenHeader,
          buildSampledRulegenSamplingLines,
          buildSampledRulegenEmptyOutput,
          buildSampledRulegenTargetsOutput,
          log
        })
      : (async () => {});
    const resetSrsData = secondaryWorkflows
      && typeof secondaryWorkflows.createResetSrsDataWorkflow === "function"
      ? secondaryWorkflows.createResetSrsDataWorkflow({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          confirmFn,
          resetButton,
          setStatus,
          setOutputText,
          colors,
          log
        })
      : (async () => {});

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
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const bootstrapTopN = Number(planningState.profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800);
        const initialActiveCount = Number(planningState.profile.srsInitialActiveCount || settingsManager.defaults.srsInitialActiveCount || 40);
        const maxActiveItemsHint = Number(planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 20);
        const profileContext = planningState.profileContext;
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
          profileContext,
          requestProfileContextMeta: planningState.contextMeta
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

    async function previewRebalance() {
      if (!rebalancePreviewButton || !output) {
        return;
      }
      const srsPair = resolvePair();
      rebalancePreviewButton.disabled = true;
      setOutputText(translate(
        "status_srs_rebalance_preview_running",
        [srsPair],
        `Preparing rebalance preview for ${srsPair}…`
      ));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const canProceed = await preflightSrsPairResources(
          srsPair,
          synced.profileId,
          "S rebalance preview",
          {
            ignoredMissingInputTypes: ["translation_dict_path", "freedict_de_en_path"]
          }
        );
        if (!canProceed) {
          return;
        }
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const profileContext = planningState.profileContext;
        const result = await helperManager.planSrsRebalance(srsPair, {
          profileId: synced.profileId,
          strategy: "profile_growth",
          objective: "rebalance",
          setTopN: planningState.profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800,
          maxActiveItems: planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
          trigger: "options_rebalance_preview_button",
          profileContext
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: result.profile_id || synced.profileId,
          payload: result,
          mode: "preview"
        }));
        setStatus(
          result.plan && result.plan.can_execute === true
            ? translate("status_srs_rebalance_ready", [srsPair], `Rebalance preview ready for ${srsPair}.`)
            : translate("status_srs_rebalance_blocked", [srsPair], `Rebalance is not ready for ${srsPair}.`),
          result.plan && result.plan.can_execute === true ? colors.SUCCESS : colors.DEFAULT
        );
        log("SRS rebalance preview", {
          pair: srsPair,
          result,
          profileContext,
          requestProfileContextMeta: planningState.contextMeta
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_rebalance_preview_failed", null, "SRS rebalance preview failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS rebalance preview failed.", err);
      } finally {
        rebalancePreviewButton.disabled = false;
      }
    }

    async function applyRebalance() {
      if (!rebalanceApplyButton || !output) {
        return;
      }
      const srsPair = resolvePair();
      rebalanceApplyButton.disabled = true;
      setOutputText(translate(
        "status_srs_rebalance_apply_running",
        [srsPair],
        `Preparing rebalance apply for ${srsPair}…`
      ));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const canProceed = await preflightSrsPairResources(
          srsPair,
          synced.profileId,
          "S rebalance apply"
        );
        if (!canProceed) {
          return;
        }
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const profileContext = planningState.profileContext;
        const requestOptions = {
          profileId: synced.profileId,
          strategy: "profile_growth",
          objective: "rebalance",
          setTopN: planningState.profile.srsBootstrapTopN || settingsManager.defaults.srsBootstrapTopN || 800,
          maxActiveItems: planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
          profileContext
        };
        const previewResult = await helperManager.planSrsRebalance(srsPair, {
          ...requestOptions,
          trigger: "options_rebalance_apply_preview"
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: previewResult.profile_id || synced.profileId,
          payload: previewResult,
          mode: "preview"
        }));
        if (!previewResult.plan || previewResult.plan.can_execute !== true) {
          setStatus(
            translate("status_srs_rebalance_blocked", [srsPair], `Rebalance is not ready for ${srsPair}.`),
            colors.DEFAULT
          );
          return;
        }
        const summary = previewResult.summary && typeof previewResult.summary === "object"
          ? previewResult.summary
          : {};
        const keepCount = Number(summary.proposed_keep_count || 0);
        const parkCount = Number(summary.proposed_park_count || 0);
        const activateCount = Number(summary.proposed_activate_count || 0);
        const confirmMessage = [
          translate(
            "confirm_srs_rebalance_title",
            [srsPair],
            `Rebalance the active SRS set for ${srsPair} using current preferences?`
          ),
          translate(
            "confirm_srs_rebalance_body_counts",
            [keepCount, parkCount, activateCount],
            `${keepCount} protected words will stay active, ${parkCount} low-commitment words will leave the active set, and ${activateCount} words will be activated. Review history will be preserved.`
          )
        ].join("\n\n");
        if (!confirmFn(confirmMessage)) {
          setStatus(
            translate("status_srs_rebalance_cancelled", [srsPair], `Rebalance cancelled for ${srsPair}.`),
            colors.DEFAULT
          );
          return;
        }
        const result = await helperManager.applySrsRebalance(srsPair, {
          ...requestOptions,
          trigger: "options_rebalance_apply_button"
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: result.profile_id || synced.profileId,
          payload: result,
          mode: "apply"
        }));
        if (result.applied && result.rulegen && result.rulegen.published !== false) {
          await markRulesetUpdatedNow();
        }
        setStatus(
          result.applied
            ? translate("status_srs_rebalance_applied", [srsPair], `Rebalance applied for ${srsPair}.`)
            : translate("status_srs_rebalance_noop", [srsPair], `Rebalance for ${srsPair} required no active-set changes.`),
          result.applied ? colors.SUCCESS : colors.DEFAULT
        );
        log("SRS rebalance apply", {
          pair: srsPair,
          result,
          profileContext,
          requestProfileContextMeta: planningState.contextMeta
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_rebalance_apply_failed", null, "SRS rebalance apply failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS rebalance apply failed.", err);
      } finally {
        rebalanceApplyButton.disabled = false;
      }
    }

    return {
      previewAdmission,
      initializeSet,
      previewRebalance,
      applyRebalance,
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
