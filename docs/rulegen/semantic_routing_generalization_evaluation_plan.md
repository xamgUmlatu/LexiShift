# Semantic Routing Generalization Evaluation Plan

Status: active planning
Role: production-stabilization plan
Purpose: define the evaluation workstream required to move semantic veto from the narrow `en-es` emitted-sibling runtime slice to a production-trustworthy, more general blocker system
Last updated: 2026-04-16
Last verified: 2026-04-16 current runtime/publication contract review plus the targeted semantic publication/runtime seam tests and current generalization evidence docs
Source-of-truth: this plan is the canonical next-step document for semantic-veto generalization; implementation truth still lives in code, test scripts, and `docs/developer/feature_state_matrix.md`

Routing note:

- use `docs/rulegen/semantic_routing_publication_contract.md` and `docs/rulegen/semantic_routing_runtime_readiness.md` for current shipped contract truth
- use `docs/rulegen/semantic_routing_en_es_publish_checklist.md` for the first-launch operational runbook
- use this document only when the question is how to move beyond the current emitted-sibling PoC and prove broader blocker-generation quality

## Short answer

Yes, this workstream goes back to the testing lab.

But not the earlier ad hoc lab.

The remaining problem is no longer basic runtime plumbing.
The remaining problem is proving that automatically generated blocker sets generalize beyond the current narrow reviewed slice without introducing harmful replaces.

That means the right next phase is:

1. freeze a rigorous evaluation stack,
2. run controlled generalization campaigns,
3. expand review only where the campaigns say the frontier is ambiguous,
4. keep the runtime path conservative until offline evidence is strong enough.

## Current boundary

The repo now has:

- a real browser-extension runtime path,
- helper-side `semantic_admit_batch`,
- a named production decision policy,
- runtime diagnostics,
- a narrow published `en-es` emitted-sibling `status=ready` subset,
- a fixed-shadow sentence-level veto harness,
- and multiple shadow-mining / promotion evaluation lanes.

What it does not yet have is proof that automatically mined competition sets beyond that emitted-sibling PoC are good enough for broad production use.

That is the key distinction:

- runtime scorer/policy is already reasonably general,
- blocker generation is not yet proven general.

## Production objective

Treat semantic veto as a conservative blocker layer over already-detected lexical matches.

The production-stability question is:

> For a broad set of real lexical matches, can we automatically publish blocker sets that cause the runtime gate to abstain when the lexical match is semantically unsafe, while avoiding harmful replace regressions and keeping false abstains bounded?

That question has four independent subproblems:

1. fixed-shadow scorer stability
2. shadow-set generation coverage
3. shadow-set promotion precision
4. phrase / frame exceptions that should not be treated as ordinary sense competition

## Current frozen baseline

These are the control reads the next generalization campaigns should compare against.

They are not proof of broad readiness.
They are the current measured starting point.

### Fixed-shadow runtime scorer control

Use the best currently measured zero-harmful-replace row from the fixed-shadow sentence harness as the scorer control:

- dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- decision accuracy: `77.5%`
- replace precision / recall: `100.0%` / `43.8%`
- harmful replace / false abstain: `0.0%` / `56.2%`

Interpretation:

- the scorer/gate already has the desired abstain-first safety shape,
- but it still misses many clear active rows even when the blocker set is fixed correctly.

### Sentence-transformer reference row

Keep the current sentence-transformer read as a reference, not as the main control:

- config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.15`
- decision accuracy: `75.0%`
- replace precision / recall: `100.0%` / `37.5%`
- harmful replace / false abstain: `0.0%` / `62.5%`

Interpretation:

- the heavier scorer is not yet beating the lexical control on the fixed-shadow harness under the current strict safety budget.

### Auto-shadow veto lower-bound controls

Use the current veto-proxy rows as the blocker-generation baseline ladder:

| Row | Meaning | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: |
| `no_shadows` | no blocker generation | `81.1%` | `0.0%` | `100.0%` | `0.0%` |
| `auto_shadows` | best plain source-only lexical lane | `87.4%` | `42.4%` | `57.6%` | `2.1%` |
| `borrowed_trigger_auto_shadows` | source-only plus borrowed-trigger seeds | `89.1%` | `51.5%` | `48.5%` | `2.1%` |
| `reviewed_auto_shadows` | reviewed-trigger auto lane | `93.7%` | `66.7%` | `33.3%` | `0.0%` |
| `curated_shadows` | current lower-bound oracle ceiling | `100.0%` | `100.0%` | `0.0%` | `0.0%` |

Interpretation:

- current source-only blocker generation is materially better than no veto,
- but it is still far from the curated blocker ceiling,
- and most of the remaining gap is still blocker-generation quality rather than scorer choice.

## Evaluation layers

Use four layers and keep them separate.

### Layer 1. Fixed-shadow runtime scorer stability

Purpose:

- prove that the runtime decision rule is stable when the active sense and shadow set are already known
- keep harmful replace at or near zero while exploring scorer or threshold changes

Primary artifacts:

- `scripts/testing/semantic_routing_sentence_veto_harness.py`
- `scripts/testing/semantic_routing_sentence_veto_sweep.py`
- `scripts/testing/semantic_routing_sentence_veto_support.py`

Interpretation:

- this layer answers whether the veto algorithm itself is behaving sensibly
- this layer does not answer whether the blocker set is good enough

### Layer 2. Auto-shadow publication quality

Purpose:

- prove whether the automatically generated blocker set contains the right competitors
- quantify `seed_missing`, `candidate_missing`, `promotion_miss`, and false-abstain pressure

Primary artifacts:

- `scripts/testing/semantic_shadow_gold_proxy_en_es.py`
- `scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py`
- `scripts/testing/semantic_shadow_experiment_matrix_en_es.py`
- `scripts/testing/semantic_shadow_experiment_compare_en_es.py`
- `scripts/testing/semantic_shadow_promotion_gap_en_es.py`

Interpretation:

- this is the main current frontier
- most production risk still lives here

### Layer 3. Held-out family generalization

Purpose:

- stop overfitting to the same reviewed trigger families
- learn whether a change helps broadly or only on the current reviewed overlap

Required shape:

- split trigger families into:
  - control / tune families
  - held-out evaluation families
- never choose thresholds only by aggregate metrics on the same families used to design the feature
- keep the split explicit in:
  - `docs/test_inputs/semantic_routing_generalization_splits_en_es.json`

Interpretation:

- this is the minimum honest generalization test
- it is much more important than simply adding more rows to one giant benchmark bucket

### Layer 4. Runtime dry-run observability

Purpose:

- validate that offline results still look sane in actual browser runtime
- inspect how much of the active runtime rule population is even eligible for semantic veto

Primary signals:

- semantic-eligible match count
- semantic-ready match count
- policy replace / abstain counts
- fallback-path counts
- readiness coverage among active SRS rules

Interpretation:

- this is not the main training surface
- it is the sanity-check surface before rollout

### Cross-layer bound artifact

Use one explicit cluster-aware bound read to summarize the current corridor:

- `scripts/testing/semantic_routing_generalization_bound_en_es.py`
- `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`

Interpretation:

- this is not a replacement for the four layers above
- it is the current scorecard that converts those layers into one conservative `en-es` read

## Are we back to the testing lab?

Yes.

Specifically:

- offline harnesses are now the main development surface again
- runtime should stay conservative and mostly unchanged while the generalization campaigns run
- product confidence should come from campaign evidence, not from anecdotal browsing sessions

The right mental model is:

- runtime path is paved
- testing lab now decides whether the data feeding that path is trustworthy

## Production-stabilization plan

Run the next work as six explicit stages.

### Stage 0. Freeze the control stack

Before new experimentation:

- freeze one fixed-shadow sentence-veto control row
- freeze one auto-shadow control row
- freeze one reviewed-auto and one curated reference row
- freeze one held-out family split for the next campaign

Required controls:

- fixed-shadow runtime scorer control
- `reviewed_auto_control`
- best current source-only automatic row
- `curated_shadows`
- `no_shadows`

Rule:

- do not casually compare new experiments against mixed campaign baselines

### Stage 1. Add explicit family buckets and held-out splits

Goal:

- make generalization measurable instead of anecdotal

Required metadata per reviewed family:

- trigger family id
- active POS
- likely shadow POS relation
- phrase-sensitive vs plain lexical
- likely idiom / frame risk
- active-support strength bucket
- trigger-support strength bucket
- whether current miss is `seed_missing`, `candidate_missing`, or `promotion_miss`

Why this matters:

- once these buckets exist, we can ask whether a change helps nouns but hurts verbs, or helps strong-support families but not weak ones
- this is much more informative than one aggregate score

### Stage 2. Run generalization campaigns by miss type

Do not optimize “quality” vaguely.
Optimize one miss family at a time.

#### Campaign A. Seed coverage

Question:

- how do we reduce `seed_missing` without opening the floodgates

Primary levers:

- trigger-support threshold
- forward-gloss seed settings
- neighbor-borrow / auxiliary seed lanes

Primary metrics:

- gold-trigger coverage
- candidate-pool trigger recall
- harmful-allow rows classified as `seed_missing`

Guardrails:

- candidate precision
- veto-proxy overblocking

#### Campaign B. Candidate generation

Question:

- how do we reduce `candidate_missing`

Primary levers:

- lexical semantic bridge
- additional source families
- compact LLM candidate suggestion lanes

Primary metrics:

- candidate-pool trigger recall
- `candidate_missing` count
- veto-proxy harmful allow

Guardrails:

- precision
- overblocking

#### Campaign C. Promotion / pruning

Question:

- how do we keep the good blockers while dropping junk

Primary levers:

- support score threshold
- max promoted shadows
- POS compatibility
- active-side support
- source agreement
- representative pruning

Primary metrics:

- abstain recall
- harmful allow
- overblocking
- `promotion_miss`

Guardrails:

- fixed-shadow scorer safety remains unchanged

#### Campaign D. Phrase / frame separation

Question:

- which runtime failures are not really shadow-selection failures

Primary levers:

- phrase-family metadata
- frame guards
- idiom-specific suppression heuristics

Primary metrics:

- harmful replace rows explained by phrase/frame class
- false abstain rows explained by phrase/frame class

Why this is separate:

- if phrase issues stay mixed into ordinary shadow mining, the blocker set will stay muddy

### Stage 3. Add active-learning review packets

Do not manually author huge broad test sets first.

Instead, generate review packets only for rows that are:

- high-impact harmful-allow cases
- unstable across top candidate rows
- contradictory across source families
- dominant within one bucket that still fails

This should produce compact, high-information review work instead of large manual suites.

### Stage 4. Launch-gate scorecard

Before enabling semantic veto for a wider `en-es` slice, require one explicit launch scorecard.

Recommended gate categories:

- fixed-shadow runtime safety
- auto-shadow veto lower bound
- held-out family generalization
- readiness coverage among active SRS rules
- runtime dry-run fallback rate

Recommended gate questions:

1. Does the fixed-shadow sentence harness still preserve the abstain-first safety shape?
2. Does the best auto-shadow lane close enough of the curated-shadow gap to justify rollout?
3. Does the held-out family split still behave similarly to the tuned split?
4. Are enough active runtime rules actually `semantic_admission.status=ready` to matter?
5. Is the fallback path rare enough on the intended launch slice?

### Stage 5. Widen runtime eligibility only after the data stabilizes

Current runtime scope is intentionally narrow:

- SRS-origin rules only
- rules already carrying semantic pointers
- default-off

Do not widen beyond that until:

- blocker quality is stable,
- held-out families behave acceptably,
- and runtime diagnostics show real ready-coverage rather than mostly fallback traffic.

## What “generalized against any word” actually means

Do not define it as “literally every possible word on the internet”.

Define it operationally:

- any active runtime lexical rule that carries a stable active-sense pointer
- for pairs where a semantic inventory can be published offline
- with blocker generation driven by generic signals rather than per-word hacks

That is the real production target.

## What should stay out of the main frontier for now

Do not spend the next cycle on:

- cloud transport decisions
- BetterDiscord/plugin runtime wiring
- polished user-facing affordance UI
- large model-choice churn on the runtime scorer

Those are downstream.
The main risk is still blocker generation quality.

## Budgeted LLM-data plan

Use LLM budget for narrow, high-leverage data only.
Do not use it to generate giant end-to-end gold labels.

### Priority 1. Candidate-shadow suggestion packets

Goal:

- reduce `candidate_missing` on high-impact ambiguous trigger families

Input to LLM:

- source trigger phrase
- active target lemma
- active POS
- active gloss / sense label
- short source-side evidence bundle
- any already-mined shadow candidates

Output wanted:

- 3-8 candidate competing target lemmas
- POS for each
- one short gloss / explanation
- confidence bucket
- whether it looks like:
  - ordinary sense competition
  - phrase/idiom issue
  - likely junk

Why this is first:

- this gives the highest information gain per token spent
- it directly attacks the current `candidate_missing` frontier

### Priority 2. Phrase / idiom / frame-control packets

Goal:

- separate phrase/frame hazards from ordinary shadow competition

Input to LLM:

- English trigger
- active target
- sample sentence or short phrase-family cues

Output wanted:

- short list of idioms / phrasal frames / control patterns where literal replacement should usually be blocked
- compact machine-usable cue text
- optional category tag such as `particle_frame`, `light_verb_frame`, `idiom`, `verb_control`

Why this is second:

- this is likely the cleanest way to keep phrase noise out of the blocker miner

### Priority 3. Compact sense-cue text for active vs shadow comparison

Goal:

- improve evidence quality when source dictionaries are too terse

Input to LLM:

- active sense record
- shadow sense record
- raw glosses / labels / examples if available

Output wanted:

- 1-2 short cue lines per sense
- no long prose
- no synthetic examples unless explicitly requested

Why this is third:

- useful, but less urgent than actually finding the right blockers

### Priority 4. Bucket metadata labeling for reviewed families

Goal:

- make the evaluation split more informative

Input to LLM:

- family description
- current misses / examples

Output wanted:

- bucket labels such as:
  - noun / verb / adjective
  - phrase-sensitive
  - idiom-risk
  - strong-active-support / weak-active-support
  - abstract / concrete / job-family / body-part / motion / institution

Why this is fourth:

- this helps evaluation organization, but it does not directly improve blocker discovery

## What not to buy with LLM budget

Do not spend budget first on:

- large synthetic sentence benchmarks
- direct final `replace` / `abstain` labels for arbitrary words
- threshold tuning suggestions
- giant all-word competitor lists with no active frontier link

Those are much more expensive and much easier to overfit.

## Recommended first budget ask

If the budget is limited, the first LLM dataset should be:

1. unresolved harmful-allow families from the current best source-only auto-shadow lane
2. for each family:
   - candidate shadow suggestions
   - phrase/frame classification
   - compact gloss/cue text only when needed

That gives the best chance of moving the blocker frontier without creating a giant manual-data dependency.
