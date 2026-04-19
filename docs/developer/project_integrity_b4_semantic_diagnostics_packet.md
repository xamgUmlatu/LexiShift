# B4 Semantic Diagnostics Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 targeted extension semantic-diagnostics contract tests, doc/state checks, and staged repo-safety gate
Purpose: bound the `B4` semantic diagnostics join-point slice so helper source-of-truth diagnostics, extension cache diagnostics, and last-reported runtime diagnostics stay explicit about what each layer can and cannot prove
Source-of-truth: packet only; executable truth still lives in extension/helper code, tests, and the semantic publication/runtime contract docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`

## Slice

- Track: `Wave B`
- Slice: `B4`
- Title: semantic diagnostics join-point audit
- Pass type: verification-first with narrow observability follow-through

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/core/helper/diagnostics_methods.js`
- `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
- `apps/chrome-extension/shared/srs/srs_runtime_diagnostics.js`
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
- `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
- `apps/chrome-extension/content/runtime/dom_scan_runtime.js`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_action_formatters.py`
- `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py`
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`

## Explicitly Out Of Scope

This slice does not directly review:

- helper-side publication-manifest generation or reset semantics
- whether cached diagnostics should become a hard gate
- broad semantic rollout readiness or default-on policy
- per-decision browser history or trace retention

## Risk Score

- likelihood: `medium`
- blast radius: `medium-high`
- observability: `medium`
- priority: `high`

Reasoning:

- semantic diagnostics is split across three layers that are easy to misread as equally authoritative
- if the cache layer stays too thin, operators lose a useful middle-tier signal between helper truth and browser live state
- if the cache or runtime layers overclaim, later debugging can mistake stale local state for helper-verified publication truth

## Contract Sketch

The intended current diagnostics split is:

1. helper source-of-truth diagnostics remain the only shipped surface that can assert publication-manifest validity and full generation-family coherence
2. extension cache diagnostics may surface cached artifact presence, counts, cached `generation_id` values, and a simple snapshot-vs-semantic sidecar alignment check
3. last-reported runtime diagnostics may surface live semantic gate enablement, helper/helper-cache resolution source, aggregate decision counts, and the last resolved `decision_policy_id`
4. neither extension cache nor last-reported runtime state should be described as equivalent to helper manifest validation

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Runtime last-state diagnostics now retain `soft_affordance` totals and `decision_policy_id`. | `apply_diagnostics_reporter.js`, `srs_runtime_diagnostics.js` | `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py` | `verified for this slice` |
| Extension cache diagnostics now surface cached snapshot/semantic generation ids and a simple alignment check. | `diagnostics_methods.js`, formatter output | `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py`, `core/tests/dev/test_extension_srs_action_formatters.py` | `verified for this slice` |
| Helper source-of-truth diagnostics remain the only layer that can speak for manifest validity. | semantic publication/docs boundary | code/doc inspection plus contract docs updated in this slice | `verified for this slice` |
| Semantic publication/runtime protections stayed intact while diagnostics observability was widened. | publication/runtime boundary suite | `core/tests/rulegen/test_semantic_publication.py`, `core/tests/rulegen/test_semantic_routing_runtime_policy.py` | `verified for this slice` |

## Invariants

1. helper diagnostics stays authoritative for manifest-family validity
2. cache diagnostics may improve observability, but it stays best-effort local state
3. runtime last-state diagnostics stays aggregate and lightweight rather than becoming a per-decision log
4. docs must distinguish helper truth, cache hints, and live browser last-state instead of collapsing them into one status story

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Cached snapshot + cached semantic inventory share one generation id | cache diagnostics reports matching ids and `snapshot_semantic_generation_aligned=true` |
| Cached snapshot and semantic inventory diverge | cache diagnostics can show non-matching ids without pretending manifest validation |
| Runtime semantic gate produces `soft_affordance` outcomes | last-state diagnostics persists those totals instead of silently dropping them |
| Helper decision service returns a named policy | last-state diagnostics persists the last resolved `decision_policy_id` |
| Helper manifest remains authoritative | docs keep manifest validation helper-only |

## Validation Floor

- `node --check apps/chrome-extension/options/core/helper/diagnostics_methods.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions/formatters.js`
- `python3 -m pytest core/tests/dev/test_extension_srs_action_formatters.py core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py -q`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. tighten the runtime last-state semantic counters to match the live semantic gate summary
2. widen the cache diagnostics layer just enough to expose cached generation ids and simple alignment
3. keep manifest validity and publication-family authority explicitly helper-only

## Outcome

Result:

- runtime last-state diagnostics now persists:
  - `semantic_policy_soft_affordances`
  - `semantic_fallback_soft_affordances`
  - `semantic_decision_policy_id`
- cache diagnostics now surfaces:
  - `cache.snapshot_generation_id`
  - `cache.semantic_inventory_schema_version`
  - `cache.semantic_inventory_generation_id`
  - `cache.snapshot_semantic_generation_aligned`
- formatter coverage and direct helper-diagnostics contract coverage now exercise those fields explicitly
- current-truth docs now state the three-layer diagnostics split more precisely:
  - helper for manifest-valid publication truth
  - cache for best-effort local generation hints
  - runtime last-state for live aggregate semantic behavior
