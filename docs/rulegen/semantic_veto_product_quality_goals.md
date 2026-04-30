# Semantic Veto Product Quality Goals

Status: draft reference
Role: Draft decision log
Purpose: define the product-oriented acceptance calculus for semantic-veto work so research does not optimize for zero-harm purity when the user experience target is broader replacement usefulness
Last updated: 2026-05-01
Last verified: 2026-05-01 against current wave7 product-metric arithmetic and sidecar bound reports
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
