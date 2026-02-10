# LexiShift JSON Schemas

This document describes the JSON formats LexiShift reads/writes today. All fields are ASCII and lowercase in JSON.

## 1) Ruleset (VocabDataset)

File: ruleset JSON (per ruleset file).

Top-level fields
- `version` (int, optional, default: 1)
- `rules` (array of `VocabRule`, optional)
- `meaning_rules` (array of `MeaningRule`, optional)
- `synonyms` (object map, optional; key -> canonical word)
- `settings` (object, optional; `VocabSettings`)

### VocabRule
- `source_phrase` (string, required)
- `replacement` (string, required)
- `priority` (int, optional, default: 0)
- `case_policy` (string, optional, default: `match`)
  - Allowed: `match`, `as-is`, `lower`, `upper`, `title`
- `enabled` (bool, optional, default: true)
- `tags` (array of string, optional)
- `metadata` (object, optional; `RuleMetadata`)
- `created_at` (string, optional; ISO 8601 preferred)

### MeaningRule
- `source_phrases` (array of string, required)
- `replacement` (string, required)
- `priority` (int, optional, default: 0)
- `case_policy` (string, optional, default: `match`)
- `enabled` (bool, optional, default: true)
- `tags` (array of string, optional)
- `metadata` (object, optional; `RuleMetadata`)

### RuleMetadata
- `label` (string, optional)
- `description` (string, optional)
- `examples` (array of string, optional)
- `notes` (string, optional)
- `source` (string, optional)
- `source_type` (string, optional)
- `language_pair` (string, optional; e.g., `en-en`, `de-en`)
- `confidence` (float, optional; 0–1)
- `script_forms` (object map, optional; script -> display form, e.g. `{ "kanji": "猫", "kana": "ねこ", "romaji": "neko" }`)

### VocabSettings
- `inflections` (object, optional; `InflectionSettings`)
- `learning` (object, optional; `LearningSettings`)

### InflectionSettings
- `enabled` (bool, optional, default: true)
- `spec` (object, optional; `InflectionSpec`)
- `per_rule_spec` (object map, optional; key -> `InflectionSpec`)
- `strict` (bool, optional, default: true)
- `overrides` (object, optional; `InflectionOverrides`)
- `include_generated_tag` (bool, optional, default: true)
- `generated_tag` (string, optional, default: `generated`)

### InflectionSpec
- `forms` (array of string, optional)
  - Typical values: `plural`, `possessive`, `past`, `gerund`, `third_person`
- `apply_to` (string, optional, default: `last_word`)
  - Allowed: `last_word`, `all_words`
- `include_original` (bool, optional, default: true)

### InflectionOverrides
- `plurals` (object map, optional; base -> plural)
- `past` (object map, optional; base -> past)
- `gerunds` (object map, optional; base -> gerund)
- `third_person` (object map, optional; base -> third-person)
- `blocked` (array of string, optional)

### LearningSettings
- `enabled` (bool, optional, default: false)
- `show_original` (bool, optional, default: true)
- `show_original_mode` (string, optional, default: `tooltip`)
  - Allowed: `tooltip`, `inline`, `side-by-side`
- `highlight_replacements` (bool, optional, default: true)

Example (minimal)
```json
{
  "version": 1,
  "rules": [
    {
      "source_phrase": "twilight",
      "replacement": "gloaming"
    }
  ],
  "meaning_rules": [],
  "synonyms": {}
}
```

Example (with settings + metadata)
```json
{
  "version": 1,
  "rules": [
    {
      "source_phrase": "twilight",
      "replacement": "gloaming",
      "case_policy": "match",
      "priority": 0,
      "enabled": true,
      "tags": ["synonym"],
      "created_at": "2026-01-19T23:57:10+00:00",
      "metadata": {
        "label": "Synonym",
        "description": "Common replacement",
        "examples": ["At twilight..."]
      }
    }
  ],
  "settings": {
    "inflections": {
      "enabled": true,
      "spec": {
        "forms": ["plural", "possessive"],
        "apply_to": "last_word",
        "include_original": true
      }
    },
    "learning": {
      "enabled": true,
      "show_original": true,
      "show_original_mode": "tooltip",
      "highlight_replacements": true
    }
  }
}
```

## 2) App Settings (AppSettings)

File: app-level settings JSON (stored per user).

Top-level fields
- `version` (int, optional, default: 1)
- `profiles` (array of `Profile`, optional)
- `active_profile_id` (string, optional)
- `import_export` (object, optional; `ImportExportSettings`)
- `synonyms` (object, optional; `SynonymSourceSettings`)
- `srs` (object, optional; `SrsSettings` — see `docs/srs_schema.md`)

### Profile
- `profile_id` (string, required)
- `name` (string, required)
- `dataset_path` (string, required)
- `description` (string, optional)
- `tags` (array of string, optional)
- `created_at` (string, optional)
- `updated_at` (string, optional)
- `rulesets` (array of string, optional; list of JSON file paths)
- `active_ruleset` (string, optional; path)
- `srs_profile` (object, optional; **planned**, see `docs/srs_profile_schema.md`)
- `srs_store_ref` (object, optional; **planned**, points to SRS store file)
  - Includes optional `schema_version` and metadata for future migrations.

### ImportExportSettings
- `allow_code_export` (bool, optional, default: true)
- `default_export_format` (string, optional, default: `json`)
  - Allowed: `json`, `code`
- `last_import_path` (string, optional)
- `last_export_path` (string, optional)

### SynonymSourceSettings
- `wordnet_dir` (string, optional)
- `moby_path` (string, optional)
- `max_synonyms` (int, optional, default: 30)
- `include_phrases` (bool, optional, default: false)
- `lower_case` (bool, optional, default: true)
- `require_consensus` (bool, optional, default: false)
- `use_embeddings` (bool, optional, default: false)
- `embedding_threshold` (float, optional, default: 0.0)
- `embedding_fallback` (bool, optional, default: true)
- `language_packs` (object map, optional; pack_id -> local path)
- `embedding_packs` (object map, optional; pack_id -> local path)
- `embedding_pair_paths` (object map, optional; pair_key -> list of embedding paths)
- `embedding_pair_enabled` (object map, optional; pair_key -> bool)

Example (minimal)
```json
{
  "version": 1,
  "profiles": [
    {
      "profile_id": "default",
      "name": "Default",
      "dataset_path": "/path/to/rulesets/default.json"
    }
  ],
  "active_profile_id": "default"
}
```
