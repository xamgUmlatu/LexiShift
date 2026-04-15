# SRS Preference Signal Admission Design

Status: Planning / WIP
Role: Planning / WIP
Purpose: define how explicit preferences and opted-in implicit behavior should affect SRS admission, specify the mathematical scoring model, and assess whether the current data architecture can support that direction
Last updated: 2026-04-15
Last verified: 2026-04-15
Verification:
- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/seed.py`
- `core/lexishift_core/srs/selector.py`
- `core/lexishift_core/srs/set_planner.py`
- `core/lexishift_core/helper/use_cases/admission_preview.py`
- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/developer/language_difficulty_and_proficiency_model.md`

Related design:
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_embedding_admission_evaluation_plan.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_preference_update_and_rebalance_policy.md`
- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`

Implementation note:
- the concrete `v1` scoring and sequencing decisions now live in `docs/srs/srs_preference_signal_admission_v1_contract.md`

## Purpose

This doc answers three questions:

1. what product behavior LexiShift should implement for explicit and implicit preference-driven admission,
2. how those signals should be represented mathematically,
3. whether the current data architecture can support that direction without a redesign.

This doc is intentionally not an implementation checklist. It is the product and algorithm design contract that should guide later implementation work.

## Product framing

Two example behaviors should both be supported:

### Example 1: explicit preference

- user chooses `animals` as an interest
- words such as `dog`, `elephant`, `fur`, and `claws` become more likely to be admitted

### Example 2: opted-in implicit behavior

- user opts into implicit personalization
- visited content is mined for either:
  - derived topics/domains
  - repeated exact lexical signals
- words such as `livestream`, `variety`, and `funny`, or closely related vocabulary, become more likely to be admitted

The important product decision is:

- example 1 should be the primary path
- example 2 should be secondary, weaker, and privacy-constrained

Explicit user intent should be authoritative. Implicit behavior should refine, not replace, explicit intent.

Important category note:

- domain/topic preferences such as `animals`, `sports`, `games`, `music`, `anime`, `livestream`, and `comedy` fit this model naturally
- register/style preferences such as `slang` do not cleanly fit the topic model and should be treated later as a separate preference axis rather than forced into `topic_weights`

## Product principles

### 1. Explicit preferences are first-class

If the user explicitly chooses `animals`, that should produce a strong, inspectable admission bias toward animal-related vocabulary.

This is:

- legible
- user-controlled
- easy to preview
- easy to undo

### 2. Implicit behavior must be opt-in and derived

Implicit behavior should not be stored or scored as raw browsing history.

The admission layer should consume derived signals such as:

- topic/domain weights
- repeated lexical affinity weights
- support counts and confidence

It should not consume:

- raw page bodies
- raw URL history
- one-off surface tokens without normalization

### 3. Topic/domain inference is better than raw word mining

For implicit behavior, the preferred signal is:

- `streaming`
- `comedy`
- `pets`
- `gaming`
- `finance`

not:

- every literal word seen on pages

Exact lexical signals are still useful, but they should be:

- secondary
- confidence-limited
- repetition-sensitive

### 4. Preferences should bias, not collapse, the admitted set

Preferences should not turn admission into a narrow bubble.

The admitted set should still preserve:

- core/general vocabulary
- some breadth
- some exploration

More concretely:

- preference signals should change relative admission likelihood, not hard-filter the seed pool
- core vocabulary should stay present because neutral frequency/coverage remains a dominant term
- selecting `music` should make music-related words more likely, not make ordinary core words disappear
- selecting `animals` should tilt the frontier toward animal vocabulary, not replace the frontier with only animal vocabulary

### 5. The system must stay explainable

Every admission boost should be attributable to named signals such as:

- explicit interest match
- implicit topic match
- implicit lexical match
- proficiency fit
- challenge fit

That is required for:

- preview UX
- debugging
- tuning
- user trust

### 6. Deterministic scoring and stochastic sampling should stay separate

The planner/scorer should stay deterministic for:

- tests
- coefficient tuning
- diagnostics
- reproducible bug reports

The user-facing admission sample should be stochastic:

- it should draw from the scored probability distribution
- repeated presses should vary
- sampling should not mutate `S`
- fixed seeds should remain available for automated tests and controlled debug runs

That means LexiShift should keep one deterministic scoring frontier, then optionally sample from that frontier for preview UX.

## Current architecture assessment

## Short verdict

The current architecture is already suitable for:

