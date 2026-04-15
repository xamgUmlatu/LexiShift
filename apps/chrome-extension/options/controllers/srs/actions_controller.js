(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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
          setOutputText: shared.setOutputText,
          setAdmissionPreviewOutputText: (text) => {
            if (admissionPreviewOutput) {
              admissionPreviewOutput.textContent = text;
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
          resolveEffectiveSrsPlanningState: opts.resolveEffectiveSrsPlanningState,
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
          resetSrsData: async () => {}
        };

    return {
      previewAdmission: workflows.previewAdmission,
      initializeSet: workflows.initializeSet,
      previewRebalance: workflows.previewRebalance,
      applyRebalance: workflows.applyRebalance,
      refreshSetNow: workflows.refreshSetNow,
      runRuntimeDiagnostics: workflows.runRuntimeDiagnostics,
      previewSampledRulegen: workflows.previewSampledRulegen,
      resetSrsData: workflows.resetSrsData
    };
  }

  root.optionsSrsActions = {
    createController
  };
})();
