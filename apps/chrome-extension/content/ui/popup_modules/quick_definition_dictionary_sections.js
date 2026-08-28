(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DISCLOSURE_PREFS_KEY = "lexishift_definition_dictionary_disclosure_v1";
  const styles = `
    .lexishift-definition-dictionaries{display:flex;flex-direction:column;gap:5px;}
    .lexishift-definition-dictionary{border-top:1px solid var(--lexishift-module-quote-border, rgba(247,244,239,0.16));}
    .lexishift-definition-dictionary:first-child{border-top:0;}
    .lexishift-definition-dictionary-toggle{display:flex;align-items:center;gap:6px;width:100%;padding:4px 0 2px;
      border:0;background:transparent;color:inherit;cursor:pointer;text-align:left;font:inherit;}
    .lexishift-definition-dictionary-toggle:focus-visible{outline:2px solid currentColor;outline-offset:2px;border-radius:3px;}
    .lexishift-definition-dictionary-arrow{width:0;height:0;flex:0 0 auto;
      border-top:4px solid transparent;border-bottom:4px solid transparent;
      border-left:6px solid var(--lexishift-module-label, rgba(247,244,239,0.72));
      transform:rotate(0deg);transform-origin:45% 50%;transition:transform 180ms ease;}
    .lexishift-definition-dictionary.is-open .lexishift-definition-dictionary-arrow{transform:rotate(90deg);}
    .lexishift-definition-dictionary-title{min-width:0;font-size:10px;line-height:1.35;font-weight:750;
      letter-spacing:0.035em;color:var(--lexishift-module-label, rgba(247,244,239,0.78));word-break:break-word;}
    .lexishift-definition-dictionary-panel{display:grid;grid-template-rows:0fr;opacity:0;
      transition:grid-template-rows 180ms ease,opacity 140ms ease;pointer-events:none;}
    .lexishift-definition-dictionary.is-open .lexishift-definition-dictionary-panel{
      grid-template-rows:1fr;opacity:1;pointer-events:auto;}
    .lexishift-definition-dictionary-panel-inner{min-height:0;overflow:hidden;display:flex;flex-direction:column;gap:5px;padding:2px 0 3px;}
  `;
  let disclosureSaveQueue = Promise.resolve();

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizePair(value) {
    return normalizeText(value).toLowerCase();
  }

  function dictionaryResultId(result, index) {
    const dictionary = result && result.dictionary && typeof result.dictionary === "object"
      ? result.dictionary
      : {};
    return normalizeText(result && result.source_id)
      || normalizeText(dictionary.pack_id)
      || normalizeText(dictionary.provider)
      || normalizeText(dictionary.title)
      || `dictionary-${index + 1}`;
  }

  function resolveResults(result, hasPresentableDefinition) {
    const rawResults = Array.isArray(result && result.dictionary_results)
      ? result.dictionary_results
      : [];
    const isPresentable = typeof hasPresentableDefinition === "function"
      ? hasPresentableDefinition
      : (() => false);
    const results = [];
    rawResults.forEach((value, index) => {
      const entry = value && typeof value === "object" ? value : {};
      if (!isPresentable(entry)) {
        return;
      }
      results.push({
        ...entry,
        disclosureId: dictionaryResultId(entry, index)
      });
    });
    return results;
  }

  function disclosureStorage() {
    try {
      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        return chrome.storage.local;
      }
    } catch (_error) {
      // Treat unavailable extension storage as an ephemeral preference.
    }
    return null;
  }

  function readDisclosureStore() {
    const storage = disclosureStorage();
    if (!storage || typeof storage.get !== "function") {
      return Promise.resolve({ version: 1, by_pair: {} });
    }
    return new Promise((resolve) => {
      storage.get({ [DISCLOSURE_PREFS_KEY]: { version: 1, by_pair: {} } }, (items) => {
        const value = items && items[DISCLOSURE_PREFS_KEY];
        resolve(value && typeof value === "object"
          ? value
          : { version: 1, by_pair: {} });
      });
    });
  }

  async function readPreferences(pair) {
    const store = await readDisclosureStore();
    const byPair = store.by_pair && typeof store.by_pair === "object" ? store.by_pair : {};
    const preferences = byPair[normalizePair(pair)];
    return preferences && typeof preferences === "object" ? { ...preferences } : {};
  }

  function savePreference(pair, dictionaryId, open) {
    const normalizedPair = normalizePair(pair);
    const normalizedId = normalizeText(dictionaryId);
    const storage = disclosureStorage();
    if (!normalizedPair || !normalizedId || !storage || typeof storage.set !== "function") {
      return Promise.resolve();
    }
    disclosureSaveQueue = disclosureSaveQueue.then(async () => {
      const store = await readDisclosureStore();
      const byPair = store.by_pair && typeof store.by_pair === "object"
        ? { ...store.by_pair }
        : {};
      const pairPreferences = byPair[normalizedPair]
        && typeof byPair[normalizedPair] === "object"
        ? { ...byPair[normalizedPair] }
        : {};
      pairPreferences[normalizedId] = open === true;
      byPair[normalizedPair] = pairPreferences;
      await new Promise((resolve) => {
        storage.set({
          [DISCLOSURE_PREFS_KEY]: {
            version: 1,
            by_pair: byPair
          }
        }, resolve);
      });
    }).catch(() => {});
    return disclosureSaveQueue;
  }

  function renderSection(parent, result, options) {
    const opts = options && typeof options === "object" ? options : {};
    const section = document.createElement("section");
    section.className = "lexishift-definition-dictionary";
    section.dataset.dictionaryId = result.disclosureId;

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "lexishift-definition-dictionary-toggle";
    const arrow = document.createElement("span");
    arrow.className = "lexishift-definition-dictionary-arrow";
    arrow.setAttribute("aria-hidden", "true");
    const title = document.createElement("span");
    title.className = "lexishift-definition-dictionary-title";
    title.textContent = normalizeText(opts.title) || "Dictionary";
    toggle.appendChild(arrow);
    toggle.appendChild(title);

    const panel = document.createElement("div");
    panel.className = "lexishift-definition-dictionary-panel";
    const panelInner = document.createElement("div");
    panelInner.className = "lexishift-definition-dictionary-panel-inner";
    if (typeof opts.renderDefinition === "function") {
      opts.renderDefinition(panelInner, result);
    }
    panel.appendChild(panelInner);
    section.appendChild(toggle);
    section.appendChild(panel);
    parent.appendChild(section);

    let open = opts.open === true;
    function setOpen(nextOpen, persist) {
      open = nextOpen === true;
      section.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      panel.setAttribute("aria-hidden", open ? "false" : "true");
      panelInner.inert = !open;
      if (persist) {
        savePreference(opts.pair, result.disclosureId, open);
      }
    }

    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(!open, true);
    });
    setOpen(open, false);
  }

  root.uiQuickDefinitionDictionarySections = {
    readPreferences,
    renderSection,
    resolveResults,
    styles
  };
})();
