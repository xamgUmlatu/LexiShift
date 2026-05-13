# Semantic LLM Generation Queueing Plan

Status: active plan
Role: Planning / pre-scan framing
Purpose: define what semantic-routing data should eventually be generated with LLM support, which units deserve queueing, what can be inferred automatically versus what remains hypothesis, and how to avoid redundant generation work
Last updated: 2026-05-12
Last verified: 2026-05-14 active-only prompt-variant bakeoff, generated-evidence admission, postprocess scoring over the frozen 24-family PoC denominator, the product-scope band-grading v1 active-only reuse tranche, the active-only scale tranche through combined 49-family packaging, inventory replay, helper runtime smoke, live-page scan, named-pack installer smoke, initial browser review with the product-soft `min_active_score=0.015` active-only policy, the no-spend full active-only generation denominator plan over the current 570-family installed SRS source-target universe, first-tranche pre-spend source-target review, first paid full active-only tranche generation/admission/source packaging, combined 91-family pack build, named-pack install smoke, live-page scan, post-tranche coverage plan, tranche-002 pre-spend source-target review/request plan, tranche-002 paid generation/admission/source packaging, combined 135-family pack build, named-pack install smoke, live-page scan, post-tranche-002 coverage plan, tranche-003 pre-spend source-target review/request plan, tranche-003 paid generation/admission/source packaging, combined 178-family pack build, named-pack install smoke, live-page scan, post-tranche-003 coverage plan, split-inline DOM semantic-context runtime fix, optimized semantic batching, tranche-003 hands-on browser-extension smoke, tranche-004 pre-spend source-target review/request plan, tranche-004 paid generation/repaired admission/source packaging, combined 224-family pack build, named-pack install smoke, live-page scan, post-tranche-004 coverage plan, tranche-005 pre-spend source-target review/request plan, tranche-005 paid generation/repaired admission/source packaging, combined 261-family pack build, named-pack install smoke, live-page scan, post-tranche-005 coverage plan, tranche-005 operator product checkpoint, tranche-006 pre-spend source-target review/request plan, tranche-006 paid generation/admission/source packaging, combined 300-family pack build, named-pack install smoke, live-page scan, post-tranche-006 coverage plan, and tranche-007 pre-spend source-target review/request plan
Source-of-truth: planning doc only; current implemented truth still lives in the semantic-routing contracts, inventory publication code, and offline evidence normalization seam
Related docs:
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
- `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_feedback_promotion_flow.md`
- `docs/rulegen/semantic_llm_generation_budget_reference.md`
- `docs/rulegen/semantic_veto_active_only_tranche_runbook.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`
- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`

## Why this exists

The next obvious question is not:

- "what should the prompt be?"

The next obvious question is:

- "which semantic problems are actually worth generating data for?"

That question is not trivial.

If LexiShift asks an LLM for semantic data indiscriminately, it will:

- waste budget on families that are already safe,
- waste budget on phrase/parsing failures that are not data problems,
- generate duplicate rows for the same underlying ambiguity family,
- and make later evaluation harder because the queueing logic itself was not explicit.

This document exists to prevent that.

## Core framing

The generation queue should not be built at the level of:

- raw emitted rule rows,
- target lemmas in isolation,
- or "all polysemous words."

The correct unit is a semantic competition family.

Current practical family identity:

- `pair`
- `normalized trigger`
- `active target`

Preferred future family identity once active sense linking is stronger:

- `pair`
- `trigger_id`
- `active_sense_id`
- `competition_set_id`

In other words:

- `pelota` is not the unit
- `ball -> pelota` is closer
- `en-es / trigger=ball / active sense=pelota(ball-object)` is the real unit

That matches the current semantic-routing architecture more closely than a word list does.

## Current productization boundary

As of 2026-05-09, the current candidate is:

- `v5_refresh_control` prompt wording
- active-only generated evidence
- `no_high_eval_overlap_sentence_only` postprocess view
- soft-assist product posture, not a zero-harmful semantic gate

The current evidence is promising but not runtime-published:

- 48 active evidence items admitted across 24 PoC families
- 0 generated-item rejects and 0 coverage shortfall
- score-contribution denominator: 91 frozen repaired-full cases
- selected postprocess view packaged 45 canonical `anchor_cue` rows
- 3 high-eval-overlap rows were excluded before packaging
- inventory-shaped replay applied all 45 rows across 24 families and 91 cases
- decision accuracy improved from 50.5% to 73.6%
- replace recall improved from 8.3% to 50.0%
- false abstains dropped from 44 to 24
- harmful replacements dropped from 1 to 0
- isolated helper runtime smoke wrote a generation-aligned ruleset, snapshot,
  semantic inventory, and publication manifest under a fixture data root
- helper semantic_admit_batch produced 91 policy decisions and 0 fallback
  decisions using the browser-style auto-selected `en_es_sentence_veto_v2`
  policy for active-only inventories
- helper-smoke decision accuracy was 76.9%, replace recall was 58.3%, false
  abstains were 20, and harmful replacements were 1
- live online-page scan produced 113 manually reviewable real-page sentence
  decisions across 17 public pages, with 0 page fetch errors and 0 fallback
  decisions

The next engineering step is manual helper/browser testing from the isolated
fixture, not another prompt rewrite and not more paid generation. The generated
rows are now canonical source evidence and have passed both inventory-shaped
replay and real helper semantic-admission smoke. They are still not published
into real user profile data.

As of 2026-05-10, the next no-spend reuse tranche has also been carried through
the same path:

- `product_scope_band_grading_v1` contributed 36 already generated active items
  across 18 families,
- postprocess selected the `no_high_eval_overlap_sentence_only` view,
- source packaging produced 35 tranche-specific `anchor_cue` rows and excluded
  1 high-overlap row,
- inventory-shaped replay applied 35/35 rows, improved decision accuracy from
  47.1% to 68.6%, improved replace recall from 0.0% to 41.7%, reduced false
  abstains from 36 to 21, and did not increase harmful replacements under the
  replay policy,
- isolated helper runtime smoke covered 70 cases with 70 policy decisions, 0
  fallback decisions, 67.1% decision accuracy, 44.4% replace recall, 3 harmful
  replacements, and 20 false abstains,
- live public-page scan produced 63 manual-review rows across 17 pages with 13
  replace and 50 abstain decisions.

This confirms the ramping posture: use active-only generation in additive
tranches, preserve tranche provenance in source ids and row ids, and require
admission, postprocess, packaging, replay, helper smoke, and page-feel review
before increasing spend. Shadow generation remains paused for scale because the
stronger-model shadow probe improved admissibility but did not improve fixed
veto scoring.

As of the later 2026-05-10 paid scale tranche, the active-only path has also
completed coverage of the current 49-family repaired product-scope denominator:

- the active-only scale request renderer selected the 16 remaining uncovered
  families after excluding 33 families already covered by packaged active
  evidence,
- the live mini run produced 16 active responses and 32 generated active items
  after one resume retry,
- one follow-up response was used for `continue -> durar` after the initial
  admitted response contained an inflected `continues` item; the repaired
  generated-response artifact corrects only request-id metadata from the repair
  response and keeps generated sentences unchanged,
- admission accepted 32/32 active items with 0 rejected items and 0 coverage
  shortfall,
- source packaging produced 32 new canonical `anchor_cue` rows across 16
  families with 0 exclusions under `no_high_eval_overlap_sentence_only`,
- combining the PoC, v1 reuse, and scale-tranche normalized evidence produced
  112 rows over 49 families,
- the combined inventory replay on 189 repaired-full cases improved decision
  accuracy from 50.3% to 72.0%, replace recall from 5.1% to 46.9%, and false
  abstains from 93 to 52, with harmful replacements unchanged at 1,
- the combined helper runtime smoke produced 189 policy decisions, 0 fallback
  decisions, 72.5% decision accuracy, 49.0% replace recall, 2 harmful
  replacements, and 50 false abstains,
- the combined live-page scan produced 120 manual-review rows from 16 fetched
  public pages, with 25 replace and 95 abstain decisions.

This is the current best manual-testing fixture. The remaining product question
is no longer whether active cue generation can materially move the curve; it can.
Initial browser review of the combined fixture found the lower-abstain
`min_active_score=0.015` active-only policy acceptable as a soft-assist smoke.
That is not a language-wide `en-es` generation result. It only proves that the
current active-only data path can be generated, admitted, packaged, installed,
and felt in a real browser on a bounded pack.

Current boundary artifact:

- `docs/test_outputs/semantic_veto_productization_readiness_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_inventory_replay_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_helper_runtime_smoke_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_inventory_replay_en_es_latest.md`
- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_helper_runtime_smoke_en_es_latest.md`
- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_inventory_replay_en_es_latest.md`
- `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-normalized_evidence.json`
- `docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_inventory_replay_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_helper_runtime_smoke_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_generation_run_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_repaired_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-001_pack_builder_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_001_pack_install_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_001_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_001_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_002_pre_spend_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_002_generation_run_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_002_repaired_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_002_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-002_pack_builder_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_002_pack_install_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_002_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_002_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_003_pre_spend_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_003_generation_run_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_003_repaired_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_003_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-003_pack_builder_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_003_pack_install_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_003_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_003_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_004_pre_spend_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_004_generation_run_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_004_repaired_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_004_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-004_pack_builder_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_004_pack_install_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_004_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_004_en_es_latest.md`

## Full `en-es` generation boundary

The entire `en-es` semantic-veto data set has not been generated.

The completed pack is:

- active-only cue evidence,
- 112 canonical evidence rows,
- 49 repaired product-scope families,
- no generated phrase/no-winner controls,
- no broad generated shadow/competitor coverage,
- and no cloud-hosted distribution path.

For product scale, "full `en-es`" should not mean every English dictionary word.
It should mean the SRS-admissible `en-es` semantic-family universe that can
actually surface during browsing:

- a trigger/source phrase the browser can match,
- a target the learner can actually have active through SRS/rulegen,
- an active semantic inventory row worth serving,
- and, only where useful, shadow/competitor rows that block clearly wrong
  replacements.

As of 2026-05-12, steps 2 and 3 have an explicit no-spend denominator plan:

- current installed full SRS-admissible target universe: 1,984 unique Spanish
  targets from 2,000 SRS seed rows,
- current generated rule source-target denominator: 570 source-target families
  from 536 unique English source triggers and 342 unique Spanish targets,
- current combined active-only semantic pack coverage: 49 of those 570
  source-target families, or 8.6%,
- remaining active-only coverage gap: 521 source-target families,
- first pre-spend source-target review covers the top 50 exposure-first rows,
  approves 42, rejects 8, and leaves 471 later uncovered rows unreviewed,
- planned active-only generation volume after known first-tranche rejections:
  1,026 generated active cue rows if every currently queued family is attempted,
- conservative first runnable request packet: 42 approved families / 84 expected
  active rows / 21,898 estimated input tokens / 11,760 output-token budget,
- current no-spend mini safety estimate for that packet:
  approximately `$0.070` expected / `$0.149` max-output ceiling using the
  2026-05-12 official `gpt-5.4-mini` standard rates,
- full active-only queue shape after known rejections: 11 resumable queue
  tranches, with future tranche rows still requiring the same pre-spend
  source-target review.

The current plan artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.md`

