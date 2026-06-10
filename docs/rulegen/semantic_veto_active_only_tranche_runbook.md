# Semantic Veto Active-Only Tranche Runbook

Status: active runbook
Role: Runbook / operational
Last updated: 2026-06-08
Last verified: 2026-06-08 against tranche-001/tranche-011 artifacts, the post-tranche-011 coverage plan, tranche-011 operator checkpoint, SPALEX-only 10k bridge and generation plan, active-only generation planner, live generation runner, admission gate, source packaging, pack builder, semantic-pack installer, live-page scanner, registry summary, cost reference, split-inline DOM semantic-context runtime fix, optimized semantic batching, and tranche-003 hands-on browser-extension smoke
Purpose: make future active-only semantic-veto data tranches repeatable, guarded, and easy to checkpoint without reopening algorithm research
Source-of-truth: operational runbook only; current implementation truth lives in the scripts and generated artifacts named below
Related docs:
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/rulegen/semantic_veto_denominator_current_state.md`
- `docs/rulegen/semantic_llm_generation_budget_reference.md`
- `docs/rulegen/semantic_pack_operator_smoke_runbook.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/developer/post_veto_productization_and_repo_posture_plan.md`

## Current State

The latest automated-clean soft-assist pack is:

```text
en-es-active-only-combined-full-v1-tranche-011
```

The latest operator-accepted product checkpoint is tranche-011. That acceptance
is based on the tranche-011 automated follow-through summary; the latest
hands-on browser-extension smoke remains tranche-003. Tranche-010 is now
historical automated-clean evidence, and tranche-005 is historical
operator-accepted checkpoint evidence.

Current checkpoint:

- automated-clean active-only coverage: `455 / 570` current SRS-derived source-target families,
- current SRS learner-target universe: `1,984` Spanish target lemmas under the
  installed frequency/source resources,
- remaining uncovered families: `115`,
- remaining active-only generation queue rows: `0`,
- remaining uncovered rows are excluded from active-only generation by source-target review,
- next required work: cleanup and denominator discussion; do not run more active-only generation unless the SRS denominator or source-target review policy changes.

Do not start another paid run from the post-tranche-011 plan directly.
The tranche-006 through tranche-011 pre-spend request packets below are
historical evidence of completed paid runs. A future pre-spend packet does not
exist unless source-target review or the SRS denominator is expanded again.

The SRS denominator has now been expanded in a separate clean-source planning
lane using `freq-es-spalex-v1`. That does not discard tranche-011. The full
tranche-011 evidence remains the current operator-accepted semantic reference
checkpoint, with `922` normalized evidence rows and `455` active family keys.
The SPALEX-only 10k bridge should be used only for future expansion queueing:
review source-target rows from
`docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_only_10k_latest.json`,
then run a new SPALEX-only tranche. Do not use the old post-tranche-011 empty
queue as evidence that SPALEX-only coverage is complete.

```text
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_006_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_006_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_007_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_008_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_008_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_009_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_009_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_010_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_010_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_011_en_es_latest.md
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
- the tranche-011 operator checkpoint or tranche-003 hands-on browser smoke
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

For a future tranche, only after the denominator or review policy changes:

1. Start from the latest post-tranche plan:
   `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_011_en_es_latest.md`.
2. Review the next tranche-size block of `source_target_review_status=unreviewed` rows.
3. Append a new `reviewed_slices` entry.
4. Add one decision row per reviewed source-target family.

This has already been completed for tranche-011; there are no still-unreviewed active-only generation queue rows under the current denominator.
The latest completed review slice was:

- reviewed rows: global need ranks `104-124`,
- approved rows: `9`,
- excluded rows: `12`,
- current request packet:
  `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.md`.

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
For the latest completed tranche-011 run, the base evidence was:

```text
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-010-normalized_evidence.json
```

Template:

```bash
python3 scripts/testing/semantic_veto_active_only_full_generation_plan_en_es.py \
  --existing-evidence-json docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-010-normalized_evidence.json \
  --pilot-id en-es-active-only-full-v1-tranche-011 \
  --request-family-limit 50 \
  --json-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.md \
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

Completed tranche-007 pre-spend result:

- status: `ok`,
- selected request families: `38`,
- expected active cue rows: `76`,
- estimated input tokens: `20,811`,
- output-token budget: `10,640`,
- review status over uncovered rows: `approved:38, excluded:61, unreviewed:171`.

Completed tranche-008 pre-spend result:

- status: `ok`,
- selected request families: `40`,
- expected active cue rows: `80`,
- estimated input tokens: `21,892`,
- output-token budget: `11,200`,
- review status over uncovered rows: `approved:40, excluded:71, unreviewed:121`.

Completed tranche-009 pre-spend result:

- status: `ok`,
- selected request families: `38`,
- expected active cue rows: `76`,
- estimated input tokens: `21,928`,
- output-token budget: `10,640`,
- review status over uncovered rows: `approved:38, excluded:83, unreviewed:71`.

Completed tranche-010 pre-spend result:

- status: `ok`,
- selected request families: `30`,
- expected active cue rows: `60`,
- estimated input tokens: `17,431`,
- output-token budget: `8,400`,
- review status over uncovered rows: `approved:30, excluded:103, unreviewed:21`.

Completed tranche-011 pre-spend result:

- status: `ok`,
- selected request families: `9`,
- expected active cue rows: `18`,
- estimated input tokens: `5,304`,
- output-token budget: `2,520`,
- review status over uncovered rows: `approved:9, excluded:115`.

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
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-011-approved \
  --max-requests <selected-request-count> \
  --require-selected-request-count <selected-request-count> \
  --expected-output-tokens 280 \
  --input-rate-per-1m <current-input-rate> \
  --output-rate-per-1m <current-output-rate> \
  --max-estimated-cost-usd <small-tranche-budget> \
  --max-estimated-cost-ceiling-usd <small-tranche-ceiling> \
  --execute-live \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_run_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_run_en_es_latest.md
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
  --generation-requests-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_011_pre_spend_en_es_latest.json \
  --generated-responses-json docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-011-approved_generated_responses.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_admission_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_admission_en_es_latest.md \
  --fail-on-review
```

Postprocess:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_postprocess_en_es.py \
  --admission-json docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_admission_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_postprocess_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_postprocess_en_es_latest.md \
  --fail-on-review
```

If admission requires a repaired admission artifact, use that repaired artifact
for both postprocess and source packaging. Do not mix repaired and unrepaired
admission files within the same tranche.

Source packaging:

```bash
python3 scripts/testing/semantic_veto_active_only_source_packaging_en_es.py \
  --admission docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_admission_en_es_latest.json \
  --generation-run docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_run_en_es_latest.json \
  --postprocess docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_generation_postprocess_en_es_latest.json \
  --run-id active-only-full-v1-tranche-011 \
  --intake-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-011_intake.json \
  --normalized-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-011_normalized_evidence.json \
  --json-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_source_packaging_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_v1_tranche_011_source_packaging_en_es_latest.md \
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
  --base-inventory docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-010_semantic_inventory.json \
  --base-normalized-evidence docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-010-normalized_evidence.json \
  --add-normalized-evidence docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-full-v1-tranche-011_normalized_evidence.json \
  --pack-id en-es-active-only-combined-full-v1-tranche-011 \
  --combined-normalized-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-normalized_evidence.json \
  --semantic-inventory-out docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011_semantic_inventory.json \
  --json-out docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-011_pack_builder_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-011_pack_builder_latest.md \
  --fail-on-review
```

Install into an isolated fixture root first:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id default \
  --pack-id en-es-active-only-combined-full-v1-tranche-011 \
  --semantic-inventory docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011_semantic_inventory.json \
  --data-root docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root \
  > docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_pack_install_en_es_latest.json
```

Run the live-page scan:

```bash
python3 scripts/testing/semantic_veto_active_only_live_page_scan_en_es.py \
  --fixture-root docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root \
  --json-out docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_live_page_scan_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_live_page_scan_en_es_latest.md \
  --fail-on-review
```

Completed tranche-007 follow-through:

- raw generation ended `partial`: `37/38` accepted responses, `74` accepted
  generated items, `1` repeated metadata-drift invalid output for
  `storm -> tempestad`, `0` API errors, and `20,068` input / `7,120` output
  tokens in the latest run report,
- the journal-inclusive paid outcomes were `41` request attempts, `37`
  accepted outcomes, `4` invalid-output outcomes, `21,616` input tokens,
  `7,638` output tokens, and about `$0.051` at the 2026-05-14
  `gpt-5.4-mini` standard rates,
- the repaired generated-response bundle applies two explicit operator
  repairs: restored `storm -> tempestad` metadata and changed one
  `invoke -> llamar` sentence from `invoked` to exact runtime token `invoke`,
- repaired admission accepted `76/76` active items across `38/38` expected
  responses with `0` rejects and `0` coverage shortfall,
- source packaging produced `76` canonical `anchor_cue` rows across `38`
  families with `0` exclusions,
- the combined pack now has `688` normalized evidence rows across `338`
  families, with `338` triggers, `380` senses, and `338` competition sets,
- isolated install wrote `338` helper rules with `315` active-only and `23`
  shadowed/mixed competition sets,
- live public-page scan over the installed fixture produced `120` policy
  decisions, `68` replaces, `52` abstains, `0` fallback decisions, and `0`
  page fetch errors.
