# Semantic Veto Product Quality Goals

Status: draft reference
Role: Draft decision log
Purpose: define the product-oriented acceptance calculus for semantic-veto work so research does not optimize for zero-harm purity when the user experience target is broader replacement usefulness
Last updated: 2026-05-06
Last verified: 2026-05-06 against current product-quality, LLM pilot, threshold-bakeoff, difficulty-stratification, sampling-design, Stage 1 materialization, Stage 1 representative scoring, and strict veto-only validation outputs
Source-of-truth: this document is planning guidance only; runtime truth remains in code, test inputs, generated outputs, and the semantic-veto registry

## Product Frame

Semantic veto is not the whole product. It is a subprocess that should make
browser replacement feel smarter.

The product goal is:

```text
When a replacement is good in context, usually show it.
When a replacement is bad in context, hide a useful share of it.
```

This is not a specialized safety product that must eliminate every false allow.
False allows are tolerable if they are uncommon and the system still preserves
most good replacements.

## Primary Product Metrics

Use these terms for product evaluation:

```text
positive = the replacement is contextually good
negative = the replacement is contextually bad
allow = the user sees the replacement
abstain = the user does not see the replacement
```

Primary rates:

```text
positive_allow_rate = allowed positives / all positives
positive_abstain_rate = abstained positives / all positives
negative_abstain_rate = abstained negatives / all negatives
negative_allow_rate = allowed negatives / all negatives
```

Initial product target:

```text
positive_allow_rate >= 80%
negative_abstain_rate >= 50%
```

Equivalent error budget:

```text
positive_abstain_rate <= 20%
negative_allow_rate <= 50%
```

These are not final contractual thresholds. They are the right first milestone
because they match the intended user experience better than a zero-harm gate.

## Secondary Product Score

Track a utility score so tradeoffs are explicit:

```text
utility =
  +1.0 * positive_allow
  -0.4 * positive_abstain
  +0.8 * negative_abstain
  -0.6 * negative_allow
```

The weights can change later. The key principle is stable:

- showing good replacements is strongly valuable,
- hiding bad replacements is valuable,
- missing a good replacement is mildly bad,
- allowing a bad replacement is annoying but tolerable.

Every product-quality report should compare this score against:

- lexical baseline: allow everything,
- abstain-all baseline: hide everything,
- current runtime or current research candidate, depending on lane.

## Evaluation Lanes

### Stress Lane

Purpose:

```text
Keep known hard semantic-veto classes visible.
```

Examples:

- current wave7 active/shadow and phrase/no-winner suites,
- residual blocker probes,
- current-evidence ceiling and upstream-gap reports.

Interpretation:

- stress results are not representative browsing estimates,
- failures should route research work,
- stress zero-harm is useful as a diagnostic but not the main product gate.

### Representative Browsing Lane

Purpose:

```text
Estimate what users will feel during normal browsing.
```

This lane needs sampled positive and negative contexts across ordinary target
vocabulary, not only adversarial residuals.

First milestone:

```text
positive_allow_rate >= 80%
negative_abstain_rate >= 50%
utility beats lexical baseline
```

Break down by:

- POS,
- frequency band,
- ambiguity class,
- active/shadow versus phrase/no-winner,
- manual versus generated labels,
- source family.

### LLM-Expanded Evaluation Lane

Purpose:

```text
Use LLM generation budget to create enough labeled breadth to estimate product quality.
```

Use LLMs primarily for data generation and evidence generation, not direct
runtime decisions.

For each source phrase or replacement family, generate:

- positive contexts where the replacement should be shown,
- negative contexts where the replacement should be hidden,
- phrase/no-winner contexts where neither ordinary active nor shadow sense
  should drive replacement.

Each generated row should include:

- sentence,
- trigger phrase,
- candidate replacement,
- gold decision: `allow` or `abstain`,
- gold reason,
- active sense,
- negative sense or no-winner reason,
- difficulty tags.

Admission filters must reject:

- label-leaking rows,
- rows containing Spanish target lemmas,
- unnatural contexts,
- duplicates,
- rows tuned on the locked evaluation split.

The LLM lane counts toward acceptance only after it runs through generation,
admission, leakage checks, sense checks, scoring, and downstream validation.

## Current Rough Read

Current wave7 phrase-control triage is a stress slice, not representative
browsing. Still, it is useful as a sanity read under product metrics:

```text
positive cases: 16
negative cases: 32

current positive allows: 14 / 16 = 87.5%
current positive abstains: 2 / 16 = 12.5%
current negative abstains: 25 / 32 = 78.1%
current negative allows: 7 / 32 = 21.9%
```

Under the first product target, this stress read is promising. It does not
prove production readiness because:

- the candidate is still research-only,
- the slice is small and intentionally hard,
- it is not representative browsing,
- LLM-expanded evaluation has not been measured,
- runtime promotion still requires separate implementation and validation.

## Relationship To Bound Reports

The current bound reports remain useful, but their role changes:

- `semantic_veto_bound_ladder_wave7_residuals`: identifies the measured floor,
  score-visible residuals, and unmeasured LLM lane.
- `semantic_veto_current_evidence_ceiling_wave7`: tests whether optimistic
  current-score headroom survives general guard sweeps.
- `semantic_veto_upstream_gap_audit_wave7`: routes residuals toward evidence,
  scoring, phrase/no-winner guard, or LLM-pipeline work.

These reports answer why a stress slice fails. Product-quality reports answer
whether the system is good enough for the user experience.

## Acceptance Milestones

### Milestone 1: Product Harness Exists

Implement a product-quality harness that computes:

- positive allow rate,
- positive abstain rate,
- negative abstain rate,
- negative allow rate,
- utility score,
- delta versus lexical baseline,
- delta versus abstain-all baseline,
- stress versus representative lane split.

Likely artifacts:

```text
scripts/testing/semantic_veto_product_quality_en_es.py
docs/test_inputs/semantic_veto_product_quality_policy_en_es.json
docs/test_outputs/semantic_veto_product_quality_en_es_latest.json
docs/test_outputs/semantic_veto_product_quality_en_es_latest.md
```

Current status: implemented for the wave7 stress lane plus the filled Stage 1
representative proxy.

Run:

```bash
python3 scripts/testing/semantic_veto_product_quality_en_es.py \
  --policy-json docs/test_inputs/semantic_veto_product_quality_policy_en_es.json \
  --json-out docs/test_outputs/semantic_veto_product_quality_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_quality_en_es_latest.md
```

The current report includes both the wave7 stress lane and the filled Stage 1
representative proxy. Its overall read is:

```text
decision: product_target_missed
cases: 168
positive_allow_rate: 39.1%
negative_abstain_rate: 92.9%
utility: 79.6
lexical_allow_all_utility: 9.6
abstain_all_utility: 51.6
```

Interpretation:

- the current stress lane clears the first product target on known hard cases,
- the filled Stage 1 representative proxy fails the first product target
  because positive allow is only `24.5%` in that lane,
- the combined measured lanes beat lexical allow-all and abstain-all baselines
  under the current utility weights,
- the immediate blocker is positive allow on broader active examples, not
  negative abstain.

### Milestone 1a: Sampling Expansion Stage 1 Exists

The scientific sampling design has now produced its first operational
materialization:

```text
scripts/testing/semantic_veto_sampling_stage1_materialization_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json
docs/test_inputs/semantic_veto_representative_gap_rows_en_es.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_frame_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_materialization_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_materialization_en_es_latest.md
```

Current read:

```text
representative locked target: 120
representative rows available: 120
base v10 representative proxy rows: 95
corpus-like representative gap rows added: 25
representative shortfall: 0
P0 manual discovery cases: 20
P0 cells: 5
runtime policy change: none
```

The representative shortfall is now tracked by an explicit gap plan:

```text
docs/test_inputs/semantic_veto_representative_gap_source_manifest_en_es.json
scripts/testing/semantic_veto_representative_gap_plan_en_es.py
docs/test_outputs/semantic_veto_representative_gap_plan_en_es_latest.json
docs/test_outputs/semantic_veto_representative_gap_plan_en_es_latest.md
```

Current gap-plan read:

```text
open primary collection slots: 0
corpus-like app-candidate rows materialized: 25
observed runtime/context rows materialized: 0
LLM locked proxy rows available: 16
LLM proxy rows count toward primary target: false
```

Interpretation:

- the representative lane is filled to the 120-row Stage 1 target without
  padding it with targeted failure-shaped rows,
- the 25-row gap is filled with corpus-like primary proxy rows; these still
  need human review and are not observed browser logs,
- the P0 manual packet is discovery data for checking cell contracts before LLM
  generation, not product-quality evidence,
- first P0 discovery scoring confirms the targeted cells are meaningful:
  TF-IDF protects the phrase/no-winner rows but misses all positive `help`
  rows, while sentence-transformer scoring recovers some positives but leaks
  four no-winner rows,
- filled-frame scoring now exists and drives the current product-quality
  representative lane.

### Milestone 1a.1: Filled Representative Frame Scoring Exists

The filled 120-row representative frame is now converted into a normal
sentence-veto dataset and scored with the same current-policy configuration as
the v10 representative proxy:

```text
scripts/testing/semantic_veto_sampling_stage1_representative_scoring_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_scoring_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_scoring_en_es_latest.md
```

