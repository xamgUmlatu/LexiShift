# Semantic Source Admission Program

Status: active plan
Role: Planning / WIP
Purpose: make semantic-veto source coverage repeatable, leakage-safe, and promotion-gated before any runtime publication claim
Last updated: 2026-04-29
Last verified: 2026-04-29 split source contract, multi-candidate generation plan, leakage/duplicate/final-composite sense admission, source-admission cycle wrapper, all-v10 reverse-aux plus WordNet/Wiktextract adapter admission, v2 active/shadow held-out validation, phrase v2 calibrated-margin validation, independent phrase challenge validation, phrase-pattern repair, fresh phrase stress validation, non-v10 phrase signal audit, non-v10 source-backed WordNet definition probe, automatic non-v10 inventory candidates, automatic non-v10 wave construction, no-spend wave-admission sweep, selected-wave held-out validation, margin policy sweep, failure-class mining, wave32/wave64 any-POS source-support sweep, ranked WordNet weak-link slate extraction, supported source-portfolio selection, semantic decision-rule comparison plan, forward-only upper-bound probe, source-support conversion audit, loader-only leakage policy, and sentence-transformer prototype-admission artifacts
Source-of-truth: planning doc only; executable truth lives in the scripts and generated artifacts referenced below
Verification:
- `scripts/testing/semantic_llm_prototype_ablation_matrix_en_es.py`
- `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py`
- `scripts/testing/semantic_llm_example_frame_sense_discrimination_audit_en_es.py`
- `scripts/testing/semantic_llm_example_frame_contract_en_es.py`
- `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py`
- `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py`
- `scripts/testing/semantic_wordnet_example_frame_batch_en_es.py`
- `scripts/testing/semantic_wiktextract_example_frame_batch_en_es.py`
- `scripts/testing/semantic_source_admission_cycle_en_es.py`
- `scripts/testing/semantic_source_heldout_validation_en_es.py`
- `scripts/testing/semantic_phrase_policy_signal_audit_en_es.py`
- `scripts/testing/semantic_source_reference_lane_en_es.py`
- `scripts/testing/semantic_source_failure_class_mining_en_es.py`
- `scripts/testing/semantic_non_v10_inventory_candidates_en_es.py`
- `scripts/testing/semantic_non_v10_wave_builder_en_es.py`
- `scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py`
- `docs/test_outputs/semantic_source_admission_cycle_latest.md`
- `docs/test_outputs/semantic_reverse_aux_example_frame_batch_all_v10_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest.md`
- `docs/test_outputs/semantic_wordnet_example_frame_batch_all_v10_latest.md`
- `docs/test_outputs/semantic_wiktextract_plant_example_frame_batch_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_wordnet_wiktextract_plant_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md`
- `docs/test_outputs/semantic_source_heldout_validation_v2_latest.md`
- `docs/test_outputs/semantic_source_phrase_heldout_validation_latest.md`
- `docs/test_outputs/semantic_source_phrase_heldout_v2_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_phrase_challenge_v1_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_phrase_stress_v1_margin005_validation_latest.md`
- `docs/test_outputs/semantic_phrase_policy_signal_non_v10_latest.md`
- `docs/test_outputs/semantic_wordnet_def_source_non_v10_probe_v1_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest.md`
- `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_latest.md`
- `docs/test_outputs/semantic_source_failure_class_mining_latest.md`
- `docs/test_outputs/semantic_non_v10_inventory_candidates_latest.md`
- `docs/test_outputs/semantic_non_v10_wave2_draft_latest.md`
- `docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave2_draft_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_draft_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave16_latest.md`
- `docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave2_selected_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_heldout_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_phrase_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_margin_policy_sweep_latest.md`
- `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave2_selected_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md`
- `docs/test_outputs/semantic_non_v10_wave4_anypos_supported_probe_min0p12_latest.md`
- `docs/test_outputs/semantic_wordnet_def_ex_non_v10_wave4_anypos_supported_probe_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave4_anypos_supported_probe_latest.md`
- `docs/test_outputs/semantic_non_v10_source_support_conversion_wave4_anypos_supported_probe_latest.md`
- `docs/test_outputs/semantic_non_v10_source_support_conversion_wave3_anypos_latest.md`
- `docs/test_outputs/semantic_source_margin005_ablation_matrix_latest.md`
- `docs/test_outputs/semantic_source_reference_lane_latest.md`
- `docs/test_outputs/semantic_llm_prototype_ablation_matrix_source_coverage_filtered_safe_v2_sentence_transformer_phrase_ablation_latest.md`
- `docs/test_outputs/semantic_llm_prototype_ablation_matrix_source_coverage_filtered_safe_v2_sense_admitted_sentence_transformer_margin0_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_source_coverage_filtered_safe_v2_sense_discrimination_sentence_transformer_margin0_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_source_coverage_filtered_safe_v2_contract_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md`
- `docs/test_outputs/semantic_source_scope_margin_bakeoff_en_es_latest.md`
Related planning:
- `docs/rulegen/semantic_sentence_veto_algorithm.md`
- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/rulegen/semantic_en_es_expansion_opportunity_roadmap.md`
- `docs/rulegen/semantic_shadow_source_intake_plan.md`

## Goal

Turn semantic-veto source coverage from a hand-patched research loop into an admission pipeline.

The app-level UX remains binary:

- show the replacement
- or do not show the replacement

Internally, evidence must pass staged admission before it can influence that binary decision.

The current best analysis-only lane is:

- active/shadow example-frame prototypes as the semantic competition source
- phrase-control evidence used as containment or abstain evidence, not broad semantic competition
- sentence-transformer scoring for semantic similarity
- surface-POS rescue/preemption as a deterministic guard around weak active/shadow cases
- leakage admission before merge, with sense admission applied to the final merged composite so base rows cannot bypass the gate

The current active-vs-shadow decision rule remains a control, not a proven
optimum. Use
`docs/rulegen/semantic_decision_rule_comparison_plan.md` before replacing or
extending `similarity(context, active) - max_similarity(context, shadow)`: the
comparison must isolate context representation, active/shadow source
representation, similarity scoring, row aggregation, final decision rule, and
phrase/no-winner handling.

Latest analysis result:

- full `v10` synthetic suite: `95` cases
- best admitted analysis lane: `100.0%` accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains
- split source contract status: semantic coverage is complete at `19 / 19`, while phrase containment and the legacy combined contract remain `review` at `0 / 19`
- promotion posture: offline `semantic_active_shadow` promotion-candidate; runtime publication remains blocked on phrase-source policy, broader held-out breadth, and packaging feasibility

Latest no-spend decision-surface result:

- the source-scope margin bakeoff compares no-source, LLM-v2 source, WordNet-reference source, and combined-source scopes in one matrix
- source rows are most useful as additive evidence over the incumbent definition/example row surface
- combined LLM-v2 plus WordNet-reference additive rows reached `0` harmful replacements and `37` false abstains across frozen v10, source-heldout v2, phrase-heldout v2, and phrase challenge
- the no-source row control on the same suites was `0` harmful replacements and `44` false abstains
- production policy remains unchanged until this candidate passes companion negative controls and broader held-out validation

## Non-Goals

This program does not immediately:

- publish runtime semantic-admission defaults
- treat reviewed sentence-veto examples as runtime source data
- accept generated rows just because an LLM returned valid JSON
- add family-specific veto exceptions to close individual cases
- let phrase-control rows compete as broad semantic prototypes by default

## Core Design

### 1. Split source obligations

The old all-in-one source contract is too coarse for the current evidence.

Use two obligations:

1. Semantic competition coverage
   - active examples per family
   - shadow examples per family/sense
   - used by semantic scoring

2. Phrase containment coverage
   - phrase-control examples or patterns
   - used only to abstain through containment or a separate phrase gate
   - not used as broad semantic competitors unless an ablation explicitly proves safety

This split is justified by the latest phrase ablation:

- `generated_composite` reaches the full-`v10` perfect analysis read on the sentence-transformer lane
- `generated_no_phrase` reaches the same read on that lane
- therefore phrase-control row absence is not the active/shadow semantic blocker for this lane

### 2. Rows must earn admission before scoring

A row is not admitted because it exists.

A row is admitted only after it passes:

- schema normalization
- benchmark leakage audit
- duplicate and near-duplicate audit
- active-vs-shadow discrimination checks
- phrase-isolation checks when relevant
- downstream ablation non-regression

Generated acceptance count and admitted source count must stay separate.

### 3. Keep source, scorer, and guard effects separable

Every candidate batch must be tested across:

- source modes:
  - current candidate source
  - no source / empty batch
  - active-only
  - no-shadow
  - no-phrase
  - reviewed oracle where useful as an upper bound
- scorers:
  - lexical controls
  - TF-IDF controls
  - sentence-transformer candidate lane
- decision shapes:
  - active/shadow semantic competition
  - phrase containment
  - surface-POS rescue/preemption
  - broad phrase prototype scoring as a negative control

The target is not a pretty headline.
The target is knowing which node created the gain.

## Execution Phases

### Phase 0. Freeze The Reference Lane

Purpose: keep a stable baseline while source work moves quickly.

Current reference artifacts:

- `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json`
- `docs/test_outputs/semantic_source_reference_lane_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md`
- `docs/test_outputs/semantic_source_heldout_validation_v2_latest.md`
- `docs/test_outputs/semantic_llm_prototype_ablation_matrix_source_coverage_filtered_safe_v2_latest.md`
- `docs/test_outputs/semantic_llm_prototype_ablation_matrix_source_coverage_filtered_safe_v2_sentence_transformer_latest.md`
- `docs/test_outputs/semantic_llm_prototype_ablation_matrix_source_coverage_filtered_safe_v2_sentence_transformer_phrase_ablation_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_source_coverage_filtered_safe_v2_contract_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_manual_source_coverage_leakage_safe_audit_latest.md`
- `docs/test_outputs/semantic_llm_example_frame_manual_plant_light_leakage_safe_audit_latest.md`

Completion criteria:

- latest reference artifacts are regenerated from committed scripts
- results are recorded in `docs/rulegen/semantic_routing_weakness_triage_plan.md`
- any newer result says whether it is `analysis-only`, `promotion-candidate`, or `runtime-ready`
- the reference-lane manifest passes with `status=ok` and `decision=reference_lane_frozen`

### Phase 1. Implement The Split Contract

Purpose: stop treating phrase-control absence as the same failure as active/shadow semantic absence.

Work items:

1. Extend the example-frame contract report to emit separate summaries:
   - semantic competition coverage
   - phrase containment coverage
   - combined legacy coverage
2. Keep the legacy combined read for comparison.
3. Add tests proving:
   - active/shadow-complete plus phrase-missing reports semantic-complete and combined-review
   - phrase rows without `phrase_containment` role do not satisfy phrase containment coverage
   - source reports do not mark promotion-ready from semantic coverage alone
4. Update generated Markdown so operators can see which obligation failed.

Acceptance:

- a batch like `en-es-balanced-plus-source-coverage-filtered-safe-v2-20260425a_normalized_evidence.json` reports semantic active/shadow coverage complete for `19 / 19`
- the same batch remains combined `review` while phrase rows are missing for `11` families

### Phase 2. Build Multi-Candidate Source Generation

Purpose: avoid one-shot LLM rows that copy benchmark-shaped sentences.

Work items:

1. Add a generation-plan mode that requests multiple candidates per active/shadow sense.
2. Keep benchmark case sentences out of prompts.
3. Add prompt constraints that steer away from known benchmark surface spans without revealing the benchmark sentence.
4. Preserve all raw candidates in immutable raw-response artifacts.
5. Normalize candidates into a provisional batch, not an admitted batch.

Candidate defaults:

- `5` candidates for ordinary active/shadow rows
- `10` candidates for same-POS hard families such as `plant`
- no automatic phrase-control generation unless the task is explicitly phrase containment

Acceptance:

- generated raw count, structurally accepted count, leakage-kept count, and admitted count are all reported separately
- interrupted live runs stay resumable through journaled `--run-id`

Current no-spend implementation:

- `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py` now plans multiple active/shadow candidate attempts per missing semantic slot
- default semantic slots use `5` candidate attempts
- same-POS hard slots use `10` candidate attempts
- phrase-control generation is excluded by default and must be requested explicitly with `phrase_control_example`
- `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md` currently plans `20` active/shadow semantic candidate requests: `10` same-POS `plant` shadow candidates, `5` `check` shadow candidates, and `5` `play` active candidates
- this planner is still provisional: it plans raw candidates, but does not itself admit rows

### Phase 3. Add Source Admission Gates

Purpose: make bad rows fail before they can inflate quality.

Admission gates:

1. Schema gate
   - raw intake parses
   - normalized evidence batch emits expected relation types and sense hints

2. Leakage gate
   - full benchmark containment check
   - contiguous benchmark token-span check
   - canonical person/determiner rewrite check
   - duplicate or near-duplicate check against prior generated/source rows

3. Sense-discrimination gate
   - candidate row must score closer to its intended active/shadow sense than its competitor under at least one approved scorer
   - rows that only repeat generic trigger context are rejected or quarantined
   - in the source-admission cycle this runs after candidate filtering and merge, so every semantic row in the final composite is admitted by the same rule

4. Phrase-isolation gate
   - phrase-control rows can only enter containment/abstain lanes by default
   - broad phrase prototype scoring remains a negative-control ablation, not a promotion lane

5. Downstream non-regression gate
   - merge only admitted rows into a candidate composite
   - rerun the ablation matrix
   - reject any source batch that introduces harmful replacements in the candidate lane

Acceptance:

- no downstream artifact uses an unfiltered generated batch as a promotion signal
- every promotion-candidate source batch links to its leakage audit and merge report

Current implementation:

- `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py` now reports `leakage_hit_count`, `duplicate_hit_count`, `rejected_row_count`, and `kept_row_count`
- the audit rejects duplicate and near-duplicate rows within the current batch and, when supplied, against `--prior-batch-json` source batches
- the current source-coverage audit remains `review` because of `3` benchmark leakage hits, with `0` duplicate hits and `19` kept rows
- the manual leakage-safe replacement batches remain `ok` with `0` leakage hits and `0` duplicate hits
- `scripts/testing/semantic_llm_example_frame_sense_discrimination_audit_en_es.py` now audits active/shadow rows against intended and competing dataset senses before merge
- the cheap lexical/TF-IDF sense screen is intentionally conservative on the safe-v2 composite: it admits `31 / 52` semantic rows and rejects `21`
- the sentence-transformer sense screen with `min_intended_score=0.5` and `min_margin=0.0` admits `50 / 52` semantic rows, rejects only `check` active reverse-aux and `report` shadow reverse-aux, and passes `8` phrase rows through as non-semantic containment evidence
- downstream ablation on that sentence-transformer admitted batch preserves the best full-`v10` read: `100.0%` accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains on `active_shadow_containment_surface_pos`
- `scripts/testing/semantic_source_admission_cycle_en_es.py` now applies the stricter end-to-end order: leakage/duplicate audit on the candidate batch, duplicate comparison against the base batch, merge, final-composite sense admission, split contract, ablation, and residual extraction
- the current cycle artifact remains `review` / `analysis_only`: it rejects `16` duplicate candidate rows against the base/current composite, rejects `2` semantic rows at final sense admission, keeps semantic coverage complete at `19 / 19`, leaves phrase coverage at `8 / 19`, and still reaches the best full-`v10` analysis read of `100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains
- the cycle wrapper supports `--empty-base`, which lets an adapter batch be evaluated by itself rather than accidentally inheriting source rows from the default reverse-aux base