- operator accepted tranche-011 as the current product checkpoint from this
  automated follow-through evidence. This did not repeat the hands-on
  browser-extension smoke flow; tranche-003 remains the latest hands-on smoke.

Completed tranche-008 follow-through:

- live generation accepted `40/40` responses after guarded retries for `2`
  metadata-drift outputs, with `80` accepted generated items, `0` API errors,
  `21,293` input tokens, and `7,613` output tokens,
- admission accepted `80/80` active items across `40/40` expected responses
  with `0` rejects and `0` coverage shortfall after the guard was corrected for
  exact source-target cognates such as `ballet -> ballet`,
- source packaging produced `80` canonical `anchor_cue` rows across `40`
  families with `0` exclusions,
- the combined pack now has `768` normalized evidence rows across `378`
  families, with `378` triggers, `420` senses, and `378` competition sets,
- isolated install wrote `378` helper rules with `355` active-only and `23`
  shadowed/mixed competition sets,
- live public-page scan over the installed fixture produced `120` policy
  decisions, `68` replaces, `52` abstains, `0` fallback decisions, and `0`
  page fetch errors.

Completed tranche-009 follow-through:

- live generation accepted `37/38` raw responses; the remaining
  `perchance -> quizás` response repeatedly drifted one hash character in the
  metadata while producing usable sentences, so a repaired generated-response
  artifact restored the reviewed request/family/slot ids without changing
  sentence content,
- repaired admission accepted `76/76` active items across `38/38` expected
  responses with `0` rejects and `0` coverage shortfall,
- source packaging produced `76` canonical `anchor_cue` rows across `38`
  families with `0` exclusions,
- the combined pack now has `844` normalized evidence rows across `416`
  families, with `416` triggers, `458` senses, and `416` competition sets,
- isolated install wrote `416` helper rules with `393` active-only and `23`
  shadowed/mixed competition sets,
- live public-page scan over the installed fixture produced `120` policy
  decisions, `68` replaces, `52` abstains, `0` fallback decisions, and `0`
  page fetch errors.

Completed tranche-010 follow-through:

- live generation accepted `30/30` responses with `0` invalid outputs,
- admission accepted `60/60` active items across `30/30` expected responses
  with `0` rejects and `0` coverage shortfall,
- source packaging produced `60` canonical `anchor_cue` rows across `30`
  families with `0` exclusions,
- the combined pack now has `904` normalized evidence rows across `446`
  families, with `446` triggers, `488` senses, and `446` competition sets,
- isolated install wrote `446` helper rules with `423` active-only and `23`
  shadowed/mixed competition sets,
- live public-page scan over the installed fixture produced `120` policy
  decisions, `68` replaces, `52` abstains, `0` fallback decisions, and `0`
  page fetch errors.

Completed tranche-011 follow-through:

- live generation accepted `9/9` responses with `0` invalid outputs,
- admission accepted `18/18` active items across `9/9` expected responses with
  `0` rejects and `0` coverage shortfall,
- source packaging produced `18` canonical `anchor_cue` rows across `9`
  families with `0` exclusions,
- the combined pack now has `922` normalized evidence rows across `455`
  families, with `455` triggers, `497` senses, and `455` competition sets,
- isolated install wrote `455` helper rules with `432` active-only and `23`
  shadowed/mixed competition sets,
- live public-page scan over the installed fixture produced `120` policy
  decisions, `68` replaces, `52` abstains, `0` fallback decisions, and `0`
  page fetch errors.

Operator smoke:

- use `docs/rulegen/semantic_pack_operator_smoke_runbook.md`,
- only after the isolated install and page scan are clean,
- the newly built tranche is automated-clean and ready for this smoke after its isolated
  install and page scan pass,
- tranche-011 is now the latest operator-accepted product checkpoint,
- tranche-003 remains the latest hands-on browser-extension smoke.

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
  --existing-evidence-json docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-normalized_evidence.json \
  --pilot-id en-es-active-only-full-v1-post-tranche-011 \
  --request-family-limit 50 \
  --json-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_011_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_011_en_es_latest.md \
  --fail-on-review
```

Expected post-tranche behavior:

- if the review manifest was not expanded beyond the completed tranche, the request packet should become empty again,
- the remaining unreviewed queue count should shrink by the reviewed tranche size,
- coverage should increase by the accepted generated families.

Current actual post-tranche-011 state:

- status is `ok`,
- covered families are `455 / 570`, or `79.8%`,
- remaining uncovered families are `115`,
- remaining active-only generation queue rows are `0` after `115` cumulative
  exclusions,
- selected request count is `0`,
- expected generated rows for all currently queued families are `0`.

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
