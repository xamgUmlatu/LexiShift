# SRS Preference Signal Admission V1 Contract

Status: Draft decision log
Role: Draft decision log
Purpose: lock the concrete `v1` admission contract for preference signals before tuning live user-personalized admission weights
Last updated: 2026-04-15
Last verified: 2026-04-15 code/doc review plus synthetic admission sanity harness
Verification:
- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/selector.py`
- `core/tests/srs/test_profile_bootstrap.py`
- `scripts/testing/srs_admission_preference_sanity.py`
- `scripts/testing/srs_frequency_topic_coverage.py`
- `core/tests/dev/test_srs_admission_preference_sanity.py`
- `core/tests/dev/test_srs_frequency_topic_coverage.py`
- `docs/test_outputs/srs_admission_preference_sanity_latest.json`
- `docs/test_outputs/srs_admission_preference_sanity_latest.md`
- `docs/test_outputs/srs_frequency_topic_coverage_latest.json`
- `docs/test_outputs/srs_frequency_topic_coverage_latest.md`
- `docs/test_outputs/srs_admission_interest_review_en_es_latest.md`
- `docs/test_outputs/srs_admission_interest_review_en_es_metrics_latest.md`

Related design:
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_embedding_admission_evaluation_plan.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_roadmap.md`
- `docs/srs/srs_preference_update_and_rebalance_policy.md`

## Why this is the final architecture

The final planner architecture should stay split into four layers:

1. profile input normalization
2. lexical candidate trait extraction
3. continuous utility scoring
4. diagnostics/preview rendering

That separation is already the correct long-term shape:

- user preferences live in normalized planner context, not in seed generation
- lexical truth lives in candidate traits, not in user profile objects
- admission ranking is continuous math over reusable features, not a pile of topic-specific branches
- preview/diagnostics explain the decision after scoring, without changing the scoring contract

This is the right architecture because it preserves both continuity and inspectability:

- UI categories such as `animals` or `gaming` are product inputs
- the planner consumes continuous weights such as `topic_weights["animals"] = 1.0`
- candidates expose continuous match traits such as topic hints, lexical forms, and difficulty estimates
- the selector produces a continuous final score instead of category-specific if/else behavior

So the product can stay category-driven at the surface while the engine stays weight-driven internally.

## V1 scope

`v1` means:

- keep `seed.py` as the neutral candidate generator
- keep `profile_bootstrap` as a reranking layer over that neutral pool
- make explicit user interests the first preference signal to tune seriously
- keep proficiency and challenge fit as existing continuous side signals
- treat implicit personalization as a deferred upstream producer of derived topic weights, not as raw browsing logic

`v1` does not mean:

- raw page-history admission logic
- topic quotas
- hard topic filtering
- automatic destructive reset
- hidden profile heuristics without diagnostics
- register/style modeling such as `slang` forced into the topic lane

## Decision log

### D1. Categories are UI inputs, not scoring primitives

The planner should not directly score category labels such as `animals_mode = true`.

Instead:

- the UI/edit model collects categorical user choices
- normalization converts them into continuous topic weights
- the scorer consumes only normalized features

That keeps the final architecture extensible:

- a curated topic taxonomy can be added later
- aliases can be added later
- onboarding can emit the same weight map later
- implicit topic mining can emit the same weight map later

without changing the scorer contract.

### D2. Explicit interests map to authoritative topic weights in `v1`

Current normalization already maps each selected interest to a normalized topic token with weight `1.0`.

That is the correct `v1` behavior.

So if the user explicitly selects `animals`, the planner contract is:

- `interests = ["animals"]`
- `explicit_topic_weights["animals"] = 1.0`
- `topic_weights["animals"] = 1.0`

This is intentionally stronger than soft implicit signals. Explicit intent should be authoritative.

### D3. Topic namespace stays normalized and freeform in `v1`

`v1` should keep the topic namespace simple:

- lowercase
- separator-normalized
- freeform normalized tokens such as `daily_life`, `animals`, `streaming`

This is the correct short-term choice because the current code already supports it and because it avoids premature ontology work.

Later, a curated taxonomy or alias layer can sit on top of the same normalized token contract.

### D4. Candidate matching uses lexical truth first, with two matching seams

Candidate preference matching should be computed against lexical candidate traits, not against UI categories.

Current `v1` matching seams are:

- topic-hint match
  - `sense_topics`
  - `topics`
  - `topic`
  - `profile_topics`
- lexical exact match
  - normalized lemma/surface/reading/sublemma variants

This is the correct boundary:

- topic-hint match is the primary product path
- lexical exact match is a secondary seam that helps when topic metadata is sparse

Lexical exact match should remain a compatibility and extensibility seam, not the core product story.

### D5. Admission scoring stays continuous

The current executable `profile_bootstrap` score is:

```text
profile_score(i) =
  0.55 * coverage_gain(i)
  + 0.15 * preference_affinity(i)
  + 0.10 * proficiency_fit(i)
  + 0.10 * challenge_fit(i)
```

