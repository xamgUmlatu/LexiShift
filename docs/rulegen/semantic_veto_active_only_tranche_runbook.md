# Semantic Veto Active-Only Tranche Runbook

Status: active runbook
Role: Runbook / operational
Last updated: 2026-05-14
Last verified: 2026-05-14 against tranche-001/tranche-006 artifacts, the post-tranche-006 coverage plan, tranche-005 operator checkpoint, active-only generation planner, live generation runner, admission gate, source packaging, pack builder, semantic-pack installer, live-page scanner, registry summary, cost reference, split-inline DOM semantic-context runtime fix, optimized semantic batching, and tranche-003 hands-on browser-extension smoke
Purpose: make future active-only semantic-veto data tranches repeatable, guarded, and easy to checkpoint without reopening algorithm research
Source-of-truth: operational runbook only; current implementation truth lives in the scripts and generated artifacts named below
Related docs:
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/rulegen/semantic_llm_generation_budget_reference.md`
- `docs/rulegen/semantic_pack_operator_smoke_runbook.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/developer/post_veto_productization_and_repo_posture_plan.md`

## Current State

The latest automated-clean soft-assist pack is:

```text
en-es-active-only-combined-full-v1-tranche-006
```

The latest operator-accepted product checkpoint is tranche-005. That acceptance
is based on the tranche-005 automated follow-through summary; the latest
hands-on browser-extension smoke remains tranche-003. Tranche-006 is
automated-clean and ready for the same kind of operator checkpoint if desired.

Current checkpoint:

- automated-clean active-only coverage: `300 / 570` current SRS-derived source-target families,
- remaining uncovered families: `270`,
- remaining unreviewed generation queue rows after tranche-006 follow-through: `221`,
- next runnable paid request packet: none until the tranche-007 source-target review slice is added,
- next required work: operator checkpoint for tranche-006 if desired, then tranche-007 source-target review.

Do not start another paid run from the post-tranche-006 plan directly.
The tranche-006 pre-spend request packet below is now historical evidence of the
just-completed paid run, not the next packet to spend.

```text
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_006_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_006_en_es_latest.md
```

## What This Runbook Improves

This runbook improves only the repeated generated-data cycle:

- which rows are allowed into the next paid request packet,
- where cost/cardinality guards are checked,
- which artifacts must be produced after a paid call,
- where to stop if something looks wrong,
- when to commit and push.

It does not change:

- the semantic decision algorithm,
- the product-soft `0.015` active-only policy,
- the tranche-005 operator checkpoint or tranche-003 hands-on browser smoke
  result.

## Tranche Loop

Each future tranche has six gates.
Do not skip ahead.

### Gate 1. Source-Target Review

Goal: prevent paid generation for source-target pairs that are not useful visible replacements.

Current review manifest:

```text
docs/test_inputs/semantic_veto_active_only_generation_source_target_review_en_es.json
```

For the next tranche:

1. Start from the latest post-tranche plan:
   `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_006_en_es_latest.md`.
2. Review the next tranche-size block of `source_target_review_status=unreviewed` rows.
3. Append a new `reviewed_slices` entry.
4. Add one decision row per reviewed source-target family.

This has already been completed for tranche-006 and must be repeated for tranche-007 before any more spend:

- reviewed rows: global need ranks `39-88`,
- approved rows: `39`,
- excluded rows: `11`,
- historical request packet:
  `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_006_pre_spend_en_es_latest.md`.

Allowed review outcomes:

- `approve_direct_mapping`
- `approve_narrow_active_mapping`
- `approve_polysemic_active_mapping`
- `exclude_no_visible_replacement`
- `exclude_weak_source_target_mapping`

The review is not a veto-accuracy claim.
It only says whether paying for active cue evidence for that source-target family is sensible.

Commit point:

- commit the reviewed manifest and refreshed no-spend plan before any paid call.

### Gate 2. No-Spend Request Plan

Goal: prove the next paid packet is non-empty, reviewed, deduped, and costable.

Use the current approved combined evidence as coverage input.
For tranche-007, the expected base evidence is:

```text
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-normalized_evidence.json
```

Template:

```bash
python3 scripts/testing/semantic_veto_active_only_full_generation_plan_en_es.py \
  --existing-evidence-json docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-normalized_evidence.json \
  --pilot-id en-es-active-only-full-v1-tranche-007 \
  --request-family-limit 50 \
  --json-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.md \
  --fail-on-review
