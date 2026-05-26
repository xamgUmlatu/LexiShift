(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createWordsDashboardWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object" ? opts.settingsManager : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object" ? opts.helperManager : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({ items, profileId: "default" }));
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318", DEFAULT: "#6c675f" };
    const wordsRefreshButton = opts.wordsRefreshButton || null;
    const wordsAdvancedInput = opts.wordsAdvancedInput || null;
    const wordsSearchInput = opts.wordsSearchInput || null;
    const wordsStatusFilterInput = opts.wordsStatusFilterInput || null;
    const wordsSortInput = opts.wordsSortInput || null;
    const wordsPageSizeInput = opts.wordsPageSizeInput || null;
    const wordsClearFiltersButton = opts.wordsClearFiltersButton || null;
    const wordsSummaryRoot = opts.wordsSummaryRoot || null;
    const wordsPaginationRoot = opts.wordsPaginationRoot || null;
    const wordsPageInfoRoot = opts.wordsPageInfoRoot || null;
    const wordsFirstPageButton = opts.wordsFirstPageButton || null;
    const wordsPrevPageButton = opts.wordsPrevPageButton || null;
    const wordsNextPageButton = opts.wordsNextPageButton || null;
    const wordsLastPageButton = opts.wordsLastPageButton || null;
    const wordsListRoot = opts.wordsListRoot || null;
    const maxRenderedWordRows = 300;
    const ruleDetailsLimit = 50;
    const dashboardModelFactory = root.optionsSrsWordsDashboardModel
      && typeof root.optionsSrsWordsDashboardModel.createWordsDashboardModel === "function"
      ? root.optionsSrsWordsDashboardModel.createWordsDashboardModel
      : null;
    const dashboardModel = dashboardModelFactory
      ? dashboardModelFactory()
      : { apply: (items) => items, isAdjusted: () => false, setSearchQuery: () => {}, setSortMode: () => {}, setStatusFilter: () => {} };
    const ruleDetailsModule = root.optionsSrsWordsDashboardRuleDetails || {};
    const renderRuleDetailsView = typeof ruleDetailsModule.renderRuleDetails === "function"
      ? ruleDetailsModule.renderRuleDetails
      : (() => null);
    const dashboardRendererFactory = root.optionsSrsWordsDashboardRenderer
      && typeof root.optionsSrsWordsDashboardRenderer.createWordsDashboardRenderer === "function"
      ? root.optionsSrsWordsDashboardRenderer.createWordsDashboardRenderer
      : null;
    let latestWordsDashboardData = null;
    let latestWordsDashboardProfileId = "default";
    let wordsDashboardAdvanced = Boolean(wordsAdvancedInput && wordsAdvancedInput.checked);
    let wordsDashboardPageIndex = 0;
    let wordsDashboardPageSize = normalizePageSize(getControlValue(wordsPageSizeInput) || 25);
    let wordsDashboardPageCount = 1;
    const expandedRuleDetailKeys = new Set();
    const loadingRuleDetailKeys = new Set();
    const ruleDetailsByKey = new Map();
    const dashboardRenderer = dashboardRendererFactory
      ? dashboardRendererFactory({
          wordsSummaryRoot,
          wordsPaginationRoot,
          wordsPageInfoRoot,
          wordsFirstPageButton,
          wordsPrevPageButton,
          wordsNextPageButton,
          wordsLastPageButton,
          wordsListRoot,
          dashboardModel,
          maxRenderedWordRows,
          renderRuleDetailsView,
          expandedRuleDetailKeys,
          loadingRuleDetailKeys,
          ruleDetailsByKey,
          isAdvancedEnabled: () => wordsDashboardAdvanced,
          canLoadRuleDetails,
          canDiscardItem,
          ruleDetailKey,
          getPaginationState: () => ({
            pageIndex: wordsDashboardPageIndex,
            pageSize: wordsDashboardPageSize
          }),
          onPaginationRendered: (state) => {
            wordsDashboardPageIndex = state.pageIndex;
            wordsDashboardPageCount = state.pageCount;
          },
          toggleRuleDetails,
          discardWord
        })
      : { render: () => {}, showListMessage: () => {} };
    dashboardModel.setSearchQuery(getControlValue(wordsSearchInput));
    dashboardModel.setStatusFilter(getControlValue(wordsStatusFilterInput) || "all");
    dashboardModel.setSortMode(getControlValue(wordsSortInput) || "source");

    bindDashboardControl(wordsSearchInput, "input", () => {
      resetWordsDashboardPage();
      dashboardModel.setSearchQuery(getControlValue(wordsSearchInput));
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsStatusFilterInput, "change", () => {
      resetWordsDashboardPage();
      dashboardModel.setStatusFilter(getControlValue(wordsStatusFilterInput) || "all");
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsSortInput, "change", () => {
      resetWordsDashboardPage();
      dashboardModel.setSortMode(getControlValue(wordsSortInput) || "source");
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsPageSizeInput, "change", () => {
      wordsDashboardPageSize = normalizePageSize(getControlValue(wordsPageSizeInput));
      resetWordsDashboardPage();
      renderWordsDashboard(latestWordsDashboardData);
    });
    bindDashboardControl(wordsClearFiltersButton, "click", clearWordsDashboardFilters);
    bindDashboardControl(wordsFirstPageButton, "click", () => setWordsDashboardPage(0));
    bindDashboardControl(wordsPrevPageButton, "click", () => {
      setWordsDashboardPage(wordsDashboardPageIndex - 1);
    });
    bindDashboardControl(wordsNextPageButton, "click", () => {
      setWordsDashboardPage(wordsDashboardPageIndex + 1);
    });
    bindDashboardControl(wordsLastPageButton, "click", () => {
      setWordsDashboardPage(wordsDashboardPageCount - 1);
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

    function normalizePageSize(value) {
      const parsed = Number.parseInt(value, 10);
      if (!Number.isFinite(parsed)) {
        return 25;
      }
      return Math.max(1, Math.min(300, parsed));
    }

    function resetWordsDashboardPage() {
      wordsDashboardPageIndex = 0;
    }

    function setWordsDashboardPage(index) {
      wordsDashboardPageIndex = Math.max(0, Math.min(wordsDashboardPageCount - 1, index));
      renderWordsDashboard(latestWordsDashboardData);
    }

    function clearWordsDashboardFilters() {
      if (wordsSearchInput) {
        wordsSearchInput.value = "";
      }
      if (wordsStatusFilterInput) {
        wordsStatusFilterInput.value = "all";
      }
      if (wordsSortInput) {
        wordsSortInput.value = "source";
      }
      dashboardModel.setSearchQuery("");
      dashboardModel.setStatusFilter("all");
      dashboardModel.setSortMode("source");
      resetWordsDashboardPage();
      renderWordsDashboard(latestWordsDashboardData);
    }

    function renderWordsDashboard(dataArg) {
      dashboardRenderer.render(dataArg || latestWordsDashboardData);
    }

    function hasPublishedRules(item) {
      const summary = item && typeof item.rule_summary === "object" ? item.rule_summary : {};
      const count = Number(summary.rule_count || summary.enabled_rule_count || 0);
      return Number.isFinite(count) && count > 0 && Boolean(String(item.lemma || "").trim());
    }

    function canLoadRuleDetails(item) {
      return hasPublishedRules(item)
        && helperManager
        && typeof helperManager.getSrsItemRuleDetails === "function";
    }

    function ruleDetailKey(item) {
      return String(item.item_id || item.lemma || "").trim();
    }

    function canDiscardItem(item) {
      const status = String(item.status || "");
      if (!String(item.lemma || "").trim()) {
        return false;
      }
      return status !== "discarded" && status !== "cleared" && status !== "removed";
    }

    function showWordsDashboardMessage(message) {
      dashboardRenderer.showListMessage(message);
    }

    async function refreshWordsDashboard() {
      if (!wordsRefreshButton || !wordsSummaryRoot || !wordsListRoot) {
        return;
      }
      const srsPair = resolvePair();
      wordsRefreshButton.disabled = true;
      showWordsDashboardMessage("Loading SRS words…");
      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const result = await helperManager.listSrsItems(srsPair, {
          profileId: synced.profileId
        });
        expandedRuleDetailKeys.clear();
        loadingRuleDetailKeys.clear();
        ruleDetailsByKey.clear();
        resetWordsDashboardPage();
        latestWordsDashboardProfileId = synced.profileId || "default";
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
        showWordsDashboardMessage(msg);
        setStatus(msg, colors.ERROR);
        log("SRS words dashboard refresh failed.", err);
      } finally {
        wordsRefreshButton.disabled = false;
      }
    }

    async function toggleRuleDetails(item) {
      const key = ruleDetailKey(item);
      const lemma = String(item && item.lemma ? item.lemma : "").trim();
      if (!key || !lemma || !canLoadRuleDetails(item)) {
        return;
      }
      if (expandedRuleDetailKeys.has(key) && !loadingRuleDetailKeys.has(key)) {
        expandedRuleDetailKeys.delete(key);
        renderWordsDashboard(latestWordsDashboardData);
        return;
      }
      expandedRuleDetailKeys.add(key);
      if (ruleDetailsByKey.has(key)) {
        renderWordsDashboard(latestWordsDashboardData);
        return;
      }
      loadingRuleDetailKeys.add(key);
      renderWordsDashboard(latestWordsDashboardData);
      try {
        const srsPair = resolvePair();
        const result = await helperManager.getSrsItemRuleDetails(srsPair, lemma, {
          profileId: latestWordsDashboardProfileId,
          limit: ruleDetailsLimit
        });
        ruleDetailsByKey.set(key, result);
        setStatus(
          translate("status_srs_rule_details_ready", [item.display || lemma], `Loaded rule details for ${item.display || lemma}.`),
          colors.SUCCESS
        );
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_rule_details_failed", null, "Failed to load rule details.");
        ruleDetailsByKey.set(key, { load_error: msg, rules: [] });
        setStatus(msg, colors.ERROR);
        log("SRS word rule details failed.", err);
      } finally {
        loadingRuleDetailKeys.delete(key);
        renderWordsDashboard(latestWordsDashboardData);
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
