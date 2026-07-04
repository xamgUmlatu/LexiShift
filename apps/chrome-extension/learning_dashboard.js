(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const model = root.learningDashboardModel;
  const formatting = root.optionsSrsWordsDashboardFormatting;
  const view = root.learningDashboardView;
  const tableFactory = root.learningDashboardTable;
  const themeFactory = root.learningDashboardTheme;

  if (!model || !formatting || !view || !tableFactory) {
    throw new Error("[LexiShift][Vocabulary Library] Missing dashboard dependencies.");
  }

  const MEANING_PREVIEW_INITIAL_LIMIT = 8;
  const MEANING_PREVIEW_CONCURRENCY = 2;
  const RULE_DETAILS_LIMIT = 50;
  const WORD_INFO_TIMEOUT_MS = 15000;

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
    const table = tableFactory.createTableSupport({
      canDiscard,
      discardItem,
      doc,
      elements,
      meaningPreviewText,
      selectItem,
      selectedKey: () => selectedKey,
      t
    });
    const theme = themeFactory && typeof themeFactory.createThemeApplier === "function"
      ? themeFactory.createThemeApplier({
          documentRef: doc,
          settingsManager
        })
      : { applyTheme: () => Promise.resolve({ applied: false }) };

    let profileId = "default";
    let pair = "en-en";
    let latestData = null;
    let availablePairs = [];
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
      await theme.applyTheme({ items });
      doc.title = t("learning_dashboard_title", null, "Vocabulary Library");
      resolveScope(items);
      await refresh();
    }

    function bindEvents() {
      elements.refreshButton.addEventListener("click", refresh);
      elements.pairSelect.addEventListener("change", () => {
        const nextPair = model.normalizeText(elements.pairSelect.value);
        if (!nextPair || nextPair === pair) {
          return;
        }
        pair = nextPair;
        selectedKey = "";
        selectedItem = null;
        wordInfoByKey.clear();
        ruleDetailsByKey.clear();
        updateScopeLabel();
        updateLocationPair();
        refresh();
      });
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
      const requestedProfileId = params.get("profileId");
      const selectedProfileId = settingsManager.getSelectedSrsProfileId(items);
      profileId = requestedProfileId || selectedProfileId;
      let languagePrefs = settingsManager.getProfileLanguagePrefs(items, { profileId });
      let fallbackPair = params.get("pair") || languagePrefs.srsPair || items.srsPair || "en-en";
      let configuredPairs = model.listPracticePairs(items, profileId);
      const canUseFallbackPair = Boolean(fallbackPair);
      availablePairs = configuredPairs.length
        ? configuredPairs
        : (canUseFallbackPair ? model.listPracticePairs(items, profileId, { fallbackPair }) : configuredPairs);
      pair = resolveInitialPair(fallbackPair);
      renderPairSelect();
      updateScopeLabel();
    }

    async function refresh() {
      if (!availablePairs.length) {
        latestData = { summary: {}, items: [], dashboard_refreshed_at: new Date().toISOString() };
        render();
        setStatus(t(
          "learning_dashboard_no_practices",
          null,
          "No Vocabulary Practice stories found for this profile."
        ));
        return;
      }
      elements.refreshButton.disabled = true;
      setStatus(t("learning_dashboard_status_refreshing", null, "Loading learning words..."));
      try {
        const result = await helperManager.listSrsItems(pair, { profileId, compact: true });
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
      view.renderSummary({ doc, elements, latestData, t });
      const rows = filteredItems();
      renderPagination(rows.length);
      table.renderTableRows({
        latestData,
        loadMeaningPreviews,
        pageRows: currentPageRows(rows),
        rows,
        token
      });
      updateClearButton();
      renderDetail();
    }

    function resolveInitialPair(fallbackPair) {
      const requested = model.normalizeText(fallbackPair);
      if (requested && availablePairs.some((entry) => entry.pair === requested)) {
        return requested;
      }
      if (availablePairs.length) {
        return availablePairs[0].pair;
      }
      return requested || "en-en";
    }

    function renderPairSelect() {
      view.clearNode(elements.pairSelect);
      if (!availablePairs.length) {
        const option = doc.createElement("option");
        option.value = "";
        option.textContent = t("learning_dashboard_no_practices_short", null, "No active practice");
        elements.pairSelect.appendChild(option);
        elements.pairSelect.disabled = true;
        return;
      }
      availablePairs.forEach((entry) => {
        const option = doc.createElement("option");
        option.value = entry.pair;
        option.textContent = entry.label;
        elements.pairSelect.appendChild(option);
      });
      elements.pairSelect.value = pair;
      elements.pairSelect.disabled = availablePairs.length <= 1;
    }

    function updateScopeLabel() {
      const pairLabel = model.pairDisplayLabel(pair);
      elements.scopeLabel.textContent = `${pairLabel} | ${profileId}`;
    }

    function updateLocationPair() {
      if (!globalThis.history || !globalThis.location || typeof globalThis.history.replaceState !== "function") {
        return;
      }
      const url = new URL(globalThis.location.href);
      url.searchParams.set("pair", pair);
      url.searchParams.set("profileId", profileId);
      globalThis.history.replaceState(null, "", url.toString());
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
      const queue = items.slice(0, MEANING_PREVIEW_INITIAL_LIMIT);
      if (!queue.length) {
        return;
      }
      scheduleDeferred(() => loadMeaningPreviewBatch(queue, token));
    }

    async function loadMeaningPreviewBatch(items, token) {
      let index = 0;
      async function worker() {
        while (token === renderToken && index < items.length) {
          const item = items[index];
          index += 1;
          await ensureWordInfo(item);
          if (token === renderToken) {
            table.updateMeaningCell(item);
          }
        }
      }
      await Promise.all(Array.from({ length: MEANING_PREVIEW_CONCURRENCY }, worker));
    }

    function scheduleDeferred(callback) {
      if (typeof globalThis.requestIdleCallback === "function") {
        globalThis.requestIdleCallback(callback, { timeout: 500 });
        return;
      }
      globalThis.setTimeout(callback, 100);
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
        timeoutMs: WORD_INFO_TIMEOUT_MS
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
        return model.sourcePhraseSummary(item)
          || t("learning_dashboard_definition_unavailable", null, "Definition unavailable.");
      }
      return model.resolveGlossPreview(entry.result)
        || model.sourcePhraseSummary(item)
        || t("learning_dashboard_definition_unavailable", null, "Definition unavailable.");
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
