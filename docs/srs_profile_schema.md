# SRS Profile Schema (Draft)

This document describes a **profile-scoped** SRS configuration that can live alongside
rulesets. It is designed to be flexible and forward‑compatible: new fields can be added
without breaking existing data.

Key idea:
- **Profile** = user intent + learning configuration (SRS settings, interests, weights).
- **Ruleset** = content to apply (replacement rules).
- **SRS Store** = evolving state (exposures, history, scheduling).

Only the SRS Store should be time‑mutable. Profile settings can be edited and versioned.

---

## 1) Profile Extension (planned)

```json
{
  "profile_id": "default",
  "name": "Default",
  "dataset_path": "/path/to/rulesets/default.json",
  "rulesets": ["/path/to/rulesets/default.json"],
  "active_ruleset": "/path/to/rulesets/default.json",

  "srs_profile": {
    "version": 1,
    "schema_version": 1,
    "enabled": true,
    "default_pair": {
      "source": "en",
      "target": "ja"
    },
    "feature_flags": {
      "embeddings_enabled": false,
      "consensus_filter_enabled": false,
      "stream_capture_enabled": false
    },
    "privacy": {
      "allow_stream_capture": false,
      "allow_external_sync": false
    },
    "data_sources": {
      "frequency_pack_ids": ["freq-ja-bccwj"],
      "dictionary_pack_ids": ["jmdict-ja-en"],
      "embedding_pack_ids": ["fasttext-ja"],
      "last_refreshed_at": "2026-02-03T08:30:00Z"
    },
    "pairs": {
      "en-ja": { /* SrsPairProfile */ },
      "en-en": { /* SrsPairProfile */ }
    },
    "sync": {
      "export_last_at": "2026-02-03T09:00:00Z",
      "import_last_at": null
    },
    "notes": "Optional free‑form profile notes."
  },

  "srs_store_ref": {
    "path": "/path/to/srs_store.json",
    "last_loaded_at": "2026-02-03T09:15:00Z",
    "schema_version": 1
  }
}
```

Notes:
- `srs_profile` is **configuration** only.
- `srs_store_ref` points to the separate SRS store file (actual progress).

---

## 2) SrsPairProfile (per language pair)

```json
{
  "enabled": true,

  "constraints": {
    "coverage_scalar": 0.35,
    "max_active_items": 40,
    "max_new_items_per_day": 8
  },

  "selector": {
    "weights": {
      "base_freq": 0.55,
      "topic_bias": 0.15,
      "user_pref": 0.10,
      "confidence": 0.10,
      "difficulty_target": 0.10
    },
    "penalties": {
      "recency_threshold": 0.25,
      "recency_multiplier": 0.30,
      "mastered_multiplier": 0.20,
      "oversubscribed_multiplier": 0.80
    },
    "policy": "top_n",
    "top_n": 20
  },

  "sources": {
    "frequency_pack_id": "freq-ja-bccwj",
    "dictionary_pack_ids": ["jmdict-ja-en", "jp-wordnet-sqlite"],
    "embedding_pack_ids": ["fasttext-ja"],
    "embedding_pair_enabled": true
  },

  "confidence_policy": {
    "min_confidence": 0.0,
    "gloss_decay": [1.0, 0.7, 0.5],
    "consensus_required": false
  },

  "filters": {
    "pos_allowlist": ["noun", "verb", "adj"],
    "stopwords": [],
    "min_source_length": 2,
    "allow_multiword_glosses": false
  },

  "feedback": {
    "enable_on_srs": true,
    "enable_on_ruleset": false,
    "sound_enabled": true
  },

  "limits": {
    "max_history_per_item": 50,
    "max_store_items": 8000
  },

  "highlight": {
    "enabled": true,
    "color": "#4B7DB5",
    "origin_colors": {
      "srs": "#4B7DB5",
      "ruleset": "#B5664B"
    }
  },

  "interests": {
    "topic_weights": {
      "music": 0.65,
      "animals": 0.50,
      "medicine": 0.20
    },
    "preferred_domains": ["news", "science"],
    "excluded_domains": []
  },

  "knowledge_profile": {
    "self_reported_level": 0.0,
    "known_lemmas": ["猫", "ありがとう"],
    "known_lemma_groups": ["greetings"],
    "avoid_mastered": true
  },

  "empirical_trends": {
    "recent_topic_bias": {
      "animals": 0.40,
      "travel": 0.15
    },
    "recent_lemmas": {
      "猫": 12,
      "犬": 8
    },
    "last_updated_at": "2026-02-03T08:30:00Z"
  },

  "rulegen": {
    "mode": "translation",
    "single_word_glosses_only": true,
    "allow_possessive_variants": false
  },

  "notes": "Optional free‑form pair notes."
}
```

**Design notes**
- Every sub‑object is optional. Missing values should fall back to defaults.
- New knobs can be added at any level without breaking existing profiles.
- The `sources` block is intentionally compact; it only contains IDs/flags that
  can be resolved to actual files via the language pack registry.

---

## 3) SRS Store (separate state file)

Use the existing `docs/srs_schema.md` for the SRS store definition.
The store file **must remain separate** so it can evolve without overwriting
profile settings.

---

## 4) Bundle (settings + store)

When exporting/importing learning state, combine:
- `srs_profile` (configuration)
- `srs_store` (progress)

```json
{
  "version": 1,
  "profile_id": "default",
  "srs_profile": { /* config */ },
  "srs_store": { /* items */ }
}
```

---

## 5) Forward‑Compatibility

Reserved keys for future additions:
- `features`: experimental toggles
- `debug`: diagnostic overrides
- `metadata`: arbitrary extra fields

Unknown keys should be preserved when saving.