### Phase 4. Build Composite Candidate Batches

Purpose: keep source provenance explicit while allowing staged experiments.

Required reports for every candidate composite:

1. source input report
2. leakage audit report
3. sense-discrimination audit report
4. filtered/admitted normalized batch
5. merge report
6. split contract report
7. ablation matrix report
8. residual-case report

Current merge command shape:

```bash
python3 scripts/testing/semantic_example_frame_batch_merge_en_es.py \
  --base-batch-json <base-normalized-evidence.json> \
  --add-batch-json <admitted-source-batch.json> \
  --batch-id <candidate-batch-id> \
  --source-id <candidate-source-id> \
  --merged-batch-out <candidate-normalized-evidence.json> \
  --json-out <merge-report.json> \
  --markdown-out <merge-report.md>
```

Preferred source-admission cycle command:

```bash
python3 scripts/testing/semantic_source_admission_cycle_en_es.py \
  --base-batch-json <base-normalized-evidence.json> \
  --candidate-batch-json <candidate-normalized-evidence.json> \
  --json-out <cycle-report.json> \
  --markdown-out <cycle-report.md>
```

The cycle wrapper assumes generation/ingestion and normalization have already produced a provisional evidence batch. It does not run live generation itself. Its purpose is to make every existing candidate batch pass the same no-spend gates before it is treated as a source candidate.

