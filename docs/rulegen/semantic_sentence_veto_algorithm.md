# Semantic Sentence-Veto Algorithm

Status: active reference
Role: Algorithm reference / research alignment
Last updated: 2026-04-29
Last verified: 2026-04-29 against `semantic_routing_runtime_scoring.py`, `semantic_routing_runtime_policy.py`, current decision-rule matrix manifests, and latest phrasing/order plus context-conditioned evidence bakeoff artifacts
Purpose: describe the semantic sentence-veto algorithm end to end so runtime behavior, source-admission work, phrase handling, and decision-rule experiments stay aligned
Source-of-truth: explanatory reference only; implementation truth lives in the code, tests, manifests, and generated artifacts named below

Primary implementation references:

- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
- `scripts/testing/semantic_decision_rule_matrix_en_es.py`
- `scripts/testing/semantic_decision_research_lanes_summary.py`
- `scripts/testing/semantic_routing_sentence_veto_sweep.py`
- `scripts/testing/semantic_source_admission_cycle_en_es.py`
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/rulegen/semantic_source_admission_program.md`
- `docs/rulegen/semantic_veto_reconciliation_workstream.md`
- `docs/test_inputs/semantic_veto_system_registry_en_es.json`

## Core Product Goal

For each browser sentence, the user should either see the replacement or not.
There is no acceptable visible middle state in the current DOM path.

Example:

- source sentence contains `change`
- learner target is Spanish `cambio`
- the semantic gate must decide whether this local sentence supports that target
- if yes, show the replacement
- if no, leave the source text alone

The governing safety rule is asymmetric:

- harmful replacement is expensive and should be driven toward zero
- false abstain is acceptable while the system is still learning coverage

That asymmetry is why the current architecture is a conservative veto/admission
gate rather than a nearest-neighbor replacement engine.

## End-To-End Shape

The algorithm has two large halves:

1. offline source and competition construction
2. runtime sentence admission

The runtime admission algorithm cannot fix a missing shadow competitor. The
source-admission algorithm cannot prove the final browser decision by itself.
Keep these halves separate when reading results.

### Offline Source And Competition Construction

Offline work builds the data that runtime needs:

- an active sense for the learner target
- source evidence rows for that active sense
- a small shadow set of competing senses that can make the same English trigger unsafe
- source evidence rows for each shadow sense
- phrase/no-winner patterns that should abstain without pretending a shadow sense won

Conceptually, for one active target `a` and trigger phrase `t`:

```text
S(a, t) = {s1, s2, ..., sk}
```

`S(a, t)` is the published shadow set. It should contain real runtime hazards,
not every lexical neighbor.

The current source-admission work uses source-backed evidence families such as
reverse auxiliary text, local WordNet-style definition/example rows,
Wiktextract/Wiktionary-style examples where available, and generated or reviewed
example-frame rows only after leakage and sense-discrimination checks.

Important distinction:

- source coverage asks whether the right active/shadow/phrase evidence exists
- runtime scoring asks whether a sentence chooses correctly given that evidence

## Runtime Admission Path

The browser/helper runtime follows this shape.

### 1. Match Eligibility

A browser match is eligible for semantic gating only when the surrounding
runtime contract says it is ready:

- SRS is enabled
- the matched rule is SRS-origin
- the rule carries `metadata.semantic_admission`
- semantic capability for the pair/profile is active
- semantic inventory resolves through helper or helper-cache
- the admission record points to a ready active sense and ready competition set
- shadow senses can be resolved from the inventory
- the match has both `context_text` and `source_phrase`

If any required item is missing, runtime uses the configured fallback decision
instead of inventing a semantic answer.

### 2. Policy Resolution

Runtime resolves a named policy from `PRODUCTION_SEMANTIC_DECISION_POLICIES`.
As of this reference:

| Policy | Scorer | Context | Evidence | Thresholds | Phrase | Rescue |
| --- | --- | --- | --- | --- | --- | --- |
| `en_es_sentence_veto_v1` | `sentence_transformer_cosine` | `masked_sentence` | `gloss_text` | active `0.0`, margin `0.0` | on | on |
| `en_es_sentence_veto_v2` | `tfidf_cosine` | `masked_sentence` | `all_evidence_text` | active `0.05`, margin `0.0` | on | on |
| `en_es_sentence_veto_v3` | `sentence_transformer_cosine` | `masked_sentence` | `all_evidence_text` | active `0.0`, margin `0.0` | on | on |

The current pair default in code is:

```text
en-es -> en_es_sentence_veto_v3
```

Do not confuse this with the library fallback constants in
`semantic_routing_runtime_scoring.py`. Named policies override those constants.
Do not confuse it with the no-spend research control either; many recent matrix
experiments intentionally use `tfidf_cosine` because they are offline,
reproducible, and cheap.

### 3. Batch Fitting

For a batch of ready matches, runtime fits the selected scorer on exactly the
texts it may compare:

- context views derived from each ready match
- active evidence text
- shadow evidence text
- backup evidence text when active rescue is enabled

This matters most for `tfidf_cosine`, where adding texts can change the fitted
vocabulary and weights. Research matrices therefore support per-suite fitting so
held-out additions cannot silently move frozen-suite scores.

### 4. Context Representation

Production runtime currently exposes these context views:

- `raw_sentence`
- `masked_sentence`
- `raw_window`
- `masked_window`

For the active trigger span, masking replaces the matched source phrase with
`___`. Example:

```text
The company announced a major change in strategy.
The company announced a major ___ in strategy.
```

The matrix harness also has harness-only experimental views such as ordered
n-grams, skip-grams, before/after slots, surface frames, POS frames,
dependency-role approximations, negation/modal signals, shuffled context, and
reversed context. Those are not production runtime views.

### 5. Evidence Representation

For each sense, runtime resolves one evidence view from `evidence_views`:

- `sense_label`
- `gloss_text`
- `sense_gloss_bundle`
- `qualifier_text`
- `all_evidence_text`

If the requested view is missing, runtime falls back through broader evidence
views and finally to the sense label or target lemma.

The matrix harness can split evidence into rows, score definitions/examples
separately, test ordered evidence, test canonical templates, test paraphrase
variants, load admitted source rows, select evidence rows based on a separate
selector context, and run source-family dropout. Those are research surfaces
unless a candidate is promoted later.

### 6. Similarity Scoring

For context `c`, active sense `a`, and shadows `s_i`, production scoring is:

```text
active_score = similarity(context_text(c), evidence_text(a))

