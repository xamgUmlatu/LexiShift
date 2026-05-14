# Productization Lane 5 Runtime Seam Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 focused helper, extension, SRS harness, SRS summary, feedback simulation, semantic gate/runtime, SRS settings, diagnostics, and semantic policy tests plus SRS quality harness artifact refresh
Purpose: record high-risk runtime seam closure slices so runtime behavior is fixed, tested, and documented before expansion resumes
Source-of-truth: inventory only; current runtime truth lives in source code, tests, generated evidence, `feature_state_matrix.md`, and seam-specific canonical docs.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane3_feature_state_truth_inventory.md`
- `productization_lane4_validation_gate_inventory.md`
- `feature_state_matrix.md`
- `../srs/README.md`
- `../srs/srs_practice_layer_design.md`
- `../srs/srs_roadmap.md`

## Scope

Lane: Lane 5, high-risk runtime seams.

Completed slices:

1. L5-A: due-aware SRS runtime serving.
2. L5-B: semantic admission unavailable-scoring fallback.

This inventory records runtime closure work only. It does not promote new
frequency/corpus sources, change semantic-veto thresholds, or certify release
packaging.

## L5-A Due-Aware SRS Runtime Serving

Product claim:

- When SRS is enabled, helper-published SRS rules should not make future-due
  study items active just because they are present in the active/admitted
  inventory.

Before this slice:

| Surface | Current Truth Before L5-A |
| --- | --- |
| Scheduler | `select_active_items()` could derive a due queue from `next_due`. |
| Helper publication | Initialize/refresh/rebalance published the active/admitted inventory for the pair. |
| Runtime gate | `srs_gate.js` accepted all helper-published SRS rules as active. |
| SRS harness | The feedback scenario warned that publication was broader than due. |

Closure action:

- Helper rulegen now annotates matching SRS-origin rules with
  `metadata.rulegen.srs`.
- The metadata records `schema_version`, `serving_policy`, `item_id`,
  `next_due`, `in_due`, scheduler state, scheduler step, and `last_review`.
- The extension SRS gate now filters helper SRS rules with future `next_due`
  metadata out of the active runtime set.
- Metadata-free cached helper rules remain active as a legacy compatibility
  fallback until regenerated.

After this slice:

| Surface | Current Truth After L5-A |
| --- | --- |
| Scheduler | Due queue derivation remains the source of due state. |
| Helper publication | Ruleset publication may still cover the active/admitted inventory, not a due-only artifact. |
| Runtime gate | Helper SRS rules with due metadata are active only when `next_due <= now` or no valid due time is present. |
| Legacy cache behavior | Metadata-free helper rules stay active to avoid breaking old cached publications. |
| SRS harness | The feedback scenario verifies runtime due-active count is bounded by the due count while publication remains broader. |

## Validation Bundle

Focused tests:

```bash
python3 -m pytest \
  core/tests/helper/test_helper_rulegen.py \
  core/tests/dev/test_extension_srs_runtime_gate_contract.py \
  core/tests/dev/test_extension_helper_rule_confidence_contract.py \
  core/tests/dev/test_srs_quality_harness.py \
  core/tests/dev/test_srs_quality_summary.py \
  core/tests/srs/test_srs_feedback_simulation.py
```

SRS quality artifact refresh:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json

python3 scripts/testing/srs_quality_summary.py \
  --quality-json docs/test_outputs/srs_quality_latest.json \
  --markdown-out docs/test_outputs/srs_quality_summary_latest.md
```

## Boundaries

L5-A does not yet close:

1. a dedicated due-only helper publication artifact,
2. automatic refresh triggers after feedback,
3. metadata migration for old cached helper rules before the next publication,
4. broader real-user LP coverage beyond the synthetic SRS quality harness,
5. the separate extension-side helper-rule confidence gate.

## L5-B Semantic Admission Unavailable-Scoring Fallback

Product claim:

- If a rule is semantically gated because the current publication is capable,
  missing inventory or unavailable semantic decision service should not silently
  allow a potentially harmful replacement.

Before this slice:

| Surface | Current Truth Before L5-B |
| --- | --- |
| Helper policy | Helper-side runtime semantic policy defaulted to `abstain_on_unavailable`. |
| Extension defaults | Extension settings, active-rule resolution, semantic gate, options profile save, and diagnostics defaulted to `legacy_on_unavailable`. |
| Failure behavior | Ready-rule inventory/helper failures could fall back to `replace` unless the runtime settings explicitly carried `abstain_on_unavailable`. |

Closure action:

- Extension semantic-admission defaults now use `abstain_on_unavailable`.
- The legacy `legacy_on_unavailable` policy remains accepted as an explicit
  compatibility policy, but it is no longer the default posture.
- Semantic gate contract coverage now verifies inventory-unavailable ready
  matches abstain by default and do not reach DOM replacement.

After this slice:

| Surface | Current Truth After L5-B |
| --- | --- |
| Helper policy | Helper and extension defaults both fail closed with `abstain_on_unavailable`. |
| Runtime gate | Ready semantic matches abstain when inventory or helper semantic scoring is unavailable unless an explicit legacy fallback is supplied. |
| Diagnostics | Runtime state reports `abstain_on_unavailable` as the default semantic fallback policy. |
| Compatibility | `legacy_on_unavailable` remains an allowed policy for explicit migration or debug scenarios. |

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py \
  core/tests/dev/test_extension_helper_rule_confidence_contract.py \
  core/tests/dev/test_extension_srs_settings_contract.py \
  core/tests/dev/test_extension_srs_action_formatters.py \
  core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py \
  core/tests/helper/test_helper_engine.py
```

L5-B does not yet close:

1. rendered `soft_affordance` UX,
2. automatic semantic pack rollout,
3. BetterDiscord/plugin runtime parity,
4. persistent helper-side semantic service error surfacing beyond existing diagnostics.
