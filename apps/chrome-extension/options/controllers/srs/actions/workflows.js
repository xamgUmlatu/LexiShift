(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const createResolvePlanningState = root.optionsSrsActionPlanningState
    && typeof root.optionsSrsActionPlanningState.createResolvePlanningState === "function"
    ? root.optionsSrsActionPlanningState.createResolvePlanningState
    : null;
  const createAdmissionPreviewWorkflow = root.optionsSrsAdmissionPreviewWorkflow
    && typeof root.optionsSrsAdmissionPreviewWorkflow.createAdmissionPreviewWorkflow === "function"
    ? root.optionsSrsAdmissionPreviewWorkflow.createAdmissionPreviewWorkflow
    : null;
  const createRebalanceWorkflows = root.optionsSrsRebalanceWorkflow
    && typeof root.optionsSrsRebalanceWorkflow.createRebalanceWorkflows === "function"
    ? root.optionsSrsRebalanceWorkflow.createRebalanceWorkflows
    : null;
  const createMaintenanceWorkflows = root.optionsSrsActionMaintenanceWorkflow
    && typeof root.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows === "function"
    ? root.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows
    : null;

  function createWorkflows(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({
          items,
          profileId: "default"
        }));
    const resolveEffectiveSrsPlanningState = typeof opts.resolveEffectiveSrsPlanningState === "function"
      ? opts.resolveEffectiveSrsPlanningState
      : null;
    const confirmFn = typeof opts.confirmFn === "function"
      ? opts.confirmFn
      : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const output = opts.output || null;
    const admissionPreviewButton = opts.admissionPreviewButton || null;
    const rebalancePreviewButton = opts.rebalancePreviewButton || null;
    const rebalanceApplyButton = opts.rebalanceApplyButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const setAdmissionPreviewOutputText = typeof opts.setAdmissionPreviewOutputText === "function"
      ? opts.setAdmissionPreviewOutputText
      : setOutputText;
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function"
      ? opts.markRulesetUpdatedNow
      : (() => Promise.resolve());
    const preflightSrsPairResources = typeof opts.preflightSrsPairResources === "function"
      ? opts.preflightSrsPairResources
      : ((_pair, _profileId, _actionLabel) => Promise.resolve(true));
    const buildRebalanceResultOutput = typeof opts.buildRebalanceResultOutput === "function"
      ? opts.buildRebalanceResultOutput
      : (_options) => "";
    const buildAdmissionPreviewOutput = typeof opts.buildAdmissionPreviewOutput === "function"
      ? opts.buildAdmissionPreviewOutput
      : (_options) => "";

    const resolvePlanningState = createResolvePlanningState
      ? createResolvePlanningState({
          settingsManager,
          resolveEffectiveSrsPlanningState
        })
      : ((items, pairKey, profileId) => {
          const profile = settingsManager.getSrsProfile(items, pairKey, { profileId });
          return {
            profileId: profile.profileId || profileId || "default",
            profile,
            signals: settingsManager.getSrsProfileSignals(items, pairKey, {
              profileId: profile.profileId || profileId
            }),
            profileContext: settingsManager.buildSrsPlanContext(items, pairKey, {
              profileId: profile.profileId || profileId
            }),
            contextMeta: {
              source: "saved_profile",
              pendingOverrides: []
            }
          };
        });
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
    const rebalanceWorkflows = createRebalanceWorkflows
      ? createRebalanceWorkflows({
          settingsManager,
          helperManager,
          translate,
          resolvePair,
          syncSelectedProfile,
          resolvePlanningState,
          preflightSrsPairResources,
          buildRebalanceResultOutput,
          rebalancePreviewButton,
          rebalanceApplyButton,
          setOutputText,
          setStatus,
          confirmFn,
          markRulesetUpdatedNow,
          log,
          colors
        })
      : {
          previewRebalance: async () => {},
          applyRebalance: async () => {}
        };
    const maintenanceWorkflows = createMaintenanceWorkflows
      ? createMaintenanceWorkflows({
          settingsManager,
          helperManager,
          translate,
          setStatus,
          resolvePair,
          syncSelectedProfile,
          resolvePlanningState,
          confirmFn,
          log,
          colors,
          output,
          initializeButton: opts.initializeButton || null,
          refreshButton: opts.refreshButton || null,
          diagnosticsButton: opts.diagnosticsButton || null,
          sampledButton: opts.sampledButton || null,
          resetButton: opts.resetButton || null,
          wordsRefreshButton: opts.wordsRefreshButton || null,
          wordsAdvancedInput: opts.wordsAdvancedInput || null,
          wordsSearchInput: opts.wordsSearchInput || null,
          wordsStatusFilterInput: opts.wordsStatusFilterInput || null,
          wordsSortInput: opts.wordsSortInput || null,
          wordsPageSizeInput: opts.wordsPageSizeInput || null,
          wordsClearFiltersButton: opts.wordsClearFiltersButton || null,
          wordsSummaryRoot: opts.wordsSummaryRoot || null,
          wordsPaginationRoot: opts.wordsPaginationRoot || null,
          wordsPageInfoRoot: opts.wordsPageInfoRoot || null,
          wordsFirstPageButton: opts.wordsFirstPageButton || null,
          wordsPrevPageButton: opts.wordsPrevPageButton || null,
          wordsNextPageButton: opts.wordsNextPageButton || null,
          wordsLastPageButton: opts.wordsLastPageButton || null,
          wordsMetaRoot: opts.wordsMetaRoot || null,
          wordsListRoot: opts.wordsListRoot || null,
          semanticPackInventoryPathInput: opts.semanticPackInventoryPathInput || null,
          semanticPackIdInput: opts.semanticPackIdInput || null,
          semanticPackDefaultDataRootInput: opts.semanticPackDefaultDataRootInput || null,
          semanticPackDataRootInput: opts.semanticPackDataRootInput || null,
          semanticPackInstallButton: opts.semanticPackInstallButton || null,
          semanticPackInstallOutput: opts.semanticPackInstallOutput || null,
          setOutputText,
          setSampledOutputText: typeof opts.setSampledOutputText === "function"
            ? opts.setSampledOutputText
            : setOutputText,
          markRulesetUpdatedNow,
          preflightSrsPairResources,
          buildInitializeResultOutput: typeof opts.buildInitializeResultOutput === "function"
            ? opts.buildInitializeResultOutput
            : (_options) => "",
          buildRefreshResultOutput: typeof opts.buildRefreshResultOutput === "function"
            ? opts.buildRefreshResultOutput
            : (_options) => "",
          buildRuntimeDiagnosticsOutput: typeof opts.buildRuntimeDiagnosticsOutput === "function"
            ? opts.buildRuntimeDiagnosticsOutput
            : (_options) => "",
          buildSampledRulegenSamplingLines: typeof opts.buildSampledRulegenSamplingLines === "function"
            ? opts.buildSampledRulegenSamplingLines
            : (_options) => [],
          buildSampledRulegenHeader: typeof opts.buildSampledRulegenHeader === "function"
            ? opts.buildSampledRulegenHeader
            : (_options) => "",
          buildSampledRulegenEmptyOutput: typeof opts.buildSampledRulegenEmptyOutput === "function"
            ? opts.buildSampledRulegenEmptyOutput
            : (_options) => "",
          buildSampledRulegenTargetsOutput: typeof opts.buildSampledRulegenTargetsOutput === "function"
            ? opts.buildSampledRulegenTargetsOutput
            : (_options) => ""
        })
      : {
          initializeSet: async () => {},
          refreshSetNow: async () => {},
          runRuntimeDiagnostics: async () => {},
          previewSampledRulegen: async () => {},
          installSemanticPack: async () => {},
          resetSrsData: async () => {},
          refreshWordsDashboard: async () => {},
          setWordsDashboardAdvanced: () => {}
        };

    return {
      previewAdmission,
      initializeSet: maintenanceWorkflows.initializeSet,
      previewRebalance: rebalanceWorkflows.previewRebalance,
      applyRebalance: rebalanceWorkflows.applyRebalance,
      refreshSetNow: maintenanceWorkflows.refreshSetNow,
      runRuntimeDiagnostics: maintenanceWorkflows.runRuntimeDiagnostics,
      previewSampledRulegen: maintenanceWorkflows.previewSampledRulegen,
      installSemanticPack: maintenanceWorkflows.installSemanticPack,
      resetSrsData: maintenanceWorkflows.resetSrsData,
      refreshWordsDashboard: maintenanceWorkflows.refreshWordsDashboard,
      setWordsDashboardAdvanced: maintenanceWorkflows.setWordsDashboardAdvanced
    };
  }

  root.optionsSrsActionWorkflows = {
    createWorkflows
  };
})();
