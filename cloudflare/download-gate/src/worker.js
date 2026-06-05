const SESSION_COOKIE = "ls_beta";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;
const MANIFEST_KEY = "releases/beta/latest.json";
const INSTALLER_PREFIX = "installers/beta/";
const CHECKSUM_PREFIX = "checksums/";
const RELEASE_PREFIX = "releases/";

const encoder = new TextEncoder();

export default {
  async fetch(request, env) {
    try {
      return await handleRequest(request, env);
    } catch (error) {
      console.error(error);
      return jsonResponse({ error: "internal_error" }, 500);
    }
  },
};

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const pathname = normalizePath(url.pathname);

  if (pathname === "/health") {
    return jsonResponse({ ok: true });
  }

  if ((request.method === "GET" || request.method === "HEAD") && (pathname === "/beta" || pathname === "/beta/")) {
    const session = await hasValidSession(request, env);
    const response = session
      ? await renderBetaDownloads(env)
      : renderBetaLogin(url.searchParams.get("next") || "/beta/");
    return withoutBodyForHead(request, response);
  }

  if (request.method === "POST" && pathname === "/beta/session") {
    return createBetaSession(request, env);
  }

  if (request.method === "POST" && pathname === "/beta/logout") {
    return redirectResponse("/beta/", {
      "Set-Cookie": clearCookieHeader(),
    });
  }

  if (request.method === "GET" && pathname === "/download") {
    return redirectResponse("/beta/");
  }

  if ((request.method === "GET" || request.method === "HEAD") && pathname.startsWith("/installers/")) {
    if (!pathname.startsWith(`/${INSTALLER_PREFIX}`)) {
      return jsonResponse({ error: "not_found" }, 404);
    }
    const session = await hasValidSession(request, env);
    if (!session) {
      return redirectResponse(`/beta/?next=${encodeURIComponent(pathname)}`);
    }
    return serveR2Object(request, env, pathname.slice(1), {
      cacheControl: "private, max-age=3600",
      forceAttachment: true,
    });
  }

  if ((request.method === "GET" || request.method === "HEAD") && pathname.startsWith(`/${RELEASE_PREFIX}`)) {
    return serveR2Object(request, env, pathname.slice(1), {
      cacheControl: "public, max-age=60",
      contentType: "application/json; charset=utf-8",
    });
  }

  if ((request.method === "GET" || request.method === "HEAD") && pathname.startsWith(`/${CHECKSUM_PREFIX}`)) {
    return serveR2Object(request, env, pathname.slice(1), {
      cacheControl: "public, max-age=300",
      contentType: "text/plain; charset=utf-8",
    });
  }

  return jsonResponse({ error: "not_found" }, 404);
}

async function createBetaSession(request, env) {
  const configuredPassword = getBetaPassword(env);
  const form = await request.formData();
  const submittedPassword = String(form.get("password") || "");
  const next = safeNextPath(String(form.get("next") || "/beta/"));

  if (!submittedPassword || submittedPassword !== configuredPassword) {
    return renderBetaLogin(next, "Password did not match.", 401);
  }

  return redirectResponse(next, {
    "Set-Cookie": await sessionCookieHeader(configuredPassword),
  });
}

