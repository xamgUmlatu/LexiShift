(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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

  function renderRuleDetails(doc, item, options) {
    const opts = options && typeof options === "object" ? options : {};
    const key = typeof opts.ruleDetailKey === "function" ? opts.ruleDetailKey(item) : "";
    const expandedKeys = opts.expandedKeys instanceof Set ? opts.expandedKeys : new Set();
    if (!key || !expandedKeys.has(key)) {
      return null;
    }
    const loadingKeys = opts.loadingKeys instanceof Set ? opts.loadingKeys : new Set();
    const detailsByKey = opts.detailsByKey instanceof Map ? opts.detailsByKey : new Map();
    const rootNode = createNode(doc, "div", "srs-word-rule-details");
    if (loadingKeys.has(key)) {
      rootNode.appendChild(createNode(doc, "p", "", "Loading rule details..."));
      return rootNode;
    }
    const details = detailsByKey.get(key);
    if (!details || typeof details !== "object") {
      rootNode.appendChild(createNode(doc, "p", "", "Rule details are not loaded yet."));
      return rootNode;
    }
    if (details.load_error) {
      rootNode.appendChild(createNode(doc, "p", "", `Rule details unavailable: ${details.load_error}`));
      return rootNode;
    }
    const rules = Array.isArray(details.rules) ? details.rules : [];
    const total = Number(details.rule_count || rules.length || 0);
    const returned = Number(details.returned_rule_count || rules.length || 0);
    const suffix = details.truncated ? `, capped at ${Number(details.limit || returned)}` : "";
    rootNode.appendChild(createNode(
      doc,
      "p",
      "srs-word-rule-details-summary",
      total
        ? `Showing ${returned} of ${total} published rules${suffix}.`
        : "No published rules found for this word."
    ));
    rules.forEach((rule) => {
      rootNode.appendChild(renderRuleDetailRow(doc, rule, Boolean(opts.advancedEnabled)));
    });
    return rootNode;
  }

  function renderRuleDetailRow(doc, rule, advancedEnabled) {
    const row = createNode(doc, "div", "srs-word-rule-detail-row");
    const source = String(rule && rule.source_phrase ? rule.source_phrase : "source");
    const replacement = String(rule && rule.replacement ? rule.replacement : "");
    row.appendChild(createNode(doc, "span", "srs-word-rule-detail-source", `${source} -> ${replacement}`));
    const meta = [
      rule && rule.enabled === false ? "Disabled" : "Enabled",
      `Priority ${Number(rule && rule.priority ? rule.priority : 0)}`,
      `Case ${String(rule && rule.case_policy ? rule.case_policy : "match")}`
    ];
    const metadata = rule && typeof rule.metadata === "object" ? rule.metadata : {};
    if (metadata.confidence !== undefined && metadata.confidence !== null) {
      meta.push(`Confidence ${metadata.confidence}`);
    }
    if (Array.isArray(rule && rule.tags) && rule.tags.length) {
      meta.push(`Tags ${rule.tags.join(", ")}`);
    }
    row.appendChild(createNode(doc, "span", "srs-word-rule-detail-meta", meta.join(" | ")));
    if (advancedEnabled) {
      const advanced = renderRuleDetailAdvanced(doc, metadata);
      if (advanced) {
        row.appendChild(advanced);
      }
    }
    return row;
  }

  function renderRuleDetailAdvanced(doc, metadata) {
    const parts = [];
    if (metadata.source_type) {
      parts.push(`Source type: ${metadata.source_type}`);
    }
    if (metadata.source) {
      parts.push(`Source: ${metadata.source}`);
    }
    if (metadata.language_pair) {
      parts.push(`Pair: ${metadata.language_pair}`);
    }
    if (metadata.word_package && typeof metadata.word_package === "object") {
      const wordPackage = metadata.word_package;
      if (wordPackage.pos_canonical || wordPackage.pos) {
        parts.push(`POS: ${wordPackage.pos_canonical || wordPackage.pos}`);
      }
      if (wordPackage.source_provider) {
        parts.push(`Provider: ${wordPackage.source_provider}`);
      }
    }
    if (!parts.length) {
      return null;
    }
    const advanced = createNode(doc, "span", "srs-word-rule-detail-advanced");
    parts.forEach((part) => {
      advanced.appendChild(createNode(doc, "span", "", part));
    });
    return advanced;
  }

  root.optionsSrsWordsDashboardRuleDetails = {
    renderRuleDetails
  };
})();