The first paid tranche has now been executed against that reviewed request
packet:

- live `gpt-5.4-mini` generation accepted `42/42` active-only responses,
- one generated item used the inflected token `works`; a one-request repair was
  run, then the repaired response bundle explicitly replaced that one response,
- repaired admission accepted `84/84` active items with `0` rejects and `0`
  coverage shortfall,
- source packaging produced `84` canonical `anchor_cue` rows across `42`
  families with `0` exclusions under `no_high_eval_overlap_sentence_only`,
- the accepted main run used `20,992` input tokens and `7,411` output tokens,
  about `$0.049` at the 2026-05-12 `gpt-5.4-mini` standard rates; the one
  request repair adds a negligible additional amount,
- the combined active-only pack now has `194` normalized evidence rows across
  `91` families after deduping two duplicate rows from the prior product-scope
  pack,
- the combined semantic inventory has `91` triggers, `133` senses, and `91`
  competition sets,
- the isolated named-pack install wrote `91` helper rules, `68` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 91-rule fixture produced `80`
  policy decisions, `0` fallback decisions, `51` replace decisions, `29`
  abstain decisions, and `0` page fetch errors.

The post-tranche coverage artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_001_en_es_latest.md`

Post-tranche state:

- current active-only coverage is `91/570` families, or `16.0%`,
- remaining uncovered active-only families are `479`,
- the remaining generation queue has `471` unreviewed source-target rows after
  excluding the `8` rows rejected in the first source-target review,
- the next runnable paid request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

The next pre-spend review slice has now been prepared without making paid
model calls:

- the cumulative source-target review manifest covers `100` reviewed rows:
  the original first `50` plus the first `50` still-unreviewed rows after
  tranche-001 coverage/exclusion,
- tranche-002 prep approves `44` of those next `50` rows and excludes `6`
  weak or no-visible-replacement mappings,
- the refreshed tranche-002 request plan is `ok` and selects only those `44`
  approved rows,
- the planned paid tranche would request `88` active cue items, with `23,006`
  estimated input tokens and `12,320` output-token budget,
- `421` remaining uncovered rows are still unreviewed after this prep slice.

The tranche-002 prep artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_002_pre_spend_en_es_latest.md`

That changed the engineering gate from source-target review to a bounded paid
run: the tranche-002 request packet was ready as a reviewed no-spend artifact,
and the only acceptable spend path was the 44-request tranche with explicit
spend/count guards plus the same admission, packaging, install, and page-scan
validation used for tranche 001.

The second paid tranche has now been executed against that reviewed request
packet:

- live `gpt-5.4-mini` generation accepted `42/44` responses on the first
  completed bundle; the two invalid outputs were structural metadata mistakes
  where the model changed request ids, not missing sentence content,
- one guarded retry reproduced the same two metadata mistakes, so the final
  admitted response bundle explicitly repaired only request/family/slot metadata
  for `maybe -> quizás` and `tax -> imponer`; sentence content was not changed,
- repaired admission accepted `88/88` active items with `0` rejects and `0`
  coverage shortfall,
- source packaging produced `88` canonical `anchor_cue` rows across `44`
  families with `0` exclusions under `no_high_eval_overlap_sentence_only`,
- the journal-inclusive paid outcomes were `23,080` input tokens and `8,297`
  output tokens, about `$0.055` at the 2026-05-12 `gpt-5.4-mini` standard
  rates,
- the combined active-only pack now has `282` normalized evidence rows across
  `135` families,
