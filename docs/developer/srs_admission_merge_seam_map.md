# SRS Admission Merge Seam Map

Status: active plan
Role: Planning / WIP
Last updated: 2026-04-15
Purpose: record the known schema-contract issues from `codex/srs-admission-checkpoint` and map the selective-merge seams onto `codex/veto-data-sources-exp` so the admission workstream can be ported without regressing the current semantic runtime/publication contract
Source-of-truth: planning doc only; code truth still lives in the current branch and the reviewed admission branch worktree

## Scope

This note assumes:

- `codex/srs-admission-checkpoint` is an admission/preferences-focused branch
- `codex/veto-data-sources-exp` is the current branch carrying the semantic runtime/publication contract
- the goal is not a wholesale merge
- the goal is a selective port that preserves current semantic runtime behavior

The main conclusion from the review is:

- most of the admission branch is conceptually additive
- the real conflict surface is small
- but that small surface sits directly on helper publication/runtime seams that semantic veto now depends on

## Logged Issues To Address Later

These are real issues in the admission branch review and should stay explicit until addressed.

### 1. Unknown-key preservation mismatch

At review time, the profile-schema docs were still easy to read as a broader passthrough contract.

But the actual extension settings path rebuilds the signals object from a fixed allowlist:

- `interests`
- `objectives`
- `proficiency`
- `difficultyPreferences`
- `empiricalTrends`
- `sourcePreferences`

So any future signal field outside that allowlist will be dropped before it reaches helper code.

Implication:

- the current executable contract is effectively fixed-allowlist, not “preserve unknown keys”
- the canonical schema doc now reflects that fixed `v1` allowlist, but selective-port work still must not assume arbitrary top-level signal passthrough

Future resolution options:

- add a real passthrough lane for unknown signal keys

### 2. `constraints` / `sizing` ambiguity

At review time, the profile-schema docs still made nested `constraints` / `sizing` look more executable than they really were.

But the executable helper path does not consume those nested fields as the authoritative input.

Actual execution shape today:

- sizing is sent as top-level helper request fields such as `set_top_n`, `bootstrap_top_n`, `initial_active_count`, and `max_active_items_hint`
- helper use cases resolve sizing from those top-level config fields
- `profile_context` is used for normalized preference signals, not as the authoritative sizing source

Implication:

- nested `constraints` / `sizing` should be treated as descriptive mirrors, not the live execution authority
- the canonical schema doc now reflects that, but selective-port work still must not assume nested fallback sizing is active in helper code

Future resolution options:

- explicitly teach helper to honor nested fallback values from `profile_context`

## Merge Summary

The admission branch should be treated as four buckets.

### Bucket A: safe additive ports

These are mostly new modules or conceptually isolated additions.

- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/rebalance.py`
- `core/lexishift_core/srs/inventory.py`
- `core/lexishift_core/helper/use_cases/admission_preview.py`
- `core/tests/srs/test_profile_bootstrap.py`
- `core/tests/srs/test_srs_rebalance.py`
- `core/tests/dev/test_srs_admission_preference_sanity.py`
- `core/tests/dev/test_srs_frequency_topic_coverage.py`
- `scripts/testing/srs_admission_preference_sanity.py`
- `scripts/testing/srs_frequency_topic_coverage.py`
- most new admission-specific docs under `docs/srs/`

Why these are relatively safe:

- the current branch largely does not already contain these exact modules
- they do not need to replace the current semantic runtime contract
- they mostly add upstream admission capabilities rather than rewriting veto behavior

### Bucket B: overlapping but mergeable UI/settings seams

These files already exist on the current branch and would need field-level merge work rather than wholesale replacement.

- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
- `apps/chrome-extension/options/controllers/srs/planning_state.js`
- `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions/secondary_workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
- `apps/chrome-extension/options/controllers/srs/actions_controller.js`

Why these should be merged carefully:

- they add useful preference-editing and preview/rebalance plumbing
- but they touch existing options/runtime code paths that may have drifted independently

