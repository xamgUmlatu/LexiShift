(() => {
  const HOST_NAME = "com.lexishift.helper";
  const BRIDGE_KIND = "lexishift_helper_request_v1";
  const DEFAULT_TIMEOUT_MS = 60000;
  const IDLE_DISCONNECT_MS = 30000;
  const LOG_PREFIX = "[LexiShift][Background][Helper]";

  let nativePort = null;
  let idleDisconnectTimer = null;
  const pendingRequests = new Map();

  function debugLog(message, details = {}) {
    try {
      console.log(`${LOG_PREFIX} ${message}`, details);
    } catch (_error) {
      // Logging is best-effort.
    }
  }

  function normalizeTimeoutMs(timeoutMs) {
    const parsed = Number(timeoutMs);
    if (!Number.isFinite(parsed)) {
      return DEFAULT_TIMEOUT_MS;
    }
    return Math.max(250, Math.min(Math.trunc(parsed), 60000));
  }

  function makeInvalidRequest(message) {
    return { ok: false, error: { code: "invalid_request", message } };
  }

  function clearIdleDisconnectTimer() {
    if (idleDisconnectTimer) {
      clearTimeout(idleDisconnectTimer);
      idleDisconnectTimer = null;
    }
  }

  function cleanupNativePort() {
    clearIdleDisconnectTimer();
    nativePort = null;
  }

  function armIdleDisconnectTimer() {
    clearIdleDisconnectTimer();
    if (!nativePort || pendingRequests.size > 0) {
      return;
    }
    idleDisconnectTimer = setTimeout(() => {
      if (!nativePort || pendingRequests.size > 0) {
        return;
      }
      debugLog("native port idle disconnect", { idle_ms: IDLE_DISCONNECT_MS });
      try {
        nativePort.disconnect();
      } catch (_error) {
        // Best-effort cleanup.
      }
      cleanupNativePort();
    }, IDLE_DISCONNECT_MS);
  }

  function rejectAllPending(error) {
    const response = { ok: false, error };
    for (const pending of pendingRequests.values()) {
      clearTimeout(pending.timer);
      pending.resolve(response);
    }
    pendingRequests.clear();
  }

  function ensureNativePort() {
    if (nativePort) {
      return nativePort;
    }
    if (!chrome || !chrome.runtime || typeof chrome.runtime.connectNative !== "function") {
      return null;
    }
    const port = chrome.runtime.connectNative(HOST_NAME);
    port.onMessage.addListener((response) => {
      const requestId = response && response.id ? String(response.id) : "";
      if (!requestId) {
        debugLog("native response missing request id", { response });
        return;
      }
      const pending = pendingRequests.get(requestId);
      if (!pending) {
        debugLog("native response without pending request", { request_id: requestId });
        return;
      }
      pendingRequests.delete(requestId);
      clearTimeout(pending.timer);
      debugLog("native request finished", {
        request_type: pending.requestType,
        request_id: requestId,
        duration_ms: Date.now() - pending.startedAt,
        ok: response && response.ok !== false,
        error: response && response.error && response.error.message ? response.error.message : null
      });
      pending.resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
      armIdleDisconnectTimer();
    });
    port.onDisconnect.addListener(() => {
      const disconnectMessage = chrome.runtime.lastError && chrome.runtime.lastError.message
        ? chrome.runtime.lastError.message
        : "Native host disconnected.";
      debugLog("native port disconnected", {
        error: disconnectMessage,
        pending_requests: pendingRequests.size
      });
      cleanupNativePort();
      rejectAllPending({ code: "native_error", message: disconnectMessage });
    });
    nativePort = port;
    debugLog("native port connected", { host_name: HOST_NAME });
    return nativePort;
  }

  function sendNativeMessage(type, payload = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
    return new Promise((resolve) => {
      if (!chrome || !chrome.runtime || typeof chrome.runtime.connectNative !== "function") {
        resolve({ ok: false, error: { code: "native_unavailable", message: "Native messaging not available." } });
        return;
      }
      const requestType = String(type || "").trim();
      if (!requestType) {
        resolve(makeInvalidRequest("Missing helper request type."));
        return;
      }
      const normalizedPayload = payload && typeof payload === "object" ? payload : {};
      const normalizedTimeoutMs = normalizeTimeoutMs(timeoutMs);
      const request = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type: requestType,
        version: 1,
        payload: normalizedPayload
      };
      const payloadKeys = Object.keys(normalizedPayload);
      const startedAt = Date.now();
      clearIdleDisconnectTimer();
      let port = null;
      const timer = setTimeout(() => {
        const pending = pendingRequests.get(request.id);
        if (!pending) {
          return;
        }
        pendingRequests.delete(request.id);
        debugLog("native request timed out", {
          request_type: requestType,
          request_id: request.id,
          timeout_ms: normalizedTimeoutMs,
          payload_keys: payloadKeys
        });
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
        armIdleDisconnectTimer();
      }, normalizedTimeoutMs);
      pendingRequests.set(request.id, {
        resolve,
        timer,
        startedAt,
        requestType
      });
      debugLog("native request started", {
        request_type: requestType,
        request_id: request.id,
        timeout_ms: normalizedTimeoutMs,
        payload_keys: payloadKeys
      });
      try {
        port = ensureNativePort();
        if (!port) {
          clearTimeout(timer);
          pendingRequests.delete(request.id);
          resolve({ ok: false, error: { code: "native_unavailable", message: "Native messaging not available." } });
          return;
        }
        port.postMessage(request);
      } catch (error) {
        clearTimeout(timer);
        pendingRequests.delete(request.id);
        const errorPayload = {
          code: "native_exception",
          message: error && error.message ? error.message : "Native messaging failed."
        };
        debugLog("native request failed before response", {
          request_type: requestType,
          request_id: request.id,
          duration_ms: Date.now() - startedAt,
          error: errorPayload.message
        });
        resolve({
          ok: false,
          error: errorPayload
        });
        rejectAllPending(errorPayload);
        if (port) {
          try {
            port.disconnect();
          } catch (_disconnectError) {
            // Best-effort cleanup.
          }
        }
        cleanupNativePort();
      }
    });
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || message.kind !== BRIDGE_KIND) {
      return false;
    }
    const requestType = String(message.requestType || "").trim();
    if (!requestType) {
      sendResponse(makeInvalidRequest("Missing requestType."));
      return false;
    }
    const payload = message.payload && typeof message.payload === "object" ? message.payload : {};
    const timeoutMs = normalizeTimeoutMs(message.timeoutMs);
    sendNativeMessage(requestType, payload, timeoutMs)
      .then((response) => sendResponse(response))
      .catch((error) => {
        sendResponse({
          ok: false,
          error: {
            code: "bridge_error",
            message: error && error.message ? error.message : "Bridge request failed."
          }
        });
      });
    return true;
  });
})();
