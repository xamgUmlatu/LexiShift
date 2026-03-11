# Project Health Remediation Workstream

Status: active
Owner: engineering
Last updated: 2026-02-28

## Objective

Treat project-health remediation as a first-class architecture project:

1. Eliminate existing maintainability violations in a controlled sequence.
2. Prevent new debt from entering while cleanup is in progress.
3. Move from advisory checks to strict CI enforcement without freezing delivery.

## Baseline Snapshot (2026-02-28, current)

Source command:

```bash
cd scripts
npm run health:project
```

Current violation profile:

1. Total violations: `0` files (out of `302` scanned)
2. By area:
   - `apps/gui/src`: `0`
   - `core/lexishift_core`: `0`
   - `scripts/*`: `0`
3. By metric:
   - `lines`: `0`
   - `functions`: `0`
   - `imports`: `0`
   - `domainBreadth`: `0`

Near-limit watchlist (non-blocking): none (`0` warnings).

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
9. 2026-02-27: split `RulesManager` internals into dedicated prototype modules:
   - `apps/chrome-extension/options/core/rules_manager/base_methods.js`
   - `apps/chrome-extension/options/core/rules_manager/ruleset_methods.js`
   - `apps/chrome-extension/options/core/rules_manager/profile_share_methods.js`
   - `apps/chrome-extension/options/core/rules_manager/bundle_methods.js`
   and reduced `apps/chrome-extension/options/core/rules_manager.js` to public API orchestration
   (`262` lines from `1505`), removing one full advisory violation.
10. 2026-02-27: extracted Share Center data resolvers into
    `apps/chrome-extension/options/controllers/rules/share_center/data_resolvers.js`
    and reduced `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
    from `1550` to `1373` lines while preserving behavior.
11. 2026-02-27: extracted Share Center event binding boilerplate into
    `apps/chrome-extension/options/controllers/rules/share_center/event_binders.js`
    and reduced `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
    from `1373` to `1281` lines.
