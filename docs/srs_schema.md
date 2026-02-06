# SRS Schema (Draft)

This schema defines the data structures needed for the SRS Practice Layer. It is intentionally independent from rulesets so the SRS layer can be enabled/disabled without mutating user rules.

## 1) SRS Settings (per user)

```json
{
  "version": 1,
  "enabled": true,
  "coverage_scalar": 0.35,
  "max_active_items": 40,
  "max_new_items_per_day": 8,
  "feedback_scale": "again_hard_good_easy",
  "pair_rules": {
    "en-en": {"enabled": true},
    "de-en": {"enabled": false}
  },
  "sync": {
    "export_last_at": "2026-01-29T10:30:00Z",
    "import_last_at": null
  }
}
```

### Fields
- `version` (int): schema version.
- `enabled` (bool): global toggle for SRS practice layer.
- `coverage_scalar` (float, 0–1 or 0–100): drives how far beyond the base lexicon S expands.
- `max_active_items` (int): cap on simultaneously “active” items.
- `max_new_items_per_day` (int): throttle for growth.
- `feedback_scale` (string): UI scale, e.g., `again_hard_good_easy`.
- `pair_rules` (object): per language-pair settings and gating.
- `sync` (object): timestamps for export/import.

---

## 2) SRS Item (per word/lemma)

```json
{
  "item_id": "en-en:gloaming",
  "lemma": "gloaming",
  "language_pair": "en-en",
  "source_type": "initial_set",
  "confidence": 0.83,
  "stability": 3.1,
  "difficulty": 0.42,
  "last_seen": "2026-01-28T18:05:00Z",
  "next_due": "2026-02-01T00:00:00Z",
  "exposures": 6,
  "srs_history": [
    {"ts": "2026-01-20T09:00:00Z", "rating": "good"},
    {"ts": "2026-01-23T09:00:00Z", "rating": "hard"}
  ]
}
```

### Fields
- `item_id` (string): stable identifier, usually `{pair}:{lemma}`.
- `lemma` (string): canonical form of the word.
- `language_pair` (string): e.g., `en-en`, `de-en`.
- `source_type` (string): e.g., `initial_set`, `frequency_list`, `user_stream`, `curated`.
- `confidence` (float, 0–1): dictionary/embedding confidence (optional but recommended).
- `stability` (float): SRS stability value.
- `difficulty` (float): SRS difficulty value.
- `last_seen` (timestamp): last time item appeared.
- `next_due` (timestamp): next scheduled review.
- `exposures` (int): total exposures in text streams.
- `srs_history` (array): list of feedback events.

---

## 3) SRS Item Store (collection)

```json
{
  "version": 1,
  "items": [
    {"item_id": "en-en:gloaming", "lemma": "gloaming", "language_pair": "en-en", "next_due": "2026-02-01T00:00:00Z"}
  ]
}
```

---

## 4) Practice Gate State (runtime only)

```json
{
  "active_pairs": ["en-en"],
  "active_items": ["en-en:gloaming", "en-en:crepuscule"],
  "generated_at": "2026-01-29T12:00:00Z"
}
```

This is in‑memory state used for gating replacements, not persisted by default.

---

## 5) Export/Import Bundles

### Bundle Format
```json
{
  "settings": { /* SRS Settings */ },
  "items": { /* SRS Item Store */ }
}
```

Use this bundle for syncing across app/extension/plugin.

---

## 6) SRS Signal Queue (event stream, scaffold)

```json
{
  "version": 1,
  "events": [
    {
      "event_type": "feedback",
      "pair": "en-ja",
      "lemma": "猫",
      "source_type": "extension",
      "rating": "good",
      "ts": "2026-02-06T10:00:00Z",
      "metadata": {}
    },
    {
      "event_type": "exposure",
      "pair": "en-ja",
      "lemma": "犬",
      "source_type": "extension",
      "ts": "2026-02-06T10:01:00Z",
      "metadata": {}
    }
  ]
}
```

Purpose:
- Collect feedback/exposure input from runtime surfaces.
- Feed future adaptive set update strategies.

---

## Notes
- **Non‑destructive:** rulesets remain unchanged; the practice layer gates replacements at runtime.
- **Pair‑aware:** items are only applied in matching language-pair contexts.
- **Extensible:** add filters and candidate sources without breaking existing data.
