(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsExposureLog";
  const MAX_ENTRIES = 2000;

  function nowIso() {
    return new Date().toISOString();
  }

  function buildExposure(detail, origin, url, lemmatize) {
    if (!detail) return null;
    const replacement = String(detail.replacement || "");
    const languagePair = String(detail.language_pair || "");
    const lemma = lemmatize ? lemmatize(replacement, languagePair) : replacement.toLowerCase();
    return {
      ts: nowIso(),
      origin: origin || "ruleset",
      lemma,
      replacement,
      original: String(detail.original || ""),
      source_phrase: String(detail.source || ""),
      language_pair: languagePair,
      url: url || ""
    };
  }

  function recordExposureBatch(entries) {
    const payload = (entries || []).filter((entry) => entry && entry.lemma);
    if (!payload.length) {
      return Promise.resolve([]);
    }
    return new Promise((resolve) => {
      try {
        if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
          resolve([]);
          return;
        }
        chrome.storage.local.get({ [STORAGE_KEY]: [] }, (items) => {
          const list = Array.isArray(items[STORAGE_KEY]) ? items[STORAGE_KEY] : [];
          list.push(...payload);
          if (list.length > MAX_ENTRIES) {
            list.splice(0, list.length - MAX_ENTRIES);
          }
          chrome.storage.local.set({ [STORAGE_KEY]: list }, () => resolve(payload));
        });
      } catch (error) {
        resolve([]);
      }
    });
  }

  function recordExposureBatchWithStore(entries) {
    return recordExposureBatch(entries).then((payload) => {
      if (payload.length && root.srsStore && typeof root.srsStore.recordExposureBatch === "function") {
        root.srsStore.recordExposureBatch(payload);
      }
      return payload;
    });
  }

  root.srsMetrics = { buildExposure, recordExposureBatch: recordExposureBatchWithStore };
})();
