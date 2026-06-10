from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROFILE_MEDIA_STORE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/profile/profile_media_store.js"
)


def _run_node(script: str) -> None:
    result = subprocess.run(
        ["node"],
        input=script,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "Node profile-media-store test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionProfileMediaStore(unittest.TestCase):
    def test_repairs_existing_database_with_missing_assets_store(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const mediaStorePath = {json.dumps(str(PROFILE_MEDIA_STORE_JS))};

function asyncCall(fn) {{
  setTimeout(fn, 0);
}}

class NameList {{
  constructor(values) {{
    this.values = Array.from(values || []);
  }}

  contains(value) {{
    return this.values.includes(value);
  }}
}}

class FakeIndex {{
  constructor(storeRecord, indexRecord, tx) {{
    this.storeRecord = storeRecord;
    this.indexRecord = indexRecord;
    this.tx = tx;
  }}

  getAll(range) {{
    const request = {{}};
    asyncCall(() => {{
      const keyPath = this.indexRecord.keyPath;
      const rows = Array.from(this.storeRecord.records.values()).filter((record) => {{
        return !range || record[keyPath] === range.value;
      }});
      request.result = rows;
      if (typeof request.onsuccess === "function") {{
        request.onsuccess();
      }}
      this.tx.completeSoon();
    }});
    return request;
  }}
}}

class FakeObjectStore {{
  constructor(storeRecord, tx) {{
    this.storeRecord = storeRecord;
    this.tx = tx || null;
  }}

  get indexNames() {{
    return new NameList(this.storeRecord.indexes.keys());
  }}

  createIndex(name, keyPath, options) {{
    this.storeRecord.indexes.set(name, {{
      keyPath,
      unique: options && options.unique === true
    }});
    return {{}};
  }}

  put(record) {{
    const request = {{}};
    asyncCall(() => {{
      this.storeRecord.records.set(record.asset_id, record);
      request.result = record.asset_id;
      if (typeof request.onsuccess === "function") {{
        request.onsuccess();
      }}
      if (this.tx) {{
        this.tx.completeSoon();
      }}
    }});
    return request;
  }}

  get(assetId) {{
    const request = {{}};
    asyncCall(() => {{
      request.result = this.storeRecord.records.get(assetId);
      if (typeof request.onsuccess === "function") {{
        request.onsuccess();
      }}
      if (this.tx) {{
        this.tx.completeSoon();
      }}
    }});
    return request;
  }}

  delete(assetId) {{
    const request = {{}};
    asyncCall(() => {{
      this.storeRecord.records.delete(assetId);
      request.result = undefined;
      if (typeof request.onsuccess === "function") {{
        request.onsuccess();
      }}
      if (this.tx) {{
        this.tx.completeSoon();
      }}
    }});
    return request;
  }}

  index(name) {{
    if (!this.storeRecord.indexes.has(name)) {{
      throw new Error(`Index not found: ${{name}}`);
    }}
    return new FakeIndex(this.storeRecord, this.storeRecord.indexes.get(name), this.tx);
  }}
}}

class FakeTransaction {{
  constructor(db) {{
    this.db = db;
    this.error = null;
    this.completed = false;
  }}

  objectStore(name) {{
    if (!this.db.stores.has(name)) {{
      throw new Error("One of the specified object stores was not found.");
    }}
    return new FakeObjectStore(this.db.stores.get(name), this);
  }}

  abort() {{
    this.error = new Error("Transaction aborted.");
    asyncCall(() => {{
      if (typeof this.onabort === "function") {{
        this.onabort();
      }}
    }});
  }}

  completeSoon() {{
    if (this.completed || this.error) {{
      return;
    }}
    this.completed = true;
    asyncCall(() => {{
      if (!this.error && typeof this.oncomplete === "function") {{
        this.oncomplete();
      }}
    }});
  }}
}}

class FakeDb {{
  constructor(version) {{
    this.version = version;
    this.stores = new Map();
    this.closed = false;
    this.onversionchange = null;
  }}

  get objectStoreNames() {{
    return new NameList(this.stores.keys());
  }}

  createObjectStore(name, options) {{
    const storeRecord = {{
      keyPath: options && options.keyPath,
      records: new Map(),
      indexes: new Map()
    }};
    this.stores.set(name, storeRecord);
    return new FakeObjectStore(storeRecord, null);
  }}

  transaction(name) {{
    if (!this.stores.has(name)) {{
      throw new Error("One of the specified object stores was not found.");
    }}
    return new FakeTransaction(this);
  }}

  close() {{
    this.closed = true;
  }}
}}

const malformedDb = new FakeDb(1);
const openCalls = [];
const indexedDB = {{
  open(_name, version) {{
    openCalls.push(version === undefined ? null : Number(version));
    const request = {{}};
    asyncCall(() => {{
      const requestedVersion = version === undefined ? null : Number(version);
      if (requestedVersion !== null && requestedVersion < malformedDb.version) {{
        request.error = new Error("VersionError");
        if (typeof request.onerror === "function") {{
          request.onerror();
        }}
        return;
      }}
      request.result = malformedDb;
      if (requestedVersion !== null && requestedVersion > malformedDb.version) {{
        malformedDb.version = requestedVersion;
        request.transaction = new FakeTransaction(malformedDb);
        if (typeof request.onupgradeneeded === "function") {{
          request.onupgradeneeded();
        }}
      }}
      if (typeof request.onsuccess === "function") {{
        request.onsuccess();
      }}
    }});
    return request;
  }}
}};

const context = vm.createContext({{
  Blob,
  console,
  indexedDB,
  setTimeout,
  IDBKeyRange: {{
    only(value) {{
      return {{ value }};
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(mediaStorePath, "utf8"), context, {{ filename: mediaStorePath }});

(async () => {{
  assert.equal(malformedDb.objectStoreNames.contains("assets"), false);
  const image = new Blob(["image"], {{ type: "image/png" }});
  const meta = await context.LexiShift.profileMediaStore.upsertProfileBackground("suisui", image, {{}});

  assert.deepEqual(openCalls, [null, 2]);
  assert.equal(malformedDb.version, 2);
  assert.equal(malformedDb.objectStoreNames.contains("assets"), true);
  assert.equal(malformedDb.stores.get("assets").indexes.has("by_profile_id"), true);
  assert.equal(meta.profile_id, "suisui");
  assert.equal(meta.kind, "profile_background");
  assert.equal(meta.mime_type, "image/png");

  const record = await context.LexiShift.profileMediaStore.getAsset(meta.asset_id);
  assert.equal(record.profile_id, "suisui");
  assert.equal(await record.blob.text(), "image");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
