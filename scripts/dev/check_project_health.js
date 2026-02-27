"use strict";

const fs = require("fs");
const path = require("path");
const rules = require("./project_health_rules");

const REPO_ROOT = path.resolve(__dirname, "..", "..");

function toPosix(filePath) {
    return String(filePath).replace(/\\/g, "/");
}

function isDirectory(entry) {
    return Boolean(entry && typeof entry.isDirectory === "function" && entry.isDirectory());
}

function walkFiles(rootDir, extensions, ignoreDirectories) {
    const files = [];
    const stack = [rootDir];
    const extensionSet = new Set((extensions || []).map((entry) => String(entry).toLowerCase()));
    const ignoredNames = new Set((ignoreDirectories || []).map((entry) => String(entry)));

    while (stack.length > 0) {
        const current = stack.pop();
        const entries = fs.readdirSync(current, { withFileTypes: true });
        for (const entry of entries) {
            const absolute = path.join(current, entry.name);
            if (isDirectory(entry)) {
                if (ignoredNames.has(entry.name)) continue;
                stack.push(absolute);
                continue;
            }
            if (!entry.isFile()) continue;
            const extension = path.extname(entry.name).toLowerCase();
            if (extensionSet.has(extension)) {
                files.push(absolute);
            }
        }
    }
    return files;
}

function uniqueStrings(values) {
    const result = new Set();
    for (const value of values || []) {
        if (typeof value !== "string") continue;
        const normalized = value.trim();
        if (!normalized) continue;
        result.add(normalized);
    }
    return Array.from(result);
}

