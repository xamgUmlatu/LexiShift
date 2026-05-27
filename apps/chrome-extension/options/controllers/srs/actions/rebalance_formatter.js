(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function buildRebalanceSection(title, entries) {
    const rows = Array.isArray(entries) ? entries : [];
    if (!rows.length) {
      return [];
    }
    const lines = [title];
    rows.slice(0, 12).forEach((entry) => {
      const lemma = entry && entry.lemma ? String(entry.lemma) : "(unknown)";
      const parts = [];
      if (entry && entry.current_state) {
        parts.push(String(entry.current_state));
      }
      if (entry && entry.source_kind) {
        parts.push(`source=${String(entry.source_kind)}`);
      }
      if (entry && entry.protection_rule) {
        parts.push(`rule=${String(entry.protection_rule)}`);
      }
      if (entry && Number.isFinite(Number(entry.profile_score))) {
        parts.push(`score=${Number(entry.profile_score).toFixed(3)}`);
      }
      lines.push(parts.length ? `- ${lemma} [${parts.join(", ")}]` : `- ${lemma}`);
      const explanation = entry && entry.explanation ? String(entry.explanation).trim() : "";
      if (explanation) {
        lines.push(`  ${explanation}`);
      }
    });
    if (rows.length > 12) {
      lines.push(`- ... ${rows.length - 12} more`);
    }
    lines.push("");
    return lines;
  }

  function buildRebalanceResultOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const srsPair = String(opts.srsPair || "en-en");
    const profileId = String(opts.profileId || "default");
    const payload = opts.payload && typeof opts.payload === "object" ? opts.payload : {};
    const mode = String(opts.mode || "preview");
    const applied = payload.applied === true;
    const plan = payload.plan && typeof payload.plan === "object" ? payload.plan : {};
    const summary = payload.summary && typeof payload.summary === "object" ? payload.summary : {};
    const diagnostics = payload.diagnostics && typeof payload.diagnostics === "object"
      ? payload.diagnostics
      : {};
    const inventory = payload.inventory && typeof payload.inventory === "object"
      ? payload.inventory
      : {};
    const rulegen = payload.rulegen && typeof payload.rulegen === "object"
      ? payload.rulegen
      : null;
    const protectedItems = Array.isArray(payload.protected_items) ? payload.protected_items : [];
    const swappableItems = Array.isArray(payload.swappable_items) ? payload.swappable_items : [];
    const proposedParks = Array.isArray(payload.proposed_parks) ? payload.proposed_parks : [];
    const proposedActivations = Array.isArray(payload.proposed_activations) ? payload.proposed_activations : [];
    const keepCount = Number(summary.proposed_keep_count || 0);
    const parkCount = Number(summary.proposed_park_count || 0);
    const activateCount = Number(summary.proposed_activate_count || 0);
    const header = mode === "apply"
      ? (applied
          ? translate(
              "status_srs_rebalance_apply_result",
              [srsPair, keepCount, parkCount, activateCount],
              `Preference retune applied for ${srsPair}: kept ${keepCount}, paused ${parkCount}, added ${activateCount}.`
            )
          : translate(
              "status_srs_rebalance_noop",
              [srsPair],
              `Preference retune for ${srsPair} did not need active-word changes.`
            ))
      : translate(
          "status_srs_rebalance_preview_header",
          [srsPair, keepCount, parkCount, activateCount],
          `Preference retune preview for ${srsPair}: keep ${keepCount}, pause ${parkCount}, add ${activateCount}.`
        );
    const lines = [
      header,
      `- profile_id: ${profileId}`,
      `- strategy_requested: ${plan.strategy_requested || "n/a"}`,
      `- strategy_effective: ${plan.strategy_effective || "n/a"}`,
      `- objective: ${plan.objective || "n/a"}`,
      `- execution_mode: ${plan.execution_mode || "n/a"}`,
      `- can_execute: ${plan.can_execute === true}`,
      `- inventory_source: ${payload.inventory_source || diagnostics.inventory_source || inventory.source || "n/a"}`,
      `- active_count_before: ${summary.active_count_before ?? "n/a"}`,
      `- protected_count: ${summary.protected_count ?? "n/a"}`,
      `- swappable_count: ${summary.swappable_count ?? "n/a"}`,
      `- candidate_slots_available: ${summary.candidate_slots_available ?? "n/a"}`,
      `- proposed_keep_count: ${summary.proposed_keep_count ?? "n/a"}`,
      `- proposed_park_count: ${summary.proposed_park_count ?? "n/a"}`,
      `- proposed_activate_count: ${summary.proposed_activate_count ?? "n/a"}`,
      `- active_count_after: ${summary.active_count_after ?? "n/a"}`
    ];
    if (mode === "apply") {
      lines.push(`- applied: ${applied}`);
      lines.push(`- inserted_items: ${payload.inserted_items ?? 0}`);
      lines.push(`- inventory_updated_at: ${inventory.updated_at || "n/a"}`);
      if (rulegen) {
        lines.push(`- rulegen_published: ${rulegen.published !== false}`);
        lines.push(`- rulegen_targets: ${rulegen.targets ?? "n/a"}`);
        lines.push(`- rulegen_rules: ${rulegen.rules ?? "n/a"}`);
      }
    }
    const noteLines = Array.isArray(plan.notes) ? plan.notes.map((note) => `- ${note}`) : [];
    const sectionLines = [];
    sectionLines.push(...buildRebalanceSection("Kept words:", protectedItems));
    sectionLines.push(...buildRebalanceSection("Words that can move:", swappableItems));
    sectionLines.push(...buildRebalanceSection("Would pause:", proposedParks));
    sectionLines.push(...buildRebalanceSection("Would add:", proposedActivations));
    if (noteLines.length) {
      sectionLines.push("Plan notes:");
      sectionLines.push(...noteLines);
    }
    if (sectionLines.length) {
      lines.push("");
      lines.push(...sectionLines);
    }
    return lines.join("\n");
  }

  root.optionsSrsRebalanceFormatter = {
    buildRebalanceResultOutput
  };
})();
