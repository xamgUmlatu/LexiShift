(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createWordsDashboardRenderer(options) {
    const opts = options && typeof options === "object" ? options : {};
    const wordsSummaryRoot = opts.wordsSummaryRoot || null;
    const wordsMetaRoot = opts.wordsMetaRoot || null;
    const wordsListRoot = opts.wordsListRoot || null;
    const wordsPaginationRoot = opts.wordsPaginationRoot || null;
    const wordsPageInfoRoot = opts.wordsPageInfoRoot || null;
    const wordsFirstPageButton = opts.wordsFirstPageButton || null;
    const wordsPrevPageButton = opts.wordsPrevPageButton || null;
    const wordsNextPageButton = opts.wordsNextPageButton || null;
    const wordsLastPageButton = opts.wordsLastPageButton || null;
    const dashboardModel = opts.dashboardModel && typeof opts.dashboardModel === "object"
      ? opts.dashboardModel
      : { apply: (items) => items, isAdjusted: () => false };
    const maxRenderedWordRows = Number.parseInt(opts.maxRenderedWordRows, 10) || 300;
    const renderRuleDetailsView = typeof opts.renderRuleDetailsView === "function"
      ? opts.renderRuleDetailsView
      : (() => null);
    const isAdvancedEnabled = typeof opts.isAdvancedEnabled === "function"
      ? opts.isAdvancedEnabled
      : (() => false);
    const canLoadRuleDetails = typeof opts.canLoadRuleDetails === "function"
      ? opts.canLoadRuleDetails
      : (() => false);
    const canDiscardItem = typeof opts.canDiscardItem === "function"
      ? opts.canDiscardItem
      : (() => false);
    const ruleDetailKey = typeof opts.ruleDetailKey === "function"
      ? opts.ruleDetailKey
      : (() => "");
    const toggleRuleDetails = typeof opts.toggleRuleDetails === "function"
      ? opts.toggleRuleDetails
      : (() => {});
    const discardWord = typeof opts.discardWord === "function" ? opts.discardWord : (() => {});
    const getPaginationState = typeof opts.getPaginationState === "function"
      ? opts.getPaginationState
      : (() => ({ pageIndex: 0, pageSize: 25 }));
    const onPaginationRendered = typeof opts.onPaginationRendered === "function"
      ? opts.onPaginationRendered
      : (() => {});

    function render(data) {
      if (!wordsSummaryRoot || !wordsListRoot) {
        return;
      }
      const doc = wordsListRoot.ownerDocument || globalThis.document;
      if (!doc) {
        return;
      }
      clearNode(wordsSummaryRoot);
      clearNode(wordsMetaRoot);
      clearNode(wordsListRoot);
      if (!data) {
        updatePaginationControls({ total: 0, pageIndex: 0, pageSize: 25, pageCount: 1 });
        showListMessage("Refresh words to load the current SRS dashboard.");
        return;
      }
      renderSummary(doc, data.summary && typeof data.summary === "object" ? data.summary : {});
      renderDashboardMeta(doc, data, renderRows(doc, data));
    }

    function showListMessage(message) {
      if (!wordsListRoot) {
        return;
      }
      const doc = wordsListRoot.ownerDocument || globalThis.document;
      if (!doc) {
        return;
      }
      clearNode(wordsListRoot);
      clearNode(wordsMetaRoot);
      wordsListRoot.appendChild(createNode(doc, "p", "srs-words-empty", message));
    }

    function renderSummary(doc, summary) {
      [
        ["Active", summary.active || 0],
        ["Due now", summary.due_now || 0],
        ["Due soon", summary.due_soon || 0],
        ["Queued", summary.queued || 0],
        ["Unseen", summary.active_zero_exposure_zero_feedback || 0],
        ["Removed", summary.removed || 0],
        ["Total", summary.total || 0]
      ].forEach(([label, value]) => {
        wordsSummaryRoot.appendChild(appendSummaryItem(doc, label, value));
      });
    }

    function renderRows(doc, data) {
      const allItems = Array.isArray(data.items) ? data.items : [];
      const items = dashboardModel.apply(allItems);
      if (!items.length) {
        const rawPagination = getPaginationState() || {};
        const emptyPagination = {
          total: 0,
          allTotal: allItems.length,
          filteredTotal: 0,
          pageIndex: 0,
          pageSize: normalizePageSize(rawPagination.pageSize),
          pageCount: 1
        };
        updatePaginationControls(emptyPagination);
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-empty",
          allItems.length
            ? "No SRS words match these filters."
            : "No SRS words are admitted for this pair yet."
        ));
        return emptyPagination;
      }
      const pagination = resolvePagination(items.length);
      pagination.allTotal = allItems.length;
      pagination.filteredTotal = items.length;
      if (dashboardModel.isAdjusted()) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-filter-note",
          `Filtered to ${items.length} of ${allItems.length} words.`
        ));
      }
      updatePaginationControls(pagination);
      items.slice(pagination.startIndex, pagination.endIndex).forEach((item) => {
        wordsListRoot.appendChild(renderWordRow(doc, item));
      });
      if (pagination.pageSize > maxRenderedWordRows) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-truncated",
          `Showing ${maxRenderedWordRows} of ${pagination.pageSize} page rows.`
        ));
      }
      return pagination;
    }

    function renderDashboardMeta(doc, data, pageState) {
      if (!wordsMetaRoot) {
        return;
      }
      clearNode(wordsMetaRoot);
      const summary = data.summary && typeof data.summary === "object" ? data.summary : {};
      const ruleSummary = data.rule_summary && typeof data.rule_summary === "object"
        ? data.rule_summary
        : {};
      const loadedCount = Number(summary.total || pageState.allTotal || 0);
      const viewingCount = Number(pageState.filteredTotal || 0);
      [
        `Last refreshed: ${formatRefreshTime(data)}`,
        `Loaded: ${formatWordCount(loadedCount)}`,
        `Viewing: ${formatWordCount(viewingCount)}`,
        formatEncounterWatchSummary(summary),
        `Inventory: ${formatSource(data.inventory_source || "unknown")}`,
        formatRulesetState(data, ruleSummary)
      ].forEach((text) => {
        wordsMetaRoot.appendChild(createNode(doc, "span", "", text));
      });
    }

    function resolvePagination(total) {
      const rawState = getPaginationState();
      const pageSize = normalizePageSize(rawState && rawState.pageSize);
      const pageCount = Math.max(1, Math.ceil(total / pageSize));
      const pageIndex = clampPageIndex(rawState && rawState.pageIndex, pageCount);
      const startIndex = Math.min(total, pageIndex * pageSize);
      const endIndex = Math.min(total, startIndex + Math.min(pageSize, maxRenderedWordRows));
      return { total, pageIndex, pageSize, pageCount, startIndex, endIndex };
    }

    function updatePaginationControls(state) {
      const total = Math.max(0, Number(state.total || 0));
      const pageIndex = clampPageIndex(state.pageIndex, state.pageCount);
      const pageCount = Math.max(1, Number(state.pageCount || 1));
      const start = total ? Number(state.startIndex || 0) + 1 : 0;
      const end = total ? Number(state.endIndex || 0) : 0;
      if (wordsPaginationRoot) {
        wordsPaginationRoot.hidden = total <= 0;
      }
      if (wordsPageInfoRoot) {
        wordsPageInfoRoot.textContent = total
          ? `Showing ${start}-${end} of ${total} words`
          : "Showing 0 words";
      }
      setButtonDisabled(wordsFirstPageButton, pageIndex <= 0);
      setButtonDisabled(wordsPrevPageButton, pageIndex <= 0);
      setButtonDisabled(wordsNextPageButton, pageIndex >= pageCount - 1);
      setButtonDisabled(wordsLastPageButton, pageIndex >= pageCount - 1);
      onPaginationRendered({ ...state, pageIndex, pageCount });
    }

    function renderWordRow(doc, item) {
      const row = createNode(doc, "div", "srs-word-row");
      row.appendChild(renderTitle(doc, item));
      const status = createNode(doc, "span", "srs-word-status", item.status_label || item.status || "SRS");
      status.setAttribute("data-status", String(item.status || ""));
      row.appendChild(status);
      row.appendChild(renderMeta(doc, item));
      appendIfPresent(row, renderRuleSources(doc, item));
      appendIfPresent(row, renderRuleDetailsView(doc, item, {
        ruleDetailKey,
        expandedKeys: opts.expandedRuleDetailKeys,
        loadingKeys: opts.loadingRuleDetailKeys,
        detailsByKey: opts.ruleDetailsByKey,
        advancedEnabled: isAdvancedEnabled()
      }));
      if (isAdvancedEnabled()) {
        row.appendChild(renderAdvancedDetails(doc, item));
      }
      appendIfPresent(row, renderWordActions(doc, item));
      return row;
    }

    function renderTitle(doc, item) {
      const title = createNode(doc, "div", "srs-word-title");
      title.appendChild(createNode(doc, "span", "srs-word-display", item.display || item.lemma || "—"));
      const reading = String(item.reading || "").trim();
      if (reading && reading !== String(item.display || "").trim()) {
        title.appendChild(createNode(doc, "span", "srs-word-reading", reading));
      }
      return title;
    }

    function renderMeta(doc, item) {
      const meta = createNode(doc, "div", "srs-word-meta");
      const rows = [
        `Due: ${formatDue(item)}`,
        `Reviews: ${Number(item.review_count || 0)}`,
        `Seen: ${Number(item.exposures || 0)}`,
        formatRuleCount(item),
        `Source: ${item.source_label || item.source_type || "srs"}`
      ];
      const encounterWatch = formatEncounterWatchItem(item);
      if (encounterWatch) rows.push(encounterWatch);
      rows.forEach((text) => meta.appendChild(createNode(doc, "span", "", text)));
      return meta;
    }

    function renderRuleSources(doc, item) {
      const summary = item && typeof item.rule_summary === "object" ? item.rule_summary : {};
      const sourcePhrases = Array.isArray(summary.source_phrases) ? summary.source_phrases : [];
      if (!sourcePhrases.length) {
        return null;
      }
      const text = sourcePhrases.join(", ");
      const suffix = summary.source_preview_truncated ? ", ..." : "";
      return createNode(doc, "div", "srs-word-rules", `Matches: ${text}${suffix}`);
    }

    function renderWordActions(doc, item) {
      const actions = createNode(doc, "div", "srs-word-actions");
      if (canLoadRuleDetails(item)) {
        const key = ruleDetailKey(item);
        const expanded = key && opts.expandedRuleDetailKeys.has(key);
        const loading = key && opts.loadingRuleDetailKeys.has(key);
        const rulesButton = createNode(
          doc,
          "button",
          "srs-word-rules-button",
          loading ? "Loading..." : (expanded ? "Hide rules" : "Rule details")
        );
        rulesButton.setAttribute("type", "button");
        rulesButton.disabled = Boolean(loading);
        rulesButton.addEventListener("click", () => toggleRuleDetails(item));
        actions.appendChild(rulesButton);
      }
      if (canDiscardItem(item)) {
        const button = createNode(doc, "button", "srs-word-discard-button", "Discard");
        button.setAttribute("type", "button");
        button.addEventListener("click", () => discardWord(item, button));
        actions.appendChild(button);
      }
      return actions.children.length ? actions : null;
    }

    return { render, showListMessage };
  }

  function appendIfPresent(parent, child) {
    if (child) {
      parent.appendChild(child);
    }
  }

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

  function setButtonDisabled(button, disabled) {
    if (button) {
      button.disabled = Boolean(disabled);
    }
  }

  function clearNode(node) {
    while (node && node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function createNode(doc, tagName, className, text) {
    const node = doc.createElement(tagName);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = String(text);
    }
    return node;
  }

  function formatDate(value) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
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
      return "Queued";
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

  function appendSummaryItem(doc, label, value) {
    const item = createNode(doc, "div", "srs-words-summary-item");
    item.appendChild(createNode(doc, "span", "srs-words-summary-value", value));
    item.appendChild(createNode(doc, "span", "srs-words-summary-label", label));
    return item;
  }

  function formatRuleCount(item) {
    const summary = item && typeof item.rule_summary === "object" ? item.rule_summary : {};
    const count = Number(summary.enabled_rule_count || 0);
    return `Rules: ${Number.isFinite(count) ? count : 0}`;
  }

  function renderAdvancedDetails(doc, item) {
    const advanced = item.advanced && typeof item.advanced === "object" ? item.advanced : {};
    const advancedRoot = createNode(doc, "div", "srs-word-advanced");
    [
      `ID: ${item.item_id || "—"}`,
      `Lifecycle: ${advanced.lifecycle_state || "active"}`,
      `Scheduler: ${advanced.scheduler_state || "—"}`,
      `Step: ${advanced.scheduler_step ?? "—"}`,
      `Confidence: ${advanced.confidence ?? "—"}`,
      `Stability: ${advanced.stability ?? "—"}`,
      `Difficulty: ${advanced.difficulty ?? "—"}`
    ].forEach((text) => {
      advancedRoot.appendChild(createNode(doc, "span", "", text));
    });
    return advancedRoot;
  }

  root.optionsSrsWordsDashboardRenderer = { createWordsDashboardRenderer };
})();
