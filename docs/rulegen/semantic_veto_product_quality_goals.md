# Semantic Veto Product Quality Goals

Status: draft reference
Role: Draft decision log
Purpose: define the product-oriented acceptance calculus for semantic-veto work so research does not optimize for zero-harm purity when the user experience target is broader replacement usefulness
Last updated: 2026-05-10
Last verified: 2026-05-10 against current product-quality, LLM pilot, threshold-bakeoff, difficulty-stratification, sampling-design, Stage 1 materialization, Stage 1 representative scoring, strict veto-only validation outputs, the product-scope algorithm bakeoff, the corrected product-scope band/formula rerun, the product-scope LLM allocation pilot generation/admission/contribution artifacts, the narrow `gpt-5.5` high-need shadow probe, and the active-only scale tranche through combined 49-family helper smoke plus live-page scan
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

### Milestone 1g: Product-Scope Algorithm Parameter Bakeoff Exists

The full-family repaired dataset previously included synthetic rows like:

```text
The dashboard listed X as an internal project code.
```

Those rows are useful diagnostics for label-preservation behavior, but they are
not product errors under the current browser soft-assist stance. It is acceptable
for visible labels to be replaced; the product goal is to avoid clearly wrong
ordinary-context replacements while preserving most good replacements.

The corrected first step is therefore parameter-first:

1. filter diagnostic label-preservation rows out of the evaluation denominator,
2. sweep algorithm parameters,
3. record the candidate peaks,
4. only then carry selected peaks into band and heuristic allocation tests.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_filter_en_es.py
scripts/testing/semantic_veto_product_scope_algorithm_bakeoff_en_es.py
docs/test_outputs/semantic_veto_product_scope_repaired_full_dataset_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_algorithm_bakeoff_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_algorithm_bakeoff_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_algorithm_bakeoff_en_es.py \
  --fail-on-review
```

Current read:

```text
original repaired-full rows: 189
product-scope rows retained: 140
diagnostic label rows excluded: 49
candidate rows evaluated: 1056
product target-pass rows: 460
best row: sentence_transformer_cosine, masked_sentence, all_evidence_text,
  phrase guard on, active rescue off, min_active=0.0, min_margin=-0.025
best positive_allow_rate: 92.9%
best negative_abstain_rate: 88.1%
best harmful share of visible replacements: 5.2%
best utility: 114.8
current v3-like row: 85.7% positive allow, 92.9% negative abstain,
  3.5% harmful share, target pass
tfidf v2-like row: 5.1% positive allow, 97.6% negative abstain, target fail
```

Interpretation:

- the label-row correction materially changes the reading: sentence-transformer
  rows that looked harmed by label preservation now look product-promising on
  ordinary repaired-full cases,
- `min_active_score` is not the metric; it is one swept parameter inside the
  decision rule,
- the repeated top rows are expected because all active scores in that structural
  row are above the low active-score grid values, so the margin and phrase guard
  dominate,
- the corrected algorithm peaks are discovery research, not runtime promotion,
- the next methodological step is to rerun band/heuristic allocation on the
  corrected product-scope denominator using at least the best utility row, a
  safer high-negative-abstain row, the current v3-like row, and a TF-IDF
  comparator.

### Milestone 1h: Product-Scope Candidate Surface And Band Formula Rerun Exist

After the parameter-first bakeoff, the next step was to carry representative
candidate peaks into the family-ranking heuristic sweep. This prevents band or
LLM-allocation conclusions from being based on the old label-preservation
denominator or on only one hand-picked threshold.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_selected_candidate_surface_en_es.py
docs/test_outputs/semantic_veto_product_scope_selected_candidate_surface_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_selected_candidate_surface_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_formula_sweep_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_formula_sweep_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_selected_candidate_surface_en_es.py \
  --fail-on-review

python3 scripts/testing/semantic_veto_repaired_full_band_formula_sweep_en_es.py \
  --dataset-json docs/test_outputs/semantic_veto_product_scope_repaired_full_dataset_en_es_latest.json \
  --score-surface-json docs/test_outputs/semantic_veto_product_scope_selected_candidate_surface_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_formula_sweep_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_formula_sweep_en_es_latest.md \
  --fail-on-review
```

Candidate surface:

```text
candidates carried forward: 5
row results emitted: 700
best utility ST row: 92.9% positive allow, 88.1% negative abstain
safest 80% positive ST row: 83.7% positive allow, 97.6% negative abstain
current v3-like ST row: 85.7% positive allow, 92.9% negative abstain
TF-IDF best-by-scorer row: 91.8% positive allow, 50.0% negative abstain
high-recall TF-IDF comparator: 99.0% positive allow, 11.9% negative abstain
```

Band/formula rerun:

```text
families: 49
observations: 245
fixed formulas: 10
sweep formulas: 3124
split counts: discovery_proxy=175, locked_eval_proxy=70
best repeated allocation signal: shadow_coverage_only
```

Interpretation:

- frequency and WordNet-style polysemy still do not prove the user's original
  frequency-band hypothesis on this corrected lane,
- the best cheap family-ranking signal is currently whether the family already
  has shadow-competitor coverage, which is a proxy for "this trigger has real
  competing-sense structure",
- this is useful for allocating an LLM pilot because it can identify families
  where semantic evidence is likely to matter, but it is not enough to claim a
  final top-N policy for the whole language,
- the locked proxy remains small, so the right use is a small LLM evidence
  pilot with high-ranked families plus low-ranked controls, not another round
  of threshold promotion.

### Milestone 1i: Product-Scope LLM Allocation Pilot Plan Exists

The corrected band/formula rerun gives a concrete next spend question:

```text
Do high shadow-coverage families benefit more from generated evidence than
middle and low shadow-coverage controls?
```

This is the right pilot before broad generation because it tests whether the
current best cheap allocation signal actually predicts evidence value. The
pilot is still no-spend at this stage; it freezes the selection and renders the
generation request packet only.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.py
docs/test_inputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_requests_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_requests_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.py \
  --fail-on-review

python3 scripts/testing/semantic_veto_evidence_gap_generation_requests_en_es.py \
  --plan-json docs/test_inputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json \
  --json-out docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_requests_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_requests_en_es_latest.md \
  --fail-on-review
```

Current pilot:

```text
candidate families: 49
selected families: 20
high_need: 8 of 19 available families, predicted need 0.85
middle_control: all 4 available families, predicted need 0.65
low_control: 8 of 26 available families, predicted need 0.30
planned generation slots: 60
expected generated items: 100
expected output-token budget: 14,000
latest prompt id: semantic_veto_evidence_gap_generation_v7_shadow_target_correctness
estimated input tokens: 45,211
```

Selection guardrails:

- selected by the pre-outcome `shadow_coverage_only` formula,
- deterministic seed sampling inside tied bands,
- observed failures attached only after selection for diagnostics,
- same active, shadow/competitor, and no-winner generation slots for every
  selected family,
- no threshold tuning or runtime promotion from this request packet.

Interpretation:

- if high-need families improve materially more than middle and low controls,
  the shadow-coverage band is useful for prioritizing broader LLM generation,
- if improvement is flat across bands, the project should stop treating this
  heuristic as a strong allocation rule and use a simpler product-spend plan,
- the middle band is undersized in the current 49-family denominator, so it is
  included as a control but should not be overread by itself.

### Milestone 1j: Product-Scope LLM Allocation Pilot Generated

The first product-scope paid pilot has now been executed against the frozen
20-family, 60-request allocation packet. Runtime policy remains unchanged; this
is still source/admission research.

Artifacts:

```text
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_run_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_run_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generated_responses_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_admission_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_admission_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_contribution_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_contribution_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_score_contribution_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_llm_allocation_generation_score_contribution_tfidf_en_es_latest.md
```

Live generation:

```text
batch id: en-es:semantic-veto-evidence-gap-generation:product-scope-allocation-20260509-003
model: gpt-5.4-mini
prompt id: semantic_veto_evidence_gap_generation_v7_shadow_target_correctness
accepted responses: 60 / 60
accepted generated items: 90
input tokens: 41,107
output tokens: 13,405
```

Admission:

```text
status: review
admitted items: 84 / 100 expected
waived items: 10
rejected items: 4
coverage shortfall: 6