Current score:

```text
cases: 120
positive cases: 53
negative cases: 67
predicted replace cases: 13
positive_allow_rate: 24.5%
negative_abstain_rate: 100.0%
harmful replacements: 0
false abstains: 40
context sources: 95 existing v10 proxy, 25 corpus-like gap rows
review states: 95 reviewed/existing, 25 agent_draft_human_review_pending
runtime policy change: none
```

Interpretation:

- the old current policy is very conservative on the filled representative
  frame,
- it hides all labeled negatives in this proxy lane, but misses most good
  replacements,
- the 25 corpus-like gap rows did not create a new harmful-replacement problem;
  they mostly reinforce the known false-abstain problem,
- this result should update product-quality estimates, but it still cannot
  serve as promotion evidence until the 25 gap rows are human-reviewed and an
  observed or LLM-expanded locked lane confirms the same shape.

### Milestone 1b: Product Objective Bakeoff Exists

The historical scorer and decision-rule sweeps must be re-ranked under the
same product criteria before we call any final YES/NO rule "preferred" for the
current product goal.

Artifacts:

```text
scripts/testing/semantic_veto_product_objective_bakeoff_en_es.py
docs/test_outputs/semantic_veto_product_objective_bakeoff_en_es_latest.json
docs/test_outputs/semantic_veto_product_objective_bakeoff_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_objective_bakeoff_en_es.py \
  --policy-json docs/test_inputs/semantic_veto_product_quality_policy_en_es.json \
  --json-out docs/test_outputs/semantic_veto_product_objective_bakeoff_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_objective_bakeoff_en_es_latest.md
```

Current read:

```text
sources: sentence-veto sweep plus decision-rule matrix
rows ranked: 3098
target-pass rows: 0
best product-rank row: control_st_masked_all_margin_phrase_override
best product-rank positive_allow_rate: 68.4%
best product-rank negative_abstain_rate: 98.2%
closest target-shape row: tfidf raw_sentence all_evidence_text with active rescue
closest target-shape positive_allow_rate: 81.6%
closest target-shape negative_abstain_rate: 49.1%
```

Interpretation:

- the current scorer family is a useful baseline, not proven best for the new
  product acceptance target,
- historical rows contain near-target permissive shapes, but none clears the
  configured positive/negative pair,
- next scoring research should inspect near-target rows before treating the
  old harm-averse rank as the product rank.

### Milestone 1c: Veto-Only Product Probe Exists

The product stance is now:

```text
allow by default;
abstain only when the word is clearly a different sense or a phrase/no-winner
blocker is visible.
```

This treats semantic veto as a bad-replacement detector, not a second full
semantic admission gate.

Artifacts:

```text
scripts/testing/semantic_veto_veto_only_probe_en_es.py
docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_veto_only_probe_en_es.py \
  --policy-json docs/test_inputs/semantic_veto_product_quality_policy_en_es.json \
  --matrix-json docs/test_outputs/semantic_decision_rule_matrix_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.md
```

Current read:

```text
matrix case traces read: 2470
policy rows evaluated: 5148
target-pass rows: 74
best row: control_st_masked_all_margin_phrase_override replayed as allow_default_shadow_veto
best positive_allow_rate: 81.6%
best negative_abstain_rate: 94.7%
best utility: 69.6
```

Interpretation:

- this is the first current product-target pass on the frozen v10 matrix traces,
- the winning shape is not "prove active sense"; it is "allow unless shadow lead
  is visible",
- this result is research-only until validated on stress lanes and broader
  representative or LLM-expanded heldout data,
- the most important failure samples are remaining negative allows where the
  shadow lead is just below the blocker threshold, plus positive abstains where
  shadow evidence barely outranks active evidence.

### Milestone 1d: Veto-Only Stress Validation Exists

The v10 matrix pass must not stand alone. The same allow-by-default blocker
family is now replayed over the current wave7 phrase-control triage stress
reports.

Artifacts:

```text
scripts/testing/semantic_veto_veto_only_validation_en_es.py
docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_veto_only_validation_en_es.py \
  --policy-json docs/test_inputs/semantic_veto_product_quality_policy_en_es.json \
  --json-out docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.md
```

Current read:

```text
stress reports read: 2
stress cases read: 48
policy rows evaluated: 540
target-pass rows: 100
strict source-pass rows: 12
best row: shadow_or_phrase_score, shadow_lead_min=0.05, shadow_score_min=0.0
best positive_allow_rate: 81.2%
best negative_abstain_rate: 75.0%
best utility: 26.2
```

The exact v10 winner shape (`shadow_or_phrase`, `shadow_lead_min=0.02`) does
not pass this stress validation because positive allow drops to `68.8%`. The
stress pass requires the existing phrase-control score as an additional blocker
and a less aggressive shadow-lead threshold.

