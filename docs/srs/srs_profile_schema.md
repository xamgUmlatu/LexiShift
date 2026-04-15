# SRS Profile Schema (Draft v3)

Related design:
- `docs/srs/srs_hybrid_model_technical.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_preference_update_and_rebalance_policy.md`
- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`

## Purpose
Define profile context used for planning admission/growth of set `S`.

Profile context is not the same as SRS progress:
- profile = user intent/preferences/proficiency signals
- SRS store = per-item learning state and schedule

It is also not the same as lexical/rulegen difficulty.

## Difficulty separation

Future SRS planning should keep at least four distinct concepts separate:

- lexical / rulegen difficulty:
  - ambiguity, phrase pressure, register leakage, and other properties of the word itself
- user proficiency:
  - self-report, placement outcome, known-lemma coverage, or similar learner-state inputs
- target challenge region:
  - where the user wants to begin or concentrate in the curriculum continuum
- optional target vocabulary label:
  - a soft user-facing summary, not the primary storage primitive
- observed SRS difficulty:
  - item-specific learning difficulty after the learner has already interacted with the item

This matters because an intermediate learner may need to begin SRS around an intermediate region even before any local item history exists.

So onboarding/planning must not depend on observed SRS difficulty alone.

## Separation of concerns

- Profile context:
  - relatively stable
  - editable by user/preferences UI
  - consumed by planner
- SRS store:
  - mutable learning state
  - updated by feedback
- Signal queue:
  - append-only event stream
  - feedback is authoritative scheduling signal

## Canonical helper files
- Global helper policy:
  - `srs/srs_settings.json`
- Profile-scoped helper state:
  - `srs/profiles/<profile_id>/srs_inventory.json`
  - `srs/profiles/<profile_id>/srs_store.json`
  - `srs/profiles/<profile_id>/srs_signal_queue.json`
  - `srs/profiles/<profile_id>/srs_status.json`
  - `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
  - `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`

Current role split:
- `srs_inventory.json`
  - pair-local active-inventory membership for admission/publication/runtime serving
- `srs_store.json`
  - retained item history, scheduling state, and word packages, including parked/protected records that may no longer be active

## Profile context payload (planner input)

```json
{
  "pair": "en-ja",
  "profile_id": "default",
  "interests": ["animals", "science"],
  "objectives": ["jlpt_n4", "daily_reading"],
  "proficiency": {
    "self_reported_level": 0.35,
    "known_lemmas": ["猫", "犬"]
  },
  "difficulty_preferences": {
    "target_challenge_center": 0.58,
    "target_challenge_spread": 0.18,
    "target_vocabulary_label": "intermediate",
    "target_label_confidence": 0.7
  },
  "empirical_trends": {
    "recent_feedback": {
      "again_rate": 0.22,
      "hard_rate": 0.18,
      "good_rate": 0.48,
      "easy_rate": 0.12
    },
    "topic_bias": {"animals": 0.4}
  },
  "source_preferences": {
    "prefer_frequency_list": true,
    "prefer_user_stream": false,
    "prefer_curated": true
  },
  "constraints": {
    "max_active_items": 40,
    "max_new_items_per_day": 8,
    "bootstrap_top_n": 800,
    "initial_active_count": 40
  }
}
```

Notes:
- Planner should tolerate missing optional keys.
- Unknown keys should be preserved where possible.
- Invalid critical values should produce diagnostics/notes before hard failure.
- Sizing fields are normalized by helper policy (`srs/set_policy.py`) with explicit clamps/defaults.
- `difficulty_preferences` is illustrative here; the main requirement is to keep target challenge preferences separate from both `proficiency` and later observed SRS difficulty.
- `target_vocabulary_label` should remain a soft summary for UI or reporting, not the only stored truth.

## Extension-local scaffold

Reserved keys in extension storage:
- `srsSelectedProfileId` (global selected profile for runtime/options)
- `srsProfiles` (profile-first container; no legacy fallback schema)

Example:

