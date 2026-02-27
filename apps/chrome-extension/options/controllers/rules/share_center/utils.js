(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizePath(path) {
    const normalized = String(path || "").trim();
    return normalized || "";
  }

  function pathBasename(path, unknownLabel, normalizePathFn) {
    const normalize = typeof normalizePathFn === "function" ? normalizePathFn : normalizePath;
    const normalized = normalize(path);
    if (!normalized) {
      return String(unknownLabel || "(unknown)");
    }
    const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
    return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
  }

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function normalizeSrsPairKey(rawPair, fallbackPair, normalizePairKeyFn) {
    const fallback = String(fallbackPair || "en-en").trim() || "en-en";
    if (typeof normalizePairKeyFn === "function") {
      return normalizePairKeyFn(rawPair || fallback);
    }
    const normalized = String(rawPair || fallback).trim();
    return normalized || fallback;
  }

  function hasMeaningfulValue(value, depth, isObjectFn) {
    const isObjectLike = typeof isObjectFn === "function" ? isObjectFn : isObject;
    const level = Number.isFinite(Number(depth)) ? Number(depth) : 0;
    if (level > 8) {
      return false;
    }
    if (value === null || value === undefined) {
      return false;
    }
    if (Array.isArray(value)) {
      if (!value.length) {
        return false;
      }
      return value.some((entry) => hasMeaningfulValue(entry, level + 1, isObjectLike));
    }
    if (isObjectLike(value)) {
      const keys = Object.keys(value);
      if (!keys.length) {
        return false;
      }
      return keys.some((key) => hasMeaningfulValue(value[key], level + 1, isObjectLike));
    }
    if (typeof value === "string") {
      return String(value).trim().length > 0;
    }
    if (typeof value === "number") {
      return Number.isFinite(value);
    }
    if (typeof value === "boolean") {
      return true;
    }
    return true;
  }

  function slugifyFileSegment(value, fallback) {
    const normalized = String(value || "").trim().toLowerCase();
    const slug = normalized
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || String(fallback || "export");
  }

  function resolveExportFileName(scope, profileId) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const profileSlug = slugifyFileSegment(profileId, "profile");
    const baseByScope = {
      profile: "profile",
      bundle: "selection",
      ruleset: "ruleset",
      srs_pair: "srs-pair",
      appearance_theme: "appearance",
      module_item: "module"
    };
    const base = Object.prototype.hasOwnProperty.call(baseByScope, scope)
      ? baseByScope[scope]
      : "selection";
    return `lexishift-share-${base}-${profileSlug}-${timestamp}.json`;
  }

  function formatByteSize(sizeBytes) {
    const bytes = Number(sizeBytes);
    if (!Number.isFinite(bytes) || bytes < 0) {
      return "0 B";
    }
    if (bytes < 1024) {
      return `${Math.round(bytes)} B`;
    }
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function downloadJsonFile(content, fileName) {
    const blob = new Blob([content], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    return blob.size;
  }

  root.optionsShareCenterUtils = {
    normalizePath,
    pathBasename,
    isObject,
    normalizeSrsPairKey,
    hasMeaningfulValue,
    slugifyFileSegment,
    resolveExportFileName,
    formatByteSize,
    downloadJsonFile
  };
})();