active_evidence_expansion: 40 admitted / 40 expected
no_winner_context_probe: 20 admitted / 20 expected
shadow_or_competitor_evidence_probe: 24 admitted, 10 waived, 4 rejected, 6 shortfall
```

Interpretation:

- the prompt now works well for active evidence and no-winner contexts,
- shadow generation is still the weak point because some provided or proposed
  competitor targets are not true distinct competitors,
- the remaining rejections are useful signal, not a formatting issue: examples
  include `begin -> comenzar` proposing near-synonym `empezar`, and
  `billow -> oleaje` receiving questionable `elevarse` competitor contexts,
- the role-contribution report queues 44 non-active rows for review before any
  source promotion; this is expected because shadow and no-winner generated
  rows are more dangerous than active evidence rows.

TF-IDF score contribution on the selected 20 families:

```text
base decision accuracy: 41.7%
generated_active_only decision accuracy: 70.0%
generated_existing_shadows decision accuracy: 65.0%
base replace recall: 12.5%
generated_active_only replace recall: 55.0%
generated_existing_shadows replace recall: 47.5%
harmful replaces: 0 in base and generated modes
false abstains: 35 base, 18 active-only, 21 active+existing-shadows
```

Arm-level false-abstain movement under TF-IDF:

```text
generated_active_only:
  high_need: 13 -> 3 false abstains
  middle_control: 7 -> 5 false abstains
  low_control: 15 -> 10 false abstains

generated_existing_shadows:
  high_need: 13 -> 5 false abstains
  middle_control: 7 -> 6 false abstains
  low_control: 15 -> 10 false abstains
```

This is a real downstream signal: generated active evidence materially reduces
false abstains on the selected families. Shadow evidence alone hurts recall,
and active-plus-shadow trails active-only on decision accuracy while improving
winner accuracy slightly. The immediate practical lesson is to treat active
evidence generation as the first product-value lane, and to keep shadow evidence
behind stricter competitor-target review.

The sentence-transformer contribution run was attempted but interrupted after
it did not complete promptly on this checkpoint. Do not cite an ST contribution
result until that slower lane is rerun or optimized.

### Milestone 1k: Product-Scope Band Grading And SRS-Mix Normalization Exist

The original band/formula sweep graded formulas mainly as a rank-ordering
problem: predicted need versus observed family failure rate. That is useful, but
it is not the same question as:

```text
If this formula creates high/middle/low need bands, do those bands actually have
different veto failure rates after accounting for the expected SRS case mix?
```

The product-scope band-grading report now answers that question directly. It
uses the current product-scope formula sweep, the selected candidate case-level
surface, and the SRS case-mix prior report. Runtime policy remains unchanged.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_band_grading_en_es.py
docs/test_outputs/semantic_veto_product_scope_band_grading_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_band_grading_en_es.py \
  --fail-on-review
```

Current normalization targets:

```text
global_test_case_mix: positive_active 70.0%, shadow_negative 30.0%, phrase_no_winner 0.0%
base_product_prior: positive_active 73.8%, shadow_negative 15.0%, phrase_no_winner 11.2%
high_no_winner_product_prior: positive_active 64.7%, shadow_negative 15.0%, phrase_no_winner 20.3%
```

Important boundary:

- the current product-scope selected-candidate surface has positive-active and
  shadow-negative rows, but no phrase/no-winner rows,
- therefore SRS-prior normalization is explicitly `measured-only` for the
  observed mass and reports the unmeasured phrase/no-winner mass instead of
  pretending it has been tested,
- this is the correct data-science posture: the report can compare formula bands
  on the evidence we have, and it also states exactly which part of the SRS
  distribution is not measured.

Current best band-grade row:

```text
scorer/config: safest_80pct_positive_sentence_transformer_a0000_m0015
formula: sweep_linear_2169
weights:
  source_zipf_risk: 0.2308
  target_zipf_risk: 0.1538
  polysemy_risk: 0.0769
  pos_shape_risk: 0.2308
  shadow_coverage_risk: 0.3077
bands: high_need 17 families, middle_need 16, low_need 16
raw high-low failure delta: +14.6 percentage points
base-SRS-prior measured high-low failure delta: +24.8 percentage points
unmeasured base-prior mass: 11.2%
```

The old repeated `shadow_coverage_only` signal remains a useful representative
comparison, but it is weaker under this band-first grading:

```text
safest ST + shadow_coverage_only:
  raw high-low failure delta: +11.9 points
  base-SRS-prior measured high-low failure delta: +20.6 points
  order score: 0.6667
```

Interpretation:

- the corrected feature-list fix means the fixed `linear_equal` and `max_signal`
  formulas now use the same actual feature ids as the swept formulas,
- the band-first report supports the user's concern that raw test-suite mix can
  distort the read,
