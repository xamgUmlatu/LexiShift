# Project Health Gate Structure

Purpose:

1. Provide a reusable structure for enforcing codebase maintainability.
2. Catch file bloat and coupling growth before it becomes architectural debt.
3. Keep thresholds explicit, reviewable, and easy to tune.

This implementation is intentionally simple so it can be explained and adopted quickly.

## Components

1. Rules file:
   - `scripts/dev/project_health_rules.js`
2. Checker script:
   - `scripts/dev/check_project_health.js`
3. Optional package script entry:
   - `scripts/package.json` -> `health:project`

## Rule Model

Rules are separated into:

1. Defaults per language profile:
   - JavaScript/TypeScript
   - Python
2. Scan targets:
   - which directories + extensions are included
3. Ignore list:
   - cache/build/vendor directories
4. Local domain list:
   - used for internal coupling breadth checks
5. File-specific overrides:
   - explicit exceptions for known orchestrator/entrypoint files
6. Warning ratio:
   - near-limit early warning threshold (default `0.9`)

## Metrics Tracked

Per file:

1. `lines`
2. `imports`
3. `domainBreadth`
4. `functions`

Meaning:

1. `lines`: raw line count guardrail.
2. `imports`: unique module dependency count.
3. `domainBreadth`: how many internal top-level domains the file couples to.
4. `functions`: complexity proxy (module surface density).

## Checker Pipeline

Checker flow:

1. Load rules.
2. Validate override paths (fail if stale).
3. Walk configured roots by extension.
4. Compute metrics per file (language-aware parser).
5. Apply limits (default + override).
6. Emit:
   - hard violations (exit `1`)
   - near-limit warnings (report only)
   - pass summary

## Output Contract

On failure:

1. Print all violating files with current vs threshold values.
2. Exit non-zero for CI/local gating.

On pass:

1. Print checked file count.
2. Print top near-limit files for proactive refactoring.

## Suggested Adoption Pattern

1. Start with conservative defaults.
2. Add explicit overrides only when necessary.
3. Keep overrides small and reviewed.
4. Run gate in local dev loops before PR.
5. Add gate to CI once noise level is acceptable.

## Command

From repository root:

```bash
node scripts/dev/check_project_health.js
```

Advisory (non-blocking introduction mode):

```bash
node scripts/dev/check_project_health.js --advisory
```

From `scripts/` package scripts:

```bash
npm run health:project
```

## Notes

1. This gate is not a replacement for tests/linting.
2. It is an architectural pressure valve for long-term maintainability.
3. Thresholds should evolve with the codebase, but changes should be explicit and documented.