function parseJavascriptImports(content) {
    const imports = [];
    for (const match of content.matchAll(/require\s*\(\s*["']([^"']+)["']\s*\)/g)) {
        if (match && match[1]) imports.push(match[1]);
    }
    for (const match of content.matchAll(/\bimport\s+(?:[^"']+?\s+from\s+)?["']([^"']+)["']/g)) {
        if (match && match[1]) imports.push(match[1]);
    }
    for (const match of content.matchAll(/\bexport\s+[^"']+?\s+from\s+["']([^"']+)["']/g)) {
        if (match && match[1]) imports.push(match[1]);
    }
    return uniqueStrings(imports);
}

function parsePythonImports(content) {
    const imports = [];
    for (const match of content.matchAll(/^\s*import\s+([a-zA-Z0-9_.,\s]+)\s*$/gm)) {
        if (!match || !match[1]) continue;
        const modules = match[1]
            .split(",")
            .map((entry) => entry.trim().split(/\s+as\s+/i)[0].trim())
            .filter(Boolean);
        imports.push(...modules);
    }
    for (const match of content.matchAll(/^\s*from\s+([a-zA-Z0-9_.]+|\.+)\s+import\s+/gm)) {
        if (match && match[1]) imports.push(match[1]);
    }
    return uniqueStrings(imports);
}

function countJavascriptFunctions(content) {
    return (content.match(/\bfunction\b/g) || []).length;
}

function countPythonFunctions(content) {
    return (content.match(/^\s*(?:async\s+def|def)\s+[A-Za-z_][A-Za-z0-9_]*\s*\(/gm) || []).length;
}

function resolveJavascriptDomainBreadth(relativePath, imports) {
    const absoluteFilePath = path.join(REPO_ROOT, relativePath);
    const domains = new Set();

    for (const entry of imports) {
        if (entry.startsWith(".")) {
            const absoluteTarget = path.resolve(path.dirname(absoluteFilePath), entry);
            const relativeTarget = toPosix(path.relative(REPO_ROOT, absoluteTarget));
            if (relativeTarget.startsWith("..")) continue;
            const topLevel = relativeTarget.split("/")[0];
            if (topLevel) domains.add(topLevel);
            continue;
        }
        if (/^(apps|core|data|scripts)\//.test(entry)) {
            domains.add(entry.split("/")[0]);
        }
    }
    return domains.size;
}

function resolvePythonDomainBreadth(relativePath, imports, localDomains) {
    const domains = new Set();
    const fileTopLevel = toPosix(relativePath).split("/")[0];
    const knownDomains = new Set((localDomains || []).map((entry) => String(entry)));

    for (const entry of imports) {
        if (!entry) continue;
        if (entry.startsWith(".")) {
            if (fileTopLevel) domains.add(fileTopLevel);
            continue;
        }
        const topLevel = entry.split(".")[0];
        if (knownDomains.has(topLevel)) {
            domains.add(topLevel);
        }
    }
    return domains.size;
}

function computeMetrics(absolutePath, language, localDomains) {
    const relativePath = toPosix(path.relative(REPO_ROOT, absolutePath));
    const content = fs.readFileSync(absolutePath, "utf8");
    const lines = content.split(/\r?\n/).length;

    if (language === "python") {
        const imports = parsePythonImports(content);
        return {
            file: relativePath,
            language,
            lines,
            imports: imports.length,
            domainBreadth: resolvePythonDomainBreadth(relativePath, imports, localDomains),
            functions: countPythonFunctions(content)
        };
    }

    const imports = parseJavascriptImports(content);
    return {
        file: relativePath,
        language: "javascript",
        lines,
        imports: imports.length,
        domainBreadth: resolveJavascriptDomainBreadth(relativePath, imports),
        functions: countJavascriptFunctions(content)
    };
}

function resolveLimits(filePath, language) {
    const defaults = rules.defaults[language];
    if (!defaults) throw new Error(`Missing defaults for language: ${language}`);

    const override = rules.overrides[filePath] || {};
    return {
        maxLines: Number(override.maxLines || defaults.maxLines),
        maxImports: Number(override.maxImports || defaults.maxImports),
        maxDomainBreadth: Number(override.maxDomainBreadth || defaults.maxDomainBreadth),
        maxFunctions: Number(override.maxFunctions || defaults.maxFunctions)
    };
}

function computeWarnings(metrics, limits) {
    const warningRatio = typeof rules.warningRatio === "number" ? rules.warningRatio : 0.9;
    const warnings = [];

    if (metrics.lines >= Math.floor(limits.maxLines * warningRatio)) warnings.push("lines");
    if (metrics.imports >= Math.floor(limits.maxImports * warningRatio)) warnings.push("imports");
    if (metrics.domainBreadth >= Math.floor(limits.maxDomainBreadth * warningRatio)) warnings.push("domainBreadth");
    if (metrics.functions >= Math.floor(limits.maxFunctions * warningRatio)) warnings.push("functions");

    return warnings;
}

function checkOverrideReferences() {
    const stale = [];
    for (const filePath of Object.keys(rules.overrides || {})) {
        const absolutePath = path.join(REPO_ROOT, filePath);
        if (!fs.existsSync(absolutePath)) stale.push(filePath);
    }
    return stale;
}

function formatMetrics(metrics, limits) {
    return [
        metrics.file,
        `lang=${metrics.language}`,
        `lines=${metrics.lines}/${limits.maxLines}`,
        `imports=${metrics.imports}/${limits.maxImports}`,
        `domainBreadth=${metrics.domainBreadth}/${limits.maxDomainBreadth}`,
        `functions=${metrics.functions}/${limits.maxFunctions}`
    ].join(" | ");
}

function main() {
    const advisoryMode = process.argv.includes("--advisory");
    const staleOverrides = checkOverrideReferences();
    if (staleOverrides.length > 0) {
        console.error("[check-project-health] Found stale override entries:");
        staleOverrides.sort().forEach((entry) => console.error(`  - ${entry}`));
        process.exit(1);
    }

    const metricsList = [];
    for (const target of rules.targets || []) {
        const rootPath = path.join(REPO_ROOT, target.root);
        if (!fs.existsSync(rootPath)) continue;
        const files = walkFiles(rootPath, target.extensions, rules.ignoreDirectories);
        for (const file of files) {
            metricsList.push(computeMetrics(file, target.language, rules.localDomains));
        }
    }

    const byFile = new Map();
    for (const entry of metricsList) {
        if (!byFile.has(entry.file)) {
            byFile.set(entry.file, entry);
        }
    }
    const uniqueMetrics = Array.from(byFile.values());

    if (uniqueMetrics.length === 0) {
        console.error("[check-project-health] No files matched configured targets.");
        process.exit(1);
    }

    const violations = [];
    const warnings = [];

    for (const metrics of uniqueMetrics) {
        const limits = resolveLimits(metrics.file, metrics.language);
        const hasViolation = metrics.lines > limits.maxLines
            || metrics.imports > limits.maxImports
            || metrics.domainBreadth > limits.maxDomainBreadth
            || metrics.functions > limits.maxFunctions;

        if (hasViolation) {
            violations.push(formatMetrics(metrics, limits));
            continue;
        }

        const nearLimit = computeWarnings(metrics, limits);
        if (nearLimit.length > 0) {
            warnings.push({ metrics, limits, warningMetrics: nearLimit });
        }
    }

    if (violations.length > 0) {
        const label = advisoryMode
            ? "[check-project-health] Advisory violations (non-blocking):"
            : "[check-project-health] Health gate violations:";
        console.error(label);
        violations.sort().forEach((entry) => console.error(`  - ${entry}`));
        if (!advisoryMode) {
            process.exit(1);
        }
    }

    const passLabel = violations.length > 0 && advisoryMode
        ? "PASS (advisory mode)"
        : "PASS";
    console.log(`[check-project-health] ${passLabel} (${uniqueMetrics.length} files checked)`);
    const topWarnings = warnings
        .sort((left, right) => left.metrics.file.localeCompare(right.metrics.file))
        .slice(0, 15);
    if (topWarnings.length > 0) {
        console.log("[check-project-health] Near-limit files:");
        topWarnings.forEach((entry) => {
            const label = entry.warningMetrics.join(",");
            console.log(
                `  - ${entry.metrics.file} [${label}] `
                + `(L ${entry.metrics.lines}/${entry.limits.maxLines}, `
                + `I ${entry.metrics.imports}/${entry.limits.maxImports}, `
                + `D ${entry.metrics.domainBreadth}/${entry.limits.maxDomainBreadth}, `
                + `F ${entry.metrics.functions}/${entry.limits.maxFunctions})`
            );
        });
    }
}

try {
    main();
} catch (error) {
    console.error("[check-project-health] Failed:", error && error.stack ? error.stack : error);
    process.exit(1);
}