Interpretation:

- the allow-by-default product framing is not limited to v10; it also finds a
  strict source-passing shape on the wave7 stress reports,
- the best shared concept is stable, but the exact blocker threshold is not yet
  frozen,
- before runtime promotion, we need a unified candidate-selection report that
  compares v10, stress, and a broader representative lane under the same
  blocker contract.

### Milestone 1e: Shared Veto-Only Candidate Selection Exists

The v10 probe and stress validation are now joined by shared blocker
parameters, so we can see whether a single candidate shape survives both.

Artifacts:

```text
scripts/testing/semantic_veto_veto_only_candidate_selection_en_es.py
docs/test_outputs/semantic_veto_veto_only_candidate_selection_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_candidate_selection_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_veto_only_candidate_selection_en_es.py \
  --probe-json docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.json \
  --validation-json docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_veto_only_candidate_selection_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_veto_only_candidate_selection_en_es_latest.md
```

Current leading shared candidate:

```text
base scorer/config: control_st_masked_all_margin_phrase_override
runtime shape: allow_default_shadow_veto
phrase_mode: shadow_or_phrase_score
shadow_lead_min: 0.05
shadow_score_min: 0.0
v10 positive_allow_rate: 97.4%
v10 negative_abstain_rate: 80.7%
stress positive_allow_rate: 81.2%
stress negative_abstain_rate: 75.0%
minimum measured positive_allow_rate: 81.2%
minimum measured negative_abstain_rate: 75.0%
```

Interpretation:

- this is now the leading research candidate family,
- it passes both frozen v10 matrix traces and current wave7 stress validation,
- it still needs a broader representative or LLM-expanded locked lane before
  production promotion,
- implementation should preserve the product framing: default allow, block only
  on clear shadow or phrase-control evidence.

### Milestone 1f: Filled-Representative Veto-Only Validation Exists

The same validation harness is now rerun with the filled Stage 1 representative
scoring report added to the wave7 stress reports. The report distinguishes
aggregate target passes from strict source-by-source passes so a candidate
cannot look promotable only because one lane averages out another lane's
failure.

Artifacts:

```text
docs/test_outputs/semantic_veto_veto_only_validation_stage1_representative_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_validation_stage1_representative_en_es_latest.md
docs/test_outputs/semantic_veto_veto_only_candidate_selection_stage1_representative_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_candidate_selection_stage1_representative_en_es_latest.md
```

Current validation read:

```text
input case rows: 168
policy rows evaluated: 540
aggregate target-pass rows: 16
strict source-pass rows: 0
decision: veto_only_validation_overall_product_target_pass_source_failures
best aggregate row: shadow_or_phrase_score, shadow_lead_min=0.02, shadow_score_min=0.0
overall positive_allow_rate: 88.4%
overall negative_abstain_rate: 53.5%
filled representative source: positive_allow_rate 100.0%, negative_abstain_rate 34.3%
active/shadow stress source: positive_allow_rate 50.0%, negative_abstain_rate 100.0%
phrase/no-winner stress source: negative_abstain_rate 87.5%
```

Current shared-candidate read with the v10 probe:

```text
matched parameter rows: 297
passing shared rows: 0
decision: veto_only_shared_candidate_not_found
```

Interpretation:

- the allow-by-default blocker family still looks promising for product
  direction, but it is not yet a promotable shared candidate,
- aggregate passes are not enough because the filled representative source
  leaks too many negatives under the high-positive-allow settings,
- conservative settings protect representative negatives but fall below the
  positive-allow target,
- next work should search for blocker signals that separate representative
  negatives from positives, instead of only sliding one shared shadow threshold.

### Milestone 2: Existing Data Product Read

Run the harness on existing stress and available sentence-veto data before
spending more generation budget.

Success:

```text
positive_allow_rate >= 80%
negative_abstain_rate >= 50%
utility beats lexical baseline on at least one meaningful locked lane
```

Failure is still useful if it tells us which lane blocks product quality.

### Milestone 2a: LLM Pilot Admission Preflight Exists

Before spending generation budget, freeze the current candidate, planned
families, row contract, admission filters, and discovery versus locked-eval
split policy.

Artifacts:

```text
scripts/testing/semantic_veto_llm_pilot_admission_en_es.py
scripts/testing/semantic_veto_llm_pilot_generation_requests_en_es.py
docs/test_inputs/semantic_veto_llm_pilot_plan_en_es.json
docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.md
docs/test_outputs/semantic_veto_llm_pilot_generation_requests_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_generation_requests_en_es_latest.md
```

Run the no-spend preflight:

```bash
python3 scripts/testing/semantic_veto_llm_pilot_admission_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.md \
  --fail-on-review
```

Render the no-spend request packet:

```bash
python3 scripts/testing/semantic_veto_llm_pilot_generation_requests_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_pilot_generation_requests_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_pilot_generation_requests_en_es_latest.md \
  --fail-on-review
```

Current read:

```text
decision: ready_for_generation
pilot families: 12
planned rows: 72
planned positive_active rows: 36
planned shadow_negative rows: 24
planned phrase_no_winner rows: 12
request packet decision: ready_for_llm_batch_execution
rendered requests: 72
estimated input tokens: 32020
expected output-token budget: 8640
runtime_policy_change: none
source_evidence_promotion: none
```

Interpretation:

- this is a process gate, not a quality win by itself,
- generated rows admitted here are evaluation rows, not source evidence,
- the pilot explicitly covers phrasing axes such as word order, trigger
  position, context distance, morphology, register, and difficulty,
- discovery rows can be used to diagnose and choose thresholds, but locked-eval
  rows cannot,
- the request packet is not generated data and does not call an LLM,
- after rows are generated, the admission harness must reject leakage,
  duplicate rows, broken labels, missing trigger context, family/type coverage
  gaps, and rows that do not match the frozen request packet before any
  candidate-scoring claim.

### Milestone 2b: LLM Pilot Generation and Admission Completed

The bounded pilot generation pass has now been executed and admitted as
evaluation data. It is still not source evidence and does not change runtime
policy.

Artifacts:

```text
scripts/testing/semantic_veto_llm_pilot_generation_run_en_es.py
scripts/testing/semantic_veto_llm_pilot_generated_rows_merge_en_es.py
docs/test_outputs/semantic_veto_llm_pilot_generation_run_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_generation_run_en_es_latest.md
docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.md
docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_admission_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_llm_pilot_batches/
```

Current read:

```text
generation run status: ok
generated rows accepted by runner: 72 / 72
generated rows assembled after targeted repairs: 72 / 72
admission status: ok
admission decision: admitted_for_scoring
admitted rows: 72
rejected rows: 0
request-aligned expected rows: 72 / 72
discovery rows: 56
locked-eval rows: 16
runtime_policy_change: none
source_evidence_promotion: none
```

Repair note:

- The first full live run produced 71 valid rows and one malformed JSON row
  missing `candidate_replacement`; the run harness now has an explicit
  `--retry-invalid-outputs` resume path.
- Two generated phrase/no-winner rows used inflected target forms that would
  not be browser replacements (`banked`, `Branching`); admission rejected them
  for missing the exact trigger token.
- The final admitted payload was assembled from the immutable full batch plus
  targeted repair batches, with the merge report recording every replacement.

Interpretation:

- this is a real process milestone: the LLM evaluation lane now has 72 admitted
  rows instead of only a plan,
- it is not yet an accuracy milestone because the admitted rows still need to
  be scored with the frozen candidate,
- source evidence remains the likely next blocker: these rows can evaluate
  decisions, but they must not be recycled as source evidence for those same
  decisions,
- discovery rows may diagnose or tune future candidate choices; locked-eval
  rows must remain untouched by threshold selection.

### Milestone 2c: LLM Pilot Scored With Independent Source Evidence

The admitted pilot rows are now scored against the frozen candidate using the
expanded reviewed source-evidence batch as independent active, shadow, and
phrase-control prototypes. The pilot rows remain evaluation data only.

Artifacts:

```text
scripts/testing/semantic_veto_llm_pilot_scoring_en_es.py
scripts/testing/semantic_veto_llm_pilot_failure_review_en_es.py
scripts/testing/semantic_veto_llm_pilot_data_comparison_en_es.py
scripts/testing/semantic_veto_llm_threshold_bakeoff_en_es.py
docs/test_outputs/semantic_veto_llm_pilot_scoring_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_scoring_en_es_latest.md
docs/test_outputs/semantic_veto_llm_pilot_failure_review_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_failure_review_en_es_latest.md
docs/test_outputs/semantic_veto_llm_pilot_data_comparison_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_data_comparison_en_es_latest.md
docs/test_outputs/semantic_veto_llm_threshold_bakeoff_en_es_latest.json
docs/test_outputs/semantic_veto_llm_threshold_bakeoff_en_es_latest.md
```

Run the scoring lane:

```bash
python3 scripts/testing/semantic_veto_llm_pilot_scoring_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_pilot_scoring_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_pilot_scoring_en_es_latest.md \
  --fail-on-review
```

Review the scored-pilot failures:

```bash
python3 scripts/testing/semantic_veto_llm_pilot_failure_review_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_pilot_failure_review_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_pilot_failure_review_en_es_latest.md \
  --fail-on-review
```

