# Interest-Tailored SRS Admission Algorithm

Status: active design reference
Role: Planning / WIP
Last updated: 2026-05-26
Last verified: 2026-05-26 by SRS profile-bootstrap preference matrix tests, SRS quality harness, feature-state audit, doc-reference check, and changed-file gate
Purpose: define the product algorithm for tailoring SRS admission probabilities to user interests, readiness, source quality, and LP resource coverage
Source-of-truth: target algorithm reference; current executable truth lives in `core/lexishift_core/srs/seed.py`, `core/lexishift_core/srs/profile_bootstrap.py`, `core/lexishift_core/srs/selector.py`, helper admission use cases, SRS tests, and `docs/developer/feature_state_matrix.md`.

Related docs:
- `srs_browsing_based_admission_plan.md`
- `srs_interest_tailored_data_acquisition_plan.md`
- `srs_preference_taxonomy_lifecycle.md`
- `srs_profile_schema.md`
- `srs_selector_technical.md`
- `srs_set_planning_technical.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../test_outputs/srs_admission_expansion_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_topic_signal_inventory_en_es_current_latest.md`

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
- an SAT or TOEFL prep learner should see exam-relevant vocabulary when legal
  source data supports that preference family,
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
  proficiency fit, challenge fit, and a multiplicative readiness gate;
- selector scoring uses weighted normalized signals;
- profile-bootstrap selector metadata now carries `readiness_multiplier`, so
  both ranked score and weighted sampling mass can suppress candidates that are
  much too easy or too hard for the learner's proficiency band;
- preview tests prove that topic-bearing candidates can move ahead of neutral
  frequency order, that stronger topic strength monotonically increases
  realized topic pressure in the synthetic matrix, and that higher proficiency
  shifts the preview toward harder candidates;
- browsing-based admission is planned as a separate opt-in word-signal layer;
  it is not implemented/default-on and must not mutate review scheduling.

The target described here is broader than current default behavior. In
particular:

- current Spanish frequency data has no native topic/domain columns. Installed
  Kaikki can enrich current CDE with explicit sense topics for `234 / 1,984`
  lemmas, including `42` `medicine` rows, but this is still partial and should
  be treated as an overlay signal rather than native frequency-pack truth;
- current helper routing still keeps default bootstrap behavior conservative;
- a promoted expansion pack needs source, POS, topic, license, and rulegen
  coverage evidence before product use.

Current SPALEX 10k candidate evidence:

- the provisional `freq-es-spalex-expanded-v1` pack passes the SRS seed
  admission path for `10,000` unique lemmas;
- rank resolves to `id` and commonness resolves to `pmw`, so the existing seed
  code reads the intended candidate ordering;
- POS mapping covers `9,435 / 10,000` frontier rows, and POS weighting moves
  non-lexical/function-heavy rows in the top 100 from `19` rank-order rows to
  `0` admission-order rows;
- topic metadata exists for `1,353 / 10,000` frontier rows, enough to prove
  controlled profile lift for tagged interests such as `medicine`, `finance`,
  `sports`, and `music`, but still too sparse for a complete personalization
  claim.
- the animals/plants overlay PoC demonstrates the intended overlay path without
  changing runtime behavior: accepted review labels become a candidate overlay,
  strong accepted rows are injected into `profile_topics`, and the existing
  profile-bootstrap reranker visibly lifts reviewed `animals` and
  `plants_nature` rows in the top preview.
- SAT and TOEFL are intended preference families, but only after legal review
  identifies allowed vocabulary, skill, or exam-prep source data. They should
  not be inferred from current Wiktionary topic labels.

## Data Model

### User Profile Vector

User interests should be stored internally as scalar weights, not binary flags.
The UI may expose simple categories, but the ranking layer should consume
weighted topic signals.

Preference IDs are intended to be stable and append-only after release. Adding
a new topic/register preference changes future admission scoring and
diagnostics; it must not delete, reset, or reschedule already-admitted SRS
items. Use `srs_preference_taxonomy_lifecycle.md` for migration rules.

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

Product UX should present these values as qualitative influence, not
percentages or quota shares. A user should be able to say "I care about
animals strongly" and "I care about cooking lightly" without managing a finite
allocation budget. Multiple topics can all be `strong`; that means they all
receive strong admission pressure when supported by the source frontier,
readiness gate, and other admission constraints.

Suggested product labels:

| UX label | Internal scalar |
| --- | ---: |
| Off | `0.00` |
| Light | `0.25` |
| Medium | `0.50` |
| Strong | `0.75` |
| Focused | `1.00` |