- the best current allocation hypothesis is no longer merely "shadow coverage
  alone"; a mixed formula with source frequency, target frequency, POS shape, and
  shadow coverage gives the strongest measured band separation on the current
  product-scope lane,
- this is still an allocation research signal, not a final product-quality
  claim, because phrase/no-winner product mass is visible but unmeasured here.

### Milestone 1l: Product-Scope Band Heuristic Accepted For Next Research Stage

Before carrying the new mixed heuristic into another LLM follow-through batch,
we ran a bounded acceptance audit rather than relying on the top row alone.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_band_grading_acceptance_audit_en_es.py
docs/test_outputs/semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_band_grading_acceptance_audit_en_es.py \
  --fail-on-review
```

Decision:

```text
accept_band_grading_v1_for_next_research_stage
```

Candidate frozen for the next research stage:

```text
candidate id: product_scope_band_grading_v1
scorer/config: safest_80pct_positive_sentence_transformer_a0000_m0015
formula: sweep_linear_2169
weights:
  source_zipf_risk: 0.2308
  target_zipf_risk: 0.1538
  polysemy_risk: 0.0769
  pos_shape_risk: 0.2308
  shadow_coverage_risk: 0.3077
bands: high_need 17 families, middle_need 16, low_need 16
```

Bounded falsification checks passed:

```text
candidate detail available: pass
normalization targets all positive: pass
normalization order all monotonic: pass
sentence-transformer configs positive: pass
near-neighbor formula family available: pass
candidate beats fixed controls: pass
```

Normalization sensitivity:

```text
balanced measured mix: high 17.6%, middle 6.2%, low 1.6%, high-low +16.1 pp
global test mix: high 23.5%, middle 8.8%, low 2.2%, high-low +21.3 pp
base SRS prior: high 27.4%, middle 10.4%, low 2.6%, high-low +24.8 pp
high no-winner SRS prior: high 26.8%, middle 10.2%, low 2.5%, high-low +24.3 pp
low no-winner SRS prior: high 29.3%, middle 11.2%, low 2.8%, high-low +26.5 pp
```

Scorer/config sensitivity:

```text
sentence-transformer configs:
  best_product_rank_sentence_transformer_a0000_mneg0025: +9.2 pp, monotonic
  current_v3_like_sentence_transformer_a0000_m0000: +20.9 pp, monotonic
  safest_80pct_positive_sentence_transformer_a0000_m0015: +24.8 pp, monotonic

TF-IDF configs:
  high_recall_soft_assist_tfidf_a0000_mneg0050: +1.0 pp, non-monotonic
  tfidf_best_by_scorer_tfidf_a0000_mneg0005: -6.2 pp, non-monotonic
```

Interpretation:

- accept this heuristic as the v1 allocation heuristic for the
  sentence-transformer product lane,
- do not call it backend-agnostic,
- do not promote runtime policy from it,
- use it to pick the next high/middle/low LLM follow-through batch, with
  low-band controls preserved.

### Milestone 1m: Product-Scope Band-Grading v1 Follow-Through Plan Exists

The accepted v1 heuristic is now materialized as a no-spend allocation plan and
generation request packet. This is the handoff point before another paid
generation run.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.py
docs/test_inputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.py \
  --fail-on-review

python3 scripts/testing/semantic_veto_evidence_gap_generation_requests_en_es.py \
  --plan-json docs/test_inputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.json \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.md \
  --fail-on-review
```

Current plan:

```text
candidate id: product_scope_band_grading_v1
source denominator: 49 repaired product-scope families
band availability:
  high_need: 17 families, 8 previous-pilot overlap, 9 new
  middle_need: 16 families, 6 previous-pilot overlap, 10 new
  low_need: 16 families, 6 previous-pilot overlap, 10 new
selected follow-through batch: 18 new families
selected arms: 6 high_need, 6 middle_control, 6 low_control
previous-pilot selected overlap: 0
planned generation slots: 54
expected generated items: 90
estimated input tokens: 40,848
expected output-token budget: 12,600
```

Selected families:

```text
high_need: cite->mencionar, smile->sonreír, bar->cercar,
  control->gobernar, except->excepto, region->comarca
middle_control: govern->gobernar, german->alemán, american->americano,
  endure->durar, tomorrow->mañana, russian->ruso
low_control: dentist->dentista, pub->taberna, shortage->falta,
  rumanian->rumano, argentinean->argentino, owe->deber
```