Compare failed LLM pilot rows to same-family manual rows and source evidence:

```bash
python3 scripts/testing/semantic_veto_llm_pilot_data_comparison_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_pilot_data_comparison_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_pilot_data_comparison_en_es_latest.md \
  --fail-on-review
```

Run the separate shadow/phrase threshold bakeoff. Candidate selection is limited
to `llm_discovery`; locked-eval and manual/stress lanes are reported after
selection and must not be used as if they were the discovery lane.

```bash
python3 scripts/testing/semantic_veto_llm_threshold_bakeoff_en_es.py \
  --json-out docs/test_outputs/semantic_veto_llm_threshold_bakeoff_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_llm_threshold_bakeoff_en_es_latest.md \
  --fail-on-review
```

Current read:

```text
status: ok
decision: frozen_candidate_product_target_passed_on_llm_pilot
scored rows: 72 / 72
scoreable families: 12 / 12
source evidence: expanded reviewed v10 source batch, 95 rows, 19 complete families
evaluation row id overlap with source evidence: 0
context text exact overlap with source evidence: 0
overall positive_allow_rate: 88.89%
overall negative_abstain_rate: 52.78%
overall utility: 35.4
discovery positive_allow_rate / negative_abstain_rate: 84.62% / 50.00%
locked_eval positive_allow_rate / negative_abstain_rate: 100.00% / 66.67%
failure review: 21 failures
positive_allow vs manual/stress best: +7.6pp
negative_abstain vs manual/stress best: -22.2pp
shadow_negative_abstain vs manual active/shadow source: -29.2pp
phrase_no_winner_abstain vs manual phrase source: -20.8pp
data comparison failed rows: 21
data comparison manual same-class rows referenced: 35
data comparison diagnosis confidence: high 16, medium 5
data comparison repeated notes:
  same-family manual matching rows passed under control: 18
  scorer chose active evidence over blocker: 12
  surface-pattern winner differed from score winner: 15
  phrase surface visible but not weighted enough: 3
threshold bakeoff rows: 121
threshold bakeoff selection lane: LLM discovery only
threshold bakeoff selected discovery candidate:
  shadow_lead_min=-0.05, phrase_lead_min=-0.025
  LLM discovery: 80.8% positive allow / 83.3% negative abstain
  LLM locked-eval: 80.0% positive allow / 83.3% negative abstain
  manual/stress: 12.5% positive allow / 100.0% negative abstain
threshold bakeoff all-lane advisory:
  shadow_lead_min=0.05, phrase_lead_min=0.075
  LLM discovery: 96.2% positive allow / 50.0% negative abstain
  LLM locked-eval: 100.0% positive allow / 66.7% negative abstain
  manual/stress: 81.2% positive allow / 68.8% negative abstain
incumbent:
  shadow_lead_min=0.05, phrase_lead_min=0.05
  LLM discovery: 84.6% positive allow / 50.0% negative abstain
  LLM locked-eval: 100.0% positive allow / 66.7% negative abstain
  manual/stress: 81.2% positive allow / 75.0% negative abstain
```

Interpretation:

- this is a real accuracy milestone for the pilot lane, not a production claim,
- it is a clean result for the current product acceptance shape because both
  discovery and locked-eval splits meet the 80% positive-allow and 50%
  negative-abstain targets,
- it does not prove broad browsing quality because the pilot is small and
  LLM-generated,
- the remaining weak class is still visible: phrase/no-winner rows only reached
  `5 / 12` abstains, so phrase/no-winner coverage should stay separate from
  ordinary active-vs-shadow scoring,
- the pilot is not weaker across the board: positive allow is higher than the
  current manual/stress comparator, but negative blocking is much weaker,
- the largest failure classes are active score dominating shadow-negative rows
  and phrase/no-winner rows where phrase-control evidence does not dominate the
  best ordinary sense,
- the data-level comparison makes the weakness more concrete: many generated
  failures are not mirror images of the manual rows, and several phrase failures
  show visible word-order evidence that still loses the score contest,
- a simple lower shadow threshold is not safe: the LLM-discovery-selected
  aggressive shadow candidate blocks nearly every manual/stress positive,
- the only threshold-only direction that currently looks plausible is not
  harsher shadow blocking, but a small phrase-threshold separation
  (`phrase_lead_min=0.075`) that improves LLM positive allow while still passing
  the combined stress target; it weakens phrase/no-winner stress blocking, so it
  remains advisory rather than promoted,
- no runtime policy or source evidence was promoted by this result.

### Milestone 3: LLM-Expanded Evaluation

Use LLM budget to generate broader locked evaluation data.

