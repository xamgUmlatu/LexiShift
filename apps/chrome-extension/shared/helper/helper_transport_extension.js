(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const BRIDGE_KIND = "lexishift_helper_request_v1";

  function classifyBridgeError(rawMessage, fallbackCode) {
    const detail = String(rawMessage || "").trim();
    const lowerDetail = detail.toLowerCase();
    if (
      lowerDetail.includes("could not establish connection")
      || lowerDetail.includes("receiving end does not exist")
    ) {
      return {
        code: "bridge_unavailable",
        message: "Helper bridge unavailable.",
        detail
      };
    }
    return {
      code: fallbackCode,
      message: fallbackCode === "bridge_unavailable"
        ? "Helper bridge unavailable."
        : "Helper bridge failed.",
      detail
    };
  }

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
              resolve({
                ok: false,
                error: classifyBridgeError(chrome.runtime.lastError.message, "bridge_error")
              });
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
          error: classifyBridgeError(
            error && error.message ? error.message : "Helper bridge failed.",
            "bridge_error"
          )
        });
      }
    });
  }

  root.helperTransportExtension = {
    send: sendViaBridge
  };
})();
