# Semantic Veto Bound Ladder Reference

Status: draft reference
Role: Draft decision log
Purpose: define sidecar accuracy-bound concepts for semantic-veto research without making current harnesses or promotion policy mechanically depend on them
Last updated: 2026-05-01
Last verified: 2026-05-01 by documentation-only review against current wave6/wave7 artifact paths
Source-of-truth: this document is explanatory only; implementation truth remains in runtime code, test inputs, generated outputs, and `docs/test_inputs/semantic_veto_system_registry_en_es.json`

## Scope

This document records how to think about lower bounds, upper bounds, and
diagnostic ceilings for the `en-es` semantic-veto workstream. Product-oriented
acceptance targets live in
`docs/rulegen/semantic_veto_product_quality_goals.md`.

It is not:

- a quality gate,
- a runtime policy,
- a registry replacement,
- a benchmark baseline,
- or promotion evidence by itself.

Use it to decide what future measurement should mean. Do not make production
behavior or test pass/fail logic depend on it until a separate implementation
plan explicitly promotes one of these ideas.

## Why Bounds Matter

The current research question is not only whether the latest candidate improves
a fixed suite. The larger question is whether the project is moving toward an
acceptable level of general semantic-veto accuracy, or whether the current
architecture is nearing its ceiling.

Bounds help by separating these questions:

- What have we actually achieved on locked inputs?
- What could the current data support if the final rule were better?
- What could planned LLM-generated evidence support if generation works?
- What could ideal evidence support if source coverage were no longer the
  bottleneck?
- Which remaining failures are genuinely policy failures versus missing or weak
  information?

They do not replace the product target. The product target is recall-oriented:
show most good replacements, and hide a meaningful share of bad replacements.
Zero harmful replacements remains a useful stress diagnostic, not the default
product acceptance bar.

## Pipeline Model

The veto decision can be treated as an information pipeline:

```text
browser sentence
-> candidate replacement family
-> active/shadow/phrase/no-winner evidence
-> context representation
-> scorer scores
-> aggregation and decision rule
-> runtime policy output
```

A useful bound should correspond to one stage of this pipeline. If a new stage
is added later, such as a cross-encoder reranker or LLM-generated evidence
normalizer, add a bound at the input and output of that stage instead of
pretending the old bound still explains the whole system.

## Bound Ladder

### End-to-End Lower Bound

Definition: the best result actually achieved by a concrete candidate on a
locked evaluation suite.

Use:

- proves at least this performance is achievable,
- gives a conservative factual progress marker,
- cannot prove language-wide readiness by itself.

Current examples:

- `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.json`
  reports a scorer-backed wave6 policy pass over `54` cases.
