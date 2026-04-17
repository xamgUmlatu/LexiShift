# SRS Admission Selective Port Sequence

Status: phases 1-5 implemented; phase 6 pending
Role: execution runbook
Last updated: 2026-04-18
Purpose: define the exact sequence for porting the admission/preferences workstream from `codex/srs-admission-checkpoint` onto `codex/veto-data-sources-exp` without regressing the current semantic publication/runtime contract
Related docs:
- `docs/developer/srs_admission_merge_seam_map.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
- `docs/developer/feature_state_matrix.md`
- `docs/srs/srs_profile_schema.md`

## Why This Exists

The admission branch is not a candidate for wholesale merge.

The correct operation is:

1. port the upstream admission functionality that is genuinely additive,
2. preserve the current semantic publication/runtime base,
3. manually reconcile the small helper/publication seam where both workstreams meet.

This runbook is the exact order for doing that safely.

## Non-Negotiable Invariants

Every phase below must preserve these current-branch truths.

### Semantic publication invariants

These must remain true after every phase:

- helper publication still writes:
  - ruleset
  - snapshot
  - semantic inventory
  - publication manifest
- helper publication still stamps a shared `generation_id`
- semantic inventory and manifest still validate as one publication family
- helper still serves `semantic_admit_batch`

### Runtime invariants

These must remain true after every phase:

- semantic runtime remains opt-in/default-off
- semantic fallback behavior remains unchanged
- extension runtime can still consume helper-published semantic inventory

### Branch hygiene invariants

These must remain true after every phase:

- the worktree ends clean
- each phase lands as its own checkpoint commit
- tests for both the admission side and the semantic side stay green

## Merge Strategy

Use three merge modes only.

### Mode A: direct additive port

Use this when the current branch does not already contain the module.

Expected operation:

- add the file with minimal adaptation
- wire imports/exports
- add tests

### Mode B: graft onto current base

Use this when both branches touch the file but the current branch owns the newer semantic contract.

Expected operation:

- start from the current branch file
- port the admission-specific behavior into it
- keep current semantic publication/runtime behavior as the base truth

### Mode C: docs after code

Use this for docs whose claims depend on integrated code.

Expected operation:

- do not copy docs first if they would overclaim integrated behavior
- update docs only after the executable seam is really present

## Phase 0: Freeze The Base

Goal:

- establish the exact baseline that must not regress

No admission code is ported yet.

Actions:

1. Record current semantic publication/runtime baseline artifacts and tests.
2. Keep the current branch versions of:
   - `core/lexishift_core/helper/rulegen_outputs.py`
   - `core/lexishift_core/helper/use_cases/semantic_admission.py`
   - `docs/rulegen/semantic_routing_*`
   - `docs/test_inputs/semantic_routing/*`
3. Treat those files as protected base files for the rest of the port.

Validation gate:

- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`

Checkpoint:

- no code change unless baseline notes need refresh
- Current refresh result on `2026-04-18`:
  - the protected semantic base files remain unchanged:
    - `core/lexishift_core/helper/rulegen_outputs.py`
    - `core/lexishift_core/helper/use_cases/semantic_admission.py`
    - `docs/rulegen/semantic_routing_*`
    - `docs/test_inputs/semantic_routing/*`
  - the minimum semantic baseline suite remains the same Phase 0 gate:
    - `core/tests/rulegen/test_semantic_publication.py`
    - `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
    - `core/tests/helper/test_rulegen_outputs.py`
    - `core/tests/architecture/test_extension_structure.py`
    - `core/tests/dev/test_helper_translation_dict_entrypoints.py`
  - the protected semantic contract to preserve before further admission work is:
    - helper publication writes one family of ruleset + snapshot + optional semantic inventory + publication manifest
    - publication family artifacts stay aligned by shared `generation_id`
    - helper/native-host continues to expose `semantic_admit_batch`
    - browser semantic runtime remains opt-in/default-off and only ready SRS-origin matches reach helper semantic admission
  - refreshed validation on `2026-04-18` reran green:
    - `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
    - `27 passed`
    - `python3 scripts/dev/check_doc_references.py`
  - adjacent Wave C findings about due-aware serving and helper-rule confidence gating are intentionally out of scope for the semantic freeze; later admission slices must not blur those SRS/runtime caveats into semantic-contract edits

## Phase 1: Port Pure Admission Core

Goal:

- add the upstream admission math and data structures without touching helper publication yet

Port mode:

- mostly Mode A

Expected files:

- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/rebalance.py`
  Current checkpoint note: landed in Phase 3 alongside the preview/rebalance helper surface because the upstream module depends on explicit active inventory.
- any directly required support updates in:
  - `core/lexishift_core/srs/admission_policy.py`
  - `core/lexishift_core/srs/selector.py`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/srs/set_strategy.py`

Tests to port with this phase:

- `core/tests/srs/test_profile_bootstrap.py`
- `core/tests/srs/test_srs_rebalance.py`
  Current checkpoint note: landed in Phase 3 with the rebalance module for the same inventory dependency reason.
- `core/tests/dev/test_srs_admission_preference_sanity.py`
- `core/tests/dev/test_srs_frequency_topic_coverage.py`

Scripts to port with this phase:

- `scripts/testing/srs_admission_preference_sanity.py`
- `scripts/testing/srs_frequency_topic_coverage.py`

Manual rules:

- do not let this phase alter semantic helper/runtime files
- if a shared SRS file already exists on the current branch, start from current branch and graft only the admission-specific logic

Validation gate:

- targeted SRS tests for the ported modules
- `python3 scripts/testing/srs_admission_preference_sanity.py`
- `python3 scripts/testing/srs_frequency_topic_coverage.py`
- semantic publication/runtime baseline tests from Phase 0

Checkpoint:

- commit after the core admission math/tests pass

## Phase 2: Port Explicit Active Inventory

Goal:

- separate active-inventory membership from retained SRS history

Port mode:

- Mode A for inventory module
- Mode B for exports and helper paths

Expected files:

- add `core/lexishift_core/srs/inventory.py`
- update `core/lexishift_core/srs/__init__.py`
- update `core/lexishift_core/helper/paths.py`

Required behavior after this phase:

- helper paths expose `srs_inventory_path_for(profile_id)`
- code can load/save explicit pair-local active inventory
- no publication flow uses inventory yet unless explicitly wired in later phases

Manual rules:

- this phase should not rewrite rule publication behavior yet
- the new inventory file should be additive to the current store/status/snapshot/ruleset layout

Validation gate:

- unit tests for inventory serialization and helpers
- targeted helper path tests if needed
- semantic publication/runtime baseline tests from Phase 0

Checkpoint:

- commit after inventory persistence exists and does not affect semantic publication

## Phase 3: Add Helper API Surface For Admission Preview / Rebalance

Goal:

- expose the new admission functionality through helper engine and CLI without changing published semantic artifacts yet

Port mode:

- Mode B

Expected files:

- `core/lexishift_core/helper/engine.py`
- `scripts/helper/lexishift_helper.py`
- add `core/lexishift_core/helper/use_cases/admission_preview.py`
- add rebalance config/use-case wiring

Required new capabilities:

- helper config dataclasses for preview/rebalance
- helper entrypoints for:
  - admission preview
  - rebalance preview
  - rebalance apply
- CLI commands for the same

Manual rules:

- preserve existing helper semantic APIs and imports
- do not remove `semantic_admit_batch`
- do not replace current rulegen-job or diagnostics behavior wholesale

Validation gate:

- targeted helper-engine tests for new preview/rebalance surfaces
- existing semantic helper/runtime tests
- `python3 scripts/dev/check_doc_references.py`

Checkpoint:

- commit after helper can expose preview/rebalance while semantic helper APIs remain intact
- Current phase result on `2026-04-15`:
  - helper engine now exposes admission preview, rebalance preview, and rebalance apply
  - CLI now exposes `preview_srs_admission`, `plan_srs_rebalance`, and `apply_srs_rebalance`
  - rebalance now updates explicit active inventory and republishes the current semantic artifact family
  - initialize/refresh/runtime diagnostics still remain on the separate Phase 4 reconciliation track

## Phase 4: Reconcile Inventory-Aware Admission Mutation With Current Semantic Publication

Goal:

- make initialize/refresh plus runtime-facing diagnostics use explicit active inventory consistently
- keep current semantic publication family intact

Port mode:

- Mode B only

This is the highest-risk phase.

Expected files:

- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/reset.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/helper/use_cases/rulegen_job.py`

Required integrated behavior:

### Initialize

- initialization persists `srs_inventory.json`
- active item ids are explicitly derived and stored
- rulegen/publication runs against the active inventory
- `write_rulegen_outputs(...)` still receives `semantic_inventory=getattr(rulegen_output, "semantic_inventory", None)`

### Refresh

- refresh updates explicit active inventory when new words enter `S`
- refresh-triggered publication still writes:
  - semantic inventory
  - publication manifest
  - shared `generation_id`

### Rebalance

- already landed in Phase 3; preserve that behavior while reconciling the remaining flows

### Reset

- reset clears pair-local inventory as well as the existing pair/profile state
- semantic publication artifacts should be cleared consistently with current branch behavior

### Diagnostics

- diagnostics should report both:
  - inventory state
  - semantic publication state

Manual rules:

- current-branch `rulegen_outputs.py` remains the base file
- do not port the admission branch version of `rulegen_outputs.py`
- do not port any removal of semantic helper/runtime code

Validation gate:

- targeted helper tests for initialize/refresh/reset/rebalance flows
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
- semantic publication/runtime baseline tests from Phase 0
- one real local `en-es` publication smoke:
  - ruleset
  - snapshot
  - semantic inventory
  - manifest
  - valid shared `generation_id`

Checkpoint:

- commit only after inventory-aware flows coexist with the current semantic publication family

## Phase 5: Port Extension Preference UI And Workflows

Goal:

- expose the admission/preferences workstream in options without destabilizing runtime veto

Port mode:

- Mode B

Expected files:

- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
- `apps/chrome-extension/options/controllers/srs/planning_state.js`
- `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `apps/chrome-extension/options/controllers/srs/actions/planning_state_resolver.js`
- `apps/chrome-extension/options/controllers/srs/actions/admission_preview_formatter.js`
- `apps/chrome-extension/options/controllers/srs/actions/admission_preview_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions/rebalance_formatter.js`
- `apps/chrome-extension/options/controllers/srs/actions/rebalance_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions_controller.js`
- `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- related UI/controller glue files

Required behavior:

- user can edit preference signals
- preview and rebalance workflows call helper with normalized `profile_context`
- runtime semantic veto remains downstream and unchanged

Manual rules:

- preserve any current branch settings/runtime fields unrelated to admission
- keep profile/pair scoping consistent with current semantic runtime settings

Validation gate:

- targeted extension/controller tests where available
- `node --check` for touched extension JS files
- helper-side preview/rebalance smoke
- semantic runtime baseline tests from Phase 0

Checkpoint:

- commit after the options flow can drive preview/rebalance without breaking existing semantic controls
- Current phase result on `2026-04-15`:
  - options UI now exposes admission-preference fields for topic interests, proficiency estimate, and challenge target
  - unsaved form overrides are normalized into a shared planning-state resolver before initialize/preview/rebalance/refresh helper calls
  - extension helper transport and native host now expose admission preview plus rebalance preview/apply
  - semantic admission toggle/fallback policy and runtime diagnostics remain on the current semantic base path
  - validation passed via `node --check` on touched extension JS, `python3 -m pytest core/tests/helper/test_helper_engine.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`, and `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`

## Phase 6: Clean The Contract Mismatches

Goal:

- resolve the two logged schema issues instead of carrying them indefinitely

This phase is intentionally after executable integration.

Issue A:

- unknown-key preservation mismatch

Resolution choices:

1. tighten docs to explicit allowlist `v1`
2. or implement true unknown-key passthrough in signals/profile-context plumbing

Issue B:

- `constraints` / `sizing` ambiguity

Resolution choices:

1. document top-level helper config fields as authoritative
2. or implement helper fallback from nested `profile_context.constraints` / `profile_context.sizing`

Validation gate:

- docs and executable contract agree
- no silent lossy signal path remains undocumented

Checkpoint:

- commit once docs and code match

## Phase 7: Docs And State Matrix

Goal:

- update repo-facing status docs only after integrated code is real

Expected docs:

- `docs/developer/feature_state_matrix.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_preference_update_and_rebalance_policy.md`
- `docs/developer/srs_admission_runtime_veto_handoff.md`

Manual rules:

- do not overclaim integration before code lands
- keep contradictions explicit if any remain

Validation gate:

- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state` if state-matrix claims change

Checkpoint:

- final documentation commit after integrated behavior is verified

## Proposed Commit Structure

The safest checkpoint structure is:

1. `Port SRS admission core modules`
2. `Add explicit SRS inventory manifest`
3. `Add helper admission preview and rebalance APIs`
4. `Integrate inventory-aware admission with semantic publication`
5. `Add admission preference options workflows`
6. `Align admission profile schema contracts`
7. `Document integrated admission and semantic runtime state`

## What Not To Do

Do not:

- merge the admission branch wholesale
- replace current `rulegen_outputs.py`
- replace current semantic helper runtime files with older branch versions
- update docs first and “fill in” code later
- let inventory-aware publication regress to ruleset+snapshot-only behavior

## Immediate Next Execution Move

When actual port work begins, start with Phase 1 only:

- add the pure admission core modules
- add their tests/scripts
- keep helper publication untouched

That is the highest-signal, lowest-risk first patch.
