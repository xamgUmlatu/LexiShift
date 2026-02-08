(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DB_NAME = "lexishift_profile_media_v1";
  const DB_VERSION = 1;
  const STORE_ASSETS = "assets";
  const INDEX_PROFILE_ID = "by_profile_id";
  const KIND_PROFILE_BACKGROUND = "profile_background";

  let dbPromise = null;

  function requireIndexedDb() {
    if (!globalThis.indexedDB) {
      throw new Error("IndexedDB is unavailable in this context.");
    }
  }

  function openDb() {
    requireIndexedDb();
    if (dbPromise) {
      return dbPromise;
    }
    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_ASSETS)) {
          const store = db.createObjectStore(STORE_ASSETS, { keyPath: "asset_id" });
          store.createIndex(INDEX_PROFILE_ID, "profile_id", { unique: false });
          return;
        }
        const store = request.transaction.objectStore(STORE_ASSETS);
        if (!store.indexNames.contains(INDEX_PROFILE_ID)) {
          store.createIndex(INDEX_PROFILE_ID, "profile_id", { unique: false });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Failed to open media store."));
      request.onblocked = () => reject(new Error("Media store upgrade is blocked by another open tab."));
    });
    return dbPromise;
  }

  async function withStore(mode, fn) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_ASSETS, mode);
      const store = tx.objectStore(STORE_ASSETS);
      let result;
      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(tx.error || new Error("IndexedDB transaction failed."));
      tx.onabort = () => reject(tx.error || new Error("IndexedDB transaction aborted."));
      Promise.resolve()
        .then(() => fn(store))
        .then((value) => {
          result = value;
        })
        .catch((error) => {
          try {
            tx.abort();
          } catch (_ignored) {}
          reject(error);
        });
    });
  }

  function requestToPromise(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("IndexedDB request failed."));
    });
  }

  function normalizeProfileId(value) {
    const normalized = String(value || "").trim();
    return normalized || "default";
  }

  function normalizeAssetId(value) {
    return String(value || "").trim();
  }

  function ensureBlob(blob) {
    if (blob instanceof Blob) {
      return blob;
    }
    throw new Error("Expected a Blob.");
  }

  function nextAssetId(profileId, kind) {
    const stamp = Date.now().toString(36);
    const nonce = Math.random().toString(36).slice(2, 10);
    return `${profileId}:${kind}:${stamp}:${nonce}`;
  }

  function toAssetMeta(record) {
    if (!record || typeof record !== "object") {
      return null;
    }
    return {
      asset_id: String(record.asset_id || ""),
      profile_id: String(record.profile_id || "default"),
      kind: String(record.kind || ""),
      mime_type: String(record.mime_type || ""),
      byte_size: Number(record.byte_size || 0),
      created_at: String(record.created_at || ""),
      updated_at: String(record.updated_at || "")
    };
  }

  async function putAsset(record) {
    if (!record || typeof record !== "object") {
      throw new Error("Invalid media asset record.");
    }
    return withStore("readwrite", (store) => requestToPromise(store.put(record)));
  }

  async function getAsset(assetId) {
    const normalizedAssetId = normalizeAssetId(assetId);
    if (!normalizedAssetId) {
      return null;
    }
    const record = await withStore("readonly", (store) => requestToPromise(store.get(normalizedAssetId)));
    return record && typeof record === "object" ? record : null;
  }

  async function getAssetMeta(assetId) {
    const record = await getAsset(assetId);
    return toAssetMeta(record);
  }

  async function deleteAsset(assetId) {
    const normalizedAssetId = normalizeAssetId(assetId);
    if (!normalizedAssetId) {
      return;
    }
    await withStore("readwrite", (store) => requestToPromise(store.delete(normalizedAssetId)));
  }

  async function listAssetMetasForProfile(profileId, kind) {
    const normalizedProfileId = normalizeProfileId(profileId);
    const kindFilter = kind ? String(kind).trim() : "";
    const records = await withStore("readonly", async (store) => {
      const index = store.index(INDEX_PROFILE_ID);
      const range = IDBKeyRange.only(normalizedProfileId);
      const rows = await requestToPromise(index.getAll(range));
      return Array.isArray(rows) ? rows : [];
    });
    const metas = records
      .filter((record) => {
        if (!kindFilter) {
          return true;
        }
        return String(record && record.kind || "") === kindFilter;
      })
      .map(toAssetMeta)
      .filter(Boolean)
      .sort((a, b) => {
        const left = String(a.updated_at || a.created_at || "");
        const right = String(b.updated_at || b.created_at || "");
        return left < right ? 1 : (left > right ? -1 : 0);
      });
    return metas;
  }

  async function deleteProfileAssets(profileId, options) {
    const opts = options && typeof options === "object" ? options : {};
    const keepAssetId = normalizeAssetId(opts.keepAssetId);
    const kindFilter = opts.kind ? String(opts.kind).trim() : "";
    const metas = await listAssetMetasForProfile(profileId, kindFilter);
    const targets = metas.filter((meta) => meta.asset_id && meta.asset_id !== keepAssetId);
    if (!targets.length) {
      return 0;
    }
    await Promise.all(targets.map((meta) => deleteAsset(meta.asset_id)));
    return targets.length;
  }

  async function upsertProfileBackground(profileId, blob, options) {
    const opts = options && typeof options === "object" ? options : {};
    const normalizedProfileId = normalizeProfileId(profileId);
    const mediaBlob = ensureBlob(blob);
    const previousAssetId = normalizeAssetId(opts.previousAssetId);
    const nowIso = new Date().toISOString();
    const assetId = nextAssetId(normalizedProfileId, KIND_PROFILE_BACKGROUND);
    const record = {
      asset_id: assetId,
      profile_id: normalizedProfileId,
      kind: KIND_PROFILE_BACKGROUND,
      mime_type: String(opts.mimeType || mediaBlob.type || "application/octet-stream"),
      byte_size: Number(mediaBlob.size || 0),
      created_at: nowIso,
      updated_at: nowIso,
      blob: mediaBlob
    };
    await putAsset(record);
    if (previousAssetId && previousAssetId !== assetId) {
      await deleteAsset(previousAssetId);
    }
    await deleteProfileAssets(normalizedProfileId, {
      kind: KIND_PROFILE_BACKGROUND,
      keepAssetId: assetId
    });
    return toAssetMeta(record);
  }

  root.profileMediaStore = {
    KIND_PROFILE_BACKGROUND,
    openDb,
    getAsset,
    getAssetMeta,
    putAsset,
    deleteAsset,
    listAssetMetasForProfile,
    deleteProfileAssets,
    upsertProfileBackground
  };
})();
