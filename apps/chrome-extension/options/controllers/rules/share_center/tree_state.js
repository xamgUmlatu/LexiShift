(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createHelpers(options) {
    const opts = options && typeof options === "object" ? options : {};
    const staticTargets = opts.staticTargets && typeof opts.staticTargets === "object" ? opts.staticTargets : {};
    const staticLeafInputs = opts.staticLeafInputs && typeof opts.staticLeafInputs === "object" ? opts.staticLeafInputs : {};
    const dynamicLeafState = opts.dynamicLeafState instanceof Map ? opts.dynamicLeafState : new Map();
    const parentInputs = opts.parentInputs && typeof opts.parentInputs === "object" ? opts.parentInputs : {};
    const getDynamicSrsPairIds = typeof opts.getDynamicSrsPairIds === "function" ? opts.getDynamicSrsPairIds : (() => []);
    const getDynamicRulesetIds = typeof opts.getDynamicRulesetIds === "function" ? opts.getDynamicRulesetIds : (() => []);
    const getDynamicModuleIds = typeof opts.getDynamicModuleIds === "function" ? opts.getDynamicModuleIds : (() => []);
    const isFullMode = typeof opts.isFullMode === "function" ? opts.isFullMode : (() => false);
    const normalizePath = typeof opts.normalizePath === "function"
      ? opts.normalizePath
      : ((value) => String(value || "").trim());
    const setSelectedRulesetPath = typeof opts.setSelectedRulesetPath === "function"
      ? opts.setSelectedRulesetPath
      : (() => {});
    const updateSummary = typeof opts.updateSummary === "function" ? opts.updateSummary : (() => {});

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
      if (Object.prototype.hasOwnProperty.call(staticTargets, leafId)) {
        const input = staticLeafInputs[leafId];
        if (!input) {
          return null;
        }
        return {
          id: leafId,
          kind: "static",
          input,
          meta: staticTargets[leafId]
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
          "appearance_theme",
          ...getDynamicSrsPairIds(),
          ...getDynamicRulesetIds(),
          ...getDynamicModuleIds()
        ];
      }
      if (parentId === "rulesets_group") {
        return [...getDynamicRulesetIds()];
      }
      if (parentId === "srs_group") {
        return [...getDynamicSrsPairIds()];
      }
      if (parentId === "appearance_group") {
        return ["appearance_theme"];
      }
      if (parentId === "modules_group") {
        return [...getDynamicModuleIds()];
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
        setSelectedRulesetPath(normalizePath(entry.meta.rulesetPath));
      }
      updateAllParentStates();
      updateSummary();
    }

    return {
      clearDynamicLeafsByKind,
      getLeafEntryById,
      collectAllLeafEntries,
      getSelectedLeafEntries,
      resolveParentChildIds,
      getSelectableChildEntries,
      updateParentState,
      updateAllParentStates,
      applyParentToggle,
      onLeafChanged
    };
  }

  root.optionsShareCenterTreeState = {
    createHelpers
  };
})();
