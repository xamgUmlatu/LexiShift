# Project Health Remediation Workstream

Status: active  
Owner: engineering  
Last updated: 2026-02-27

## Objective

Treat project-health remediation as a first-class architecture project:

1. Eliminate existing maintainability violations in a controlled sequence.
2. Prevent new debt from entering while cleanup is in progress.
3. Move from advisory checks to strict CI enforcement without freezing delivery.

## Baseline Snapshot (2026-02-27, current)

Source command:

```bash
cd scripts
npm run health:project
```

Current violation profile:

1. Total violations: `11` files (out of `258` scanned)
2. By area:
   - `apps/chrome-extension`: `2`
   - `apps/gui/src`: `2`
   - `core/lexishift_core`: `3`
   - `scripts/*`: `4`
3. By metric:
   - `lines`: `9`
   - `functions`: `3`
   - `imports`: `3`
   - `domainBreadth`: `0`

Top hotspots by line overage:

1. `apps/gui/src/main.py` (`2455/900`, `122/50`, `41/24`)
2. `apps/chrome-extension/options/controllers/rules/share_center_controller.js` (`1550/500`, `45/45`)
3. `apps/chrome-extension/options/core/rules_manager.js` (`1505/500`)
4. `apps/gui/src/settings_language_packs.py` (`1617/900`, `86/50`)
5. `core/lexishift_core/frequency/de/build.py` (`1074/900`)

## Progress Log

1. 2026-02-27: extracted feedback sync primitives from
   `apps/chrome-extension/shared/helper/helper_feedback_sync.js`
   into `apps/chrome-extension/shared/helper/helper_feedback_sync_primitives.js`.
2. 2026-02-27: extracted replacement selection pipeline from
   `apps/chrome-extension/content/processing/replacements.js`
   into `apps/chrome-extension/content/processing/replacement_selection.js`.
3. 2026-02-27: extracted background controller setup/factory resolution from
   `apps/chrome-extension/options/controllers/profile/background_controller.js`
   into `apps/chrome-extension/options/controllers/profile/background/controller_context.js`.
4. 2026-02-27: normalized helper tray imports in
   `apps/gui/src/helper_tray.py` to remove a checker import-overage violation.
5. 2026-02-27: extracted popup locale/theme/runtime-order helpers from
   `apps/chrome-extension/content/ui/ui.js` into
   `apps/chrome-extension/content/ui/popup_locale_helpers.js` and
   `apps/chrome-extension/content/ui/popup_helpers.js`.
6. 2026-02-27: split target language modal flow into dedicated modules:
   - `apps/chrome-extension/options/controllers/ui/target_language_modal/utils.js`
   - `apps/chrome-extension/options/controllers/ui/target_language_modal/renderer.js`
   - `apps/chrome-extension/options/controllers/ui/target_language_modal/interactions.js`
   - `apps/chrome-extension/options/controllers/ui/target_language_modal/focus.js`
   and reduced `apps/chrome-extension/options/controllers/ui/target_language_modal_controller.js`
   to orchestration.
7. Result: removed six full advisory violations (`helper_feedback_sync.js`,
   `replacements.js`, `background_controller.js`, `helper_tray.py`, `ui.js`,
   `target_language_modal_controller.js`) without changing runtime API shape.
8. 2026-02-27: extracted Share Center helpers into:
   - `apps/chrome-extension/options/controllers/rules/share_center/utils.js`
   - `apps/chrome-extension/options/controllers/rules/share_center/status.js`
   - `apps/chrome-extension/options/controllers/rules/share_center/modal.js`
   - `apps/chrome-extension/options/controllers/rules/share_center/selection.js`
   and rewired `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
   to consume shared modules (now `1550` lines / `45` functions from `1836` / `74`).

## Leaf-First Remediation Queue (Current)

Hotspot-first globally, then leaf-first per hotspot:

1. `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
   - Extract: payload normalization, validator policies, API client adapters, modal state reducers.
2. `apps/chrome-extension/options/core/rules_manager.js`
   - Extract: pure diff/merge ops, sorting/grouping helpers, persistence adapter wrapper.
3. `apps/gui/src/main.py`
   - Extract: non-Qt app services, command wiring, data loading orchestration.
4. `apps/gui/src/settings_language_packs.py`
   - Extract: download/use-case services, table mappers, validation logic.
5. `core/lexishift_core/__init__.py`
   - Extract: optional/advanced exports into lazy import boundary to reduce import fanout.
6. `core/lexishift_core/helper/engine.py`
   - Extract: optional dependencies and heavyweight integrations into dedicated modules.