- explicit interest-driven admission
- derived implicit topic-weight admission
- proficiency/challenge-aware reranking

It is only partially suitable for:

- exact lexical boosts from implicit behavior
- a full final utility function with penalties and exploration terms

It is not suitable yet for:

- direct raw browsing-to-admission logic

That last part is good. Raw browsing history should not be the planner input primitive.

## What already exists

### 1. Stable profile-signal storage in extension state

Current extension storage already has a pair-local profile signal seam:

- `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`

Current stored signal groups already include:

- `interests`
- `objectives`
- `proficiency`
- `difficultyPreferences`
- `empiricalTrends`
- `sourcePreferences`

This is implemented in [signals_methods.js](D:/projects/LexiShift/apps/chrome-extension/options/core/settings/signals_methods.js).

### 2. Planner payload composition already carries these signals

Current options/helper payload composition already emits:

- `interests`
- `objectives`
- `proficiency`
- `difficulty_preferences`
- `empirical_trends`
- `source_preferences`
- `constraints`
- `sizing`

This is implemented in [srs_profile_methods.js](D:/projects/LexiShift/apps/chrome-extension/options/core/settings/srs_profile_methods.js).

That means the transport seam already exists. The planner/helper does not need a new top-level payload model to carry preference data.

### 3. Admission normalization already supports explicit and implicit topic weights

Current helper normalization in [admission_features.py](D:/projects/LexiShift/core/lexishift_core/srs/admission_features.py) already reads:

- `interests`
- `topic_weights`
- `empirical_trends.topic_bias`
- `proficiency`
- `difficulty_preferences`
- `placement_result`

and normalizes them into:

- `explicit_topic_weights`
- `implicit_topic_weights`
- `topic_weights`
- `proficiency_estimate`
- `challenge_target`
- `challenge_spread`
- `active_signals`
- `missing_signals`
- `signal_sources`

This is a strong architectural seam. It means the scorer can remain stable while the raw profile schema grows.

### 4. Candidate trait extraction already supports topic and lexical matching

Current candidate extraction in [profile_bootstrap.py](D:/projects/LexiShift/core/lexishift_core/srs/profile_bootstrap.py) already pulls:

- `topic_hints`
- `lexical_forms`
- `difficulty_estimate`
- `lexical_commonness`

Topic hints currently come from seed metadata such as:

- `sense_topics`
- `topics`
- `topic`
- `profile_topics`

and lexical forms come from the lemma/word-package forms.

This is supported by [seed.py](D:/projects/LexiShift/core/lexishift_core/srs/seed.py), which already preserves topic-relevant metadata when available from the frequency source.

### 5. Preview and initialize already consume `profile_context`

Current helper preview/init paths already run through `profile_context`:

- admission preview
- initialization
- rebalance preview/apply

So there is already an end-to-end execution path for profile-aware admission decisions.

## What is only partially ready

### 1. Implicit exact lexical boosts are not first-class yet

Current code can technically boost exact lexical matches by placing lexical tokens into `topic_weights`, because [profile_bootstrap.py](D:/projects/LexiShift/core/lexishift_core/srs/profile_bootstrap.py) checks both:

- candidate `topic_hints`
- candidate `lexical_forms`

against the normalized `topic_weights`.

That means a profile context like:

```json
{
  "topic_weights": {
    "livestream": 0.35
  }
}
```

can already boost exact matches to `livestream`.

But this is only technically workable, not conceptually clean. It overloads one namespace for two different concepts:

- topics/domains
- exact lexical affinities

Long-term, those should be stored separately.

### 2. The selector only exposes positive terms today

Current selector scoring in [selector.py](D:/projects/LexiShift/core/lexishift_core/srs/selector.py) only exposes:

- `base_freq`
- `topic_bias`
- `user_pref`
- `confidence`
- `difficulty_target`

Current `AdmissionUtilitySignals` already has placeholders for:

- `lexical_risk`
- `redundancy`
- `exploration_bonus`

but those terms are not yet mapped through the selector.

So the architecture is ready for the positive preference terms, but not yet fully wired for the complete final utility equation.

### 3. `sourcePreferences` is stored but not active in scoring

Current storage can carry source preferences, but the scorer does not yet use them.

That is acceptable. It means source-preference policy can be added later without a storage redesign.

## Recommended normalized signal model

The preferred long-term model keeps four preference-related maps distinct:

1. explicit topic weights
2. implicit topic weights
3. explicit lexical weights
4. implicit lexical weights

