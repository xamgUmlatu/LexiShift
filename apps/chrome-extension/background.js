(() => {
  try {
    importScripts("shared/profile_media_store.js");
  } catch (_error) {
    // Optional in environments where importScripts is unavailable.
  }

  const HOST_NAME = "com.lexishift.helper";
  const BRIDGE_KIND = "lexishift_helper_request_v1";
  const PROFILE_MEDIA_BRIDGE_KIND = "lexishift_profile_media_v1";
  const MAX_MEDIA_PAYLOAD_BYTES = 8 * 1024 * 1024;
  const MEDIA_CACHE_LIMIT = 6;
  const mediaDataUrlCache = new Map();

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

  function makeMediaError(code, message) {
    return { ok: false, error: { code, message } };
  }

  function trimMediaCache() {
    while (mediaDataUrlCache.size > MEDIA_CACHE_LIMIT) {
      const firstKey = mediaDataUrlCache.keys().next();
      if (firstKey && !firstKey.done) {
        mediaDataUrlCache.delete(firstKey.value);
      } else {
        break;
      }
    }
  }

  async function blobToDataUrl(blob, mimeType) {
    const type = String(mimeType || blob.type || "application/octet-stream");
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let binary = "";
    const chunkSize = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      const chunk = bytes.subarray(offset, offset + chunkSize);
      binary += String.fromCharCode(...chunk);
    }
    const base64 = btoa(binary);
    return `data:${type};base64,${base64}`;
  }

  async function handleProfileMediaRequest(message) {
    const action = String(message && message.action || "").trim();
    const payload = message && typeof message.payload === "object" ? message.payload : {};
    const mediaStore = globalThis.LexiShift && globalThis.LexiShift.profileMediaStore;
    if (!mediaStore) {
      return makeMediaError("media_store_unavailable", "Profile media store is unavailable.");
    }

    if (action === "get_background_data_url") {
      const assetId = String(payload.assetId || "").trim();
      if (!assetId) {
        return makeMediaError("invalid_request", "Missing assetId.");
      }
      const cached = mediaDataUrlCache.get(assetId);
      if (cached) {
        return { ok: true, data: cached };
      }
      const record = await mediaStore.getAsset(assetId);
      if (!record || !(record.blob instanceof Blob)) {
        return makeMediaError("asset_not_found", "Background image asset not found.");
      }
      const byteSize = Number(record.byte_size || record.blob.size || 0);
      if (byteSize > MAX_MEDIA_PAYLOAD_BYTES) {
        return makeMediaError(
          "asset_too_large",
          "Background image is too large for runtime transfer. Please use a smaller image."
        );
      }
      const dataUrl = await blobToDataUrl(record.blob, record.mime_type);
      const responseData = {
        assetId,
        dataUrl,
        mimeType: String(record.mime_type || record.blob.type || "application/octet-stream"),
        byteSize
      };
      mediaDataUrlCache.set(assetId, responseData);
      trimMediaCache();
      return { ok: true, data: responseData };
    }

    return makeMediaError("unsupported_action", `Unsupported media action: ${action || "(empty)"}.`);
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
    if (message && message.kind === PROFILE_MEDIA_BRIDGE_KIND) {
      handleProfileMediaRequest(message)
        .then((response) => sendResponse(response))
        .catch((error) => {
          sendResponse({
            ok: false,
            error: {
              code: "media_bridge_error",
              message: error && error.message ? error.message : "Media bridge request failed."
            }
          });
        });
      return true;
    }
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