with:

- `coverage_gain(i)` from lexical commonness / admission weight
- `preference_affinity(i)` from the strongest topic or lexical match against normalized topic weights
- `proficiency_fit(i)` from a taper against estimated proficiency
- `challenge_fit(i)` from a target-centered spread function

This is the right architecture because:

- it preserves a continuous frontier
- it allows multiple signals to combine rather than override
- it gives us inspectable per-term diagnostics
- it will extend cleanly when later terms become active

The long-term utility target still remains:

```text
score(user, item) =
  proficiency_fit
  + challenge_fit
  + preference_affinity
  + coverage_gain
  - lexical_risk
  - redundancy
  + exploration_bonus
```

But `v1` should only tune the positive terms that are already real and inspectable.

### D6. Bubble protection comes from weighting, not hard rules

`v1` should not use hard topic quotas or hard off-topic filters.

Instead, bubble protection comes from three facts:

- the neutral seed generator remains frequency- and dictionary-driven
- `coverage_gain` remains the dominant weighted term
- missing preference signals stay neutral instead of collapsing the pool

This is the safest short-term product behavior:

- interests can move ranking materially
- the set still retains common/general vocabulary
- we do not accidentally create a narrow topical bubble with brittle rules

The intended semantics are probabilistic rather than absolute:

- preference signals change relative admission likelihood
- they do not erase the neutral/core frontier
- a user with `music` interest should still receive general high-coverage words
- a user with no interests should stay near the neutral frequency order

### D7. Missing signals must stay neutral and explicit

If the profile lacks interests, proficiency, or challenge preference, the planner should:

- contribute `0` for that signal
- keep ranking near neutral frequency order
- surface the missing signal explicitly in diagnostics

That is already the current seam, and it is the correct one.

This avoids hidden fallbacks and keeps planner behavior inspectable.

### D8. Implicit personalization must emit derived weights, not raw history

The architecture is already compatible with implicit personalization, but only through derived signals.

The contract should be:

- upstream mining produces normalized topic weights such as `empirical_trends.topic_bias`
- the planner consumes those weights through the same normalized profile feature layer

The planner should not consume:

- raw page content
- raw URL history
- opaque embedding blobs

If lexical mining is later added, it should still land as normalized weighted signals with support/confidence, not raw browsing traces.

### D8a. Register/style preferences are not topic preferences

If LexiShift later wants preferences such as:

- `slang`
- `formal`
- `colloquial`

those should not be modeled as ordinary topic tokens.

They are better treated as a separate register/style axis with:

- separate normalized profile fields
- separate candidate traits
- separate diagnostics

That keeps the current topic model clean and avoids turning the topic namespace into an incoherent catch-all.

### D9. Preview is the primary acceptance surface

The admitted-word sample preview is the first product-quality acceptance surface for this workstream.

That means:

- it must show whether the profile was effectively neutral or not
- it must show which signals were active and missing
- it must show per-item explanations and rank deltas
- it must stay non-mutating

If the preview cannot clearly show why ranking changed, the architecture is not ready for coefficient tuning.

The preview surface should also distinguish two layers:

- deterministic scoring/diagnostics
- stochastic admission selection from the scored neutral frontier

So the product contract is:

- the scorer/reranker remains deterministic for testability
- the shared selector may vary across presses because it samples from the weighted frontier without replacement
- the sample button should reuse that same selector rather than layering a second sampling step inside an already admitted pool
- fixed sampling seeds are reserved for tests and controlled debugging

### D10. Real metadata coverage is the main remaining uncertainty

The current architecture can score preference-aware admission correctly.

The main remaining uncertainty is not the planner shape. It is metadata coverage:

- how often the live seed pool actually carries usable topic hints
- how reliable those hints are across supported pairs and frequency sources
- how often lexical exact match would be doing the work instead of topic metadata

That is why the next implementation slice needed sanity and coverage reporting before live weight tuning.

Current checkpoint on `2026-04-15`:

- the synthetic preference sanity harness is implemented and passing, with a remaining `WARN` only because that harness does not itself inspect live pack metadata
- the live frequency topic coverage audit is implemented and currently passes the local `freq-ja-bccwj` and `freq-es-cde` packs while warning that `freq-en-coca` still lacks topic columns
- GUI/manual frequency-pack conversion can now enrich `freq-ja-bccwj` and `freq-es-cde` from companion Kaikki/Wiktionary SQLite topic metadata when those local source packs exist
- live admission preview has confirmed that explicit interests can move real `en-es` bootstrap candidates materially while leaving core-vocabulary weighting intact
- the options admission-sample button is now expected to simulate a weighted admitted set from the scored bootstrap frontier instead of echoing a deterministic top `N` cutoff
- a 200-seed `en-es` Monte Carlo review now confirms that the live selector is sampling from the correct frontier and that topic-biased profiles produce positive but still modest uplift in admitted-topic hit rate; that is sufficient to validate the architecture, but not yet sufficient to claim final tuning quality

