# Semantic Veto Product Quality Goals

Status: draft reference
Role: Draft decision log
Purpose: define the product-oriented acceptance calculus for semantic-veto work so research does not optimize for zero-harm purity when the user experience target is broader replacement usefulness
Last updated: 2026-05-01
Last verified: 2026-05-01 against current wave7 product-quality harness output and sidecar bound reports
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

Current status: implemented for the wave7 stress lane plus the existing
sentence-veto v10 representative proxy.

Run:

```bash
python3 scripts/testing/semantic_veto_product_quality_en_es.py \
  --policy-json docs/test_inputs/semantic_veto_product_quality_policy_en_es.json \
  --json-out docs/test_outputs/semantic_veto_product_quality_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_veto_product_quality_en_es_latest.md
```

The current report includes both the wave7 stress lane and the existing
sentence-veto v10 representative proxy. Its overall read is:

```text
decision: product_target_missed
cases: 143
positive_allow_rate: 50.0%
negative_abstain_rate: 92.1%
utility: 77.6
lexical_allow_all_utility: 0.6
abstain_all_utility: 49.6
```

Interpretation:

- the current stress lane clears the first product target on known hard cases,
- the existing v10 representative proxy fails the first product target because
  positive allow is only `34.2%` in that lane,
- the combined measured lanes beat lexical allow-all and abstain-all baselines
  under the current utility weights,
- the immediate blocker is positive allow on broader active examples, not
  negative abstain.

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
  passing shape on the wave7 stress reports,
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

### Milestone 3: LLM-Expanded Evaluation

Use LLM budget to generate broader locked evaluation data.

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
