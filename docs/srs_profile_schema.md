# SRS Profile Schema (Draft v3)

Related design:
- `docs/srs_hybrid_model_technical.md`
- `docs/srs_set_planning_technical.md`

## Purpose
Define profile context used for planning admission/growth of set `S`.

Profile context is not the same as SRS progress:
- profile = user intent/preferences/proficiency signals
- SRS store = per-item learning state and schedule

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
  - `srs/profiles/<profile_id>/srs_store.json`
  - `srs/profiles/<profile_id>/srs_signal_queue.json`
  - `srs/profiles/<profile_id>/srs_status.json`
  - `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
  - `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`

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
- Sizing fields are normalized by helper policy (`srs_set_policy.py`) with explicit clamps/defaults.

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
        "srsPair": "en-ja"
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
          "empiricalTrends": {"topic_bias": {"animals": 0.4}},
          "sourcePreferences": {"prefer_frequency_list": true}
        }
      }
    }
  }
}
```

Notes:
- Language-pair SRS settings are nested under the selected profile.
- Active LP (`sourceLanguage`, `targetLanguage`, `srsPair`) is also stored per selected profile in `languagePrefs`.
- Switching language pair should never reset selected profile.
- Runtime helper calls must always carry `profile_id` + `pair`.

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

## Strategy taxonomy alignment

- `frequency_bootstrap`: executable baseline.
- `profile_bootstrap`: planner-supported, currently fallback execution.
- `profile_growth`: planner-only.
- `adaptive_refresh`: planner-only, feedback-aggregation dependent.

Objectives:
- `bootstrap`
- `growth`
- `refresh`