Interpretation:

- this plan expands coverage rather than duplicating the previous paid pilot,
- it keeps the same active, shadow/competitor, and no-winner request contract
  for all arms,
- observed historical failures are shown for diagnostics only and are not used
  for selection,
- the next paid step should not happen until the request packet is reviewed.

### Milestone 1n: Product-Scope Band-Grading v1 Follow-Through Generated

The v1 follow-through batch has now been generated, admitted, and rescored. This
does not change runtime policy and does not promote generated rows directly into
source evidence.

Artifacts:

```text
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generated_responses_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_contribution_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_contribution_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.md
```

Run:

```bash
.venv/bin/python scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json \
  --run-id product-scope-band-grading-v1-20260510-001 \
  --execute-live \
  --model-id gpt-5.4-mini \
  --input-rate-per-1m 0.75 \
  --output-rate-per-1m 4.50 \
  --require-selected-request-count 54 \
  --max-estimated-cost-usd 1 \
  --max-estimated-cost-ceiling-usd 2 \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.md \
  --generated-responses-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generated_responses_en_es_latest.json

.venv/bin/python scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json \
  --run-id product-scope-band-grading-v1-20260510-001 \
  --execute-live \
  --resume \
  --retry-invalid-outputs \
  --model-id gpt-5.4-mini \
  --input-rate-per-1m 0.75 \
  --output-rate-per-1m 4.50 \
  --require-selected-request-count 54 \
  --max-estimated-cost-usd 1 \
  --max-estimated-cost-ceiling-usd 2 \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.md \
  --generated-responses-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generated_responses_en_es_latest.json

.venv/bin/python scripts/testing/semantic_veto_evidence_gap_generation_admission_en_es.py \
  --generation-requests-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json \
  --generated-responses-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generated_responses_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.md

.venv/bin/python scripts/testing/semantic_veto_evidence_gap_generation_contribution_en_es.py \
  --generation-requests-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_requests_en_es_latest.json \
  --admission-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.json \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_contribution_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_contribution_en_es_latest.md

python3 scripts/testing/semantic_veto_evidence_gap_generation_score_contribution_en_es.py \
  --dataset-json docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json \
  --admission-json docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_admission_en_es_latest.json \
  --scorer-id sentence_transformer_cosine \
  --min-active-score 0 \
  --min-margin 0.015 \
  --skip-policy-sweep \
  --json-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.md
```

Generation:

```text
batch id: en-es:semantic-veto-evidence-gap-generation:product-scope-band-grading-v1-20260510-001
model: gpt-5.4-mini
prompt id: semantic_veto_evidence_gap_generation_v7_shadow_target_correctness
accepted responses: 54 / 54 after one request-id retry
accepted generated items: 80
latest accepted-token summary: 36,840 input / 11,899 output
journal-inclusive paid outcomes: 37,543 input / 12,085 output
estimated standard-processing cost from journal: about $0.083
```

Admission:

```text
status: review
admitted items: 67 / 90 expected
active_evidence_expansion: 36 admitted / 36 expected
no_winner_context_probe: 17 admitted / 18 expected
shadow_or_competitor_evidence_probe: 14 admitted, 10 waived, 4 rejected, 12 shortfall
```

Accepted sentence-transformer configuration read:

```text
scorer: sentence_transformer_cosine
min_active_score: 0.0
min_margin: 0.015
policy sweep: skipped for this targeted read

base: 77.1% decision accuracy, 91.7% replace recall, 13 harmful replaces, 3 false abstains
generated_active_only: 78.6% decision accuracy, 97.2% replace recall, 14 harmful replaces, 1 false abstain
generated_existing_shadows: 75.7% decision accuracy, 91.7% replace recall, 14 harmful replaces, 3 false abstains
```

Per-arm accepted-config read:

```text
generated_active_only:
  high_need: +3.3 pp accuracy, +16.7 pp replace recall, false abstains 3 -> 1, harmful 2 -> 3
  middle_control: flat
  low_control: flat

generated_existing_shadows:
  high_need: flat accuracy, +16.7 pp replace recall, false abstains 3 -> 1, harmful 2 -> 4
  middle_control: -4.5 pp accuracy, -16.7 pp recall
  low_control: flat
```

TF-IDF read, kept as a fast diagnostic rather than the accepted product scorer:

```text
base: 47.1% decision accuracy, 0.0% replace recall, 1 harmful replace, 36 false abstains
generated_active_only: 65.7% decision accuracy, 38.9% replace recall, 2 harmful replaces, 22 false abstains
generated_existing_shadows: 62.9% decision accuracy, 33.3% replace recall, 2 harmful replaces, 24 false abstains
```

Interpretation:

- active evidence generation is the only clearly useful part of this batch,
- the accepted sentence-transformer configuration shows the lift concentrated in
  `high_need`; middle and low controls are flat under active-only application,
- shadow/competitor generation still creates too much admission shortfall and can
  hurt scoring, so it should remain review-gated rather than used as automatic
  source evidence,
- no-winner generated rows are useful as diagnostics but are not applied as
  runtime evidence in the current score-contribution probe,
- the heuristic is not proven language-wide, but this follow-through supports the
  practical next posture: use LLM budget first for active evidence on high-need
  families, keep a small control slice, and pause broad shadow generation until
  the competitor-target problem is cleaner.

### Milestone 1o: Top-Heavy Allocation Recheck

The equal-thirds banding decision has been rechecked against a more product-like
top-heavy allocation view. This is a no-spend research report; it does not change
runtime policy and does not replace the v1 evidence already generated.

Artifacts:

```text
scripts/testing/semantic_veto_product_scope_top_heavy_band_grading_en_es.py
core/tests/dev/test_semantic_veto_product_scope_top_heavy_band_grading_en_es.py
docs/test_outputs/semantic_veto_product_scope_top_heavy_band_grading_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_top_heavy_band_grading_en_es_latest.md
```

Run:

```bash
python3 scripts/testing/semantic_veto_product_scope_top_heavy_band_grading_en_es.py \
  --fail-on-review
```

Current read:

```text
formula scopes evaluated: 2,001 / 15,670
strategy scopes evaluated: 48,024
band strategies: equal tertiles, top 5/15/rest, top 10/20/rest,
  top 15/25/rest, top 20/30/rest, top 25/25/rest
ranking modes: algorithm_need, source_exposure_product,
  source_exposure_blend_25, source_exposure_blend_50
```

Accepted candidate takeaway:

```text
decision: top_heavy_has_signal_but_does_not_beat_equal_tertile_control
accepted equal-tertile control:
  bands: 17 high / 16 middle / 16 low
  high failure: 27.4%
  rest failure: 6.5%
  high-rest delta: 20.9 pp
  grade: 0.1856

best accepted top-heavy alternative:
  strategy: top_05_next_15_rest
  ranking: source_exposure_blend_50
  bands: 3 high / 7 middle / 39 low
  high failure: 27.7%
  rest failure: 13.1%
  high-rest delta: 14.6 pp
  grade: 0.0864
  grade ratio to equal-tertile control: 0.4655
```

Interpretation:

- the top-heavy/common-language intuition is not wrong: the best concentrated
  slice does find a tiny high-failure group (`break`, `control`, `current`),
- but on the current repaired 49-family product-scope suite, that concentrated
  slice does not beat the equal-tertile accepted candidate as an allocation
  heuristic,
- the equal-tertile result remains stronger because failures are spread through
  a broader upper group, not only the first few daily-language families,
- source exposure is still useful for product framing and top-N budget curves,
  but this report does not justify switching the next allocation strategy to a
  tiny top-heavy batch yet,
- the result is sample-fragile because top 5% is only three families in this
  suite; treat it as a hypothesis to revisit when the SRS candidate universe is
  scored, not as a final product cutoff.

### Milestone 1p: High-Need Shadow Stronger-Model Probe

The harder shadow/competitor slots were tested with a stronger model before
spending broadly on shadow data. This was intentionally narrow: the exact six
`high_need` shadow requests from `product_scope_band_grading_v1` were rerun with
`gpt-5.5`, then admitted and rescored against the same repaired manual sentence
cases. Runtime policy remains unchanged.

Artifacts:

```text
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_run_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_run_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generated_responses_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_admission_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_admission_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_contribution_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_contribution_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generated_responses_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generation_admission_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generation_admission_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_mini_high_generation_score_contribution_sentence_transformer_a0000_m0015_en_es_latest.md
```

Run shape:

```text
model: gpt-5.5
request scope: six high_need shadow_or_competitor_evidence_probe requests
temperature: omitted, because this model rejects the temperature parameter
retry policy: one retry of the three truncated JSON outputs with max_output_tokens 1400
journal-inclusive usage: 7,807 input tokens / 6,449 output tokens
estimated standard-processing cost at the 2026-05-09 price snapshot: about $0.233
```

