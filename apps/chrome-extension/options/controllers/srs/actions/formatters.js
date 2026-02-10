(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function formatMissingResourceList(missingInputs) {
    const missing = Array.isArray(missingInputs) ? missingInputs : [];
    if (!missing.length) {
      return "none";
    }
    return missing.map((entry) => {
      if (!entry || typeof entry !== "object") {
        return "unknown";
      }
      const resourceType = String(entry.type || "unknown");
      const resourcePath = typeof entry.path === "string" && entry.path
        ? entry.path
        : "(path unresolved)";
      return `${resourceType}: ${resourcePath}`;
    }).join("; ");
  }

  function formatPairPolicySummary(pairPolicy) {
    if (!pairPolicy || typeof pairPolicy !== "object") {
      return "n/a";
    }
    return [
      `bootstrap_top_n_default=${pairPolicy.bootstrap_top_n_default ?? "n/a"}`,
      `refresh_top_n_default=${pairPolicy.refresh_top_n_default ?? "n/a"}`,
      `feedback_window_size_default=${pairPolicy.feedback_window_size_default ?? "n/a"}`,
      `initial_active_count_default=${pairPolicy.initial_active_count_default ?? "n/a"}`
    ].join(", ");
  }

  function buildPreflightBlockedLines(options) {
    const opts = options && typeof options === "object" ? options : {};
    const actionLabel = String(opts.actionLabel || "Action");
    const pair = String(opts.pair || "en-en");
    const profileId = String(opts.profileId || "default");
    const helperData = opts.helperData && typeof opts.helperData === "object" ? opts.helperData : {};
    const requirements = helperData.requirements && typeof helperData.requirements === "object"
      ? helperData.requirements
      : {};
    const pairPolicy = helperData.pair_policy && typeof helperData.pair_policy === "object"
      ? helperData.pair_policy
      : null;
    const missingInputs = Array.isArray(helperData.missing_inputs) ? helperData.missing_inputs : [];
    return [
      `${actionLabel} blocked for ${pair}: required resources are missing.`,
      `profile: ${profileId}`,
      "",
      "LP requirements:",
      `- supports_rulegen: ${requirements.supports_rulegen === true}`,
      `- requires_jmdict_for_seed: ${requirements.requires_jmdict_for_seed === true}`,
      `- requires_jmdict_for_rulegen: ${requirements.requires_jmdict_for_rulegen === true}`,
      `- requires_freedict_de_en_for_rulegen: ${requirements.requires_freedict_de_en_for_rulegen === true}`,
      "",
      "Resolved resources:",
      `- set_source_db: ${helperData.set_source_db || "n/a"} (exists=${helperData.set_source_db_exists === true})`,
      `- jmdict_path: ${helperData.jmdict_path || "n/a"} (exists=${helperData.jmdict_exists === true})`,
      `- freedict_de_en_path: ${helperData.freedict_de_en_path || "n/a"} (exists=${helperData.freedict_de_en_exists === true})`,
      `- stopwords_path: ${helperData.stopwords_path || "n/a"} (exists=${helperData.stopwords_exists === true})`,
      "",
      "Pair policy defaults:",
      `- ${formatPairPolicySummary(pairPolicy)}`,
      "",
      "Missing inputs:",
      ...missingInputs.map((entry) => {
        const resourceType = entry && entry.type ? String(entry.type) : "unknown";
        const resourcePath = entry && entry.path ? String(entry.path) : "(path unresolved)";
        return `- ${resourceType}: ${resourcePath}`;
      })
    ];
  }

  function buildAdmissionWeightSummary(admissionWeightProfile) {
    if (!admissionWeightProfile || typeof admissionWeightProfile !== "object") {
      return "";
    }
    return [
      ["noun", admissionWeightProfile.noun],
      ["adjective", admissionWeightProfile.adjective],
      ["verb", admissionWeightProfile.verb],
      ["adverb", admissionWeightProfile.adverb],
      ["other", admissionWeightProfile.other]
    ]
      .filter((entry) => Number.isFinite(Number(entry[1])))
      .map((entry) => `${entry[0]}=${Number(entry[1]).toFixed(2)}`)
      .join(", ");
  }

  function buildInitialActiveWeightPreviewSummary(initialActiveWeightPreview) {
    const preview = Array.isArray(initialActiveWeightPreview) ? initialActiveWeightPreview : [];
    if (!preview.length) {
      return "";
    }
    return preview.slice(0, 10).map((entry) => {
      const lemma = entry && entry.lemma ? String(entry.lemma) : "";
      const bucket = entry && entry.pos_bucket ? String(entry.pos_bucket) : "other";
      const score = entry && Number.isFinite(Number(entry.admission_weight))
        ? Number(entry.admission_weight).toFixed(3)
        : "n/a";
      return `${lemma}[${bucket}:${score}]`;
    }).join(", ");
  }

  function buildInitializeResultOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const applied = opts.applied === true;
    const added = Number(opts.added || 0);
    const total = Number(opts.total || 0);
    const srsPair = String(opts.srsPair || "en-en");
    const plan = opts.plan && typeof opts.plan === "object" ? opts.plan : {};
    const result = opts.result && typeof opts.result === "object" ? opts.result : {};
    const bootstrapTopN = Number(opts.bootstrapTopN || 0);
    const initialActiveCount = Number(opts.initialActiveCount || 0);
    const maxActiveItemsHint = Number(opts.maxActiveItemsHint || 0);
    const bootstrapDiagnostics = opts.bootstrapDiagnostics && typeof opts.bootstrapDiagnostics === "object"
      ? opts.bootstrapDiagnostics
      : {};
    const publishedRulegen = opts.publishedRulegen && typeof opts.publishedRulegen === "object"
      ? opts.publishedRulegen
      : null;
    const notes = Array.isArray(plan.notes) ? plan.notes : [];
    const noteLines = notes.length ? notes.map((note) => `- ${note}`) : [];
    const initialActivePreview = Array.isArray(bootstrapDiagnostics.initial_active_preview)
      ? bootstrapDiagnostics.initial_active_preview
      : [];
    const initialActiveWeightPreview = Array.isArray(bootstrapDiagnostics.initial_active_weight_preview)
      ? bootstrapDiagnostics.initial_active_weight_preview
      : [];
    const admissionWeightSummary = buildAdmissionWeightSummary(bootstrapDiagnostics.admission_weight_profile);
    const weightPreviewSummary = buildInitialActiveWeightPreviewSummary(initialActiveWeightPreview);
    const header = applied
      ? translate(
          "status_srs_set_init_result",
          [added, total, srsPair],
          `S initialized for ${srsPair}: +${added} items (total ${total}).`
        )
      : translate(
          "status_srs_set_plan_result",
          [srsPair],
          `S planning completed for ${srsPair}.`
        );
    return [
      header,
      `- applied: ${applied}`,
      `- strategy_requested: ${plan.strategy_requested || "n/a"}`,
      `- strategy_effective: ${plan.strategy_effective || "n/a"}`,
      `- bootstrap_top_n: ${result.bootstrap_top_n ?? result.set_top_n ?? bootstrapTopN}`,
      `- initial_active_count: ${result.initial_active_count ?? initialActiveCount}`,
      `- max_active_items_hint: ${result.max_active_items_hint ?? maxActiveItemsHint}`,
      `- source_type: ${result.source_type || "initial_set"}`,
      `- store_path: ${result.store_path || "n/a"}`,
      `- stopwords_path: ${result.stopwords_path || "n/a"}`,
      applied ? `- rulegen_published: ${publishedRulegen ? publishedRulegen.published !== false : false}` : null,
      applied && publishedRulegen ? `- rulegen_targets: ${publishedRulegen.targets ?? "n/a"}` : null,
      applied && publishedRulegen ? `- rulegen_rules: ${publishedRulegen.rules ?? "n/a"}` : null,
      applied && publishedRulegen ? `- ruleset_path: ${publishedRulegen.ruleset_path || "n/a"}` : null,
      applied ? `- selected_count: ${bootstrapDiagnostics.selected_count ?? "n/a"}` : null,
      applied ? `- selected_unique_count: ${bootstrapDiagnostics.selected_unique_count ?? "n/a"}` : null,
      applied ? `- admitted_count: ${bootstrapDiagnostics.admitted_count ?? "n/a"}` : null,
      applied ? `- inserted_count: ${bootstrapDiagnostics.inserted_count ?? "n/a"}` : null,
      applied ? `- updated_count: ${bootstrapDiagnostics.updated_count ?? "n/a"}` : null,
      applied && admissionWeightSummary ? `- admission_weight_profile: ${admissionWeightSummary}` : null,
      applied && initialActivePreview.length
        ? `- initial_active_preview: ${initialActivePreview.slice(0, 20).join(", ")}`
        : null,
      applied && weightPreviewSummary
        ? `- initial_active_weight_preview: ${weightPreviewSummary}`
        : null,
      noteLines.length ? "" : null,
      noteLines.length ? "Plan notes:" : null,
      ...noteLines
    ].filter(Boolean).join("\n");
  }

  function buildRefreshResultOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const applied = opts.applied === true;
    const added = Number(opts.added || 0);
    const srsPair = String(opts.srsPair || "en-en");
    const result = opts.result && typeof opts.result === "object" ? opts.result : {};
    const admission = opts.admission && typeof opts.admission === "object" ? opts.admission : {};
    const feedbackWindow = admission.feedback_window && typeof admission.feedback_window === "object"
      ? admission.feedback_window
      : {};
    const publishedRulegen = opts.publishedRulegen && typeof opts.publishedRulegen === "object"
      ? opts.publishedRulegen
      : null;
    const header = applied
      ? translate(
          "status_srs_refresh_success",
          [srsPair, added],
          `S refreshed for ${srsPair}: +${added} admitted.`
        )
      : translate(
          "status_srs_refresh_noop",
          [srsPair],
          `S refresh for ${srsPair}: no new admissions.`
        );
    return [
      header,
      `- applied: ${applied}`,
      `- added_items: ${added}`,
      `- total_items_for_pair: ${result.total_items_for_pair ?? "n/a"}`,
      `- max_active_items: ${result.max_active_items ?? "n/a"}`,
      `- max_new_items_per_day: ${result.max_new_items_per_day ?? "n/a"}`,
      `- reason_code: ${admission.reason_code || "n/a"}`,
      `- feedback_count: ${feedbackWindow.feedback_count ?? "n/a"}`,
      `- retention_ratio: ${feedbackWindow.retention_ratio ?? "n/a"}`,
      `- rulegen_published: ${publishedRulegen ? publishedRulegen.published !== false : false}`,
      publishedRulegen ? `- rulegen_targets: ${publishedRulegen.targets ?? "n/a"}` : null,
      publishedRulegen ? `- rulegen_rules: ${publishedRulegen.rules ?? "n/a"}` : null,
      publishedRulegen ? `- ruleset_path: ${publishedRulegen.ruleset_path || "n/a"}` : null
    ].filter(Boolean).join("\n");
  }

  function buildRuntimeDiagnosticsOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const srsPair = String(opts.srsPair || "en-en");
    const selectedProfileId = String(opts.selectedProfileId || "default");
    const diagnostics = opts.diagnostics && typeof opts.diagnostics === "object" ? opts.diagnostics : {};
    const helperData = diagnostics.helper && typeof diagnostics.helper === "object"
      ? diagnostics.helper
      : null;
    const pairPolicy = helperData && helperData.pair_policy && typeof helperData.pair_policy === "object"
      ? helperData.pair_policy
      : null;
    const runtimeState = diagnostics.runtime_state && typeof diagnostics.runtime_state === "object"
      ? diagnostics.runtime_state
      : null;
    const cache = diagnostics.cache && typeof diagnostics.cache === "object"
      ? diagnostics.cache
      : {};
    return [
      translate(
        "status_srs_diagnostics_header",
        [srsPair],
        `SRS Runtime Diagnostics (${srsPair})`
      ),
      `profile: ${selectedProfileId}`,
      "",
      "Helper (source of truth):",
      helperData
        ? `- store_items_for_pair: ${helperData.store_items_for_pair ?? "n/a"}`
        : `- unavailable: ${diagnostics.helper_error || "unknown"}`,
      helperData ? `- pair_policy: ${formatPairPolicySummary(pairPolicy)}` : null,
      helperData ? `- set_source_db: ${helperData.set_source_db || "n/a"} (exists=${helperData.set_source_db_exists === true})` : null,
      helperData ? `- jmdict_path: ${helperData.jmdict_path || "n/a"} (exists=${helperData.jmdict_exists === true})` : null,
      helperData ? `- freedict_de_en_path: ${helperData.freedict_de_en_path || "n/a"} (exists=${helperData.freedict_de_en_exists === true})` : null,
      helperData ? `- stopwords_path: ${helperData.stopwords_path || "n/a"} (exists=${helperData.stopwords_exists === true})` : null,
      helperData ? `- missing_inputs: ${formatMissingResourceList(helperData.missing_inputs)}` : null,
      helperData ? `- ruleset_rules_count: ${helperData.ruleset_rules_count ?? "n/a"}` : null,
      helperData ? `- snapshot_target_count: ${helperData.snapshot_target_count ?? "n/a"}` : null,
      helperData ? `- store_path: ${helperData.store_path || "n/a"}` : null,
      helperData ? `- ruleset_path: ${helperData.ruleset_path || "n/a"}` : null,
      "",
      "Extension cache:",
      `- cached_ruleset_rules: ${cache.ruleset_rules_count ?? 0}`,
      `- cached_snapshot_targets: ${cache.snapshot_target_count ?? 0}`,
      "",
      "Current tab/runtime (last reported):",
      runtimeState ? `- ts: ${runtimeState.ts || "n/a"}` : "- ts: n/a",
      runtimeState ? `- pair: ${runtimeState.pair || "n/a"}` : "- pair: n/a",
      runtimeState ? `- profile_id: ${runtimeState.profile_id || "n/a"}` : "- profile_id: n/a",
      runtimeState ? `- srs_enabled: ${runtimeState.srs_enabled === true}` : "- srs_enabled: n/a",
      runtimeState ? `- rules_source: ${runtimeState.rules_source || "n/a"}` : "- rules_source: n/a",
      runtimeState ? `- rules_local_enabled: ${runtimeState.rules_local_enabled ?? "n/a"}` : "- rules_local_enabled: n/a",
      runtimeState ? `- rules_srs_enabled: ${runtimeState.rules_srs_enabled ?? "n/a"}` : "- rules_srs_enabled: n/a",
      runtimeState ? `- active_rules_total: ${runtimeState.active_rules_total ?? "n/a"}` : "- active_rules_total: n/a",
      runtimeState ? `- active_rules_srs: ${runtimeState.active_rules_srs ?? "n/a"}` : "- active_rules_srs: n/a",
      runtimeState ? `- helper_rules_error: ${runtimeState.helper_rules_error || "none"}` : "- helper_rules_error: n/a",
      runtimeState ? `- frame_type: ${runtimeState.frame_type || "n/a"}` : "- frame_type: n/a"
    ].filter(Boolean).join("\n");
  }

  function buildSampledRulegenSamplingLines(options) {
    const opts = options && typeof options === "object" ? options : {};
    const sampling = opts.sampling && typeof opts.sampling === "object" ? opts.sampling : {};
    const sampledLemmas = Array.isArray(opts.sampledLemmas) ? opts.sampledLemmas : [];
    const sampleCount = Number(opts.sampleCount || 0);
    const sampledCount = Number(opts.sampledCount || 0);
    return [
      `- strategy_requested: ${sampling.strategy_requested || "n/a"}`,
      `- strategy_effective: ${sampling.strategy_effective || "n/a"}`,
      `- sample_count_requested: ${sampling.sample_count_requested ?? sampleCount}`,
      `- sample_count_effective: ${sampling.sample_count_effective ?? sampledCount}`,
      `- total_items_for_pair: ${sampling.total_items_for_pair ?? "n/a"}`,
      sampledLemmas.length ? `- sampled_lemmas: ${sampledLemmas.join(", ")}` : null
    ].filter(Boolean);
  }

  function buildSampledRulegenHeader(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const sampledCount = Number(opts.sampledCount || 0);
    const rulegenTargets = Number(opts.rulegenTargets || 0);
    const rulegenRules = Number(opts.rulegenRules || 0);
    const duration = Number(opts.duration || 0);
    return translate(
      "status_srs_rulegen_sampled_result_header",
      [sampledCount, rulegenTargets, rulegenRules, duration],
      `Sampled rulegen: ${sampledCount} words, ${rulegenTargets} targets, ${rulegenRules} rules (${duration}s)`
    );
  }

  function buildSampledRulegenEmptyOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const header = String(opts.header || "");
    const samplingLines = Array.isArray(opts.samplingLines) ? opts.samplingLines : [];
    const diag = opts.diagnostics && typeof opts.diagnostics === "object" ? opts.diagnostics : {};
    const srsPair = String(opts.srsPair || "en-en");
    const diagLines = [
      translate("diag_header", null, "Diagnostics:"),
      `- ${translate("label_pair", null, "pair")}: ${diag.pair || srsPair}`,
      `- jmdict: ${diag.jmdict_path || "n/a"} (exists=${diag.jmdict_exists})`,
      `- freedict_de_en: ${diag.freedict_de_en_path || "n/a"} (exists=${diag.freedict_de_en_exists})`,
      `- set_source_db: ${diag.set_source_db || "n/a"} (exists=${diag.set_source_db_exists})`,
      `- store_items: ${diag.store_items ?? "n/a"}`,
      `- store_items_for_pair: ${diag.store_items_for_pair ?? "n/a"}`,
      `- store_sample: ${(Array.isArray(diag.store_sample) ? diag.store_sample.join(", ") : "n/a")}`
    ];
    return [
      header,
      ...samplingLines,
      "",
      translate("status_srs_rulegen_empty", null, "No rules found for current active words."),
      "",
      ...diagLines
    ].join("\n");
  }

  function buildSampledRulegenTargetsOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : ((_key, _subs, fallback) => fallback || "");
    const header = String(opts.header || "");
    const samplingLines = Array.isArray(opts.samplingLines) ? opts.samplingLines : [];
    const targets = Array.isArray(opts.targets) ? opts.targets : [];
    const sortedTargets = [...targets].sort((a, b) => {
      const lemmaA = String(a.lemma || "");
      const lemmaB = String(b.lemma || "");
      return lemmaA.localeCompare(lemmaB);
    });
    const lines = sortedTargets.map((entry) => {
      const lemma = String(entry.lemma || "").trim();
      const sources = Array.isArray(entry.sources) ? entry.sources : [];
      if (!lemma) {
        return null;
      }
      if (!sources.length) {
        return translate(
          "status_srs_rulegen_line_no_rules",
          [lemma],
          `${lemma} → (no rules)`
        );
      }
      return translate(
        "status_srs_rulegen_line_rules",
        [lemma, sources.join(", ")],
        `${lemma} → ${sources.join(", ")}`
      );
    }).filter(Boolean);
    return [header, ...samplingLines, "", ...lines].join("\n");
  }

  root.optionsSrsActionFormatters = {
    formatMissingResourceList,
    formatPairPolicySummary,
    buildPreflightBlockedLines,
    buildInitializeResultOutput,
    buildRefreshResultOutput,
    buildRuntimeDiagnosticsOutput,
    buildSampledRulegenSamplingLines,
    buildSampledRulegenHeader,
    buildSampledRulegenEmptyOutput,
    buildSampledRulegenTargetsOutput
  };
})();
