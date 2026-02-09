/*
Archived: web-page profile background runtime path removed from LexiShift production.
Date: 2026-02-09

This file intentionally stores the removed implementation for personal reuse.
It is not loaded by the extension manifest.

===============================================================================
shared/profile_media_bridge.js (removed from runtime wiring)
===============================================================================

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

===============================================================================
background.js profile media branch (removed)
===============================================================================

try {
  importScripts("shared/profile_media_store.js");
} catch (_error) {
  // Optional in environments where importScripts is unavailable.
}

const PROFILE_MEDIA_BRIDGE_KIND = "lexishift_profile_media_v1";
const MAX_MEDIA_PAYLOAD_BYTES = 8 * 1024 * 1024;
const MEDIA_CACHE_LIMIT = 6;
const mediaDataUrlCache = new Map();

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

// In chrome.runtime.onMessage.addListener:
// if (message && message.kind === PROFILE_MEDIA_BRIDGE_KIND) {
//   handleProfileMediaRequest(message)
//     .then((response) => sendResponse(response))
//     .catch((error) => {
//       sendResponse({
//         ok: false,
//         error: {
//           code: "media_bridge_error",
//           message: error && error.message ? error.message : "Media bridge request failed."
//         }
//       });
//     });
//   return true;
// }

===============================================================================
content/ui.js injected web-page background layer (removed)
===============================================================================

const PROFILE_BACKGROUND_ID = "lexishift-profile-background";
let profileBackgroundLayer = null;

// In ensureStyle:
// .lexishift-profile-background{position:fixed;inset:0;pointer-events:none;z-index:2147483000;
//   background-size:cover;background-position:center;background-repeat:no-repeat;
//   mix-blend-mode:soft-light;opacity:0;transition:opacity 180ms ease;}

function escapeCssUrl(url) {
  return String(url || "").replace(/["\\\n\r]/g, "\\$&");
}

function clampOpacity(value) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return 0.18;
  }
  return Math.min(1, Math.max(0, parsed));
}

function ensureProfileBackgroundLayer() {
  let layer = profileBackgroundLayer || document.getElementById(PROFILE_BACKGROUND_ID);
  if (layer) {
    profileBackgroundLayer = layer;
    return layer;
  }
  layer = document.createElement("div");
  layer.id = PROFILE_BACKGROUND_ID;
  layer.className = "lexishift-profile-background";
  const parent = document.documentElement || document.body;
  if (!parent) {
    return null;
  }
  parent.appendChild(layer);
  profileBackgroundLayer = layer;
  return layer;
}

function clearProfileBackground() {
  const layer = profileBackgroundLayer || document.getElementById(PROFILE_BACKGROUND_ID);
  if (!layer) {
    return;
  }
  layer.remove();
  profileBackgroundLayer = null;
}

function applyProfileBackground(config = {}) {
  const enabled = config.enabled === true;
  const dataUrl = enabled ? String(config.dataUrl || "").trim() : "";
  if (!enabled || !dataUrl) {
    clearProfileBackground();
    return;
  }
  const layer = ensureProfileBackgroundLayer();
  if (!layer) {
    return;
  }
  layer.style.backgroundImage = `url("${escapeCssUrl(dataUrl)}")`;
  layer.style.opacity = String(clampOpacity(config.opacity));
}

===============================================================================
content_script.js integration points (removed)
===============================================================================

const profileMediaBridge = root.profileMediaBridge;
let profileBackgroundDataUrlCache = new Map();

function clampProfileBackgroundOpacity(value) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return 0.18;
  }
  return Math.min(1, Math.max(0, parsed));
}

async function resolveProfileBackgroundDataUrl(settings) {
  const assetId = String(settings && settings.profileBackgroundAssetId || "").trim();
  const enabled = settings && settings.enabled !== false && settings.profileBackgroundEnabled === true;
  if (!enabled || !assetId) {
    return { dataUrl: "", error: null };
  }
  const cached = profileBackgroundDataUrlCache.get(assetId);
  if (cached) {
    return { dataUrl: cached, error: null };
  }
  if (!profileMediaBridge || typeof profileMediaBridge.getBackgroundDataUrl !== "function") {
    return { dataUrl: "", error: "Profile media bridge unavailable." };
  }
  const response = await profileMediaBridge.getBackgroundDataUrl(assetId, 6000);
  if (!response || response.ok === false) {
    const message = response && response.error && response.error.message
      ? response.error.message
      : "Failed to load profile background.";
    return { dataUrl: "", error: message };
  }
  const dataUrl = response.data && typeof response.data.dataUrl === "string"
    ? response.data.dataUrl
    : "";
  if (!dataUrl) {
    return { dataUrl: "", error: "Profile background asset is empty." };
  }
  profileBackgroundDataUrlCache.set(assetId, dataUrl);
  if (profileBackgroundDataUrlCache.size > 6) {
    const first = profileBackgroundDataUrlCache.keys().next();
    if (first && !first.done) {
      profileBackgroundDataUrlCache.delete(first.value);
    }
  }
  return { dataUrl, error: null };
}

// In applySettings:
// const profileBackgroundOpacity = clampProfileBackgroundOpacity(currentSettings.profileBackgroundOpacity);
// const backgroundResult = await resolveProfileBackgroundDataUrl(currentSettings);
// const profileBackgroundDataUrl = backgroundResult.dataUrl || "";
// if (typeof applyProfileBackground === "function") {
//   applyProfileBackground({
//     enabled: currentSettings.enabled !== false && currentSettings.profileBackgroundEnabled === true,
//     dataUrl: profileBackgroundDataUrl,
//     opacity: profileBackgroundOpacity
//   });
// }

*/
