# SRS Admission Frontier Gaussian Plan

Status: implemented for profile-bootstrap admission; hard-hybrid v2 default-on
Last updated: 2026-07-12
Purpose: formalize the next proposed admission-policy shape for profile-based
SRS admission, especially the relationship between user proficiency, topic
preference, learned-word history, and candidate difficulty.

Related docs:
- `srs_admission_lifecycle_current_state.md`
- `srs_interest_tailored_admission_algorithm.md`
- `srs_browsing_based_admission_plan.md`
- `srs_learner_difficulty_model_workplan.md`
- `srs_learner_difficulty_lp_onboarding_playbook.md`

Executable truth currently lives in:
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/profile_bootstrap_support.py`
- `core/lexishift_core/helper/use_cases/admission_preview.py`
- `core/lexishift_core/helper/use_cases/admission_candidate_index.py`
- `core/lexishift_core/srs/growth.py`
- `core/lexishift_core/srs/admission_refresh.py`
- `core/lexishift_core/srs/active_rotation.py`

## Problem

The current profile-bootstrap policy is usable, fast after the candidate index
work, and product-plausible for many profiles. Its weakness is that the
proficiency signal is still closer to a soft window than to a true frontier.

Current behavior, in simplified terms:

- difficulty ranking owns the global ordering of words on a `0..1` scale;
- admission uses the user's proficiency plus topics to choose which words enter
  the active SRS set;
- topic preference can widen readiness bounds;
- words outside the readiness bounds receive a penalty, but the penalty is soft;
- preview `score` is a profile/admission score, not the raw learner-difficulty
  score.

The observed concern is that a high-proficiency profile, such as `p=0.93`, can
still surface noticeably easier words because the existing readiness policy
keeps a wide lower range alive. Some of that is useful backfill, but if it is
unstructured it feels like the proficiency slider is not being honored.

This plan moves admission toward an explicit frontier model:

> New words should mostly be near the learner's current frontier, with a
> controlled trail for missed useful words and a controlled topic lane for
> learner interests.

## Current Policy Snapshot

Profile-bootstrap admission now uses
`profile_bootstrap_frontier_gaussian_hybrid_policy_v2` as the active
deterministic lane selector for helper initialization, admission preview, and
profile-growth refresh candidate formation. The base
`profile_bootstrap_policy_v5` utility model still supplies normalized
candidate/profile signals and the core fallback score, especially when a profile
has topic preferences but no proficiency estimate yet.

Comparison policies remain available:

- `profile_bootstrap_frontier_gaussian_policy_v1` is the first narrow frontier
  prototype;
- `profile_bootstrap_frontier_gaussian_hybrid_soft_topic_policy_v3` is the
  soft topic-bound diagnostic variant.

Hybrid soft v3 is not default-on because it recovered more topic rows at the
cost of reintroducing below-frontier leakage.

As of this plan, `profile_bootstrap_policy_v5` uses selector weights:

| Component | Weight |
| --- | ---: |
| `base_freq` | `0.05` |
| `topic_bias` | `0.30` |
| `scarcity_bonus` | `0.05` |
| `user_pref` | `0.55` |
| `confidence` | `0.00` |
| `difficulty_target` | `0.00` |

Readiness/proficiency constants:

| Constant | Value |
| --- | ---: |
| `proficiency_taper_width` | `0.75` |
| `challenge_default_spread` | `0.18` |
| `challenge_min_spread` | `0.10` |
| `readiness_base_lower_margin` | `0.15` |
| `readiness_base_upper_margin` | `0.18` |
| `readiness_topic_extra_lower_margin` | `0.12` |
| `readiness_topic_extra_upper_margin` | `0.08` |

## Passive Comparison Result

Latest artifact:

- `docs/test_outputs/srs_admission_frontier_gaussian_config_compare_en_ja_latest.md`

The latest offline comparison uses the same en-ja seed frontier, corrected
difficulty hook, and topic overlay for all selectors. It compares:

- legacy/base `profile_bootstrap_policy_v5`;
- first passive frontier selector, `profile_bootstrap_frontier_gaussian_policy_v1`;
- hybrid passive selector, `profile_bootstrap_frontier_gaussian_hybrid_policy_v2`;
- soft-topic hybrid selector,
  `profile_bootstrap_frontier_gaussian_hybrid_soft_topic_policy_v3`.

Headline over 22 profile/configuration samples:

| Metric | Legacy v5 | Frontier v1 | Hybrid v2 | Hybrid soft v3 |
| --- | ---: | ---: | ---: | ---: |
| Below target by more than `0.20` | `67` | `14` | `0` | `16` |
| Within target `±0.10` | `328` | `729` | `704` | `688` |
| Topic selections | `262` | `69` | `172` | `188` |

Interpretation:

- frontier v1 proved the Gaussian frontier geometry fixes the too-easy
  high-proficiency behavior, but made topic profiles too weak;
- hybrid v2 keeps the frontier/trail geometry, adds a beginner core lane, and
  uses adaptive topic slots with an explicit `p - 0.20` lower guard;
- hybrid soft v3 replaces the hard topic lower guard with a Gaussian lower-tail
  penalty (`sigma=0.03`), recovering some plausible topic rows just under the
  guard but reintroducing a small number of `>0.20` below-target selections;
- hybrid v2 is now the active profile-bootstrap/growth selector because it is
  the safest tested tradeoff: it preserved topic visibility better than frontier
  v1 while holding severe below-target leakage to zero in the comparison pack.
  Hybrid soft v3 is useful as a comparison candidate, not yet an obvious
  default.
| `readiness_too_easy_penalty` | `60.0` |
| `readiness_too_hard_penalty` | `35.0` |

The current indexed preview query preselects candidates by an absolute
difficulty window:

```text
lower = max(0.0, proficiency - 0.30)
upper = min(1.0, proficiency + 0.28)
```

That window is a latency optimization, not the product definition of the
admission policy. The next policy should keep an efficient index query, but the
final policy score should be defined by the frontier math below.

## Target Shape

Admission should be a deterministic multi-lane selector over a scored candidate
frontier. The default product path should not be "randomly admit words from a
big eligible bucket." It should be:

1. Build a candidate pool from indexed difficulty, topic, lifecycle, and
   suitability data.
2. Score each candidate under explicit lanes.
3. Fill the active set by deterministic lane quotas.
4. Use preview sampling only for user-facing preview variety, not for the real
   mutation order.

The policy should preserve the conceptual separation that already matters:

- difficulty ranking estimates where a word belongs on the proficiency scale;
- candidate classification decides whether a word is suitable SRS vocabulary;
- admission policy decides when to introduce suitable words to this learner;
- topic preference changes priority inside a bounded readiness range;
- browsing interest is an optional admission-pressure signal, not a bypass.

## Frontier Math

Let:

```text
d = candidate learner difficulty in [0, 1]
p = effective user proficiency in [0, 1]
t = frontier target, usually clamp(p + target_offset, 0, 1)
```

The core frontier fit should be Gaussian or Gaussian-like:

```text
frontier_fit(d, p) = exp(-0.5 * ((d - t) / sigma_side)^2)

