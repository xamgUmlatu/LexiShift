(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_CACHE_TTL_MS = 30 * 60 * 1000;
  const CACHE_OPTION_KEYS = new Set(["cacheTtlMs", "sourceIndexCacheTtlMs"]);

  function requestOptions(options) {
    if (!options || typeof options !== "object" || Array.isArray(options)) {
      return {};
    }
    const cleaned = {};
    for (const key of Object.keys(options).sort()) {
      if (!CACHE_OPTION_KEYS.has(key)) cleaned[key] = options[key];
    }
    return cleaned;
  }

  function optionsKey(options) {
    return JSON.stringify(requestOptions(options));
  }

  function cacheTtlMs(options) {
    const opts = options && typeof options === "object" ? options : {};
    const raw = Number(
      opts.sourceIndexCacheTtlMs !== undefined ? opts.sourceIndexCacheTtlMs : opts.cacheTtlMs
    );
    return Number.isFinite(raw) && raw >= 0 ? raw : DEFAULT_CACHE_TTL_MS;
  }

  function withMetadata(index, key) {
    const sourceIndex = index && typeof index === "object" ? index : {};
    return {
      ...sourceIndex,
      _cache: { options_key: key, cached_at_ms: Date.now() }
    };
  }

  function isUsable(index, key, options, allowStale) {
    if (
      !index
      || typeof index !== "object"
      || !Array.isArray(index.rules)
      || !index.rules.length
    ) {
      return false;
    }
    const metadata = index._cache && typeof index._cache === "object" ? index._cache : {};
    if (String(metadata.options_key || "") !== key) {
      return false;
    }
    if (allowStale === true) {
      return true;
    }
    const cachedAt = Number(metadata.cached_at_ms);
    return Number.isFinite(cachedAt) && (Date.now() - cachedAt) <= cacheTtlMs(options);
  }

  root.helperSourceIndexCache = {
    requestOptions,
    optionsKey,
    withMetadata,
    isUsable
  };
})();
