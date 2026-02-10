(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const RULESET_KEY = "helperRulesetCache";
  const SNAPSHOT_KEY = "helperSnapshotCache";
  const DEFAULT_PROFILE_ID = "default";

  function normalizeProfileId(value) {
    const normalized = String(value || "").trim();
    return normalized || DEFAULT_PROFILE_ID;
  }

  function scopedKey(pair, options) {
    const normalizedPair = String(pair || "").trim();
    const opts = options && typeof options === "object" ? options : {};
    const profileId = normalizeProfileId(opts.profileId);
    return `${profileId}::${normalizedPair}`;
  }

  function readKey(key) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.storage || !chrome.storage.local) {
        resolve({});
        return;
      }
      chrome.storage.local.get({ [key]: {} }, (items) => {
        resolve(items && items[key] ? items[key] : {});
      });
    });
  }

  function writeKey(key, value) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.storage || !chrome.storage.local) {
        resolve();
        return;
      }
      chrome.storage.local.set({ [key]: value }, () => resolve());
    });
  }

  async function saveRuleset(pair, ruleset, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return;
    const cache = await readKey(RULESET_KEY);
    cache[key] = { saved_at: new Date().toISOString(), data: ruleset };
    await writeKey(RULESET_KEY, cache);
  }

  async function loadRuleset(pair, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return null;
    const cache = await readKey(RULESET_KEY);
    return cache[key] ? cache[key].data : null;
  }

  async function saveSnapshot(pair, snapshot, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return;
    const cache = await readKey(SNAPSHOT_KEY);
    cache[key] = { saved_at: new Date().toISOString(), data: snapshot };
    await writeKey(SNAPSHOT_KEY, cache);
  }

  async function loadSnapshot(pair, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return null;
    const cache = await readKey(SNAPSHOT_KEY);
    return cache[key] ? cache[key].data : null;
  }

  async function deleteRuleset(pair, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return;
    const cache = await readKey(RULESET_KEY);
    if (!(key in cache)) return;
    delete cache[key];
    await writeKey(RULESET_KEY, cache);
  }

  async function deleteSnapshot(pair, options) {
    const key = scopedKey(pair, options);
    if (!key || key.endsWith("::")) return;
    const cache = await readKey(SNAPSHOT_KEY);
    if (!(key in cache)) return;
    delete cache[key];
    await writeKey(SNAPSHOT_KEY, cache);
  }

  async function clearPair(pair, options) {
    await Promise.all([
      deleteRuleset(pair, options),
      deleteSnapshot(pair, options)
    ]);
  }

  root.helperCache = {
    saveRuleset,
    loadRuleset,
    saveSnapshot,
    loadSnapshot,
    deleteRuleset,
    deleteSnapshot,
    clearPair
  };
})();
