# Interest-Tailored SRS Admission Algorithm

Status: active design reference
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 by SRS seed/admission/profile-bootstrap code read and related SRS docs
Purpose: define the product algorithm for tailoring SRS admission probabilities to user interests, readiness, source quality, and LP resource coverage
Source-of-truth: target algorithm reference; current executable truth lives in `core/lexishift_core/srs/seed.py`, `core/lexishift_core/srs/profile_bootstrap.py`, `core/lexishift_core/srs/selector.py`, helper admission use cases, SRS tests, and `docs/developer/feature_state_matrix.md`.

Related docs:
- `srs_interest_tailored_data_acquisition_plan.md`
- `srs_profile_schema.md`
- `srs_selector_technical.md`
- `srs_set_planning_technical.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`

## Product Goal

Admission into SRS should not mean "take the next most frequent word." It
should mean:

> Admit words that are frequent enough, learnable now, source-supported,
> rulegen-usable when required, and unusually valuable for this learner's
> interests and reading life.

The core product advantage is individualized admission pressure:

- a medical learner should see more health and clinical vocabulary,
- a gamer should see more game vocabulary,
- a finance reader should see more finance vocabulary,
- an advanced learner should not be forced through only beginner vocabulary,
- a beginner should not be flooded with rare specialist words just because they
  selected a topic.

Interest does not replace frequency, readiness, source quality, or rulegen
coverage. It adds controlled probability pressure.

## Current Implementation Boundary

Current code already has important pieces of this model:

- seed extraction reads frequency, POS, source, and topic columns when present;
- supported topic columns are `sense_topics`, `topics`, `topic`, and
  `profile_topics`;
- profile-bootstrap scoring computes coverage, topic affinity, scarcity,
  proficiency fit, and challenge fit;
- selector scoring uses weighted normalized signals;
- preview tests prove that topic-bearing candidates can move ahead of neutral
  frequency order.

The target described here is broader than current default behavior. In
particular:

- current Spanish frequency data has no topic/domain metadata, so interest
  tailoring cannot meaningfully favor medical terms from that source alone;
- current helper routing still keeps default bootstrap behavior conservative;
- a promoted expansion pack needs source, POS, topic, license, and rulegen
  coverage evidence before product use.

## Data Model

### User Profile Vector

User interests should be stored internally as scalar weights, not binary flags.
The UI may expose simple categories, but the ranking layer should consume
weighted topic signals.

Example helper-facing shape:

```json
{
  "topic_weights": {
    "medicine": 0.85,
    "health": 0.65,
    "travel": 0.20
  },
  "topic_confidence": {
    "medicine": 0.90,
    "health": 0.70,
    "travel": 0.40
  },
  "proficiency": {
    "estimated_value": 0.62
  },
  "difficulty_preferences": {
    "target_challenge_center": 0.58,
    "target_challenge_spread": 0.15
  }
}
```

Interpretation:

- `topic_weights` are preference strength, not exact desired admission share.
- `topic_confidence` says how reliable the signal is.
- explicit user choices should start with higher confidence than inferred page
  behavior.
- inferred weights should change gradually with smoothing and decay.

### Candidate Topic Matrix

Each candidate lemma should have a topic-membership vector over the same topic
space.

Example candidate:

```json
{
  "lemma": "salud",
  "topics": {
    "health": 0.95,
    "medicine": 0.55,
    "daily_life": 0.30
  },
  "topic_confidence": 0.90
}
```

The candidate topic values should be scalar memberships, not exclusive labels.
Many useful words are cross-domain. For example, `virus`, `operacion`,
`presion`, and `consulta` can be medical, general, academic, or administrative
depending on context.

### Candidate Feature Row

The admission candidate row should eventually expose these normalized fields:

| Field | Meaning |
| --- | --- |
| `lemma` | canonical target-language lemma |
| `language_pair` | LP key, such as `en-es` |
| `frequency_score` | general usefulness from rank/frequency, normalized `0..1` |
| `topic_vector` | candidate memberships across topic taxonomy |
| `topic_confidence` | confidence in candidate topic labels |
| `pos_quality` | POS usefulness and POS normalization confidence |
| `rulegen_coverage` | whether rulegen can produce usable rules for the lemma |
| `difficulty_estimate` | candidate difficulty proxy, normalized `0..1` |
| `source_confidence` | trust in the source row and merge provenance |
| `novelty` | whether the candidate is not already known/recently saturated |
| `diversity_bucket` | topic/POS/source bucket for cap and balance policies |
| `provenance` | source contributions, versions, and license status |

Rows without topic metadata remain valid general-frequency candidates, but their
topic affinity is zero except for exact lexical fallback. They should not be
used as evidence that an LP supports personalized topic admission.

## Core Math

This is not a vector cross product. The topic match is a dot product, or matrix
multiplication when scoring many candidates.

Let:

```text
K = number of topics in the taxonomy
N = number of eligible candidates

u[K] = user topic weight vector
c_user[K] = confidence for each user topic signal
T[N,K] = candidate topic-membership matrix
c_item[N] = candidate topic-label confidence
```

The confidence-adjusted user vector is:

```text
u_eff = u * c_user
```

For candidate `i`, topic affinity is:

```text
topic_affinity_i = dot(T[i], u_eff) * c_item[i]
```

For a full candidate pool:

```text
topic_affinity[N] = T @ u_eff
topic_affinity = topic_affinity * c_item
```

Then clamp or normalize to `0..1`:

```text
topic_affinity_i = clamp01(topic_affinity_i)
```

This is the clean linear-algebra layer:

- one user profile vector,
- one candidate-topic matrix,
- one affinity score per candidate.

## Readiness And Non-Beginner Handling

The algorithm must not assume every new user is a beginner.

Let:

```text
d_i = candidate difficulty estimate in 0..1
target = user's target challenge center in 0..1
spread = accepted challenge spread
```

Difficulty fit can use a Gaussian-shaped score:

```text
difficulty_fit_i = exp(-((d_i - target)^2) / (2 * spread^2))
```

Behavior:

- beginner users have lower `target`, so rare specialist terms receive less
  readiness lift;
- advanced users have higher `target`, so basic words are less favored unless
  they are known gaps or highly useful;
- topic preference can lift a word only inside the readiness envelope, not
  override all other quality signals.

The system may also keep a separate proficiency guard:

```text
proficiency_fit_i = 1.0                 if d_i <= user_proficiency
proficiency_fit_i = taper_down(d_i)     if d_i > user_proficiency
```

The exact difficulty source can evolve:

- frequency rank proxy,
- learner-level or CEFR overlay,
- user known-word estimate,
- historical SRS feedback,
- source-specific difficulty metadata.

## Candidate Score

After hard filters, each candidate receives a weighted score.

```text
raw_score_i =
    w_freq       * frequency_score_i
  + w_topic      * topic_affinity_i
  + w_rulegen    * rulegen_coverage_i
  + w_pos        * pos_quality_i
  + w_difficulty * difficulty_fit_i
  + w_source     * source_confidence_i
  + w_novelty    * novelty_i
  + w_diversity  * diversity_bonus_i
  - penalties_i
```

All components should be normalized to `0..1` before scoring.

Initial product posture:

- frequency should remain the largest stabilizing term;
- topic affinity should be strong enough to visibly move relevant terms;
- rulegen coverage should be a hard filter or heavy score term depending on the
  admission mode;
- source confidence and license readiness should be promotion gates, not hidden
  preferences;
- diversity should prevent one topic from monopolizing the admitted set.

## Admission Probability

The score can be converted to admission probability with a softmax:

```text
probability_i = exp(raw_score_i / temperature)
                / sum(exp(raw_score_j / temperature) for j in eligible_pool)
```

Temperature controls exploration:

- lower temperature: more deterministic, top-score-heavy admission;
- higher temperature: more variety and exploration.

An implementation may also use weighted sampling without replacement over
positive scores:

```text
mass_i = max(epsilon, raw_score_i)
probability_i = mass_i / sum(mass_j for j in eligible_pool)
```

The product requirement is not a specific probability formula. The requirement
is that admission probability is a monotonic, explainable function of the
candidate's weighted score, with diversity and safety constraints applied.

## Clean Admission Sequence

Admission should be staged.

1. Resolve LP resources:
   - frequency pack,
   - dictionary/rulegen pack,
   - stopwords/exclusions,
   - profile context,
   - source and license manifests.

2. Build candidate pool:
   - read top `bootstrap_top_n` or growth-frontier rows,
   - normalize lemma, rank/frequency, POS, topic metadata, and provenance.

3. Apply hard filters:
   - wrong LP,
   - malformed lemma,
   - blocked or already admitted when replacement is not requested,
   - disallowed source or license state,
   - stopword/function-word policy,
   - unsupported rulegen coverage when the mode requires rulegen.

4. Compute static candidate features:
   - frequency score,
   - POS quality,
   - topic vector,
   - source confidence,
   - rulegen coverage,
   - difficulty estimate.

5. Compute user-specific features:
   - topic affinity,
   - proficiency fit,
   - challenge fit,
   - novelty against the user's SRS store,
   - diversity pressure against current active/admitted inventory.

6. Score candidates:
   - weighted score,
   - penalties,
   - explanation components.

7. Convert scores to selection probabilities:
   - softmax or weighted sampling mass,
   - optionally keep top safety floor deterministic.

8. Select admitted lemmas:
   - sample or take top candidates,
   - enforce topic/POS/source caps,
   - persist only the admitted subset into `S`.

9. Generate rulegen outputs:
   - use admitted active targets,
   - preserve word-package provenance,
   - publish helper artifacts for runtime.

10. Store decision evidence:
   - selected lemmas,
   - top rejected near-misses when useful,
   - profile hash,
   - source pack hashes,
   - selector/admission policy version,
   - explanation terms.