Admission comparison:

```text
gpt-5.4-mini same six high-need shadow requests:
  admitted 10 / 12 expected items
  rejected 2 items
  selected families reaching scoring: 5

gpt-5.5 same six high-need shadow requests:
  admitted 12 / 12 expected items
  rejected 0 items
  selected families reaching scoring: 6
```

Fixed sentence-transformer score contribution at `min_active_score=0.0` and
`min_margin=0.015`:

```text
gpt-5.5 selected-family base:
  83.3% decision accuracy, 75.0% replace recall,
  2 harmful replaces, 3 false abstains

gpt-5.5 generated_existing_shadows:
  80.0% decision accuracy, 66.7% replace recall,
  2 harmful replaces, 4 false abstains

gpt-5.4-mini same-six subset generated_existing_shadows:
  76.0% decision accuracy, 70.0% replace recall,
  3 harmful replaces, 3 false abstains
```

Interpretation:

- the stronger model materially improved shadow-row admissibility; for example,
  it generated usable `except -> objetar` competitor contexts where the mini
  row fell back to the active `excepto` sense and was rejected,
- that admission improvement did not translate into fixed-threshold veto lift;
  stronger shadows still added abstention pressure and did not reduce harmful
  replacements on this six-family slice,
- therefore broad paid shadow generation should stay paused unless the next
  change also changes how shadow evidence is represented, weighted, or admitted,
  or unless a separate reviewer lane can prove that accepted shadows improve
  downstream decisions outside this fixed scorer setup,
- the practical paid-data path remains active evidence first for high-need
  families, with shadow generation reserved for narrow experiments.

### Milestone 1q: Active-Only v1 Reuse Tranche

Before spending on another active-only batch, the already generated
`product_scope_band_grading_v1` active evidence was carried through the
productization path as a no-spend scale-up rehearsal. This answers whether the
current active-only packaging/replay/helper flow can handle another tranche with
tranche-specific provenance.

Artifacts:

```text
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_postprocess_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_postprocess_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_source_packaging_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_source_packaging_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-source-packaging-latest_intake_batch.json
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-source-packaging-latest_normalized_evidence.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_inventory_replay_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_inventory_replay_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-inventory-replay-latest_semantic_inventory.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_helper_runtime_smoke_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_helper_runtime_smoke_en_es_latest.md
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_live_page_scan_en_es_latest.json
docs/test_outputs/semantic_veto_product_scope_band_grading_v1_active_only_live_page_scan_en_es_latest.md
```

Postprocess:

```text
active items audited: 36
families: 18
high eval-overlap items: 1
POS-weak items: 12
target lemma in evidence note: 0
selected view: no_high_eval_overlap_sentence_only
selected view score: 68.6% decision accuracy, 41.7% replace recall,
  1 harmful replace, 21 false abstains on 70 cases
```

Source packaging:

```text
packaged anchor_cue rows: 35
excluded rows: 1 high eval-overlap row
families: 18
runtime_publishable rows: 0
source_id / row_id provenance: tranche-specific
```

Inventory-shaped replay:

```text
applied rows: 35 / 35
cases: 70
base: 47.1% decision accuracy, 0.0% replace recall,
  1 harmful replace, 36 false abstains
candidate: 68.6% decision accuracy, 41.7% replace recall,
  1 harmful replace, 21 false abstains
delta: +21.4 pp decision accuracy, +41.7 pp replace recall,
  -15 false abstains, +0 harmful replaces
```

Helper runtime smoke:

```text
families / rules: 18
cases: 70
policy decisions: 70
fallback decisions: 0
decision accuracy: 67.1%
replace recall: 44.4%
harmful replaces: 3
false abstains: 20
```

Live page scan:

```text
pages scanned: 17 / 17
page fetch errors: 0
review rows: 63
decisions: 13 replace / 50 abstain
fallback decisions: 0
```

Interpretation:

- the scale-up flow works without new spend: generated active rows can be
  audited, packaged, normalized, replayed, helper-published into an isolated
  fixture, and scanned against public pages with no fallback decisions,
- this tranche reproduces the core active-only benefit: it mainly reduces false
  abstains and increases replacement recall,
