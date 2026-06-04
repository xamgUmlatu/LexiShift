(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function renderOutputContent(output, content) {
    if (!output) {
      return;
    }
    if (content && typeof content === "object" && typeof content.html === "string") {
      output.innerHTML = content.html;
      return;
    }
    output.textContent = String(content ?? "");
  }

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({
          items,
          profileId: "default"
        }));
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const confirmFn = typeof opts.confirm === "function" ? opts.confirm : (message) => globalThis.confirm(message);
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const output = elements.output || null;
    const admissionPreviewOutput = elements.admissionPreviewOutput || null;
    const sampledOutput = elements.sampledOutput || null;
    const admissionPreviewButton = elements.admissionPreviewButton || null;
    const initializeButton = elements.initializeButton || null;
    const rebalancePreviewButton = elements.rebalancePreviewButton || null;
    const rebalanceApplyButton = elements.rebalanceApplyButton || null;
    const refreshButton = elements.refreshButton || null;
    const diagnosticsButton = elements.diagnosticsButton || null;
    const sampledButton = elements.sampledButton || null;
    const resetButton = elements.resetButton || null;
    const wordsRefreshButton = elements.wordsRefreshButton || null;
    const wordsAdvancedInput = elements.wordsAdvancedInput || null;
    const wordsSearchInput = elements.wordsSearchInput || null;
    const wordsStatusFilterInput = elements.wordsStatusFilterInput || null;
    const wordsSortInput = elements.wordsSortInput || null;
    const wordsPageSizeInput = elements.wordsPageSizeInput || null;
    const wordsClearFiltersButton = elements.wordsClearFiltersButton || null;
    const wordsSummaryRoot = elements.wordsSummaryRoot || null;
    const wordsPaginationRoot = elements.wordsPaginationRoot || null;
    const wordsPageInfoRoot = elements.wordsPageInfoRoot || null;
    const wordsFirstPageButton = elements.wordsFirstPageButton || null;
    const wordsPrevPageButton = elements.wordsPrevPageButton || null;
    const wordsNextPageButton = elements.wordsNextPageButton || null;
    const wordsLastPageButton = elements.wordsLastPageButton || null;
    const wordsMetaRoot = elements.wordsMetaRoot || null;
    const wordsListRoot = elements.wordsListRoot || null;
    const semanticPackInventoryPathInput = elements.semanticPackInventoryPathInput || null;
    const semanticPackIdInput = elements.semanticPackIdInput || null;
    const semanticPackDefaultDataRootInput = elements.semanticPackDefaultDataRootInput || null;
    const semanticPackDataRootInput = elements.semanticPackDataRootInput || null;
    const semanticPackInstallButton = elements.semanticPackInstallButton || null;
    const semanticPackInstallOutput = elements.semanticPackInstallOutput || null;

    const formatterHelpers = root.optionsSrsActionFormatters && typeof root.optionsSrsActionFormatters === "object"
      ? root.optionsSrsActionFormatters
      : {};
    const buildPreflightBlockedLines = typeof formatterHelpers.buildPreflightBlockedLines === "function"
      ? formatterHelpers.buildPreflightBlockedLines
      : (_options) => [];
    const buildInitializeResultOutput = typeof formatterHelpers.buildInitializeResultOutput === "function"
      ? formatterHelpers.buildInitializeResultOutput
      : (_options) => "";
    const buildRebalanceResultOutput = typeof formatterHelpers.buildRebalanceResultOutput === "function"
      ? formatterHelpers.buildRebalanceResultOutput
      : (_options) => "";
    const buildRefreshResultOutput = typeof formatterHelpers.buildRefreshResultOutput === "function"
      ? formatterHelpers.buildRefreshResultOutput
      : (_options) => "";
    const buildRuntimeDiagnosticsOutput = typeof formatterHelpers.buildRuntimeDiagnosticsOutput === "function"
      ? formatterHelpers.buildRuntimeDiagnosticsOutput
      : (_options) => "";
    const buildAdmissionPreviewOutput = typeof formatterHelpers.buildAdmissionPreviewOutput === "function"
      ? formatterHelpers.buildAdmissionPreviewOutput
      : (_options) => "";
    const buildSampledRulegenSamplingLines = typeof formatterHelpers.buildSampledRulegenSamplingLines === "function"
      ? formatterHelpers.buildSampledRulegenSamplingLines
      : (_options) => [];
    const buildSampledRulegenHeader = typeof formatterHelpers.buildSampledRulegenHeader === "function"
      ? formatterHelpers.buildSampledRulegenHeader
      : (_options) => "";
    const buildSampledRulegenEmptyOutput = typeof formatterHelpers.buildSampledRulegenEmptyOutput === "function"
      ? formatterHelpers.buildSampledRulegenEmptyOutput
      : (_options) => "";
    const buildSampledRulegenTargetsOutput = typeof formatterHelpers.buildSampledRulegenTargetsOutput === "function"
      ? formatterHelpers.buildSampledRulegenTargetsOutput
      : (_options) => "";

    const sharedFactory = root.optionsSrsActionsShared
      && typeof root.optionsSrsActionsShared.createShared === "function"
      ? root.optionsSrsActionsShared.createShared
      : null;
    const shared = sharedFactory
      ? sharedFactory({
          output,
          helperManager,
          buildPreflightBlockedLines,
          setStatus,
          colors,
          log
        })
      : {
          setOutputText: (_text) => {},
          markRulesetUpdatedNow: () => Promise.resolve(),
          preflightSrsPairResources: (_pair, _profileId, _actionLabel) => Promise.resolve(true)
        };

    const workflowsFactory = root.optionsSrsActionWorkflows
      && typeof root.optionsSrsActionWorkflows.createWorkflows === "function"
      ? root.optionsSrsActionWorkflows.createWorkflows
      : null;
    const workflows = workflowsFactory
      ? workflowsFactory({
          settingsManager,
          helperManager,
          translate,
          setStatus,
          resolvePair,
          syncSelectedProfile,
          confirmFn,
          log,
          colors,
          output,
          admissionPreviewOutput,
          sampledOutput,
          admissionPreviewButton,
          initializeButton,
          rebalancePreviewButton,
          rebalanceApplyButton,
          refreshButton,
          diagnosticsButton,
          sampledButton,
          resetButton,
          wordsRefreshButton,
          wordsAdvancedInput,
          wordsSearchInput,
          wordsStatusFilterInput,
          wordsSortInput,
          wordsPageSizeInput,
          wordsClearFiltersButton,
          wordsSummaryRoot,
          wordsPaginationRoot,
          wordsPageInfoRoot,
          wordsFirstPageButton,
          wordsPrevPageButton,
          wordsNextPageButton,
          wordsLastPageButton,
          wordsMetaRoot,
          wordsListRoot,
          semanticPackInventoryPathInput,
          semanticPackIdInput,
          semanticPackDefaultDataRootInput,
          semanticPackDataRootInput,
          semanticPackInstallButton,
          semanticPackInstallOutput,
          setOutputText: shared.setOutputText,
          setAdmissionPreviewOutputText: (text) => {
            if (admissionPreviewOutput) {
              renderOutputContent(admissionPreviewOutput, text);
              return;
            }
            shared.setOutputText(text);
          },
          setSampledOutputText: (text) => {
            if (sampledOutput) {
              sampledOutput.textContent = text;
              return;
            }
            shared.setOutputText(text);
          },
          loadSrsProfileForPair: opts.loadSrsProfileForPair,
          resolveEffectiveSrsPlanningState: opts.resolveEffectiveSrsPlanningState,
          refreshSemanticAdmissionStatus: opts.refreshSemanticAdmissionStatus,
          markRulesetUpdatedNow: shared.markRulesetUpdatedNow,
          preflightSrsPairResources: shared.preflightSrsPairResources,
          buildInitializeResultOutput,
          buildRebalanceResultOutput,
          buildRefreshResultOutput,
          buildRuntimeDiagnosticsOutput,
          buildAdmissionPreviewOutput,
          buildSampledRulegenSamplingLines,
          buildSampledRulegenHeader,
          buildSampledRulegenEmptyOutput,
          buildSampledRulegenTargetsOutput
        })
      : {
          previewAdmission: async () => {},
          initializeSet: async () => {},
          previewRebalance: async () => {},
          applyRebalance: async () => {},
          refreshSetNow: async () => {},
          runRuntimeDiagnostics: async () => {},
          previewSampledRulegen: async () => {},
          installSemanticPack: async () => {},
          resetSrsData: async () => {},
          refreshWordsDashboard: async () => {},
          setWordsDashboardAdvanced: () => {}
        };

    return {
      previewAdmission: workflows.previewAdmission,
      initializeSet: workflows.initializeSet,
      previewRebalance: workflows.previewRebalance,
      applyRebalance: workflows.applyRebalance,
      refreshSetNow: workflows.refreshSetNow,
      runRuntimeDiagnostics: workflows.runRuntimeDiagnostics,
      previewSampledRulegen: workflows.previewSampledRulegen,
      installSemanticPack: workflows.installSemanticPack,
      resetSrsData: workflows.resetSrsData,
      refreshWordsDashboard: workflows.refreshWordsDashboard,
      setWordsDashboardAdvanced: workflows.setWordsDashboardAdvanced
    };
  }

  root.optionsSrsActions = {
    createController
  };
})();