The current system already has explicit/implicit topic separation. It does not yet have explicit/implicit lexical separation as first-class fields.

Future non-topic preference axes such as register/style should remain separate from those four maps.

Example:

- `slang`
- `formal`
- `colloquial`
- `internet_register`

Those are better modeled later as explicit/implicit register or style preferences, not as topics.

## Recommended helper-side normalized context

```json
{
  "topic_weights_explicit": {
    "animals": 1.0
  },
  "topic_weights_implicit": {
    "streaming": 0.42,
    "comedy": 0.28
  },
  "lexical_weights_explicit": {},
  "lexical_weights_implicit": {
    "livestream": 0.30,
    "vtuber": 0.22
  },
  "proficiency_estimate": 0.35,
  "challenge_target": 0.58,
  "challenge_spread": 0.18
}
```

This is the clean conceptual target.

## Current-compatible storage assessment

Current architecture can already store or derive:

- `interests`
- `topic_weights`
- `empirical_trends.topic_bias`
- `proficiency`
- `difficulty_preferences`

Current architecture cannot yet store lexical affinities as a dedicated normalized field, but it can support them in either of two ways:

1. temporary current-compatible encoding:
   - put lexical tokens into `topic_weights`
2. preferred long-term encoding:
   - add a dedicated lexical-bias field under `empirical_trends`

Recommended future storage extension:

```json
{
  "empiricalTrends": {
    "topic_bias": {
      "streaming": 0.42,
      "comedy": 0.28
    },
    "lexical_bias": {
      "livestream": 0.30,
      "vtuber": 0.22
    },
    "topic_support": {
      "streaming": 18,
      "comedy": 11
    },
    "lexical_support": {
      "livestream": 7,
      "vtuber": 5
    },
    "updated_at": "2026-04-13T00:00:00Z"
  }
}
```

Important rule:

- these should be derived summaries
- not raw browsing logs

## Future non-topic preference axes

The current schema direction is not a one-way door.

If LexiShift later wants preferences such as:

- `slang`
- `colloquial`
- `formal`
- `internet_register`

those should be added as a separate normalized axis rather than overloaded into topic or lexical weights.

Recommended future direction:

- `register_weights_explicit`
- `register_weights_implicit`
- candidate-side `register_hints`

That keeps:

- topic/domain meaning separate from style/register meaning
- diagnostics legible
- future tuning coherent

## Mathematical model

## Notation

Let:

- `u` = user/profile
- `c` = candidate word
- `S` = current active inventory
- `d(c)` = candidate difficulty estimate in `[0, 1]`
- `T(c)` = set of candidate topic hints
- `L(c)` = set of candidate lexical forms

Let the normalized user-side signals be:

- `w_topic_exp_u(t)` in `[0, 1]`
- `w_topic_imp_u(t)` in `[0, 1]`
- `w_lex_exp_u(l)` in `[0, 1]`
- `w_lex_imp_u(l)` in `[0, 1]`
- `p_u` = proficiency estimate in `[0, 1]`
- `q_u` = challenge target in `[0, 1]`
- `s_u` = challenge spread in `(0, 1]`

## Explicit topic weighting

The simplest explicit-interest rule is:

`w_topic_exp_u(t) = 1` if `t` is an explicit interest, else `0`

More generally, explicit topic sliders or presets can emit:

`w_topic_exp_u(t) in [0, 1]`

The important product rule is:

- explicit topic weights are high-trust
- they should dominate implicit topic weights when both exist

## Implicit topic weighting

Implicit topic weighting should be computed from opted-in derived events, not raw text blobs.

For each opted-in event `e` and topic `t`, define:

- `conf_topic(e, t)` = confidence that event `e` implies topic `t`
- `src(e)` = source kind
- `alpha_src(src(e))` = source-specific trust weight
- `age(e)` = event age in days
- `decay_topic(age) = exp(-age / tau_topic)`

Then define per-event contribution:

`contrib_topic(e, t) = alpha_src(src(e)) * conf_topic(e, t) * decay_topic(age(e))`

Aggregate with a saturating function:

`w_topic_imp_u(t) = clamp01(1 - exp(-sum_e contrib_topic(e, t)))`

This shape is recommended because it:

- increases smoothly with repeated evidence
- saturates instead of growing unbounded
- naturally supports recency decay

## Implicit lexical weighting

Implicit lexical weighting should be weaker than topic weighting and require repeated evidence.

For lexical item `l`, define:

