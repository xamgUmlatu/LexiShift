(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function formatLimitedList(values, limit = 10) {
    const items = Array.isArray(values)
      ? values.map((value) => String(value || "").trim()).filter((value) => value)
      : [];
    if (!items.length) {
      return "none";
    }
    const maxItems = Math.max(1, Number.parseInt(limit, 10) || 10);
    const visible = items.slice(0, maxItems);
    const suffix = items.length > visible.length
      ? `, +${items.length - visible.length} more`
      : "";
    return `${visible.join(", ")}${suffix}`;
  }

  function resolveBrowsingSimulation(preview, key) {
    const simulations = preview && preview.simulations && typeof preview.simulations === "object"
      ? preview.simulations
      : {};
    return simulations[key] && typeof simulations[key] === "object" ? simulations[key] : null;
  }

  function buildRefreshResultOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
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
    const selectedLemmas = Array.isArray(admission.selected_lemmas)
      ? admission.selected_lemmas
      : [];
    const browsingPreview = result.browsing_admission_preview
      && typeof result.browsing_admission_preview === "object"
      ? result.browsing_admission_preview
      : null;
    const selectedPreferredTopic = admission.selected_preferred_topic
      && typeof admission.selected_preferred_topic === "object"
      ? admission.selected_preferred_topic
      : null;
    const browsingBalanced = resolveBrowsingSimulation(browsingPreview, "balanced");
    const browsingStrong = resolveBrowsingSimulation(browsingPreview, "strong");
    const activeUnseen = admission.active_zero_exposure_zero_feedback;
    const staleUnseen = admission.active_stale_zero_exposure_zero_feedback;
    const staleDays = admission.stale_active_age_days;
    const header = applied
      ? translate(
          "status_srs_refresh_success",
          [srsPair, added],
          `Learning words refreshed for ${srsPair}: +${added} new words.`
        )
      : translate(
          "status_srs_refresh_noop",
          [srsPair],
          `Learning words refreshed for ${srsPair}: no new words added.`
        );
    return [
      header,
      `- applied: ${applied}`,
      `- added_items: ${added}`,
      `- total_items_for_pair: ${result.total_items_for_pair ?? "n/a"}`,
      `- max_active_items: ${result.max_active_items ?? "n/a"}`,
      `- max_new_items_per_day: ${result.max_new_items_per_day ?? "n/a"}`,
      `- active_count: ${admission.active_count ?? "n/a"}`,
      activeUnseen !== undefined ? `- active_unseen_no_feedback: ${activeUnseen}` : null,
      staleUnseen !== undefined
        ? `- active_stale_unseen_no_feedback: ${staleUnseen}${staleDays !== undefined ? ` >${staleDays}d` : ""}`
        : null,
      `- due_count: ${admission.due_count ?? "n/a"}`,
      `- due_pressure: ${admission.due_pressure ?? "n/a"}`,
      `- capacity_budget: ${admission.capacity_budget ?? "n/a"}`,
      `- base_admission_budget: ${admission.base_admission_budget ?? "n/a"}`,
      `- admission_budget: ${admission.admission_budget ?? "n/a"}`,
      `- reason_code: ${admission.reason_code || "n/a"}`,
      `- feedback_count: ${feedbackWindow.feedback_count ?? "n/a"}`,
      `- retention_ratio: ${feedbackWindow.retention_ratio ?? "n/a"}`,
      selectedPreferredTopic
        ? `- selected_preferred_topic_share: ${selectedPreferredTopic.share ?? "n/a"} (${selectedPreferredTopic.preferred_count ?? 0}/${selectedPreferredTopic.selected_count ?? 0})`
        : null,
      selectedLemmas.length ? `- selected_lemmas: ${formatLimitedList(selectedLemmas, 12)}` : null,
      `- rulegen_published: ${publishedRulegen ? publishedRulegen.published !== false : false}`,
      publishedRulegen ? `- rulegen_targets: ${publishedRulegen.targets ?? "n/a"}` : null,
      publishedRulegen ? `- rulegen_rules: ${publishedRulegen.rules ?? "n/a"}` : null,
      publishedRulegen ? `- ruleset_path: ${publishedRulegen.ruleset_path || "n/a"}` : null,
      browsingPreview ? `- browsing_preview_status: ${browsingPreview.status || "n/a"}` : null,
      browsingPreview
        ? `- browsing_signal_matches: ${browsingPreview.matching_signal_count ?? 0} / ${browsingPreview.aggregate_item_count ?? 0}`
        : null,
      browsingPreview && Array.isArray(browsingPreview.neutral_selected_lemmas)
        ? `- browsing_neutral_selected: ${formatLimitedList(browsingPreview.neutral_selected_lemmas, 12)}`
        : null,
      browsingBalanced && Array.isArray(browsingBalanced.selected_lemmas)
        ? `- browsing_balanced_selected: ${formatLimitedList(browsingBalanced.selected_lemmas, 12)}`
        : null,
      browsingStrong && Array.isArray(browsingStrong.selected_lemmas)
        ? `- browsing_strong_selected: ${formatLimitedList(browsingStrong.selected_lemmas, 12)}`
        : null
    ].filter(Boolean).join("\n");
  }

  root.optionsSrsRefreshResultFormatter = {
    buildRefreshResultOutput
  };
})();
