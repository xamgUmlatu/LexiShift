# SRS Schema (Current + Planned)

Related design:
- `docs/srs/srs_hybrid_model_technical.md`

This schema document separates what is implemented now from planned extensibility fields.

---

## 1) SRS Settings (implemented)

```json
{
  "version": 1,
  "enabled": true,
  "coverage_scalar": 0.35,
  "max_active_items": 40,
  "max_new_items_per_day": 8,
  "feedback_scale": "again_hard_good_easy",
  "pair_rules": {
    "en-ja": {"enabled": true}
  },
  "sync": {
    "export_last_at": null,
    "import_last_at": null
  }
}
```

Key semantics:
- `feedback_scale` maps UI choices to ratings:
  - `1 -> again`
  - `2 -> hard`
  - `3 -> good`
  - `4 -> easy`
- `max_active_items` caps study load.
- `max_new_items_per_day` throttles growth into `S`.
- Pair bootstrap sizing is currently configured via profile/options payload:
  - `bootstrap_top_n` (default `800`)
  - `initial_active_count` (default `40`)
  - Admission rule: only `initial_active_count` unique lemmas are written into sparse `S` at initialization.

---

## 2) SRS Item Store (implemented shape)

```json
{
  "version": 1,
  "items": [
    {
      "item_id": "en-ja:猫",
      "lemma": "猫",
      "language_pair": "en-ja",
      "source_type": "initial_set",
      "confidence": 0.81,
      "stability": 1.5,
      "difficulty": 0.45,
      "last_seen": "2026-02-06T11:12:13+00:00",
      "next_due": "2026-02-08T11:12:13+00:00",
      "exposures": 3,
      "srs_history": [
        {"ts": "2026-02-04T10:00:00+00:00", "rating": "good"},
        {"ts": "2026-02-06T11:12:13+00:00", "rating": "hard"}
      ]
    }
  ]
}
```

Notes:
- This sparse store is the persisted study inventory `S`.
- Items not in `S` are implicitly outside the active curriculum.
- `next_due` drives due-based serving order.
- `source_type: "initial_set"` identifies words admitted by bootstrap initialization.
- Current store does not require a single explicit `probability` column; serving probability is derived from due/order policy at runtime.

---

## 3) Planned item extensions (not required yet)

These fields improve lifecycle clarity without breaking existing data:

```json
{
  "status": "learning",
  "review_count": 12,
  "lapses": 2,
  "admission_base_weight": 0.73,
  "admission_profile_bias": 0.18,
  "admission_score": 0.86,
  "admission_source": "frequency+pos+profile",
  "admission_version": 1,
  "admission_updated_at": "2026-02-07T10:00:00+00:00",
  "serving_priority_bias": 0.15,
  "suspended": false
}
```

Recommended statuses:
- `new`
- `learning`
- `review`
- `mature`
- `relearn`
- `suspended`

Meaning:
- `admission_*` fields correspond to **weight 1** (entry/growth decision into `S`).
- scheduler fields (`next_due`, `stability`, `difficulty`) plus optional `serving_priority_bias` correspond to **weight 2** (serving order/probability inside `S`).

---

## 4) Planned profile admission state (pair-level, helper-owned)

Suggested helper-owned sidecar file:
- `srs/srs_admission_profile.json`

Suggested shape:

```json
{
  "version": 1,
  "pairs": {
    "en-ja": {
      "updated_at": "2026-02-07T10:00:00+00:00",
      "signals_hash": "sha256:...",
      "pos_bias": {
        "名詞": 1.25,
        "動詞": 1.05,
        "形容詞": 1.05,
        "助詞": 0.0,
        "助動詞": 0.0
      },
      "interest_bias": {},
      "proficiency_bias": {},
      "difficulty_bias": {}
    }
  }
}
```

Rationale:
- Keep admission policy state in helper storage (source of truth), not extension-local.
- Keep profile knobs pair-scoped and versioned for safe evolution.
- Keep per-item scheduling state independent from profile knobs once item is in normal review flow.

---

## 5) Practice Gate State (runtime, optional persistence)

```json
{
  "active_pairs": ["en-ja"],
  "active_items": ["en-ja:猫", "en-ja:犬"],
  "generated_at": "2026-02-06T12:00:00+00:00"
}
```

This is runtime-derived from settings + due policy.

---

## 6) Signal Queue (scheduling policy: feedback authoritative)

Current queue shape can hold multiple event types:

```json
{
  "version": 1,
  "events": [
    {
      "event_type": "feedback",
      "pair": "en-ja",
      "lemma": "猫",
      "source_type": "extension",
      "rating": "again",
      "ts": "2026-02-06T12:10:00+00:00",
      "metadata": {}
    }
  ]
}
```

Policy for this architecture:
- Scheduling consumes `feedback` events.
- Passive display/exposure logs are telemetry only unless explicitly promoted by policy.

---

## 7) Export/import bundle

```json
{
  "settings": { /* SRS settings */ },
  "items": { /* SRS item store */ }
}
```

Bundle remains stable as fields are added; unknown keys should be preserved where possible.
