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

  const RATING_SET = new Set(["again", "hard", "good", "easy"]);

  function nowMs() {
    return Date.now();
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function randomId() {
    return `${nowMs()}-${Math.random().toString(16).slice(2)}`;
  }

  function normalizeString(value) {
    return String(value || "").trim();
  }

  function normalizeRating(value) {
    const rating = normalizeString(value).toLowerCase();
    return RATING_SET.has(rating) ? rating : "";
  }

  function buildDefaultTransportError(message) {
    return { ok: false, error: { code: "transport_missing", message } };
  }

  function readLocal(defaults) {
    return new Promise((resolve) => {
      try {
        if (!globalThis.chrome || !chrome.storage || !chrome.storage.local) {
          resolve(defaults || {});
          return;
        }
        chrome.storage.local.get(defaults || {}, (items) => {
          resolve(items || defaults || {});
        });
      } catch (_error) {
        resolve(defaults || {});
      }
    });
  }

  function writeLocal(payload) {
    return new Promise((resolve) => {
      try {
        if (!globalThis.chrome || !chrome.storage || !chrome.storage.local) {
          resolve(false);
          return;
        }
        chrome.storage.local.set(payload || {}, () => resolve(true));
      } catch (_error) {
        resolve(false);
      }
    });
  }

  function removeLocal(keys) {
    return new Promise((resolve) => {
      try {
        if (!globalThis.chrome || !chrome.storage || !chrome.storage.local) {
          resolve(false);
          return;
        }
        chrome.storage.local.remove(keys, () => resolve(true));
      } catch (_error) {
        resolve(false);
      }
    });
  }

  async function readKey(key, fallback) {
    const data = await readLocal({ [key]: fallback });
    return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : fallback;
  }

  async function writeKey(key, value) {
    await writeLocal({ [key]: value });
  }

  async function removeKey(key) {
    await removeLocal(key);
  }

  function sanitizeFeedbackPayload(payload) {
    if (!payload || typeof payload !== "object") {
      return null;
    }
    const pair = normalizeString(payload.pair);
    const lemma = normalizeString(payload.lemma);
    const rating = normalizeRating(payload.rating);
    if (!pair || pair === "all" || !lemma || !rating) {
      return null;
    }
    return {
      pair,
      lemma,
      rating,
      source_type: normalizeString(payload.source_type) || "extension",
      ts: normalizeString(payload.ts) || nowIso()
    };
  }

  function sanitizeQueueEntry(entry) {
    if (!entry || typeof entry !== "object") {
      return null;
    }
    const id = normalizeString(entry.id);
    const payload = sanitizeFeedbackPayload(entry.payload);
    const createdAt = Number(entry.created_at || 0);
    const attempts = Number(entry.attempts || 0);
    const nextAttemptAt = Number(entry.next_attempt_at || createdAt || nowMs());
    if (!id || !payload) {
      return null;
    }
    return {
      id,
      payload,
      created_at: Number.isFinite(createdAt) && createdAt > 0 ? createdAt : nowMs(),
      attempts: Number.isFinite(attempts) && attempts > 0 ? Math.floor(attempts) : 0,
      next_attempt_at: Number.isFinite(nextAttemptAt) && nextAttemptAt > 0 ? Math.floor(nextAttemptAt) : nowMs(),
      last_error: entry.last_error && typeof entry.last_error === "object" ? {
        code: normalizeString(entry.last_error.code) || "unknown",
        message: normalizeString(entry.last_error.message) || "unknown",
        at: normalizeString(entry.last_error.at) || nowIso()
      } : null,
      updated_at: Number(entry.updated_at || 0) || undefined
    };
  }

  function sortByCreatedAt(items) {
    return [...items].sort((a, b) => {
      const aTs = Number(a.created_at || 0);
      const bTs = Number(b.created_at || 0);
      if (aTs === bTs) {
        return String(a.id || "").localeCompare(String(b.id || ""));
      }
      return aTs - bTs;
    });
  }

  function trimQueue(items) {
    const sorted = sortByCreatedAt(items);
    if (sorted.length <= MAX_QUEUE_ITEMS) {
      return sorted;
    }
    return sorted.slice(sorted.length - MAX_QUEUE_ITEMS);
  }

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

  function computeRetryDelayMs(attempts) {
    const safeAttempts = Math.max(1, Number(attempts || 1));
    const exponential = BASE_RETRY_MS * Math.pow(2, safeAttempts - 1);
    const bounded = Math.min(MAX_RETRY_MS, exponential);
    const jitter = Math.floor(Math.random() * 300);
    return bounded + jitter;
  }

  function errorFromResponse(response) {
    if (!response || typeof response !== "object") {
      return { code: "unknown", message: "Unknown helper error.", at: nowIso() };
    }
    if (response.error && typeof response.error === "object") {
      return {
        code: normalizeString(response.error.code) || "unknown",
        message: normalizeString(response.error.message) || "Unknown helper error.",
        at: nowIso()
      };
    }
    return { code: "unknown", message: "Unknown helper error.", at: nowIso() };
  }

  function delayFromQueue(queue) {
    if (!Array.isArray(queue) || !queue.length) {
      return null;
    }
    const now = nowMs();
    let minTs = null;
    for (const item of queue) {
      const ts = Number(item.next_attempt_at || 0);
      if (!Number.isFinite(ts) || ts <= 0) {
        continue;
      }
      if (minTs === null || ts < minTs) {
        minTs = ts;
      }
    }
    if (minTs === null) {
      return null;
    }
    return Math.max(250, minTs - now);
  }

  class HelperFeedbackSync {
    constructor(options = {}) {
      const sendFeedback = options.sendFeedback;
      this._sendFeedback = typeof sendFeedback === "function"
        ? sendFeedback
        : (() => Promise.resolve(buildDefaultTransportError("Helper client unavailable.")));
      this._log = typeof options.log === "function" ? options.log : null;
      this._flushIntervalMs = Math.max(5000, Number(options.flushIntervalMs || DEFAULT_FLUSH_INTERVAL_MS));
      this._batchSize = Math.max(1, Math.min(50, Number(options.batchSize || DEFAULT_BATCH_SIZE)));
      this._isFlushWorker = options.isFlushWorker !== false;
      this._workerId = `worker-${randomId()}`;
      this._flushTimer = null;
      this._flushInFlight = false;
      this._started = false;
      this._onStorageChanged = null;
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

    async flushNow(reason = "manual") {
      if (!this._isFlushWorker) {
        return false;
      }
      if (this._flushInFlight) {
        return false;
      }
      this._flushInFlight = true;
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
        return handled > 0;
      } finally {
        await this._releaseLock();
        this._flushInFlight = false;
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