shadow_score_i = similarity(context_text(c), evidence_text(s_i))

strongest_shadow_score = max_i shadow_score_i

margin = active_score - strongest_shadow_score
```

Supported runtime scorers are:

- `token_jaccard`
- `tfidf_cosine`
- `sentence_transformer_cosine`

`sentence_transformer_cosine` normalizes cosine into the `[0, 1]` range. TF-IDF
and token overlap are no-spend controls and useful for exposing whether a result
is mostly word-presence behavior.

### 7. Primary YES/NO Decision

The primary decision is:

```text
replace if:
  active_score >= min_active_score
  and active_score - strongest_shadow_score >= min_margin

abstain otherwise
```

This is better described as a one-versus-strongest-competitor decision rule, not
as a metric. Evaluation metrics are separate things such as harmful replacement
count, false abstain count, winner accuracy, ROC AUC, and average precision.

### 8. Phrase Preemption

Phrase preemption is not just another shadow score. It handles no-winner cases
where the source phrase belongs to a local construction that should not become
the learner target.

Examples from the current family of concerns:

- `bank on`
- `file past`
- `play out`
- `report back`
- noun-frame expressions such as `the rest of`

Production phrase control currently applies only when the family POS tags are
noun-like. It inspects local tokens around the trigger for frames such as:

- modal + trigger
- `to` + trigger
- subject + trigger + object
- trigger + particle
- selected idiom or noun-of frames

If phrase preemption hits, the policy forces `abstain`. This keeps phrase/no-
winner behavior visible and separately testable instead of burying it inside
ordinary active-vs-shadow scoring.

### 9. Active Rescue

Active rescue is a narrow recovery path for near-tie abstains. It is deliberately
not a general permission to replace.

It can run only when:

- the primary decision abstained
- phrase preemption did not hit
- the primary margin is close enough to the active side
- a backup scorer is available

The backup pass uses `sense_label` evidence. It can rescue only if the backup
decision is `replace`, the backup winner is active, and the backup margin clears
the rescue floor.

This is a bounded false-abstain reducer. It is not allowed to override phrase
preemption.

### 10. Runtime Output

The helper returns a decision record with:

- `decision`
- `reason_codes`
- active score
- top shadow score
- score margin
- shadow winner sense id
- phrase preemption flag
- policy id and selection metadata

Today only `decision=replace` survives into the DOM apply path. `abstain` leaves
the original text visible. `soft_affordance` is reserved by the contract but is
not a current visible product behavior.

## Current Research Controls

Recent decision research deliberately decomposes the algorithm instead of asking
one opaque question.

### Current Incumbent Shape

The oldest control is:

```text
c = masked sentence
a = concatenated all-evidence text
s_i = concatenated all-evidence text for each shadow
score = TF-IDF cosine or sentence-transformer cosine depending on lane
decision = active_score - strongest_shadow_score
phrase = phrase override / phrase guard
```

This is a valid baseline, not a proof of optimality.

### Decision-Rule Matrix

`scripts/testing/semantic_decision_rule_matrix_en_es.py` compares:

- context representation
- sense/evidence representation
- scoring backend
- aggregation rule
- final YES/NO rule
- phrase handling
- negative controls
- threshold sensitivity
- source-family dropout
- discovery-vs-locked summaries

Important negative controls include:

- active-only source
- shadow-only source
- no-shadow competition
- shuffled active/shadow labels
- target-lemma-only evidence
- shuffled/reversed context and evidence for order probes

### Current No-Spend Findings

The active-score surface bakeoff found the first small fixed-source improvement:

- `definition_and_example_rows_separate`
- `max_row_score` or `top_k_mean`
- `0` harmful replacements
- `45` false abstains

The comparable current all-evidence control had:

- `1` harmful replacement
- `46` false abstains

The phrasing/order bakeoff added ordered n-grams, skip-grams, before/after slots,
surface frames, POS frames, heuristic dependency-role frames, negation/modal
signals, ordered evidence, template evidence, paraphrase evidence, and
shuffled/reversed controls.

That bakeoff did not beat the row-level evidence control:

- best row-level evidence control: `0` harmful, `45` false abstains
- best dependency-role approximation: `0` harmful, `55` false abstains
- best pure phrase/frame surfaces also over-abstained at roughly the same level

The context-conditioned evidence bakeoff then loaded the admitted WordNet
definition/example source batch and attached all `87` source rows. It tested
whether `a` should be chosen dynamically from source rows using masked-sentence,
window, before/after, surface-frame, or dependency-role selector contexts.

That first dynamic-`a` pass also did not beat the row-level evidence control:

- best prior separate-row max control: `0` harmful, `45` false abstains
- best source-plus-definition selector: `0` harmful, `53` false abstains
- best pure source-row selector: `0` harmful, `55` false abstains
- sentence-transformer source-row probes reduced false abstains but introduced
  harmful replacements, so they are diagnostic only

The source-row alignment audit explains the limitation of that result:

- `16/87` admitted rows contained the trigger at all
- `7/87` had a two-sided trigger frame
- only `5` families had both active and shadow selector-ready rows

The source-frame gap plan now converts that limitation into a source queue:

- `38` active/shadow sense slots
- `23` missing selector-ready active/shadow slots
- `97` planned candidate requests for trigger-bearing sentence-frame rows
- request rows are compatible with the existing spend-guarded generation runner
- prompts use sense labels and glosses only, not reviewed evaluation sentences

The first live aligned-frame run executed that queue under cost caps. It
generated `97` rows, admitted `36` after leakage/duplicate and
sense-discrimination filtering, and improved the source-admission ablation to
`0` harmful replacements and `1` false abstain on frozen v10 when merged into
the prior `87`-row source control. Active/shadow held-out v2 still had `1`
false abstain, so the result is a research improvement, not a promotion.

The first live run also showed that repeated prompts can collapse into
near-duplicate sentence frames. The planner now emits
`aligned-sentence-frame-v2` prompts with candidate-specific diversity frames.
After the v1 admitted rows were audited, only one selector-ready slot remained
missing. The v2 micro-run requested `5` board-shadow rows, admitted `3`, and
produced a `126`-row composite where all `19` families have both active and
shadow selector-ready rows.

The fully selector-ready v2 context-conditioned bakeoff improved the best
source-plus-definition selector from `0` harmful and `53` false abstains to
`0` harmful and `47` false abstains. The row-level definition/example control
still leads at `0` harmful and `45` false abstains. That means source-aligned
phrasing is helping, but the final dynamic selector is not yet the best
decision surface.

The next source-scope margin bakeoff corrected an important representation
problem: source rows were tested both as partial replacements for the incumbent
row-level evidence and as true additive evidence. The additive surface won:

- `definition_example_plus_source_rows_separate`
- combined LLM-v2 source rows plus the existing WordNet active-related
  reference rows
- `max_row_score`
- `0` harmful replacements
- `37` false abstains across frozen v10, source-heldout v2, phrase-heldout v2,
  and phrase challenge

The no-source definition/example row control on the same four suites was
`0` harmful and `44` false abstains. Source-heldout v2 improved from `0/17` to
`0/12`, and phrase suites stayed clean. The earlier source-plus-definition rows
looked weaker because they omitted the incumbent auxiliary/example rows; that
was a test-surface issue, not proof that source rows were unhelpful.

So this is not a global rejection of dynamic evidence selection. It says the
best current no-spend evidence surface is additive source evidence over the
row-level control, while context-conditioned row selection is still research
infrastructure rather than the leading candidate.

Interpretation:

- shallow frame labels over gloss text are not enough
- the first admitted source batch and first aligned-frame expansion are not
  enough to make dynamic row selection win by itself
- source rows are materially useful when they supplement, rather than replace,
  incumbent definition/example evidence
- order and frame are still worth testing, but they need source/example rows
  whose wording directly resembles runtime contexts
- the current best no-spend path is additive row-level evidence, not another
  threshold tweak

## What Is Not Set In Stone

The current production and research surfaces are intentionally malleable.

Open design choices include:

- the definition of `c`
  - sentence, window, masked view, phrase-risk view, multi-context bundle
- the definition of `a`
  - concatenated evidence, row set, source-weighted rows, examples only,
    context-conditioned rows
- the scoring function
  - lexical overlap, TF-IDF, sentence transformer, cross-encoder, entailment, or
    learned reranker
- aggregation
  - max row, top-k mean, agreement count, source-family agreement, calibrated
    row weighting
- phrase handling
  - phrase-first, phrase override, phrase-as-shadow, separate phrase classifier
- fallback behavior
  - abstain, legacy replace, or future visible soft affordance

None of those should be promoted because they feel elegant. Each needs a frozen
suite, held-out suite, negative controls, and a clear comparison against the
incumbent.

## Current Best Path Forward

The latest evidence points to this order:

1. Keep the production runtime policy unchanged while research continues.
2. Preserve the row-level evidence control as the no-spend incumbent.
3. Treat additive definition/example plus admitted source rows as the leading
   research candidate, while keeping production policy unchanged.
4. Expand aligned evidence rows, especially real examples and admitted source
   rows whose phrasing can match browser contexts.
5. Use the context-conditioned selector machinery as a research tool, but do
   not promote the current source-row result.
6. Mine the remaining active/shadow held-out false abstains and test whether
   each is a source row problem, a scorer/threshold problem, or an aggregation
   problem.
7. Build richer source-aligned examples and re-run the selector/order surfaces
   before changing runtime policy.
8. Reuse the existing matrix harness to compare those new `c` and `a` choices
   on frozen plus held-out suites.
9. Only after a candidate beats the incumbent, consider runtime policy changes
   and run the rulegen quality loop required by `AGENTS.md`.

Process rule:

- keep every active idea in
  `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- regenerate `docs/test_outputs/semantic_decision_research_lanes_latest.md`
  after changing a lane state
- never use a generic `done` state; distinguish idea, partial harness,
  unswept-ready harness, completed sweep, source-program lane, and parked
  second-lane candidate

This is not handcrafting every case if the promoted rule is general:

- source rows must come from repeatable source adapters or documented admission
  contracts
- phrase rules must be framed as reusable local constructions
- thresholds must be selected outside the exact cases used for final claims
- failure classes must be promoted into held-out coverage before being used as
  evidence of broad progress

## Promotion Criteria

A new setup is promotable only if it:

- keeps harmful replacements at `0` on frozen and held-out suites
- matches or improves false abstains versus the incumbent
- improves or preserves active/shadow/no-winner winner accuracy
- passes negative controls
- beats the incumbent outside the threshold-selection cases
- keeps phrase/no-winner behavior visible separately
- is simpler, or clearly more accurate enough to justify complexity

If no candidate beats the incumbent, that is still useful. It means the bottleneck
is probably source coverage, evidence representation, or evaluation coverage
rather than the final comparison formula.
