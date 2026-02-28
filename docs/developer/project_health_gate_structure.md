# Project Health Gate Structure

Purpose:

1. Provide a reusable structure for enforcing codebase maintainability.
2. Catch file bloat and coupling growth before it becomes architectural debt.
3. Keep thresholds explicit, reviewable, and easy to tune.

This implementation starts simple and now supports baseline/delta gating so it can scale from advisory mode to strict CI enforcement without blocking unrelated work.

## Components

1. Rules file:
   - `scripts/dev/project_health_rules.js`
2. Checker script:
   - `scripts/dev/check_project_health.js`
3. Optional package script entry:
   - `scripts/package.json` -> `health:project`
4. Optional baseline artifact:
   - `docs/test_outputs/project_health/project_health_baseline.json`
5. Remediation workstream:
   - `project_health_remediation_workstream.md`
6. CI workflow gate:
   - `.github/workflows/ci.yml` (`project-health-changed`)

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
7. Optional scope reduction:
   - changed-files-only scan (`--changed-only`, `--base-ref`, `--staged`)
8. Optional baseline/delta comparison:
   - classify violations into `legacy`, `new`, `regressions`
   - fail on only new/regression debt when configured

## Output Contract

On failure:

1. Print all violating files with current vs threshold values.
2. Exit non-zero for CI/local gating.

On pass:

1. Print checked file count.
2. Print top near-limit files for proactive refactoring.

Optional machine-readable output:

1. Write JSON report (`--json-output`).
2. Write/update baseline snapshot (`--write-baseline`).

## Suggested Adoption Pattern

1. Start with advisory global scan and capture baseline.
2. Add explicit overrides only when necessary.
3. Keep overrides small and reviewed.
4. Enable changed-file baseline gating in CI:
   - fail on `--fail-on-new` and `--fail-on-regressions`
5. Keep global strict mode (`--enforce-all`) disabled until legacy debt is near zero.
6. Ratchet limits/overrides as remediation proceeds.

## CI Integration (Current)

1. CI enforcement is active for pull requests via `.github/workflows/ci.yml` job `project-health-changed`.
2. Mode is changed-files baseline gating (`--changed-only`) against `docs/test_outputs/project_health/project_health_baseline.json`.
3. Failures are limited to new/regressed debt (`--fail-on-new`, `--fail-on-regressions`).
4. Base ref is derived from PR target branch (`origin/${{ github.base_ref }}`).
5. Global strict mode remains disabled (`--enforce-all` is not used in CI).

## Command

From repository root:

```bash
node scripts/dev/check_project_health.js
```

Advisory (non-blocking introduction mode):

```bash
node scripts/dev/check_project_health.js --advisory

Write baseline snapshot:

```bash
node scripts/dev/check_project_health.js \
  --advisory \
  --write-baseline docs/test_outputs/project_health/project_health_baseline.json
```

Changed-file strict gating against baseline:

```bash
node scripts/dev/check_project_health.js \
  --changed-only \
  --base-ref origin/main \
  --baseline-json docs/test_outputs/project_health/project_health_baseline.json \
  --fail-on-new \
  --fail-on-regressions
```

JSON report output:

```bash
node scripts/dev/check_project_health.js \
  --advisory \
  --json-output docs/test_outputs/project_health/project_health_latest.json
```
```

From `scripts/` package scripts:

```bash
npm run health:project
```

From `scripts/` package scripts:

```bash
npm run health:project:report
npm run health:project:baseline
npm run health:project:changed
```

## Notes

1. This gate is not a replacement for tests/linting.
2. It is an architectural pressure valve for long-term maintainability.
3. Thresholds should evolve with the codebase, but changes should be explicit and documented.
4. Baseline artifacts are policy snapshots; refresh only with explicit rationale.
