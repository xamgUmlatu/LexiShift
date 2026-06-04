(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const model = root.learningDashboardModel;
  const view = root.learningDashboardView;

  if (!model || !view) {
    throw new Error("[LexiShift][Vocabulary Library] Missing table dependencies.");
  }

  function createTableSupport(options) {
    const opts = options && typeof options === "object" ? options : {};
    const doc = opts.doc;
    const elements = opts.elements;
    const t = typeof opts.t === "function" ? opts.t : ((_key, _subs, fallback) => fallback);

    function renderTableRows(config) {
      const cfg = config && typeof config === "object" ? config : {};
      const rows = Array.isArray(cfg.rows) ? cfg.rows : [];
      if (!rows.length) {
        renderEmptyRow(cfg.latestData);
        return;
      }
      const pageRows = Array.isArray(cfg.pageRows) ? cfg.pageRows : [];
      pageRows.forEach((item) => {
        elements.tableBody.appendChild(renderItemRow(item));
      });
      cfg.loadMeaningPreviews(pageRows, cfg.token);
    }

    function renderEmptyRow(latestData) {
      const row = doc.createElement("tr");
      const cell = doc.createElement("td");
      cell.colSpan = 6;
      cell.className = "library-empty";
      cell.textContent = latestData
        ? t("learning_dashboard_empty_filtered", null, "No learning words match these filters.")
        : t("learning_dashboard_empty_unloaded", null, "No learning words loaded yet.");
      row.appendChild(cell);
      elements.tableBody.appendChild(row);
    }

    function renderItemRow(item) {
      const key = model.itemKey(item);
      const row = doc.createElement("tr");
      row.className = key === opts.selectedKey() ? "is-selected" : "";
      row.tabIndex = 0;
      row.dataset.itemKey = key;
      row.addEventListener("dblclick", () => opts.selectItem(item));
      row.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }
        event.preventDefault();
        opts.selectItem(item);
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
      cell.textContent = opts.meaningPreviewText(item);
      return cell;
    }

    function actionCell(item) {
      const cell = view.createNode(doc, "td", "library-action-cell");
      if (!opts.canDiscard(item)) {
        return cell;
      }
      const button = view.createNode(doc, "button", "library-discard-button", t("learning_dashboard_discard", null, "Discard"));
      button.type = "button";
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        opts.discardItem(item, button);
      });
      cell.appendChild(button);
      return cell;
    }

    function updateMeaningCell(item) {
      const key = model.itemKey(item);
      elements.tableBody.querySelectorAll("[data-meaning-key]").forEach((cell) => {
        if (cell.dataset.meaningKey === key) {
          cell.textContent = opts.meaningPreviewText(item);
        }
      });
    }

    return {
      renderTableRows,
      updateMeaningCell
    };
  }

  root.learningDashboardTable = {
    createTableSupport
  };
})();