sigma_side =
  sigma_low(p)   if d < t
  sigma_high(p)  if d >= t
```

Why asymmetric:

- a learner can usually tolerate some words above their current level;
- too many words far below their level feel wasteful;
- high-proficiency learners especially need a narrower lower tail.

Initial sweepable shape:

```text
sigma_low(p) = lerp(sigma_low_beginner, sigma_low_advanced, p)
sigma_high(p) = lerp(sigma_high_beginner, sigma_high_advanced, p)

sigma_low_beginner     in [0.12, 0.22]
sigma_low_advanced     in [0.04, 0.10]
sigma_high_beginner    in [0.10, 0.18]
sigma_high_advanced    in [0.08, 0.18]
target_offset          in [-0.03, +0.05]
```

The sweep should include the current behavior as a reproducible baseline, but
the expected winning behavior is a narrower high-proficiency lower tail.

## Deterministic Lanes

The admission set should be filled by lanes instead of one blended score. This
keeps product behavior understandable and prevents a single signal from silently
dominating.

Suggested initial quotas:

| Lane | Share | Purpose |
| --- | ---: | --- |
| Frontier | `0.65..0.80` | Mostly words near the learner's level. |
| Trail/backfill | `0.10..0.25` | Useful missed words below the frontier. |
| Topic | `0.05..0.20` | Learner-interest words that still fit readiness. |

Final admission order should be deterministic:

```text
frontier_score = frontier_fit * admission_suitability * lifecycle_ok
trail_score = trail_fit * importance * admission_suitability * lifecycle_ok
topic_score = topic_affinity * topic_fit * admission_suitability * lifecycle_ok
```

After lane selection, dedupe by candidate identity. If a lane cannot fill its
quota, spill its remainder to the frontier lane first, then to topic only if
topic support is strong enough.

## Trail And Missed Easy Words

The trail lane exists because proficiency can rise before every useful easier
word has been admitted. Without a trail, a learner who advances quickly might
miss common words that still belong in the active vocabulary journey.

Trail candidates should be below the frontier but not arbitrarily easy:

```text
below = max(0, t - d)
trail_band_fit = exp(-0.5 * ((below - trail_center) / trail_sigma)^2)
too_easy_floor = sigmoid((d - minimum_trail_difficulty) / floor_width)
trail_fit = trail_band_fit * too_easy_floor
```

Possible starting ranges:

```text
trail_center              in [0.08, 0.18]
trail_sigma               in [0.05, 0.12]
minimum_trail_difficulty  in [0.15, 0.35]
```

The lane should prefer useful words, but must avoid double-dipping the global
difficulty model. Frequency/commonness can be a tie-breaker or importance proxy
inside the trail lane, not a second full difficulty system.

## Topic Lane

Topic preference should not override level. It should widen or reshape the
frontier slightly for topic-matching candidates.

Suggested shape:

```text
topic_sigma_low = sigma_low(p) * (1 + topic_lower_widen * topic_affinity)
topic_sigma_high = sigma_high(p) * (1 + topic_upper_widen * topic_affinity)
topic_fit = gaussian(d, t, topic_sigma_side)
topic_score = topic_affinity * topic_fit * topic_quality * admission_suitability
```

Initial ranges:

```text
topic_lower_widen in [0.00, 0.60]
topic_upper_widen in [0.10, 0.80]
```

This should make topic words more likely at the same broad proficiency level,
not make beginner profiles receive extreme advanced topic vocabulary.

## Learned And Existing Words

The frontier policy must respect existing lifecycle behavior:

- active items should not be re-admitted;
- parked/released mature items should not occupy active capacity;
- discarded/suppressed items should remain blocked;
- cleared/mastered items should not be re-admitted unless a future product
  policy explicitly opts into review resurfacing.

The new policy should reuse the existing growth/admission-refresh filters. Its
job is to rank eligible candidates, not to redefine lifecycle truth.

## Proficiency Creep

The product has one simple proficiency setting from `0..1`, but we still need a
safe way for the system to update or recommend that number over time.

Recommended first estimator:

```text
eligible mastered-ish item:
  state is review
  review_count >= N
  next_due_days >= D
  recent retention is acceptable

