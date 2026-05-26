(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createWordsDashboardWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({ items, profileId: "default" }));
    const confirmFn = typeof opts.confirmFn === "function"
      ? opts.confirmFn
      : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const wordsRefreshButton = opts.wordsRefreshButton || null;
    const wordsAdvancedInput = opts.wordsAdvancedInput || null;
    const wordsSearchInput = opts.wordsSearchInput || null;
    const wordsStatusFilterInput = opts.wordsStatusFilterInput || null;
    const wordsSortInput = opts.wordsSortInput || null;
    const wordsSummaryRoot = opts.wordsSummaryRoot || null;
    const wordsListRoot = opts.wordsListRoot || null;
    const maxRenderedWordRows = 300;
    const dashboardModelFactory = root.optionsSrsWordsDashboardModel
      && typeof root.optionsSrsWordsDashboardModel.createWordsDashboardModel === "function"
      ? root.optionsSrsWordsDashboardModel.createWordsDashboardModel
      : null;
    const dashboardModel = dashboardModelFactory
      ? dashboardModelFactory()
      : {
          apply: (items) => items,
          isAdjusted: () => false,
          setSearchQuery: () => {},
          setSortMode: () => {},
          setStatusFilter: () => {}
        };
    let latestWordsDashboardData = null;
    let wordsDashboardAdvanced = Boolean(wordsAdvancedInput && wordsAdvancedInput.checked);
    dashboardModel.setSearchQuery(getControlValue(wordsSearchInput));
    dashboardModel.setStatusFilter(getControlValue(wordsStatusFilterInput) || "all");
    dashboardModel.setSortMode(getControlValue(wordsSortInput) || "source");

    bindDashboardControl(wordsSearchInput, "input", () => {
      dashboardModel.setSearchQuery(getControlValue(wordsSearchInput));
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsStatusFilterInput, "change", () => {
      dashboardModel.setStatusFilter(getControlValue(wordsStatusFilterInput) || "all");
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsSortInput, "change", () => {
      dashboardModel.setSortMode(getControlValue(wordsSortInput) || "source");
      renderWordsDashboard(latestWordsDashboardData);
    });

    function getControlValue(control) {
      return control && control.value !== undefined ? String(control.value || "").trim() : "";
    }

    function bindDashboardControl(control, eventName, handler) {
      if (!control || typeof control.addEventListener !== "function") {
        return;
      }
      control.addEventListener(eventName, handler);
    }

    function clearNode(node) {
      if (!node) {
        return;
      }
      while (node.firstChild) {
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
      if (Number.isNaN(date.getTime())) {
        return "—";
      }
      return date.toLocaleString();
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

    function renderWordsDashboard(dataArg) {
      if (!wordsSummaryRoot || !wordsListRoot) {
        return;
      }
      const doc = wordsListRoot.ownerDocument || globalThis.document;
      if (!doc) {
        return;
      }
      const data = dataArg || latestWordsDashboardData;
      clearNode(wordsSummaryRoot);
      clearNode(wordsListRoot);
      if (!data) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-empty",
          "Refresh words to load the current SRS dashboard."
        ));
        return;
      }

      const summary = data.summary && typeof data.summary === "object" ? data.summary : {};
      [
        ["Active", summary.active || 0],
        ["Due now", summary.due_now || 0],
        ["Due soon", summary.due_soon || 0],
        ["Queued", summary.queued || 0],
        ["Removed", summary.removed || 0],
        ["Total", summary.total || 0]
      ].forEach(([label, value]) => {
        wordsSummaryRoot.appendChild(appendSummaryItem(doc, label, value));
      });

      const allItems = Array.isArray(data.items) ? data.items : [];
      const items = dashboardModel.apply(allItems);
      if (!items.length) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-empty",
          allItems.length
            ? "No SRS words match these filters."
            : "No SRS words are admitted for this pair yet."
        ));
        return;
      }

      if (dashboardModel.isAdjusted()) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-filter-note",
          `Showing ${items.length} of ${allItems.length} words.`
        ));
      }

      items.slice(0, maxRenderedWordRows).forEach((item) => {
        wordsListRoot.appendChild(renderWordRow(doc, item));
      });

      if (items.length > maxRenderedWordRows) {
        wordsListRoot.appendChild(createNode(
          doc,
          "p",
          "srs-words-truncated",
          `Showing ${maxRenderedWordRows} of ${items.length} words.`
        ));
      }
    }

    function renderWordRow(doc, item) {
      const row = createNode(doc, "div", "srs-word-row");
      const title = createNode(doc, "div", "srs-word-title");
      const display = createNode(doc, "span", "srs-word-display", item.display || item.lemma || "—");
      title.appendChild(display);
      const reading = String(item.reading || "").trim();
      if (reading && reading !== String(item.display || "").trim()) {
        title.appendChild(createNode(doc, "span", "srs-word-reading", reading));
      }
      row.appendChild(title);

      const status = createNode(doc, "span", "srs-word-status", item.status_label || item.status || "SRS");
      status.setAttribute("data-status", String(item.status || ""));
      row.appendChild(status);

      const meta = createNode(doc, "div", "srs-word-meta");
      [
        `Due: ${formatDue(item)}`,
        `Reviews: ${Number(item.review_count || 0)}`,
        `Seen: ${Number(item.exposures || 0)}`,
        `Source: ${item.source_label || item.source_type || "srs"}`
      ].forEach((text) => {
        meta.appendChild(createNode(doc, "span", "", text));
      });
      row.appendChild(meta);

      if (wordsDashboardAdvanced) {
        row.appendChild(renderAdvancedDetails(doc, item));
      }
      if (canDiscardItem(item)) {
        row.appendChild(renderWordActions(doc, item));
      }

      return row;
    }

    function canDiscardItem(item) {
      const status = String(item.status || "");
      if (!String(item.lemma || "").trim()) {
        return false;
      }
      return status !== "discarded" && status !== "cleared" && status !== "removed";
    }

    function renderWordActions(doc, item) {
      const actions = createNode(doc, "div", "srs-word-actions");
      const button = createNode(doc, "button", "srs-word-discard-button", "Discard");
      button.setAttribute("type", "button");
      button.addEventListener("click", () => discardWord(item, button));
      actions.appendChild(button);
      return actions;
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

    async function refreshWordsDashboard() {
      if (!wordsRefreshButton || !wordsSummaryRoot || !wordsListRoot) {
        return;
      }
      const srsPair = resolvePair();
      wordsRefreshButton.disabled = true;
      const doc = wordsListRoot.ownerDocument || globalThis.document;
      if (doc) {
        clearNode(wordsListRoot);
        wordsListRoot.appendChild(createNode(doc, "p", "srs-words-empty", "Loading SRS words…"));
      }
      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const result = await helperManager.listSrsItems(srsPair, {
          profileId: synced.profileId
        });
        latestWordsDashboardData = result;
        renderWordsDashboard(result);
        const total = result && result.summary ? Number(result.summary.total || 0) : 0;
        setStatus(
          translate("status_srs_items_list_ready", [total], `Loaded ${total} SRS words.`),
          colors.SUCCESS
        );
        log("SRS words dashboard refreshed", {
          pair: srsPair,
          profileId: synced.profileId,
          summary: result.summary || null
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_items_list_failed", null, "Failed to load SRS words.");
        if (doc) {
          clearNode(wordsListRoot);
          wordsListRoot.appendChild(createNode(doc, "p", "srs-words-empty", msg));
        }
        setStatus(msg, colors.ERROR);
        log("SRS words dashboard refresh failed.", err);
      } finally {
        wordsRefreshButton.disabled = false;
      }
    }

    async function discardWord(item, button) {
      const lemma = String(item.lemma || "").trim();
      const display = String(item.display || lemma || "this word").trim();
      if (!lemma) {
        return;
      }
      const confirmed = confirmFn(translate(
        "confirm_srs_discard_word",
        [display],
        `Discard ${display}? It will be removed from SRS and blocked from future admission until SRS data is reset.`
      ));
      if (!confirmed) {
        return;
      }
      const srsPair = resolvePair();
      if (button) {
        button.disabled = true;
      }
      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const result = await helperManager.discardSrsItem(srsPair, lemma, {
          profileId: synced.profileId
        });
        setStatus(
          translate("status_srs_discard_success", [display], `Discarded ${display}.`),
          colors.SUCCESS
        );
        log("SRS word discarded", {
          pair: srsPair,
          profileId: synced.profileId,
          lemma,
          result
        });
        await refreshWordsDashboard();
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_discard_failed", null, "Failed to discard SRS word.");
        setStatus(msg, colors.ERROR);
        log("SRS word discard failed.", err);
      } finally {
        if (button) {
          button.disabled = false;
        }
      }
    }

    function setWordsDashboardAdvanced(enabled) {
      wordsDashboardAdvanced = Boolean(enabled);
      renderWordsDashboard(latestWordsDashboardData);
    }

    return {
      refreshWordsDashboard,
      setWordsDashboardAdvanced
    };
  }

  root.optionsSrsWordsDashboardWorkflow = {
    createWordsDashboardWorkflow
  };
})();
