(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const HOST_NAME = "com.lexishift.helper";

  function sendNativeMessage(type, payload = {}, timeoutMs = 4000) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.runtime || !chrome.runtime.sendNativeMessage) {
        resolve({ ok: false, error: { code: "native_unavailable", message: "Native messaging not available." } });
        return;
      }
      const request = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type,
        version: 1,
        payload
      };
      let finished = false;
      const timer = setTimeout(() => {
        if (finished) return;
        finished = true;
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
      }, timeoutMs);
      chrome.runtime.sendNativeMessage(HOST_NAME, request, (response) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        if (chrome.runtime.lastError) {
          resolve({ ok: false, error: { code: "native_error", message: chrome.runtime.lastError.message } });
          return;
        }
        resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
      });
    });
  }

  root.helperTransportExtension = {
    send: sendNativeMessage
  };
})();