- the combined semantic inventory has `135` triggers, `177` senses, and `135`
  competition sets,
- the isolated named-pack install wrote `135` helper rules, `112` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 135-rule fixture produced `120`
  policy decisions, `0` fallback decisions, `69` replace decisions, `51`
  abstain decisions, and `0` page fetch errors.

The post-tranche-002 coverage artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_002_en_es_latest.md`

Post-tranche-002 state:

- current active-only coverage is `135/570` families, or `23.7%`,
- remaining uncovered active-only families are `435`,
- the remaining generation queue has `421` unreviewed source-target rows after
  excluding the `14` cumulative rejected rows,
- the post-tranche-002 request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

The tranche-003 pre-spend review slice has now been prepared without making
paid model calls:

- the cumulative source-target review manifest covers `150` reviewed rows,
- tranche-003 prep reviewed the first `50` still-unreviewed rows after
  tranche-002 coverage/exclusion, global_need_rank `15-64` in the
  post-tranche-002 queue,
- tranche-003 prep approves `43` of those rows and excludes `7` weak or
  no-visible-replacement mappings,
- the refreshed tranche-003 request plan is `ok` and selects only those `43`
  approved rows,
- the planned paid tranche would request `86` active cue items, with `22,570`
  estimated input tokens and `12,040` output-token budget,
- `371` remaining uncovered rows are still unreviewed after this prep slice.

The tranche-003 prep artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_003_pre_spend_en_es_latest.md`

That changes the current engineering gate from source-target review to a
bounded paid run. The only acceptable spend path is the 43-request tranche with
explicit spend/count guards plus the same admission, postprocess, packaging,
install, and page-scan validation used for tranches 001 and 002.

The third paid tranche has now been executed against that reviewed request
packet:

- live `gpt-5.4-mini` generation accepted `42/43` responses on the first
  completed bundle; the one invalid output was a `horizon -> horizonte`
  metadata typo where the model changed `family_id`,
- one guarded retry accepted the `horizon -> horizonte` response,
- the final generated-response bundle needed one explicit operator exact-token
  repair for `indicate -> mostrar`, replacing two `indicates` sentences with
  exact-token `indicate` sentences,
- repaired admission accepted `86/86` active items with `0` rejects and `0`
  coverage shortfall,
- source packaging produced `86` canonical `anchor_cue` rows across `43`
  families with `0` exclusions under `no_high_eval_overlap_sentence_only`,
- the journal-inclusive paid outcomes were `22,259` input tokens and `8,106`
  output tokens, about `$0.053` at the 2026-05-12 `gpt-5.4-mini` standard
  rates,
- the combined active-only pack now has `368` normalized evidence rows across
  `178` families,
- the combined semantic inventory has `178` triggers, `220` senses, and `178`
  competition sets,
- the isolated named-pack install wrote `178` helper rules, `155` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 178-rule fixture produced `120`
  policy decisions, `0` fallback decisions, `72` replace decisions, `48`
  abstain decisions, and `0` page fetch errors.

The post-tranche-003 coverage artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_003_en_es_latest.md`

Post-tranche-003 state:

- current active-only coverage is `178/570` families, or `31.2%`,
- remaining uncovered active-only families are `392`,
- the remaining generation queue has `371` unreviewed source-target rows after
  excluding the `21` cumulative rejected rows,
- the post-tranche-003 request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

Operator live-smoke result:

- the options-page Advanced debug installer can install the current tranche-003
  pack by default pack id,
- tranche-002 remains a successful earlier smoke on Wikipedia Acceptable
  sources,
- after the split-inline DOM semantic-context fix and batching speedup, a real
  browser-extension smoke of tranche-003 is accepted as successful product-feel
  evidence for the PoC,
- the accepted product posture is soft assist: false abstains and some harmful
  replacements are tolerated, and narrow source-target mappings such as
  `tax -> imponer` are not a blocker for this checkpoint.

The tranche-004 pre-spend review slice has now been prepared without making
paid calls:

- the cumulative source-target review manifest covers `200` reviewed rows,
  with `175` cumulative approvals and `25` cumulative exclusions,
- tranche-004 prep reviewed the first `50` still-unreviewed rows after
  tranche-003 coverage and exclusions, global need ranks `22-71`,
- tranche-004 prep approves `46` of those rows and excludes `4` weak mappings
  (`leader -> amo`, `quote -> mencionar`, `sharp -> justamente`, and
  `soft -> dulce`),
- the refreshed tranche-004 request plan is `ok` and selects only those `46`
  approved families,
- the request packet expects `92` active cue rows, estimates `24,061` input
  tokens, and budgets `12,880` output tokens,
- `321` remaining uncovered rows are still unreviewed after this prep slice.

The tranche-004 prep artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_004_pre_spend_en_es_latest.md`

The fourth paid tranche has now been executed against that reviewed request
packet:

- live `gpt-5.4-mini` generation accepted `46/46` responses with `0` API
  errors and `0` invalid outputs,
- the raw generated content still needed `7` semantic operator repairs where
  the prompt did not give the model enough reviewed source-target sense
  guidance (`jack -> gato`, `knock -> llamar`, `naked -> desnudo`,
  `protest -> protesta`, `quiet -> silencio`, `regulation -> regla`, and
  `taste -> gusto`),
- the active-only planner now carries the source-target review rationale into
  future prompt evidence so later tranches get the reviewed intended-sense note
  directly,
- repaired admission accepted `92/92` active items with `0` rejects and `0`
  coverage shortfall,
- source packaging produced `92` canonical `anchor_cue` rows across `46`
  families with `0` exclusions under `no_high_eval_overlap_sentence_only`,
- the live run used `23,358` input tokens and `8,450` output tokens, about
  `$0.056` at the 2026-05-12 `gpt-5.4-mini` standard rates,
- the combined active-only pack now has `460` normalized evidence rows across
  `224` families,
- the combined semantic inventory has `224` triggers, `266` senses, and `224`
  competition sets,
- the isolated named-pack install wrote `224` helper rules, `201` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 224-rule fixture produced `120`
  policy decisions, `0` fallback decisions, `73` replace decisions, `47`
  abstain decisions, and `0` page fetch errors.