```json
{
  "srsSelectedProfileId": "default",
  "srsProfiles": {
    "default": {
      "languagePrefs": {
        "sourceLanguage": "en",
        "targetLanguage": "ja",
        "srsPairAuto": true,
        "srsPair": "en-ja",
        "targetScriptPrefs": {
          "ja": {
            "primaryDisplayScript": "kanji"
          }
        }
      },
      "srsByPair": {
        "en-ja": {
          "srsEnabled": true,
          "srsMaxActive": 40,
          "srsBootstrapTopN": 800,
          "srsInitialActiveCount": 40
        }
      },
      "srsSignalsByPair": {
        "en-ja": {
          "interests": ["animals", "science"],
          "objectives": ["jlpt_n4"],
          "proficiency": {"self_reported_level": 0.35},
          "difficultyPreferences": {
            "target_challenge_center": 0.58,
            "target_challenge_spread": 0.18
          },
          "empiricalTrends": {"topic_bias": {"animals": 0.4}},
          "sourcePreferences": {"prefer_frequency_list": true}
        }
      },
      "uiPrefs": {
        "backgroundEnabled": false,
        "backgroundAssetId": "",
        "backgroundOpacity": 0.18,
        "backgroundBackdropColor": "#fbf7f0"
      }
    }
  }
}
```

Notes:
- Language-pair SRS settings are nested under the selected profile.
- Active LP (`sourceLanguage`, `targetLanguage`, `srsPair`) is also stored per selected profile in `languagePrefs`.
- Target-language display preferences are stored per profile in `languagePrefs.targetScriptPrefs` (for example Japanese script preference).
- Profile UI preferences are also stored per selected profile in `uiPrefs` and are independent from helper scheduling data.
- Runtime mirrors for background UI (`profileBackground*`) are published from `uiPrefs` only when user clicks Apply in options.
- Switching language pair should never reset selected profile.
- Runtime helper calls must always carry `profile_id` + `pair`.

## Current executable `profile_bootstrap` contract

The helper now normalizes raw `profile_context` into an explicit internal bootstrap context before scoring.

Current normalized fields:
- `explicit_topic_weights`
- `implicit_topic_weights`
- `topic_weights`
- `proficiency_estimate`
- `challenge_target`
- `challenge_spread`
- diagnostics for `raw_profile_keys`, `active_signals`, `missing_signals`, and per-signal sources

Current accepted planner inputs for that normalization:
- `interests`
- `topic_weights`
- `empirical_trends.topic_bias`
- `proficiency.self_reported_level`
- `proficiency.estimated_value`
- `difficulty_preferences.target_challenge_center`
- `difficulty_preferences.target_challenge_spread`
- `placement_result.proficiency_estimate.value`
- `placement_result.target_challenge.center`
- `placement_result.target_challenge.spread`

Current explicit-topic semantics:
- selected `interests` are normalized into `explicit_topic_weights` with weight `1.0`
- any saved/manual `topic_weights` input is merged into that same explicit layer
- `topic_weights` is then the final merged view across explicit and implicit topic bias

Current non-goals and limits:
- this is still bootstrap reranking only, not full preference architecture
- missing signals stay explicitly neutral; the helper does not invent challenge preferences
- candidate difficulty is still a coarse proxy derived from neutral admission weight, not a full curriculum model
- topical lift is limited by explicit topic weights, candidate topic hints, or exact lexical matches
- profile-aware admission should tilt probabilities rather than hard-filter core vocabulary out of the bootstrap frontier
- exact implicit lexical trends are not yet a first-class normalized field or lane
- register/style preferences such as `slang` are future separate-axis work, not topic fields

Current preview semantics:
- planner scoring stays deterministic
- live active-set admission now uses an explicit weighted-without-replacement selector over the scored bootstrap frontier
- the user-facing admission sample may be stochastic and vary across presses because it reuses that same selector
- fixed seeds remain a debug/test seam so preview and live selection can be compared reproducibly

## Planner contract expectations

`srs_plan_set` / `srs_initialize` should continue to return:
- `strategy_requested`
- `strategy_effective`
- `can_execute`
- `execution_mode`
- `requires_profile_fields`
- `notes`
- `diagnostics`

This keeps profile modeling decoupled from mutation details.

It also leaves room for future planner outputs that can explain:

- estimated proficiency band
- chosen target challenge center/spread
- optional chosen target vocabulary label
- confidence in that choice

## Strategy taxonomy alignment

- `frequency_bootstrap`: executable baseline.
- `profile_bootstrap`: executable bootstrap reranking over the neutral seed pool; current signals are proficiency fit, interest/topic affinity when hints exist, and challenge preference fit.
- `profile_growth`: partially executable for manual `objective="rebalance"` preview/apply; general continuous growth is still not implemented.
- `adaptive_refresh`: planner-only, feedback-aggregation dependent.

Objectives:
- `bootstrap`
- `growth`
- `refresh`
- `rebalance`
