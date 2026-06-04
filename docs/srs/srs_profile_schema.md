# SRS Profile Schema (Draft v3)

Status: active mixed schema reference
Role: Mixed
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 normalization plus SRS-adjacent doc/code/test read; schema content not fully re-audited
Purpose: describe the current SRS profile signal shapes, helper profile context, and sizing fields while preserving planned schema context
Source-of-truth: mixed schema reference; executable truth lives in extension SRS profile/settings code, helper SRS planning code, and focused profile-schema tests.

Related design:
- `docs/srs/srs_hybrid_model_technical.md`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_preference_taxonomy_lifecycle.md`

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

## Current Executable Shapes

This workstream currently has three related but distinct shapes:

1. extension-managed signal storage
2. normalized helper `profile_context`
3. top-level helper sizing fields

Do not treat those as interchangeable.

### 1. Extension-managed signal storage

Current signal storage lives under:

- `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`

Current executable top-level signal allowlist (`v1`):

- `interests`
- `objectives`
- `proficiency`
- `difficultyPreferences`
- `empiricalTrends`
- `sourcePreferences`

Current stored example:

```json
{
  "interests": ["animals", "science"],
  "objectives": ["jlpt_n4", "daily_reading"],
  "proficiency": {
    "estimated_value": 0.35,
    "known_lemmas": ["猫", "犬"]
  },
  "difficultyPreferences": {
    "target_challenge_center": 0.55
  },
  "empiricalTrends": {
    "recent_feedback": {
      "again_rate": 0.22,
      "hard_rate": 0.18,
      "good_rate": 0.48,
      "easy_rate": 0.12
    },
    "topic_bias": {"animals": 0.4}
  },
  "sourcePreferences": {
    "prefer_frequency_list": true,
    "prefer_user_stream": false,
    "prefer_curated": true
  }
}
```

Notes:

- the extension settings path rebuilds the signal object from that fixed top-level allowlist
- unknown top-level signal families are dropped before helper code sees them
- within the allowed object families, non-empty nested keys are currently retained
- current options UI directly edits:
  - `interests`
  - `proficiency.estimated_value`
  - `difficultyPreferences.target_challenge_center`
- other stored signal families are data-ready and persisted, but not all are first-class UI controls yet

### Preference Taxonomy Expansion

Post-release topic/register expansion is intended to be additive. New
preference IDs should be added under existing profile signal families, usually
`interests` or nested topic-bias data, unless a schema migration updates the
top-level allowlist and tests first.

Adding a new topic/register preference must not mutate the SRS store scheduler
state. The new preference can affect future admission and diagnostics, and
source metadata can optionally enrich existing items, but it must not delete,
reset, or reschedule already-admitted cards.

Use `srs_preference_taxonomy_lifecycle.md` for the append-only ID policy,
axis/UX grouping rules, pair-scoped availability, and migration requirements.

### 2. Normalized Helper `profile_context`

`composeSrsPlanContext(...)` converts the extension storage shape into the helper-facing planner context.

Current normalized helper example:

```json
{
  "pair": "en-ja",
  "profile_id": "default",
  "interests": ["animals", "science"],
  "objectives": ["jlpt_n4", "daily_reading"],
  "proficiency": {
    "estimated_value": 0.35,
    "known_lemmas": ["猫", "犬"]
  },
  "difficulty_preferences": {
    "target_challenge_center": 0.55
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
    "max_active_items": 40
  },
  "sizing": {
    "bootstrap_top_n": 800,
    "initial_active_count": 40
  }
}
```

Notes:
- Planner should tolerate missing optional keys.
- The helper-facing shape uses normalized snake_case keys such as:
  - `difficulty_preferences`
  - `empirical_trends`
  - `source_preferences`
- `pair` and `profile_id` are added by the extension/helper planning layer; they are not stored inside `srsSignalsByPair`.
- Invalid critical values should produce diagnostics/notes before hard failure.
- Nested `constraints` / `sizing` are descriptive mirrors used to keep planner context cohesive.
- They are not the authoritative execution sizing source.

Current helper-side feature normalization reads most directly from:

- `interests`
- `proficiency.estimated_value`
- `proficiency.self_reported_level`
- `difficulty_preferences.target_challenge_center`
- `difficulty_preferences.target_challenge_spread`
- `difficulty_preferences.goal_mode`
- `empirical_trends.topic_bias`

Other nested keys inside the allowed families may survive storage and diagnostics, but they are not guaranteed to affect current helper execution.

### 3. Authoritative Helper Request Sizing

Current helper initialize / plan / preview requests still send sizing at the top level.

Current request envelope example:

```json
{
  "pair": "en-ja",
  "profile_id": "default",
  "set_top_n": 800,
  "bootstrap_top_n": 800,
  "initial_active_count": 40,
  "max_active_items_hint": 40,
  "profile_context": {
    "pair": "en-ja",
    "profile_id": "default",
    "interests": ["animals", "science"],
    "objectives": ["jlpt_n4", "daily_reading"],
    "proficiency": {
      "estimated_value": 0.35,
      "known_lemmas": ["猫", "犬"]
    },
    "difficulty_preferences": {
      "target_challenge_center": 0.55
    },
    "empirical_trends": {
      "topic_bias": {"animals": 0.4}
    },
    "source_preferences": {
      "prefer_frequency_list": true
    },
    "constraints": {
      "max_active_items": 40
    },
    "sizing": {
      "bootstrap_top_n": 800,
      "initial_active_count": 40
    }
  }
}
```

Notes:

- helper use cases currently resolve sizing from top-level request fields:
  - `set_top_n`
  - `bootstrap_top_n`
  - `initial_active_count`
  - `max_active_items_hint`
- sizing normalization is centralized in `srs/set_policy.py`
- if nested `profile_context.constraints` / `profile_context.sizing` disagree with the top-level request, the top-level request wins

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
          "proficiency": {"estimated_value": 0.35},
          "difficultyPreferences": {"target_challenge_center": 0.55},
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
- `profile_bootstrap`: executable when requested; options initialize and
  admission preview request this strategy with normalized profile context.
- `profile_growth`: executable for refresh/growth admission and dedicated
  rebalance preview/apply.
- `adaptive_refresh`: planner-only, feedback-aggregation dependent.

Objectives:
- `bootstrap`
- `growth`
- `refresh`