Before spending broadly, use the difficulty-stratification research plan to
test whether failure risk is concentrated in high-frequency / high-polysemy
source triggers:

```text
docs/rulegen/semantic_veto_difficulty_stratification_research_plan.md
```

That plan keeps three product axes separate:

```text
learner_value: user/profile/topic usefulness
learner_difficulty: Spanish target level for SRS admission
veto_decision_difficulty: English trigger ambiguity and replacement risk
```

The expected first no-spend artifact is a rank-bin report that joins existing
LLM/manual/stress rows to frequency, source-coverage, and ambiguity metadata
before deciding whether expensive LLM generation should focus on the first
500-1000 English triggers.

That first artifact now exists.

Artifacts:

```text
scripts/testing/semantic_veto_difficulty_stratification_en_es.py
docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.json
docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_difficulty_stratification_en_es.py \
  --json-out docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.md \
  --fail-on-review
```

Current no-spend read:

```text
status: ok
decision: difficulty_stratification_baseline_established
case rows: 215
policy/product rows: 143
LLM pilot rows: 72
families: 35
triggers: 35
overall positive_allow_rate: 65.6%
overall negative_abstain_rate: 80.8%
overall utility: 113.0
English source-trigger rank coverage: 73 / 215 = 34.0%
Spanish target-rank coverage: 15 / 215 = 7.0%
known top-1000 English trigger failures: 6 / 25 rows
10+ WordNet-sense failures: 9 / 48 rows
```

Interpretation:

- this is a real research-infrastructure milestone, not an accuracy promotion,
- the first rank curve is not yet strong enough to answer the beginner-versus
  advanced-word hypothesis because local frequency coverage is sparse,
- the report already gives actionable generation priorities: high-failure
  triggers such as `check`, `order`, `plant`, `report`, and `play` should stay
  in the next LLM-evaluation budget even when their frequency-rank metadata is
  currently missing,
- source-trigger rank, Spanish target rank, declared LLM ambiguity class,
  WordNet sense count, translation fan-out, and score-surface bins are now
  reported separately,
- target difficulty for SRS cannot yet rely on the installed Spanish frequency
  pack alone; the next data layer needs better target-lemma normalization or a
  denser target-frequency/level source,
- the report is self-contained as a no-spend measurement harness, but broad
  success is not self-contained inside this artifact; it feeds the next LLM
  budget planner and future representative evaluation.

The next methodology step is also materialized as a small-group pilot:

```text
scripts/testing/semantic_veto_heuristic_group_pilot_en_es.py
docs/test_outputs/semantic_veto_heuristic_group_pilot_en_es_latest.json
docs/test_outputs/semantic_veto_heuristic_group_pilot_en_es_latest.md
```

Current heuristic-group pilot read:

```text
candidate pool: 4112
selected triggers: 29
manual review rows: 29
primary groups: 6
sentinel group: 1
case slots per trigger: 5
```

The six primary groups are selected from pre-outcome frequency and WordNet
metadata while excluding current measured triggers. The measured missing-rank
high-failure group is deliberately outcome-informed and exists only as a
regression anchor, not as proof that the frequency/polysemy heuristic works.

That small-group pilot now has a first draft authoring and scoring lane:

```text
scripts/testing/semantic_veto_heuristic_group_case_authoring_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json
docs/test_outputs/semantic_veto_heuristic_group_case_authoring_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_sentence_veto_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_sentence_veto_st_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_veto_only_validation_st_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_difficulty_surface_en_es_latest.md
```

Current first draft:

```text
authored triggers: 29
dataset cases: 121
positive_active cases: 58
shadow_negative cases: 34
phrase_no_winner cases: 29
manual state: agent_draft_human_review_pending
```

First diagnostic scoring read:

```text
tfidf_cosine: positive recall 39.7%, harmful replace 3.2%
sentence_transformer_cosine: positive recall 89.7%, harmful replace 33.3%
veto-only replay over ST rows: positive allow 100.0%, negative abstain 47.6%
```

The useful signal is not "this passes." It does not. The useful signal is that
the lane now exposes the target tradeoff at the word-group level: high-positive
allow is reachable on the draft groups, but no-winner and phrase-like negatives
still leak enough to miss the `>= 50%` negative-abstain product target on the
frozen veto-only replay. The low-polysemy controls also show that easy words
should not be forced into fake shadow-negative cases; their evaluation mix is
positive plus mention/phrase no-winner unless a real alternate sense exists.

The heuristic difficulty surface makes that shape explicit:

```text
sentence_transformer_cosine:
  positive_allow_difficulty: 10.3%
  shadow_negative_difficulty: 5.9%
  phrase_no_winner_difficulty: 65.5%

tfidf_cosine:
  positive_allow_difficulty: 60.3%
  shadow_negative_difficulty: 0.0%
  phrase_no_winner_difficulty: 6.9%
```