7. `core/lexishift_core/frequency/de/build.py`
   - Extract: parsing pipeline stages into focused builder helpers.
8. `scripts/testing/rulegen_benchmark.py`
   - Extract: case loading, runner, metrics, renderers into separate script helpers.
9. `scripts/testing/rulegen_quality_gate.py`
   - Extract: policy evaluation core and report rendering.
10. `scripts/dev/licensing_header_audit.py`
   - Extract: scanners, license classifiers, report writer.
11. `scripts/dev/licensing_source_header_fetch.py`
   - Extract: source fetch adapters, cache/store logic, retry policy.

## Remediation Strategy

Use a two-level sequencing model:

1. Hotspot-first across the repo (highest overage/risk first).
2. Leaf-first inside each hotspot (extract pure utilities first, then side-effect modules, then keep root orchestrator thin).

Why this ordering:

1. Global leaf-first wastes cycles on low-impact files.
2. Hotspots are where delivery risk and merge pain are concentrated.
3. Leaf extraction first inside hotspots lowers blast radius and test burden.

## Work Phases

### Phase 0 - Governance + Gating Foundation

Deliverables:

1. Baseline/delta-capable checker in `scripts/dev/check_project_health.js`.
2. NPM workflows in `scripts/package.json`:
   - `health:project`
   - `health:project:report`
   - `health:project:baseline`
   - `health:project:changed`
3. Baseline artifact path:
   - `docs/test_outputs/project_health/project_health_baseline.json`

Exit criteria:

1. CI can gate changed files against baseline deltas.
2. New violations/regressions are blocked.
3. Legacy violations remain non-blocking.
4. Temporary checker override (`scripts/dev/check_project_health.js`) is explicitly tracked and not treated as hidden debt.

### Phase 1 - Chrome Extension Hotspots

Target files (initial):

1. `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
2. `apps/chrome-extension/options/core/rules_manager.js`

Extraction order per file:

1. Pure format/parse helpers.
2. Stateless policy/validation modules.
3. IO/DOM adapters.
4. Keep controller/orchestrator focused on sequencing.

Exit criteria:

1. Each target under line cap or covered by temporary override with expiry note.
2. Function count reduced to cap or documented temporary exception.

### Phase 2 - GUI Hotspots

Target files (initial):

1. `apps/gui/src/main.py`
2. `apps/gui/src/settings_language_packs.py`

Extraction order per file:

1. DTO/config parsing modules.
2. Service/use-case layers (non-Qt logic).
3. UI composition/controller shell.

Exit criteria:

1. `main.py` no longer aggregates broad service wiring and flow logic in one module.
2. Imports/function counts reduced and stable.

### Phase 3 - Core + Script Tooling Cleanup

Target files (initial):

1. `core/lexishift_core/__init__.py` (import surface trim)
2. `core/lexishift_core/helper/engine.py`
3. `core/lexishift_core/frequency/de/build.py`
4. `scripts/testing/rulegen_benchmark.py`
5. `scripts/testing/rulegen_quality_gate.py`
6. `scripts/dev/licensing_header_audit.py`
7. `scripts/dev/licensing_source_header_fetch.py`

Exit criteria:

1. Violations in core/scripts eliminated or bounded by explicit, short-lived overrides.
2. No churn in gate noise between releases.

### Phase 4 - Strict Global Enforcement

Transition:

1. Turn on global strict gating (`--enforce-all`) in CI.
2. Keep changed-only delta gate as pre-merge fast path.

Exit criteria:

1. Global strict gate passes on default branch.
2. Overrides are minimal, reviewed, and time-bounded.

## CI Policy Ladder

1. Stage A (now):
   - Advisory global report.
   - Strict changed-only baseline gate (`new` + `regressions`).
2. Stage B:
   - Tighten warning thresholds and prune overrides.
3. Stage C:
   - Global strict enforcement.

## Backlog Tracking Model

For each violating file, track:

1. Owner
2. Planned extraction modules
3. Dependency risks
4. Test plan
5. Target cap date
6. Override expiry date (if temporary override is required)

## Definition Of Done

Project health remediation is complete when:

1. Violation count is zero under global strict mode.
2. Changed-file gate remains green over multiple release cycles.
3. No stale overrides remain in `project_health_rules.js`.
4. Development velocity is unchanged (no widespread gate-induced PR blocks).

## Operational Commands

Generate advisory report JSON:

```bash
cd scripts
npm run health:project:report
```

Write/update baseline snapshot:

```bash
cd scripts
npm run health:project:baseline
```

Run changed-file strict gate:

```bash
cd scripts
npm run health:project:changed
```
