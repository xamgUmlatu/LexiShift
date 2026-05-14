# Productization Lane 5 Runtime Seam Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 focused helper, extension, SRS harness, SRS summary, feedback simulation tests plus SRS quality harness artifact refresh
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
