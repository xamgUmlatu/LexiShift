(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const RULESET_KEY = "helperRulesetCache";
  const SNAPSHOT_KEY = "helperSnapshotCache";

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

  async function saveRuleset(pair, ruleset) {
    if (!pair) return;
    const cache = await readKey(RULESET_KEY);
    cache[pair] = { saved_at: new Date().toISOString(), data: ruleset };
    await writeKey(RULESET_KEY, cache);
  }

  async function loadRuleset(pair) {
    if (!pair) return null;
    const cache = await readKey(RULESET_KEY);
    return cache[pair] ? cache[pair].data : null;
  }

  async function saveSnapshot(pair, snapshot) {
    if (!pair) return;
    const cache = await readKey(SNAPSHOT_KEY);
    cache[pair] = { saved_at: new Date().toISOString(), data: snapshot };
    await writeKey(SNAPSHOT_KEY, cache);
  }

  async function loadSnapshot(pair) {
    if (!pair) return null;
    const cache = await readKey(SNAPSHOT_KEY);
    return cache[pair] ? cache[pair].data : null;
  }

  async function deleteRuleset(pair) {
    if (!pair) return;
    const cache = await readKey(RULESET_KEY);
    if (!(pair in cache)) return;
    delete cache[pair];
    await writeKey(RULESET_KEY, cache);
  }

  async function deleteSnapshot(pair) {
    if (!pair) return;
    const cache = await readKey(SNAPSHOT_KEY);
    if (!(pair in cache)) return;
    delete cache[pair];
    await writeKey(SNAPSHOT_KEY, cache);
  }

  async function clearPair(pair) {
    await Promise.all([deleteRuleset(pair), deleteSnapshot(pair)]);
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
