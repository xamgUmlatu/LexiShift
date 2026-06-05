import assert from "node:assert/strict";
import test from "node:test";

import worker from "../src/worker.js";

const fixturePassword = "fixture-beta-password";

const manifest = {
  schema_version: 1,
  channel: "beta",
  version: "0.1.0",
  platforms: {
    macos: {
      url: "https://downloads.lexishift.app/installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg",
      sha256: "a".repeat(64),
      size_bytes: 1024 * 1024 * 42,
    },
  },
};

test("health route returns ok", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/health");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
});

test("beta gate does not expose the password", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/beta/");
  const body = await response.text();
  assert.equal(response.status, 200);
  assert.match(body, /Enter beta password/);
  assert.doesNotMatch(body, new RegExp(`\\b${fixturePassword}\\b`));
});

test("beta gate supports smoke-test HEAD requests", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/beta/", {
    method: "HEAD",
  });
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") || "", /text\/html/);
  assert.equal(await response.text(), "");
});

test("wrong password is rejected", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/beta/session", {
    method: "POST",
    body: new URLSearchParams({ password: "wrong" }),
  });
  assert.equal(response.status, 401);
});

test("correct password creates a signed session cookie", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/beta/session", {
    method: "POST",
    body: new URLSearchParams({ password: fixturePassword }),
  });
  assert.equal(response.status, 302);
  assert.match(response.headers.get("location") || "", /^\/beta\/?$/);
  assert.match(response.headers.get("set-cookie") || "", /ls_beta=/);
  assert.match(response.headers.get("set-cookie") || "", /HttpOnly/);
});

test("installer redirects to beta gate without a session", async () => {
  const response = await fetchWorker(
    "https://downloads.lexishift.app/installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg",
  );
  assert.equal(response.status, 302);
  assert.match(response.headers.get("location") || "", /^\/beta\//);
});

test("installer streams from R2 with a valid session", async () => {
  const session = await fetchWorker("https://downloads.lexishift.app/beta/session", {
    method: "POST",
    body: new URLSearchParams({ password: fixturePassword }),
  });
  const response = await fetchWorker(
    "https://downloads.lexishift.app/installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg",
    {
      headers: { Cookie: session.headers.get("set-cookie") || "" },
    },
  );
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "fake dmg");
  assert.match(response.headers.get("content-disposition") || "", /LexiShift-0.1.0.dmg/);
});

test("release manifest is public", async () => {
  const response = await fetchWorker("https://downloads.lexishift.app/releases/beta/latest.json");
  assert.equal(response.status, 200);
  assert.equal((await response.json()).version, "0.1.0");
});

function fetchWorker(url, init) {
  return worker.fetch(new Request(url, init), makeEnv());
}

function makeEnv() {
  const objects = new Map([
    ["releases/beta/latest.json", JSON.stringify(manifest)],
    ["installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg", "fake dmg"],
  ]);
  return {
    BETA_DOWNLOAD_PASSWORD: fixturePassword,
    DISTRIBUTION_BUCKET: {
      async get(key) {
        if (!objects.has(key)) {
          return null;
        }
        const body = objects.get(key);
        return {
          body,
          httpEtag: `"${key}"`,
          async text() {
            return body;
          },
          writeHttpMetadata(headers) {
            headers.set("Content-Type", key.endsWith(".json") ? "application/json" : "application/octet-stream");
          },
        };
      },
    },
  };
}
