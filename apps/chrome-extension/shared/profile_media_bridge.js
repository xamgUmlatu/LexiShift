(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const BRIDGE_KIND = "lexishift_profile_media_v1";
  const DEFAULT_TIMEOUT_MS = 4000;

  function normalizeTimeoutMs(value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return DEFAULT_TIMEOUT_MS;
    }
    return Math.max(250, Math.min(Math.trunc(parsed), 20000));
  }

  function send(action, payload = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
    return new Promise((resolve) => {
      if (!globalThis.chrome || !chrome.runtime || typeof chrome.runtime.sendMessage !== "function") {
        resolve({
          ok: false,
          error: {
            code: "runtime_unavailable",
            message: "Chrome runtime messaging is unavailable."
          }
        });
        return;
      }
      const message = {
        kind: BRIDGE_KIND,
        action: String(action || "").trim(),
        payload: payload && typeof payload === "object" ? payload : {},
        timeoutMs: normalizeTimeoutMs(timeoutMs)
      };
      if (!message.action) {
        resolve({
          ok: false,
          error: {
            code: "invalid_action",
            message: "Missing action."
          }
        });
        return;
      }
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          resolve({
            ok: false,
            error: {
              code: "runtime_error",
              message: chrome.runtime.lastError.message
            }
          });
          return;
        }
        resolve(response || {
          ok: false,
          error: {
            code: "empty_response",
            message: "No bridge response."
          }
        });
      });
    });
  }

  root.profileMediaBridge = {
    getBackgroundDataUrl(assetId, timeoutMs) {
      return send("get_background_data_url", { assetId }, timeoutMs);
    }
  };
})();