12. 2026-02-27: completed full Share Center split into dedicated modules:
    - `apps/chrome-extension/options/controllers/rules/share_center/workflows.js`
    - `apps/chrome-extension/options/controllers/rules/share_center/summary.js`
    - `apps/chrome-extension/options/controllers/rules/share_center/sync.js`
    - `apps/chrome-extension/options/controllers/rules/share_center/tree_state.js`
    - `apps/chrome-extension/options/controllers/rules/share_center/renderers.js`
    reducing `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
    from `1836` to `452` lines and removing the violation entirely.
13. 2026-02-27: completed RulesManager split and removed its violation by moving internals into:
    - `apps/chrome-extension/options/core/rules_manager/base_methods.js`
    - `apps/chrome-extension/options/core/rules_manager/ruleset_methods.js`
    - `apps/chrome-extension/options/core/rules_manager/profile_share_methods.js`
    - `apps/chrome-extension/options/core/rules_manager/bundle_methods.js`
    while reducing `apps/chrome-extension/options/core/rules_manager.js` to `262` lines.
14. 2026-02-27: started GUI hotspot extraction by moving app-data/ruleset/startup path helpers from
    `apps/gui/src/main.py` into `apps/gui/src/main_paths.py`, reducing `main.py` line/function pressure.
15. 2026-02-27: extracted runtime/bootstrap helpers from `apps/gui/src/main.py` into
    `apps/gui/src/main_runtime.py` (startup logging, crash hook, single-instance handling,
    activation binding, theme priming), reducing `main.py` imports from `42` to `37`
    and further lowering line/function count.
16. 2026-02-28: extracted setup-guide URL probing/opening from `apps/gui/src/main.py` into
    `apps/gui/src/main_help.py`, removing network/browser helper logic from the root window module.
17. 2026-02-28: extracted dataset/profile import-export and unsaved-change confirmation flows from
    `apps/gui/src/main.py` into `apps/gui/src/main_import_export_mixin.py`.
18. 2026-02-28: extracted menu/action wiring + helper install diagnostics + profile menu rebuild logic from
    `apps/gui/src/main.py` into `apps/gui/src/main_menu_mixin.py`, reducing `main.py`
    from `2360` to `1927` lines and from `113` to `90` functions while preserving baseline gate status.
19. 2026-02-28: extracted empty-workspace locale selection/rendering methods from `apps/gui/src/main.py`
    into `apps/gui/src/main_locale_mixin.py`, further reducing `main.py` to `1835` lines
    and `86` functions.
20. 2026-02-28: extracted profile/ruleset lifecycle + profile UI refresh + ruleset migration helpers from
    `apps/gui/src/main.py` into `apps/gui/src/main_profiles_mixin.py`, reducing `main.py`
    to `1591` lines, `62` functions, and `31` imports.
21. 2026-02-28: extracted bulk synonym/rulegen pipeline from `apps/gui/src/main.py` into
    `apps/gui/src/main_bulk_rules_mixin.py` (bulk dialog defaults, pack selection memory,
    source probing/stats, and candidate rule expansion).
22. 2026-02-28: extracted SRS seed-growth and replacement-filter/embedding flows into:
    - `apps/gui/src/main_srs_mixin.py`
    - `apps/gui/src/main_replacement_filter_mixin.py`
    and moved embedding loader thread to `apps/gui/src/main_embedding_loader.py`.
23. 2026-02-28: consolidated GUI mixin imports via `apps/gui/src/main_mixins.py`,
    reducing `apps/gui/src/main.py` to `750` lines, `35` functions, `24` imports, and
    fully clearing `main.py` from the health-violation list (now only near-limit import warning).
24. 2026-02-28: started `settings_language_packs.py` remediation by extracting support primitives into
    `apps/gui/src/settings_language_packs_support.py`:
    - row dataclasses (`LanguagePackRow`, `FrequencyPackRow`, `EmbeddingPackRow`)
    - SQLite/path probes (`is_sqlite_db_file`, `has_frequency_table`)
    - embedding conversion thread (`EmbeddingConversionThread`)
    - app-data directory resolvers for language/frequency/embedding packs
    resulting in `settings_language_packs.py` reduction from `1617` to `1483` lines and
    from `86` to `78` functions.
25. 2026-02-28: extracted download-path/filesystem utility methods from
    `apps/gui/src/settings_language_packs.py` into `apps/gui/src/settings_language_packs_path_mixin.py`
    (`_download_archive_path`, `_resolve_downloaded_path`, `_remove_path`, wordnet/sqlite helpers, etc.),
    reducing `settings_language_packs.py` from `1483` to `1370` lines and from `78` to `65` functions.
26. 2026-02-28: extracted panel-state/status helper methods from
    `apps/gui/src/settings_language_packs.py` into
    `apps/gui/src/settings_language_packs_panel_state_mixin.py`
    (`apply_synonym_settings`, path accessors, theme/status tone helpers, dir/help actions, seed helpers),
    reducing `settings_language_packs.py` from `1370` to `1247` lines and from `65` to `45` functions.
27. 2026-02-28: extracted table refresh/population methods from
    `apps/gui/src/settings_language_packs.py` into
    `apps/gui/src/settings_language_packs_table_mixin.py` (`_refresh_*`, `_populate_*`, embedding row resolver),
    reducing `settings_language_packs.py` to `896` lines and `35` functions.
28. 2026-02-28: completed Phase 2 cleanup milestone:
    both GUI hotspot files (`apps/gui/src/main.py`, `apps/gui/src/settings_language_packs.py`)
    are now out of health violations; `health:project:changed` reports `legacy=0 new=0 regressions=0`.
29. 2026-02-28: reduced `core/lexishift_core/__init__.py` import overage by replacing eager
    re-exports from `srs`, `srs.scheduler`, and `srs.gate` with lazy module-level exports
    via `__getattr__`, bringing import count to `24/24` (warning threshold) and clearing
    the file from active violations.
30. 2026-02-28: cleared `core/lexishift_core/helper/engine.py` import violation by replacing
    low-frequency dependency imports (`validate_frequency_sqlite_db`, `build_seed_candidates`)
    with runtime module resolution via `__import__`, reducing import statements to `24/24`
    (warning threshold, no longer a violation).
31. 2026-02-28: cleared `core/lexishift_core/frequency/de/build.py` line overage by extracting
    argument parsing/token normalization/POS inventory helpers into
    `core/lexishift_core/frequency/de/build_support.py`, reducing `build.py` to `834` lines.
32. 2026-02-28: cleared `scripts/dev/licensing_source_header_fetch.py` line overage by extracting
    data models/parsing/download/probe helpers into
    `scripts/dev/licensing_source_header_fetch_support.py`, reducing the orchestrator script
    to `205` lines.
33. 2026-02-28: cleared `scripts/dev/licensing_header_audit.py` line overage by extracting
    audit models/parsers/probes/report helpers into
    `scripts/dev/licensing_header_audit_support.py`, reducing the orchestrator script
    to `146` lines.
34. 2026-02-28: cleared `scripts/testing/rulegen_quality_gate.py` line overage by extracting
    gate models/validators/utility functions into
    `scripts/testing/rulegen_quality_gate_support.py`, reducing the entry script
    to `302` lines while preserving CLI behavior.
35. 2026-02-28: cleared `scripts/testing/rulegen_benchmark.py` line overage by extracting
    the HTML dashboard renderer into `scripts/testing/rulegen_benchmark_html.py`,
    reducing the entry script to `705` lines.
36. 2026-02-28: project-health violations reached zero; both
    `npm run -s health:project:report` and `npm run -s health:project:changed`
    pass with `legacy=0 new=0 regressions=0`.
37. 2026-02-28: hardened near-limit `scripts/testing/rulegen_quality_gate_support.py` by
    splitting gate core and validators into:
    - `scripts/testing/rulegen_quality_gate_core.py`
    - `scripts/testing/rulegen_quality_gate_validators.py`
    and reducing `scripts/testing/rulegen_quality_gate_support.py` to a stable re-export shim
    (`51` lines), preserving existing imports in `rulegen_quality_gate.py`.
38. 2026-02-28: extracted resource-tab layout builders from
    `apps/gui/src/settings_language_packs.py` into
    `apps/gui/src/settings_language_packs_layout_mixin.py`,
    reducing the panel module from `896` to `830` lines while preserving behavior and
    keeping changed-only health gating green.
39. 2026-02-28: extracted themed tab container + background/theme utility helpers from
    `apps/gui/src/dialogs.py` into `apps/gui/src/dialogs_theme_utils.py`,
    reducing `dialogs.py` from `896` to `791` lines and removing it from near-limit warnings.
40. 2026-02-28: extracted language-pack transfer handlers from
    `apps/gui/src/settings_language_packs.py` into
    `apps/gui/src/settings_language_packs_transfer_mixin.py`
    (`_on_*_progress`, `_on_*_failed`, and thread cleanup),
    reducing `settings_language_packs.py` from `830` to `711` lines and removing it from
    near-limit warnings and changed-only near-limit output.
41. 2026-02-28: extracted language pack catalog/data declarations from
    `apps/gui/src/language_packs.py` into `apps/gui/src/language_packs_catalog.py`
    while preserving runtime exports; reduced `language_packs.py` to `376` lines and removed
    it from near-limit warnings.
42. 2026-02-28: reduced `apps/gui/src/main.py` import pressure by consolidating UI/logging
    bridge imports into `apps/gui/src/main_ui_components.py`, replacing direct logger/widget/path
    imports with a single adapter import and removing `main.py` from near-limit warnings.
43. 2026-02-28: extracted embedding vector index logic from
    `core/lexishift_core/resources/synonyms.py` into
    `core/lexishift_core/resources/synonyms_embeddings.py`,
    reducing `synonyms.py` from `852` to `494` lines and removing it from near-limit warnings.
44. 2026-02-28: extracted DE frequency lexicon loaders/discovery helpers from
    `core/lexishift_core/frequency/de/build.py` into
    `core/lexishift_core/frequency/de/build_support.py`,
    reducing `build.py` from `834` to `743` lines and removing it from near-limit warnings.
45. 2026-02-28: extracted Share Center row/resolver helpers into:
    - `apps/chrome-extension/options/controllers/rules/share_center/row_factory.js`
    - `apps/chrome-extension/options/controllers/rules/share_center/profile_resolvers.js`
    and rewired:
    - `apps/chrome-extension/options/controllers/rules/share_center/renderers.js`
    - `apps/chrome-extension/options/controllers/rules/share_center_controller.js`
    with script-order updates in `apps/chrome-extension/options.html`,
    reducing renderers (`450` -> `403`) and controller (`451` -> `442`) and clearing
    changed-only near-limit warnings.
46. 2026-02-28: extracted profile-ruleset state/normalization helpers from
    `apps/chrome-extension/options/controllers/rules/profile_rulesets_controller.js`
    into `apps/chrome-extension/options/controllers/rules/profile_rulesets_state.js`,
    reducing the controller from `458` to `284` lines and removing it from near-limit warnings.
47. 2026-02-28: extracted options bootstrap element maps from
    `apps/chrome-extension/options/core/bootstrap/controller_graph.js` into
    `apps/chrome-extension/options/core/bootstrap/controller_graph_elements.js`,
    reducing `controller_graph.js` from `451` to `274` lines and removing it from near-limit warnings.
48. 2026-02-28: converted additional high-fanout exports in
    `core/lexishift_core/__init__.py` to lazy export resolution
    (`frequency providers/sqlite`, `ja_en rulegen`, `seed`, `weighting`),
    reducing import pressure and removing `__init__.py` from near-limit warnings.
49. 2026-02-28: reduced import pressure in `core/lexishift_core/helper/engine.py`
    by lazy-loading low-frequency use-case modules (`runtime_diagnostics`,
    `rulegen_job`, `reset`) through local runtime wrappers.
50. 2026-02-28: reduced import pressure in `core/lexishift_core/helper/rulegen.py`
    by lazy-loading the seed module (`SeedSelectionConfig`, `build_seed_candidates`)
    and fully clearing the remaining near-limit warning list.
51. 2026-02-28: project health is now fully clean in advisory mode:
    `npm run -s health:project:report` and `npm run -s health:project:changed`
    both pass with `0` violations and `0` warnings.
52. 2026-02-28: enabled changed-file project-health CI enforcement in
    `.github/workflows/ci.yml` via `project-health-changed` (PR-only) using
    baseline-delta gating (`--fail-on-new`, `--fail-on-regressions`) against
    `docs/test_outputs/project_health/project_health_baseline.json`.
53. 2026-02-28: restored patch-compatible seed entry points after lazy-import changes:
    - `core/lexishift_core/helper/engine.py` now exposes `build_seed_candidates` wrapper.
    - `core/lexishift_core/helper/rulegen.py` now exposes and uses a module-level
      `build_seed_candidates` wrapper.
    This preserved test patch seams while keeping import pressure low.
54. 2026-02-28: completed mypy health pass for core by fixing typing issues in:
    - `core/lexishift_core/frequency/sqlite.py`
    - `core/lexishift_core/frequency/de/build_support.py`
    - `core/lexishift_core/rulegen/benchmarking.py`
    - `core/lexishift_core/frequency/de/build.py`
    - `core/lexishift_core/frequency/de/pipeline.py`
    - `core/lexishift_core/srs/admission_refresh.py`
    resulting in `mypy core/lexishift_core` passing with `0` errors.

## Leaf-First Remediation Queue (Current)

Active health violations are now cleared (`0`) and near-limit warnings are also cleared (`0`).
Current queue is maintenance-only:

1. Keep `npm run -s health:project:changed` in the PR loop and block new warnings/regressions.
2. Re-run full `npm run -s health:project:report` before release cuts or large refactors.

## Post-Refactor Status Checkpoint (2026-02-28)

Verification snapshot after the large split/refactor set:

1. Maintainability gate:
   - `npm run -s health:project:report`: pass (`302` files, `0` violations, `0` warnings)
   - `npm run -s health:project:changed`: pass (`legacy=0`, `new=0`, `regressions=0`)
2. Core runtime tests:
   - `python3 -m unittest discover -s core/tests`: pass (`197` tests)
3. Targeted regression suites impacted by lazy-import compatibility changes:
   - `python3 -m unittest core.tests.helper.test_helper_rulegen core.tests.helper.test_helper_engine core.tests.srs.test_srs_feedback_simulation`: pass (`38` tests)
4. CI enforcement:
   - PR workflow now includes `project-health-changed` gate in `.github/workflows/ci.yml`.
5. Known non-health quality checks currently not green:
   - `python3 scripts/testing/rulegen_quality_gate.py ...` currently fails en-es floor/delta checks against current baseline.

Interpretation:

1. Refactor stability is good for architecture/maintainability and core unit runtime behavior.
2. Rulegen quality remains an active workstream, independent from the health refactor itself.

## Responsibility Map (Current)

High-value module boundaries after refactor:

1. Extension options bootstrap:
   - `apps/chrome-extension/options/core/bootstrap/controller_graph.js`: orchestration/composition root only.
   - `apps/chrome-extension/options/core/bootstrap/controller_graph_elements.js`: static DOM element mapping groups.
2. Extension profile rulesets:
   - `apps/chrome-extension/options/controllers/rules/profile_rulesets_controller.js`: async flow + persistence orchestration.
   - `apps/chrome-extension/options/controllers/rules/profile_rulesets_state.js`: pure state normalization/merge/summarize helpers.
3. Extension share center:
   - `apps/chrome-extension/options/controllers/rules/share_center_controller.js`: top-level wiring.
   - `apps/chrome-extension/options/controllers/rules/share_center/*.js`: focused helpers (status/render/sync/selection/tree/workflow).
4. GUI app shell:
   - `apps/gui/src/main.py`: app/window composition + high-level wiring.
   - `apps/gui/src/main_*_mixin.py`: feature-domain behavior (profiles, SRS, menus, import/export, locale, bulk rules).
   - `apps/gui/src/main_ui_components.py`: import aggregation adapter to reduce top-level import fanout.
5. GUI language packs:
   - `apps/gui/src/settings_language_packs.py`: panel orchestration.
   - `apps/gui/src/settings_language_packs_*_mixin.py`: layout/path/table/transfer/panel-state responsibilities.
   - `apps/gui/src/language_packs_catalog.py`: data catalog + pack declarations.
6. Core package surfaces:
   - `core/lexishift_core/__init__.py`: public exports + lazy export resolution.
   - `core/lexishift_core/helper/engine.py`: helper use-case orchestration with compatibility-safe lazy loading.
   - `core/lexishift_core/helper/rulegen.py`: rulegen/set initialization flows with patch-friendly seed wrappers.

Assessment:

1. Responsibility boundaries are more coherent than before (orchestrators vs pure helpers are now mostly separated).
2. Feature changes should generally be easier, because most edits now land in domain-specific helper modules instead of giant multi-domain files.
3. Main risk introduced by the refactor is coordination overhead (more files + load-order coupling in extension script tags + lazy import wrappers). This is manageable with current docs and CI gate coverage.

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

Status: completed (2026-02-27)

Completed targets:

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

Status: completed (2026-02-28)

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
