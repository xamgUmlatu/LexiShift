(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "popupModuleHistoryStore";
  const MAX_ITEMS = 12000;
  const MAX_FEEDBACK_DIGITS = 120;
  const MAX_SENTENCE_WORDS = 15;

  let writeQueue = Promise.resolve();

  function nowIso() {
    return new Date().toISOString();
  }

  function emptyStore() {
    return { version: 1, items: [] };
  }

  function normalizeString(value) {
    return String(value || "").trim();
  }

  function normalizeProfileId(value) {
    return normalizeString(value) || "default";
  }

  function normalizePair(value) {
    return normalizeString(value).toLowerCase();
  }

  function normalizeLemma(value) {
    return normalizeString(value).toLowerCase();
  }

  function buildItemId(profileId, languagePair, lemma) {
    return `${profileId}:${languagePair}:${lemma}`;
  }

  function normalizeRatingDigit(value) {
    const raw = normalizeString(value).toLowerCase();
    if (raw === "1" || raw === "again") return "1";
    if (raw === "2" || raw === "hard") return "2";
    if (raw === "3" || raw === "good") return "3";
    if (raw === "4" || raw === "easy") return "4";
    return "";
  }

  function normalizeSentenceExcerpt(value) {
    const raw = normalizeString(value).replace(/\.{3}/g, " ");
    if (!raw) {
      return "";
    }
    const words = raw.split(/\s+/).filter(Boolean);
    if (!words.length) {
      return "";
    }
    const clipped = words.slice(0, MAX_SENTENCE_WORDS);
    return `... ${clipped.join(" ")} ...`;
  }

  function sanitizeItem(item) {
    if (!item || typeof item !== "object") {
      return null;
    }
    const profileId = normalizeProfileId(item.profile_id);
    const languagePair = normalizePair(item.language_pair);
    const lemma = normalizeLemma(item.lemma);
    if (!profileId || !languagePair || !lemma) {
      return null;
    }
    const feedbackDigits = normalizeString(item.feedback_digits).replace(/[^1-4]/g, "").slice(-MAX_FEEDBACK_DIGITS);
    const feedbackTotal = Number.isFinite(Number(item.feedback_total))
      ? Math.max(0, Number(item.feedback_total))
      : feedbackDigits.length;
    return {
      item_id: buildItemId(profileId, languagePair, lemma),
      profile_id: profileId,
      language_pair: languagePair,
      lemma,
      replacement: normalizeString(item.replacement),
      feedback_digits: feedbackDigits,
      feedback_total: feedbackTotal,
      encounter_count: Number.isFinite(Number(item.encounter_count))
        ? Math.max(0, Number(item.encounter_count))
        : 0,
      last_sentence_excerpt: normalizeSentenceExcerpt(item.last_sentence_excerpt),
      last_seen: normalizeString(item.last_seen)
    };
  }

  function normalizeStore(value) {
    if (!value || typeof value !== "object") {
      return emptyStore();
    }
    const items = Array.isArray(value.items) ? value.items : [];
    const normalizedItems = items
      .map(sanitizeItem)
      .filter(Boolean);
    return {
      version: Number(value.version || 1),
      items: normalizedItems
    };
  }

  function pruneStore(store) {
    const sourceItems = Array.isArray(store.items) ? store.items.slice() : [];
    if (sourceItems.length <= MAX_ITEMS) {
      return store;
    }
    sourceItems.sort((a, b) => {
      const aSeen = normalizeString(a && a.last_seen);
      const bSeen = normalizeString(b && b.last_seen);
      return aSeen.localeCompare(bSeen);
    });
    const trimmed = sourceItems.slice(sourceItems.length - MAX_ITEMS);
    return {
      ...store,
      items: trimmed
    };
  }

  function loadStore() {
    return new Promise((resolve) => {
      try {
        if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
          resolve(emptyStore());
          return;
        }
        chrome.storage.local.get({ [STORAGE_KEY]: emptyStore() }, (items) => {
          resolve(normalizeStore(items[STORAGE_KEY]));
        });
      } catch (_error) {
        resolve(emptyStore());
      }
    });
  }

  function saveStore(store) {
    return new Promise((resolve) => {
      try {
        if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
          resolve(store);
          return;
        }
        const payload = pruneStore(normalizeStore(store));
        chrome.storage.local.set({ [STORAGE_KEY]: payload }, () => resolve(payload));
      } catch (_error) {
        resolve(store);
      }
    });
  }

  function enqueueWrite(task) {
    writeQueue = writeQueue.then(task, task);
    return writeQueue;
  }

  function normalizeFeedbackEntry(entry) {
    const profileId = normalizeProfileId(entry && entry.profile_id);
    const languagePair = normalizePair(entry && entry.language_pair);
    const lemma = normalizeLemma(entry && (entry.lemma || entry.replacement));
    const rating = normalizeRatingDigit(entry && entry.rating);
    if (!languagePair || !lemma || !rating) {
      return null;
    }
    return {
      profile_id: profileId,
      language_pair: languagePair,
      lemma,
      replacement: normalizeString(entry && entry.replacement),
      rating,
      ts: normalizeString(entry && entry.ts) || nowIso()
    };
  }

  function normalizeEncounterEntry(entry) {
    const profileId = normalizeProfileId(entry && entry.profile_id);
    const languagePair = normalizePair(entry && entry.language_pair);
    const lemma = normalizeLemma(entry && (entry.lemma || entry.replacement));
    if (!languagePair || !lemma) {
      return null;
    }
    return {
      profile_id: profileId,
      language_pair: languagePair,
      lemma,
      replacement: normalizeString(entry && entry.replacement),
      sentence_excerpt: normalizeSentenceExcerpt(entry && entry.sentence_excerpt),
      ts: normalizeString(entry && entry.ts) || nowIso()
    };
  }

  function ensureItem(items, payload) {
    const itemId = buildItemId(payload.profile_id, payload.language_pair, payload.lemma);
    const index = items.findIndex((item) => item && item.item_id === itemId);
    if (index >= 0) {
      return index;
    }
    const nextItem = {
      item_id: itemId,
      profile_id: payload.profile_id,
      language_pair: payload.language_pair,
      lemma: payload.lemma,
      replacement: payload.replacement || payload.lemma,
      feedback_digits: "",
      feedback_total: 0,
      encounter_count: 0,
      last_sentence_excerpt: "",
      last_seen: payload.ts || nowIso()
    };
    items.push(nextItem);
    return items.length - 1;
  }

  function applyFeedbackUpdate(items, payload) {
    const index = ensureItem(items, payload);
    const current = sanitizeItem(items[index]) || {
      item_id: buildItemId(payload.profile_id, payload.language_pair, payload.lemma),
      profile_id: payload.profile_id,
      language_pair: payload.language_pair,
      lemma: payload.lemma,
      replacement: payload.replacement || payload.lemma,
      feedback_digits: "",
      feedback_total: 0,
      encounter_count: 0,
      last_sentence_excerpt: "",
      last_seen: payload.ts || nowIso()
    };
    const digits = `${current.feedback_digits || ""}${payload.rating}`.slice(-MAX_FEEDBACK_DIGITS);
    items[index] = {
      ...current,
      replacement: current.replacement || payload.replacement || payload.lemma,
      feedback_digits: digits,
      feedback_total: Number(current.feedback_total || 0) + 1,
      last_seen: payload.ts || nowIso()
    };
  }

  function applyEncounterUpdate(items, payload) {
    const index = ensureItem(items, payload);
    const current = sanitizeItem(items[index]) || {
      item_id: buildItemId(payload.profile_id, payload.language_pair, payload.lemma),
      profile_id: payload.profile_id,
      language_pair: payload.language_pair,
      lemma: payload.lemma,
      replacement: payload.replacement || payload.lemma,
      feedback_digits: "",
      feedback_total: 0,
      encounter_count: 0,
      last_sentence_excerpt: "",
      last_seen: payload.ts || nowIso()
    };
    items[index] = {
      ...current,
      replacement: current.replacement || payload.replacement || payload.lemma,
      encounter_count: Number(current.encounter_count || 0) + 1,
      last_sentence_excerpt: payload.sentence_excerpt || current.last_sentence_excerpt || "",
      last_seen: payload.ts || nowIso()
    };
  }

  function recordFeedback(entry) {
    const payload = normalizeFeedbackEntry(entry);
    if (!payload) {
      return Promise.resolve(null);
    }
    return enqueueWrite(async () => {
      const store = await loadStore();
      const items = Array.isArray(store.items) ? store.items.slice() : [];
      applyFeedbackUpdate(items, payload);
      await saveStore({ ...store, items });
      return payload;
    });
  }

  function recordEncounter(entry) {
    const payload = normalizeEncounterEntry(entry);
    if (!payload) {
      return Promise.resolve(null);
    }
    return enqueueWrite(async () => {
      const store = await loadStore();
      const items = Array.isArray(store.items) ? store.items.slice() : [];
      applyEncounterUpdate(items, payload);
      await saveStore({ ...store, items });
      return payload;
    });
  }

  function recordEncounterBatch(entries) {
    const payload = Array.isArray(entries)
      ? entries.map(normalizeEncounterEntry).filter(Boolean)
      : [];
    if (!payload.length) {
      return Promise.resolve([]);
    }
    return enqueueWrite(async () => {
      const store = await loadStore();
      const items = Array.isArray(store.items) ? store.items.slice() : [];
      for (const entry of payload) {
        applyEncounterUpdate(items, entry);
      }
      await saveStore({ ...store, items });
      return payload;
    });
  }

  async function getHistoryForWord(entry) {
    const profileId = normalizeProfileId(entry && entry.profile_id);
    const languagePair = normalizePair(entry && entry.language_pair);
    const lemma = normalizeLemma(entry && (entry.lemma || entry.replacement));
    if (!languagePair || !lemma) {
      return null;
    }
    await writeQueue.catch(() => {});
    const store = await loadStore();
    const itemId = buildItemId(profileId, languagePair, lemma);
    const found = Array.isArray(store.items)
      ? store.items.find((item) => item && item.item_id === itemId)
      : null;
    return sanitizeItem(found);
  }

  root.popupModuleHistoryStore = {
    loadStore,
    saveStore,
    recordFeedback,
    recordEncounter,
    recordEncounterBatch,
    getHistoryForWord
  };
})();
