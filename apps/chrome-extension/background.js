(() => {
  const HOST_NAME = "com.lexishift.helper";
  const BRIDGE_KIND = "lexishift_helper_request_v1";
  const pendingNativeRequests = new Map();
  let nativePort = null;

  function normalizeTimeoutMs(timeoutMs) {
    const parsed = Number(timeoutMs);
    if (!Number.isFinite(parsed)) {
      return 4000;
    }
    return Math.max(250, Math.min(Math.trunc(parsed), 60000));
  }

  function makeInvalidRequest(message) {
    return { ok: false, error: { code: "invalid_request", message } };
  }

  function classifyNativeMessagingError(rawMessage, fallbackCode) {
    const detail = String(rawMessage || "").trim();
    const lowerDetail = detail.toLowerCase();
    if (
      lowerDetail.includes("specified native messaging host not found")
      || lowerDetail.includes("no such native application")
    ) {
      return {
        code: "native_unavailable",
        message: "Helper unavailable.",
        detail
      };
    }
    if (lowerDetail.includes("native host has exited")) {
      return {
        code: "native_host_exited",
        message: "The helper exited unexpectedly.",
        detail
      };
    }
    if (lowerDetail.includes("access to the specified native messaging host is forbidden")) {
      return {
        code: "native_forbidden",
        message: "Native messaging access is blocked.",
        detail
      };
    }
    return {
      code: fallbackCode,
      message: fallbackCode === "bridge_error"
        ? "Helper bridge failed."
        : "Could not communicate with the helper.",
      detail
    };
  }

  function nativePortDisconnectError() {
    const detail = chrome && chrome.runtime && chrome.runtime.lastError
      ? chrome.runtime.lastError.message
      : "Native host has exited.";
    return classifyNativeMessagingError(detail || "Native host has exited.", "native_host_exited");
  }

  function rejectPendingNativeRequests(error) {
    pendingNativeRequests.forEach((entry) => {
      clearTimeout(entry.timer);
      entry.resolve({ ok: false, error });
    });
    pendingNativeRequests.clear();
  }

  function resetNativePort(error) {
    nativePort = null;
    if (error) {
      rejectPendingNativeRequests(error);
    }
  }

  function ensureNativePort() {
    if (!chrome || !chrome.runtime || typeof chrome.runtime.connectNative !== "function") {
      return null;
    }
    if (nativePort) {
      return nativePort;
    }
    try {
      const port = chrome.runtime.connectNative(HOST_NAME);
      if (!port || typeof port.postMessage !== "function") {
        return null;
      }
      nativePort = port;
      if (port.onMessage && typeof port.onMessage.addListener === "function") {
        port.onMessage.addListener((response) => {
          const requestId = String(response && response.id || "");
          const entry = pendingNativeRequests.get(requestId);
          if (!entry) {
            return;
          }
          pendingNativeRequests.delete(requestId);
          clearTimeout(entry.timer);
          entry.resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
        });
      }
      if (port.onDisconnect && typeof port.onDisconnect.addListener === "function") {
        port.onDisconnect.addListener(() => {
          resetNativePort(nativePortDisconnectError());
        });
      }
      return nativePort;
    } catch (_error) {
      resetNativePort(null);
      return null;
    }
  }

  function sendNativeMessageViaPort(type, payload = {}, timeoutMs = 4000) {
    return new Promise((resolve) => {
      const port = ensureNativePort();
      if (!port) {
        resolve({ useOneShotFallback: true });
        return;
      }
      const requestType = String(type || "").trim();
      if (!requestType) {
        resolve(makeInvalidRequest("Missing helper request type."));
        return;
      }
      const request = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type: requestType,
        version: 1,
        payload: payload && typeof payload === "object" ? payload : {}
      };
      const timer = setTimeout(() => {
        if (!pendingNativeRequests.has(request.id)) {
          return;
        }
        pendingNativeRequests.delete(request.id);
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
      }, normalizeTimeoutMs(timeoutMs));
      pendingNativeRequests.set(request.id, { resolve, timer });
      try {
        port.postMessage(request);
      } catch (_error) {
        pendingNativeRequests.delete(request.id);
        clearTimeout(timer);
        resetNativePort(null);
        resolve({ useOneShotFallback: true });
      }
    });
  }

  function sendNativeMessageOneShot(type, payload = {}, timeoutMs = 4000) {
    return new Promise((resolve) => {
      if (!chrome || !chrome.runtime || typeof chrome.runtime.sendNativeMessage !== "function") {
        resolve({ ok: false, error: { code: "native_unavailable", message: "Native messaging not available." } });
        return;
      }
      const requestType = String(type || "").trim();
      if (!requestType) {
        resolve(makeInvalidRequest("Missing helper request type."));
        return;
      }
      const request = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type: requestType,
        version: 1,
        payload: payload && typeof payload === "object" ? payload : {}
      };
      let finished = false;
      const timer = setTimeout(() => {
        if (finished) {
          return;
        }
        finished = true;
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
      }, normalizeTimeoutMs(timeoutMs));
      try {
        chrome.runtime.sendNativeMessage(HOST_NAME, request, (response) => {
          if (finished) {
            return;
          }
          finished = true;
          clearTimeout(timer);
          if (chrome.runtime.lastError) {
            const error = classifyNativeMessagingError(
              chrome.runtime.lastError.message,
              "native_error"
            );
            resolve({
              ok: false,
              error
            });
            return;
          }
          resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
        });
      } catch (error) {
        if (finished) {
          return;
        }
        finished = true;
        clearTimeout(timer);
        resolve({
          ok: false,
          error: classifyNativeMessagingError(
            error && error.message ? error.message : "Native messaging failed.",
            "native_exception"
          )
        });
      }
    });
  }

  async function sendNativeMessage(type, payload = {}, timeoutMs = 4000) {
    const portResponse = await sendNativeMessageViaPort(type, payload, timeoutMs);
    if (portResponse && portResponse.useOneShotFallback === true) {
      return sendNativeMessageOneShot(type, payload, timeoutMs);
    }
    return portResponse;
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
        const normalizedError = classifyNativeMessagingError(
          error && error.message ? error.message : "Bridge request failed.",
          "bridge_error"
        );
        sendResponse({
          ok: false,
          error: normalizedError
        });
      });
    return true;
  });
})();
