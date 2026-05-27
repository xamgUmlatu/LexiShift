(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const removedStatuses = new Set(["discarded", "cleared", "removed"]);

  function createWordsDashboardModel() {
    let searchQuery = "";
    let statusFilter = "all";
    let sortMode = "source";

    function setSearchQuery(value) {
      searchQuery = String(value || "").trim();
    }

    function setStatusFilter(value) {
      statusFilter = String(value || "all").trim() || "all";
    }

    function setSortMode(value) {
      sortMode = String(value || "source").trim() || "source";
    }

    function isAdjusted() {
      return Boolean(searchQuery) || statusFilter !== "all" || sortMode !== "source";
    }

    function apply(items) {
      const entries = items.map((item, index) => ({ item, index }))
        .filter((entry) => matchesSearch(entry.item))
        .filter((entry) => matchesStatus(entry.item));
      if (sortMode !== "source") {
        entries.sort(compareItems);
      }
      return entries.map((entry) => entry.item);
    }

    function matchesSearch(item) {
      const query = searchQuery.toLocaleLowerCase();
      if (!query) {
        return true;
      }
      return [
        item.display,
        item.lemma,
        item.reading,
        item.status_label,
        item.status,
        item.serving_label,
        item.serving_state,
        item.serving ? "replacing now" : "",
        item.source_label,
        item.source_type,
        ...ruleSourcePhrases(item)
      ].some((value) => String(value || "").toLocaleLowerCase().includes(query));
    }

    function matchesStatus(item) {
      const status = String(item.status || "");
      if (statusFilter === "all") {
        return true;
      }
      if (statusFilter === "due") {
        return status === "due_now" || status === "due_soon";
      }
      if (statusFilter === "queued") {
        return status === "queued";
      }
      if (statusFilter === "removed") {
        return removedStatuses.has(status);
      }
      if (statusFilter === "active") {
        return status !== "queued" && !removedStatuses.has(status);
      }
      return true;
    }

    function compareItems(left, right) {
      let comparison = 0;
      if (sortMode === "word") {
        comparison = wordSortText(left.item).localeCompare(wordSortText(right.item));
      } else if (sortMode === "reviews") {
        comparison = Number(right.item.review_count || 0) - Number(left.item.review_count || 0);
      } else if (sortMode === "seen") {
        comparison = Number(right.item.exposures || 0) - Number(left.item.exposures || 0);
      } else if (sortMode === "due") {
        comparison = dueSortValue(left.item) - dueSortValue(right.item);
      }
      return comparison || left.index - right.index;
    }

    return {
      apply,
      isAdjusted,
      setSearchQuery,
      setSortMode,
      setStatusFilter
    };
  }

  function wordSortText(item) {
    return String(item.display || item.lemma || item.reading || "").toLocaleLowerCase();
  }

  function dueSortValue(item) {
    const status = String(item.status || "");
    if (removedStatuses.has(status)) {
      return 9000000000;
    }
    if (status === "queued") {
      return 8000000000;
    }
    const dueSeconds = Number(item.due_in_seconds);
    if (Number.isFinite(dueSeconds)) {
      return dueSeconds;
    }
    return 7000000000;
  }

  function ruleSourcePhrases(item) {
    const summary = item && typeof item.rule_summary === "object" ? item.rule_summary : {};
    return Array.isArray(summary.source_phrases) ? summary.source_phrases : [];
  }

  root.optionsSrsWordsDashboardModel = {
    createWordsDashboardModel
  };
})();