User-facing copy should avoid claims like "50% animals." Prefer language such
as "more likely to admit animal words when they fit your level" or "strongly
shape new-word admission toward animals." Developer diagnostics and local labs
may expose the raw scalar values.

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

Exam-prep categories are the same shape as other preference families once data
exists, but the source bar is higher: a row should carry an allowed exam-prep
source, internal skill-taxonomy mapping, or reviewed proxy evidence before
receiving `sat`, `toefl`, or related topic membership.

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

The executable profile-bootstrap path also keeps a separate proficiency guard:

```text
proficiency_fit_i = 1.0                 if d_i <= user_proficiency
proficiency_fit_i = taper_down(d_i)     if d_i > user_proficiency
```

That guard is only a positive fit signal. To avoid admitting extremely basic
words to advanced users, profile bootstrap also computes a multiplicative
readiness gate:

```text
topic_strength_i = clamp01(topic_affinity_i)

lower_i = clamp01(
    user_proficiency
  - base_lower_margin
  - topic_strength_i * topic_extra_lower_margin
)

upper_i = clamp01(
    user_proficiency
  + base_upper_margin
  + topic_strength_i * topic_extra_upper_margin
)

too_easy_gap_i = max(0, lower_i - d_i)
too_hard_gap_i = max(0, d_i - upper_i)

readiness_multiplier_i = exp(
    -too_easy_penalty * too_easy_gap_i^2
    -too_hard_penalty * too_hard_gap_i^2
)
```

The multiplier is neutral (`1.0`) when no proficiency estimate is available.
When proficiency is available, it is applied after the additive score and to
the frequency baseline used by weighted sampling. Topic relevance widens the
acceptable band a little below and above the learner's proficiency level, but
it does not bypass the gate: a very basic word can still collapse to near-zero
admission mass for a high-proficiency learner.

### Deferred Problem: Global Vs Topic-Local Proficiency

The current readiness model deliberately uses one global proficiency estimate.
That is a useful first product simplification, but it is not conceptually
complete for highly specialized journeys.

Example clash:

- a doctor may have strong medical vocabulary in the target language while
  still having weaker everyday vocabulary;
- another learner may be generally advanced but weak in medical terminology;
- a learner may only care about one domain, such as medicine, law, gaming, or
  cooking, and may want admission to optimize that domain rather than a general
  frequency journey.

In those cases, one scalar `user_proficiency` can be misleading. General
proficiency and topic-local proficiency may need to diverge:

```json
{
  "proficiency": {
    "estimated_value": 0.55
  },
  "topic_proficiency": {
    "medicine": 0.82,
    "animals": 0.35
  }
}
```

Potential future approaches:

1. Keep global proficiency as the default and add optional topic-local
   proficiency estimates only for well-supported topics.
2. Add explicit journey modes, such as `general_srs`, `topic_intensive`, or
   `domain_pack`, so a hyperspecialized learner is not treated as a normal
   frequency-frontier learner.
3. Treat curated/user-defined vocabulary packs as a separate admission surface
   when a user intentionally wants a closed domain list. That path should not be
   assumed to support SRS until a dedicated SRS integration exists.

Current decision: do not implement topic-local proficiency yet. The current
readiness gate remains global, with topic relevance only widening the global
band. This keeps the model testable while preserving the unresolved product
problem for a later design pass.

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

For profile bootstrap, the final executable score is:

```text
final_score_i = raw_score_i * readiness_multiplier_i
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

## Admission Selection Semantics

Current profile-bootstrap admission does not treat topic strength as a direct
percentage chance. The topic scalar is an input to candidate scoring. The
realized share of preferred-topic admissions is an output determined by:

- the eligible candidate frontier;
- active topic weights and candidate topic metadata;
- source/topic label coverage;
- proficiency and readiness gates;
- active SRS inventory, blocked lemmas, and deduplication;
- selector policy and requested admission count.

Let `A` be the set of candidates that match at least one active preferred
topic. In the current executable profile-bootstrap path, topic affinity is the
strongest active topic match after topic-specificity dampening:

```text
topic_affinity_i = max(topic_weight_t * topic_specificity_i,t)
```

The current profile-bootstrap selector weights are:

```text
weighted_score_i =
    0.55 * base_frequency_i
  + 0.15 * topic_affinity_i
  + 0.05 * scarcity_bonus_i
  + 0.10 * proficiency_fit_i
  + 0.10 * challenge_fit_i

