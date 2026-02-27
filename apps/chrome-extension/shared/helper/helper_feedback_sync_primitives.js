(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_CONFIG = Object.freeze({
    ratings: Object.freeze(["again", "hard", "good", "easy"]),
    maxQueueItems: 2000,
    baseRetryMs: 2000,
    maxRetryMs: 10 * 60 * 1000
  });

  function create(options = {}) {
    const config = options && typeof options === "object" ? options : {};
    const ratings = Array.isArray(config.ratings) && config.ratings.length
      ? config.ratings
      : DEFAULT_CONFIG.ratings;
    const ratingSet = new Set(ratings.map((value) => String(value || "").trim().toLowerCase()).filter(Boolean));
    const maxQueueItems = Math.max(1, Number(config.maxQueueItems || DEFAULT_CONFIG.maxQueueItems));
    const baseRetryMs = Math.max(1, Number(config.baseRetryMs || DEFAULT_CONFIG.baseRetryMs));
    const maxRetryMs = Math.max(baseRetryMs, Number(config.maxRetryMs || DEFAULT_CONFIG.maxRetryMs));

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
      return ratingSet.has(rating) ? rating : "";
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
      const profileId = normalizeString(payload.profile_id) || "default";
      if (!pair || pair === "all" || !lemma || !rating) {
        return null;
      }
      return {
        pair,
        profile_id: profileId,
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
      if (sorted.length <= maxQueueItems) {
        return sorted;
      }
      return sorted.slice(sorted.length - maxQueueItems);
    }

    function computeRetryDelayMs(attempts) {
      const safeAttempts = Math.max(1, Number(attempts || 1));
      const exponential = baseRetryMs * Math.pow(2, safeAttempts - 1);
      const bounded = Math.min(maxRetryMs, exponential);
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

    return Object.freeze({
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
    });
  }

  root.helperFeedbackSyncPrimitives = {
    create
  };
})();
