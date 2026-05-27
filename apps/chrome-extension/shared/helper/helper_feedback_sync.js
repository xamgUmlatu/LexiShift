(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const QUEUE_KEY = "helperFeedbackSyncQueue";
  const LOCK_KEY = "helperFeedbackSyncLock";
  const DROPPED_KEY = "helperFeedbackSyncDropped";

  const MAX_QUEUE_ITEMS = 2000;
  const MAX_DROPPED_ITEMS = 200;
  // Set to 0 to keep retrying indefinitely (bounded by MAX_QUEUE_ITEMS).
  const MAX_ATTEMPTS = 0;
  const BASE_RETRY_MS = 2000;
  const MAX_RETRY_MS = 10 * 60 * 1000;
  const DEFAULT_FLUSH_INTERVAL_MS = 30000;
  const DEFAULT_BATCH_SIZE = 8;
  const LOCK_TTL_MS = 15000;
  const LOCK_RETRY_MS = 2500;

  const primitivesModule = root.helperFeedbackSyncPrimitives;
  const primitives = primitivesModule && typeof primitivesModule.create === "function"
    ? primitivesModule.create({
      maxQueueItems: MAX_QUEUE_ITEMS,
      baseRetryMs: BASE_RETRY_MS,
      maxRetryMs: MAX_RETRY_MS
    })
    : null;

  if (!primitives) {
    root.helperFeedbackSync = {
      create() {
        return {
          start() {},
          stop() {},
          scheduleFlush() {},
          enqueue: async () => null,
          flushNow: async () => false
        };
      },
      storageKeys: {
        queue: QUEUE_KEY,
        lock: LOCK_KEY,
        dropped: DROPPED_KEY
      }
    };
    return;
  }

  const {
    nowMs,
    nowIso,
    randomId,
    normalizeString,
    buildDefaultTransportError,
    readKey,
    writeKey,
    removeKey,
    sanitizeFeedbackPayload,
    sanitizeQueueEntry,
    sortByCreatedAt,
    trimQueue,
    computeRetryDelayMs,
    errorFromResponse,
    delayFromQueue
  } = primitives;

  async function loadQueue() {
    const raw = await readKey(QUEUE_KEY, []);
    const list = Array.isArray(raw) ? raw : [];
    const sanitized = [];
    for (const entry of list) {
      const normalized = sanitizeQueueEntry(entry);
      if (normalized) {
        sanitized.push(normalized);
      }
    }
    return sortByCreatedAt(sanitized);
  }

  async function saveQueue(items) {
    await writeKey(QUEUE_KEY, trimQueue(items || []));
  }

  class HelperFeedbackSync {
    constructor(options = {}) {
      const sendFeedback = options.sendFeedback;
      this._sendFeedback = typeof sendFeedback === "function"
        ? sendFeedback
        : (() => Promise.resolve(buildDefaultTransportError("Helper client unavailable.")));
      this._maybeAutoRefresh = typeof options.maybeAutoRefresh === "function"
        ? options.maybeAutoRefresh
        : null;
      this._log = typeof options.log === "function" ? options.log : null;
      this._flushIntervalMs = Math.max(5000, Number(options.flushIntervalMs || DEFAULT_FLUSH_INTERVAL_MS));
      this._batchSize = Math.max(1, Math.min(50, Number(options.batchSize || DEFAULT_BATCH_SIZE)));
      this._isFlushWorker = options.isFlushWorker !== false;
      this._workerId = `worker-${randomId()}`;
      this._flushTimer = null;
      this._flushInFlight = false;
      this._started = false;
      this._onStorageChanged = null;
      this._autoRefreshInFlight = false;
    }

    _debug(message, payload) {
      if (!this._log) {
        return;
      }
      if (payload !== undefined) {
        this._log(`[HelperFeedbackSync] ${message}`, payload);
      } else {
        this._log(`[HelperFeedbackSync] ${message}`);
      }
    }

    start() {
      if (this._started) {
        return;
      }
      this._started = true;
      if (!this._isFlushWorker) {
        return;
      }
      if (globalThis.chrome && chrome.storage && chrome.storage.onChanged) {
        this._onStorageChanged = (changes, areaName) => {
          if (areaName !== "local") {
            return;
          }
          if (changes[QUEUE_KEY]) {
            this.scheduleFlush(250);
          }
          if (changes[LOCK_KEY]) {
            this.scheduleFlush(750);
          }
        };
        chrome.storage.onChanged.addListener(this._onStorageChanged);
      }
      this.scheduleFlush(500);
    }

    stop() {
      this._started = false;
      if (this._flushTimer) {
        clearTimeout(this._flushTimer);
        this._flushTimer = null;
      }
      if (this._onStorageChanged && globalThis.chrome && chrome.storage && chrome.storage.onChanged) {
        chrome.storage.onChanged.removeListener(this._onStorageChanged);
      }
      this._onStorageChanged = null;
    }

    scheduleFlush(delayMs = 0) {
      if (!this._isFlushWorker) {
        return;
      }
      if (this._flushTimer) {
        clearTimeout(this._flushTimer);
      }
      const delay = Math.max(0, Number(delayMs || 0));
      this._flushTimer = setTimeout(() => {
        this._flushTimer = null;
        this.flushNow("scheduled");
      }, delay);
    }

    async enqueue(payload) {
      const normalized = sanitizeFeedbackPayload(payload);
      if (!normalized) {
        return null;
      }
      const entry = {
        id: randomId(),
        payload: normalized,
        created_at: nowMs(),
        attempts: 0,
        next_attempt_at: nowMs()
      };

      // Best-effort merge with verification to avoid accidental drops under concurrent writers.
      for (let attempt = 0; attempt < 3; attempt += 1) {
        const queue = await loadQueue();
        if (queue.some((item) => item.id === entry.id)) {
          break;
        }
        await saveQueue([...queue, entry]);
        const verify = await loadQueue();
        if (verify.some((item) => item.id === entry.id)) {
          break;
        }
      }

      if (this._isFlushWorker) {
        this.scheduleFlush(100);
      }
      return entry.id;
    }

    async _acquireLock() {
      const now = nowMs();
      const lock = await readKey(LOCK_KEY, null);
      if (lock && typeof lock === "object") {
        const owner = normalizeString(lock.owner);
        const expiresAt = Number(lock.expires_at || 0);
        if (owner && owner !== this._workerId && Number.isFinite(expiresAt) && expiresAt > now) {
          return false;
        }
      }
      const candidate = {
        owner: this._workerId,
        acquired_at: now,
        expires_at: now + LOCK_TTL_MS
      };
      await writeKey(LOCK_KEY, candidate);
      const verify = await readKey(LOCK_KEY, null);
      return Boolean(
        verify
          && typeof verify === "object"
          && normalizeString(verify.owner) === this._workerId
          && Number(verify.expires_at || 0) > nowMs()
      );
    }

    async _renewLock() {
      const lock = await readKey(LOCK_KEY, null);
      if (!lock || typeof lock !== "object") {
        return false;
      }
      if (normalizeString(lock.owner) !== this._workerId) {
        return false;
      }
      await writeKey(LOCK_KEY, {
        owner: this._workerId,
        acquired_at: Number(lock.acquired_at || nowMs()),
        expires_at: nowMs() + LOCK_TTL_MS
      });
      return true;
    }

    async _releaseLock() {
      const lock = await readKey(LOCK_KEY, null);
      if (!lock || typeof lock !== "object") {
        return;
      }
      if (normalizeString(lock.owner) !== this._workerId) {
        return;
      }
      await removeKey(LOCK_KEY);
    }

    async _appendDropped(entry, error) {
      const current = await readKey(DROPPED_KEY, []);
      const list = Array.isArray(current) ? current : [];
      list.push({
        id: normalizeString(entry && entry.id),
        payload: entry && entry.payload ? entry.payload : null,
        created_at: Number(entry && entry.created_at) || nowMs(),
        attempts: Number(entry && entry.attempts) || 0,
        dropped_at: nowIso(),
        last_error: error || null
      });
      const trimmed = list.length > MAX_DROPPED_ITEMS
        ? list.slice(list.length - MAX_DROPPED_ITEMS)
        : list;
      await writeKey(DROPPED_KEY, trimmed);
    }

    async _send(payload) {
      try {
        const result = await Promise.resolve(this._sendFeedback(payload));
        if (result && typeof result === "object") {
          return result;
        }
        return buildDefaultTransportError("Invalid helper response.");
      } catch (error) {
        return {
          ok: false,
          error: {
            code: "send_exception",
            message: error && error.message ? error.message : "Failed to send helper feedback."
          }
        };
      }
    }

    async _runAutoRefresh(reason, handled) {
      if (!this._maybeAutoRefresh || this._autoRefreshInFlight || handled <= 0) {
        return;
      }
      this._autoRefreshInFlight = true;
      try {
        const result = await Promise.resolve(this._maybeAutoRefresh({
          reason,
          handled
        }));
        if (result && typeof result === "object") {
          const payload = result.data && typeof result.data === "object" ? result.data : result;
          if (payload.attempted || payload.applied || payload.auto_refresh) {
            this._debug("Auto-refresh check completed.", payload);
          }
        }
      } catch (error) {
        this._debug("Auto-refresh check failed.", {
          message: error && error.message ? error.message : String(error || "")
        });
      } finally {
        this._autoRefreshInFlight = false;
      }
    }

    async flushNow(reason = "manual") {
      if (!this._isFlushWorker) {
        return false;
      }
      if (this._flushInFlight) {
        return false;
      }
      this._flushInFlight = true;
      let handledCount = 0;
      try {
        const locked = await this._acquireLock();
        if (!locked) {
          this.scheduleFlush(LOCK_RETRY_MS);
          return false;
        }
        const queue = await loadQueue();
        if (!queue.length) {
          return false;
        }
        const now = nowMs();
        const due = queue
          .filter((item) => Number(item.next_attempt_at || 0) <= now)
          .slice(0, this._batchSize);
        if (!due.length) {
          const delay = delayFromQueue(queue);
          this.scheduleFlush(delay === null ? this._flushIntervalMs : delay);
          return false;
        }

        const updates = new Map();
        const removeIds = new Set();
        let handled = 0;
        for (const item of due) {
          const response = await this._send(item.payload);
          if (response && response.ok === true) {
            removeIds.add(item.id);
            handled += 1;
            await this._renewLock();
            continue;
          }

          const attempts = Number(item.attempts || 0) + 1;
          const lastError = errorFromResponse(response);
          if (MAX_ATTEMPTS > 0 && attempts >= MAX_ATTEMPTS) {
            removeIds.add(item.id);
            await this._appendDropped(
              { ...item, attempts },
              lastError
            );
            handled += 1;
            await this._renewLock();
            continue;
          }
          updates.set(item.id, {
            ...item,
            attempts,
            next_attempt_at: nowMs() + computeRetryDelayMs(attempts),
            last_error: lastError,
            updated_at: nowMs()
          });
          handled += 1;
          await this._renewLock();
        }

        // Merge against latest queue to avoid clobbering concurrent enqueues.
        const latest = await loadQueue();
        const merged = [];
        for (const item of latest) {
          if (removeIds.has(item.id)) {
            continue;
          }
          if (updates.has(item.id)) {
            merged.push(updates.get(item.id));
          } else {
            merged.push(item);
          }
        }
        await saveQueue(merged);

        if (merged.length) {
          const dueDelay = delayFromQueue(merged);
          this.scheduleFlush(dueDelay === null ? this._flushIntervalMs : dueDelay);
        }

        if (handled > 0) {
          this._debug(`Flushed feedback queue (${handled} item(s), reason=${reason}).`);
        }
        handledCount = handled;
        return handled > 0;
      } finally {
        await this._releaseLock();
        this._flushInFlight = false;
        if (handledCount > 0) {
          await this._runAutoRefresh(reason, handledCount);
        }
      }
    }
  }

  root.helperFeedbackSync = {
    create(options) {
      return new HelperFeedbackSync(options || {});
    },
    storageKeys: {
      queue: QUEUE_KEY,
      lock: LOCK_KEY,
      dropped: DROPPED_KEY
    }
  };
})();
