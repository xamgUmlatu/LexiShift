#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const extensionRoot = path.join(repoRoot, "apps", "chrome-extension");
const helperIdsPath = path.join(repoRoot, "apps", "gui", "resources", "helper_extension_ids.json");
const reportDir = path.join(repoRoot, "docs", "runbooks", "cws_preflight_reports");

const findings = [];

function addFinding(level, check, message, detail = "") {
  findings.push({ level, check, message, detail });
}

function toPosix(filePath) {
  return filePath.split(path.sep).join("/");
}

function existsFile(root, relPath) {
  const absolute = path.join(root, relPath);
  return fs.existsSync(absolute) && fs.statSync(absolute).isFile();
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function walkFiles(dirPath) {
  const out = [];
  function walk(current) {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const resolved = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(resolved);
      } else if (entry.isFile()) {
        out.push(resolved);
      }
    }
  }
  walk(dirPath);
  return out;
}

function patternToRegex(globLike) {
  const escaped = globLike
    .split("*")
    .map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"))
    .join("[^/]*");
  return new RegExp(`^${escaped}$`);
}

function matchingFilesForPattern(root, pattern, relFiles) {
  const regex = patternToRegex(toPosix(pattern));
  return relFiles.filter((rel) => regex.test(rel));
}

function parsePngSize(filePath) {
  const buffer = fs.readFileSync(filePath);
  if (buffer.length < 24) {
    throw new Error("PNG too small.");
  }
  const signature = "89504e470d0a1a0a";
  if (buffer.subarray(0, 8).toString("hex") !== signature) {
    throw new Error("Not a PNG file.");
  }
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20)
  };
}

function extractManifestMessageKeys(manifest) {
  const keys = new Set();
  function walk(value) {
    if (typeof value === "string") {
      const regex = /__MSG_([A-Za-z0-9_@]+)__/g;
      let match;
      while ((match = regex.exec(value)) !== null) {
        keys.add(match[1]);
      }
      return;
    }
    if (Array.isArray(value)) {
      value.forEach(walk);
      return;
    }
    if (value && typeof value === "object") {
      Object.values(value).forEach(walk);
    }
  }
  walk(manifest);
  return [...keys].sort();
}

function checkManifestReferences(manifest, relFiles) {
  const checks = [];
  const missing = [];

  function checkDirectRef(relPath, label) {
    checks.push({ relPath, label });
    if (!existsFile(extensionRoot, relPath)) {
      missing.push(`${label}: ${relPath}`);
    }
  }

  const iconMap = manifest.icons || {};
  Object.entries(iconMap).forEach(([size, relPath]) => {
    checkDirectRef(relPath, `icon ${size}`);
  });

  if (manifest.background && manifest.background.service_worker) {
    checkDirectRef(manifest.background.service_worker, "background service worker");
  }
  if (manifest.options_page) {
    checkDirectRef(manifest.options_page, "options page");
  }

  const contentScripts = Array.isArray(manifest.content_scripts) ? manifest.content_scripts : [];
  contentScripts.forEach((contentScript, idx) => {
    const jsFiles = Array.isArray(contentScript.js) ? contentScript.js : [];
    jsFiles.forEach((relPath) => checkDirectRef(relPath, `content script[${idx}]`));
  });

  const resources = Array.isArray(manifest.web_accessible_resources) ? manifest.web_accessible_resources : [];
  resources.forEach((entry, idx) => {
    const listed = Array.isArray(entry.resources) ? entry.resources : [];
    listed.forEach((resourcePattern) => {
      if (resourcePattern.includes("*")) {
        const matches = matchingFilesForPattern(extensionRoot, resourcePattern, relFiles);
        if (matches.length === 0) {
          missing.push(`web_accessible_resources[${idx}] pattern has no matches: ${resourcePattern}`);
        }
      } else if (!existsFile(extensionRoot, resourcePattern)) {
        missing.push(`web_accessible_resources[${idx}] missing file: ${resourcePattern}`);
      }
    });
  });

  if (missing.length) {
    addFinding("FAIL", "Manifest references", "One or more manifest-referenced files are missing.", missing.join("\n"));
  } else {
    addFinding("PASS", "Manifest references", "All manifest-referenced files were found.");
  }
}

