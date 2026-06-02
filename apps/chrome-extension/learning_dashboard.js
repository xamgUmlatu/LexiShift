(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const model = root.learningDashboardModel;
  const formatting = root.optionsSrsWordsDashboardFormatting;
  const view = root.learningDashboardView;

  if (!model || !formatting || !view) {
    throw new Error("[LexiShift][Vocabulary Library] Missing dashboard dependencies.");
  }

  const MEANING_PREVIEW_LIMIT = 25;
  const RULE_DETAILS_LIMIT = 50;

  function createLearningDashboardController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const doc = opts.document || globalThis.document;
    const settingsManager = opts.settingsManager;
    const helperManager = opts.helperManager;
    const i18n = opts.i18n;
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : globalThis.confirm;
    const dashboardModelFactory = root.optionsSrsWordsDashboardModel
      && typeof root.optionsSrsWordsDashboardModel.createWordsDashboardModel === "function"
      ? root.optionsSrsWordsDashboardModel.createWordsDashboardModel
      : null;
    const dashboardModel = dashboardModelFactory
      ? dashboardModelFactory()
      : { apply: (items) => items, isAdjusted: () => false, setSearchQuery: () => {}, setSortMode: () => {}, setStatusFilter: () => {} };
    const elements = view.resolveElements(doc);

    let profileId = "default";
    let pair = "en-en";
    let latestData = null;
    let pageIndex = 0;
    let pageSize = 25;
    let pageCount = 1;
    let selectedKey = "";
    let selectedItem = null;
    let advancedEnabled = false;
    let renderToken = 0;
    const wordInfoByKey = new Map();
    const ruleDetailsByKey = new Map();

    async function init() {
      bindEvents();
      setStatus(t("learning_dashboard_status_loading", null, "Loading Vocabulary Library..."));
      const items = await settingsManager.load();
      if (i18n && typeof i18n.load === "function") {
        await i18n.load(items.uiLanguage || "system");
      }
      doc.title = t("learning_dashboard_title", null, "Vocabulary Library");
      resolveScope(items);
      await refresh();
    }

    function bindEvents() {
      elements.refreshButton.addEventListener("click", refresh);
      elements.searchInput.addEventListener("input", () => {
        dashboardModel.setSearchQuery(elements.searchInput.value);
        resetPage();
        render();
      });
      elements.searchInput.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !elements.searchInput.value) {
          return;
        }
        elements.searchInput.value = "";
        dashboardModel.setSearchQuery("");
        resetPage();
        render();
      });
      elements.statusFilter.addEventListener("change", () => {
        dashboardModel.setStatusFilter(elements.statusFilter.value);
        resetPage();
        render();
      });
      elements.sortInput.addEventListener("change", () => {
        dashboardModel.setSortMode(elements.sortInput.value);
        resetPage();
        render();
      });
      elements.pageSizeInput.addEventListener("change", () => {
        pageSize = formatting.normalizePageSize(elements.pageSizeInput.value);
        resetPage();
        render();
      });
      elements.advancedInput.addEventListener("change", () => {
        advancedEnabled = Boolean(elements.advancedInput.checked);
        renderDetail();
      });
      elements.clearButton.addEventListener("click", clearFilters);
      elements.firstPageButton.addEventListener("click", () => setPage(0));
      elements.prevPageButton.addEventListener("click", () => setPage(pageIndex - 1));
      elements.nextPageButton.addEventListener("click", () => setPage(pageIndex + 1));
      elements.lastPageButton.addEventListener("click", () => setPage(pageCount - 1));
    }

    function resolveScope(items) {
      const params = new URLSearchParams(globalThis.location ? globalThis.location.search : "");
      profileId = params.get("profileId") || settingsManager.getSelectedSrsProfileId(items);
      const languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
      pair = params.get("pair") || languagePrefs.srsPair || items.srsPair || "en-en";
      elements.scopeLabel.textContent = `${pair} | ${profileId}`;
    }

    async function refresh() {
      elements.refreshButton.disabled = true;
      setStatus(t("learning_dashboard_status_refreshing", null, "Loading learning words..."));
      try {
        const result = await helperManager.listSrsItems(pair, { profileId });
        latestData = {
          ...(result && typeof result === "object" ? result : {}),
          dashboard_refreshed_at: new Date().toISOString()
        };
        resetPage();
        render();
        const total = latestData.summary ? Number(latestData.summary.total || 0) : 0;
        setStatus(t("learning_dashboard_status_ready", [total], `Loaded ${total} learning words.`));
      } catch (error) {
        latestData = null;
        render();
        setStatus(error && error.message ? error.message : t("learning_dashboard_status_failed", null, "Failed to load learning words."));
      } finally {
        elements.refreshButton.disabled = false;
      }
    }

    function render() {
      renderToken += 1;
      const token = renderToken;
      view.clearNode(elements.summaryRoot);
      view.clearNode(elements.tableBody);
      renderSummary();
      const rows = filteredItems();
      renderPagination(rows.length);
      renderTableRows(rows, token);
      updateClearButton();
      renderDetail();
    }

    function renderSummary() {
      const summary = latestData && latestData.summary && typeof latestData.summary === "object"
        ? latestData.summary
        : {};
      [
        ["learning_dashboard_summary_active", "Active", summary.active || 0],
        ["learning_dashboard_summary_due", "Due now", summary.due_now || 0],
        ["learning_dashboard_summary_can_appear", "Can appear", summary.serving_now || 0],
        ["learning_dashboard_summary_upcoming", "Upcoming", summary.queued || 0],
        ["learning_dashboard_summary_removed", "Removed", summary.removed || 0],
        ["learning_dashboard_summary_total", "Total", summary.total || 0]
      ].forEach(([key, fallback, value]) => {
        const item = view.createNode(doc, "div", "library-summary-item");
        item.appendChild(view.createNode(doc, "span", "library-summary-value", value));
        item.appendChild(view.createNode(doc, "span", "library-summary-label", t(key, null, fallback)));
        elements.summaryRoot.appendChild(item);
      });
    }

    function renderTableRows(rows, token) {
      if (!rows.length) {
        const row = doc.createElement("tr");
        const cell = doc.createElement("td");
        cell.colSpan = 6;
        cell.className = "library-empty";
        cell.textContent = latestData
          ? t("learning_dashboard_empty_filtered", null, "No learning words match these filters.")
          : t("learning_dashboard_empty_unloaded", null, "No learning words loaded yet.");
        row.appendChild(cell);
        elements.tableBody.appendChild(row);
        return;
      }
      const pageRows = currentPageRows(rows);
      pageRows.forEach((item) => {
        const row = renderItemRow(item);
        elements.tableBody.appendChild(row);
      });
      loadMeaningPreviews(pageRows, token);
    }

    function renderItemRow(item) {
      const key = model.itemKey(item);
      const row = doc.createElement("tr");
      row.className = key === selectedKey ? "is-selected" : "";
      row.tabIndex = 0;
      row.dataset.itemKey = key;
      row.addEventListener("dblclick", () => selectItem(item));
      row.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }
        event.preventDefault();
        selectItem(item);
      });
      row.appendChild(wordCell(item));
      row.appendChild(meaningCell(item));
      row.appendChild(view.createNode(doc, "td", "", item.status_label || item.status || "Learning"));
      row.appendChild(view.createNode(doc, "td", "", model.formatActivity(item)));
      row.appendChild(view.createNode(doc, "td", "", model.resolveTopicLabel(item)));
      row.appendChild(actionCell(item));
      return row;
    }

    function wordCell(item) {
      const cell = view.createNode(doc, "td", "library-word-cell");
      cell.appendChild(view.createNode(doc, "span", "library-word", item.display || item.lemma || "-"));
      const info = [item.reading, item.pos].map(model.normalizeText).filter(Boolean).join(" | ");
      if (info) {
        cell.appendChild(view.createNode(doc, "span", "library-word-sub", info));
      }
      return cell;
    }

    function meaningCell(item) {
      const key = model.itemKey(item);
      const cell = view.createNode(doc, "td", "library-meaning-cell");
      cell.dataset.meaningKey = key;
      cell.textContent = meaningPreviewText(item);
      return cell;
    }

    function actionCell(item) {
      const cell = view.createNode(doc, "td", "library-action-cell");
      if (!canDiscard(item)) {
        return cell;
      }
      const button = view.createNode(doc, "button", "library-discard-button", t("learning_dashboard_discard", null, "Discard"));
      button.type = "button";
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        discardItem(item, button);
      });
      cell.appendChild(button);
      return cell;
    }

    function renderDetail() {
      view.renderDetail({
        advancedEnabled,
        doc,
        elements,
        ensureRuleDetails,
        ensureWordInfo,
        getSelectedKey: () => selectedKey,
        isAdvancedEnabled: () => advancedEnabled,
        item: selectedItem,
        renderDetail,
        t,
        wordInfoByKey
      });
    }

    function loadMeaningPreviews(items, token) {
      items.slice(0, MEANING_PREVIEW_LIMIT).forEach((item) => {
        ensureWordInfo(item).then(() => {
          if (token === renderToken) {
            updateMeaningCell(item);
          }
        });
      });
    }

    async function ensureWordInfo(item) {
      const key = model.itemKey(item);
      const existing = wordInfoByKey.get(key);
      if (existing && existing.promise) {
        return existing.promise;
      }
      if (existing && existing.status === "ready") {
        return existing.result;
      }
      const promise = helperManager.lookupWordInfo(model.createWordInfoRequest({ item, pair, profileId }), {
        timeoutMs: 4000
      }).then((result) => {
        wordInfoByKey.set(key, { status: "ready", result });
        return result;
      }).catch((error) => {
        wordInfoByKey.set(key, { status: "error", error });
        return null;
      });
      wordInfoByKey.set(key, { status: "loading", promise });
      return promise;
    }

    async function ensureRuleDetails(item) {
      if (!model.hasPublishedRules(item)) {
        return null;
      }
      const key = model.itemKey(item);
      const existing = ruleDetailsByKey.get(key);
      if (existing) {
        return existing;
      }
      const details = await helperManager.getSrsItemRuleDetails(pair, item.lemma, {
        profileId,
        limit: RULE_DETAILS_LIMIT
      });
      ruleDetailsByKey.set(key, details);
      return details;
    }

    function meaningPreviewText(item) {
      const entry = wordInfoByKey.get(model.itemKey(item));
      if (!entry) {
        return t("learning_dashboard_definition_loading", null, "Loading definition...");
      }
      if (entry.status === "loading") {
        return t("learning_dashboard_definition_loading", null, "Loading definition...");
      }
      if (entry.status === "error") {
        return t("learning_dashboard_definition_unavailable", null, "Definition unavailable.");
      }
      return model.resolveGlossPreview(entry.result)
        || t("learning_dashboard_definition_unavailable", null, "Definition unavailable.");
    }

    function updateMeaningCell(item) {
      const key = model.itemKey(item);
      elements.tableBody.querySelectorAll("[data-meaning-key]").forEach((cell) => {
        if (cell.dataset.meaningKey === key) {
          cell.textContent = meaningPreviewText(item);
        }
      });
    }

    function selectItem(item) {
      selectedItem = item;
      selectedKey = model.itemKey(item);
      elements.tableBody.querySelectorAll("tr").forEach((row) => {
        row.classList.toggle("is-selected", row.dataset.itemKey === selectedKey);
      });
      renderDetail();
    }

    async function discardItem(item, button) {
      const lemma = model.normalizeText(item && item.lemma);
      if (!lemma) {
        return;
      }
      const display = model.normalizeText(item.display || lemma);
      const confirmed = confirmFn(t(
        "confirm_srs_discard_word",
        [display],
        `Discard ${display}? It will be removed from Vocabulary Practice and blocked from future admission until practice data is reset.`
      ));
      if (!confirmed) {
        return;
      }
      button.disabled = true;
      try {
        await helperManager.discardSrsItem(pair, lemma, { profileId });
        if (selectedKey === model.itemKey(item)) {
          selectedKey = "";
          selectedItem = null;
        }
        await refresh();
      } finally {
        button.disabled = false;
      }
    }

    function filteredItems() {
      if (!latestData || !Array.isArray(latestData.items)) {
        return [];
      }
      return dashboardModel.apply(latestData.items);
    }

    function currentPageRows(rows) {
      const start = Math.min(rows.length, pageIndex * pageSize);
      return rows.slice(start, Math.min(rows.length, start + pageSize));
    }

    function renderPagination(total) {
      pageCount = Math.max(1, Math.ceil(total / pageSize));
      pageIndex = formatting.clampPageIndex(pageIndex, pageCount);
      const start = total ? pageIndex * pageSize + 1 : 0;
      const end = total ? Math.min(total, start + pageSize - 1) : 0;
      elements.pageInfo.textContent = total
        ? t("learning_dashboard_page_info", [start, end, total], `Showing ${start}-${end} of ${total} words`)
        : t("learning_dashboard_page_empty", null, "Showing 0 words");
      elements.firstPageButton.disabled = pageIndex <= 0;
      elements.prevPageButton.disabled = pageIndex <= 0;
      elements.nextPageButton.disabled = pageIndex >= pageCount - 1;
      elements.lastPageButton.disabled = pageIndex >= pageCount - 1;
    }

    function clearFilters() {
      elements.searchInput.value = "";
      elements.statusFilter.value = "all";
      elements.sortInput.value = "source";
      dashboardModel.setSearchQuery("");
      dashboardModel.setStatusFilter("all");
      dashboardModel.setSortMode("source");
      resetPage();
      render();
    }

    function updateClearButton() {
      elements.clearButton.disabled = !dashboardModel.isAdjusted();
    }

    function setPage(index) {
      pageIndex = formatting.clampPageIndex(index, pageCount);
      render();
    }

    function resetPage() {
      pageIndex = 0;
    }

    function canDiscard(item) {
      const status = model.normalizeText(item && item.status);
      return Boolean(model.normalizeText(item && item.lemma))
        && !["discarded", "cleared", "removed"].includes(status);
    }

    function setStatus(message) {
      elements.statusOutput.textContent = message;
    }

    function t(key, substitutions, fallback) {
      return i18n && typeof i18n.t === "function" ? i18n.t(key, substitutions, fallback) : fallback;
    }

    return { init, refresh };
  }

  async function startDefaultController() {
    const i18n = new LocalizationService();
    const settingsManager = new SettingsManager();
    const helperManager = new HelperManager(i18n, (...args) => console.log("[LexiShift][Vocabulary Library]", ...args));
    const controller = createLearningDashboardController({
      document,
      settingsManager,
      helperManager,
      i18n
    });
    await controller.init();
  }

  root.learningDashboard = {
    createLearningDashboardController,
    resolveGlosses: view.resolveGlosses
  };

  if (globalThis.document && typeof document.addEventListener === "function") {
    document.addEventListener("DOMContentLoaded", () => {
      startDefaultController().catch((error) => {
        console.error("[LexiShift][Vocabulary Library] Failed to start.", error);
      });
    });
  }
})();
