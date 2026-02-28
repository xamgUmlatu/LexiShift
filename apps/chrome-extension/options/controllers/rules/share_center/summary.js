(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function updateSummary(context) {
    const ctx = context && typeof context === "object" ? context : {};
    const isFullMode = typeof ctx.isFullMode === "function" ? ctx.isFullMode : (() => true);
    const tr = typeof ctx.tr === "function" ? ctx.tr : ((key, fallback) => String(fallback || key || ""));
    const currentProfileId = String(ctx.currentProfileId || "default");
    const summaryTarget = ctx.summaryTarget || null;
    const summaryGroups = ctx.summaryGroups || null;
    const summaryOutput = ctx.summaryOutput || null;
    const generateButton = ctx.generateButton || null;
    const fullProfileGroups = Array.isArray(ctx.fullProfileGroups) ? ctx.fullProfileGroups : [];
    const setExportHint = typeof ctx.setExportHint === "function" ? ctx.setExportHint : (() => {});
    const shareCenterSelection = ctx.shareCenterSelection && typeof ctx.shareCenterSelection === "object"
      ? ctx.shareCenterSelection
      : null;
    const getSelectedLeafEntries = typeof ctx.getSelectedLeafEntries === "function"
      ? ctx.getSelectedLeafEntries
      : (() => []);
    const normalizePath = typeof ctx.normalizePath === "function"
      ? ctx.normalizePath
      : ((value) => String(value || "").trim());

    if (!shareCenterSelection) {
      return;
    }

    if (isFullMode()) {
      if (summaryTarget) {
        summaryTarget.textContent = tr(
          "share_center_path_full_profile",
          `Full profile (${currentProfileId})`,
          [currentProfileId]
        );
      }
      if (summaryGroups) {
        summaryGroups.textContent = fullProfileGroups.join(" | ");
      }
      if (summaryOutput) {
        summaryOutput.textContent = shareCenterSelection.recommendOutput(tr);
      }
      if (generateButton) {
        generateButton.disabled = false;
      }
      setExportHint(tr("share_center_hint_ready_full_export", "Ready to export full profile as JSON file."));
      return;
    }

    const plan = shareCenterSelection.resolveSelectionPlan(getSelectedLeafEntries());
    const outputRecommendation = shareCenterSelection.recommendOutput(tr);
    if (summaryTarget) {
      summaryTarget.textContent = shareCenterSelection.buildPathSummary(plan, currentProfileId, tr);
    }
    if (summaryGroups) {
      summaryGroups.textContent = shareCenterSelection.buildIncludesSummary(plan, tr);
    }
    if (summaryOutput) {
      summaryOutput.textContent = outputRecommendation;
    }
    const resolution = shareCenterSelection.resolveGenerateSelection({
      plan,
      tr,
      normalizePath
    });
    if (generateButton) {
      generateButton.disabled = resolution.ok !== true;
    }
    if (resolution.ok === true) {
      if (resolution.ignoredCount > 0) {
        setExportHint(
          tr(
            "share_center_hint_ready_with_ignored",
            `Ready. ${resolution.ignoredCount} unsupported selection(s) will be ignored.`,
            [String(resolution.ignoredCount)]
          )
        );
      } else {
        setExportHint(tr("share_center_hint_ready_selection_export", "Ready to export selection as JSON file."));
      }
    } else {
      setExportHint(resolution.message);
    }
  }

  root.optionsShareCenterSummary = {
    updateSummary
  };
})();