function checkIconDimensions(manifest) {
  const iconMap = manifest.icons || {};
  const issues = [];
  Object.entries(iconMap).forEach(([sizeText, relPath]) => {
    const expected = Number(sizeText);
    const absolute = path.join(extensionRoot, relPath);
    if (!Number.isFinite(expected)) {
      issues.push(`Invalid icon size key: ${sizeText}`);
      return;
    }
    try {
      const parsed = parsePngSize(absolute);
      if (parsed.width !== expected || parsed.height !== expected) {
        issues.push(`${relPath}: expected ${expected}x${expected}, got ${parsed.width}x${parsed.height}`);
      }
    } catch (error) {
      issues.push(`${relPath}: ${error.message}`);
    }
  });
  if (issues.length) {
    addFinding("FAIL", "Icon dimensions", "Icon files do not match declared sizes.", issues.join("\n"));
  } else {
    addFinding("PASS", "Icon dimensions", "Declared icon sizes match actual PNG dimensions.");
  }
}

function checkLocaleKeys(manifest) {
  const localesDir = path.join(extensionRoot, "_locales");
  const availableLocales = fs.existsSync(localesDir)
    ? fs.readdirSync(localesDir).filter((name) => {
        const filePath = path.join(localesDir, name, "messages.json");
        return fs.existsSync(filePath);
      })
    : [];

  if (availableLocales.length === 0) {
    addFinding("FAIL", "Locales", "No locale catalogs were found under _locales.");
    return;
  }

  const defaultLocale = manifest.default_locale;
  if (!defaultLocale) {
    addFinding("FAIL", "Locales", "manifest.default_locale is missing.");
    return;
  }
  if (!availableLocales.includes(defaultLocale)) {
    addFinding("FAIL", "Locales", `Default locale '${defaultLocale}' is missing a messages.json catalog.`);
    return;
  }

  const requiredKeys = extractManifestMessageKeys(manifest);
  if (requiredKeys.length === 0) {
    addFinding("PASS", "Locale keys", "Manifest has no __MSG_* placeholders.");
    return;
  }

  const missingByLocale = [];
  for (const locale of availableLocales) {
    const messagesPath = path.join(localesDir, locale, "messages.json");
    const messages = readJson(messagesPath);
    const missing = requiredKeys.filter((key) => !messages[key] || typeof messages[key].message !== "string");
    if (missing.length) {
      missingByLocale.push(`${locale}: ${missing.join(", ")}`);
    }
  }

  if (missingByLocale.length) {
    addFinding(
      "FAIL",
      "Locale keys",
      "Some locales are missing manifest placeholder keys.",
      missingByLocale.join("\n")
    );
  } else {
    addFinding("PASS", "Locale keys", "All manifest __MSG_* placeholder keys exist in all locale catalogs.");
  }
}

function checkHelperExtensionIds() {
  if (!fs.existsSync(helperIdsPath)) {
    addFinding("WARN", "Helper extension IDs", "helper_extension_ids.json not found; skipping fixed-ID validation.");
    return;
  }
  const data = readJson(helperIdsPath);
  const envs = Array.isArray(data.environments) ? data.environments : [];
  const placeholders = new Set(["", "__FILL_ME__", "<FILL_ME>"]);
  const issues = [];
  envs.forEach((env) => {
    if (!env || typeof env !== "object") return;
    if (env.fixed === true) {
      const id = String(env.extension_id || "").trim();
      if (placeholders.has(id)) {
        issues.push(`${env.key || "(unknown key)"} has placeholder extension_id`);
      }
    }
  });
  if (issues.length) {
    addFinding(
      "FAIL",
      "Helper extension IDs",
      "Fixed helper environments still contain placeholder extension IDs.",
      issues.join("\n")
    );
  } else {
    addFinding("PASS", "Helper extension IDs", "Fixed helper environments use non-placeholder extension IDs.");
  }
}