```

Required before paid execution:

- status is `ok`,
- selected request family count is greater than `0`,
- selected rows are all source-target reviewed and approved,
- selected rows do not overlap current coverage,
- the generated Markdown prints the exact safe live-run command shape,
- pricing is rechecked before live execution and passed explicitly.

Stop if:

- the selected packet is empty,
- any row is unreviewed,
- a large number of rows look linguistically weak,
- estimated cost or selected count differs from the intended tranche.

Commit point:

- commit the no-spend pre-spend packet and review manifest when the packet is ready for approval.

### Gate 3. Paid Generation

Goal: execute only the reviewed request packet, with count and cost guards.

Use the safe command printed by the pre-spend Markdown artifact.
Do not reuse an old tranche command without updating:

- `--request-json`,
- `--run-id`,
- `--max-requests`,
- `--require-selected-request-count`,
- output paths,
- pricing inputs,
- cost ceilings.

Minimum live-run guard shape:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-007-approved \
  --max-requests <selected-request-count> \
  --require-selected-request-count <selected-request-count> \
  --expected-output-tokens 280 \
  --input-rate-per-1m <current-input-rate> \
  --output-rate-per-1m <current-output-rate> \
  --max-estimated-cost-usd <small-tranche-budget> \
  --max-estimated-cost-ceiling-usd <small-tranche-ceiling> \
  --execute-live \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_run_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_run_en_es_latest.md
```

Before any paid call, re-check model prices and choose explicit caps.
The cap should be much higher than the expected mini cost but low enough to catch wrong packets, wrong rates, or wrong model ids.

If a paid run is interrupted:

- rerun with the same `--run-id` and `--resume`,
- do not start a new run id for the same approved packet unless the old journal is explicitly abandoned,
- if paid outputs exist but downstream validation is not complete, commit a recovery checkpoint only if it clearly labels the tranche as incomplete.

Commit point:

- prefer committing after admission and packaging, not immediately after raw generation.
- if interruption risk is high, commit raw paid artifacts as an explicit incomplete recovery checkpoint.

### Gate 4. Admission, Postprocess, And Source Packaging

Goal: convert raw generated responses into canonical active cue evidence without silently accepting bad rows.

Admission:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_admission_en_es.py \
  --generation-requests-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.json \
  --generated-responses-json docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_generated_responses.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_admission_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_admission_en_es_latest.md \
  --fail-on-review
```

Postprocess:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_postprocess_en_es.py \
  --admission-json docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_repaired_generation_admission_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_postprocess_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_postprocess_en_es_latest.md \
  --fail-on-review
```

Source packaging:

```bash
python3 scripts/testing/semantic_veto_active_only_source_packaging_en_es.py \
  --admission docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_repaired_generation_admission_en_es_latest.json \
  --generation-run docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_run_en_es_latest.json \
  --postprocess docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_generation_postprocess_en_es_latest.json \
  --run-id active-only-full-v1-tranche-007 \
  --intake-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-007_intake.json \
  --normalized-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-007_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_source_packaging_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_007_source_packaging_en_es_latest.md \
  --fail-on-review
```

Stop if:

- admission rejects rows without a clear repair plan,
- generated rows leak Spanish target lemmas into source sentences,
- source phrases are missing or fused,
- postprocess raises overlap or leakage concerns,
- packaging excludes unexpected rows.

Commit point:

- commit admission, postprocess, and source packaging together when all are clean.

### Gate 5. Pack Build, Install, And Page Scan