The post-tranche-004 coverage artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_004_en_es_latest.md`

Post-tranche-004 state:

- current active-only coverage is `224/570` families, or `39.3%`,
- remaining uncovered active-only families are `346`,
- the remaining generation queue has `321` unreviewed source-target rows after
  excluding the `25` cumulative rejected rows,
- the post-tranche-004 request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

Tranche-004 is historical automated-clean evidence. Tranche-005 is now the latest
automated-clean pack and the latest operator-accepted product checkpoint.
That acceptance is based on the automated follow-through summary, not a repeated
hands-on browser-extension smoke. Tranche-003 remains the latest formally
recorded hands-on browser-extension smoke.

The tranche-005 pre-spend review slice and paid follow-through have also
completed:

- the cumulative source-target review manifest covers `250` reviewed rows,
  with `212` cumulative approvals and `38` cumulative exclusions,
- tranche-005 prep reviewed the first `50` still-unreviewed rows after
  tranche-004 coverage and exclusions, global need ranks `26-75`,
- tranche-005 prep approved `37` of those rows and excluded `13` weak mappings
  (`workplace -> taller`, `ask -> demandar`, `offer -> pretensión`,
  `show -> designar`, `become -> acontecer`, `front -> frontón`,
  `barn -> puesto`, `centennial -> siglo`, `compartment -> departamento`,
  `dismal -> común`, `beg -> demandar`, `bid -> demandar`, and
  `blank -> formulario`),
- the reviewed tranche-005 request plan selected only those `37` approved
  families, expected `74` active cue rows, estimated `20,540` input tokens, and
  budgeted `10,360` output tokens,
- live `gpt-5.4-mini` generation accepted `37/37` responses after one guarded
  retry for request metadata drift on `commencement -> principio`,
- the final generated-response bundle applied one explicit runtime-token repair
  for `bed -> cauce`, changing a `riverbed` compound into standalone `bed of
  the river`,
- repaired admission accepted `74/74` active items with `0` rejects and `0`
  coverage shortfall,
- source packaging produced `74` canonical `anchor_cue` rows across `37`
  families with `0` exclusions,
- the live run recorded `19,644` input tokens and `6,827` output tokens, about
  `$0.045` at the 2026-05-13 `gpt-5.4-mini` standard rates,
- the combined active-only pack now has `534` normalized evidence rows across
  `261` families,
- the combined semantic inventory has `261` triggers, `303` senses, and `261`
  competition sets,
- the isolated named-pack install wrote `261` helper rules, `238` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 261-rule fixture produced `120`
  policy decisions, `0` fallback decisions, `70` replace decisions, `50`
  abstain decisions, and `0` page fetch errors.

The tranche-005 artifacts are:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_005_pre_spend_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_005_generation_run_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_005_repaired_generation_admission_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_005_source_packaging_en_es_latest.md`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-005_pack_builder_latest.md`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_005_pack_install_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_005_live_page_scan_en_es_latest.md`
- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_005_en_es_latest.md`

Post-tranche-005 state:

- current active-only coverage is `261/570` families, or `45.8%`,
- remaining uncovered active-only families are `309`,
- the remaining generation queue has `271` unreviewed source-target rows after
  excluding the `38` cumulative rejected rows,
- the post-tranche-005 request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

The tranche-005 product checkpoint artifact is:

- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_005_operator_checkpoint_en_es_latest.md`

The tranche-006 pre-spend review slice has now been prepared without making
paid calls:

- the cumulative source-target review manifest covers `300` reviewed rows,
  with `251` cumulative approvals and `49` cumulative exclusions,
- tranche-006 prep reviewed the first `50` still-unreviewed rows after
  tranche-005 coverage and exclusions, global need ranks `39-88`,
- tranche-006 prep approved `39` of those rows and excluded `11` weak mappings
  (`burst -> grieta`, `chase -> cazar`, `copy -> trasladar`,
  `count -> calcular`, `demand -> deducción`, `escort -> acompañamiento`,
  `indicate -> designar`, `nearby -> adyacente`, `proposal -> pretensión`,
  `remove -> abolir`, and `replacement -> suplemento`),
- the refreshed tranche-006 request plan is `ok` and selects only those `39`
  approved families,
- the request packet expects `78` active cue rows, estimates `21,302` input
  tokens, and budgets `10,920` output tokens,
- `221` remaining uncovered rows are still unreviewed after this prep slice.

The tranche-006 prep artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_006_pre_spend_en_es_latest.md`

The sixth paid tranche has now been executed against that reviewed request
packet:

- live `gpt-5.4-mini` generation accepted `39/39` responses after guarded
  retries for `3` metadata-drift outputs (`height -> elevación`,
  `hip -> cadera`, and `reserve -> reservar`),
- admission accepted `78/78` active items with `0` rejects and `0` coverage
  shortfall,
- source packaging produced `78` canonical `anchor_cue` rows across `39`
  families with `0` exclusions under `no_high_eval_overlap_sentence_only`,
- the accepted run recorded `20,628` input tokens and `7,223` output tokens,
  about `$0.048` at the 2026-05-14 `gpt-5.4-mini` standard rates,
- the combined active-only pack now has `612` normalized evidence rows across
  `300` families,
- the combined semantic inventory has `300` triggers, `342` senses, and `300`
  competition sets,
- the isolated named-pack install wrote `300` helper rules, `277` active-only
  competition sets, and `23` shadowed/mixed sets,
- live public-page scan over the installed 300-rule fixture produced `120`
  policy decisions, `0` fallback decisions, `68` replace decisions, `52`
  abstain decisions, and `0` page fetch errors.

The post-tranche-006 coverage artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_post_tranche_006_en_es_latest.md`

Post-tranche-006 state:

- current active-only coverage is `300/570` families, or `52.6%`,
- remaining uncovered active-only families are `270`,
- the remaining generation queue has `221` unreviewed source-target rows after
  excluding the `49` cumulative rejected rows,
- the post-tranche-006 request packet is intentionally empty until the next
  pre-spend source-target review approves more rows.

The tranche-007 pre-spend review slice has now been prepared without making
paid calls:

- the cumulative source-target review manifest covers `350` reviewed rows,
  with `289` cumulative approvals and `61` cumulative exclusions,
- tranche-007 prep reviewed the first `50` still-unreviewed rows after
  tranche-006 coverage and exclusions, global need ranks `50-99`,
- tranche-007 prep approved `38` of those rows and excluded `12` weak mappings
  (`sale -> deducción`, `suggest -> designar`, `transfer -> atravesar`,
  `abstraction -> robo`, `bark -> barco`, `chunk -> bola`,
  `delegate -> diputado`, `junction -> reunión`, `restrain -> gobernar`,
  `utilize -> explotar`, `vocabulary -> diccionario`, and
  `divide -> segregar`),
- the refreshed tranche-007 request plan is `ok` and selects only those `38`
  approved families,
- the request packet expects `76` active cue rows, estimates `20,811` input
  tokens, and budgets `10,640` output tokens,
- `171` remaining uncovered rows are still unreviewed after this prep slice.

The tranche-007 prep artifact is:

- `docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.md`

The scale-generation program should therefore proceed in lanes:

1. Freeze the current `active_only_combined_product_scope_v1` pack as the
   product-smoke control.
2. Keep the SRS-admissible family universe refreshed from current `en-es`
   rulegen/SRS candidate data, with enough metadata to identify already-covered
   families.
3. Render and refresh the no-spend active-only request plan for uncovered
   families in deterministic resumable tranches.
4. Generate active cue evidence first, because this is the only paid data shape
   that has repeatedly admitted cleanly and improved downstream false abstains.
5. Run admission, postprocess, source packaging, product-shaped pack build,
   named-pack install, and live-page sample review after each tranche before
   larger spend. Inventory replay remains useful only when the generated
   families overlap a frozen manual sentence suite.
6. Add generated shadows only for high-need or observed-harm families where
   active-only evidence still allows clearly wrong replacements.
7. Keep phrase/no-winner controls as a separate lane; active cue generation does
   not solve those cases.

The immediate engineering gap is now tranche-006 operator checkpoint if desired,
followed by explicit approval/current pricing for tranche-007 paid generation.
Do not attempt to spend the whole budget at once.

Use `docs/rulegen/semantic_veto_active_only_tranche_runbook.md` for the
repeatable active-only tranche cycle. That runbook owns the step-by-step gates,
commit points, and stop rules for tranche-003 and later; this queueing plan owns
the rationale and current state.

## What "worried about polysemy" should mean

A family is "worried about polysemy" when it is plausible that:

- the runtime trigger can support more than one meaning,
- at least one alternative meaning could map to a different learner-relevant target,
- a wrong replacement would be meaningfully harmful,
- and current non-semantic controls do not already make the family safe enough.

This is not the same as:

- "the English word is polysemous in a dictionary"

Many dictionary-polysemous words do not deserve semantic-routing investment because:

- the trigger is phrase-specific enough,
- the rule is not currently publishable or common enough,
- or the ambiguity does not create a meaningful replacement hazard.

So the queueing question is not:

- "is this word polysemous?"

It is:

- "is this family risky enough, live enough, and data-fixable enough to justify semantic-generation effort?"

## Current intended generated data

The current semantic evidence intake seam supports four row types:

- `shadow_candidate`
- `bridge_candidate`
- `anchor_cue`
- `phrase_control_example`

Interpretation:

- `shadow_candidate`
  - propose another target reading that competes with the active target under the same trigger
- `bridge_candidate`
  - propose a plausible competing target that current lexical mining may miss
- `anchor_cue`
  - propose discriminative evidence text for an already-known active/shadow contrast
- `phrase_control_example`
  - propose or ingest an abstain-side example/frame for phrase, idiom, lexicalized, or otherwise no-replacement uses of the same trigger

Those rows are offline evidence only.
They are not runtime decisions and they are not runtime sidecars.
The current example-frame contract requires active, shadow, and phrase-control rows together before a generated/source batch is promotion-relevant.

## Budget posture

The current intended operating posture is:

- spend one bounded first LLM tranche to see how far veto quality can improve
- preserve every batch as additive source-of-truth evidence
- and keep the repo able to accept later tranches without reworking the pipeline

That means the first budgeted run should be treated as:

- a deliberate pilot slice
- not a one-time monolithic dump
- and not a shortcut to runtime artifacts

The practical implication is:

- queue a limited set of high-value families first
- record which families were attempted and by which batch
- normalize every batch into the canonical evidence layer
- and let later batches add coverage family-by-family

## Why the first tranche must be additive

If the first LLM tranche is handled as a one-off merged blob, later expansion becomes awkward.

The main failure modes would be:

- redundant generation for families that were already attempted
- loss of provenance about which prompt/model fixed which family
- difficult rollback when a later batch is worse
- and inability to compare one budget wave against another

The desired future is simpler:

1. generate for a bounded family queue
2. ingest raw batch rows
3. normalize and dedupe them
4. compile a new generation
5. compare that generation against the previous one
6. keep the new generation only if it is genuinely better

That process only works cleanly if the first tranche already follows it.

## Queueing buckets

The current working buckets are:

- `not_applicable`
- `needs_shadow_data`
- `needs_cue_data`
- `needs_algorithm_fix`
- `needs_phrase_parsing_fix`

These are operating labels.
They are not ground truth claims.

That distinction matters enough to make explicit:

- the system will usually not know the true root cause with certainty
- the system can only infer the most likely explanation from the current evidence

So in practice the desired output of a future queueing pass is not:

- `bucket=needs_shadow_data`

It is:

- `likely_bucket=needs_shadow_data`
- `bucket_confidence=...`
- `bucket_evidence=[...]`

## What can and cannot be known automatically

### What we cannot know with certainty

Without manual review, the system usually cannot prove:

- whether a family truly needs more blocker coverage or just better pruning,
- whether a family is fundamentally a phrase-boundary bug,
- whether the current active sense identity is already slightly wrong,
- or whether a family is simply not worth semantic-routing investment.

That means a fully automatic pass cannot be treated as authoritative diagnosis.

### What we can infer well enough to triage

A future automatic pass can still be useful if it emits:

- a likely bucket,
- a confidence estimate,
- evidence signals,
- and a recommended next action.

This is enough to drive:

- human sampling,
- LLM budget allocation,
- and later ablation work.

The correct posture is:

- automatic triage first
- sampled human review second
- policy refinement third

## Signals for each bucket

These are current working heuristics, not final rules.

### 1. `needs_shadow_data`

Likely when:

- the family is plausibly ambiguous,
- harmful allow risk appears to come from missing competitors,
- and the current competition set is empty or obviously too thin.

Example signal pattern:

- trigger has multiple plausible readings
- current `competition_set` is missing or has no ready `shadow_sense_ids`
- manual or lower-bound shadows substantially improve the family
- runtime scorer quality is not the main bottleneck once blockers are present

Interpretation:

- coverage problem first

### 2. `needs_cue_data`

Likely when:

- the blocker identities are mostly right,
- but runtime still abstains too often or fails to separate active from shadow because the evidence text is weak.

Example signal pattern:

- the competition set exists and looks plausible
- the same shadow identities perform much better with stronger evidence text
- the main weakness is weak active-vs-shadow separation, not missing competitors

Interpretation:

- discrimination problem first

### 3. `needs_algorithm_fix`

Likely when:

- the needed information is already in the pipeline or candidate pool,
- but current filtering, promotion, pruning, or thresholding discards or misuses it.

Example signal pattern:

- good candidates appear in the raw candidate pool but do not survive promotion
- small policy-node changes recover the family without new source data
- the family looks data-rich but decision-poor

Interpretation:

- logic problem first

### 4. `needs_phrase_parsing_fix`

Likely when:

- the family is not primarily about sense competition,
- but about broken phrase retention, MWE leakage, or malformed trigger extraction.

Example signal pattern:

- phrasal forms collapse into bare tokens
- POS alignment becomes implausible in a way that suggests bad span identity
- the wrong text span is being admitted into semantic routing

Interpretation:

- parse or surface-form problem first

### 5. `not_applicable`

Likely when:

- the family does not create enough semantic hazard to justify queueing,
- or existing controls already make it safe enough.

Example signal pattern:

- ambiguity is narrow or harmless
- phrase specificity already protects the family
- semantic routing adds little practical value even if the word is dictionary-polysemous

Interpretation:

- do not spend queue budget here yet

## Reuse rules

The queue should be optimized for reuse from the start.

Do not generate separately for every emitted rule row when the same semantic family repeats.

### Shadow proposal reuse

Generate once per family:

- `pair`
- `normalized trigger`
- `active target`

or later:

- `pair`
- `trigger_id`
- `active_sense_id`

The same result should then feed every emitted rule that points to that family.

### Cue reuse

Cue generation should usually be keyed more narrowly:

- `pair`
- `active sense`
- `shadow sense`

That is because cue text is about distinguishing one specific contrast, not about expanding the whole family.

### Sense-hint reuse

Any future sense hints or reviewed locators should be reusable across families whenever:

- the same target sense appears in multiple trigger families

### Publication reuse

Even if helper materialization stays profile-local, semantic-generation work should aim toward:

- pair-global semantic core
- profile-local overlay only where needed

That remains the best way to avoid redundant cloud or local artifact churn later.

## Family inventory and queue state

To support later add-on waves, the repo needs explicit family-level queue state.

Without that state, later LLM work would keep re-answering questions the repo has already asked.

Current first concrete artifact:

- `docs/test_inputs/semantic_routing/semantic_family_inventory_en_es_v10.json`
- `docs/test_outputs/semantic_llm_queue_review_en_es_latest.md`
- `docs/test_outputs/semantic_example_sentence_bank_pilot_en_es_latest.md`

Current posture from that first artifact:

