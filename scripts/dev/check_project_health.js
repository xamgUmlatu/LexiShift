"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const rules = require("./project_health_rules");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_WARNING_LIMIT = 15;

function toPosix(filePath) {
    return String(filePath).replace(/\\/g, "/");
}

function nowIsoUtc() {
    return new Date().toISOString();
}

function resolveFromCwd(rawPath) {
    if (!rawPath) return "";
    return path.resolve(process.cwd(), String(rawPath));
}

function ensureParentDir(filePath) {
    const dir = path.dirname(filePath);
    fs.mkdirSync(dir, { recursive: true });
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

function metricOverages(metrics, limits) {
    return {
        lines: Math.max(0, Number(metrics.lines) - Number(limits.maxLines)),
        imports: Math.max(0, Number(metrics.imports) - Number(limits.maxImports)),
        domainBreadth: Math.max(0, Number(metrics.domainBreadth) - Number(limits.maxDomainBreadth)),
        functions: Math.max(0, Number(metrics.functions) - Number(limits.maxFunctions))
    };
}

function violationMetricsFromOverages(overages) {
    return Object.keys(overages).filter((key) => Number(overages[key]) > 0);
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

function parseArgs(argv) {
    const options = {
        advisory: false,
        changedOnly: false,
        staged: false,
        baseRef: "",
        jsonOutput: "",
        baselineJson: "",
        writeBaseline: "",
        failOnNew: false,
        failOnRegressions: false,
        enforceAll: false,
        warningLimit: DEFAULT_WARNING_LIMIT
    };

    const args = argv.slice(2);
    for (let index = 0; index < args.length; index += 1) {
        const current = args[index];
        switch (current) {
        case "--advisory":
            options.advisory = true;
            break;
        case "--changed-only":
            options.changedOnly = true;
            break;
        case "--staged":
            options.staged = true;
            options.changedOnly = true;
            break;
        case "--base-ref":
            if (index + 1 >= args.length) throw new Error("Missing value for --base-ref");
            options.baseRef = String(args[index + 1] || "").trim();
            index += 1;
            break;
        case "--json-output":
            if (index + 1 >= args.length) throw new Error("Missing value for --json-output");
            options.jsonOutput = resolveFromCwd(args[index + 1]);
            index += 1;
            break;
        case "--baseline-json":
            if (index + 1 >= args.length) throw new Error("Missing value for --baseline-json");
            options.baselineJson = resolveFromCwd(args[index + 1]);
            index += 1;
            break;
        case "--write-baseline":
            if (index + 1 >= args.length) throw new Error("Missing value for --write-baseline");
            options.writeBaseline = resolveFromCwd(args[index + 1]);
            index += 1;
            break;
        case "--fail-on-new":
            options.failOnNew = true;
            break;
        case "--fail-on-regressions":
            options.failOnRegressions = true;
            break;
        case "--enforce-all":
            options.enforceAll = true;
            break;
        case "--warning-limit": {
            if (index + 1 >= args.length) throw new Error("Missing value for --warning-limit");
            const parsed = Number(args[index + 1]);
            if (!Number.isFinite(parsed) || parsed < 0) {
                throw new Error("Invalid value for --warning-limit");
            }
            options.warningLimit = Math.floor(parsed);
            index += 1;
            break;
        }
        default:
            throw new Error(`Unknown argument: ${current}`);
        }
    }

    return options;
}

function changedFilesFromGit(options) {
    const args = options.staged
        ? ["diff", "--name-only", "--cached", "--diff-filter=ACMR"]
        : options.baseRef
            ? ["diff", "--name-only", "--diff-filter=ACMR", `${options.baseRef}...HEAD`]
            : ["diff", "--name-only", "--diff-filter=ACMR"];

    const output = execFileSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" });
    return new Set(
        String(output || "")
            .split(/\r?\n/)
            .map((line) => toPosix(line.trim()))
            .filter(Boolean)
    );
}

function readJsonFile(filePath) {
    const raw = fs.readFileSync(filePath, "utf8");
    return JSON.parse(raw);
}

function loadBaseline(baselinePath) {
    if (!baselinePath) return null;
    if (!fs.existsSync(baselinePath)) {
        throw new Error(`Baseline file not found: ${baselinePath}`);
    }
    const parsed = readJsonFile(baselinePath);
    const files = parsed && typeof parsed === "object" && parsed.files && typeof parsed.files === "object"
        ? parsed.files
        : {};
    return {
        path: baselinePath,
        parsed,
        files
    };
}

function serializeRecord(record) {
    return {
        file: record.metrics.file,
        language: record.metrics.language,
        metrics: {
            lines: record.metrics.lines,
            imports: record.metrics.imports,
            domainBreadth: record.metrics.domainBreadth,
            functions: record.metrics.functions
        },
        limits: {
            maxLines: record.limits.maxLines,
            maxImports: record.limits.maxImports,
            maxDomainBreadth: record.limits.maxDomainBreadth,
            maxFunctions: record.limits.maxFunctions
        },
        overages: record.overages,
        violation_metrics: record.violationMetrics,
        warning_metrics: record.warningMetrics
    };
}

function compareWithBaseline(records, baselineFiles) {
    const newViolations = [];
    const regressions = [];
    const legacyViolations = [];

    for (const record of records) {
        if (record.violationMetrics.length === 0) continue;
        const baselineEntry = baselineFiles[record.metrics.file];
        if (!baselineEntry || !Array.isArray(baselineEntry.violation_metrics)) {
            newViolations.push({
                file: record.metrics.file,
                reason: "new_file_violation",
                violation_metrics: record.violationMetrics,
                overages: record.overages
            });
            continue;
        }

        const baseViolationSet = new Set(baselineEntry.violation_metrics.map((entry) => String(entry)));
        const baseOverages = baselineEntry.overages && typeof baselineEntry.overages === "object"
            ? baselineEntry.overages
            : {};

        let hasNewMetric = false;
        let hasRegression = false;
        const regressedMetrics = [];

        for (const metric of record.violationMetrics) {
            if (!baseViolationSet.has(metric)) {
                hasNewMetric = true;
                continue;
            }
            const baselineOverage = Number(baseOverages[metric] || 0);
            const currentOverage = Number(record.overages[metric] || 0);
            if (currentOverage > baselineOverage) {
                hasRegression = true;
                regressedMetrics.push({
                    metric,
                    baseline_overage: baselineOverage,
                    current_overage: currentOverage
                });
            }
        }

        if (hasNewMetric) {
            newViolations.push({
                file: record.metrics.file,
                reason: "new_metric_violation",
                violation_metrics: record.violationMetrics,
                overages: record.overages
            });
            continue;
        }

        if (hasRegression) {
            regressions.push({
                file: record.metrics.file,
                regressed_metrics: regressedMetrics,
                violation_metrics: record.violationMetrics,
                overages: record.overages
            });
            continue;
        }

        legacyViolations.push({
            file: record.metrics.file,
            violation_metrics: record.violationMetrics,
            overages: record.overages
        });
    }

    return {
        newViolations,
        regressions,
        legacyViolations
    };
}

function buildRecords(metricsList) {
    const records = [];
    for (const metrics of metricsList) {
        const limits = resolveLimits(metrics.file, metrics.language);
        const overages = metricOverages(metrics, limits);
        const violationMetrics = violationMetricsFromOverages(overages);
        const warningMetrics = violationMetrics.length > 0 ? [] : computeWarnings(metrics, limits);
        records.push({ metrics, limits, overages, violationMetrics, warningMetrics });
    }
    return records;
}

function uniqueByFile(metricsList) {
    const byFile = new Map();
    for (const entry of metricsList) {
        if (!byFile.has(entry.file)) {
            byFile.set(entry.file, entry);
        }
    }
    return Array.from(byFile.values());
}

function scanAllMetrics() {
    const metricsList = [];
    for (const target of rules.targets || []) {
        const rootPath = path.join(REPO_ROOT, target.root);
        if (!fs.existsSync(rootPath)) continue;
        const files = walkFiles(rootPath, target.extensions, rules.ignoreDirectories);
        for (const file of files) {
            metricsList.push(computeMetrics(file, target.language, rules.localDomains));
        }
    }
    return uniqueByFile(metricsList);
}

function writeJson(filePath, payload) {
    ensureParentDir(filePath);
    fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function buildBaselinePayload(records, options, summary) {
    const files = {};
    for (const record of records) {
        files[record.metrics.file] = serializeRecord(record);
    }
    return {
        version: 1,
        generated_at_utc: nowIsoUtc(),
        source_script: "scripts/dev/check_project_health.js",
        rules_path: "scripts/dev/project_health_rules.js",
        options: {
            advisory: Boolean(options.advisory),
            changed_only: Boolean(options.changedOnly),
            staged: Boolean(options.staged),
            base_ref: options.baseRef || ""
        },
        summary,
        files
    };
}

function printViolations(violations, advisoryMode) {
    if (violations.length === 0) return;
    const label = advisoryMode
        ? "[check-project-health] Advisory violations (non-blocking):"
        : "[check-project-health] Health gate violations:";
    console.error(label);
    violations
        .map((entry) => formatMetrics(entry.metrics, entry.limits))
        .sort()
        .forEach((entry) => console.error(`  - ${entry}`));
}

function printLegacyBaselineViolations(legacyViolations, recordsByFile) {
    if (!legacyViolations || legacyViolations.length === 0) return;
    console.log("[check-project-health] Legacy baseline violations (non-blocking):");
    legacyViolations
        .slice()
        .sort((a, b) => String(a.file).localeCompare(String(b.file)))
        .forEach((entry) => {
            const record = recordsByFile.get(String(entry.file));
            if (!record) {
                console.log(`  - ${entry.file}`);
                return;
            }
            console.log(`  - ${formatMetrics(record.metrics, record.limits)}`);
        });
}

function printWarnings(warnings, warningLimit) {
    if (warningLimit <= 0) return;
    const topWarnings = warnings
        .sort((left, right) => left.metrics.file.localeCompare(right.metrics.file))
        .slice(0, warningLimit);
    if (topWarnings.length === 0) return;
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

function printBaselineDelta(delta, options) {
    if (!delta) return;
    console.log(
        `[check-project-health] Baseline delta: `
        + `legacy=${delta.legacyViolations.length} `
        + `new=${delta.newViolations.length} `
        + `regressions=${delta.regressions.length}`
    );

    if (delta.newViolations.length > 0) {
        console.error("[check-project-health] New violations vs baseline:");
        delta.newViolations
            .slice()
            .sort((a, b) => a.file.localeCompare(b.file))
            .forEach((entry) => {
                const metrics = entry.violation_metrics.join(",");
                console.error(`  - ${entry.file} (${entry.reason}; metrics=${metrics})`);
            });
    }

    if (delta.regressions.length > 0) {
        console.error("[check-project-health] Regression violations vs baseline:");
        delta.regressions
            .slice()
            .sort((a, b) => a.file.localeCompare(b.file))
            .forEach((entry) => {
                const metrics = entry.regressed_metrics
                    .map((metric) => `${metric.metric}:${metric.baseline_overage}->${metric.current_overage}`)
                    .join(", ");
                console.error(`  - ${entry.file} (${metrics})`);
            });
    }

    if (options.enforceAll && delta.legacyViolations.length > 0) {
        console.error("[check-project-health] Legacy baseline violations are enforced (--enforce-all).");
    }
}

function main() {
    const options = parseArgs(process.argv);

    const staleOverrides = checkOverrideReferences();
    if (staleOverrides.length > 0) {
        console.error("[check-project-health] Found stale override entries:");
        staleOverrides.sort().forEach((entry) => console.error(`  - ${entry}`));
        process.exit(1);
    }

    let metrics = scanAllMetrics();
    if (metrics.length === 0) {
        throw new Error("No files matched configured targets.");
    }

    let changedFiles = null;
    if (options.changedOnly) {
        changedFiles = changedFilesFromGit(options);
        metrics = metrics.filter((entry) => changedFiles.has(entry.file));
        if (metrics.length === 0) {
            const payload = {
                generated_at_utc: nowIsoUtc(),
                summary: {
                    files_checked: 0,
                    violations: 0,
                    warnings: 0,
                    changed_only: true,
                    changed_file_count: changedFiles.size
                }
            };
            console.log("[check-project-health] PASS (no matched changed files)");
            if (options.jsonOutput) writeJson(options.jsonOutput, payload);
            if (options.writeBaseline) writeJson(options.writeBaseline, buildBaselinePayload([], options, payload.summary));
            return;
        }
    }

    const records = buildRecords(metrics);
    const violations = records.filter((entry) => entry.violationMetrics.length > 0);
    const warnings = records.filter((entry) => entry.warningMetrics.length > 0);
    const recordsByFile = new Map(records.map((entry) => [entry.metrics.file, entry]));

    const baseline = options.baselineJson ? loadBaseline(options.baselineJson) : null;
    const delta = baseline ? compareWithBaseline(records, baseline.files) : null;

    let shouldFail = false;
    if (!baseline) {
        shouldFail = violations.length > 0 && !options.advisory;
    } else {
        const failOnNew = options.failOnNew && delta && delta.newViolations.length > 0;
        const failOnRegressions = options.failOnRegressions && delta && delta.regressions.length > 0;
        const failOnAll = options.enforceAll && violations.length > 0 && !options.advisory;
        shouldFail = Boolean(failOnNew || failOnRegressions || failOnAll);
    }

    if (!baseline || options.enforceAll || options.advisory) {
        printViolations(violations, options.advisory);
    } else if (delta) {
        printLegacyBaselineViolations(delta.legacyViolations, recordsByFile);
    }

    const passLabel = shouldFail
        ? "FAIL"
        : violations.length > 0 && options.advisory
            ? "PASS (advisory mode)"
            : baseline
                ? "PASS (baseline-gated)"
                : "PASS";

    console.log(`[check-project-health] ${passLabel} (${records.length} files checked)`);

    if (options.changedOnly && changedFiles) {
        console.log(`[check-project-health] Scope: changed-only (${changedFiles.size} changed files discovered)`);
    }

    printWarnings(warnings, options.warningLimit);
    printBaselineDelta(delta, options);

    const summary = {
        files_checked: records.length,
        violations: violations.length,
        warnings: warnings.length,
        changed_only: Boolean(options.changedOnly),
        changed_file_count: changedFiles ? changedFiles.size : null,
        baseline_path: baseline ? baseline.path : "",
        baseline_legacy_violations: delta ? delta.legacyViolations.length : null,
        baseline_new_violations: delta ? delta.newViolations.length : null,
        baseline_regressions: delta ? delta.regressions.length : null,
        advisory: Boolean(options.advisory)
    };

    const payload = {
        generated_at_utc: nowIsoUtc(),
        repo_root: REPO_ROOT,
        options: {
            advisory: Boolean(options.advisory),
            changed_only: Boolean(options.changedOnly),
            staged: Boolean(options.staged),
            base_ref: options.baseRef || "",
            baseline_json: options.baselineJson || "",
            fail_on_new: Boolean(options.failOnNew),
            fail_on_regressions: Boolean(options.failOnRegressions),
            enforce_all: Boolean(options.enforceAll)
        },
        summary,
        violations: violations.map(serializeRecord),
        warnings: warnings.map(serializeRecord),
        baseline_delta: delta
            ? {
                new_violations: delta.newViolations,
                regressions: delta.regressions,
                legacy_violations: delta.legacyViolations
            }
            : null
    };

    if (options.jsonOutput) {
        writeJson(options.jsonOutput, payload);
    }

    if (options.writeBaseline) {
        writeJson(options.writeBaseline, buildBaselinePayload(records, options, summary));
    }

    if (shouldFail) {
        process.exit(1);
    }
}

try {
    main();
} catch (error) {
    console.error("[check-project-health] Failed:", error && error.stack ? error.stack : error);
    process.exit(1);
}
