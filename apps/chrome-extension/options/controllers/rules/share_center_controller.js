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
    const targetSrsPairInput = elements.targetSrsPairInput || null;
    const targetAppearanceThemeInput = elements.targetAppearanceThemeInput || null;
    const rulesetItemsRoot = elements.rulesetItemsRoot || null;
    const rulesetStatus = elements.rulesetStatus || null;
    const moduleItemsRoot = elements.moduleItemsRoot || null;
    const moduleStatus = elements.moduleStatus || null;
    const summaryTarget = elements.summaryTarget || null;
    const summaryGroups = elements.summaryGroups || null;
    const summarySize = elements.summarySize || null;
    const summaryOutput = elements.summaryOutput || null;
    const exportCodeInput = elements.shareCodeInput || null;
    const exportCodeCjk = elements.shareCodeCjk || null;
    const generateButton = elements.generateButton || null;
    const copyButton = elements.copyButton || null;
    const importCodeInput = elements.importCodeInput || null;
    const importCodeCjk = elements.importCodeCjk || null;
    const importButton = elements.importButton || null;
    const importClearButton = elements.importClearButton || null;
    const statusOutput = elements.statusOutput || null;
    const exportStatusOutput = elements.exportStatusOutput || null;
    const importStatusOutput = elements.importStatusOutput || null;

    const STATIC_TARGETS = {
      profile_settings: {
        id: "profile_settings",
        kind: "profile_settings",
        label: "Profile settings",
        path: "Profile > Configuration",
        groups: ["Profile configuration", "SRS data"],
        scope: "srs",
        enabled: true
      },
      srs_pair: {
        id: "srs_pair",
        kind: "srs_pair",
        label: "SRS progress (pair)",
        path: "Profile > SRS data > Pair progress",
        groups: ["SRS data"],
        scope: null,
        enabled: false,
        reason: "Coming soon"
      },
      appearance_theme: {
        id: "appearance_theme",
        kind: "appearance_theme",
        label: "Theme/colors",
        path: "Profile > Appearance > Theme/colors",
        groups: ["Appearance"],
        scope: null,
        enabled: false,
        reason: "Coming soon"
      }
    };
    const FULL_PROFILE_GROUPS = [
      "Profile configuration",
      "Rulesets",
      "SRS data",
      "Appearance",
      "Modules"
    ];

    const staticLeafInputs = {
      profile_settings: targetProfileSettingsInput,
      srs_pair: targetSrsPairInput,
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
    let dynamicRulesetIds = [];
    let dynamicModuleIds = [];
    let exportMode = "full";
    const dynamicLeafState = new Map();

    function normalizeProfileId(profileId) {
      if (settingsManager && typeof settingsManager.normalizeSrsProfileId === "function") {
        return settingsManager.normalizeSrsProfileId(profileId);
      }
      const normalized = String(profileId || "").trim();
      return normalized || "default";
    }

    function normalizePath(path) {
      const normalized = String(path || "").trim();
      return normalized || "";
    }

    function pathBasename(path) {
      const normalized = normalizePath(path);
      if (!normalized) {
        return "(unknown)";
      }
      const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
      return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
    }

    function isObject(value) {
      return Boolean(value) && typeof value === "object" && !Array.isArray(value);
    }

    function getPopupModulesRegistry() {
      const registry = root.popupModulesRegistry;
      return registry && typeof registry === "object" ? registry : null;
    }

    function setOutputStatus(output, message, color) {
      if (!output) {
        return;
      }
      output.textContent = message || "";
      output.style.color = color || colors.DEFAULT;
    }

    function setCardStatus(message, color) {
      setOutputStatus(statusOutput, message, color);
      if (message) {
        setStatus(message, color || colors.DEFAULT);
      }
    }

    function setRulesetStatus(message, color) {
      setOutputStatus(rulesetStatus, message, color);
    }

    function setModuleStatus(message, color) {
      setOutputStatus(moduleStatus, message, color);
    }

    function setExportStatus(message, color) {
      setOutputStatus(exportStatusOutput, message, color);
      if (message) {
        setCardStatus(message, color);
      }
    }

    function setExportHint(message) {
      setOutputStatus(exportStatusOutput, message, colors.DEFAULT);
    }

    function setImportStatus(message, color) {
      setOutputStatus(importStatusOutput, message, color);
      if (message) {
        setCardStatus(message, color);
      }
    }

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

    function clearDynamicLeafsByKind(kind) {
      const removeIds = [];
      dynamicLeafState.forEach((entry, leafId) => {
        if (entry && entry.kind === kind) {
          removeIds.push(leafId);
        }
      });
      removeIds.forEach((leafId) => {
        dynamicLeafState.delete(leafId);
      });
    }

    function getLeafEntryById(leafId) {
      if (Object.prototype.hasOwnProperty.call(STATIC_TARGETS, leafId)) {
        const input = staticLeafInputs[leafId];
        if (!input) {
          return null;
        }
        return {
          id: leafId,
          kind: "static",
          input,
          meta: STATIC_TARGETS[leafId]
        };
      }
      return dynamicLeafState.get(leafId) || null;
    }

    function collectAllLeafEntries() {
      const entries = [];
      Object.keys(staticLeafInputs).forEach((leafId) => {
        const entry = getLeafEntryById(leafId);
        if (entry) {
          entries.push(entry);
        }
      });
      dynamicLeafState.forEach((entry) => {
        if (entry && entry.input) {
          entries.push(entry);
        }
      });
      return entries;
    }

    function getSelectedLeafEntries() {
      return collectAllLeafEntries().filter((entry) => entry.input.checked === true);
    }

    function resolveParentChildIds(parentId) {
      if (parentId === "profile_group") {
        return [
          "profile_settings",
          "srs_pair",
          "appearance_theme",
          ...dynamicRulesetIds,
          ...dynamicModuleIds
        ];
      }
      if (parentId === "rulesets_group") {
        return [...dynamicRulesetIds];
      }
      if (parentId === "srs_group") {
        return ["srs_pair"];
      }
      if (parentId === "appearance_group") {
        return ["appearance_theme"];
      }
      if (parentId === "modules_group") {
        return [...dynamicModuleIds];
      }
      return [];
    }

    function getSelectableChildEntries(parentId) {
      return resolveParentChildIds(parentId)
        .map((leafId) => getLeafEntryById(leafId))
        .filter((entry) => entry && entry.input && entry.input.disabled !== true);
    }

    function updateParentState(parentId) {
      const parentInput = parentInputs[parentId];
      if (!parentInput) {
        return;
      }
      const childEntries = getSelectableChildEntries(parentId);
      if (!childEntries.length) {
        parentInput.checked = false;
        parentInput.indeterminate = false;
        parentInput.disabled = true;
        return;
      }
      parentInput.disabled = false;
      const checkedCount = childEntries.filter((entry) => entry.input.checked === true).length;
      if (checkedCount <= 0) {
        parentInput.checked = false;
        parentInput.indeterminate = false;
        return;
      }
      if (checkedCount >= childEntries.length) {
        parentInput.checked = true;
        parentInput.indeterminate = false;
        return;
      }
      parentInput.checked = false;
      parentInput.indeterminate = true;
    }

    function updateAllParentStates() {
      if (isFullMode()) {
        Object.values(parentInputs).forEach((input) => {
          if (!input) {
            return;
          }
          input.checked = false;
          input.indeterminate = false;
          input.disabled = true;
        });
        return;
      }
      Object.keys(parentInputs).forEach((parentId) => {
        updateParentState(parentId);
      });
    }

    function applyParentToggle(parentId, checked) {
      const childEntries = getSelectableChildEntries(parentId);
      childEntries.forEach((entry) => {
        entry.input.checked = checked === true;
      });
    }

    function onLeafChanged(entry) {
      if (entry && entry.meta && entry.meta.kind === "ruleset_item" && entry.input.checked === true) {
        selectedRulesetPath = normalizePath(entry.meta.rulesetPath);
      }
      updateAllParentStates();
      updateSummary();
    }

    function createDynamicLeafRow(targetMeta, optionsArg) {
      const options = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const label = document.createElement("label");
      label.className = "share-center-target";
      if (options.isPending) {
        label.classList.add("is-pending");
      }
      if (options.isDisabled) {
        label.classList.add("is-disabled");
      }

      const input = document.createElement("input");
      input.type = "checkbox";
      input.name = "share-center-target";
      input.value = targetMeta.id;
      if (options.checked === true) {
        input.checked = true;
      }
      if (options.isDisabled === true) {
        input.disabled = true;
      }

      const body = document.createElement("span");
      body.className = "share-center-target-body";

      const title = document.createElement("span");
      title.className = "share-center-target-title";
      title.textContent = targetMeta.label;

      const hint = document.createElement("span");
      hint.className = "share-center-target-hint";
      hint.textContent = String(options.hint || "").trim() || " ";

      body.appendChild(title);
      body.appendChild(hint);

      label.appendChild(input);
      label.appendChild(body);

      if (options.badge) {
        const badge = document.createElement("span");
        badge.className = "share-center-badge";
        badge.textContent = String(options.badge);
        label.appendChild(badge);
      }

      return {
        label,
        input
      };
    }

    function resolveProfileModules(items, profileId) {
      const languagePrefs = settingsManager && typeof settingsManager.getProfileLanguagePrefs === "function"
        ? settingsManager.getProfileLanguagePrefs(items, { profileId })
        : { targetLanguage: "en" };
      const targetLanguage = String(languagePrefs && languagePrefs.targetLanguage || "en").trim() || "en";
      const modulePrefs = settingsManager && typeof settingsManager.getProfileModulePrefs === "function"
        ? settingsManager.getProfileModulePrefs(items, { profileId, targetLanguage })
        : { byId: {}, order: [] };
      const byId = isObject(modulePrefs && modulePrefs.byId) ? modulePrefs.byId : {};
      const prefsOrder = Array.isArray(modulePrefs && modulePrefs.order) ? modulePrefs.order : [];

      const registry = getPopupModulesRegistry();
      if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
        const fallbackOrder = [];
        const fallbackSeen = new Set();
        prefsOrder.forEach((rawId) => {
          const moduleId = String(rawId || "").trim();
          if (!moduleId || fallbackSeen.has(moduleId)) {
            return;
          }
          fallbackSeen.add(moduleId);
          fallbackOrder.push(moduleId);
        });
        Object.keys(byId).forEach((rawId) => {
          const moduleId = String(rawId || "").trim();
          if (!moduleId || fallbackSeen.has(moduleId)) {
            return;
          }
          fallbackSeen.add(moduleId);
          fallbackOrder.push(moduleId);
        });
        return {
          targetLanguage,
          modules: fallbackOrder.map((moduleId) => {
            const prefsEntry = isObject(byId[moduleId]) ? byId[moduleId] : {};
            return {
              moduleId,
              label: moduleId,
              description: "",
              enabledInProfile: prefsEntry.enabled !== false
            };
          })
        };
      }

      const visibleDefinitionsRaw = registry.resolveVisibleSettingModules(targetLanguage);
      const visibleDefinitions = Array.isArray(visibleDefinitionsRaw) ? visibleDefinitionsRaw : [];
      const definitionsById = new Map();
      visibleDefinitions.forEach((definition) => {
        const moduleId = String(definition && definition.id || "").trim();
        if (!moduleId) {
          return;
        }
        definitionsById.set(moduleId, definition);
      });

      const order = [];
      const seen = new Set();
      prefsOrder.forEach((rawId) => {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || seen.has(moduleId)) {
          return;
        }
        seen.add(moduleId);
        order.push(moduleId);
      });
      Object.keys(byId).forEach((rawId) => {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || seen.has(moduleId)) {
          return;
        }
        seen.add(moduleId);
        order.push(moduleId);
      });
      visibleDefinitions.forEach((definition) => {
        const moduleId = String(definition && definition.id || "").trim();
        if (!moduleId || seen.has(moduleId)) {
          return;
        }
        seen.add(moduleId);
        order.push(moduleId);
      });

      const modules = order.map((moduleId) => {
        const definition = definitionsById.get(moduleId) || {};
        const prefsEntry = isObject(byId[moduleId]) ? byId[moduleId] : {};
        const moduleEnabled = prefsEntry.enabled !== false;
        const label = translate(
          String(definition.labelKey || ""),
          null,
          String(definition.labelFallback || moduleId)
        );
        const description = translate(
          String(definition.descriptionKey || ""),
          null,
          String(definition.descriptionFallback || "")
        );
        return {
          moduleId,
          label: String(label || moduleId),
          description: String(description || "").trim(),
          enabledInProfile: moduleEnabled
        };
      });
      return {
        targetLanguage,
        modules
      };
    }

    function renderRulesetItems(profileId, manualState, cache) {
      if (!rulesetItemsRoot) {
        return;
      }
      const previouslyCheckedPaths = new Set();
      dynamicLeafState.forEach((entry) => {
        if (!entry || entry.kind !== "ruleset_item") {
          return;
        }
        if (entry.input && entry.input.checked && entry.meta && entry.meta.rulesetPath) {
          previouslyCheckedPaths.add(String(entry.meta.rulesetPath));
        }
      });

      clearDynamicLeafsByKind("ruleset_item");
      dynamicRulesetIds = [];
      rulesetItemsRoot.innerHTML = "";

      const entries = [];
      const seen = new Set();
      const enabledByPath = isObject(manualState && manualState.enabledByPath)
        ? manualState.enabledByPath
        : {};
      (Array.isArray(manualState.order) ? manualState.order : []).forEach((rawPath) => {
        const pathKey = normalizePath(rawPath);
        if (!pathKey || seen.has(pathKey)) {
          return;
        }
        seen.add(pathKey);
        const cacheEntry = cache[pathKey];
        const rules = cacheEntry && Array.isArray(cacheEntry.rules) ? cacheEntry.rules : [];
        const rulesCountRaw = cacheEntry
          ? (Number.isFinite(Number(cacheEntry.rulesCount)) ? Number(cacheEntry.rulesCount) : rules.length)
          : 0;
        const rulesCount = Math.max(0, rulesCountRaw);
        const exportable = rulesCount > 0;
        entries.push({
          path: pathKey,
          displayPath: cacheEntry && cacheEntry.displayPath ? cacheEntry.displayPath : pathKey,
          rulesCount,
          exportable,
          profileEnabled: enabledByPath[pathKey] !== false
        });
      });

      if (!entries.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = "No profile rulesets available.";
        rulesetItemsRoot.appendChild(empty);
        setRulesetStatus(`No exportable rulesets for profile ${profileId}.`, colors.DEFAULT);
        return;
      }

      const firstExportablePath = (() => {
        for (const entry of entries) {
          if (entry.exportable) {
            return entry.path;
          }
        }
        return "";
      })();

      entries.forEach((rulesetEntry) => {
        const pathKey = normalizePath(rulesetEntry.path);
        const leafId = `ruleset::${encodeURIComponent(pathKey)}`;
        const label = pathBasename(rulesetEntry.displayPath);
        const exportable = rulesetEntry.exportable === true;
        const meta = {
          id: leafId,
          kind: "ruleset_item",
          label,
          path: `Profile > Rulesets > ${label}`,
          groups: ["Rulesets"],
          scope: exportable ? "ruleset" : null,
          enabled: exportable,
          reason: exportable ? "" : "Rules not loaded",
          rulesetPath: pathKey,
          rulesetName: label,
          rulesCount: rulesetEntry.rulesCount,
          profileEnabled: rulesetEntry.profileEnabled
        };
        const checked = exportable && (
          previouslyCheckedPaths.has(pathKey)
          || (!previouslyCheckedPaths.size && selectedRulesetPath === pathKey)
          || (!previouslyCheckedPaths.size && !selectedRulesetPath && pathKey === firstExportablePath)
        );
        const profileEnabledText = rulesetEntry.profileEnabled ? "Enabled in profile" : "Disabled in profile";
        const pathText = normalizePath(rulesetEntry.displayPath);
        const hint = exportable
          ? `${rulesetEntry.rulesCount} rules • ${profileEnabledText}${pathText && pathText !== label ? ` • ${pathText}` : ""}`
          : `Rules not loaded yet for this path${pathText && pathText !== label ? ` • ${pathText}` : ""}`;
        const row = createDynamicLeafRow(meta, {
          checked,
          hint,
          isPending: exportable !== true,
          isDisabled: exportable !== true,
          badge: exportable ? (rulesetEntry.profileEnabled ? "Enabled" : "Disabled") : "Unavailable"
        });
        const entry = {
          id: leafId,
          kind: "ruleset_item",
          input: row.input,
          meta
        };
        row.input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
        rulesetItemsRoot.appendChild(row.label);
        dynamicLeafState.set(leafId, entry);
        dynamicRulesetIds.push(leafId);
        if (row.input.checked && exportable) {
          selectedRulesetPath = pathKey;
        }
      });
      const exportableCount = entries.filter((entry) => entry.exportable).length;
      setRulesetStatus(
        `${entries.length} ruleset${entries.length === 1 ? "" : "s"} on profile ${profileId}; ${exportableCount} exportable now.`,
        colors.DEFAULT
      );
    }

    function renderModuleItems(items, profileId) {
      if (!moduleItemsRoot) {
        return;
      }
      const previouslyCheckedModuleIds = new Set();
      dynamicLeafState.forEach((entry) => {
        if (!entry || entry.kind !== "module_item") {
          return;
        }
        if (entry.input && entry.input.checked && entry.meta && entry.meta.moduleId) {
          previouslyCheckedModuleIds.add(String(entry.meta.moduleId));
        }
      });

      clearDynamicLeafsByKind("module_item");
      dynamicModuleIds = [];
      moduleItemsRoot.innerHTML = "";

      const moduleData = resolveProfileModules(items, profileId);
      const modules = Array.isArray(moduleData.modules) ? moduleData.modules : [];
      const targetLanguage = String(moduleData.targetLanguage || "en");

      if (!modules.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = "No modules available for this profile/language.";
        moduleItemsRoot.appendChild(empty);
        setModuleStatus(`No modules available for profile ${profileId} (${targetLanguage}).`, colors.DEFAULT);
        return;
      }

      modules.forEach((moduleEntry) => {
        const moduleId = String(moduleEntry.moduleId || "").trim();
        if (!moduleId) {
          return;
        }
        const leafId = `module::${moduleId}`;
        const label = String(moduleEntry.label || moduleId);
        const meta = {
          id: leafId,
          kind: "module_item",
          label,
          path: `Profile > Modules > ${label}`,
          groups: ["Modules"],
          scope: null,
          enabled: false,
          reason: "Coming soon",
          moduleId,
          moduleEnabledInProfile: moduleEntry.enabledInProfile === true
        };
        const enabledInProfile = moduleEntry.enabledInProfile === true;
        const row = createDynamicLeafRow(meta, {
          checked: previouslyCheckedModuleIds.has(moduleId),
          hint: moduleEntry.description
            ? `${moduleEntry.description} • ${enabledInProfile ? "Enabled in profile" : "Disabled in profile"}`
            : (
                enabledInProfile
                  ? "Enabled in this profile."
                  : "Disabled in this profile."
              ),
          isPending: true,
          badge: "Coming soon"
        });
        const entry = {
          id: leafId,
          kind: "module_item",
          input: row.input,
          meta
        };
        row.input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
        moduleItemsRoot.appendChild(row.label);
        dynamicLeafState.set(leafId, entry);
        dynamicModuleIds.push(leafId);
      });

      setModuleStatus(
        `${modules.length} module${modules.length === 1 ? "" : "s"} for profile ${profileId} (${targetLanguage}).`,
        colors.DEFAULT
      );
    }

    function resolveSelectionPlan() {
      const selectedEntries = getSelectedLeafEntries();
      const selectedTargets = selectedEntries.map((entry) => entry.meta).filter(Boolean);
      const supportedTargets = selectedTargets.filter((target) => target.enabled !== false && Boolean(target.scope));
      const unsupportedTargets = selectedTargets.filter((target) => target.enabled === false || !target.scope);
      return {
        selectedTargets,
        supportedTargets,
        unsupportedTargets
      };
    }

    function estimateSize(plan) {
      const supportedTargets = Array.isArray(plan && plan.supportedTargets) ? plan.supportedTargets : [];
      if (!supportedTargets.length) {
        return "—";
      }
      if (supportedTargets.some((target) => target.kind === "profile")) {
        return "large";
      }
      let score = 1;
      supportedTargets.forEach((target) => {
        if (target.kind === "profile_settings") {
          score = Math.max(score, 2);
          return;
        }
        if (target.kind === "ruleset_item") {
          const rulesCount = Number(target.rulesCount || 0);
          if (rulesCount > 1500) {
            score = Math.max(score, 3);
          } else if (rulesCount > 250) {
            score = Math.max(score, 2);
          }
        }
      });
      if (supportedTargets.length > 1) {
        score = Math.max(score, 2);
      }
      if (score >= 3) {
        return "large";
      }
      if (score <= 1) {
        return "small";
      }
      return "medium";
    }

    function recommendOutput(plan, sizeCategory) {
      const supportedTargets = Array.isArray(plan && plan.supportedTargets) ? plan.supportedTargets : [];
      if (!supportedTargets.length) {
        return "—";
      }
      if (supportedTargets.length > 1) {
        return "file (bundle)";
      }
      if (sizeCategory === "large") {
        return "file";
      }
      return "short code";
    }

    function buildPathSummary(plan) {
      const selectedTargets = Array.isArray(plan && plan.selectedTargets) ? plan.selectedTargets : [];
      if (!selectedTargets.length) {
        return `None (${currentProfileId})`;
      }
      const paths = selectedTargets.map((target) => String(target.path || target.label || "").trim()).filter(Boolean);
      if (!paths.length) {
        return `None (${currentProfileId})`;
      }
      if (paths.length <= 2) {
        return `${paths.join(" + ")} (${currentProfileId})`;
      }
      return `${paths[0]} + ${paths[1]} + ${paths.length - 2} more (${currentProfileId})`;
    }

    function buildIncludesSummary(plan) {
      const selectedTargets = Array.isArray(plan && plan.selectedTargets) ? plan.selectedTargets : [];
      if (!selectedTargets.length) {
        return "Nothing selected.";
      }
      return selectedTargets.map((target) => {
        if (target.kind === "ruleset_item") {
          return `Ruleset: ${target.label} (${target.rulesCount} rules)`;
        }
        if (target.kind === "module_item") {
          return `Module: ${target.label}`;
        }
        return target.label;
      }).join(" | ");
    }

    function resolveGenerateSelection(planArg) {
      const plan = planArg && typeof planArg === "object" ? planArg : resolveSelectionPlan();
      if (!plan.selectedTargets.length) {
        return {
          ok: false,
          message: "Select one or more nodes."
        };
      }
      if (!plan.supportedTargets.length) {
        return {
          ok: false,
          message: "Selected nodes are not exportable yet."
        };
      }
      if (plan.supportedTargets.length > 1) {
        return {
          ok: false,
          message: "Bundle export for multiple nodes is coming soon. Keep one exportable node selected for now."
        };
      }
      const target = plan.supportedTargets[0];
      if (target.kind === "ruleset_item" && !normalizePath(target.rulesetPath)) {
        return {
          ok: false,
          message: "Choose a ruleset entry before generating."
        };
      }
      return {
        ok: true,
        target,
        ignoredCount: plan.unsupportedTargets.length
      };
    }

    function updateSummary() {
      if (isFullMode()) {
        if (summaryTarget) {
          summaryTarget.textContent = `Profile > Full profile (${currentProfileId})`;
        }
        if (summaryGroups) {
          summaryGroups.textContent = FULL_PROFILE_GROUPS.join(" | ");
        }
        if (summarySize) {
          summarySize.textContent = "large";
        }
        if (summaryOutput) {
          summaryOutput.textContent = "file";
        }
        if (generateButton) {
          generateButton.disabled = false;
        }
        if (copyButton) {
          copyButton.disabled = !exportCodeInput || !String(exportCodeInput.value || "").trim();
        }
        setExportHint("Ready to generate full profile export.");
        return;
      }
      const plan = resolveSelectionPlan();
      const sizeCategory = estimateSize(plan);
      const outputRecommendation = recommendOutput(plan, sizeCategory);
      if (summaryTarget) {
        summaryTarget.textContent = buildPathSummary(plan);
      }
      if (summaryGroups) {
        summaryGroups.textContent = buildIncludesSummary(plan);
      }
      if (summarySize) {
        summarySize.textContent = sizeCategory;
      }
      if (summaryOutput) {
        summaryOutput.textContent = outputRecommendation;
      }
      const resolution = resolveGenerateSelection(plan);
      if (generateButton) {
        generateButton.disabled = resolution.ok !== true;
      }
      if (copyButton) {
        copyButton.disabled = !exportCodeInput || !String(exportCodeInput.value || "").trim();
      }
      if (resolution.ok === true) {
        if (resolution.ignoredCount > 0) {
          setExportHint(`Ready. ${resolution.ignoredCount} coming-soon selection(s) will be ignored.`);
        } else {
          setExportHint("Ready to generate.");
        }
      } else {
        setExportHint(resolution.message);
      }
    }

    function isModalOpen(backdrop) {
      return Boolean(backdrop) && !backdrop.classList.contains("hidden");
    }

    function syncBodyModalState() {
      const hasOpen = isModalOpen(exportBackdrop) || isModalOpen(importBackdrop);
      document.body.classList.toggle("modal-open", hasOpen);
    }

    function openModal(kind) {
      if (kind === "export" && exportBackdrop) {
        exportBackdrop.classList.remove("hidden");
        exportBackdrop.setAttribute("aria-hidden", "false");
        if (exportModal) {
          exportModal.focus();
        }
      }
      if (kind === "import" && importBackdrop) {
        importBackdrop.classList.remove("hidden");
        importBackdrop.setAttribute("aria-hidden", "false");
        if (importModal) {
          importModal.focus();
        }
      }
      syncBodyModalState();
    }

    function closeModal(kind) {
      if (kind === "export" && exportBackdrop) {
        exportBackdrop.classList.add("hidden");
        exportBackdrop.setAttribute("aria-hidden", "true");
      }
      if (kind === "import" && importBackdrop) {
        importBackdrop.classList.add("hidden");
        importBackdrop.setAttribute("aria-hidden", "true");
      }
      syncBodyModalState();
    }

    function closeAllModals() {
      closeModal("export");
      closeModal("import");
    }

    async function generateShareCode() {
      if (!rulesShareController || typeof rulesShareController.generateShareCodeWithOptions !== "function") {
        return;
      }
      const useCjk = exportCodeCjk ? exportCodeCjk.checked === true : true;
      try {
        let code = "";
        let ignoredCount = 0;
        if (isFullMode()) {
          code = await rulesShareController.generateShareCodeWithOptions({
            scope: "profile",
            useCjk,
            profileId: currentProfileId
          });
        } else {
          const resolution = resolveGenerateSelection();
          if (resolution.ok !== true) {
            setExportStatus(resolution.message || "Cannot generate with current selection.", colors.ERROR);
            return;
          }
          const target = resolution.target;
          ignoredCount = resolution.ignoredCount;
          if (target.kind === "ruleset_item") {
            code = await rulesShareController.generateShareCodeWithOptions({
              scope: "ruleset",
              useCjk,
              profileId: currentProfileId,
              helperManager,
              rulesetPath: target.rulesetPath,
              rulesetName: target.rulesetName || target.label
            });
          } else {
            code = await rulesShareController.generateShareCodeWithOptions({
              scope: target.scope,
              useCjk,
              profileId: currentProfileId
            });
          }
        }
        if (exportCodeInput) {
          exportCodeInput.value = code;
        }
        updateSummary();
        let message = translate("status_generated_code", String(code.length), `Code generated (${code.length} chars).`);
        if (ignoredCount > 0) {
          message += ` Ignored ${ignoredCount} coming-soon selection(s).`;
        }
        setExportStatus(message, colors.SUCCESS);
      } catch (err) {
        const message = err && err.message ? err.message : "Failed to generate code.";
        setExportStatus(message, colors.ERROR);
      }
    }

    async function importShareCode() {
      if (!rulesShareController || typeof rulesShareController.importShareCodeWithOptions !== "function") {
        return;
      }
      const code = importCodeInput ? String(importCodeInput.value || "").trim() : "";
      if (!code) {
        setImportStatus("Paste a share code first.", colors.ERROR);
        return;
      }
      try {
        const result = await rulesShareController.importShareCodeWithOptions({
          code,
          useCjk: importCodeCjk ? importCodeCjk.checked === true : true,
          profileId: currentProfileId,
          helperManager
        });
        if (result && result.scope === "ruleset") {
          await syncForProfile({ profileId: currentProfileId });
          const name = result.ruleset && result.ruleset.name ? result.ruleset.name : "ruleset";
          setImportStatus(`Imported ${name} and enabled it for this profile.`, colors.SUCCESS);
          return;
        }
        if (result && (result.scope === "srs" || result.scope === "profile")) {
          setImportStatus("Import applied. Reloading options…", colors.SUCCESS);
          setTimeout(() => {
            window.location.reload();
          }, 120);
          return;
        }
        setImportStatus("Code imported.", colors.SUCCESS);
      } catch (err) {
        const message = err && err.message ? err.message : "Invalid code.";
        setImportStatus(message, colors.ERROR);
      }
    }

    function copyShareCode() {
      if (!exportCodeInput) {
        return;
      }
      const value = String(exportCodeInput.value || "").trim();
      if (!value) {
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(() => {
          setExportStatus(translate("status_copied", null, "Copied."), colors.SUCCESS);
          updateSummary();
        });
        return;
      }
      exportCodeInput.select();
      document.execCommand("copy");
      setExportStatus(translate("status_copied", null, "Copied."), colors.SUCCESS);
      updateSummary();
    }

    function bindParentEvents() {
      Object.entries(parentInputs).forEach(([parentId, input]) => {
        if (!input) {
          return;
        }
        input.addEventListener("change", () => {
          applyParentToggle(parentId, input.checked === true);
          updateAllParentStates();
          updateSummary();
        });
      });
    }

    function bindStaticLeafEvents() {
      Object.entries(staticLeafInputs).forEach(([leafId, input]) => {
        if (!input) {
          return;
        }
        const entry = {
          id: leafId,
          kind: "static",
          input,
          meta: STATIC_TARGETS[leafId]
        };
        input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
      });
    }

    function bindModeEvents() {
      if (exportModeFullInput) {
        exportModeFullInput.addEventListener("change", () => {
          if (exportModeFullInput.checked === true) {
            setExportMode("full");
          }
        });
      }
      if (exportModeCustomInput) {
        exportModeCustomInput.addEventListener("change", () => {
          if (exportModeCustomInput.checked === true) {
            setExportMode("custom");
          }
        });
      }
    }

    function bindModalEvents() {
      if (openExportButton) {
        openExportButton.addEventListener("click", () => {
          updateSummary();
          openModal("export");
        });
      }
      if (openImportButton) {
        openImportButton.addEventListener("click", () => {
          setOutputStatus(importStatusOutput, "", colors.DEFAULT);
          openModal("import");
        });
      }
      if (exportCloseButton) {
        exportCloseButton.addEventListener("click", () => {
          closeModal("export");
        });
      }
      if (importCloseButton) {
        importCloseButton.addEventListener("click", () => {
          closeModal("import");
        });
      }
      if (exportBackdrop) {
        exportBackdrop.addEventListener("click", (event) => {
          if (event.target === exportBackdrop) {
            closeModal("export");
          }
        });
      }
      if (importBackdrop) {
        importBackdrop.addEventListener("click", (event) => {
          if (event.target === importBackdrop) {
            closeModal("import");
          }
        });
      }
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          closeAllModals();
        }
      });
    }

    function bindActionEvents() {
      if (exportCodeInput) {
        exportCodeInput.addEventListener("input", () => {
          updateSummary();
        });
      }
      if (generateButton) {
        generateButton.addEventListener("click", () => {
          generateShareCode().catch((error) => {
            const message = error && error.message ? error.message : "Failed to generate code.";
            setExportStatus(message, colors.ERROR);
            log("Share center generate failed.", error);
          });
        });
      }
      if (copyButton) {
        copyButton.addEventListener("click", () => {
          copyShareCode();
        });
      }
      if (importButton) {
        importButton.addEventListener("click", () => {
          importShareCode().catch((error) => {
            const message = error && error.message ? error.message : "Failed to import code.";
            setImportStatus(message, colors.ERROR);
            log("Share center import failed.", error);
          });
        });
      }
      if (importClearButton) {
        importClearButton.addEventListener("click", () => {
          if (importCodeInput) {
            importCodeInput.value = "";
          }
          setOutputStatus(importStatusOutput, "", colors.DEFAULT);
        });
      }
    }

    function bindEvents() {
      bindModalEvents();
      bindModeEvents();
      bindParentEvents();
      bindStaticLeafEvents();
      bindActionEvents();
    }

    async function syncForProfile(optionsArg) {
      if (!settingsManager) {
        return null;
      }
      const options = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const items = isObject(options.items) ? options.items : await settingsManager.load();
      const profileId = normalizeProfileId(
        options.profileId !== undefined
          ? options.profileId
          : (settingsManager.getSelectedSrsProfileId
            ? settingsManager.getSelectedSrsProfileId(items)
            : "default")
      );
      const profilesRoot = isObject(items.srsProfiles) ? items.srsProfiles : {};
      const profileEntry = isObject(profilesRoot[profileId]) ? profilesRoot[profileId] : {};
      const manualStateRoot = isObject(profileEntry.manualRulesets) ? profileEntry.manualRulesets : {};
      const manualState = {
        order: Array.isArray(manualStateRoot.order)
          ? manualStateRoot.order
          : [],
        enabledByPath: isObject(manualStateRoot.enabledByPath)
          ? manualStateRoot.enabledByPath
          : {}
      };
      const cacheRaw = isObject(items.manualRulesetCacheByPath) ? items.manualRulesetCacheByPath : {};
      const cache = {};
      Object.entries(cacheRaw).forEach(([cachePath, cacheEntry]) => {
        const key = normalizePath(cachePath);
        if (!key || !isObject(cacheEntry)) {
          return;
        }
        cache[key] = {
          rules: Array.isArray(cacheEntry.rules) ? cacheEntry.rules : [],
          rulesCount: Number.isFinite(Number(cacheEntry.rulesCount))
            ? Number(cacheEntry.rulesCount)
            : (Array.isArray(cacheEntry.rules) ? cacheEntry.rules.length : 0),
          displayPath: normalizePath(cacheEntry.displayPath) || key
        };
      });

      currentProfileId = profileId;
      renderRulesetItems(profileId, manualState, cache);
      renderModuleItems(items, profileId);
      applyExportModeUI();
      updateAllParentStates();
      updateSummary();
      return {
        profileId,
        rulesetLeafIds: [...dynamicRulesetIds],
        moduleLeafIds: [...dynamicModuleIds]
      };
    }

    bindEvents();
    if (targetSrsPairInput) {
      targetSrsPairInput.disabled = true;
    }
    if (targetAppearanceThemeInput) {
      targetAppearanceThemeInput.disabled = true;
    }
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
      importShareCode,
      copyShareCode
    };
  }

  root.optionsShareCenter = {
    createController
  };
})();