### Bucket C: helper/SRS execution seams that require manual reconciliation

These are the important merge seams.

- `core/lexishift_core/helper/paths.py`
- `core/lexishift_core/helper/engine.py`
- `scripts/helper/lexishift_helper.py`
- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/reset.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/helper/use_cases/rulegen_job.py`
- `core/lexishift_core/srs/__init__.py`

Why these are the real seam:

- the admission branch adds explicit pair-local active inventory and rebalance behavior here
- the current branch already has a newer semantic publication/runtime contract here
- both workstreams are valid, but they cannot be merged by taking one side wholesale

The target integrated behavior should be:

- keep the current semantic publication family:
  - ruleset
  - snapshot
  - semantic inventory
  - publication manifest
  - shared `generation_id`
- add the admission branch’s pair-local active inventory and rebalance behavior
- keep helper diagnostics aware of both:
  - semantic publication state
  - pair-local active inventory state

### Bucket D: current-branch files that must remain the base

These should not be replaced by the admission branch versions.

- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/use_cases/semantic_admission.py`
- current semantic publication/readiness docs under `docs/rulegen/`
- current semantic planning schemas under `docs/test_inputs/semantic_routing/`

Reason:

- the admission branch versions predate the current semantic runtime/publication checkpoint
- replacing these files would remove:
  - semantic sidecar publication
  - publication manifest writing/validation
  - shared `generation_id`
  - live helper-side semantic admission support

## Recommended Selective-Port Order

The safest merge order is:

1. Port Bucket A additive SRS modules and their tests.
2. Port pair-local active inventory persistence:
   - `srs_inventory.json`
   - `srs_inventory_path_for(...)`
   - inventory load/save/resolve helpers
3. Add helper preview/rebalance API surfaces:
   - config dataclasses
   - helper CLI commands
   - engine entrypoints
4. Manually reconcile the execution seams:
   - `initialize_set.py`
   - `refresh_set.py`
   - `reset.py`
   - `runtime_diagnostics.py`
   - `rulegen_job.py`
   so they preserve both inventory behavior and current semantic publication behavior
5. Merge the extension settings/UI wiring.
6. Update docs after the executable contract is stable.

## Specific Manual-Reconciliation Rules

When the actual merge starts, these rules should stay explicit.

### Rule 1

Do not take the admission branch version of `helper/rulegen_outputs.py`.

Instead:

- keep the current branch file as the base
- thread any needed inventory-aware callers into the current semantic publication writer

### Rule 2

Do not take the admission branch deletion/reversion of helper semantic runtime code.

Instead:

- preserve the current branch semantic helper/use-case path
- add admission-side inventory/rebalance behavior around it

### Rule 3

Treat `runtime_diagnostics.py` as a join point.

The integrated diagnostics should eventually report both:

- semantic publication health
- active inventory / inventory source / last rebalance or refresh state

### Rule 4

Treat `paths.py`, `engine.py`, and `lexishift_helper.py` as API join points.

They should expose:

- the current semantic artifact/runtime APIs
- plus the new admission preview/rebalance APIs

without silently dropping either family.

## Validation Plan After Selective Merge

Once the actual selective merge starts, validation should include both workstreams.

Admission-side:

- targeted SRS admission/profile/rebalance tests from the admission branch
- `python3 scripts/testing/srs_admission_preference_sanity.py`
- `python3 scripts/testing/srs_frequency_topic_coverage.py`

Current semantic-side:

- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`

Repo hygiene:

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`

If helper publication, admission refresh, or runtime SRS serving changes materially, also keep the AGENTS SRS quality loop in scope:

- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`

## Bottom Line

The admission branch is not a dead-end.

The correct reading is:

- most of it is still useful
- the merge risk is concentrated
- and the concentrated risk is mainly at the helper publication boundary

So the right future merge strategy is:

- selective port
- preserve current semantic publication/runtime base
- explicitly join in admission inventory, preview, and rebalance
- and keep the two logged schema issues visible until the integrated contract is cleaned up
