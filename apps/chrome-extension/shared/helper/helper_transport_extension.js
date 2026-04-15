(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const BRIDGE_KIND = "lexishift_helper_request_v1";
  const DEFAULT_TIMEOUT_MS = 60000;
  const LOG_PREFIX = "[LexiShift][Options][HelperTransport]";

  function debugLog(message, details = {}) {
    try {
      console.log(`${LOG_PREFIX} ${message}`, details);
    } catch (_error) {
      // Logging is best-effort.
    }
  }

  function sendViaBridge(type, payload = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.runtime || typeof chrome.runtime.sendMessage !== "function") {
        resolve({ ok: false, error: { code: "bridge_unavailable", message: "Helper bridge unavailable." } });
        return;
      }
      const requestType = String(type || "").trim();
      const normalizedPayload = payload && typeof payload === "object" ? payload : {};
      const payloadKeys = Object.keys(normalizedPayload);
      const startedAt = Date.now();
      debugLog("bridge request started", {
        request_type: requestType,
        timeout_ms: timeoutMs,
        payload_keys: payloadKeys
      });
      let finished = false;
      const timer = setTimeout(() => {
        if (finished) return;
        finished = true;
        debugLog("bridge request timed out", {
          request_type: requestType,
          duration_ms: Date.now() - startedAt,
          timeout_ms: timeoutMs
        });
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
      }, timeoutMs);
      try {
        chrome.runtime.sendMessage(
          {
            kind: BRIDGE_KIND,
            requestType,
            payload: normalizedPayload,
            timeoutMs
          },
          (response) => {
            if (finished) return;
            finished = true;
            clearTimeout(timer);
            if (chrome.runtime.lastError) {
              debugLog("bridge request finished", {
                request_type: requestType,
                duration_ms: Date.now() - startedAt,
                ok: false,
                error: chrome.runtime.lastError.message
              });
              resolve({ ok: false, error: { code: "bridge_error", message: chrome.runtime.lastError.message } });
              return;
            }
            debugLog("bridge request finished", {
              request_type: requestType,
              duration_ms: Date.now() - startedAt,
              ok: response && response.ok !== false,
              error: response && response.error && response.error.message ? response.error.message : null
            });
            resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
          }
        );
      } catch (error) {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        debugLog("bridge request failed before response", {
          request_type: requestType,
          duration_ms: Date.now() - startedAt,
          error: error && error.message ? error.message : "Helper bridge failed."
        });
        resolve({
          ok: false,
          error: { code: "bridge_error", message: error && error.message ? error.message : "Helper bridge failed." }
        });
      }
    });
  }

  root.helperTransportExtension = {
    send: sendViaBridge
  };
})();
