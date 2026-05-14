# Productization Lane 5 Runtime Seam Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 focused helper, extension, SRS harness, SRS summary, feedback simulation, semantic gate/runtime exception containment, DOM-scan metrics, SRS settings, diagnostics, action formatter, and semantic policy tests plus SRS quality harness artifact refresh
Purpose: record high-risk runtime seam closure slices so runtime behavior is fixed, tested, and documented before expansion resumes
Source-of-truth: inventory only; current runtime truth lives in source code, tests, generated evidence, `feature_state_matrix.md`, and seam-specific canonical docs.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane3_feature_state_truth_inventory.md`
- `productization_lane4_validation_gate_inventory.md`
- `productization_lane6_data_provenance_inventory.md`
- `feature_state_matrix.md`
- `../srs/README.md`
- `../srs/srs_practice_layer_design.md`
- `../srs/srs_roadmap.md`

## Scope

Lane: Lane 5, high-risk runtime seams.

Completed slices:

1. L5-A: due-aware SRS runtime serving.
2. L5-B: semantic admission unavailable-scoring fallback.
3. L5-C: semantic fallback reason diagnostics.
4. L5-D: semantic helper decision-service exception containment.
5. L5-E: semantic inventory exception containment.

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

## L5-C Semantic Fallback Reason Diagnostics

Product claim:

- Runtime diagnostics should show why semantic admission fell back, not just how
  many matches used a fallback decision.

Before this slice:

| Surface | Current Truth Before L5-C |
| --- | --- |
| Decision detail | Individual semantic decisions carried `reason_codes`. |
| Aggregate scan state | DOM scan and runtime diagnostics preserved aggregate fallback replace/abstain/soft-affordance counts, but not reason-code buckets. |
| Options diagnostics | The SRS runtime diagnostics action could show that fallback happened, but not whether the dominant cause was non-ready metadata, missing inventory, helper transport, or malformed helper response. |

Closure action:

- Semantic gate summaries now aggregate fallback decision `reason_codes`.
- DOM scan metrics merge those buckets across text-node admissions.
- Apply diagnostics persist the aggregate as
  `semantic_fallback_reason_counts` in the last runtime state.
- The options-page SRS runtime diagnostics formatter renders those counts as a
  JSON object.

After this slice:

| Surface | Current Truth After L5-C |
| --- | --- |
| Runtime gate | Scoring behavior is unchanged; only aggregate observability changed. |
| Debug logs | Semantic apply summaries include fallback reason buckets when eligible matches used fallback policy. |
| Persisted diagnostics | `srsRuntimeLastState.semantic_fallback_reason_counts` records normalized aggregate counts such as `semantic_status_pending`, `semantic_inventory_unavailable`, and `decision_service_error`. |
| Options diagnostics | `SRS runtime diagnostics` includes `semantic_fallback_reason_counts`, so operators can distinguish non-ready metadata from helper/inventory failures without inspecting per-replacement DOM attributes. |

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py \
  core/tests/dev/test_extension_dom_scan_runtime_contract.py \
  core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py \
  core/tests/dev/test_extension_srs_action_formatters.py
```

L5-C does not yet close:

1. automatic remediation or retry behavior for helper semantic service errors,
2. durable cross-session trend reporting,
3. BetterDiscord/plugin runtime parity,
4. user-facing explanations for individual abstained replacements.

## L5-D Semantic Helper Decision-Service Exception Containment

Product claim:

- A thrown helper semantic decision-service exception should not abort page
  scanning or silently bypass semantic admission when the current runtime is
  capable.

Before this slice:

| Surface | Current Truth Before L5-D |
| --- | --- |
| Helper decision service | A thrown `semanticAdmitBatch(...)` call could reject the queued admission batch instead of being recorded as a helper service fallback. |
| Diagnostics | Non-throwing helper decision-service failures were visible through existing error fields and fallback reason counts, but thrown helper exceptions were not contained at the semantic gate boundary. |

Closure action:

- Helper semantic-admission exceptions are caught per helper request chunk.
- The gate converts those failures into the existing fail-closed fallback path:
  - `decision_service_error` for helper decision-service exceptions
- The corresponding `helperError` field is populated so debug logs and
  persisted diagnostics retain the failure message.

After this slice:

| Surface | Current Truth After L5-D |
| --- | --- |
| Runtime gate | Thrown helper semantic decision-service failures are contained and resolve through the configured fallback policy, which defaults to `abstain_on_unavailable`. |
| Scan continuity | A helper semantic exception no longer rejects the whole queued admission batch for the current page scan. |
| Diagnostics | Existing fallback reason diagnostics now include thrown helper decision-service failures via `decision_service_error`. |
| Scoring policy | Scorer behavior and decision thresholds are unchanged; this only hardens the failure boundary. |

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py
```

L5-D does not yet close:

1. automatic retry/backoff after helper semantic service errors,
2. durable cross-session trend reporting,
3. BetterDiscord/plugin runtime parity,
4. user-facing explanations for individual abstained replacements.

## L5-E Semantic Inventory Exception Containment

Product claim:

- A thrown semantic inventory-resolution exception should not abort page
  scanning or silently bypass semantic admission when the current runtime is
  capable.

Before this slice:

| Surface | Current Truth Before L5-E |
| --- | --- |
| Inventory resolution | A rejected `resolveSemanticInventory(...)` call could reject the semantic admission batch instead of returning a fail-closed fallback decision. |
| Diagnostics | Non-throwing inventory failures were visible through existing error fields and fallback reason counts, but thrown inventory exceptions were not contained at the semantic gate boundary. |

Closure action:

- Semantic inventory resolution exceptions are caught per ready group.
- The gate converts those failures into the existing fail-closed fallback path:
  - `semantic_inventory_unavailable` for inventory exceptions
- The corresponding `inventoryError` field is populated so debug logs and
  persisted diagnostics retain the failure message.

After this slice:

| Surface | Current Truth After L5-E |
| --- | --- |
| Runtime gate | Thrown semantic inventory-resolution failures are contained and resolve through the configured fallback policy, which defaults to `abstain_on_unavailable`. |
| Scan continuity | An inventory route exception no longer rejects the whole queued admission batch for the current page scan. |
| Diagnostics | Existing fallback reason diagnostics now include thrown inventory failures via `semantic_inventory_unavailable`. |
| Scoring policy | Scorer behavior and decision thresholds are unchanged; this only hardens the failure boundary. |

Validation:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py
```

L5-E does not yet close:

1. automatic retry/backoff after helper semantic service errors,
2. durable cross-session trend reporting,
3. BetterDiscord/plugin runtime parity,
4. user-facing explanations for individual abstained replacements.

## Remaining Runtime Seam Triage

Current expansion-gate read:

- No known browser-extension runtime fail-open blocker remains in the Lane 5
  SRS/semantic admission path after L5-A through L5-E.
- The current safe posture is conservative:
  - future-due helper SRS rules are filtered at runtime when due metadata is
    present,
  - semantic unavailable-scoring defaults to `abstain_on_unavailable`,
  - helper decision-service exceptions fail closed,
  - inventory-resolution exceptions fail closed,
  - fallback reason counts are visible in runtime diagnostics.
- This does not mean expansion is ready by itself. It means the next broad
  blocker is no longer this browser runtime fail-closed seam; it shifts to
  Lane 6 data provenance, pack lifecycle, source auditability, and generated
  artifact traceability.

Must fix before broad expansion:

| Item | Owner Lane | Rationale |
| --- | --- | --- |
| Pack/source provenance and installed-resource auditability | Lane 6 | Expansion adds more local/generated data. The next release-quality risk is knowing exactly which source files, generated SQLite packs, manifests, installed paths, and licenses are active. |
| Expansion readiness checklist | Lane 6 / closure roadmap | Expansion should resume only when runtime truth, diagnostics truth, pack provenance, validation commands, and artifact ownership are explicitly linked. Start from `productization_lane6_data_provenance_inventory.md`. |

Useful but not expansion-blocking runtime hardening:

| Item | Current posture | Why not blocking |
| --- | --- | --- |
| Helper semantic retry/backoff | Fail-closed now; no automatic retry. | Retry can improve availability, but incorrect retry policy can add page latency and complexity. It should be designed separately instead of rushed into the safety seam. |
| Durable cross-session runtime trend reporting | Last runtime state plus helper/cache diagnostics exist. | Trend reporting helps operations, but the per-run diagnostics now expose the reason buckets needed for manual triage. |
| Metadata migration for old cached helper SRS rules | Metadata-free cached helper rules remain active for compatibility. | Regenerated helper publications carry due metadata; migration is useful cleanup, not a blocker for new generated artifacts. |
| Dedicated due-only helper publication artifact | Runtime gate now filters future-due rules from broad helper publications. | A due-only artifact would simplify the publication model, but runtime serving is already due-aware when metadata exists. |

Defer out of Lane 5:

| Item | Defer To | Rationale |
| --- | --- | --- |
| Rendered `soft_affordance` UX | Product/UX runtime lane | Current DOM behavior treats non-`replace` decisions as keep-original, which is safe. The visible affordance should be designed deliberately. |
| User-facing explanations for individual abstains | Product/UX diagnostics lane | Operator diagnostics now have aggregate reasons. End-user explanations need separate copy and interaction design. |
| BetterDiscord/plugin runtime parity | Platform parity lane | Lane 5 has closed the browser-extension runtime seam; plugin parity should be tracked as a platform-specific runtime surface. |
| Automatic semantic pack rollout | Pack lifecycle / launch lane | Rollout policy depends on provenance, install/update behavior, and launch controls, not only runtime safety. |