- `conf_lex(e, l)` = confidence that event `e` implies lexical affinity for `l`
- `decay_lex(age) = exp(-age / tau_lex)`
- `beta_src(src(e))` = lexical-source trust weight

Then:

`contrib_lex(e, l) = beta_src(src(e)) * conf_lex(e, l) * decay_lex(age(e))`

and:

`w_lex_imp_u(l) = clamp01(1 - exp(-sum_e contrib_lex(e, l)))`

Product rule:

- lexical implicit weights should usually have lower caps than topic implicit weights
- they should be support-thresholded
- they should never be the only admission signal

## Merging explicit and implicit signals

Recommended trust hierarchy:

- explicit topic > implicit topic > implicit lexical

The simplest merge that preserves that hierarchy is:

`w_topic_u(t) = clamp01(max(w_topic_exp_u(t), gamma_topic * w_topic_imp_u(t)))`

`w_lex_u(l) = clamp01(max(w_lex_exp_u(l), gamma_lex * w_lex_imp_u(l)))`

with:

- `0 < gamma_lex <= gamma_topic <= 1`
- typically `gamma_lex < gamma_topic`

This is recommended over naive summation because it:

- keeps explicit signals authoritative
- prevents implicit drift from overpowering user intent
- keeps explanations simple

## Candidate preference affinity

Define:

`topic_match(u, c) = max_{t in T(c)} w_topic_u(t)`

`lexical_match(u, c) = max_{l in L(c)} w_lex_u(l)`

Then:

`preference_affinity(u, c) = clamp01(max(topic_match(u, c), lexical_match(u, c)))`

This matches the current scorer shape well because current `profile_bootstrap` already uses strongest-match semantics for topic and lexical matching.

## Exact lexical trend admission policy

There is an important distinction between:

- stable topic/domain preference
- short-lived exact-word trend preference

Stable topics fit naturally into the main continuous scorer.

Short-lived lexical trends often do not. If exact lexical trend weights are forced into the same global scorer, they usually either:

- do almost nothing,
- or require overly large coefficients that distort the entire frontier.

Recommended long-term policy:

- keep the regular weighted admission function as the primary path
- allow a small, explicit lexical-trend lane for repeated, opted-in, time-decayed implicit words
- cap that lexical-trend lane by budget so it cannot displace the main admission frontier

Conceptually:

`A_total = A_regular union A_lexical_trend`

with:

- `A_regular` chosen from the main scored frontier
- `A_lexical_trend` chosen from an exact-word implicit trend pool
- `|A_lexical_trend| <= B_lexical_trend`

Where `B_lexical_trend` is small relative to the refresh or growth batch.

This is preferred over inflating one lexical-weight term inside the global scorer because it:

- preserves core-vocabulary stability
- lets trending exact words enter early when they matter
- gives explicit caps and diagnostics
- decays naturally when the trend fades

This should be thought of as:

- unified scoring within lane
- explicit source-mixture policy across lanes

not as an unprincipled random override.

## Proficiency fit

Current implemented shape in [profile_bootstrap.py](D:/projects/LexiShift/core/lexishift_core/srs/profile_bootstrap.py) is:

`proficiency_fit(u, c) = 1` if `d(c) <= p_u`

otherwise:

`proficiency_fit(u, c) = clamp01(1 - (d(c) - p_u) / tau_prof)`

where `tau_prof` is the taper width.

This is a good shape because:

- it fully accepts words at or below the learner estimate
- it decays smoothly above the learner estimate
- it avoids hard difficulty cliffs

## Challenge fit

Current implemented shape is a Gaussian preference around the desired challenge center:

`challenge_fit(u, c) = clamp01(exp(-0.5 * ((d(c) - q_u) / s_u)^2))`

This is also a good shape because:

- it allows a target region rather than a rigid level
- it supports easier or harder user preference independently of proficiency

## Coverage gain

Current bootstrap uses lexical commonness as a proxy:

`coverage_gain(c) = lexical_commonness(c)`

Today this comes from neutral admission/frequency weighting. That is acceptable as a bootstrap baseline.

## Recommended admission utility

The final preferred admission utility is:

`U(u, c | S) = w_cov * coverage_gain(c) + w_pref * preference_affinity(u, c) + w_prof * proficiency_fit(u, c) + w_chal * challenge_fit(u, c) - w_risk * lexical_risk(c) - w_red * redundancy(c, S) + w_exp * exploration_bonus(u, c, S)`

where all component values are normalized to `[0, 1]`.

Interpretation:

- `coverage_gain`
  - preserves core/general vocabulary pressure
- `preference_affinity`
  - explicit and implicit preference matching
- `proficiency_fit`
  - avoids starting too far above the learner
- `challenge_fit`
  - supports user-desired difficulty concentration
- `lexical_risk`
  - protects against bad early admissions
- `redundancy`
  - avoids wasting slots on near-duplicates
- `exploration_bonus`
  - prevents over-collapse into a narrow preference bubble

## Current executable subset

Today the architecture can directly support this reduced executable form:

`U_v1(u, c) = w_cov * coverage_gain(c) + w_pref * preference_affinity(u, c) + w_prof * proficiency_fit(u, c) + w_chal * challenge_fit(u, c)`

That is already aligned with the current selector fields:

- `coverage_gain` -> `base_freq`
- `preference_affinity` -> `topic_bias`
- `proficiency_fit` -> `user_pref`
- `challenge_fit` -> `difficulty_target`

## Not yet executable without selector extension

These terms are conceptually present but not wired through the selector yet:

- `lexical_risk`
- `redundancy`
- `exploration_bonus`

So the architecture is only partially ready for the full final utility equation.

## How the two product examples fit mathematically

## Example 1: explicit `animals`

User signal:

- `w_topic_exp_u(animals) = 1.0`

Candidate examples:

- `dog` with `animals` topic hint
- `elephant` with `animals` topic hint
- `fur` with `animals` or `biology` topic hint
- `claws` with `animals` or `body_parts` topic hint

Then:

- `topic_match(u, dog) = 1.0`
- `preference_affinity(u, dog) = 1.0`

The candidate is then boosted, but still moderated by:

- base frequency
- proficiency fit
- challenge fit
- later risk/redundancy terms

This is the desired product behavior.

Important implementation constraint:

- explicit interests currently normalize to `1.0`
- merged topic weights are clamped into `[0, 1]`
- clean topic matches can therefore already saturate the current `preference_affinity` term

That means future sparse-topic correction should not be implemented as naive global topic-weight inflation. Raising `animals` from `1.0` to “even bigger” is not meaningful in the current scorer shape.

## Example 2: opted-in implicit streaming/comedy behavior

Derived profile result:

- `w_topic_imp_u(streaming) = 0.42`
- `w_topic_imp_u(comedy) = 0.28`
- `w_lex_imp_u(livestream) = 0.30`

Merged with source attenuation:

- `w_topic_u(streaming) = gamma_topic * 0.42`
- `w_topic_u(comedy) = gamma_topic * 0.28`
- `w_lex_u(livestream) = gamma_lex * 0.30`

Then candidates with:

- topic hints `streaming`, `entertainment`, `broadcast`
- lexical form `livestream`

receive non-zero `preference_affinity`.

This is the desired product behavior for opted-in implicit personalization:

- related vocabulary is more likely
- but weaker than explicit declared interests

## Recommendation on raw-word mining

The product should prefer:

- page -> derived topic/domain weights

over:

- page -> direct raw token boosts

Reasons:

- topic inference is more stable
- topic inference is more explainable
- direct raw lexical mining is noisier
- privacy semantics are easier when only derived summaries are retained

Exact lexical boosts are still useful, but should be:

- lower weight
- lower cap
- repetition-gated

## Sparse-topic calibration policy

If LexiShift later wants sparse-but-valid topics such as `animals` to appear more often, the calibration should be:

- pool-local
- bounded
- diagnostics-first
- separate from the raw user preference weight

It should not be:

- raw inverse count (`1 / n`)
- a hidden multiplier folded directly into saved `topic_weights`
- a workaround for topics that are effectively absent from the neutral frontier

Reason:

- the current planner already saturates explicit topic weights at `1.0`
- the true bottleneck is often frontier support, not user preference strength
- a topic with zero or one viable candidates in the bootstrap frontier is not a good target for aggressive score inflation

Recommended future shape:

1. measure active-topic support on the same neutral seed frontier that `profile_bootstrap` reranks
2. expose diagnostics:
   - candidate count
   - support mass
   - top examples
   - readiness for scarcity calibration
3. only after that, add a separate bounded scarcity-calibration term for topics with real support

Recommended support mass proxy:

`support_mass(topic) = sum_c lexical_commonness(c) * topic_specificity(c, topic)`

This is better than raw count because:

- it discounts weak/polysemous matches
- it respects the neutral coverage floor
- it reflects how much usable mass is actually available to promote

