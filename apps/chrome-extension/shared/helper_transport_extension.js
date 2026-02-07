(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const BRIDGE_KIND = "lexishift_helper_request_v1";

  function sendViaBridge(type, payload = {}, timeoutMs = 4000) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.runtime || typeof chrome.runtime.sendMessage !== "function") {
        resolve({ ok: false, error: { code: "bridge_unavailable", message: "Helper bridge unavailable." } });
        return;
      }
      let finished = false;
      const timer = setTimeout(() => {
        if (finished) return;
        finished = true;
        resolve({ ok: false, error: { code: "timeout", message: "Helper request timed out." } });
      }, timeoutMs);
      try {
        chrome.runtime.sendMessage(
          {
            kind: BRIDGE_KIND,
            requestType: type,
            payload,
            timeoutMs
          },
          (response) => {
            if (finished) return;
            finished = true;
            clearTimeout(timer);
            if (chrome.runtime.lastError) {
              resolve({ ok: false, error: { code: "bridge_error", message: chrome.runtime.lastError.message } });
              return;
            }
            resolve(response || { ok: false, error: { code: "empty_response", message: "No response." } });
          }
        );
      } catch (error) {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
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
