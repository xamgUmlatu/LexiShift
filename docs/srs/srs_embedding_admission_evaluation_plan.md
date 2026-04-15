# SRS Embedding Admission Evaluation Plan

Status: Planning / research gate
Role: Planning / research gate
Purpose: define the exact evaluation needed before adding embedding-based semantic generalization to SRS admission scoring
Last updated: 2026-04-15
Last verified: 2026-04-15
Verification:
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_profile_schema.md`
- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/seed.py`
- `core/lexishift_core/frequency/sqlite.py`
- `apps/gui/src/language_packs_catalog.py`
- `docs/TODOs.md`

Related design:
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_roadmap.md`

## Decision summary

Embedding-based semantic generalization is worth evaluating, but it should not be added blindly and it should not replace the current symbolic preference architecture.

Current recommendation:

- keep explicit interests and derived topic weights as the primary admission guidance layer
- evaluate embeddings only as a secondary semantic-generalization signal
- require the embedding layer to emit an inspectable scalar feature, not a hidden vector-native ranking path
- make the decision from a controlled internal bake-off, not from intuition alone

This is a research gate, not an implementation spec.

## What is already true

Current admission architecture already has the correct extension seam:

- user preferences normalize into continuous weights in `AdmissionProfileFeatures`
- candidate traits are extracted separately from seed metadata and lexical forms
- the selector consumes scalar utility terms
- preview and diagnostics explain the score after ranking

Current code already supports:

- `interests`
- `explicit_topic_weights`
- `implicit_topic_weights`
- `topic_weights`
- lexical-form matching
- candidate `topic_hints`

Current code does not yet support:

- a dedicated semantic-affinity term sourced from embeddings
- a pair-local embedding-backed admission evaluation harness
- a clear decision on whether static word vectors or multilingual text embeddings are the better fit

The repository does already have embedding resource plumbing on the GUI/resource side, including fastText packs and aligned cross-lingual packs, so this work is an extension of the current system rather than a new subsystem from zero.

## Why this deserves evaluation

The open question is not whether embeddings can add signal. They can.

The open questions are:

1. whether they improve concept generalization on LexiShift admission tasks more than simpler alias/topic-expansion approaches,
2. whether they help on supported pairs such as `en-es` and later `en-ja`,
3. whether they preserve core-vocabulary stability,
4. whether their behavior remains explainable enough for preview UX and tuning.

That makes this an evaluation problem, not a product-faith problem.

This evaluation is about topic/domain semantic generalization.

It is not the first evaluation for:

- register/style preferences such as `slang`
- exact implicit lexical-trend lane policy

Those are adjacent future extensions, but they are not the same decision.

## Architectural constraints

Any embedding-based admission extension must obey these constraints:

### 1. Symbolic preferences remain authoritative

If the user explicitly selects `animals`, that explicit declaration remains the first-class preference signal.

Embeddings may generalize that concept, but they do not replace:

- `interests`
- `explicit_topic_weights`
- `topic_weights`

### 2. The embedding layer must output a scalar feature

The selector should never consume high-dimensional vectors directly.

The admissible contract is:

```text
semantic_interest_affinity(item) -> [0, 1]
```

Optionally with diagnostics:

- matched_interest
- matched_representation
- similarity_raw
- similarity_calibrated
- embedding_provider

### 3. Embeddings are secondary and capped

The embedding-derived term must not dominate:

- `coverage_gain`
- explicit symbolic `topic_affinity`

If embeddings are added, they should act as:

- sparse-metadata fallback
- semantic generalization layer
- weaker companion to explicit symbolic interests

### 4. Missing embedding resources stay neutral

Admission must not become unavailable or unstable when embedding resources are absent.

If no embedding provider is active:

- semantic affinity contributes `0`
- existing symbolic behavior remains intact

### 5. Diagnostics must stay legible

The preview must still be able to say why a word moved.

That means the embedding path must be explainable as:

- “boosted because semantically close to `animals`”
- not “boosted because opaque vector math happened”

## Candidate solution families

The evaluation should compare families, not only one model.

### A. Symbolic-only control

This is the current baseline:

- explicit interests
- topic metadata
- lexical exact-form match

This control is required so we measure real gain instead of novelty.

### B. Symbolic + alias/topic expansion control

This is the cheapest non-embedding generalization path.

Example:

- `animals` expands to `pets`, `wildlife`, `zoology`, `veterinary`

This control matters because some of the perceived “need for embeddings” may actually be taxonomy/alias coverage debt.

### C. Symbolic + static word/subword embeddings

This family is attractive because:

- the repo already has fastText resource plumbing
- it is relatively cheap
- it handles out-of-vocabulary forms better than pure token lookup

Likely strengths:

- cheap local inference
- lexical neighborhood expansion

Likely weaknesses:

- weak sense disambiguation
- more brittle behavior on abstract or polysemous concepts

### D. Symbolic + multilingual text embeddings

This family is attractive because it is closer to concept-level semantic retrieval.

Likely strengths:

- better semantic generalization
- better cross-lingual concept matching
- better behavior for phrase-like interests such as `live streaming`, `crime drama`, `cute animals`

Likely weaknesses:

- higher resource and packaging cost
- greater need for calibration
- more complex offline indexing story

## Candidate text representations

The evaluation should also compare what gets embedded, not only which model gets used.

### Interest-side representation

Start with:

- normalized interest token

Then optionally compare:

- normalized interest phrase
- interest token plus curated aliases

### Item-side representation

Start with the semantic text already closest to the current admission seam:

- lemma
- lexical forms
- topic hints

Then compare richer text where available:

- lemma plus topic hints
- lemma plus available source-side gloss text
- lemma plus topic hints plus available gloss text

Current repository state suggests:

- `topic_hints` and lexical forms are already available in the seed/profile-bootstrap path
- gloss-adjacent source material exists upstream in frequency/dictionary resources, but is not yet a standard admission feature

So richer semantic text may improve results, but it should be evaluated rather than assumed.

## Proposed scoring shape

The likely winning architecture is:

```text
score(user, item) =
  coverage_gain
  + symbolic_topic_affinity
  + semantic_interest_affinity
  + proficiency_fit
  + challenge_fit