- current first-tranche queue is cue-heavy, not shadow-heavy
- current routed primary targets are `check`, `order`, `trip`, and `report`
- current calibration families are `plant` and `drink`
- current negative controls are `play` and `watch`
- current `needs_shadow_data` tranche count is `0`
- current installed packs expose no queued-family example rows on that frozen slice:
  - `0 / 6` target families are example-ready for `example_sentence_bank`
  - `6 / 6` target families do expose reverse-side auxiliary sense text
- the new reverse-aux-text pilot now resolves that remaining cheap-control choice:
  - `reverse_aux_plus_all_evidence` is the best non-LLM queue-slice control
  - it improves the frozen prompt-slice point read without widening the current harmful count
  - so prompt spend can now proceed with one explicit non-LLM reference row rather than an unresolved source question
- the new downstream bakeoff on the accepted `gpt-5.4` cue tranche now sharpens the generation decision too:
  - the safe additive LLM lane (`llm_cue_plus_all_evidence`) is flat on both the hard reference and the active-sense overlay
  - it only swaps `drink:002` for `drink:001`, so it is not yet better than the existing baseline
  - the stronger LLM cue insertions (`llm_cue_plus_sense_label`, `llm_cue_plus_gloss`) do move recall, but only by widening harmful replace
  - so the current routed conclusion is not "scale cue generation now"
  - it is "keep the queue fixed, keep reverse-aux as the current control, and redesign the next cue prompt around stronger overlap-bearing discriminators before larger spend"
- that redesign is now prepared as a bounded no-spend challenger matrix rather than a vague idea:
  - now also exercised once on a real cheap proxy batch and once on the target model for the overlap challenger slots
  - `semantic_prompt_bakeoff_v3`
  - `4` active cue slots and `12` proxy requests on the same frozen queue
  - incumbents:
    - `cue_contrastive_general_v1`
    - `cue_cross_pos_frame_v1`
  - challengers:
    - `cue_contrastive_overlap_v1`
    - `cue_cross_pos_overlap_v1`
  - current target/downstream result is negative for promotion:
    - the narrowed target pass accepted and normalized `6 / 6` overlap requests
    - the safe additive downstream lane still stays flat on false abstain and worsens the hard-lane harmful count
    - `reverse_aux_plus_all_evidence` remains better than the LLM cue rows on the frozen queue slice
  - the preserved failure diagnostic now explains the failure mode:
    - `scripts/testing/semantic_llm_prompt_failure_diagnostic_en_es.py`
    - `docs/test_outputs/semantic_llm_prompt_failure_diagnostic_latest.md`
    - reverse-aux works best when both active and shadow senses receive source-side auxiliary evidence
    - active-only cue additions are unsafe or inert
    - LLM cues add no value on top of the current reverse-aux evidence surface
  - next spend decision is therefore "stop", not "scale":
    - keep both accepted target cue tranches analysis-only
    - do not broaden cue-generation spend from the current prompt matrix
    - only re-enter paid generation after a source-data, insertion-strategy, or evaluation-lane change gives a concrete path past the reverse-aux control

Minimum family inventory responsibilities:

- remember which family has already been queued
- remember whether the family received shadow generation, cue generation, or both
- remember which `batch_id` attempted the family
- remember whether the family still looks unresolved
- remember whether the current best diagnosis is data-related or non-data-related

Minimum family inventory fields:

- `family_id`
- `pair`
- `trigger`
- `normalized_trigger`
- `active_target`
- `active_sense_hint`
- `queue_status`
- `attempted_generation_kinds`
- `last_attempt_batch_id`
- `last_attempted_at`
- `resolved_status`
- `likely_bucket`
- `bucket_confidence`
- `recommended_action`

This inventory is not optional if the goal is:

- spend a bounded amount now and add more later without redundant regeneration

It is the memory layer for the generation queue.

Current planning anchor:

- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

## Future user-feedback role

Future user feedback is realistic, but it should enter the system as weak evidence rather than direct truth.

The safest first interpretation is:

- raw user feedback should be captured at the per-event and per-rule level
- durable fixes will usually be promoted at the family or competition-set level
- and promotion into shared semantic truth should remain review-gated

That means the future system should preserve both:

- exact firing context for the reported rule event
- the broader semantic family that event belongs to

### What feedback can safely do

User feedback can safely support:

- local per-user safety suppression
- ranking families for manual review
- ranking families for future LLM generation
- pattern mining across repeated failures

### What feedback should not do automatically

User feedback should not directly:

- create new shared shadow candidates
- create new shared cue data
- rewrite the canonical semantic evidence layer
- or trigger global positive behavior without review

That is true even when the feedback is attached to a very specific rule event.

### Promotion posture

The current intended posture is conservative:

- even per-rule event feedback should normally require manual promotion before it changes shared semantic truth
- repeated reports may justify faster manual review or a future conservative global abstain bias
- but raw reports should not silently become global semantic data

### Pattern mining

The repo should still be able to mine user feedback for patterns such as:

- topic or domain clusters
- trigger families
- phrase-boundary failures
- repeated active-vs-shadow confusions
- policy-version regressions

Those mined patterns are valuable, but promoting them into global behavior should usually remain manual at first.

## Safe first product action

The safest immediate product action is a local user override.

Example:

- the user can completely remove or suppress a rule locally after a bad replacement

This is valuable because it:

- protects the user immediately
- does not require trust in global feedback quality
- and does not pollute shared semantic truth

So future feedback architecture should distinguish clearly between:

- local safety action
- and shared semantic-data promotion

The first can be automatic.
The second should usually remain review-gated.

Current planning anchors:

- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/rulegen/semantic_feedback_promotion_flow.md`

## Recommended first-budget posture

Budget calculation reference:

- `docs/rulegen/semantic_llm_generation_budget_reference.md`

Before any full scan, the current recommended first-budget posture is:

- choose a bounded first tranche of high-value families
- prefer families that are clearly runtime-relevant and plausibly data-fixable
- avoid spending early budget on obvious phrase/parsing failures
- avoid spending early budget on families that appear to be pure algorithm problems
- preserve raw batch provenance so future batches can be compared directly

This should make the first tranche useful in two ways:

- it may improve quality immediately
- and it will teach the repo which kinds of families are actually worth paying for

Current cost posture:

- the `$100` budget is not tight at the current request sizes
- the completed active-only PoC cost estimate is only cents on `gpt-5.4-mini`
- even hundreds of active-only requests are expected to remain in low dollars
- the real constraint is generated-data validity and downstream contribution, not
  raw token spend

Post-generation audit posture:

- raw LLM outputs remain immutable
- derived postprocess views may mechanically drop or scrub generated evidence
  before rescoring
- the current active-only audit lane is:
  - `scripts/testing/semantic_veto_evidence_gap_generation_postprocess_en_es.py`
  - `docs/test_outputs/semantic_veto_evidence_gap_generation_postprocess_active_only_poc_en_es_latest.md`
- this lane compares sentence-plus-note, sentence-only, note-only diagnostic,
  eval-overlap-filtered, POS-anchored, conservative, and quality-ranked views
- promotion candidates should prefer generated browser sentences over explanatory
  evidence notes unless the postprocess report proves the notes are harmless

Current prompt-variant bakeoff result:

- no runtime policy, threshold, or raw-output mutation was made
- four active-only prompt packets were generated over the same frozen 24-family
  denominator:
  - `v5_refresh_control`
  - `v6_pos_only`
  - `v6_diversity_only`
  - `v6_pos_diversity`
- live generation accepted `24 / 24` responses for every variant
- admission accepted all rows for `v5_refresh_control`, `v6_pos_only`, and
  `v6_diversity_only`
- admission rejected one `v6_pos_diversity` row because the model wrote
  `smiled` instead of the exact browser trigger `smile`; this is kept as a
  prompt-quality signal, not repaired in raw output
- the consolidated bakeoff artifact is:
  - `scripts/testing/semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es.py`
  - `docs/test_outputs/semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es_latest.md`
- primary comparison view: `no_high_eval_overlap_sentence_only`
- primary result:
  - `v5_refresh_control`: `73.63%` accuracy / `50.00%` replace recall / `0`
    harmful / `24` false abstains
  - `v6_pos_only`: `68.13%` / `43.75%` / `2` harmful / `27`
  - `v6_diversity_only`: `67.03%` / `41.67%` / `2` harmful / `28`
  - `v6_pos_diversity`: `68.13%` / `41.67%` / `1` harmful / `28`
- interpretation:
  - POS/diversity prompting improved some mechanical diagnostics, especially
    model-provided frame labels and POS-weak counts
  - those mechanical improvements did not improve downstream veto decisions on
    this frozen active-only lane
  - the current best immediate prompt posture is therefore the simpler v5
    active-only shape plus postprocess filtering, not the heavier v6 wording

## What a future automatic pass should emit

Before attempting a full scan, the repo should converge on a family-level inventory row shape.

Minimum fields:

- `family_id`
- `pair`
- `trigger`
- `normalized_trigger`
- `active_target`
- `active_sense_hint`
- `current_pointer_status`
- `current_competition_status`
- `current_shadow_candidate_count`
- `current_promoted_shadow_count`
- `runtime_relevance`
- `likely_bucket`
- `bucket_confidence`
- `bucket_evidence`
- `recommended_action`

This inventory is the real prerequisite for later prompt work.

Current planning anchor:

- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

The prompt should be written after the queueing unit is stable, not before.

The current queueing unit is now stable enough for a first bounded pre-prompt workflow:

- inventory row
- sampled manual queue review
- frozen bakeoff queue
- frozen prompt-slot manifest
- frozen prompt spec
- rendered prompt smoke bundle

What is still missing before another prompt-spend wave:

- a concrete explanation of why the accepted cue text is not moving the safe additive downstream lane
- a changed source-data, insertion-strategy, or evaluation-lane hypothesis that could plausibly beat the current reverse-aux control
- then another bounded proxy/target pass only for that new hypothesis

Current answer to the first item:

- the accepted cue text is active-side only
- active-side-only evidence broadens replace pressure without equal shadow-side calibration
- reverse-aux succeeds because it changes active and shadow evidence together
- therefore the next queue work should prioritize competition-symmetric source data over another prompt wording pass
- the new source/insertion probe makes that concrete:
  - `scripts/testing/semantic_llm_source_insertion_probe_en_es.py`
  - `docs/test_outputs/semantic_llm_source_insertion_probe_latest.md`
  - full symmetric reverse-aux is `82.5%` accuracy / `62.5%` replace recall / `1` harmful / `6` false abstains
  - active-only reverse-aux drops to `80.0%` / `56.2%` / `1` / `7`
  - shadow-only reverse-aux drops to `77.5%` / `56.2%` / `2` / `7`
  - active LLM cues plus reverse-shadow calibration still lands at `72.5%` / `56.2%` / `4` / `7`
  - hard reviewed example frames remove all false abstains but reopen phrase leaks: `92.5%` / `100.0%` / `3` / `0`
  - active-guard reviewed example frames reach `100.0%` / `100.0%` / `0` / `0` as an internal upper bound
  - `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py` now tests the more fundamental internal shape: score contexts against active/shadow example prototypes, then still emit only `replace` or `abstain`
  - `docs/test_outputs/semantic_llm_prototype_admission_probe_latest.md` clears the frozen queue at `100.0%` / `100.0%` / `0` / `0`
  - `docs/test_outputs/semantic_llm_prototype_admission_probe_expanded_latest.md` expands to all `95` `v10` cases and shows that active/shadow prototypes plus active-sense phrase guarding still leave phrase-control leaks at `97.9%` / `100.0%` / `2` / `0`
  - adding reviewed phrase-control prototypes as abstain competitors clears that expanded oracle read at `100.0%` / `100.0%` / `0` / `0`
  - the canonical intake/evidence schemas and normalizer now accept `relation_type=phrase_control_example` and `role=phrase_containment`
  - `scripts/testing/semantic_llm_example_frame_contract_en_es.py` now gates future source batches against the full active/shadow/phrase-control contract
  - `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py` now builds a no-spend reviewed fixture in the same raw-intake and normalized-evidence shape expected from future generated batches
  - `docs/test_outputs/semantic_llm_example_frame_contract_latest.md` shows the frozen-queue fixture is contract-complete: `8 / 8` families
  - `docs/test_outputs/semantic_llm_example_frame_contract_expanded_latest.md` shows the full-`v10` fixture is contract-complete: `19 / 19` families
  - `docs/test_outputs/semantic_llm_example_frame_contract_overlap_latest.md` preserves the current overlap target batch as a negative contract read: `0 / 6` families are complete because the batch only has active cue rows
  - the prototype-admission probe now consumes the normalized reviewed evidence batches directly and still clears the frozen queue and full-`v10` reads
  - the generated missing-row quality gate now shows why that reviewed oracle result cannot be copied directly into source admission: broad semantic phrase-control prototypes put phrase-overreach pressure on `12` active false-abstain rows and directly add `2` incremental false abstains, while local containment-pattern admission creates `0` incremental containment false-abstains and `2` correct containment hits
  - so the next source hypothesis needs balanced active/shadow example-frame evidence generated or ingested together, plus phrase-control rows admitted as containment patterns or a separate abstain gate, not active cue text with a later shadow-side patch
  - `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py` now turns the reverse-aux required-family gap into a no-spend candidate plan
  - `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md` currently plans `20` active/shadow semantic candidate requests by default: `10` same-POS `plant` shadow candidates, `5` `check` shadow candidates, and `5` `play` active candidates; phrase-control generation is explicit opt-in
  - that plan keeps reviewed sentence-veto case text and translation targets out of prompt input; the prompts carry only trigger text, active/shadow sense labels and glosses, and queue role/archetype/notes
  - the live missing-row execution completed cleanly, but the downstream quality gate rejects the result:
    - `scripts/testing/semantic_llm_example_frame_generation_run_en_es.py`
    - `scripts/testing/semantic_example_frame_batch_merge_en_es.py`
    - `scripts/testing/semantic_llm_example_frame_remediation_plan_en_es.py`
    - `docs/test_outputs/semantic_llm_example_frame_remediation_plan_latest.md`
    - the next no-spend remediation plan is `8` requests: `7` active examples for active false-abstain families and `1` shadow example for the harmful `report` shadow cases, with phrase-control evidence left on the containment-only path
    - `scripts/testing/semantic_llm_example_frame_generation_quality_gate_en_es.py`
    - `docs/test_outputs/semantic_llm_example_frame_generation_run_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_generation_contract_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_generation_quality_gate_latest.md`
    - live generation accepted and normalized `11 / 11` rows
    - the merged reverse-aux plus generated batch is structurally complete at `8 / 8` required families
    - the quality gate rejects it as analysis-only: best prototype config is `67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains
    - current conclusion is not "generate more missing rows"; it is "change the source shape and scorer interface"
    - phrase-control generated examples should not be used as broad semantic competitors without an additional containment/gating layer
    - future generated source batches should generate balanced active and shadow exemplars as a set, not only fill reverse-aux gaps
  - the residual source pass has now been executed and filtered:
    - `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py`
    - `docs/test_outputs/semantic_llm_example_frame_remediation_run_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_leakage_audit_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_run_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_leakage_audit_latest.md`
    - the first residual pass accepted `8 / 8` rows, but leakage filtering removed `1` benchmark-near-copy `plant` row
    - the second bounded residual pass was replayed through rekeyed row ids and accepted `6 / 6` rows, but leakage filtering removed `1` shared-span `plant` row
    - the filtered generated-source composite is structurally complete at `8 / 8` families with `36` rows
  - the key quality gain came from a scorer-interface change, not more rows alone:
    - `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`
    - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_prototype_admission_probe_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_quality_gate_latest.md`
    - the new `prototype_reviewed_examples_surface_pos_rescue_guard` keeps the UX binary, keeps phrase-control evidence containment-only, and adds local surface-POS rescue/preemption for noun-active vs verb-shadow frames
    - that config clears the prototype-quality gate at `95.0%` accuracy / `87.5%` recall / `0` harmful / `2` false abstains
    - the two remaining false abstains are same-POS `plant` rows; the next queue should target same-POS discrimination or held-out validation of the surface-POS guard, not another generic cross-POS prompt fill
  - the next plant-only source attempt has now been bounded and shown not to fix the gate:
    - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_generalization_probe_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_plan_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_run_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_v2_run_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_leakage_audit_latest.md`
    - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_v2_leakage_audit_latest.md`
    - the broader `95`-case read keeps the surface-POS guard at `0` harmful replacements, so that guard remains safety-positive rather than an overfit harmful-replacement source
    - the remediation planner now auto-selects the current best remediation-eligible prototype config; the latest plan correctly reduces the live source target to one active `plant` request
    - both plant live attempts were structurally accepted, but canonical leakage admission filtered both because the model kept returning `watered` / `windowsill` variants of the reviewed benchmark sentence
    - current conclusion: no quality fix came from the plant-only source spend; the next source step needs a stronger repair strategy, such as split multi-example active generation with explicit non-overlap validation or a different source family, before more paid plant attempts

Current status on that seam:

- the no-spend preflight runner now exists:
  - `scripts/testing/semantic_llm_prompt_preflight_en_es.py`
- the no-spend cost-estimate runner now exists:
  - `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py`
- the execution runner now exists:
  - `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`
- the no-spend source/insertion probe now exists:
  - `scripts/testing/semantic_llm_source_insertion_probe_en_es.py`
- the no-spend prototype-admission probe now exists:
  - `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`
- the no-spend example-frame source-contract gate now exists:
  - `scripts/testing/semantic_llm_example_frame_contract_en_es.py`
  - use `--required-family-json` for promotion-relevant reads so all frozen queue families must be covered, not only families present in the batch
- the no-spend reviewed example-frame batch generator now exists:
  - `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py`
- the non-LLM reverse-aux example-frame batch generator now exists:
  - `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py`
  - `docs/test_outputs/semantic_reverse_aux_example_frame_contract_latest.md` shows the real external batch is useful but not contract-complete: `0 / 8` required families complete, with missing shadow rows for `plant` and `check` and missing phrase-control rows for every family
- the no-spend missing-row generation planner now exists:
  - `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py`
  - `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md`
- the live/replay missing-row generation runner and post-generation gates now exist:
  - `scripts/testing/semantic_llm_example_frame_generation_run_en_es.py`
  - `scripts/testing/semantic_example_frame_batch_merge_en_es.py`
  - `scripts/testing/semantic_llm_example_frame_generation_quality_gate_en_es.py`
  - current status is `analysis_only`, not promotion-ready
- the same runner now has a strict replay path:
  - `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`
  - `docs/test_outputs/semantic_llm_prompt_replay_latest.md`
- the live runner now requires explicit `--execute-live` so prompt spend cannot happen accidentally
- live runs are now also hard-stopped unless they declare:
  - the exact selected request count
  - explicit pricing inputs
  - and an explicit estimated cost ceiling
- live execution is now also journaled by operator-supplied `--run-id`:
  - completed request outcomes are append-only and resumable
  - rerunning without `--resume` over an existing journal is rejected
  - ambiguous started-without-outcome requests block resume instead of risking duplicate spend
- the evidence-gap generation runner now also emits scale-safe run artifacts:
  - `*_run_manifest.json` before live spend and after final bundle write
  - `*_request_queue.jsonl` before live spend
  - `*_raw_responses.jsonl` immediately after each live outcome
  - `*_failures.jsonl` immediately after each failed live outcome
  - final JSON/Markdown/JSONL bundle writes use temp-file-and-rename atomic writes
- the current Codex command shell still does not inherit `OPENAI_API_KEY` automatically, but the sourced-shell + repo-venv path is now surfaced explicitly by the preflight artifact
- current token-volume review is also explicit before any paid run:
  - latest target-overlap preflight selected `6` target requests
  - heuristic `3155` input tokens
  - heuristic `540` expected output tokens
- the replay rehearsal has already proven the preserved-batch plumbing:
  - `1` accepted request normalized cleanly
  - `1` malformed output stayed raw-only and was rejected
  - `1` forced API error stayed raw-only and was counted separately
- the latest sourced-shell target path is now proven end to end:
  - `6 / 6` overlap challenger target requests accepted and normalized
  - actual target usage was `2825` input tokens and `179` output tokens
- so the blocker is no longer local runner infrastructure or target-model prompt validity; it is downstream acceptance

Once the queueing unit is stable, use `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md` for the prompt-slot matrix, proxy-vs-target model policy, and cheap bakeoff workflow.

## Human review posture

The project should not aim to manually review every family.
That is not realistic.

Instead:

- automatically triage all families,
- manually sample high-impact or low-confidence families,
- cluster repeated families together,
- and use the reviewed slice to calibrate the triage policy.

The target is not:

- perfect automatic diagnosis

The target is:

- useful queue prioritization with explicit uncertainty

## Practical current takeaway

The present understanding is:

- the queueing unit should be a competition family, not a word
- "worried about polysemy" should mean product-relevant semantic hazard, not dictionary polysemy alone
- automatic classification can only produce hypotheses, not certain root-cause labels
- LLM budget should be spent only after a family-level queue exists
- the frozen `v10` queue now already carries the first prompt-ready bundle:
  - family inventory
  - bakeoff queue
  - slot manifest
  - prompt spec
  - rendered smoke bundle
- current first-tranche defaults are now explicit:
  - proxy `gpt-5.4-mini`
  - target `gpt-5.4`
- reuse should happen at family level for shadows and at sense-pair level for cues

## Not yet decided

The following still need deeper discussion before a full scan/pass is justified:

- the exact family identity before full active-sense coverage exists
- the exact confidence model for bucket guesses
- the exact minimum signal set for `not_applicable`
- how much runtime evidence versus offline proxy evidence should influence queueing
- which reviewed slice should calibrate the first automatic triage pass
- what budget threshold should separate "generate now" from "leave unresolved"
