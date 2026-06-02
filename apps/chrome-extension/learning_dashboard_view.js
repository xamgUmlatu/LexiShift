(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const model = root.learningDashboardModel;
  const formatting = root.optionsSrsWordsDashboardFormatting;

  if (!model || !formatting) {
    throw new Error("[LexiShift][Vocabulary Library] Missing view dependencies.");
  }

  function resolveElements(doc) {
    return {
      advancedInput: byId(doc, "learning-dashboard-advanced"),
      clearButton: byId(doc, "learning-dashboard-clear"),
      detailRoot: byId(doc, "learning-dashboard-detail"),
      firstPageButton: byId(doc, "learning-dashboard-first"),
      lastPageButton: byId(doc, "learning-dashboard-last"),
      nextPageButton: byId(doc, "learning-dashboard-next"),
      pageInfo: byId(doc, "learning-dashboard-page-info"),
      pageSizeInput: byId(doc, "learning-dashboard-page-size"),
      prevPageButton: byId(doc, "learning-dashboard-prev"),
      refreshButton: byId(doc, "learning-dashboard-refresh"),
      scopeLabel: byId(doc, "learning-dashboard-scope"),
      searchInput: byId(doc, "learning-dashboard-search"),
      sortInput: byId(doc, "learning-dashboard-sort"),
      statusFilter: byId(doc, "learning-dashboard-status-filter"),
      statusOutput: byId(doc, "learning-dashboard-status"),
      summaryRoot: byId(doc, "learning-dashboard-summary"),
      tableBody: byId(doc, "learning-dashboard-table-body")
    };
  }

  function renderDetail(options) {
    const opts = options && typeof options === "object" ? options : {};
    const item = opts.item || null;
    const elements = opts.elements || {};
    const t = typeof opts.t === "function" ? opts.t : ((_key, _subs, fallback) => fallback);
    clearNode(elements.detailRoot);
    if (!item) {
      elements.detailRoot.appendChild(createNode(opts.doc, "p", "library-detail-empty", t(
        "learning_dashboard_detail_empty",
        null,
        "Double-click a word to view definitions and practice details."
      )));
      return;
    }
    elements.detailRoot.appendChild(createNode(opts.doc, "h2", "", item.display || item.lemma || "-"));
    elements.detailRoot.appendChild(createNode(opts.doc, "p", "library-detail-meta", [
      item.status_label || item.status || "Learning",
      model.formatActivity(item),
      `${opts.t("learning_dashboard_page_replacement_label", null, "Page replacement")}: ${formatting.formatServingLabel(item)}`
    ].join(" | ")));
    renderDefinitionDetail(opts);
    renderReplacementSources(opts);
    renderExternalLinks(opts);
    if (opts.advancedEnabled) {
      renderAdvancedDetail(opts);
    }
  }

  function renderDefinitionDetail(opts) {
    const item = opts.item;
    const t = opts.t;
    const section = detailSection(opts.doc, t, "learning_dashboard_definition", "Definition");
    const entry = opts.wordInfoByKey.get(model.itemKey(item));
    if (!entry || entry.status === "loading") {
      section.appendChild(createNode(opts.doc, "p", "", t("learning_dashboard_definition_loading", null, "Loading definition...")));
      opts.elements.detailRoot.appendChild(section);
      opts.ensureWordInfo(item).then(() => opts.renderDetail());
      return;
    }
    const glosses = resolveGlosses(entry.result);
    if (entry.status === "error" || !glosses.length) {
      section.appendChild(createNode(opts.doc, "p", "", t("learning_dashboard_definition_unavailable", null, "Definition unavailable.")));
      opts.elements.detailRoot.appendChild(section);
      return;
    }
    const list = opts.doc.createElement("ul");
    glosses.forEach((gloss) => {
      const row = opts.doc.createElement("li");
      row.textContent = gloss.text;
      if (gloss.details.length) {
        row.appendChild(createNode(opts.doc, "span", "library-gloss-detail", ` ${gloss.details.join("; ")}`));
      }
      list.appendChild(row);
    });
    section.appendChild(list);
    opts.elements.detailRoot.appendChild(section);
  }

  function renderReplacementSources(opts) {
    const section = detailSection(opts.doc, opts.t, "learning_dashboard_replacement_sources", "Page replacements");
    const summary = model.sourcePhraseSummary(opts.item);
    section.appendChild(createNode(
      opts.doc,
      "p",
      "",
      summary || opts.t("learning_dashboard_no_replacement_sources", null, "No published page-replacement sources found.")
    ));
    opts.elements.detailRoot.appendChild(section);
  }

  function renderExternalLinks(opts) {
    const entry = opts.wordInfoByKey.get(model.itemKey(opts.item));
    const links = Array.isArray(entry && entry.result && entry.result.external_links)
      ? entry.result.external_links
      : [];
    if (!links.length) {
      return;
    }
    const section = detailSection(opts.doc, opts.t, "learning_dashboard_dictionaries", "Dictionaries");
    links.slice(0, 3).forEach((link) => {
      const url = model.normalizeText(link && link.url);
      if (!url) {
        return;
      }
      const anchor = opts.doc.createElement("a");
      anchor.href = url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = model.normalizeText(link.label) || "Dictionary";
      section.appendChild(anchor);
    });
    opts.elements.detailRoot.appendChild(section);
  }

  function renderAdvancedDetail(opts) {
    const section = detailSection(opts.doc, opts.t, "learning_dashboard_advanced", "Advanced");
    const advanced = opts.item.advanced && typeof opts.item.advanced === "object" ? opts.item.advanced : {};
    [
      [opts.t("learning_dashboard_practice_state_label", null, "Practice state"), advanced.lifecycle_state || "active"],
      [opts.t("learning_dashboard_scheduler_label", null, "Scheduler"), advanced.scheduler_state || "-"],
      [opts.t("learning_dashboard_step_label", null, "Step"), advanced.scheduler_step ?? "-"],
      [opts.t("learning_dashboard_confidence_label", null, "Confidence"), advanced.confidence ?? "-"],
      [opts.t("learning_dashboard_stability_label", null, "Stability"), advanced.stability ?? "-"],
      [opts.t("learning_dashboard_difficulty_label", null, "Difficulty"), advanced.difficulty ?? "-"]
    ].forEach(([label, value]) => {
      section.appendChild(createNode(opts.doc, "span", "library-advanced-chip", `${label}: ${value}`));
    });
    opts.elements.detailRoot.appendChild(section);
    opts.ensureRuleDetails(opts.item).then((details) => renderAdvancedRules(opts, details));
  }

  function renderAdvancedRules(opts, details) {
    if (model.itemKey(opts.item) !== opts.getSelectedKey() || !opts.isAdvancedEnabled() || !details) {
      return;
    }
    const section = detailSection(opts.doc, opts.t, "learning_dashboard_advanced_rules", "Published rules");
    const rules = Array.isArray(details.rules) ? details.rules : [];
    if (!rules.length) {
      section.appendChild(createNode(opts.doc, "p", "", opts.t("learning_dashboard_no_published_rules", null, "No published rules found.")));
    }
    rules.slice(0, 8).forEach((rule) => {
      section.appendChild(createNode(opts.doc, "p", "", `${rule.source_phrase || "source"} -> ${rule.replacement || ""}`));
    });
    opts.elements.detailRoot.appendChild(section);
  }

  function detailSection(doc, t, key, fallback) {
    const section = doc.createElement("section");
    section.className = "library-detail-section";
    section.appendChild(createNode(doc, "h3", "", t(key, null, fallback)));
    return section;
  }

  function resolveGlosses(result) {
    const glosses = [];
    const seen = new Set();
    for (const value of Array.isArray(result && result.glosses) ? result.glosses : []) {
      const raw = value && typeof value === "object" ? value : { text: value };
      const text = model.normalizeText(raw.text);
      if (!text || seen.has(text.toLowerCase())) {
        continue;
      }
      seen.add(text.toLowerCase());
      glosses.push({
        text,
        details: Array.isArray(raw.details) ? raw.details.map(model.normalizeText).filter(Boolean).slice(0, 2) : []
      });
      if (glosses.length >= 5) {
        break;
      }
    }
    return glosses;
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

  function clearNode(node) {
    while (node && node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function byId(doc, id) {
    const node = doc.getElementById(id);
    if (!node) {
      throw new Error(`Missing Vocabulary Library element: ${id}`);
    }
    return node;
  }

  root.learningDashboardView = {
    clearNode,
    createNode,
    renderDetail,
    resolveElements,
    resolveGlosses
  };
})();
