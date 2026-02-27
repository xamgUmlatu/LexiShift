"use strict";

module.exports = Object.freeze({
    warningRatio: 0.9,
    defaults: Object.freeze({
        javascript: Object.freeze({
            maxLines: 500,
            maxImports: 16,
            maxDomainBreadth: 6,
            maxFunctions: 45
        }),
        python: Object.freeze({
            maxLines: 900,
            maxImports: 24,
            maxDomainBreadth: 8,
            maxFunctions: 50
        })
    }),
    targets: Object.freeze([
        Object.freeze({
            root: "apps/chrome-extension",
            language: "javascript",
            extensions: Object.freeze([".js", ".mjs", ".cjs", ".ts", ".tsx"])
        }),
        Object.freeze({
            root: "apps/betterdiscord-plugin/src",
            language: "javascript",
            extensions: Object.freeze([".js", ".mjs", ".cjs", ".ts", ".tsx"])
        }),
        Object.freeze({
            root: "scripts/dev",
            language: "javascript",
            extensions: Object.freeze([".js", ".mjs", ".cjs"])
        }),
        Object.freeze({
            root: "apps/gui/src",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "core/lexishift_core",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "scripts/testing",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "scripts/dev",
            language: "python",
            extensions: Object.freeze([".py"])
        }),
        Object.freeze({
            root: "scripts/helper",
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
        "node_modules",
        "dist",
        "build"
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
