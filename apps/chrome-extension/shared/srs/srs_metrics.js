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
      url: url || "",
      word_package: detail.word_package && typeof detail.word_package === "object"
        ? detail.word_package
        : null
    };
  }

  function normalizeExposurePayload(entries) {
    return (entries || []).filter((entry) => entry && entry.lemma);
  }

  function recordExposureBatch(entries) {
    const payload = normalizeExposurePayload(entries);
    if (!payload.length) {
      return Promise.resolve([]);
    }
    return new Promise((resolve) => {
      try {
        if (
          typeof chrome === "undefined"
          || !chrome.storage
          || !chrome.runtime
          || !chrome.runtime.id
        ) {
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

  function recordExposureBatchWithStore(entries, options) {
    const opts = options && typeof options === "object" ? options : {};
    const payload = normalizeExposurePayload(entries);
    if (!payload.length) {
      return Promise.resolve([]);
    }
    const shouldRecordLocalExposure = opts.recordLocalExposureLog !== false;
    const localWrite = shouldRecordLocalExposure
      ? recordExposureBatch(payload)
      : Promise.resolve([]);
    return localWrite.then((savedPayload) => {
      if (
        shouldRecordLocalExposure
        && savedPayload.length
        && root.srsStore
        && typeof root.srsStore.recordExposureBatch === "function"
      ) {
        root.srsStore.recordExposureBatch(savedPayload);
      }
      if (
        payload.length
        && opts.browsingAdmissionSignals
        && typeof opts.browsingAdmissionSignals.recordExposureBatch === "function"
        && opts.settings
        && opts.settings.srsBrowsingAdmissionSignalsEnabled === true
      ) {
        opts.browsingAdmissionSignals.recordExposureBatch(payload, opts.settings).catch((error) => {
          if (opts.settings.debugEnabled && typeof opts.log === "function") {
            opts.log("Failed to queue browsing-admission signals.", error);
          }
        });
      }
      return savedPayload;
    });
  }

  root.srsMetrics = { buildExposure, recordExposureBatch: recordExposureBatchWithStore };
})();