function checkBroadPermissionPosture(manifest) {
  const contentScripts = Array.isArray(manifest.content_scripts) ? manifest.content_scripts : [];
  const broad = contentScripts.some((entry) => Array.isArray(entry.matches) && entry.matches.includes("<all_urls>"));
  const aboutBlank = contentScripts.some((entry) => entry.match_about_blank === true);
  const allFrames = contentScripts.some((entry) => entry.all_frames === true);

  if (broad) {
    addFinding(
      "WARN",
      "Broad host access",
      "Content scripts include <all_urls>. Manual CWS review scrutiny is expected."
    );
  } else {
    addFinding("PASS", "Broad host access", "Content scripts do not use <all_urls>.");
  }
  if (aboutBlank) {
    addFinding("INFO", "about:blank injection", "match_about_blank is enabled for at least one content script.");
  }
  if (allFrames) {
    addFinding("INFO", "All frames injection", "all_frames is enabled for at least one content script.");
  }
}

function checkRemoteUrls(relFiles) {
  const urlRegex = /https?:\/\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+/g;
  const hosts = new Map();
  const scoped = relFiles.filter((rel) => rel.endsWith(".js") || rel.endsWith(".html") || rel.endsWith(".json"));
  for (const rel of scoped) {
    const absolute = path.join(extensionRoot, rel);
    const content = fs.readFileSync(absolute, "utf8");
    const matches = content.match(urlRegex);
    if (!matches) continue;
    for (const match of matches) {
      try {
        const host = new URL(match).host;
        if (!hosts.has(host)) {
          hosts.set(host, new Set());
        }
        if (hosts.get(host).size < 5) {
          hosts.get(host).add(rel);
        }
      } catch (_error) {
        // Ignore invalid URL parse attempts.
      }
    }
  }

  if (hosts.size === 0) {
    addFinding("PASS", "Remote URLs", "No literal remote URLs were found in extension files.");
    return;
  }

  const details = [...hosts.entries()]
    .map(([host, refs]) => `${host}: ${[...refs].join(", ")}`)
    .join("\n");
  addFinding("WARN", "Remote URLs", "Literal remote URLs were found. Ensure they are expected and policy-declared.", details);
}

function checkPackagingNoise(relFiles) {
  const noise = relFiles.filter((rel) => {
    const base = path.basename(rel);
    return base === ".DS_Store" || base.endsWith(".tmp") || base.endsWith(".swp");
  });
  if (noise.length) {
    addFinding("FAIL", "Package noise", "Unexpected temporary/system files found in extension tree.", noise.join("\n"));
  } else {
    addFinding("PASS", "Package noise", "No obvious temporary/system files found in extension tree.");
  }
}

function buildManualChecklistMarkdown() {
  return [
    "## Manual Upload Checklist",
    "",
    "- [ ] Privacy policy reviewed and current behavior (including local-only sensitive data handling) is accurately described.",
    "- [ ] Permission scope reviewed; any new permissions/hosts are intentional and documented for reviewer notes.",
    "- [ ] Helper onboarding flow tested on clean profile (helper present and helper missing).",
    "- [ ] No debug/dev-only artifacts in package (temporary files, stale assets, test-only toggles).",
    "- [ ] Release package hash recorded and upload timestamp noted by maintainer."
  ].join("\n");
}

