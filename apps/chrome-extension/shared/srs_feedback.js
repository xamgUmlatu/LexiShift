(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsFeedbackLog";
  const MAX_ENTRIES = 500;

  function nowIso() {
    return new Date().toISOString();
  }

  function sanitizeEntry(entry) {
    if (!entry || typeof entry !== "object") {
      return null;
    }
    return {
      ts: entry.ts || nowIso(),
      rating: String(entry.rating || ""),
      lemma: String(entry.lemma || ""),
      replacement: String(entry.replacement || ""),
      original: String(entry.original || ""),
      language_pair: entry.language_pair ? String(entry.language_pair) : "",
      source_phrase: entry.source_phrase ? String(entry.source_phrase) : "",
      url: entry.url ? String(entry.url) : ""
    };
  }

  function recordFeedback(entry) {
    const payload = sanitizeEntry(entry);
    if (!payload || !payload.rating) {
      return Promise.resolve(null);
    }
    return new Promise((resolve) => {
      chrome.storage.local.get({ [STORAGE_KEY]: [] }, (items) => {
        const list = Array.isArray(items[STORAGE_KEY]) ? items[STORAGE_KEY] : [];
        list.push(payload);
        if (list.length > MAX_ENTRIES) {
          list.splice(0, list.length - MAX_ENTRIES);
        }
        chrome.storage.local.set({ [STORAGE_KEY]: list }, () => resolve(payload));
      });
    });
  }

  root.srsFeedback = { recordFeedback };
})();
