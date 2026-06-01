(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const GLOSS_LIMIT = 3;
  const LINK_LIMIT = 2;
  const LOOKUP_TIMEOUT_MS = 4000;

  function t(key, substitutions, fallback) {
    try {
      if (typeof chrome !== "undefined"
        && chrome.i18n
        && typeof chrome.i18n.getMessage === "function") {
        const message = chrome.i18n.getMessage(key, substitutions);
        if (message) {
          return message;
        }
      }
    } catch (_error) {
      // Ignore i18n runtime errors and return fallback.
    }
    return String(fallback || key || "");
  }

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizePair(value) {
    return normalizeText(value).toLowerCase();
  }

  function parseObjectJson(value) {
    const text = normalizeText(value);
    if (!text) {
      return null;
    }
    try {
      const parsed = JSON.parse(text);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? parsed
        : null;
    } catch (_error) {
      return null;
    }
  }

  function parseTargetPayload(target) {
    if (!target || !target.dataset) {
      return null;
    }
    const languagePair = normalizePair(target.dataset.languagePair);
    const replacement = normalizeText(
      target.dataset.replacement
      || target.dataset.displayReplacement
      || target.textContent
    );
    const displayReplacement = normalizeText(
      target.dataset.displayReplacement
      || target.dataset.replacement
      || target.textContent
    );
    if (!languagePair || !replacement) {
      return null;
    }
    return {
      languagePair,
      replacement,
      displayReplacement,
      origin: normalizeText(target.dataset.origin).toLowerCase(),
      sourcePhrase: normalizeText(target.dataset.source),
      wordPackage: parseObjectJson(target.dataset.wordPackage)
    };
  }

  function resolveWordInfoApi(context) {
    const ctx = context && typeof context === "object" ? context : {};
    if (ctx.wordInfo && typeof ctx.wordInfo.lookup === "function") {
      return ctx.wordInfo;
    }
    if (ctx.wordInfoApi && typeof ctx.wordInfoApi.lookup === "function") {
      return ctx.wordInfoApi;
    }
    if (root.wordInfoApi && typeof root.wordInfoApi.lookup === "function") {
      return root.wordInfoApi;
    }
    return null;
  }

  function appendText(parent, className, text) {
    const node = document.createElement("div");
    node.className = className;
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function dedupeTexts(values) {
    const seen = new Set();
    const texts = [];
    for (const value of Array.isArray(values) ? values : []) {
      const text = normalizeText(value && typeof value === "object" ? value.text : value);
      if (!text) {
        continue;
      }
      const key = text.toLowerCase();
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      texts.push(text);
    }
    return texts;
  }

  function resolveGlosses(result) {
    return dedupeTexts(result && result.glosses).slice(0, GLOSS_LIMIT);
  }

  function resolveSourcePhrase(result, payload) {
    const fromResult = Array.isArray(result && result.source_phrases)
      ? dedupeTexts(result.source_phrases)[0]
      : "";
    return fromResult || payload.sourcePhrase || "";
  }

  function resolvePosLabel(result) {
    const pos = result && result.pos && typeof result.pos === "object" ? result.pos : {};
    return normalizeText(pos.label || pos.canonical);
  }

  function resolveDisplayWord(result, payload) {
    return normalizeText(result && result.display)
      || normalizeText(payload.displayReplacement)
      || normalizeText(payload.replacement);
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
      anchor.textContent = label;
      row.appendChild(anchor);
    });
    if (row.childNodes.length) {
      parent.appendChild(row);
    }
  }

  function build(target, debugLog, context) {
    const ctx = context && typeof context === "object" ? context : {};
    const translate = typeof ctx.t === "function" ? ctx.t : t;
    const payload = parseTargetPayload(target);
    if (!payload) {
      if (typeof debugLog === "function") {
        debugLog("Skipping quick-definition module: target payload missing.");
      }
      return null;
    }

    const moduleEl = document.createElement("section");
    moduleEl.className = "lexishift-popup-module lexishift-definition-module";

    const header = document.createElement("div");
    header.className = "lexishift-definition-header";
    const word = document.createElement("div");
    word.className = "lexishift-definition-word";
    word.textContent = payload.displayReplacement || payload.replacement;
    const pos = document.createElement("div");
    pos.className = "lexishift-definition-pos";
    header.appendChild(word);
    header.appendChild(pos);

    const body = document.createElement("div");
    body.className = "lexishift-definition-body";
    appendText(
      body,
      "lexishift-definition-status",
      translate("popup_definition_loading", null, "Loading definition...")
    );
    moduleEl.appendChild(header);
    moduleEl.appendChild(body);

    function renderUnavailable(message) {
      body.textContent = "";
      appendText(body, "lexishift-definition-status", message);
    }

    function renderResult(result) {
      body.textContent = "";
      word.textContent = resolveDisplayWord(result, payload);
      const posLabel = resolvePosLabel(result);
      pos.textContent = posLabel;
      pos.style.display = posLabel ? "" : "none";

      const glosses = resolveGlosses(result);
      const sourcePhrase = resolveSourcePhrase(result, payload);
      if (sourcePhrase) {
        appendText(
          body,
          "lexishift-definition-match",
          translate("popup_definition_match", [sourcePhrase], `Matches: ${sourcePhrase}`)
        );
      }

      if (glosses.length) {
        const list = document.createElement("div");
        list.className = "lexishift-definition-glosses";
        for (const gloss of glosses) {
          appendText(list, "lexishift-definition-gloss", gloss);
        }
        body.appendChild(list);
      } else {
        appendText(
          body,
          "lexishift-definition-status",
          hasMissingDefinitionData(result)
            ? translate(
                "popup_definition_missing",
                null,
                "Definition data is not installed for this word."
              )
            : translate("popup_definition_unavailable", null, "No definition available.")
        );
      }
      renderLinks(body, result && result.external_links);
    }

    async function loadDefinition() {
      const api = resolveWordInfoApi(ctx);
      if (!api) {
        renderUnavailable(translate("popup_definition_unavailable", null, "No definition available."));
        return;
      }
      try {
        const result = await api.lookup(
          {
            languagePair: payload.languagePair,
            profileId: ctx.profileId,
            replacement: payload.replacement,
            displayReplacement: payload.displayReplacement,
            origin: payload.origin,
            sourcePhrase: payload.sourcePhrase,
            wordPackage: payload.wordPackage || undefined
          },
          { timeoutMs: LOOKUP_TIMEOUT_MS }
        );
        if (!result || result.status === "error") {
          renderUnavailable(translate("popup_definition_unavailable", null, "No definition available."));
          return;
        }
        renderResult(result);
      } catch (error) {
        renderUnavailable(translate("popup_definition_error", null, "Failed to load definition."));
        if (typeof debugLog === "function") {
          debugLog("Failed to load quick-definition module.", {
            message: error && error.message ? error.message : String(error),
            languagePair: payload.languagePair,
            replacement: payload.replacement
          });
        }
      }
    }

    Promise.resolve(loadDefinition());
    return moduleEl;
  }

  root.uiQuickDefinitionModule = {
    build,
    parseTargetPayload
  };
})();