async function renderBetaDownloads(env) {
  const manifest = await readManifest(env);
  const rows = manifest
    ? Object.entries(manifest.platforms || {})
        .map(([platform, meta]) => renderDownloadRow(platform, meta, manifest))
        .join("")
    : "";
  const releaseMeta = manifest
    ? `<p class="meta">Version ${escapeHtml(manifest.version || "unknown")} · ${escapeHtml(manifest.channel || "beta")}</p>`
    : `<p class="meta">No installer manifest has been uploaded yet.</p>`;

  return htmlResponse(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LexiShift beta downloads</title>
  ${inlineStyles()}
</head>
<body>
  <main class="shell">
    <p class="kicker">LexiShift private beta</p>
    <h1>Beta downloads</h1>
    ${releaseMeta}
    <div class="downloads">
      ${rows || `<p class="empty">The first beta artifact is not uploaded yet.</p>`}
    </div>
    <form method="post" action="/beta/logout">
      <button class="secondary" type="submit">Sign out</button>
    </form>
  </main>
</body>
</html>`);
}

function renderDownloadRow(platform, meta, manifest) {
  const href = safeDownloadHref(meta && meta.url);
  const filename = href ? basename(href) : "";
  const sha = meta && meta.sha256 ? String(meta.sha256) : "";
  const size = meta && Number.isFinite(Number(meta.size_bytes)) ? Number(meta.size_bytes) : 0;
  const checksumHref = checksumPath(manifest);
  return `<article class="download">
    <div>
      <h2>${escapeHtml(platformLabel(platform))}</h2>
      <p class="filename">${filename ? escapeHtml(filename) : "Installer pending"}</p>
      <dl class="artifact-meta">
        ${size ? `<div><dt>Size</dt><dd>${escapeHtml(formatBytes(size))}</dd></div>` : ""}
        <div><dt>SHA-256</dt><dd>${sha ? `<code>${escapeHtml(sha)}</code>` : "Pending"}</dd></div>
        ${
          checksumHref
            ? `<div><dt>Checksum file</dt><dd><a href="${escapeAttribute(checksumHref)}">SHA256SUMS.txt</a></dd></div>`
            : ""
        }
      </dl>
      ${renderTrustNotes(platform, meta)}
    </div>
    ${href ? `<a class="button" href="${escapeAttribute(href)}">Download</a>` : `<span class="disabled">Pending</span>`}
  </article>`;
}

function renderTrustNotes(platform, meta) {
  const normalized = String(platform || "").toLowerCase();
  const notes = [];
  if (normalized === "macos") {
    if (meta && meta.signed === true && meta.notarized === true) {
      notes.push("Signed and notarized for macOS.");
    } else {
      notes.push("Unsigned beta build. macOS may require Control-click > Open.");
      notes.push("Not notarized yet; this is expected for the current private beta.");
    }
  } else if (normalized === "windows") {
    if (meta && meta.signed === true) {
      notes.push("Signed Windows build.");
    } else {
      notes.push("Unsigned beta build. Windows SmartScreen may require More info > Run anyway.");
    }
  } else if (meta && meta.signed === false) {
    notes.push("Unsigned beta build.");
  }

  if (!notes.length) {
    return "";
  }
  return `<ul class="trust-notes">${notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>`;
}

function renderBetaLogin(next, errorMessage = "", status = 200) {
  return htmlResponse(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LexiShift beta access</title>
  ${inlineStyles()}
</head>
<body>
  <main class="shell">
    <p class="kicker">LexiShift private beta</p>
    <h1>Enter beta password</h1>
    <p class="meta">Installer downloads are limited to invited testers.</p>
    ${errorMessage ? `<p class="error">${escapeHtml(errorMessage)}</p>` : ""}
    <form method="post" action="/beta/session">
      <input type="hidden" name="next" value="${escapeAttribute(safeNextPath(next))}">
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Continue</button>
    </form>
  </main>
</body>
</html>`, status);
}

async function readManifest(env) {
  const object = await getBucket(env).get(MANIFEST_KEY);
  if (!object) {
    return null;
  }
  const text = await object.text();
  return JSON.parse(text);
}

async function serveR2Object(request, env, key, options = {}) {
  if (!isSafeObjectKey(key)) {
    return jsonResponse({ error: "invalid_object_key" }, 400);
  }

  const object = await getBucket(env).get(key);
  if (!object) {
    return jsonResponse({ error: "not_found" }, 404);
  }

  const headers = new Headers();
  if (typeof object.writeHttpMetadata === "function") {
    object.writeHttpMetadata(headers);
  }
  headers.set("etag", object.httpEtag || object.etag || "");
  headers.set("Cache-Control", options.cacheControl || "private, max-age=0");
  headers.set("X-Content-Type-Options", "nosniff");
  if (options.contentType && !headers.has("Content-Type")) {
    headers.set("Content-Type", options.contentType);
  }
  if (options.forceAttachment) {
    headers.set("Content-Disposition", `attachment; filename="${basename(key)}"`);
  }

  return new Response(request.method === "HEAD" ? null : object.body, {
    status: 200,
    headers,
  });
}

function getBucket(env) {
  if (!env || !env.DISTRIBUTION_BUCKET) {
    throw new Error("DISTRIBUTION_BUCKET binding is not configured");
  }
  return env.DISTRIBUTION_BUCKET;
}

function getBetaPassword(env) {
  if (!env || !env.BETA_DOWNLOAD_PASSWORD) {
    throw new Error("BETA_DOWNLOAD_PASSWORD secret is not configured");
  }
  return String(env.BETA_DOWNLOAD_PASSWORD);
}

async function hasValidSession(request, env) {
  const password = getBetaPassword(env);
  const cookieHeader = request.headers.get("Cookie") || "";
  const cookie = parseCookie(cookieHeader, SESSION_COOKIE);
  if (!cookie) {
    return false;
  }

  const [issuedAtRaw, signature] = cookie.split(".");
  const issuedAt = Number(issuedAtRaw);
  if (!Number.isFinite(issuedAt) || !signature) {
    return false;
  }

  const ageSeconds = Math.floor(Date.now() / 1000) - issuedAt;
  if (ageSeconds < 0 || ageSeconds > SESSION_MAX_AGE_SECONDS) {
    return false;
  }

  const expected = await signSession(issuedAtRaw, password);
  return constantTimeEqual(signature, expected);
}

async function sessionCookieHeader(secret) {
  const issuedAt = String(Math.floor(Date.now() / 1000));
  const signature = await signSession(issuedAt, secret);
  const value = `${issuedAt}.${signature}`;
  return `${SESSION_COOKIE}=${value}; Max-Age=${SESSION_MAX_AGE_SECONDS}; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

function clearCookieHeader() {
  return `${SESSION_COOKIE}=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

async function signSession(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(`lexishift-beta:${value}`));
  return hex(signature);
}

function hex(buffer) {
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function constantTimeEqual(a, b) {
  if (a.length !== b.length) {
    return false;
  }
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function parseCookie(header, name) {
  return header
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

function safeNextPath(value) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/beta/";
  }
  return normalizePath(value);
}

function safeDownloadHref(value) {
  if (!value) {
    return "";
  }
  const url = new URL(String(value), "https://downloads.lexishift.app");
  if (url.hostname !== "downloads.lexishift.app") {
    return "";
  }
  return url.pathname.startsWith(`/${INSTALLER_PREFIX}`) ? url.pathname : "";
}

function checksumPath(manifest) {
  const channel = manifest && typeof manifest.channel === "string" ? manifest.channel : "";
  const version = manifest && typeof manifest.version === "string" ? manifest.version : "";
  if (!channel || !version || !/^[a-z0-9._-]+$/i.test(channel) || !/^[a-z0-9._-]+$/i.test(version)) {
    return "";
  }
  return `/${CHECKSUM_PREFIX}${channel}/${version}/SHA256SUMS.txt`;
}

function platformLabel(platform) {
  const normalized = String(platform || "").toLowerCase();
  if (normalized === "macos") {
    return "macOS";
  }
  if (normalized === "windows") {
    return "Windows";
  }
  return platform || "Platform";
}

function normalizePath(pathname) {
  const normalized = pathname.replace(/\/{2,}/g, "/");
  return normalized.length > 1 && normalized.endsWith("/") ? normalized.slice(0, -1) : normalized;
}

function isSafeObjectKey(key) {
  return key && !key.startsWith("/") && !key.includes("..") && !key.includes("\\");
}

function basename(key) {
  return key.split("/").pop().replace(/["\\]/g, "");
}

function formatBytes(size) {
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function redirectResponse(location, headers = {}) {
  return new Response(null, {
    status: 302,
    headers: {
      Location: location,
      ...headers,
    },
  });
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload) + "\n", {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function htmlResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
    },
  });
}

function withoutBodyForHead(request, response) {
  if (request.method !== "HEAD") {
    return response;
  }
  return new Response(null, {
    status: response.status,
    headers: response.headers,
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    const escapes = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return escapes[char];
  });
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

function inlineStyles() {
  return `<style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #f4f8f6;
      color: #173c46;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    .shell {
      width: min(42rem, calc(100% - 2rem));
      margin: 8vh auto;
      padding: 1.25rem;
      border: 1px solid #d7e3e0;
      border-radius: 8px;
      background: #ffffff;
      box-shadow: 0 14px 36px rgba(23, 60, 70, 0.1);
    }
    .kicker {
      margin: 0 0 0.35rem;
      color: #5b6971;
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0 0 0.55rem;
      font-size: clamp(1.8rem, 6vw, 2.6rem);
      line-height: 1.05;
    }
    h2 {
      margin: 0;
      font-size: 1.05rem;
      text-transform: capitalize;
    }
    .meta {
      margin: 0 0 1rem;
      color: #526a72;
    }
    form {
      display: grid;
      gap: 0.7rem;
    }
    label {
      font-weight: 800;
    }
    input {
      min-height: 2.8rem;
      border: 1px solid #aebfbb;
      border-radius: 8px;
      padding: 0.6rem 0.72rem;
      font: inherit;
    }
    button,
    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 2.8rem;
      border: 1px solid #1f6f5f;
      border-radius: 8px;
      padding: 0.58rem 0.9rem;
      background: #1f6f5f;
      color: #ffffff;
      font: inherit;
      font-weight: 800;
      text-decoration: none;
      cursor: pointer;
    }
    .secondary {
      margin-top: 1rem;
      border-color: #9fb8b3;
      background: #ffffff;
      color: #1c4f5a;
    }
    .downloads {
      display: grid;
      gap: 0.75rem;
    }
    .download {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 0.85rem;
      border: 1px solid #d7e3e0;
      border-radius: 8px;
      background: #f7fbfa;
    }
    .download p,
    .empty {
      margin: 0.2rem 0 0;
      color: #526a72;
      overflow-wrap: anywhere;
    }
    .filename {
      font-weight: 800;
    }
    .artifact-meta {
      display: grid;
      gap: 0.35rem;
      margin: 0.7rem 0 0;
    }
    .artifact-meta div {
      display: grid;
      grid-template-columns: 7.4rem minmax(0, 1fr);
      gap: 0.55rem;
    }
    .artifact-meta dt {
      color: #526a72;
      font-weight: 800;
    }
    .artifact-meta dd {
      min-width: 0;
      margin: 0;
      color: #213f49;
      overflow-wrap: anywhere;
    }
    .artifact-meta code {
      font-size: 0.82rem;
      white-space: normal;
    }
    .trust-notes {
      margin: 0.75rem 0 0;
      padding-left: 1.15rem;
      color: #81510f;
    }
    .trust-notes li + li {
      margin-top: 0.18rem;
    }
    .disabled,
    .error {
      color: #9b5f11;
      font-weight: 800;
    }
    @media (max-width: 34rem) {
      .download {
        align-items: stretch;
        flex-direction: column;
      }
      .artifact-meta div {
        grid-template-columns: 1fr;
        gap: 0.1rem;
      }
      .button {
        width: 100%;
      }
    }
  </style>`;
}