- `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.json`
  and
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.json`
  show the broader wave7 lane remains blocked.

### Current-Evidence Upper Bound

Definition: the best possible result using only the evidence already admitted
for the frozen suite.

Question:

> If the final decision rule were better, but no new source rows or generated
> evidence were added, how many failures could disappear?

This bound should be measured from fixed score traces and fixed admitted
evidence. It should not silently add new glosses, examples, phrase rows, or
source-class rows.

Interpretation:

- high current-evidence upper bound means decision-rule research still has room,
- low current-evidence upper bound means more threshold work is unlikely to
  solve the problem.

### Source-Coverage Upper Bound

Definition: the maximum result possible when the current source inventory is
the only allowed source of active, shadow, and phrase/no-winner evidence.

Question:

> Is the correct sense or competing no-replace explanation present anywhere in
> the available source data?

This is not the same as current-evidence upper bound. Current-evidence bound
uses rows already admitted into the candidate. Source-coverage bound asks
whether the raw source inventory had enough information before admission,
filtering, or representation choices discarded it.

Interpretation:

- missing gold evidence points to source acquisition or generation,
- present but unused evidence points to source admission,
- present and admitted but not useful points to representation or scoring.

### Evidence-Representation Upper Bound

Definition: the maximum result possible if the correct source data exists, but
the evidence text is represented in the current row format.

Question:

> Does the row text actually express the distinction needed by the sentence?

Example failure shape:

- the source has a relevant sense,
- the row reduces it to a vague label,
- the scorer cannot separate the active and shadow meanings.

Interpretation:

- a low representation bound means better data alone may not help unless the
  rows say the right thing,
- a high representation bound means the row format can support the distinction
  if scoring or policy improves.

### Scorer-Ranking Upper Bound

Definition: the best result possible if the decision rule could choose from
the scores produced by one or more available scorers, without adding new
evidence.

Question:

> Does any scorer rank the gold active, shadow, or phrase/no-winner evidence in
> a way that makes the correct decision recoverable?

Interpretation:

- if the gold winner is never score-visible, final policy cannot recover it
  reliably,
- if the gold winner is score-visible under some scorer, backend or aggregation
  research may still be worthwhile.

### Score-Trace Decision Upper Bound

Definition: the best result a constrained classifier can achieve using fixed
score traces only.

Question:

> Given the same scores the runtime-shaped policy would see, can any simple
> rule separate replace from abstain?

This should be handled carefully. A classifier that memorizes case IDs is not a
meaningful upper bound for deployable quality. Use cross-validation,
leave-family-out splits, or locked confirmation suites before treating this
bound as evidence.

Interpretation:

- high score-trace bound plus low current runtime result points to decision-rule
  weakness,
- low score-trace bound points upstream to evidence, representation, or scorer
  weakness.

### Runtime-Policy Upper Bound

Definition: the best result achievable by the family of policies we would
actually consider shipping.

Question:

> If we restrict ourselves to runtime-compatible features and stable parameters,
> how close can we get?

This is the practical bound for promotion discussions. It may be lower than the
score-trace decision upper bound because production policy should avoid
case-specific features and fragile knobs.

## LLM-Generated Evidence Lanes

Bounds over current evidence do not account for planned LLM-generated data.
Use separate lanes so the result is not ambiguous.

### Current-Input Bound

Uses frozen current source rows and admitted evidence only.

Purpose:

- tells us whether more scoring or policy work can help without generation.

### LLM-Pipeline Bound

Uses the actual planned LLM generation process, including prompt, generated
rows, admission, leakage rejection, sense checks, and downstream scoring.

Purpose:

- tells us whether the real generation pipeline improves the locked suite,
- keeps LLM benefits honest by including the filters that production would
  need.

This bound should never tune prompts on the same cases later used for a
promotion claim.

### Oracle-Evidence Bound

Uses ideal active, shadow, and no-winner evidence for diagnostic purposes. The
ideal evidence may be human-written or LLM-assisted, but it may inspect the
gold label only because it is explicitly not promotion evidence.

Purpose:

- tells us whether better evidence could solve the residuals at all,
- separates evidence-generation opportunity from scorer and policy limits.

If oracle evidence solves cases that current evidence cannot solve, planned
LLM generation is a plausible route. If oracle evidence still fails, LLM data
alone is unlikely to fix the current architecture.

### Oracle-Decision Bound

Uses fixed score traces and asks what would happen if the final decision were
perfect inside a constrained feature family.

Purpose:

- tells us whether current scores contain enough signal,
- should be treated as a ceiling on decision-rule research, not as a shippable
  configuration.

## How This Helps Define Acceptable Goals

An acceptable goal should be chosen against the relevant bound, not against an
abstract desire for perfect language understanding.

If the oracle-evidence and scorer-ranking bounds are high, then an ambitious
goal is reasonable:

```text
0 harmful replacements on locked heldout,
low false abstain count,
stable leave-family-out behavior,
and no regression when phrase/no-winner is measured separately.
```

If current-evidence and scorer-ranking bounds are low, then the acceptable goal
for the current architecture should be more conservative:

```text
keep harmful replacements at 0,
accept higher abstention,
and invest in source/evidence generation before claiming broader recall.
```

If LLM-pipeline bounds approach oracle-evidence bounds, then generated evidence
is likely the right expansion path. If LLM-pipeline bounds remain far below
oracle-evidence bounds, the problem is likely generation quality, admission, or
representation. If oracle-evidence bounds are also low, the bottleneck is likely
the scorer or final decision formulation.

## Residual Case Audit Template

For every residual failure, record:

| Question | Answer options | Meaning |
| --- | --- | --- |
| Was the gold active/shadow/no-winner evidence available in raw sources? | yes / no / unclear | source-coverage bound |
| Was that evidence admitted into the candidate rows? | yes / no / partial | source-admission bound |
| Did the admitted row express the needed distinction? | yes / no / partial | representation bound |
| Did any scorer rank the gold evidence recoverably? | yes / no / scorer-specific | scorer-ranking bound |
| Could a constrained rule over fixed scores get the case right? | yes / no / overfit-only | score-trace decision bound |
| Could runtime-compatible policy get it right without harming other cases? | yes / no / unknown | runtime-policy bound |
| Would oracle evidence likely fix it? | yes / no / unknown | LLM/source opportunity |

## Guardrails

- Keep phrase/no-winner bounds separate from active/shadow bounds.
- Keep current-evidence, LLM-pipeline, and oracle-evidence lanes separate.
- Do not treat oracle-evidence or oracle-decision results as promotion
  evidence.
- Do not update quality baselines from bound experiments.
- Do not use generated evidence on the same cases for both prompt tuning and
  promotion claims.
- Prefer family-level heldout splits when estimating score-trace or
  runtime-policy ceilings.
- If a bound is computed from dirty or local-only artifacts, label it
  non-authoritative until the artifact disposition is resolved.

## Near-Term Developer Use

Before more wave7 remediation, this reference now has two sidecar reports:

```text
scripts/testing/semantic_veto_bound_ladder_wave7_residuals.py
docs/test_outputs/semantic_veto_bound_ladder_wave7_residuals_latest.json
docs/test_outputs/semantic_veto_bound_ladder_wave7_residuals_latest.md

scripts/testing/semantic_veto_current_evidence_ceiling_wave7.py
docs/test_outputs/semantic_veto_current_evidence_ceiling_wave7_latest.json
docs/test_outputs/semantic_veto_current_evidence_ceiling_wave7_latest.md

scripts/testing/semantic_veto_upstream_gap_audit_wave7.py
docs/test_outputs/semantic_veto_upstream_gap_audit_wave7_latest.json
docs/test_outputs/semantic_veto_upstream_gap_audit_wave7_latest.md
```

The bound-ladder report inspects the current residual failures and classifies
each one by the template above. Its first value is to answer whether the
remaining gap is mostly:

- missing source coverage,
- weak admitted evidence,
- scorer ranking failure,
- decision-rule weakness,
- phrase/no-winner guard weakness,
- or runtime-policy constraint.

The current-evidence ceiling report tests whether the optimistic current-score
ceiling survives a no-new-data guard sweep. It uses only general score/surface
features, no case IDs, and no trigger-specific rules. Its first value is to
separate real current-evidence headroom from optimistic bookkeeping.

The upstream gap audit reads those two reports plus the source/admission
artifacts and classifies each remaining residual by the next useful work lane:
evidence representation, scorer visibility, phrase/no-winner guard signal,
shadow-frame evidence strength, or confirmed current-guard headroom.

Only after that report is useful should any bound become a harness, gate, or
promotion criterion.