p_auto = weighted_quantile_75(difficulty of eligible mastered-ish items)

p_effective = blend(self_reported_p, p_auto)
```

Starting ranges:

```text
N in [3, 5]
D in [5, 14]
quantile in [0.65, 0.85]
self_report_weight in [0.40, 0.80]
max_up_step_per_period in [0.02, 0.08]
max_down_step_per_period in [0.02, 0.08]
```

Guardrails:

- easy successes alone cannot prove advanced proficiency;
- proficiency should not jump upward if important lower-frontier coverage gaps
  remain large;
- user self-report should matter, but repeated SRS evidence should gradually
  correct it;
- low-confidence browsing signals should not move proficiency directly.

## Performance And Precomputation

The frontier policy should stay compatible with the current indexed preview
work. It does not require precomputing every profile or topic combination.

Static candidate facts should remain precomputed:

- candidate identity;
- corrected learner difficulty;
- lexical commonness or base frequency tie-breaker;
- candidate classification and admission suitability;
- topic memberships;
- topic source/confidence metadata;
- presentation/restriction state;
- static lifecycle-independent rulegen suitability.

Profile-dependent values should be computed at request time:

- `frontier_fit`;
- `trail_fit`;
- `topic_fit`;
- effective topic affinity for the user's selected topics;
- final lane membership and lane score;
- lifecycle filtering against the current store/inventory;
- exclusion of active, discarded, cleared, or otherwise blocked items.

This is still a closed-form calculation over a candidate matrix. The first
implementation can use the existing Python/indexed scorer for correctness. If
latency becomes a problem, the same formula can be vectorized over columns from
the candidate index because each candidate score is independent before final
lane fill and dedupe.

## Scenarios To Break

Each implementation candidate should be tested against these cases:

| Scenario | Desired behavior |
| --- | --- |
| User self-reports too high | Admit mostly near a capped frontier until review evidence catches up. |
| User self-reports too low | Stay comfortable initially, then rise with mature successful reviews. |
| User learned all words below `0.30` | `p_auto` should land around that frontier, not around individual easy successes. |
| Useful easier words were missed | Trail lane admits some, but does not dominate. |
| Topic word is much too hard | Topic lane may boost it only if still inside bounded readiness. |
| Topic word is below level | Topic lane can admit it as trail/topic value, but not flood the set. |
| High proficiency near `1.00` | Lower tail narrows; samples mostly come from advanced bands. |
| Beginner near `0.00` | Upper tail stays conservative; curriculum/common beginner words dominate. |
| Noisy browsing interest | Multi-page/time-decayed signals influence topic pressure, not difficulty truth. |
| Cleared or discarded candidate | Lifecycle filters block it regardless of score. |
| Bad difficulty label | Manual correction remains the proper fix; admission policy should not hide it. |

## Implementation Roadmap

- [x] Add an explicit admission policy version for the frontier-Gaussian
  candidate, leaving `profile_bootstrap_policy_v5` intact.
- [x] Add pure helper functions for `frontier_fit`, asymmetric sigma resolution,
  trail fit, and topic widened fit.
- [x] Add a passive offline lane selector that compares current profile scores
  against frontier/trail/topic lane scores for the same candidates.
- [x] Add a sample-pack harness that compares current policy vs frontier policy
  on real profile samples.
- [x] Extend the candidate-index query only as needed to fetch enough candidates
  around the frontier and trail bands.
- [x] Implement deterministic lane filling behind a passive policy version.
- [x] Preserve preview randomness separately from real admission order.
- [x] Add diagnostics that show raw difficulty, lane, lane score, topic
  affinity, and final rank for the passive selector.
- [ ] Add lifecycle status to frontier diagnostics once the selector is tested
  inside refresh/admission contexts.
- [ ] Add a proficiency-estimator sidecar; do not default it on until reviewed.
- [ ] Review representative samples for `en-ja`, `en-es`, and `en-de` across
  low, middle, high, and topic-heavy profiles.
- [x] Promote only after SRS quality harness, targeted policy tests, and manual
  sample review show no product regression.

## Open Decisions

- Whether real admission should be fully deterministic, or deterministic by
  lane with small preview-only randomization.
- Whether `p_effective` should be user-visible, silently used, or only offered
  as a recommendation.
- Whether self-reported proficiency should cap, blend with, or merely initialize
  `p_auto`.
- How large the trail lane should be for high-proficiency users who still have
  many lower-band gaps.
- Whether topic lane quota should be fixed, topic-depth-dependent, or allowed
  to spill when topic coverage is sparse.
- Whether browsing-derived interest should feed only topic weights, or also a
  separate source-interest score inside the topic lane.
- How aggressively cleared/mastered items should be hidden from future
  admission after long inactivity.

## Validation Criteria

A candidate policy is not accepted just because a scalar metric improves. It
must also look coherent in product samples.

Minimum evidence:

- quality harness stays clean;
- current lifecycle and suppression tests stay clean;
- indexed preview remains responsive;
- `p=0.90+` no-topic samples are mostly high difficulty, with only controlled
  trail exceptions;
- `p=0.30..0.50` samples remain learner-plausible and do not become too narrow;
- topic profiles show visible topic pressure without bypassing difficulty;
- already-active, cleared, discarded, and no-rule candidates remain blocked;
- diagnostics make it clear whether a word came from frontier, trail, or topic.

## Non-Goals

This plan does not:

- replace learner-difficulty ranking;
- introduce runtime LLM inference;
- merge difficulty, topic, and browsing interest into one opaque score;
- make every admission probabilistic;
- require precomputing every topic combination;
- solve every bad dictionary row or presentation-form issue.

The intended improvement is narrower and more concrete: make the proficiency
setting behave like a real learning frontier while preserving backfill, topic
preference, and lifecycle safety.
