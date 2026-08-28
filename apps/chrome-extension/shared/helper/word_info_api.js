(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_PROFILE_ID = "default";
  const DEFAULT_TIMEOUT_MS = 4000;

  function normalizeProfileId(value) {
    const normalized = String(value || "").trim();
    return normalized || DEFAULT_PROFILE_ID;
  }

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizePair(value) {
    return normalizeText(value).toLowerCase();
  }

  function normalizeLookupRequest(request) {
    const raw = request && typeof request === "object" ? request : {};
    const pair = normalizePair(raw.pair || raw.languagePair);
    const lemma = normalizeText(raw.lemma || raw.replacement);
    const wordPackage = raw.wordPackage && typeof raw.wordPackage === "object"
      ? raw.wordPackage
      : (
          raw.word_package && typeof raw.word_package === "object"
            ? raw.word_package
            : undefined
        );
    const payload = {
      pair,
      profile_id: normalizeProfileId(raw.profileId || raw.profile_id),
      lemma,
      display: normalizeText(raw.display || raw.displayReplacement),
      origin: normalizeText(raw.origin).toLowerCase(),
      source_phrase: normalizeText(raw.sourcePhrase || raw.source_phrase)
    };
    if (wordPackage) {
      payload.word_package = wordPackage;
    }
    return payload;
  }

  function cacheKey(payload) {
    return [
      normalizeProfileId(payload.profile_id),
      normalizePair(payload.pair),
      normalizeText(payload.lemma).toLowerCase(),
      normalizeText(payload.display).toLowerCase(),
      wordPackageCacheIdentity(payload.word_package)
    ].join("::");
  }

  function wordPackageCacheIdentity(wordPackage) {
    const packageValue = wordPackage && typeof wordPackage === "object"
      ? wordPackage
      : {};
    const source = packageValue.source && typeof packageValue.source === "object"
      ? packageValue.source
      : {};
    return [
      normalizeText(packageValue.surface).toLowerCase(),
      normalizeText(packageValue.reading).toLowerCase(),
      normalizeText(
        packageValue.candidate_identity_key || source.candidate_identity_key
      ).toLowerCase(),
      normalizeText(packageValue.row_index ?? packageValue.row_rank),
      normalizeText(packageValue.pos_canonical || packageValue.pos).toLowerCase()
    ].join("|");
  }

  function defaultErrorResponse(code, message) {
    return {
      status: "error",
      error: {
        code,
        message
      },
      glosses: [],
      senses: [],
      dictionary_results: [],
      source_phrases: [],
      srs: { present: false },
      external_links: []
    };
  }

  function create(options = {}) {
    const opts = options && typeof options === "object" ? options : {};
    let helperClient = opts.helperClient || null;
    const cache = opts.cache instanceof Map ? opts.cache : new Map();

    function configure(nextOptions = {}) {
      if (nextOptions && Object.prototype.hasOwnProperty.call(nextOptions, "helperClient")) {
        helperClient = nextOptions.helperClient || null;
      }
      return api;
    }

    async function lookup(request, lookupOptions = {}) {
      const payload = normalizeLookupRequest(request);
      if (!payload.pair || !payload.lemma) {
        return defaultErrorResponse("invalid_request", "Missing pair or lemma.");
      }
      const key = cacheKey(payload);
      const bypassCache = lookupOptions && lookupOptions.bypassCache === true;
      if (!bypassCache && cache.has(key)) {
        return cache.get(key);
      }
      if (!helperClient || typeof helperClient.lookupWordInfo !== "function") {
        return defaultErrorResponse("helper_unavailable", "Helper unavailable.");
      }
      const timeoutMs = Number.isFinite(Number(lookupOptions.timeoutMs))
        ? Number(lookupOptions.timeoutMs)
        : DEFAULT_TIMEOUT_MS;
      const response = await helperClient.lookupWordInfo(payload, timeoutMs);
      if (!response || response.ok === false) {
        const error = response && response.error && typeof response.error === "object"
          ? response.error
          : {};
        return defaultErrorResponse(
          normalizeText(error.code) || "helper_error",
          normalizeText(error.message) || "Word info lookup failed."
        );
      }
      const data = response.data && typeof response.data === "object" ? response.data : {};
      cache.set(key, data);
      return data;
    }

    function clearCache() {
      cache.clear();
    }

    const api = {
      configure,
      lookup,
      clearCache,
      normalizeLookupRequest
    };
    return api;
  }

  const singleton = create();
  root.wordInfoApi = {
    create,
    configure: singleton.configure,
    lookup: singleton.lookup,
    clearCache: singleton.clearCache,
    normalizeLookupRequest
  };
})();