Goal: make the generated rows product-shaped before claiming tranche value.

Build a new combined pack from the previous approved pack plus the new normalized evidence:

```bash
python3 scripts/testing/semantic_veto_active_only_full_pack_builder_en_es.py \
  --base-inventory docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006_semantic_inventory.json \
  --base-normalized-evidence docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-normalized_evidence.json \
  --add-normalized-evidence docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-007_normalized_evidence.json \
  --pack-id en-es-active-only-combined-full-v1-tranche-007 \
  --combined-normalized-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-normalized_evidence.json \
  --semantic-inventory-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007_semantic_inventory.json \
  --json-out docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-007_pack_builder_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-007_pack_builder_latest.md \
  --fail-on-review
```

Install into an isolated fixture root first:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id default \
  --pack-id en-es-active-only-combined-full-v1-tranche-007 \
  --semantic-inventory docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007_semantic_inventory.json \
  --data-root docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root \
  > docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_007_pack_install_en_es_latest.json
```

Run the live-page scan:

```bash
python3 scripts/testing/semantic_veto_active_only_live_page_scan_en_es.py \
  --fixture-root docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root \
  --json-out docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_007_live_page_scan_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_007_live_page_scan_en_es_latest.md \
  --fail-on-review
```

Operator smoke:

- use `docs/rulegen/semantic_pack_operator_smoke_runbook.md`,
- only after the isolated install and page scan are clean,
- the newly built tranche is automated-clean and ready for this smoke after its isolated
  install and page scan pass,
- tranche-003 remains the rollback/latest operator-approved pack until
  a later tranche is tested and accepted.

Commit point:

- commit the combined pack, install smoke artifact, live-page scan, registry update, and docs together.

### Gate 6. Registry And Post-Tranche Plan

Goal: make the new tranche visible as current truth and compute the next empty-or-ready queue state.

After a clean product-shaped tranche, update:

- `docs/test_inputs/semantic_veto_system_registry_en_es.json`,
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`,
- `docs/rulegen/semantic_llm_generation_budget_reference.md` if new cost anchors matter,
- `docs/developer/feature_state_matrix.md` if default behavior, verification evidence, or known gaps changed.

Regenerate registry summary:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue
```

Refresh the post-tranche plan with the new combined evidence:

```bash
python3 scripts/testing/semantic_veto_active_only_full_generation_plan_en_es.py \
  --existing-evidence-json docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-normalized_evidence.json \
  --pilot-id en-es-active-only-full-v1-post-tranche-007 \
  --request-family-limit 50 \
  --json-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_007_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_007_en_es_latest.md \
  --fail-on-review
```

Expected post-tranche behavior:

- if the review manifest was not expanded beyond the completed tranche, the request packet should become empty again,
- the remaining unreviewed queue count should shrink by the reviewed tranche size,
- coverage should increase by the accepted generated families.

Commit point:

- commit and push after the registry summary, post-tranche plan, doc references, state audit, and whitespace checks pass.

## Validation Commands

Run after doc/registry changes:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue
python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

Run focused tests before committing tranche infrastructure or registry changes:

```bash
PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_system_registry_summary.py \
  core/tests/helper/test_semantic_pack_install.py \
  core/tests/architecture/test_extension_structure.py
```

If Python generation/admission scripts change, also run their focused tests or add them before promotion.

## Commit Discipline

Use small commits with clear boundaries:

1. source-target review + no-spend request packet,
2. paid generation + admission + source packaging,
3. combined pack + install/page scan + registry/post-tranche docs.

Push after each clean commit.

Do not include unrelated worktree dirt.
At the time this runbook was written, the known unrelated local file was:

```text
docs/language_pairs/lp_state_and_onboarding_research_2026-05-06.md
```

If a paid run is partially complete and the agent is about to stop, commit only if the checkpoint prevents data loss and clearly says the tranche is incomplete.
Otherwise finish the gate before committing.
