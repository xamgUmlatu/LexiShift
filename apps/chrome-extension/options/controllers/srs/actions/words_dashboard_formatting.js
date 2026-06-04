(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizePageSize(value) {
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
      return 25;
    }
    return Math.max(1, Math.min(300, parsed));
  }

  function clampPageIndex(value, pageCount) {
    const parsed = Number.parseInt(value, 10);
    const maxPageIndex = Math.max(0, Number(pageCount || 1) - 1);
    if (!Number.isFinite(parsed)) {
      return 0;
    }
    return Math.max(0, Math.min(maxPageIndex, parsed));
  }

  function formatSource(value) {
    const normalized = String(value || "").trim();
    return normalized ? normalized.replaceAll("_", " ") : "unknown";
  }

  function formatRefreshTime(data) {
    const rawValue = data && (data.dashboard_refreshed_at || data.refreshed_at);
    const date = rawValue ? new Date(rawValue) : new Date();
    return Number.isNaN(date.getTime()) ? "unknown" : date.toLocaleTimeString();
  }

  function formatWordCount(count) {
    const normalized = Number.isFinite(count) ? count : 0;
    return `${normalized} ${normalized === 1 ? "word" : "words"}`;
  }

  function formatRulesetState(data, ruleSummary) {
    if (ruleSummary.load_error) {
      return "Ruleset: warning";
    }
    const count = Number(ruleSummary.enabled_rule_count || ruleSummary.rule_count || 0);
    if (Number.isFinite(count) && count > 0) {
      return `Ruleset: ${count} rules`;
    }
    return data && data.ruleset_exists ? "Ruleset: empty" : "Ruleset: none";
  }

  function formatEncounterWatchSummary(summary) {
    const unseen = Number(summary.active_zero_exposure_zero_feedback || 0);
    const staleUnseen = Number(summary.active_stale_zero_exposure_zero_feedback || 0);
    const ageUnknown = Number(summary.active_zero_exposure_zero_feedback_age_unknown || 0);
    const withoutRules = Number(summary.active_without_enabled_rules || 0);
    const watch = Number(summary.encounter_watch || Math.max(unseen, withoutRules) || 0);
    const staleDays = Number(summary.encounter_stale_age_days || 7);
    if (!Number.isFinite(watch) || watch <= 0) {
      return "Encounter watch: none";
    }
    const details = [
      unseen > 0 ? `${unseen} unseen/no feedback` : "",
      staleUnseen > 0 ? `${staleUnseen} over ${staleDays}d` : "",
      ageUnknown > 0 ? `${ageUnknown} age unknown` : "",
      withoutRules > 0 ? `${withoutRules} without rules` : ""
    ].filter(Boolean).join(", ");
    return `Encounter watch: ${formatWordCount(watch)}${details ? ` (${details})` : ""}`;
  }

  function formatEncounterWatchItem(item) {
    const state = item && typeof item.encounter_state === "object" ? item.encounter_state : {};
    return state.stale_zero_exposure_zero_feedback
      ? `Watch: unseen/no feedback >${Number(state.stale_age_days || 7)}d`
      : state.zero_exposure_zero_feedback_age_unknown
        ? "Watch: unseen/no feedback (age unknown)"
        : state.zero_exposure_zero_feedback
          ? "Watch: unseen/no feedback"
          : (state.without_enabled_rules ? "Watch: no enabled rules" : "");
  }

  function formatDue(item) {
    const status = String(item.status || "");
    if (status === "queued") {
      return "Upcoming";
    }
    if (status === "discarded" || status === "cleared" || status === "removed") {
      return item.status_label || "Removed";
    }
    const dueSeconds = Number(item.due_in_seconds);
    if (!Number.isFinite(dueSeconds)) {
      return "No due date";
    }
    if (dueSeconds <= 0) {
      return "Due now";
    }
    if (dueSeconds < 3600) {
      return `Due in ${Math.max(1, Math.round(dueSeconds / 60))}m`;
    }
    if (dueSeconds < 86400) {
      return `Due in ${Math.round(dueSeconds / 3600)}h`;
    }
    return `Due ${formatDate(item.next_due)}`;
  }

  function formatRuleCount(item) {
    const summary = item && typeof item.rule_summary === "object" ? item.rule_summary : {};
    const count = Number(summary.enabled_rule_count || 0);
    return `Rules: ${Number.isFinite(count) ? count : 0}`;
  }

  function formatServingLabel(item) {
    const label = String(item && item.serving_label || "").trim();
    if (label === "Now") {
      return "Can appear";
    }
    if (label === "Not due") {
      return "Waiting until due";
    }
    if (label === "No rules") {
      return "No replacement rules";
    }
    if (label === "Queued") {
      return "Upcoming";
    }
    if (label) {
      return label;
    }
    return item && item.serving ? "Can appear" : "Not active";
  }

  function isInteractiveTarget(target) {
    if (!target || !target.tagName) {
      return false;
    }
    return ["BUTTON", "A", "INPUT", "SELECT", "TEXTAREA", "SUMMARY"].includes(
      String(target.tagName).toUpperCase()
    );
  }

  function formatDate(value) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
  }

  root.optionsSrsWordsDashboardFormatting = {
    clampPageIndex,
    formatDue,
    formatEncounterWatchItem,
    formatEncounterWatchSummary,
    formatRefreshTime,
    formatRuleCount,
    formatRulesetState,
    formatServingLabel,
    formatSource,
    formatWordCount,
    isInteractiveTarget,
    normalizePageSize
  };
})();