The current frequency/polysemy formula is therefore only a control. On this
draft lane it does not explain the sentence-transformer failure surface well;
phrase/no-winner risk is the dominant specific difficulty. The next expansion
budget should target phrase/no-winner cells first, and should keep low-polysemy
controls as phrase/mention probes rather than manufacturing fake shadow senses.

The planning question is now more precise than "which words are difficult."
For product quality and spend control, the useful function is:

```text
which cells deserve more data =
  expected exposure
  * product impact
  * current uncertainty
  * predicted failure risk
  * likely fixability from better evidence or more rows
  * current coverage gap
```

The difficulty plan therefore treats signals and formula shape separately. The
same source-rank, polysemy, case-shape, phrase-order, and score-margin signals
must be tested under multiple mathematically distinct compositions: linear,
normalized dot product, multiplicative interaction, max-risk, gated
per-failure-class formulas, logistic scoring, small monotone rule tables, and
rank aggregation. A formula only earns trust if it predicts observed
difficulty on discovery data and keeps that ordering on locked evaluation; it
does not become a runtime decision policy by itself.

That bakeoff now exists:

```text
docs/test_inputs/semantic_veto_formula_shape_bakeoff_en_es.json
scripts/testing/semantic_veto_formula_shape_bakeoff_en_es.py
docs/test_outputs/semantic_veto_formula_shape_bakeoff_en_es_latest.md
```

Current read:

```text
cells: 48
primary cells: 42
formula families: 9
parameter sweeps: 2
primary all-scorer leader: monotone_rule_table
primary all-scorer Spearman: 0.3056
primary all-scorer top-k lift: 1.2632
selected gated sweep Spearman: 0.2599
selected gated sweep top-k lift: 1.5918
selected gated sweep Brier: 0.0915
weight-surface analysis: implemented
sampled maxima shape: sharp_sampled_peak for both linear and gated sweeps
```

This is useful but not a product-quality claim. It says formula shape matters
enough to keep testing, and the continuous sweep can slide weights
programmatically instead of relying only on fixed hand weights. It gives a more
disciplined spend queue for manual and LLM rows. It does not prove that the
current heuristic-group draft data is representative browsing data, and it
does not promote runtime policy.

The curve analysis strengthens the next-data argument: the apparent maxima are
sharp, so the right use is to map where the measured difficulty curve changes,
not to treat this draft lane as a coefficient optimizer. The next move is to
expand the high-priority cells, especially phrase/no-winner underfilled
coverage, order-sensitive mention rows, shadow near ties, and positive-active
low-score rows, then rerun the surface analysis to see whether the same shapes
or broad plateaus survive.

The current curve-guided expansion report turns that into an explicit first
queue: 24 cells, 5 P0 cells, 16 P1 cells, 3 P2 cells, and a first-wave budget of
74 manual discovery rows, 258 LLM discovery rows, and 129 locked-eval rows if
the whole queue is pursued. That is a planning artifact, not a requirement to
generate all rows immediately.

The scientific sampling design now wraps that targeted queue in a broader
anti-bias expansion plan:

```text
representative random product lane: 120 locked rows
stratified difficulty-surface lane: 144 rows
targeted P0 curve-mechanism lane: 140 rows
negative/leakage control lane: 36 rows
total planned rows: 440
locked-eval share: 50.0%
```

This prevents the project from accidentally proving only the current theory.
The representative random lane is the product-quality estimator. The
stratified lane draws the difficulty surface. The targeted P0 lane tests the
strongest mechanisms from the curve report. The control lane checks whether
generation or scoring is leaking labels. Promotion claims still require the
representative locked lane; targeted rows can explain failures but cannot
estimate their real-world frequency.

Success:

```text
positive_allow_rate >= 80%
negative_abstain_rate >= 50%
utility beats lexical baseline
results remain stable by POS, frequency band, ambiguity class, and source family
```

This is the first milestone that can support a serious product-quality claim
across broader `en-es`.

### Milestone 4: Runtime Promotion Candidate

Only after the product harness and LLM-expanded evaluation pass should runtime
promotion be considered.

Promotion still needs:

- runtime-compatible policy implementation,
- runtime-path tests,
- product-quality report,
- stress-lane report,
- clear rollback or fallback policy.

## Operating Rule

Every next semantic-veto task should answer at least one of these:

- Did product utility improve?
- Did positive allow stay high?
- Did negative abstain improve enough to matter?
- Did the result beat lexical baseline on a locked lane?
- Did LLM-generated data improve product metrics after admission and filtering?
- Did a stress failure explain a product risk?

If a task does not answer one of those, it is probably not the right next task.
