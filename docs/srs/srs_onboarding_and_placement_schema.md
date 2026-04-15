# SRS Onboarding And Placement Schema (Draft v1)

Status: active proposal
Role: Planning / WIP
Purpose: define a concrete future schema for onboarding/placement inputs, placement outputs, and a shared diagnostics payload that can later support both SRS planning and trait-conditioned rulegen routing without collapsing distinct difficulty concepts into one score.
Last updated: 2026-03-29
Last verified: 2026-03-29
Source-of-truth: planning doc only; executable truth still lives in future planner/profile code, benchmark trait payloads, and helper-owned SRS planning contracts.

Related design:
- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_selector_technical.md`
- `docs/rulegen/trait_conditioned_rulegen_profiles.md`

## Purpose

This doc makes the difficulty/proficiency model concrete enough to implement later.

It defines three future payload types:

1. onboarding / placement input
2. placement output
3. shared diagnostics payload

The design goal is:

- let SRS onboarding choose a sensible starting region for a learner in a continuous vocabulary space
- keep that choice explainable
- keep the same conceptual vocabulary compatible with later trait-based rulegen routing

## Non-Goal

This is not a claim that:

- the current app already exposes these fields
- the current helper already stores these exact payloads
- rulegen should directly consume SRS profile payloads today

This is a forward-compatible planning contract.

## Core Separation

These concepts must remain distinct:

- `user_proficiency_estimate`
- `target_challenge_center`
- `target_challenge_spread`
- optional `target_vocabulary_band_label`
- `lexical_rulegen_difficulty`
- `observed_srs_difficulty`

If a future planner computes aggregate scalars, they must remain derived values, not the only source of truth.

## Design Principles

1. Keep user context separate from word-intrinsic traits.
2. Keep observed learning history separate from cold-start placement.
3. Keep decomposed diagnostics even if the planner also emits aggregate scores.
4. Use continuous internal values first; any labels or bands should be derived summaries.
5. Make the payload explainable enough for UI and logs.

## Continuous Model First

The internal placement/admission model should be continuous.

That means:

- the user is represented by continuous signals
- the candidate words are represented by continuous signals
- placement and admission are based on fit within that space

Named labels like:

- beginner
- intermediate
- advanced

may still exist, but should be treated as:

- UI summaries
- explanation labels
- optional reporting categories

not the primary storage model.

## Recommended First UI Shape

The recommended user-facing control surface is:

- one scalar challenge slider
- explicit preference controls
- later implicit interest weighting behind the scenes
- a `generate sample words` button

That preview should use the same admission logic as the actual planner.

## 1. Onboarding / Placement Input

This payload is the cold-start or re-placement request for one user profile and pair.

Illustrative shape:

```json
{
  "version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "trigger": "first_run",
  "proficiency_signals": {
    "self_report": {
      "label": "intermediate",
      "scale": "cefr_like",
      "value": 0.5,
      "confidence": 0.6
    },
    "placement_probe": {
      "completed": false,
      "estimated_value": null,
      "confidence": null
    },
    "known_lemma_probe": {
      "sample_size": 0,
      "known_ratio": null,
      "estimated_value": null,
      "confidence": null
    },
    "imported_history": {
      "present": false,
      "estimated_value": null,
      "confidence": null
    }
  },
  "challenge_preferences": {
    "target_center": 0.58,
    "target_spread": 0.18,
    "derived_label": "intermediate",
    "allow_auto_adjust": true
  },
  "learning_preferences": {
    "goal_mode": "balanced",
    "domain_bias": ["daily_life", "web"],
    "technical_tolerance": 0.25,
    "slang_tolerance": 0.15
  },
  "constraints": {
    "bootstrap_top_n": 800,
    "initial_active_count": 40,
    "max_new_items_per_day": 8
  }
}
```

### Notes

- `proficiency_signals` is decomposed evidence, not the final answer.
- `challenge_preferences` is the important planner input.
- `derived_label` is a soft UI summary, not a rigid constraint.
- `goal_mode` is broader than proficiency:
  - two users with the same proficiency may want different vocabulary mixes

### Minimum viable version

The earliest useful implementation can support only:

- self-report
- scalar challenge preference
- basic sizing constraints

and leave the rest nullable.

## 2. Placement Output

This payload is the planner's chosen onboarding result.

Illustrative shape:

```json
{
  "version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "placement_result": {
    "proficiency_estimate": {
      "value": 0.52,
      "confidence": 0.68,
      "derived_label": "intermediate",
      "sources_used": ["self_report"]
    },
    "target_challenge": {
      "center": 0.56,
      "spread": 0.17,
      "derived_label": "intermediate_core",
      "growth_mode": "balanced"
    },
    "planner_decision": {
      "decision_mode": "cold_start_region_selection",
      "can_execute": true,
      "notes": [
        "Using self-report as the only proficiency signal.",
        "Requested challenge level accepted with a moderate spread."
      ]
    }
  }
}
```

### Why output both proficiency and challenge target

They are not the same thing.

Examples:

- a learner may be broadly intermediate but want a slightly easier challenge center
- an advanced learner may still want a balanced non-technical region
- a lower-confidence placement may choose a narrower spread even if the estimated proficiency is higher

## 3. Optional Derived Label Schema

If the product wants named labels, they should be derived summaries over the continuous model.

Illustrative shape:

```json
{
  "label": "intermediate_core",
  "description": "Common-to-mid vocabulary with limited technicality and moderate ambiguity tolerance.",
  "heuristics": {
    "challenge_center": 0.56,
    "challenge_spread": 0.17,
    "frequency_percentile_min": 0.20,
    "frequency_percentile_max": 0.55,
    "technical_tolerance": 0.30,
    "ambiguity_tolerance": 0.45
  }
}
```

### Why keep labels optional

Named labels are:

- easier to explain in UI
- easier to keep stable over time
- useful for analytics and summaries

But they should not become rigid gating buckets.

## 4. Shared Diagnostics Payload

This is the key bridge between SRS planning and future rulegen routing.

It should keep decomposed evidence available for diagnostics, analysis, and later learned grouping.

Illustrative shape:

```json
{
  "version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "context": {
    "estimated_proficiency_label": "intermediate",
    "target_challenge_center": 0.56,
    "target_challenge_spread": 0.17,
    "target_vocabulary_label": "intermediate_core",
    "goal_mode": "balanced"
  },
  "decomposed_signals": {
    "proficiency": {
      "self_report_value": 0.5,
      "placement_value": null,
      "known_lemma_value": null,
      "aggregate_value": 0.52,
      "confidence": 0.68
    },
    "challenge_fit": {
      "target_center": 0.56,
      "target_spread": 0.17,
      "fit_value": 0.74
    },
    "topic_affinity": {
      "explicit_preference_fit": 0.66,
      "implicit_interest_fit": 0.41
    },
    "lexical_commonness": {
      "frequency_percentile": 0.37,
      "source_frequency_percentile": 0.42
    },
    "lexical_rulegen_difficulty": {
      "ambiguity": 0.61,
      "phrase_pressure": 0.18,
      "register_risk": 0.12,
      "domain_pressure": 0.21
    },
    "observed_srs_difficulty": {
      "available": false,
      "difficulty": null,
      "stability": null
    }
  },
  "derived_aggregates": {
    "difficulty_target": 0.58
  },
  "explanations": [
    "Intermediate self-report with no local history.",
    "Challenge fit favors mid-range vocabulary with moderate spread.",
    "Lexical ambiguity is moderate but not extreme."
  ]
}
```

## 5. How SRS Uses The Shared Diagnostics

SRS onboarding/planning should primarily use:

- `proficiency`
- `challenge_fit`
- `topic_affinity`
- `lexical_commonness`
- later `observed_srs_difficulty`

Cold-start SRS should not require `observed_srs_difficulty`.

## 6. How Rulegen Could Later Use The Shared Diagnostics

Future rulegen routing should **not** consume the whole SRS placement payload blindly.

Instead, it may use selected context plus lexical signals such as:

- target challenge center/spread
- optional derived label
- goal mode
- lexical rulegen difficulty
- lexical commonness

Important:

- user proficiency is allowed as explicit external context
- observed SRS difficulty should usually stay an SRS-side feature unless there is a later proven use case

## 7. Optional Stable Labels

Illustrative early labels:

- proficiency labels:
  - `beginner`
  - `lower_intermediate`
  - `intermediate`
  - `upper_intermediate`
  - `advanced`

- target-vocabulary labels:
  - `beginner_core`
  - `intermediate_core`
  - `balanced_general`
  - `advanced_general`
  - `advanced_technical`

- goal modes:
  - `safe`
  - `balanced`
  - `technical`
  - `conversation`
  - `reading`

These are examples only. The schema should tolerate later refinement and should never require the planner to operate only on labels.

## 8. Cold-Start vs Warm-Start Rule

Cold start:

- rely on self-report, placement, known-lemma probes, and explicit preferences

Warm start:

- refine with observed SRS difficulty and retention behavior

The same output contract should work in both states.

## 9. Recommended Near-Term Implementation Order

1. keep this as a planning contract first
2. later add `difficulty_preferences` / placement fields to profile planning payloads
3. keep derived `difficulty_target` explainable and decomposable
4. implement scalar challenge control plus preview before introducing rigid label-based UX
5. only after real placement inputs exist, decide which fields become required

## 10. Open Questions

1. Should derived labels be global across pairs or pair-specific with shared names?
2. Should `goal_mode` stay free-form at first or use strict enums immediately?
3. Should the first placement flow prefer:
   - pure self-report
   - self-report plus a small known-lemma probe
   - or a true placement quiz
4. How stable should the preview sample be across repeated clicks under the same settings?

## Recommended Current Answer

For the first real implementation:

- keep proficiency estimate and target challenge as separate outputs
- allow self-report to be the initial primary signal
- use a scalar challenge control for the user-facing level input
- use sample-word preview from the same admission scorer
- add known-lemma probing later
- keep shared diagnostics decomposed even if a derived `difficulty_target` scalar is also emitted