function timestampUtc() {
  const now = new Date();
  const yyyy = String(now.getUTCFullYear());
  const mm = String(now.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(now.getUTCDate()).padStart(2, "0");
  const hh = String(now.getUTCHours()).padStart(2, "0");
  const mi = String(now.getUTCMinutes()).padStart(2, "0");
  const ss = String(now.getUTCSeconds()).padStart(2, "0");
  return `${yyyy}${mm}${dd}_${hh}${mi}${ss}Z`;
}

function renderReport(reportName) {
  const failCount = findings.filter((f) => f.level === "FAIL").length;
  const warnCount = findings.filter((f) => f.level === "WARN").length;
  const passCount = findings.filter((f) => f.level === "PASS").length;
  const infoCount = findings.filter((f) => f.level === "INFO").length;
  const gateResult = failCount === 0 ? "PASS" : "FAIL";

  const lines = [];
  lines.push(`# CWS Preflight Report: ${reportName}`);
  lines.push("");
  lines.push(`- Generated (UTC): ${new Date().toISOString()}`);
  lines.push(`- Gate result: **${gateResult}**`);
  lines.push(`- Summary: ${passCount} PASS, ${warnCount} WARN, ${infoCount} INFO, ${failCount} FAIL`);
  lines.push("");
  lines.push("## Automated Checks");
  lines.push("");
  lines.push("| Level | Check | Message |");
  lines.push("|---|---|---|");
  findings.forEach((item) => {
    lines.push(`| ${item.level} | ${item.check} | ${item.message.replace(/\|/g, "\\|")} |`);
  });
  lines.push("");

  const withDetail = findings.filter((item) => item.detail && item.detail.trim());
  if (withDetail.length) {
    lines.push("## Check Details");
    lines.push("");
    withDetail.forEach((item) => {
      lines.push(`### ${item.level}: ${item.check}`);
      lines.push("");
      lines.push("```text");
      lines.push(item.detail);
      lines.push("```");
      lines.push("");
    });
  }

  lines.push(buildManualChecklistMarkdown());
  lines.push("");
  return { gateResult, content: lines.join("\n") };
}

function main() {
  if (!fs.existsSync(extensionRoot)) {
    console.error(`Extension directory not found: ${extensionRoot}`);
    process.exit(2);
  }

  const manifestPath = path.join(extensionRoot, "manifest.json");
  if (!fs.existsSync(manifestPath)) {
    console.error(`manifest.json not found: ${manifestPath}`);
    process.exit(2);
  }

  const manifest = readJson(manifestPath);
  const absFiles = walkFiles(extensionRoot);
  const relFiles = absFiles.map((absolute) => toPosix(path.relative(extensionRoot, absolute)));

  if (manifest.manifest_version === 3) {
    addFinding("PASS", "Manifest version", "manifest_version is 3.");
  } else {
    addFinding("FAIL", "Manifest version", `Expected manifest_version=3, got ${manifest.manifest_version}.`);
  }

  checkManifestReferences(manifest, relFiles);
  checkIconDimensions(manifest);
  checkLocaleKeys(manifest);
  checkHelperExtensionIds();
  checkBroadPermissionPosture(manifest);
  checkRemoteUrls(relFiles);
  checkPackagingNoise(relFiles);

  fs.mkdirSync(reportDir, { recursive: true });
  const reportName = `cws_preflight_${timestampUtc()}`;
  const reportPath = path.join(reportDir, `${reportName}.md`);
  const report = renderReport(reportName);
  fs.writeFileSync(reportPath, report.content, "utf8");

  const failCount = findings.filter((f) => f.level === "FAIL").length;
  const warnCount = findings.filter((f) => f.level === "WARN").length;
  console.log(`[CWS preflight] Report: ${reportPath}`);
  console.log(
    `[CWS preflight] Result: ${report.gateResult} (${findings.filter((f) => f.level === "PASS").length} PASS, ${warnCount} WARN, ${findings.filter((f) => f.level === "INFO").length} INFO, ${failCount} FAIL)`
  );

  if (failCount > 0) {
    process.exit(1);
  }
}

main();
