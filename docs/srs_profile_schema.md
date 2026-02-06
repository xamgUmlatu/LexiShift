# SRS Profile Schema (Draft v2)

This document defines the profile-scoped data model used to plan and evolve set `S`.

Design intent:
- Keep profile/config data separate from mutable SRS progress state.
- Support incremental rollout: scaffolding first, strategy logic later.
- Preserve forward compatibility by allowing unknown keys.

---

## 1) Separation of concerns

- **Profile context**: user intent and learning preferences (stable, editable).
- **SRS store**: item-level progress and scheduling state (mutable runtime state).
- **Signal queue**: feedback/exposure event stream (append-only input for adaptive policies).

Current canonical helper files:
- `srs/srs_settings.json`
- `srs/srs_store.json`
- `srs/srs_signal_queue.json`

---

## 2) Profile context payload (for planning)

`profile_context` is now accepted by helper commands (`srs_plan_set`, `srs_initialize`).
This payload is scaffolding-friendly and intentionally permissive.

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
    "recent_topic_bias": {"animals": 0.4},
    "recent_lemmas": {"猫": 12}
  },
  "source_preferences": {
    "prefer_frequency_list": true,
    "prefer_user_stream": false
  },
  "constraints": {
    "max_active_items": 40
  }
}
```

Notes:
- Only a subset is required today.
- Current executable strategy still falls back to `frequency_bootstrap`.
- Planner returns `requires_profile_fields` to show what future strategies expect.

---

## 3) Extension-local storage scaffold

The extension now reserves:
- `srsProfileSignals` (object keyed by pair)

Example:
```json
{
  "srsProfileSignals": {
    "en-ja": {
      "profileId": "default",
      "interests": ["animals", "science"],
      "objectives": ["jlpt_n4"],
      "proficiency": {"self_reported_level": 0.35},
      "empiricalTrends": {"recent_topic_bias": {"animals": 0.4}},
      "sourcePreferences": {"prefer_frequency_list": true}
    }
  }
}
```

This is currently a scaffold only; UI for editing these signals is pending.

---

## 4) Set planning contract

`srs_plan_set` / `srs_initialize` return a `plan` object:

```json
{
  "strategy_requested": "profile_bootstrap",
  "strategy_effective": "frequency_bootstrap",
  "objective": "bootstrap",
  "can_execute": true,
  "execution_mode": "frequency_bootstrap",
  "requires_profile_fields": ["interests", "proficiency", "empirical_trends"],
  "notes": [
    "Profile-aware weighting is scaffolding-only. Falling back to frequency bootstrap."
  ],
  "diagnostics": {
    "pair": "en-ja",
    "set_top_n": 800,
    "trigger": "options_initialize_button",
    "existing_items_for_pair": 42
  }
}
```

This contract is the primary extension point for future strategy logic.

---

## 5) Strategy taxonomy (current)

- `frequency_bootstrap`
  - Executable today.
  - Initializes `S` from frequency + dictionary constraints.
- `profile_bootstrap`
  - Planner-supported.
  - Currently falls back to `frequency_bootstrap`.
- `profile_growth`
  - Planner-only (not executable yet).
- `adaptive_refresh`
  - Planner-only (awaiting signal aggregation logic).

Objectives:
- `bootstrap`
- `growth`
- `refresh`

---

## 6) Forward-compatibility rules

- Unknown keys in `profile_context` should be preserved where possible.
- Planner should never fail only because extra keys are present.
- Missing optional keys should produce plan notes, not hard failures.
- Hard failure is reserved for invalid critical inputs (e.g., missing pair, missing required files for execution).