Acceptance:

- merge report lists every component batch
- row counts by relation type are visible
- duplicate rows are reported, not silently used as extra evidence

### Phase 5. Promote The Ablation Matrix To The Main Gate

Purpose: make batch acceptance empirical.

Minimum ablations:

- source modes:
  - `empty_batch`
  - `reverse_aux`
  - `generated_composite`
  - `generated_active_only`
  - `generated_no_phrase`
  - `generated_no_shadow`
  - `reviewed_dataset` when an oracle upper bound is useful
- scopes:
  - frozen prompt queue
  - full `v10` dataset
- scorers:
  - `token_jaccard`
  - `tfidf_cosine`
  - `sentence_transformer_cosine`
- context views:
  - at least `masked_sentence`
  - wider context only when explicitly testing context sensitivity
- decision shapes:
  - active/shadow baseline
  - containment-only phrase handling
  - surface-POS guard
  - broad phrase prototype negative control

Promotion-candidate floor:

- `0` harmful replacements on full `v10`
- no unadmitted generated rows in the source path
- phrase-control rows do not improve the headline only by leaking benchmark-shaped abstain data
- sentence-transformer dependency is named and tested against lexical controls

Runtime-ready floor is stricter and not yet met:

- split source contract implemented
- promotion candidate survives fresh source generation or external-source ingestion
- runtime cost/install/fallback plan for sentence-transformer lane is documented
- held-out or newly generated non-benchmark evaluation still passes