```

with the constraint that:

```text
semantic_interest_affinity << coverage_gain
semantic_interest_affinity <= symbolic_topic_affinity cap
```

Two acceptable semantic-affinity formulations are:

### Max-over-interests

```text
semantic_interest_affinity(item) =
  max_k [ interest_weight_k * calibrated_similarity(interest_k, item) ]
```

This is the preferred starting shape because it is easy to inspect.

### Weighted blended user vector

```text
user_interest_vector = normalize(sum_k interest_weight_k * embedding(interest_k))
semantic_interest_affinity(item) =
  calibrated_similarity(user_interest_vector, item)
```

This is less preferred initially because it is harder to debug and easier to over-smooth.

## Evaluation tasks

The bake-off should answer four concrete product questions.

### 1. Sparse metadata generalization

Example:

- user selects `animals`
- explicit topic metadata is sparse
- does the candidate method still lift words such as `fur`, `claws`, `wildlife`, `kennel`, `veterinarian`?

### 2. Cross-lingual preference relevance

Example:

- user interests are stored in one language-normalized form
- candidate items are in Spanish or Japanese
- does the method still recover semantically relevant target vocabulary?

### 3. Core-vocabulary preservation

Example:

- user selects `sports`
- `penal` or `stadium` should become more likely
- ordinary core words should still remain in the active frontier

### 4. Explainability

Example:

- preview should still be able to tell the user:
  - that `penal` was boosted by symbolic topic match,
  - or that `wildlife` was boosted by semantic proximity to `animals`

## Evaluation dataset design

This should be a small, explicit, product-facing evaluation set first, not a giant benchmark.

For each active pair, define:

- a concept label
- positive expected words
- acceptable nearby words
- obvious false-positive words
- a neutral/core vocabulary anchor set

Initial concept set:

- `animals`
- `sports`
- `music`
- `games`
- `anime`
- `finance`
- `livestream`
- `comedy`

Initial pair focus:

- `en-es`
- `en-ja` later if data coverage supports it

Each concept lane should evaluate:

- symbolic-only baseline
- symbolic + alias expansion
- symbolic + static embeddings
- symbolic + multilingual text embeddings

Do not include `slang` in the first topic bake-off.

Reason:

- `slang` is a register/style preference rather than a topic/domain preference
- it should eventually be evaluated on its own axis, not mixed into the topic benchmark

## Metrics

The evaluation should report product-facing metrics, not only cosine numbers.

Required metrics:

- concept-hit rate in top `N`
- concept-hit rate inside planned active `40`
- neutral overlap with baseline active `40`
- false-positive leakage into unrelated concept lanes
- median and max semantic uplift applied
- explanation coverage rate

Useful secondary metrics:

- runtime cost per preview
- local resource size
- cold-start behavior when no embedding index is loaded

The bake-off should also explicitly note whether semantic generalization reduces the need for a separate lexical-trend lane, but it should not assume those are interchangeable.

## Acceptance criteria

An embedding-backed approach should only move to implementation if it satisfies all of these:

1. It beats symbolic-only on sparse-metadata concept recall.
2. It does not materially collapse core-vocabulary retention in the active frontier.
3. It outperforms or meaningfully complements simple alias/topic expansion.
4. It can produce user-legible diagnostics.
5. Its local footprint and latency are acceptable for helper-driven preview and admission planning.

If those conditions are not met, the right next step is:

- improve aliasing
- improve metadata coverage
- defer embeddings

## Recommended implementation order after the bake-off

If the bake-off is positive, implementation should proceed in this order:

1. Add an analysis-only semantic-affinity harness.
2. Add a non-live helper preview mode that reports semantic affinity without changing ranking.
3. Add `semantic_interest_affinity` as a separate scalar utility term.
4. Cap it conservatively and log the winning concept/similarity source.
5. Tune pair-locally only after preview behavior is legible.

## Exact next steps

1. Define the small concept evaluation set for `en-es`.
2. Add an offline admission comparison harness:
   - symbolic-only
   - symbolic + alias expansion
   - symbolic + static embeddings
   - symbolic + multilingual text embeddings
3. Decide the item semantic text representation to test first:
   - lemma only
   - lemma + topic hints
   - lemma + topic hints + gloss text when available
4. Produce a short evidence report before any live admission integration.

## Final recommendation

The correct current stance is:

- yes, this deserves targeted research
- no, it does not require outside expert sign-off before we move
- yes, embeddings are a realistic path for smarter generalization
- no, embeddings should not replace the symbolic admission architecture

The most likely long-term shape is:

- symbolic interests and topic weights first
- semantic embeddings second
- diagnostics and caps always explicit