final_score_i = weighted_score_i * readiness_multiplier_i
```

The default selection policy is deterministic top-N ranking. For a batch of
`k` admitted words:

```text
selected = top_k(sort_by(final_score, descending))
preferred_topic_share = count(i in selected where i in A) / k
```

Under deterministic top-N, the "chance" that the next admitted word is a
preferred-topic word is therefore `0` or `1` for a single slot, and the batch
share is a measured result, not a probability guarantee. A topic scalar of
`0.50` does not mean "50% of admitted words should be this topic."

The optional weighted-without-replacement selector, used by previews and labs
when explicitly requested, does have probability mass. Its first-draw mass is:

```text
base_mass_i = base_frequency_i * readiness_multiplier_i
score_mass_i = final_score_i
mass_i = 0.35 * base_mass_i + 0.65 * score_mass_i
```

For a single admitted word:

```text
P(first word is in preferred topic A) =
    sum(mass_i for i in A) / sum(mass_j for j in eligible_pool)
```

For `k > 1` weighted draws without replacement, the exact topic inclusion
probability is sequential: after each selected word, its mass is removed and
the next draw is normalized over the remaining pool. The expected preferred
topic share is computable from the same selector code, but it is not a simple
function of the user scalar alone.

The product requirement is not a specific probability formula. The requirement
is that stronger topic preference monotonically increases matching candidates'
rank or sampling mass when source coverage and readiness allow it, while
diagnostics report the realized preferred-topic share and source-limited cases.
The committed preference sanity matrix checks this as a deterministic contract:
it compares topic top-N counts, first-draw selection mass, proficiency-driven
difficulty shift, and high-proficiency topic pressure on a controlled synthetic
frontier.

## Encounterability Constraint

A word should not enter active SRS only because it is topically interesting. It
also needs a plausible path to being seen, reviewed, and eventually moved out
of the active learning lane.

The failure mode is "encounter starvation":

```text
rare topical word admitted -> replacement rule rarely matches pages ->
little/no feedback -> word remains active -> active capacity stays full ->
future admission slows or stalls
```

This is especially relevant for narrow topic preferences such as rare animals,
plants, technical tools, or specialist jargon. The answer is not to remove
topic personalization. The answer is to keep topic lift bounded and pair it
with servability signals.

Recommended scoring extension:

```text
encounterability_i =
    0.70 * general_frequency_i
  + 0.20 * recent_browsing_match_i
  + 0.10 * replacement_source_frequency_i

final_score_i =
    interest_score_i
  * readiness_multiplier_i
  * encounterability_floor_i
```

For MVP, `general_frequency_i` and the existing frequency/rank frontier are the
main encounterability proxy. Browsing signals can later raise encounterability
only after opt-in. Passive replacement exposure should not count as recall, but
it is useful evidence that an admitted word is actually servable in the
learner's reading environment.

Operational policy:

- a strong topic preference may reserve a capped lane, but should not consume
  the whole active set;
- very rare topic words should need either strong source/readiness evidence or
  direct browsing evidence before receiving large admission pressure;
- active words with low/no exposure and no feedback should be visible in
  diagnostics before testers evaluate the SRS experience;
- a future stale-active release/clear policy should be able to free capacity
  without marking the word learned.

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

7. Select admitted lemmas:
   - default to deterministic top-N over final scores,
   - optionally use weighted sampling mass for preview or exploration modes,
   - enforce topic/POS/source caps,
   - persist only the admitted subset into `S`.

8. Generate rulegen outputs:
   - use admitted active targets,
   - preserve word-package provenance,
   - publish helper artifacts for runtime.

9. Store decision evidence:
   - selected lemmas,
   - realized preferred-topic share when topic preferences are active,
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
  - current implementation uses `profile_growth`, which reuses the same
    profile-aware utility signals as `profile_bootstrap` against the current
    eligible frontier, then admits only within the normal refresh budget.

- profile or source changes:
  - if interests, proficiency, source pack, rulegen coverage, or blocked terms
    change, the next admission preview or mutation recomputes probabilities.

Review scheduling is separate. A due review should not recompute admission
probabilities unless that review also triggers a growth or refresh workflow.
Feedback from reviews may update profile signals, but admission probability is
used when admitting new items into `S`.

Admission is durable. Once a word is selected into `S`, it normally remains part
of the learner's review path until scheduler maturity, suspension/discard, or a
future lifecycle policy changes that state. Therefore every personalization
signal, including the planned browsing-based signal, must pass through the same
budget and lifecycle gates as ordinary admission:

- daily/session new-word budget;
- active-set budget;
- blocked/discarded/suspended item policy;
- source/rulegen/readiness eligibility;
- no duplicate admission for already admitted or mastered target lemmas.

Browsing-based admission should be treated as an extra score component plus a
share-calibrated admission policy, not as an automatic route from page exposure
to durable SRS obligation.

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
10. exam-prep preferences such as SAT and TOEFL have documented legal/source
    provenance before they appear as selectable product preferences.