- the helper/runtime smoke is more product-realistic than the inventory replay
  and shows the expected soft-assist tradeoff: more visible replacements plus a
  few harmful allows,
- the next paid generation step should use the same active-only path, not broad
  shadow generation, and should be stopped if a tranche fails admission,
  packaging, replay, or manual page feel.

### Milestone 1r: Active-Only Scale Tranche and Combined Product-Scope Fixture

The next paid active-only tranche was run after excluding families already
covered by the PoC and v1 reuse batches. The purpose was not to retune the
algorithm. It was to complete active generated-evidence coverage for the current
49-family repaired product-scope denominator, then replay the combined source
evidence through the same offline and helper paths.

Artifacts:

```text
scripts/testing/semantic_veto_active_only_scale_tranche_requests_en_es.py
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_requests_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_run_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_run_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generated_responses_repaired_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_admission_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_admission_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_postprocess_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_postprocess_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_source_packaging_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_source_packaging_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-scale-tranche-v1-source-packaging-latest_normalized_evidence.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_inventory_replay_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_inventory_replay_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-normalized_evidence.json
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_inventory_replay_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_inventory_replay_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_helper_runtime_smoke_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_helper_runtime_smoke_en_es_latest.md
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_live_page_scan_en_es_latest.json
docs/test_outputs/semantic_veto_active_only_combined_product_scope_v1_live_page_scan_en_es_latest.md
```

Request packet:

```text
covered families excluded: 33
selected uncovered families: 16
requests: 16 active_evidence_expansion
expected generated items: 32
arms: 6 high_need, 4 middle_control, 6 low_control
estimated input tokens: 7,967
expected output-token budget: 4,480
```

Generation and admission:

```text
model: gpt-5.4-mini
accepted responses after resume: 16 / 16
admitted active items after repair: 32 / 32
rejected generated items: 0
coverage shortfall: 0
journal-inclusive paid outcomes: 18
journal-inclusive usage: 8,469 input tokens / 3,079 output tokens
estimated cost at the 2026-05-09 mini rates: about $0.020
```

One mechanical repair was applied to the generated-response bundle:

```text
continue -> durar repair:
  initial accepted response had one rejected item because it used "continues"
  instead of the exact runtime token "continue";
  the one-request repair response used exact-token sentences but changed
  request_id metadata from en_es to en-es;
  the repaired generated-response artifact corrects only that request_id
  metadata and leaves generated sentences unchanged.
```

Scale-tranche-only replay:

```text
families: 16
cases: 63
packaged rows: 32
base: 55.6% decision accuracy, 12.5% replace recall,
  0 harmful replaces, 28 false abstains
candidate: 71.4% decision accuracy, 50.0% replace recall,
  2 harmful replaces, 16 false abstains
delta: +15.9 pp decision accuracy, +37.5 pp replace recall,
  -12 false abstains, +2 harmful replaces
```

Combined product-scope replay:

```text
combined batches: PoC active-only + v1 reuse active-only + scale tranche
families: 49
cases: 189
packaged rows: 112
base: 50.3% decision accuracy, 5.1% replace recall,
  1 harmful replace, 93 false abstains
candidate: 72.0% decision accuracy, 46.9% replace recall,
  1 harmful replace, 52 false abstains
delta: +21.7 pp decision accuracy, +41.8 pp replace recall,
  -41 false abstains, +0 harmful replaces
```

Combined helper runtime smoke:

```text
families / rules: 49
cases: 189
policy decisions: 189
fallback decisions: 0
decision accuracy: 72.5%
replace recall: 49.0%
harmful replaces: 2
false abstains: 50
```

Combined live page scan:

```text
pages scanned: 16 / 17
page fetch errors: 0
review rows: 120
decisions: 25 replace / 95 abstain
decision source: 120 policy, 0 fallback
scan stopped reason: max_total_matches
```

Interpretation:

- the active-only path now has source evidence coverage for the full current
  49-family product-scope denominator,
- the combined offline replay is a clean improvement over the base product-scope
  state and does not increase harmful replacements under that replay policy,
- the helper smoke is the more runtime-realistic reading and shows the expected
  soft-assist tradeoff: nearly half of positives allowed, 50 false abstains
  remaining, and 2 harmful replacements,
- the live-page scan is still a manual product-feel packet, not a statistical
  promotion metric,
- broad shadow generation remains paused because the strongest shadow probe did
  not improve fixed scorer outcomes.

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