## Source Cohesion Requirements

Expansion sources become cohesive with existing LP sources only after they are
normalized into one candidate contract.

Minimum promoted row contract:

- stable lemma key,
- normalized rank/frequency,
- POS or POS backfill with confidence,
- topic/domain metadata or explicit `no_topic_metadata` status,
- source provenance per field,
- license/promotion status,
- dictionary/rulegen coverage evidence,
- merge policy for duplicates and conflicts.

The current `en-es` baseline can remain the frozen comparison source while a
new pack is evaluated separately. A hybrid pack should not erase provenance.
For example, a row may have:

```json
{
  "lemma": "salud",
  "frequency_source": "freq-es-cde",
  "topic_source": "domain-overlay-health-v1",
  "pos_source": "wiktionary-es-en",
  "rulegen_source": "wiktionary-es-en",
  "merge_policy": "baseline_frequency_plus_topic_overlay_v1"
}
```

## When Computation Happens

Admission math should run when admission is needed, not on every review.

Primary computation points:

- admission preview:
  - user opens an SRS setup or growth preview;
  - no mutation;
  - scores and explanations are computed for display.

- initial set creation:
  - user initializes a pair/profile;
  - scores are computed;
  - selected lemmas are persisted into `S`;
  - rulegen runs for admitted targets.

- growth or refresh:
  - user requests more words or policy triggers a growth cycle;
  - profile and inventory state are current inputs;
  - new probabilities are computed against the current eligible frontier.

- profile or source changes:
  - if interests, proficiency, source pack, rulegen coverage, or blocked terms
    change, the next admission preview or mutation recomputes probabilities.

Review scheduling is separate. A due review should not recompute admission
probabilities unless that review also triggers a growth or refresh workflow.
Feedback from reviews may update profile signals, but admission probability is
used when admitting new items into `S`.

## Caching Policy

The topic dot product is cheap for a normal SRS frontier. Even `50,000`
candidates times a modest topic taxonomy is small enough to compute on demand
in an admission job. Correctness is more important than prematurely caching
user-specific probabilities.

Recommended cache layers:

| Cache | Scope | Key | Why |
| --- | --- | --- | --- |
| Candidate feature cache | pair + source pack version | `pair`, pack hash, feature version | avoids re-reading and re-normalizing static source data |
| Topic matrix cache | pair + source pack version | `pair`, pack hash, topic-taxonomy version | makes repeated previews cheap |
| Rulegen coverage cache | pair + dictionary pack version | `pair`, dictionary hash, rulegen policy version | avoids repeated dictionary coverage probes |
| User profile vector cache | profile + pair | `profile_id`, pair, profile signal hash | cheap but useful for repeated previews |
| Admission decision audit | profile + pair + run | run id, policy version, source hashes | explains what happened; not used as truth for future scoring |

Avoid long-lived caching for final admission probabilities unless all dependency
hashes are included:

- source pack hash,
- topic matrix version,
- profile signal hash,
- SRS inventory hash,
- blocked/known lemma hash,
- rulegen coverage version,
- selector/admission policy version,
- time-window or feedback-window id when recency is involved.

In practice:

1. Cache static candidate features and matrices.
2. Recompute user-specific affinity and final scores at admission time.
3. Persist the selected result and explanation, not stale probability truth.

This keeps preview and admission fast while avoiding incorrect personalization
after a user changes interests, progresses in proficiency, blocks terms, or
admits a new batch.

## Explainability Contract

Each admitted word should be explainable in product terms:

```json
{
  "lemma": "salud",
  "admission_reason": [
    "strong general frequency",
    "matches medicine/health interest",
    "appropriate for current challenge target",
    "rulegen coverage available",
    "source confidence high"
  ],
  "weighted_components": {
    "frequency_score": 0.82,
    "topic_affinity": 0.74,
    "difficulty_fit": 0.69,
    "rulegen_coverage": 1.0,
    "source_confidence": 0.92
  }
}
```

The explanation should not expose every internal coefficient to users by
default. Developer diagnostics can expose full component scores and versions.

## Acceptance Criteria For Implementation

The product algorithm is ready to become default behavior for an LP when:

1. the LP has a promoted source pack with frequency, POS, provenance, and
   license evidence;
2. topic/domain metadata coverage is high enough for the intended personalized
   mode, or the UI clearly reports limited topic support;
3. profile preferences are scalar and confidence-aware internally;
4. non-beginner users can set or infer proficiency/challenge targets;
5. neutral admission remains stable against the current frequency baseline;
6. a topic preference visibly moves matching candidates without overwhelming
   core vocabulary;
7. rulegen coverage is audited for admitted targets when browser replacement is
   expected;
8. decision output includes policy version, source hashes, profile signal hash,
   selected lemmas, and explanation components;
9. targeted tests cover neutral, beginner, advanced, topic-heavy, sparse-topic,
   and metadata-free source scenarios.