### D11. Exact lexical trends should use a bounded lane, not inflated global weights

There is a real product use case for exact implicit lexical trends:

- trending words
- repeated page vocabulary
- temporarily salient proper or niche terms

Those words do not fit the same control surface as durable topic/domain preference.

So the preferred long-term direction is:

- keep topic/domain guidance inside the main continuous admission scorer
- add exact lexical trends later as a separate bounded lane with a small reserved budget
- avoid trying to make exact-word trends win early by inflating one global lexical coefficient

This is preferred because it:

- preserves core-vocabulary stability
- allows exact trending words to appear while they matter
- is easier to decay, cap, and explain

Conceptually:

- main admission frontier remains deterministic and scored
- a small lexical-trend lane can contribute additional candidates under explicit caps
- preview can show both the main scorer explanation and the lexical-trend source when relevant

### D12. Live core admission uses an explicit stochastic selector

Current product behavior should now be:

- deterministic ranked/scored frontier construction
- explicit weighted-without-replacement admission selection into the active set
- the same seedable selector reused by preview and live bootstrap paths

That means the current system is now probabilistic at the admission-selection layer while remaining deterministic at the scoring layer.

The correctness constraints are:

- stochasticity must be an explicit selection-policy decision, not an accidental side effect
- preview and live bootstrap must agree when given the same seed and inputs
- diagnostics must still expose the deterministic scored frontier underneath the stochastic selection

## Acceptance criteria for the next implementation slice

Before tuning live preference coefficients more aggressively, the following should be true:

1. A neutral profile keeps ranking close to neutral seed order.
2. An explicit interest such as `animals` measurably promotes topic-matching items in a deterministic sanity harness.
3. Planner diagnostics show which signals were active, which were missing, and where they came from.
4. Admission preview remains non-mutating.
5. A follow-up coverage pass can tell us whether live seed metadata is rich enough to justify stronger topic-affinity tuning.
6. The user-facing sample button may vary across presses, but its draws must come from the same weighted selector that live admission uses against the scored frontier.

## Ordered next steps

### 1. Synthetic sanity first

Add and keep a deterministic synthetic sanity harness for:

- neutral profile behavior
- explicit-interest uplift
- implicit topic-bias uplift

This proves the contract itself before we depend on live DB metadata.

### 2. Live metadata coverage second

Keep and extend a coverage report against the real supported frequency sources so we can answer:

- what fraction of seed candidates have usable topic metadata
- which topic keys are actually populated
- where lexical exact match would be carrying preference behavior

Current refinement to that requirement:

- coverage alone is not enough
- the planner also needs active-topic frontier support diagnostics on the actual neutral seed pool

That support summary should answer, for the active topics in the current profile:

- how many frontier candidates support the topic
- how much support mass is present after topic-specificity dampening
- whether the topic has enough real support to justify later scarcity calibration

This prerequisite is now partially satisfied: local `ja` and `es` frequency packs can carry live topic metadata, while `en` still falls back to lexical exact-match behavior.

### 3. Semantic generalization evaluation third

Before adding embeddings or any other “smart” semantic fallback to live admission, run the controlled bake-off described in `docs/srs/srs_embedding_admission_evaluation_plan.md`.

That evaluation should answer:

- whether alias/topic expansion already solves most of the gap,
- whether static embeddings materially help,
- whether multilingual text embeddings justify their added cost,
- whether any semantic fallback preserves core-vocabulary stability and explainability.

### 4. Weight tuning fourth

Only after the above should we tune:

- preference-affinity strength
- relative dominance against coverage gain
- pair-local coefficient differences if needed
- bounded scarcity calibration for sparse-but-real topics

Current checkpoint note:

- coefficient tuning is now an explicit follow-up task, not an architectural blocker
- the merge-safe claim is limited to scorer/selector/preview/rebalance architecture and diagnostics correctness
- stronger topic lift still requires later coefficient and coverage work

Important constraint:

- explicit interests currently normalize to `1.0`
- merged topic weights are clamped to `[0, 1]`
- current topic affinity therefore already saturates for clean explicit matches

So future sparse-topic handling should not be implemented as naive topic-weight inflation. It should be implemented as a separate bounded calibration term backed by frontier support diagnostics.

Current checkpoint:

- a bounded PoC `scarcity_bonus` lane is now an acceptable executable extension to `profile_bootstrap`
- it is gated by active-topic frontier support diagnostics
- it is intentionally secondary and bounded
- it should be treated as a tuning unblocker, not as the final calibrated topic-scarcity policy

### 5. Implicit mining fifth

Only after explicit-interest behavior is validated should we invest in:

- better topic mining
- support/confidence logic for implicit signals
- privacy-constrained lexical affinity signals
- bounded lexical-trend admission policy

Later still, if needed:

- separate register/style modeling such as `slang`

That order keeps the workstream grounded in inspectable behavior instead of speculative data plumbing.
