(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsStore";
  const MAX_ITEMS = 8000;
  const MAX_HISTORY = 50;

  function nowIso() {
    return new Date().toISOString();
  }

  function emptyStore() {
    return { version: 1, items: [] };
  }

  function normalizeStore(value) {
    if (!value || typeof value !== "object") return emptyStore();
    const items = Array.isArray(value.items) ? value.items : [];
    return { version: Number(value.version || 1), items };
  }

  function buildItemId(languagePair, lemma) {
    return `${languagePair}:${lemma}`;
  }

  function ensureItem(store, entry) {
    const lemma = String(entry.lemma || "").trim();
    const languagePair = String(entry.language_pair || "").trim();
    if (!lemma || !languagePair) return [store, null];

    const itemId = buildItemId(languagePair, lemma);
    const items = Array.isArray(store.items) ? store.items.slice() : [];
    const index = items.findIndex((item) => item && item.item_id === itemId);
    if (index >= 0) {
      return [{ ...store, items }, items[index]];
    }
    const created = {
      item_id: itemId,
      lemma,
      language_pair: languagePair,
      source_type: entry.source_type || entry.origin || "extension",
      exposures: 0,
      srs_history: []
    };
    items.push(created);
    return [{ ...store, items }, created];
  }

  function pruneStore(store) {
    const items = Array.isArray(store.items) ? store.items.slice() : [];
    if (items.length <= MAX_ITEMS) return store;
    items.sort((a, b) => {
      const aTs = a && a.last_seen ? String(a.last_seen) : "";
      const bTs = b && b.last_seen ? String(b.last_seen) : "";
      return aTs.localeCompare(bTs);
    });
    const trimmed = items.slice(Math.max(0, items.length - MAX_ITEMS));
    return { ...store, items: trimmed };
  }

  function clampHistory(item) {
    const history = Array.isArray(item.srs_history) ? item.srs_history.slice() : [];
    if (history.length <= MAX_HISTORY) return item;
    return { ...item, srs_history: history.slice(history.length - MAX_HISTORY) };
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
      } catch (error) {
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
        const payload = pruneStore(store);
        chrome.storage.local.set({ [STORAGE_KEY]: payload }, () => resolve(payload));
      } catch (error) {
        resolve(store);
      }
    });
  }

  async function recordExposure(entry) {
    const payload = entry && entry.lemma ? entry : null;
    if (!payload) return null;
    const store = await loadStore();
    const [updatedStore, item] = ensureItem(store, payload);
    if (!item) return null;
    const items = updatedStore.items.slice();
    const idx = items.findIndex((value) => value && value.item_id === item.item_id);
    if (idx >= 0) {
      items[idx] = clampHistory({
        ...items[idx],
        exposures: Number(items[idx].exposures || 0) + 1,
        last_seen: payload.ts || nowIso()
      });
    }
    return saveStore({ ...updatedStore, items });
  }

  async function recordExposureBatch(entries) {
    const list = Array.isArray(entries) ? entries.filter((entry) => entry && entry.lemma) : [];
    if (!list.length) return [];
    let store = await loadStore();
    let items = Array.isArray(store.items) ? store.items.slice() : [];

    for (const entry of list) {
      const [nextStore, item] = ensureItem({ ...store, items }, entry);
      store = nextStore;
      items = Array.isArray(store.items) ? store.items.slice() : [];
      if (!item) continue;
      const idx = items.findIndex((value) => value && value.item_id === item.item_id);
      if (idx >= 0) {
        items[idx] = clampHistory({
          ...items[idx],
          exposures: Number(items[idx].exposures || 0) + 1,
          last_seen: entry.ts || nowIso()
        });
      }
    }
    store = { ...store, items };
    await saveStore(store);
    return list;
  }

  async function recordFeedback(entry) {
    const payload = entry && entry.rating && entry.lemma ? entry : null;
    if (!payload) return null;
    const store = await loadStore();
    const [updatedStore, item] = ensureItem(store, payload);
    if (!item) return null;
    const items = updatedStore.items.slice();
    const idx = items.findIndex((value) => value && value.item_id === item.item_id);
    if (idx >= 0) {
      const history = Array.isArray(items[idx].srs_history) ? items[idx].srs_history.slice() : [];
      history.push({ ts: payload.ts || nowIso(), rating: String(payload.rating || "") });
      items[idx] = clampHistory({
        ...items[idx],
        exposures: Number(items[idx].exposures || 0) + 1,
        last_seen: payload.ts || nowIso(),
        srs_history: history
      });
    }
    return saveStore({ ...updatedStore, items });
  }

  root.srsStore = {
    loadStore,
    saveStore,
    recordExposure,
    recordExposureBatch,
    recordFeedback
  };
})();
