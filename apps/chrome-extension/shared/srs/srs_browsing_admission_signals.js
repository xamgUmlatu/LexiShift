(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const SIDE_REPLACEMENT_EXPOSURE = "replacement_exposure";
  const DEFAULT_FLUSH_DELAY_MS = 2000;
  const DEFAULT_MAX_SCOPES = 8;
  const DEFAULT_MAX_SIGNALS_PER_PACKET = 50;
  const DEFAULT_MAX_COUNT_PER_SIGNAL = 5;
  const DEFAULT_CONTEXT_BUCKET_MS = 5 * 60 * 1000;
  let runtimePageContextToken = "";

  function normalizeProfileId(value) {
    const normalized = String(value || "").trim();
    return normalized || "default";
  }

  function normalizePair(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLemma(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeTargetMetadata(value) {
    return String(value || "").trim();
  }

  function normalizeContextMetadata(value) {
    return String(value || "").trim();
  }

  function stableHash(value) {
    const text = String(value || "");
    let hash = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(36);
  }

  function randomToken() {
    const cryptoApi = globalThis.crypto || globalThis.msCrypto;
    if (cryptoApi && typeof cryptoApi.getRandomValues === "function") {
      const buffer = new Uint32Array(2);
      cryptoApi.getRandomValues(buffer);
      return `${buffer[0].toString(36)}${buffer[1].toString(36)}`;
    }
    return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
  }

  function pageContextToken(options) {
    const opts = options && typeof options === "object" ? options : {};
    const explicit = normalizeContextMetadata(
      opts.page_context_key
        || opts.pageContextKey
        || opts.runtime_context_key
        || opts.runtimeContextKey
        || ""
    );
    if (explicit) {
      return explicit;
    }
    if (typeof opts.getPageContextKey === "function") {
      const fromCallback = normalizeContextMetadata(opts.getPageContextKey());
      if (fromCallback) {
        return fromCallback;
      }
    }
    if (!runtimePageContextToken) {
      runtimePageContextToken = randomToken();
    }
    return runtimePageContextToken;
  }

  function contextBucket(options) {
    const opts = options && typeof options === "object" ? options : {};
    const bucketMs = Math.max(60000, Number(opts.contextBucketMs || DEFAULT_CONTEXT_BUCKET_MS));
    const nowMs = typeof opts.nowMs === "function" ? Number(opts.nowMs()) : Date.now();
    const safeNowMs = Number.isFinite(nowMs) ? nowMs : Date.now();
    return Math.floor(safeNowMs / bucketMs);
  }

  function contextKeyForExposure(exposure, options) {
    const explicitContext = normalizeContextMetadata(
      exposure.context_key
        || exposure.contextKey
        || exposure.page_context_key
        || exposure.pageContextKey
        || exposure.session_key
        || exposure.sessionKey
        || exposure.document_id
        || exposure.documentId
        || ""
    );
    const bucket = contextBucket(options);
    if (explicitContext) {
      return `ctxh:${stableHash(explicitContext)}:t${bucket}`;
    }
    return `pageh:${stableHash(pageContextToken(options))}:t${bucket}`;
  }

  function targetKeyForExposure(lemma, exposure) {
    const explicitKey = normalizeTargetMetadata(
      exposure.target_key
        || exposure.targetKey
        || exposure.browsing_target_key
        || exposure.browsingTargetKey
        || ""
    );
    if (explicitKey) {
      return explicitKey;
    }
    const reading = normalizeTargetMetadata(
      exposure.target_reading || exposure.targetReading || exposure.reading || ""
    );
    if (lemma && reading && reading !== lemma) {
      return `${lemma}|${reading}`;
    }
    return lemma;
  }

  function isEnabled(settings) {
    return Boolean(settings && settings.srsBrowsingAdmissionSignalsEnabled === true);
  }

  function addExposureBatchToPending(pendingByScope, exposures, settings, options) {
    const opts = options && typeof options === "object" ? options : {};
    const maxScopes = Math.max(1, Number(opts.maxScopes || DEFAULT_MAX_SCOPES));
    const maxCountPerSignal = Math.max(
      1,
      Number(opts.maxCountPerSignal || DEFAULT_MAX_COUNT_PER_SIGNAL)
    );
    const profileId = normalizeProfileId(settings && settings.srsProfileId);
    const fallbackPair = normalizePair(settings && settings.srsPair);
    let accepted = 0;
    for (const exposure of Array.isArray(exposures) ? exposures : []) {
      if (!exposure || typeof exposure !== "object") {
        continue;
      }
      const pair = normalizePair(exposure.language_pair || fallbackPair);
      const lemma = normalizeLemma(exposure.lemma || exposure.replacement);
      if (!pair || pair === "all" || !lemma) {
        continue;
      }
      const targetKey = targetKeyForExposure(lemma, exposure);
      const targetReading = normalizeTargetMetadata(
        exposure.target_reading || exposure.targetReading || exposure.reading || ""
      );
      const readingConfidence = Number(
        exposure.reading_confidence ?? exposure.readingConfidence ?? 1
      );
      const contextKey = contextKeyForExposure(exposure, opts);
      const scopeKey = `${profileId}\t${pair}`;
      if (!pendingByScope.has(scopeKey)) {
        if (pendingByScope.size >= maxScopes) {
          continue;
        }
        pendingByScope.set(scopeKey, {
          pair,
          profileId,
          targets: new Map()
        });
      }
      const scope = pendingByScope.get(scopeKey);
      const pendingKey = `${targetKey}\t${contextKey}`;
      const previous = scope.targets.get(pendingKey) || {
        target_key: targetKey,
        target_lemma: lemma,
        target_reading: targetReading,
        reading_confidence: Number.isFinite(readingConfidence) ? readingConfidence : 1,
        context_key: contextKey,
        count: 0
      };
      previous.count = Math.min(maxCountPerSignal, Number(previous.count || 0) + 1);
      if (!previous.target_reading && targetReading) {
        previous.target_reading = targetReading;
      }
      previous.reading_confidence = Math.max(
        0,
        Math.min(
          1,
          Math.max(
            Number(previous.reading_confidence || 0),
            Number.isFinite(readingConfidence) ? readingConfidence : 1
          )
        )
      );
      scope.targets.set(pendingKey, previous);
      accepted += 1;
    }
    return accepted;
  }

  function buildPacketPayloads(pendingByScope, options) {
    const opts = options && typeof options === "object" ? options : {};
    const nowIso = typeof opts.nowIso === "function"
      ? opts.nowIso
      : (() => new Date().toISOString());
    const maxSignalsPerPacket = Math.max(
      1,
      Number(opts.maxSignalsPerPacket || DEFAULT_MAX_SIGNALS_PER_PACKET)
    );
    const payloads = [];
    for (const scope of pendingByScope.values()) {
      const targetRows = scope.targets
        ? Array.from(scope.targets.values())
        : Array.from((scope.lemmas || new Map()).entries()).map(([lemma, count]) => ({
            target_key: lemma,
            target_lemma: lemma,
            target_reading: "",
            reading_confidence: 1,
            count
          }));
      const rows = targetRows
        .map((row) => {
          if (row && typeof row === "object") {
            return {
              target_key: normalizeTargetMetadata(row.target_key || row.targetKey || ""),
              target_lemma: normalizeLemma(row.target_lemma || row.lemma || ""),
              target_reading: normalizeTargetMetadata(
                row.target_reading || row.targetReading || ""
              ),
              reading_confidence: Number(row.reading_confidence ?? row.readingConfidence ?? 1),
              context_key: normalizeContextMetadata(row.context_key || row.contextKey || ""),
              count: Number(row.count || 0)
            };
          }
          const lemma = normalizeLemma(row);
          return {
            target_key: lemma,
            target_lemma: lemma,
            target_reading: "",
            reading_confidence: 1,
            context_key: "",
            count: 0
          };
        })
        .filter((row) => row.target_lemma && row.count > 0)
        .sort((left, right) => {
          if (right.count !== left.count) {
            return right.count - left.count;
          }
          return left.target_key.localeCompare(right.target_key);
        })
        .slice(0, maxSignalsPerPacket);
      if (!rows.length) {
        continue;
      }
      payloads.push({
        pair: scope.pair,
        profile_id: scope.profileId,
        captured_at: nowIso(),
        opt_in: true,
        signals: rows.map((row) => ({
          target_key: row.target_key || row.target_lemma,
          target_lemma: row.target_lemma,
          target_reading: row.target_reading,
          side: SIDE_REPLACEMENT_EXPOSURE,
          count: row.count,
          reading_confidence: Number.isFinite(row.reading_confidence)
            ? Math.max(0, Math.min(1, row.reading_confidence))
            : 1,
          observation_source: SIDE_REPLACEMENT_EXPOSURE,
          source_mapping_confidence: 1.0,
          context_key: row.context_key
        }))
      });
    }
    return payloads;
  }

  function createSender(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getHelperClient = typeof opts.getHelperClient === "function"
      ? opts.getHelperClient
      : (() => null);
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const flushDelayMs = Math.max(0, Number(opts.flushDelayMs ?? DEFAULT_FLUSH_DELAY_MS));
    const pendingByScope = new Map();
    let flushTimer = null;
    let flushPromise = null;

    function clearTimer() {
      if (flushTimer !== null && typeof globalThis.clearTimeout === "function") {
        globalThis.clearTimeout(flushTimer);
      }
      flushTimer = null;
    }

    function scheduleFlush() {
      if (flushTimer !== null || flushPromise) {
        return;
      }
      if (flushDelayMs <= 0) {
        flushPromise = Promise.resolve()
          .then(() => flush())
          .finally(() => {
            flushPromise = null;
          });
        return;
      }
      if (typeof globalThis.setTimeout !== "function") {
        return;
      }
      flushTimer = globalThis.setTimeout(() => {
        flushTimer = null;
        flushPromise = flush().finally(() => {
          flushPromise = null;
        });
      }, flushDelayMs);
    }

    async function flush() {
      clearTimer();
      if (!pendingByScope.size) {
        return { status: "empty", packet_count: 0 };
      }
      const payloads = buildPacketPayloads(pendingByScope, {
        nowIso: opts.nowIso,
        maxSignalsPerPacket: opts.maxSignalsPerPacket
      });
      pendingByScope.clear();
      if (!payloads.length) {
        return { status: "empty", packet_count: 0 };
      }
      const helperClient = getHelperClient();
      if (
        !helperClient
        || typeof helperClient.ingestBrowsingAdmissionSignals !== "function"
      ) {
        return { status: "skipped", reason: "helper_client_unavailable", packet_count: 0 };
      }
      const responses = [];
      for (const payload of payloads) {
        try {
          responses.push(await helperClient.ingestBrowsingAdmissionSignals(payload));
        } catch (error) {
          responses.push({
            ok: false,
            error: {
              code: "browsing_admission_ingest_failed",
              message: error && error.message ? error.message : String(error || "Unknown error.")
            }
          });
        }
      }
      return {
        status: "sent",
        packet_count: payloads.length,
        signal_count: payloads.reduce((sum, payload) => sum + payload.signals.length, 0),
        responses
      };
    }

    function recordExposureBatch(exposures, settingsOverride) {
      const settings = settingsOverride && typeof settingsOverride === "object"
        ? settingsOverride
        : getCurrentSettings();
      if (!isEnabled(settings)) {
        return Promise.resolve({ status: "skipped", reason: "not_enabled" });
      }
      const accepted = addExposureBatchToPending(pendingByScope, exposures, settings, opts);
      if (!accepted) {
        return Promise.resolve({ status: "empty", accepted: 0 });
      }
      scheduleFlush();
      if (settings.debugEnabled) {
        log(`Queued ${accepted} browsing-admission signal exposure(s).`);
      }
      return Promise.resolve({ status: "queued", accepted });
    }

    return {
      flush,
      recordExposureBatch,
      _pendingByScope: pendingByScope
    };
  }

  root.srsBrowsingAdmissionSignals = {
    SIDE_REPLACEMENT_EXPOSURE,
    addExposureBatchToPending,
    buildPacketPayloads,
    contextKeyForExposure,
    createSender,
    isEnabled
  };
})();
