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
    const rulesShareController = opts.rulesShareController && typeof opts.rulesShareController === "object"
      ? opts.rulesShareController
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const openExportButton = elements.openExportButton || null;
    const openImportButton = elements.openImportButton || null;
    const exportBackdrop = elements.exportBackdrop || null;
    const exportModal = elements.exportModal || null;
    const exportCloseButton = elements.exportCloseButton || null;
    const exportModeFullInput = elements.exportModeFullInput || null;
    const exportModeCustomInput = elements.exportModeCustomInput || null;
    const treePanel = elements.treePanel || null;
    const importBackdrop = elements.importBackdrop || null;
    const importModal = elements.importModal || null;
    const importCloseButton = elements.importCloseButton || null;
    const parentProfileInput = elements.parentProfileInput || null;
    const parentRulesetsInput = elements.parentRulesetsInput || null;
    const parentSrsInput = elements.parentSrsInput || null;
    const parentAppearanceInput = elements.parentAppearanceInput || null;
    const parentModuleHistoriesInput = elements.parentModuleHistoriesInput || null;
    const targetProfileSettingsInput = elements.targetProfileSettingsInput || null;
    const targetAppearanceThemeInput = elements.targetAppearanceThemeInput || null;
    const srsPairItemsRoot = elements.srsPairItemsRoot || null;
    const srsPairStatus = elements.srsPairStatus || null;
    const rulesetItemsRoot = elements.rulesetItemsRoot || null;
    const rulesetStatus = elements.rulesetStatus || null;
    const moduleItemsRoot = elements.moduleItemsRoot || null;
    const moduleStatus = elements.moduleStatus || null;
    const summaryTarget = elements.summaryTarget || null;
    const summaryGroups = elements.summaryGroups || null;
    const summaryOutput = elements.summaryOutput || null;
    const generateButton = elements.generateButton || null;
    const importFileInput = elements.importFileInput || null;
    const importFileNameOutput = elements.importFileNameOutput || null;
    const importButton = elements.importButton || null;
    const statusOutput = elements.statusOutput || null;
    const exportStatusOutput = elements.exportStatusOutput || null;
    const importStatusOutput = elements.importStatusOutput || null;
    const tr = (key, fallback, substitutions) => translate(key, substitutions, fallback);
    const pathJoiner = " > ";
    const shareCenterUtils = root.optionsShareCenterUtils;
    const shareCenterStatus = root.optionsShareCenterStatus;
    const shareCenterModal = root.optionsShareCenterModal;
    const shareCenterDataResolvers = root.optionsShareCenterDataResolvers;
    const shareCenterEventBinders = root.optionsShareCenterEventBinders;
    const shareCenterWorkflows = root.optionsShareCenterWorkflows;
    const shareCenterSummary = root.optionsShareCenterSummary;
    const shareCenterSync = root.optionsShareCenterSync;
    const shareCenterTreeState = root.optionsShareCenterTreeState;
    const shareCenterRenderers = root.optionsShareCenterRenderers;
    const shareCenterSelection = root.optionsShareCenterSelection;
    const shareCenterProfileResolvers = root.optionsShareCenterProfileResolvers;
    if (!shareCenterUtils || !shareCenterStatus || !shareCenterModal || !shareCenterDataResolvers || !shareCenterEventBinders || !shareCenterWorkflows || !shareCenterSummary || !shareCenterSync || !shareCenterTreeState || !shareCenterRenderers || !shareCenterSelection || !shareCenterProfileResolvers) {
      throw new Error("Share Center dependencies are missing.");
    }
    const labels = {
      profile: tr("share_center_group_profile", "Profile"),
      profileConfiguration: tr("share_center_group_profile_configuration", "Profile configuration"),
      configuration: tr("share_center_path_configuration", "Configuration"),
      rulesets: tr("share_center_group_rulesets", "Rulesets"),
      srsData: tr("share_center_group_srs_data", "SRS data"),
      appearance: tr("share_center_group_appearance", "Appearance"),
      modules: tr("share_center_group_modules", "Modules"),
      themeColors: tr("share_center_target_theme_colors", "Theme/colors")
    };
    function joinPath(parts) {
      const list = Array.isArray(parts) ? parts.filter((part) => String(part || "").trim()) : [];
      return list.join(pathJoiner);
    }

    const STATIC_TARGETS = {
      profile_settings: {
        id: "profile_settings",
        kind: "profile_settings",
        label: tr("share_center_target_profile_settings", "Profile settings"),
        path: joinPath([labels.profile, labels.configuration]),
        groups: [labels.profileConfiguration, labels.srsData],
        scope: "srs",
        enabled: true
      },
      appearance_theme: {
        id: "appearance_theme",
        kind: "appearance_theme",
        label: labels.themeColors,
        path: joinPath([labels.profile, labels.appearance, labels.themeColors]),
        groups: [labels.appearance],
        scope: "appearance_theme",
        enabled: true
      }
    };
    const FULL_PROFILE_GROUPS = [
      labels.profileConfiguration,
      labels.rulesets,
      labels.srsData,
      labels.appearance,
      labels.modules
    ];

    const staticLeafInputs = {
      profile_settings: targetProfileSettingsInput,
      appearance_theme: targetAppearanceThemeInput
    };

    const parentInputs = {
      profile_group: parentProfileInput,
      rulesets_group: parentRulesetsInput,
      srs_group: parentSrsInput,
      appearance_group: parentAppearanceInput,
      modules_group: parentModuleHistoriesInput
    };

    let currentProfileId = "default";
    let selectedRulesetPath = "";
    let dynamicSrsPairIds = [];
    let dynamicRulesetIds = [];
    let dynamicModuleIds = [];
    let exportMode = "full";
    const dynamicLeafState = new Map();

    const normalizePath = shareCenterUtils.normalizePath;
    const pathBasename = (path) => shareCenterUtils.pathBasename(
      path,
      tr("share_center_value_unknown", "(unknown)"),
      normalizePath
    );
    const isObject = shareCenterUtils.isObject;
    const normalizeSrsPairKey = (rawPair, fallbackPair) => shareCenterUtils.normalizeSrsPairKey(
      rawPair,
      fallbackPair,
      settingsManager && typeof settingsManager._normalizePairKey === "function"
        ? settingsManager._normalizePairKey.bind(settingsManager)
        : null
    );
    const hasMeaningfulValue = (value, depth) => shareCenterUtils.hasMeaningfulValue(value, depth, isObject);
    const resolveExportFileName = shareCenterUtils.resolveExportFileName;
    const formatByteSize = shareCenterUtils.formatByteSize;
    const downloadJsonFile = shareCenterUtils.downloadJsonFile;
    const statusHelpers = shareCenterStatus.createStatusHelpers({
      colors,
      setStatus,
      statusOutput,
      rulesetStatus,
      srsPairStatus,
      moduleStatus,
      exportStatusOutput,
      importStatusOutput
    });
    const modalHelpers = shareCenterModal.createModalHelpers({
      exportBackdrop,
      exportModal,
      importBackdrop,
      importModal,
      body: document.body
    });
    const setOutputStatus = statusHelpers.setOutputStatus;
    const setRulesetStatus = statusHelpers.setRulesetStatus;
    const setSrsPairStatus = statusHelpers.setSrsPairStatus;
    const setModuleStatus = statusHelpers.setModuleStatus;
    const setExportStatus = statusHelpers.setExportStatus;
    const setExportHint = statusHelpers.setExportHint;
    const setImportStatus = statusHelpers.setImportStatus;
    const openModal = modalHelpers.openModal;
    const closeModal = modalHelpers.closeModal;
    const closeAllModals = modalHelpers.closeAllModals;

    function isFullMode() {
      return exportMode !== "custom";
    }

    function isEntryBaseDisabled(entry) {
      return !entry || !entry.meta || entry.meta.enabled === false;
    }

    function updateTreePanelModeState() {
      if (!treePanel) {
        return;
      }
      treePanel.classList.toggle("is-disabled", isFullMode());
    }

    function applyExportModeUI() {
      const fullMode = isFullMode();
      updateTreePanelModeState();
      Object.values(parentInputs).forEach((input) => {
        if (!input) {
          return;
        }
        if (fullMode) {
          input.checked = false;
          input.indeterminate = false;
          input.disabled = true;
        } else {
          input.disabled = false;
        }
      });
      collectAllLeafEntries().forEach((entry) => {
        if (!entry || !entry.input) {
          return;
        }
        const disabled = fullMode || isEntryBaseDisabled(entry);
        entry.input.disabled = disabled;
        const row = entry.input.closest(".share-center-target");
        if (row) {
          row.classList.toggle("is-disabled", disabled);
          row.classList.toggle("is-mode-disabled", fullMode && !isEntryBaseDisabled(entry));
        }
      });
    }

    function setExportMode(modeValue) {
      exportMode = String(modeValue || "").trim().toLowerCase() === "custom" ? "custom" : "full";
      if (exportModeFullInput) {
        exportModeFullInput.checked = exportMode === "full";
      }
      if (exportModeCustomInput) {
        exportModeCustomInput.checked = exportMode === "custom";
      }
      applyExportModeUI();
      updateAllParentStates();
      updateSummary();
    }

    const shareCenterTreeApi = shareCenterTreeState.createHelpers({
      staticTargets: STATIC_TARGETS,
      staticLeafInputs,
      dynamicLeafState,
      parentInputs,
      getDynamicSrsPairIds: () => dynamicSrsPairIds,
      getDynamicRulesetIds: () => dynamicRulesetIds,
      getDynamicModuleIds: () => dynamicModuleIds,
      isFullMode,
      normalizePath,
      setSelectedRulesetPath: (nextPath) => {
        selectedRulesetPath = nextPath;
      },
      updateSummary: () => updateSummary()
    });
    const clearDynamicLeafsByKind = shareCenterTreeApi.clearDynamicLeafsByKind;
    const collectAllLeafEntries = shareCenterTreeApi.collectAllLeafEntries;
    const getSelectedLeafEntries = shareCenterTreeApi.getSelectedLeafEntries;
    const updateAllParentStates = shareCenterTreeApi.updateAllParentStates;
    const applyParentToggle = shareCenterTreeApi.applyParentToggle;
    const onLeafChanged = shareCenterTreeApi.onLeafChanged;

    const profileResolverHelpers = shareCenterProfileResolvers.createProfileResolverHelpers({
      settingsManager,
      translate,
      labels,
      isObject,
      normalizeSrsPairKey,
      hasMeaningfulValue,
      shareCenterDataResolvers
    });
    const resolveProfileModules = profileResolverHelpers.resolveProfileModules;
    const resolveProfileSrsPairs = profileResolverHelpers.resolveProfileSrsPairs;

    const shareCenterRendererApi = shareCenterRenderers.createRenderers({
      srsPairItemsRoot,
      rulesetItemsRoot,
      moduleItemsRoot,
      dynamicLeafState,
      getDynamicSrsPairIds: () => dynamicSrsPairIds,
      setDynamicSrsPairIds: (nextValue) => {
        dynamicSrsPairIds = Array.isArray(nextValue) ? nextValue : [];
      },
      getDynamicRulesetIds: () => dynamicRulesetIds,
      setDynamicRulesetIds: (nextValue) => {
        dynamicRulesetIds = Array.isArray(nextValue) ? nextValue : [];
      },
      getDynamicModuleIds: () => dynamicModuleIds,
      setDynamicModuleIds: (nextValue) => {
        dynamicModuleIds = Array.isArray(nextValue) ? nextValue : [];
      },
      clearDynamicLeafsByKind,
      resolveProfileSrsPairs,
      resolveProfileModules,
      joinPath,
      labels,
      tr,
      colors,
      setSrsPairStatus,
      setRulesetStatus,
      setModuleStatus,
      onLeafChanged,
      normalizePath,
      pathBasename,
      isObject,
      getSelectedRulesetPath: () => selectedRulesetPath,
      setSelectedRulesetPath: (nextPath) => {
        selectedRulesetPath = nextPath;
      }
    });
    const renderSrsPairItems = shareCenterRendererApi.renderSrsPairItems;
    const renderRulesetItems = shareCenterRendererApi.renderRulesetItems;
    const renderModuleItems = shareCenterRendererApi.renderModuleItems;

    function updateSummary() {
      shareCenterSummary.updateSummary({
        isFullMode,
        tr,
        currentProfileId,
        summaryTarget,
        summaryGroups,
        summaryOutput,
        generateButton,
        fullProfileGroups: FULL_PROFILE_GROUPS,
        setExportHint,
        shareCenterSelection,
        getSelectedLeafEntries,
        normalizePath
      });
    }

    const shareCenterWorkflowApi = shareCenterWorkflows.createWorkflows({
      rulesShareController,
      helperManager,
      shareCenterSelection,
      isFullMode,
      getCurrentProfileId: () => currentProfileId,
      getSelectedLeafEntries,
      normalizePath,
      resolveExportFileName,
      formatByteSize,
      downloadJsonFile,
      setExportStatus,
      setImportStatus,
      updateSummary,
      syncForProfile: (optionsArg) => syncForProfile(optionsArg),
      tr,
      colors,
      importFileInput,
      importFileNameOutput,
      reloadPage: () => {
        window.location.reload();
      }
    });
    const setImportFileName = shareCenterWorkflowApi.setImportFileName;
    const generateShareCode = shareCenterWorkflowApi.generateShareCode;
    const importShareCode = shareCenterWorkflowApi.importShareCode;

    function bindEvents() {
      shareCenterEventBinders.bindEvents({
        parentInputs,
        staticLeafInputs,
        staticTargets: STATIC_TARGETS,
        applyParentToggle,
        updateAllParentStates,
        updateSummary,
        onLeafChanged,
        setExportMode,
        openModal,
        closeModal,
        closeAllModals,
        setOutputStatus,
        setImportFileName,
        generateShareCode,
        importShareCode,
        setExportStatus,
        setImportStatus,
        log,
        tr,
        colors,
        openExportButton,
        openImportButton,
        exportBackdrop,
        exportCloseButton,
        importBackdrop,
        importCloseButton,
        exportModeFullInput,
        exportModeCustomInput,
        importFileInput,
        importButton,
        generateButton,
        importStatusOutput
      });
    }

    const shareCenterSyncHelpers = shareCenterSync.createSyncHelpers({
      settingsManager,
      isObject,
      normalizePath,
      renderSrsPairItems,
      renderRulesetItems,
      renderModuleItems,
      applyExportModeUI,
      updateAllParentStates,
      updateSummary,
      setCurrentProfileId: (profileId) => {
        currentProfileId = profileId;
      },
      getDynamicSrsPairIds: () => dynamicSrsPairIds,
      getDynamicRulesetIds: () => dynamicRulesetIds,
      getDynamicModuleIds: () => dynamicModuleIds
    });

    async function syncForProfile(optionsArg) {
      return shareCenterSyncHelpers.syncForProfile(optionsArg);
    }

    bindEvents();
    if (targetProfileSettingsInput && targetProfileSettingsInput.checked !== true) {
      targetProfileSettingsInput.checked = true;
    }
    if (exportModeCustomInput && exportModeCustomInput.checked === true) {
      exportMode = "custom";
    } else {
      exportMode = "full";
    }
    setExportMode(exportMode);

    return {
      syncForProfile,
      generateShareCode,
      importShareCode
    };
  }

  root.optionsShareCenter = {
    createController
  };
})();
