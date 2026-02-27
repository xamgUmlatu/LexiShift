(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resolveSelectionPlan(selectedEntries) {
    const entries = Array.isArray(selectedEntries) ? selectedEntries : [];
    const selectedTargets = entries.map((entry) => entry && entry.meta).filter(Boolean);
    const supportedTargets = selectedTargets.filter((target) => target.enabled !== false && Boolean(target.scope));
    const unsupportedTargets = selectedTargets.filter((target) => target.enabled === false || !target.scope);
    return {
      selectedTargets,
      supportedTargets,
      unsupportedTargets
    };
  }

  function recommendOutput(translate) {
    return translate("share_center_output_json_file", "JSON file");
  }

  function buildPathSummary(plan, currentProfileId, translate) {
    const selectedTargets = Array.isArray(plan && plan.selectedTargets) ? plan.selectedTargets : [];
    const profileId = String(currentProfileId || "").trim() || "default";
    if (!selectedTargets.length) {
      return translate("share_center_path_none", `None (${profileId})`, [profileId]);
    }
    if (selectedTargets.length === 1) {
      const only = selectedTargets[0];
      const label = String(only.path || only.label || translate("share_center_summary_selection", "Selection")).trim();
      return translate("share_center_path_single_with_profile", `${label} (${profileId})`, [label, profileId]);
    }
    return translate(
      "share_center_path_selected_nodes",
      `${selectedTargets.length} selected nodes (${profileId})`,
      [String(selectedTargets.length), profileId]
    );
  }

  function buildIncludesSummary(plan, translate) {
    const selectedTargets = Array.isArray(plan && plan.selectedTargets) ? plan.selectedTargets : [];
    if (!selectedTargets.length) {
      return translate("share_center_includes_nothing_selected", "Nothing selected.");
    }
    const counters = {
      profileSettings: 0,
      rulesets: 0,
      srsPairs: 0,
      appearance: 0,
      modules: 0
    };
    selectedTargets.forEach((target) => {
      if (!target || !target.kind) {
        return;
      }
      if (target.kind === "profile_settings") {
        counters.profileSettings += 1;
        return;
      }
      if (target.kind === "ruleset_item") {
        counters.rulesets += 1;
        return;
      }
      if (target.kind === "srs_pair_item") {
        counters.srsPairs += 1;
        return;
      }
      if (target.kind === "appearance_theme") {
        counters.appearance += 1;
        return;
      }
      if (target.kind === "module_item") {
        counters.modules += 1;
      }
    });
    const parts = [];
    if (counters.profileSettings > 0) {
      parts.push(translate("share_center_includes_profile_settings", "Profile settings"));
    }
    if (counters.rulesets > 0) {
      parts.push(translate("share_center_includes_rulesets", `Rulesets (${counters.rulesets})`, [String(counters.rulesets)]));
    }
    if (counters.srsPairs > 0) {
      parts.push(translate("share_center_includes_srs_pairs", `SRS pairs (${counters.srsPairs})`, [String(counters.srsPairs)]));
    }
    if (counters.appearance > 0) {
      parts.push(translate("share_center_includes_appearance", "Appearance"));
    }
    if (counters.modules > 0) {
      parts.push(translate("share_center_includes_modules", `Modules (${counters.modules})`, [String(counters.modules)]));
    }
    return parts.length ? parts.join(" | ") : translate("share_center_includes_selected_nodes", "Selected nodes");
  }

  function resolveGenerateSelection(options) {
    const opts = options && typeof options === "object" ? options : {};
    const plan = opts.plan && typeof opts.plan === "object"
      ? opts.plan
      : resolveSelectionPlan([]);
    const translate = typeof opts.tr === "function"
      ? opts.tr
      : ((key, fallback) => String(fallback || key || ""));
    const normalizePath = typeof opts.normalizePath === "function"
      ? opts.normalizePath
      : ((value) => String(value || "").trim());
    if (!plan.selectedTargets.length) {
      return {
        ok: false,
        message: translate("share_center_error_select_nodes", "Select one or more nodes.")
      };
    }
    if (!plan.supportedTargets.length) {
      return {
        ok: false,
        message: translate("share_center_error_nodes_not_exportable", "Selected nodes are not exportable yet.")
      };
    }
    const invalidRuleset = plan.supportedTargets.find((target) => (
      target.kind === "ruleset_item" && !normalizePath(target.rulesetPath)
    ));
    if (invalidRuleset) {
      return {
        ok: false,
        message: translate("share_center_error_choose_ruleset_entry", "Choose a ruleset entry before generating.")
      };
    }
    const invalidModule = plan.supportedTargets.find((target) => (
      target.kind === "module_item" && !String(target.moduleId || "").trim()
    ));
    if (invalidModule) {
      return {
        ok: false,
        message: translate("share_center_error_choose_module_entry", "Choose a valid module entry before generating.")
      };
    }
    const invalidSrsPair = plan.supportedTargets.find((target) => (
      target.kind === "srs_pair_item" && !String(target.srsPair || "").trim()
    ));
    if (invalidSrsPair) {
      return {
        ok: false,
        message: translate("share_center_error_choose_srs_pair_entry", "Choose a valid SRS pair entry before generating.")
      };
    }
    return {
      ok: true,
      supportedTargets: plan.supportedTargets,
      ignoredCount: plan.unsupportedTargets.length
    };
  }

  root.optionsShareCenterSelection = {
    resolveSelectionPlan,
    recommendOutput,
    buildPathSummary,
    buildIncludesSummary,
    resolveGenerateSelection
  };
})();
