(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsFeedbackLog";
  const MAX_ENTRIES = 500;

  function nowIso() {
    return new Date().toISOString();
  }

  function parseWordPackage(value) {
    if (!value) {
      return null;
    }
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (!parsed || typeof parsed !== "object") {
        return null;
      }
      return parsed;
    } catch (_error) {
      return null;
    }
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
      origin: String(entry.origin || "srs"),
      language_pair: entry.language_pair ? String(entry.language_pair) : "",
      profile_id: entry.profile_id ? String(entry.profile_id) : "default",
      source_phrase: entry.source_phrase ? String(entry.source_phrase) : "",
      url: entry.url ? String(entry.url) : "",
      word_package: parseWordPackage(entry.word_package || null)
    };
  }

  function buildEntryFromSpan(target, rating, url) {
    if (!target) {
      return null;
    }
    return {
      rating,
      lemma: String(target.dataset.replacement || target.textContent || ""),
      replacement: String(target.dataset.replacement || target.textContent || ""),
      original: String(target.dataset.original || ""),
      origin: String(target.dataset.origin || "ruleset"),
      language_pair: target.dataset.languagePair || "",
      source_phrase: target.dataset.source || "",
      url: url || (window.location ? window.location.href : ""),
      word_package: parseWordPackage(target.dataset.wordPackage || null)
    };
  }

  function recordFeedback(entry) {
    const payload = sanitizeEntry(entry);
    if (!payload || !payload.rating) {
      return Promise.resolve(null);
    }
    return new Promise((resolve) => {
      try {
        if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
          resolve(null);
          return;
        }
        chrome.storage.local.get({ [STORAGE_KEY]: [] }, (items) => {
          const list = Array.isArray(items[STORAGE_KEY]) ? items[STORAGE_KEY] : [];
          list.push(payload);
          if (list.length > MAX_ENTRIES) {
            list.splice(0, list.length - MAX_ENTRIES);
          }
          chrome.storage.local.set({ [STORAGE_KEY]: list }, () => resolve(payload));
        });
      } catch (error) {
        resolve(null);
      }
    });
  }

  function recordFeedbackWithStore(entry) {
    return recordFeedback(entry).then((payload) => {
      if (payload && root.srsStore && typeof root.srsStore.recordFeedback === "function") {
        root.srsStore.recordFeedback(payload);
      }
      return payload;
    });
  }

  root.srsFeedback = { recordFeedback: recordFeedbackWithStore, buildEntryFromSpan };
})();
