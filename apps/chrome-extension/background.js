(() => {
  const HOST_NAME = "com.lexishift.helper";
  const BRIDGE_KIND = "lexishift_helper_request_v1";

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

  function sendNativeMessage(type, payload = {}, timeoutMs = 4000) {
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
            resolve({
              ok: false,
              error: {
                code: "native_error",
                message: chrome.runtime.lastError.message
              }
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
          error: {
            code: "native_exception",
            message: error && error.message ? error.message : "Native messaging failed."
          }
        });
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
