(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const LINK_LIMIT = 2;

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function resolvePosLabel(result) {
    const pos = result && result.pos && typeof result.pos === "object" ? result.pos : {};
    return normalizeText(pos.label || pos.canonical);
  }

  function resolveDisplayWord(result, payload) {
    return normalizeText(result && result.display)
      || normalizeText(payload && payload.displayReplacement)
      || normalizeText(payload && payload.replacement);
  }

  function resolveDictionaryTitle(result) {
    const dictionary = result && result.dictionary && typeof result.dictionary === "object"
      ? result.dictionary
      : {};
    return normalizeText(dictionary.title);
  }

  function hasMissingDefinitionData(result) {
    const diagnostics = result && result.diagnostics && typeof result.diagnostics === "object"
      ? result.diagnostics
      : {};
    const providerStatus = normalizeText(diagnostics.provider_status).toLowerCase();
    const missingResources = Array.isArray(diagnostics.missing_resources)
      ? diagnostics.missing_resources
      : [];
    return providerStatus.startsWith("missing_") || missingResources.length > 0;
  }

  function renderLinks(parent, links) {
    const safeLinks = Array.isArray(links) ? links.slice(0, LINK_LIMIT) : [];
    if (!safeLinks.length) {
      return;
    }
    const row = document.createElement("div");
    row.className = "lexishift-definition-links";
    safeLinks.forEach((link) => {
      const url = normalizeText(link && link.url);
      const label = normalizeText(link && link.label) || "Dictionary";
      if (!url) {
        return;
      }
      const anchor = document.createElement("a");
      anchor.className = "lexishift-definition-link";
      anchor.href = url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = `${label} ↗`;
      row.appendChild(anchor);
    });
    if (row.childNodes.length) {
      parent.appendChild(row);
    }
  }

  root.uiQuickDefinitionResultSupport = {
    hasMissingDefinitionData,
    renderLinks,
    resolveDictionaryTitle,
    resolveDisplayWord,
    resolvePosLabel
  };
})();