### Phase 6. External Source Expansion

Purpose: reduce dependence on manually curated or LLM-generated examples.

Prioritized source adapters:

1. Wiktionary / Kaikki examples
   - value: real examples and structured sense material
   - risk: sense alignment noise

2. Dictionary example packs
   - value: high-quality active/shadow examples where licensing permits local use
   - risk: uneven coverage by pair

3. Tatoeba / parallel corpora
   - value: real sentence contexts
   - risk: weak sense alignment and phrase leakage

4. Local/web corpus retrieval
   - value: broad real text for hard families
   - risk: licensing, noisier filtering, larger preprocessing surface

5. LLM generation
   - value: fast coverage and controllable sense targets
   - risk: benchmark-shaped outputs unless multi-candidate admission is strict

Adapter acceptance:

- source family is registered in `docs/test_inputs/semantic_shadow_source_registry.json`
- adapter emits raw intake or normalized evidence in the existing schema
- source-specific quality is measured by ablation, not assumed from provenance

Current external-source result:

- `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py` now supports `--scope all_dataset_families`
- `docs/test_outputs/semantic_reverse_aux_example_frame_batch_all_v10_latest.md` extracts a real non-LLM reverse-aux batch across all `19` v10 families: `35` rows, active aux coverage for `18 / 19`, shadow aux coverage for `17 / 19`, and `0 / 19` phrase-control coverage
- `docs/test_outputs/semantic_source_admission_cycle_reverse_aux_all_v10_latest.md` keeps that adapter lane honest: leakage rejects `0`, final sense admission rejects `3`, the admitted batch keeps `32` rows, semantic contract coverage is only `14 / 19`, phrase coverage is `0 / 19`, and the best full-`v10` ablation is `90.5%` accuracy / `86.8%` recall / `4` harmful / `5` false abstains
- interpretation: reverse-aux all-v10 is a strong source floor and a good gap router, but not the one design improvement that closes the quality gate by itself