Recommended future bounded multiplier:

`scarcity_multiplier(topic) = 1 + min(max_extra, max(0, (target_mass / (support_mass(topic) + lambda))^alpha - 1))`

Applied as:

- a separate scarcity-calibration lane in the scorer or diagnostics-backed selector policy
- not as a rewrite of the user’s declared preference weight itself

Current checkpoint:

- a bounded PoC scarcity-calibration lane is now acceptable and implemented for `profile_bootstrap`
- it operates only when the active topic has enough real support on the neutral frontier
- it remains bounded and secondary to `coverage_gain` and `topic_affinity`
- it is intended to unblock tuning and preview sanity, not to claim final coefficient quality

Current TODOs before calling this final:

- tune eligibility thresholds and target mass against more live pairs
- decide whether support mass should remain lexical-commonness-weighted or become admission-weight-weighted
- review whether the current PoC lane is too permissive for noisy domains such as `finance`
- improve topic metadata/frontier coverage for underrepresented topics such as `animals`

## Architecture verdict by capability

### Explicit topic preferences

Verdict: yes, current architecture already supports this cleanly.

Reason:

- pair-local signal storage exists
- planner payload transport exists
- helper normalization exists
- candidate topic hints exist
- scorer already computes topic affinity

### Derived implicit topic preferences

Verdict: yes, current architecture supports this if the behavior pipeline writes derived topic weights into `empirical_trends.topic_bias`.

Reason:

- that field already exists conceptually and in code
- normalization already reads it into `implicit_topic_weights`

### Exact lexical boosts from implicit behavior

Verdict: partially.

Reason:

- scorer can already match lexical forms
- but the schema does not have a dedicated lexical-affinity field

Recommendation:

- short-term, only if needed, encode lexical boosts carefully through current-compatible weights
- long-term, add a dedicated lexical-bias field
- when exact-word trends become real, prefer a capped lexical-trend admission lane over forcing giant lexical weights into the main scorer

### Full final utility function

Verdict: partially.

Reason:

- data architecture is ready
- selector architecture is not yet fully ready for explicit negative and exploration channels

Recommendation:

- extend the selector rather than hiding those terms inside ad hoc combined weights

### Embedding-based semantic generalization

Verdict: yes, but only as a researched secondary signal.

Reason:

- the current admission architecture can accept a scalar semantic-affinity term cleanly
- the repo already has embedding-resource plumbing on the GUI side
- the remaining uncertainty is empirical fit, calibration, and explainability rather than architecture

Recommendation:

- keep symbolic interests/topic weights as the primary path
- evaluate embeddings as a secondary semantic-generalization layer
- require a controlled bake-off before any live admission integration
- use `docs/srs/srs_embedding_admission_evaluation_plan.md` as the gate

### Raw browsing history as planner input

Verdict: no, and that is good.

Recommendation:

- keep raw browsing outside the planner contract
- persist only derived preference summaries and support diagnostics

### Register/style preferences such as `slang`

Verdict: later, but compatible with the current architecture.

Reason:

- the schema direction is extensible
- the scorer already accepts additional scalar feature families
- `slang` is a register/style property rather than a topic/domain property

Recommendation:

- do not force `slang` into the topic lane
- if added later, model it as a separate register/style axis with its own candidate hints and diagnostics

## Recommended implementation order

When implementation begins, the correct order is:

1. make explicit interests materially affect admission scoring
2. expose derived topic weights clearly in preview diagnostics
3. add opted-in implicit topic-weight ingestion
4. evaluate semantic generalization approaches before live embedding integration
5. only later add exact lexical implicit boosts
6. when exact lexical trends are added, use a capped lexical-trend lane rather than giant global lexical weights
7. extend selector for negative and exploration terms

This order is recommended because it yields:

- immediate user-visible value
- low ambiguity in product behavior
- strong preview/testability
- minimal privacy risk
- an explicit evidence gate before any semantic-embedding expansion

## Final recommendation

The current architecture is good enough to proceed without redesign.

The correct direction is:

- treat explicit interests as strong normalized topic weights
- treat opted-in implicit behavior primarily as weaker derived topic weights
- treat embeddings, if adopted, as a later secondary semantic-generalization term
- treat exact lexical mining as a later secondary signal
- keep the scoring function continuous, decomposed, and explainable
- extend the selector later for negative and exploration terms rather than folding them into hidden heuristics

That gives LexiShift the right product behavior and preserves a clean long-term architecture for admission.
