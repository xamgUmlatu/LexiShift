"use strict";

module.exports = Object.freeze({
    warningRatio: 0.9,
    defaults: Object.freeze({
        javascript: Object.freeze({
            maxLines: 320,
            maxImports: 12,
            maxDomainBreadth: 5,
            maxFunctions: 24
        }),
        python: Object.freeze({
            maxLines: 380,
            maxImports: 20,
            maxDomainBreadth: 8,
            maxFunctions: 30
        })
    }),
    targets: Object.freeze([
        Object.freeze({
            root: "apps",
            language: "javascript",
            extensions: Object.freeze([".js", ".mjs", ".cjs", ".ts", ".tsx"])
        }),
        Object.freeze({
            root: "scripts",
            language: "javascript",
            extensions: Object.freeze([".js", ".mjs", ".cjs"])
        }),
        Object.freeze({
            root: "apps",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "core",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "scripts",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "data",
            language: "python",
            extensions: Object.freeze([".py"])
        })
    ]),
    localDomains: Object.freeze([
        "apps",
        "core",
        "data",
        "scripts",
        "lexishift_core"
    ]),
    ignoreDirectories: Object.freeze([
        ".git",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules"
    ]),
    overrides: Object.freeze({
        "scripts/dev/cws_preflight.js": Object.freeze({
            maxLines: 500,
            maxFunctions: 36
        }),
        "scripts/dev/licensing_header_audit.py": Object.freeze({
            maxLines: 520
        }),
        "scripts/dev/licensing_source_header_fetch.py": Object.freeze({
            maxLines: 520
        })
    })
});