Current composite-source promotion candidate:

- `scripts/testing/semantic_wordnet_example_frame_batch_en_es.py` builds a local English WordNet source batch; the adapter now emits entry sentence frames when they are stronger than generic synset examples and records WordNet sense rank so weak lexical overlaps can fall back to the source's own sense order instead of over-weighting generic tokens such as `different` or `part`.
- `scripts/testing/semantic_wiktextract_example_frame_batch_en_es.py` builds a raw Wiktextract example adapter for residual families; the current plant run uses `--min-link-score 0.08` to recover a living-plant example that the converted SQLite packs do not expose
- `scripts/testing/semantic_wordnet_example_frame_batch_en_es.py` also supports source-backed related-hyponym rows with a bounded `--related-hyponym-depth`; the current accepted use is active-side related rows for living-plant and deeper biology-cell evidence, not broad shadow-side related expansion
- `scripts/testing/semantic_source_heldout_validation_en_es.py` now validates a v2 active/shadow held-out slice across all `19` v10 families and `38` cases. The v2 expansion exposed two real misses: irregular predicate-frame handling for `play` (`won`) and shallow WordNet biology-cell evidence.
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_heldout_cases_v1.json` adds a separate phrase/no-winner held-out slice across all `19` v10 families. This intentionally does not change the active/shadow reference lane.
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_heldout_cases_v2.json` broadens that phrase slice to `38` no-winner cases. The zero-margin phrase run exposed one near-tie harmful replacement, `board:002` (`The new designer came on board last month.`); the separate `min_margin=0.005` phrase-policy candidate artifact passes with `0` harmful replacements and also preserves active/shadow v2.
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md` is the current best fresh-source read: leakage rejects `0`, final sense admission rejects `0`, the admitted composite keeps `133` rows, semantic contract coverage is `19 / 19`, phrase coverage is still `0 / 19`, the embedded v2 held-out check is `ok` / `heldout_pass`, and the best full-`v10` ablation reaches `100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains
- `docs/test_outputs/semantic_source_phrase_heldout_validation_latest.md` is the current phrase-boundary read: `19` phrase/no-winner cases, `0` harmful replacements, `0` false abstains, and `100.0%` decision accuracy after the general subject-trigger-object phrase preemption caught the verb-frame `match the totals` miss. This is still bounded phrase evidence, not proof that phrase policy is broadly solved.
- `docs/test_outputs/semantic_source_phrase_heldout_v2_margin005_validation_latest.md` is the current phrase-policy candidate read: `38` phrase/no-winner cases, `0` harmful replacements, `0` false abstains, and `100.0%` decision accuracy at `min_margin=0.005`. This is a calibrated-margin candidate, not a runtime publication decision.
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_challenge_cases_v1.json` adds a fresh independent `19`-case phrase/no-winner challenge. Its first `min_margin=0.005` validation failed with two harmful replacements, `ball:001` (`keep the ball rolling`) and `file:001` (`Customers file past...`); the current phrase-pattern repair passes that suite with `0` harmful replacements and `0` false abstains.
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_stress_cases_v1.json` adds a second fresh `19`-case phrase/no-winner stress suite after the phrase-pattern repair. It passes at `min_margin=0.005` with `0` harmful replacements and `0` false abstains.
- `docs/test_inputs/semantic_routing_cases/en_es_phrase_policy_signal_non_v10_v1.json` and `docs/test_outputs/semantic_phrase_policy_signal_non_v10_latest.md` add a signal-only non-v10 phrase audit. It passes `16 / 16` rows with `0` false positives and `0` false negatives, but it intentionally does not claim end-to-end source coverage or translation quality.
- `docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_probe_v1.json` and `docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_heldout_cases_v1.json` graduate the first non-v10 heads into a source-backed active/shadow probe: `8` ambiguous families, `24` seed cases, and `16` held-out cases.
- `docs/test_outputs/semantic_wordnet_def_source_non_v10_probe_v1_latest.md` shows that definition-preferred WordNet evidence covers `8 / 8` active families and `8 / 8` shadow families with `18` rows; the earlier example-preferred mode covered the same families but lost four active rows at sense admission, so the mode choice is a real source-method decision.
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest.md` admits all `18` definition-preferred rows with `0` leakage rejects and `0` sense rejects, completing the semantic contract at `8 / 8` while leaving phrase containment at `0 / 8`. It embeds the non-v10 held-out pass but remains `analysis_only` because the seed ablation is not a promotion lane and phrase contract coverage is still intentionally separate.
- `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.md` passes the first source-backed non-v10 held-out slice at `100.0%` decision accuracy / `100.0%` replace recall / `0` harmful replacements / `0` false abstains. The first run caught one harmful alternate-noun shadow over-rescue (`violin case`), fixed by requiring active-noun surface rescue to respect the strongest shadow POS instead of any verb shadow in the family.
- `docs/test_outputs/semantic_source_failure_class_mining_latest.md` makes the overfitting boundary explicit. It reports `review` / `seed_pass_expand_inventory`: `0` blocking semantic-promotion failure classes and a clean `16`-case held-out read, but medium manual-overfit risk because the current non-v10 proof is still only `8` families / `16` held-out cases, the seed ablation still has `4` false abstains (`rock`, `point`, `date`), phrase contract coverage is still `0 / 8`, and the breadth gap is `42` more families plus `184` more cases before the default broad-confidence thresholds. The same report records the useful source-method signal: definition-preferred WordNet reduces seed false abstains by `3` and sense rejects by `4` versus the example-preferred comparator.
- `docs/test_outputs/semantic_non_v10_inventory_candidates_latest.md` is the first automatic non-v10 inventory expansion surface. It ranks `75` WordNet-backed ambiguous English headwords after excluding the current v10 and non-v10 seed triggers. This is intentionally not an admitted en-es family file yet: it reports source availability and ambiguity shape, then requires a separate active/shadow Spanish target construction step before source extraction or admission.
- `docs/test_outputs/semantic_non_v10_wave2_draft_latest.md` is the first automatic Spanish active/shadow family construction from that inventory. It uses local Wiktionary en-es, reverse Wiktionary, FreeDict, and WordNet-link support, now requiring visible active/shadow target distinction so UX-invisible pairs such as same-target noun/verb replacements are not admitted as draft families.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_latest.md` is the fixed-size no-spend control for that constructor. Across `9` variants it selects `min_link_score=0.2` plus `definition_and_example:2` as the best fixed-eight source shape: `8` selected families, `34` WordNet rows, `27` final admitted rows, `0` leakage rejects, and semantic contract coverage `7 / 8`. The remaining semantic gap is `end:fin`; phrase containment remains `0 / 8` because WordNet does not generate phrase-control rows.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave16_latest.md` tests the more fundamental pool-first design: over-generate a source-supported pool, then admit-select the final wave. With a `16` requested pool and `8` family selection target, the best variant is `ok` / `semantic_complete_variant_found`: it finds `9` semantic-complete families in the pool and materializes an `8`-family admission-selected draft wave.
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_heldout_margin005_validation_latest.md` and `docs/test_outputs/semantic_source_non_v10_wave2_selected_phrase_margin005_validation_latest.md` now validate that admission-selected automatic wave. The first active/shadow run caught two surface-POS false preemptions (`safe use of...`, `days of rest`), fixed by recognizing conservative `of` noun-complement frames; the first phrase/no-winner run caught `The rest of the team...`, fixed by adding a guarded `the rest of` phrase-control frame. Both selected-wave held-out suites now pass with `0` harmful replacements and `0` false abstains.
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest.md` is the current best admitted artifact for that admission-selected automatic wave. It is `ok` / `analysis_only`: the active/shadow semantic lane is complete at `8 / 8` with `30` final admitted rows, `0` leakage rejects, and a clean `16`-case active/shadow held-out read. It remains analysis-only because the automatic dataset's loader-only scaffold cases are excluded from promotion ablation, and phrase containment is still a tracked `0 / 8` source-contract residual. Sense-discrimination rejects are now treated as source-precision telemetry when the final admitted batch still completes the semantic contract.
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_margin_policy_sweep_latest.md` adds the selected wave to a separate margin-policy sweep. Both the selected active/shadow suite (`16` cases) and the selected phrase/no-winner suite (`8` cases) pass at every tested margin from `0` through `0.05`; this confirms the selected-wave fixes are not margin-threshold artifacts.
- `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave2_selected_latest.md` is the selected-wave anti-handcrafting control. It reports `review` / `seed_pass_expand_inventory` with `0` blocking semantic-promotion classes and `24` clean held-out cases across `8` families, but still medium overfit risk because broad-confidence thresholds need `42` more families and `176` more cases, phrase containment source coverage is absent, and sense-filter rejects remain tracked telemetry.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_latest.md` and `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.md` are the broader supported-source scale-up. The builder now supports `any_cross_pos` in addition to the original `noun_verb` control, moving construction from `11` selected families in the supported noun/verb wave32 probe to `16` selected families. Expanding the requested pool to `64` still does not find additional supported families at the constructor tier: `docs/test_outputs/semantic_non_v10_wave4_anypos_supported_probe_min0p12_latest.md` records `40` skipped candidates for missing reverse/FreeDict-supported cross-POS translations and `13` for missing WordNet-linked cross-POS translations.
- The latest supported-source sweep separates family construction from evidence extraction. It keeps the conservative `min_link_score=0.12` constructor, but adds an `extract0` WordNet candidate-slate variant for source admission. The best single variant is `15 / 16` semantic-complete families; the source portfolio across variants is `ok` / `semantic_complete_source_portfolio_found`, with `17` supported semantic-complete families available and a materialized `16`-family portfolio-selected dataset/queue tagged `reverse_or_freedict_required`. This supersedes the old two-gap read: ranked weak-link extraction fixes `change:cambio` with the event/phase-transition synset and `end:fin` with the extremity synset, while the portfolio keeps `rest:reposo` covered by the non-slate variant where the first WordNet sense is the wrong "remainder" sense.
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave4_anypos_supported_probe_latest.md` remains the detailed single-source supported-probe admission read, and `docs/test_outputs/semantic_non_v10_source_support_conversion_wave4_anypos_supported_probe_latest.md` confirms the supported probe has `36 / 36` translation-supported senses across `16 / 16` families. The current blocker is no longer translation support or the original `change`/`end` source gaps; it is materializing the source-portfolio admitted evidence, then adding held-out active/shadow and phrase cases before any quality claim.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md` is the deliberate source-support upper-bound probe. It keeps the same `any_cross_pos` constructor but allows forward-only translations without reverse Wiktionary or FreeDict support. After the loader-only leakage fix, that lane reaches `ok` / `semantic_complete_variant_found`: the best variant is `min0p2-definition_and_example-rows2`, with `32` constructed families, `31 / 32` semantic-complete families, `111` final admitted rows, and a materialized `16`-family control dataset/queue tagged `forward_only_upper_bound`. This is not promotion evidence because `docs/test_outputs/semantic_non_v10_source_support_conversion_wave3_anypos_latest.md` shows only `3 / 16` selected upper-bound families are fully translation-supported, only one selected row has a non-duplicate same-POS supported alternative, and `12 / 16` families need reviewed or reverse-side source support before quality claims.
- `docs/test_outputs/semantic_source_margin_policy_sweep_latest.md` now compares candidate margins across active/shadow v2, phrase v1, phrase v2, phrase challenge v1, phrase stress v1, and the full-`v10` source ablation. After the phrase-pattern repair and stress suite it is `ok` / `margin_candidate_found`: `0.005` is the smallest passing margin, `0.01` also passes, `0` and `0.001` keep the phrase v2 `on board` harmful replacement, and `0.02+` introduces active false abstains.
- the held-out slices mattered: v1 caught surface-POS over-preemption and missing living-plant source support; v2 caught the irregular `play won` noun frame and the shallow `cell` source gap. The accepted fixes narrow surface-POS preemption, add active-side WordNet related evidence such as `pot plant`, and admit deeper active-side cell evidence such as erythrocyte/red-blood-cell descendants after duplicate and sense-discrimination filtering.
- `scripts/testing/semantic_source_admission_cycle_en_es.py` now makes that split policy machine-readable: the offline promotion lane is `semantic_active_shadow`, phrase containment does not block offline semantic promotion, the source-cycle report consumes the held-out validation artifact directly, and runtime publication is still blocked on phrase-source policy, broader held-out breadth, and runtime packaging feasibility
- `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json` freezes the exact source-cycle, active/shadow held-out, phrase-candidate held-out, and admitted-evidence artifacts for this lane; `docs/test_outputs/semantic_source_reference_lane_latest.md` currently reports `59` passing checks, `0` failures, and `decision=reference_lane_frozen`
- decision: `promotion_candidate` for the offline semantic active/shadow source lane; not runtime-ready behavior

### Phase 7. Runtime Publication Decision

Purpose: prevent analysis artifacts from becoming product defaults prematurely.

Before runtime publication:

1. Decide whether sentence-transformer scoring is acceptable in runtime:
   - bundle size
   - latency
   - offline availability
   - fallback behavior
   - pair/profile gating
2. Decide whether surface-POS rescue/preemption is a stable deterministic guard.
3. Decide what source rows are allowed to become `runtime_publishable=true`.
4. Update publication docs and schemas only after the source-admission gate is stable.

Runtime publication must preserve the UX binary:

- replace
- abstain

Any internal soft states must remain diagnostic unless product explicitly accepts a third user-visible state.

## Operator Checklist

Use this checklist for each aggressive source-coverage slice.

1. Choose scope
   - frozen queue
   - full `v10`
   - specific residual families

2. Choose source family
   - LLM multi-candidate
   - external examples
   - manual/internal analysis artifact
   - reviewed oracle only for upper bound

3. Generate or ingest provisional rows
   - preserve raw input/output
   - keep `runtime_publishable=false`

4. Normalize
   - produce raw intake and normalized evidence artifacts

5. Run leakage admission
   - save audit report
   - use filtered batch only

6. Merge
   - preserve component provenance
   - do not overwrite prior candidate batches

7. Run split contract
   - semantic active/shadow coverage
   - phrase containment coverage
   - legacy combined status

8. Run ablation matrix
   - include `no_phrase` and `no_shadow`
   - include lexical and sentence-transformer lanes

9. Extract residuals
   - list harmful replacements
   - list false abstains
   - classify by source gap, scorer gap, phrase gap, or guard gap

10. Record decision
    - update `docs/rulegen/semantic_routing_weakness_triage_plan.md`
    - use `do_now`, `experiment_next`, or `defer`
    - state whether result is analysis-only, promotion-candidate, or runtime-ready

## Current Next Work

Immediate implementation order:

1. Treat `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md` plus `docs/test_outputs/semantic_source_heldout_validation_v2_latest.md` as the current offline promotion-candidate source lane, not as runtime-ready behavior.
2. Keep the frozen lane manifest and reference report current:
   `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json`
   and `docs/test_outputs/semantic_source_reference_lane_latest.md`.
3. Treat the first source-backed non-v10 WordNet definition probe as a promising expansion pattern, not as broad proof: keep `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.md` as seed evidence, then add more non-v10 waves without tuning on this slice.
4. Use `scripts/testing/semantic_source_failure_class_mining_en_es.py` as the current anti-handcrafting control. A passing seed slice should route to broader automatic inventory generation; a failing slice should first be clustered by reusable failure class before any case-specific patch.
5. Use `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave16_latest.md`, `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest.md`, and `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave2_selected_latest.md` as the selected-wave control. The important design change is pool-first admission selection plus held-out validation, not a one-off `end:fin` patch.
6. Use `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.md`, `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md`, and the two source-support conversion audits as the current breadth/design probe pair. The supported lane now has a no-spend `16`-family semantic source portfolio; the forward-only upper-bound lane still shows the likely ceiling if unsupported translations can be converted into reviewed or reverse-supported source rows.
7. Materialize and validate the supported source portfolio before making broader scoring changes: emit the admitted per-family evidence chosen from the supporting variants, run the source-admission cycle on that portfolio as one batch, then add held-out active/shadow and phrase rows for the selected `16` families.
8. Convert the upper-bound selected families into supported evidence before claiming quality: add or ingest reverse-side support, FreeDict support, Wiktextract examples, reviewed dictionary examples, or another documented source lane, then rerun admission plus independent held-out validation.
9. Decide the runtime phrase-source policy explicitly: either build real phrase-control source adapters for the `19` phrase gaps, add a general pattern policy for phrase/no-winner frames, or accept the already-formalized split where phrase containment remains a separate runtime/publication blocker. Phrase v2, phrase challenge v1, phrase stress v1, and the selected non-v10 phrase suite now pass under the current pattern/margin candidate, but this is still bounded-suite evidence rather than runtime-publication breadth.
8. Audit runtime feasibility for the sentence-transformer plus surface-POS shape: resource packaging, latency, fallback behavior, and pair/profile gating.
9. Only then revisit broader source generation scale-out.

## Open Decisions

1. Should phrase-control coverage remain required for runtime publication if `no_phrase` ablations keep matching the full candidate lane?
2. How broad must held-out validation become before treating the sentence-transformer lane as runtime-publication-ready rather than offline promotion-candidate?
3. Which external source adapter should be implemented first: Wiktionary/Kaikki examples, dictionary examples, or corpus retrieval?
4. Should manual leakage-safe rows remain allowed as analysis artifacts, or should all future promotion-candidate rows come from reproducible source adapters/generators?
5. What exact runtime fallback is acceptable if sentence-transformer resources are missing?
