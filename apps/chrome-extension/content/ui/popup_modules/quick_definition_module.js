(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const GLOSS_LIMIT = 5;
  const SENSE_LIMIT = 5;
  const DETAIL_LIMIT = 2;
  const EXAMPLE_LIMIT = 1;
  const LOOKUP_TIMEOUT_MS = 4000;
  const structuredContent = root.uiQuickDefinitionStructuredContent || {};
  const resultSupport = root.uiQuickDefinitionResultSupport || {};
  const dictionarySections = root.uiQuickDefinitionDictionarySections || {};
  const appendStructuredContent = typeof structuredContent.appendContent === "function"
    ? structuredContent.appendContent : (() => {});
  const normalizeStructuredContent = typeof structuredContent.normalizeContent === "function"
    ? structuredContent.normalizeContent : (() => []);
  const normalizeStructuredNotes = typeof structuredContent.normalizeNotes === "function"
    ? structuredContent.normalizeNotes : (() => []);
  const hasMissingDefinitionData = typeof resultSupport.hasMissingDefinitionData === "function"
    ? resultSupport.hasMissingDefinitionData : (() => false);
  const renderLinks = typeof resultSupport.renderLinks === "function"
    ? resultSupport.renderLinks : (() => {});
  const resolveDictionaryTitle = typeof resultSupport.resolveDictionaryTitle === "function"
    ? resultSupport.resolveDictionaryTitle : (() => "");
  const resolveDisplayWord = typeof resultSupport.resolveDisplayWord === "function"
    ? resultSupport.resolveDisplayWord : ((result, payload) => normalizeText(
        (result && result.display) || (payload && payload.displayReplacement)
      ));
  const resolvePosLabel = typeof resultSupport.resolvePosLabel === "function"
    ? resultSupport.resolvePosLabel : (() => "");
  const readDictionaryPreferences = typeof dictionarySections.readPreferences === "function"
    ? dictionarySections.readPreferences : (async () => ({}));
  const renderDictionarySection = typeof dictionarySections.renderSection === "function"
    ? dictionarySections.renderSection : (() => {});
  const resolveDictionaryResults = typeof dictionarySections.resolveResults === "function"
    ? dictionarySections.resolveResults : (() => []);

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

  function comparableText(value) {
    return normalizeText(value).replace(/\s+/g, " ").toLowerCase();
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

  function normalizeTextList(values, limit) {
    return dedupeTexts(Array.isArray(values) ? values : []).slice(0, limit);
  }

  function normalizeExamples(values) {
    const examples = [];
    const seen = new Set();
    for (const value of Array.isArray(values) ? values : []) {
      const row = value && typeof value === "object" ? value : {};
      const text = normalizeText(row.text);
      const translation = normalizeText(row.translation || row.english);
      if (!text && !translation) {
        continue;
      }
      const key = `${text.toLowerCase()}::${translation.toLowerCase()}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      examples.push({ text, translation });
      if (examples.length >= EXAMPLE_LIMIT) {
        break;
      }
    }
    return examples;
  }

  function resolveGlosses(result) {
    const seen = new Set();
    const glosses = [];
    for (const value of Array.isArray(result && result.glosses) ? result.glosses : []) {
      const raw = value && typeof value === "object" ? value : { text: value };
      const text = normalizeText(raw.text);
      if (!text) {
        continue;
      }
      const key = text.toLowerCase();
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      glosses.push({
        text,
        details: normalizeTextList(raw.details || raw.raw_glosses, DETAIL_LIMIT),
        examples: normalizeExamples(raw.examples)
      });
      if (glosses.length >= GLOSS_LIMIT) {
        break;
      }
    }
    return glosses;
  }

  function resolveSenses(result) {
    const senses = [];
    for (const value of Array.isArray(result && result.senses) ? result.senses : []) {
      const raw = value && typeof value === "object" ? value : {};
      const glosses = dedupeTexts(raw.glosses);
      if (!glosses.length) {
        continue;
      }
      const structuredNotes = normalizeStructuredNotes(raw.structured_notes);
      const structuredSourceTexts = new Set(
        structuredNotes.map((note) => comparableText(note.sourceText))
      );
      senses.push({
        glosses,
        structuredContent: normalizeStructuredContent(raw.structured_content),
        structuredContentTruncated: raw.structured_content_truncated === true,
        details: normalizeTextList(raw.details || raw.notes, DETAIL_LIMIT)
          .filter((detail) => !structuredSourceTexts.has(comparableText(detail))),
        structuredNotes,
        labels: normalizeTextList(raw.labels || raw.tags, 4),
        examples: normalizeExamples(raw.examples)
      });
      if (senses.length >= SENSE_LIMIT) {
        break;
      }
    }
    return senses;
  }

  function appendExamples(parent, examples) {
    for (const example of examples || []) {
      const exampleText = [example.text, example.translation]
        .map(normalizeText)
        .filter(Boolean)
        .join(" / ");
      if (exampleText) {
        appendText(parent, "lexishift-definition-example", exampleText);
      }
    }
  }

  function appendLabels(parent, labels) {
    if (!labels || !labels.length) {
      return;
    }
    const labelRow = document.createElement("div");
    labelRow.className = "lexishift-definition-labels";
    for (const label of labels) {
      const labelNode = document.createElement("span");
      labelNode.className = "lexishift-definition-label";
      labelNode.textContent = label;
      labelRow.appendChild(labelNode);
    }
    parent.appendChild(labelRow);
  }

  function renderSenses(parent, senses) {
    if (senses.some((sense) => sense.structuredContent.length)) {
      const container = document.createElement("div");
      container.className = "lexishift-definition-structured-senses";
      for (const sense of senses) {
        const item = document.createElement("div");
        item.className = "lexishift-definition-structured-sense";
        if (sense.structuredContent.length) {
          appendStructuredContent(
            item,
            sense.structuredContent,
            sense.structuredContentTruncated
          );
        } else {
          appendText(
            item,
            "lexishift-definition-sense-glosses",
            sense.glosses.join(" · ")
          );
        }
        appendLabels(item, sense.labels);
        for (const detail of sense.details || []) {
          appendText(item, "lexishift-definition-detail", detail);
        }
        appendExamples(item, sense.examples);
        container.appendChild(item);
      }
      parent.appendChild(container);
      return;
    }
    const list = document.createElement("ol");
    list.className = "lexishift-definition-senses";
    for (const sense of senses) {
      const item = document.createElement("li");
      item.className = "lexishift-definition-sense";
      appendText(
        item,
        "lexishift-definition-sense-glosses",
        sense.glosses.join(" · ")
      );
      for (const note of sense.structuredNotes || []) {
        for (const noteItem of note.items || []) {
          const row = document.createElement("div");
          row.className = "lexishift-definition-orthography-note";
          const writtenForm = document.createElement("span");
          writtenForm.className = "lexishift-definition-orthography-form";
          writtenForm.textContent = `《${noteItem.writtenForm}》`;
          const text = document.createElement("span");
          text.className = "lexishift-definition-orthography-text";
          text.textContent = noteItem.text;
          row.appendChild(writtenForm);
          row.appendChild(text);
          item.appendChild(row);
        }
      }
      appendLabels(item, sense.labels);
      for (const detail of sense.details || []) {
        appendText(item, "lexishift-definition-detail", detail);
      }
      appendExamples(item, sense.examples);
      list.appendChild(item);
    }
    parent.appendChild(list);
  }

  function renderFlatGlosses(parent, glosses) {
    const list = document.createElement("ul");
    list.className = "lexishift-definition-glosses";
    for (const gloss of glosses) {
      const item = document.createElement("li");
      item.className = "lexishift-definition-gloss-item";
      appendText(item, "lexishift-definition-gloss", gloss.text);
      for (const detail of gloss.details || []) {
        appendText(item, "lexishift-definition-detail", detail);
      }
      appendExamples(item, gloss.examples);
      list.appendChild(item);
    }
    parent.appendChild(list);
  }

  function hasPresentableDefinition(result) {
    return resolveSenses(result).length > 0 || resolveGlosses(result).length > 0;
  }

  function renderDictionaryDefinition(parent, result) {
    const senses = resolveSenses(result);
    const glosses = resolveGlosses(result);
    if (senses.length) {
      renderSenses(parent, senses);
    } else if (glosses.length) {
      renderFlatGlosses(parent, glosses);
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

    async function renderResult(result) {
      const nextBody = document.createElement("div");
      const dictionaryResults = resolveDictionaryResults(result, hasPresentableDefinition);
      if (dictionaryResults.length) {
        const preferences = await readDictionaryPreferences(payload.languagePair);
        const dictionaryList = document.createElement("div");
        dictionaryList.className = "lexishift-definition-dictionaries";
        dictionaryResults.forEach((dictionaryResult, index) => {
          const hasSavedPreference = Object.prototype.hasOwnProperty.call(
            preferences,
            dictionaryResult.disclosureId
          );
          renderDictionarySection(dictionaryList, dictionaryResult, {
            pair: payload.languagePair,
            title: resolveDictionaryTitle(dictionaryResult),
            renderDefinition: renderDictionaryDefinition,
            open: hasSavedPreference
              ? preferences[dictionaryResult.disclosureId] === true
              : index === 0
          });
        });
        nextBody.appendChild(dictionaryList);
      } else {
        const dictionaryTitle = resolveDictionaryTitle(result);
        if (dictionaryTitle) {
          appendText(nextBody, "lexishift-definition-source", dictionaryTitle);
        }
        const senses = resolveSenses(result);
        const glosses = resolveGlosses(result);
        if (senses.length) {
          renderSenses(nextBody, senses);
        } else if (glosses.length) {
          renderFlatGlosses(nextBody, glosses);
        } else {
          appendText(
            nextBody,
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
      }
      renderLinks(nextBody, result && result.external_links);

      word.textContent = resolveDisplayWord(result, payload);
      const posLabel = resolvePosLabel(result, translate);
      pos.textContent = posLabel;
      pos.style.display = posLabel ? "" : "none";
      body.textContent = "";
      Array.from(nextBody.childNodes).forEach((child) => body.appendChild(child));
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
          { timeoutMs: LOOKUP_TIMEOUT_MS, bypassCache: true }
        );
        if (!result || result.status === "error") {
          renderUnavailable(
            translate("popup_definition_error", null, "Failed to load definition.")
          );
          return;
        }
        await renderResult(result);
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
