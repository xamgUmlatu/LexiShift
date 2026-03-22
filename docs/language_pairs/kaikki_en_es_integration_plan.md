# Kaikki `en-es` Integration Plan

Status: draft implementation contract
Role: working design note
Last updated: 2026-03-22
Source-of-truth: current implementation still lives in code; this note records the intended contract for the first Kaikki-backed `en-es` rollout.

## Scope

- First target:
  - Replace `freedict-es-en` as the primary dictionary resource for `en-es` rulegen.
- First non-goals:
  - Do not add synonym runtime support yet.
  - Do not add a generic multi-purpose Wiktionary runtime loader.
  - Do not switch `es-en` in the same slice unless the reverse-check path is explicitly revisited.

## Source Decision

- Use the English-edition Kaikki raw dump as the source feed.
- Do not use Spanish-edition raw data for the first `en-es` rollout.

Reasoning:

- The English-edition dump exposes Spanish entries with English glosses, which matches the current `en-es` rulegen requirement: Spanish target headword -> English source-side gloss candidates.
- This keeps the replacement semantically aligned with the current `spa-eng.tei` role, while also preserving richer Wiktionary metadata for later ranking and filtering work.

## Resource Modeling Decision

- Model the first Kaikki resource as a pair-specific translation pack in the app.
- Do not model the first rollout as a generic `multi -> multi` runtime dictionary pack.

Implementation consequence:

- App-facing pack id should be specific to the runtime use case, e.g. `wiktionary-es-en`.
- The source URL may still be a multi-language Kaikki dump, but the post-conversion artifact must be pair-specific.

## Runtime Contract Decision

- The Kaikki converter must emit the same normalized SQLite surface that current FreeDict-backed rulegen already consumes.
- Existing runtime loaders and rulegen code should continue to work against the normalized `entries` table without requiring a new raw-data code path.

Required normalized table:

- `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`
- `meta(key, value)`

Required behavior:

- Preserve ordered gloss candidates for each headword.
- Preserve raw POS in the same `pos` field used by the current FreeDict SQLite path.
- Keep the SQLite file directly consumable by current dictionary loaders.

## Metadata Preservation Decision

- Do not discard Kaikki-only metadata during conversion.
- Preserve richer metadata in auxiliary tables and/or metadata JSON, while keeping the normalized `entries` contract stable.

First-slice auxiliary metadata priorities:

- record-level language and POS
- sense glosses and raw glosses
- sense tags/topics/categories
- entry forms
- entry sounds
- entry synonyms
- etymology text

## Extraction Decision

- For the first `en-es` converter, extract Spanish headwords from English-edition records where `lang_code == "es"`.
- Build translation candidates from English glosses in `senses[].glosses`.
- Do not build the first `en-es` resource from English translation boxes pointing to Spanish words.

Reasoning:

- Using Spanish entries with English glosses matches the current FreeDict `spa-eng` orientation.
- This is the cleanest drop-in replacement for `en-es` rulegen.

## Filtering Decision

- The first converter must exclude obvious non-lemma / inflection-only sense noise from the normalized `entries` output.
- Filtering should be conservative and explicitly documented.

First-slice exclusion targets:

- `form-of`
- `alt-of`
- inflection-only glosses such as `inflection of ...`

Note:

- Richer morphology-aware handling is a later improvement; the first slice only needs to stop obvious rulegen pollution.

## Download / Conversion Decision

- The app should support Kaikki via `download + convert + auto-link`.
- The converter must accept `.jsonl.gz` directly and stream it line-by-line.
- Avoid requiring a fully expanded intermediate raw file for normal app usage.

Implementation consequence:

- This flow should behave more like the existing frequency/embedding conversion flows than the existing FreeDict `download-as-is` flow.

## POS Normalization Decision

- Kaikki/Wiktionary should get its own explicit POS source profile.
- Do not keep treating Kaikki POS as `freedict` metadata by accident.

First-slice expectation:

- Common English POS tags from Kaikki such as `noun`, `verb`, `adj`, `adjective`, `adverb` should normalize through an explicit `wiktionary`/`kaikki` profile.

## Default Resolution Decision

- For `en-es`, pair resource resolution should prefer the Kaikki-derived SQLite artifact when present.
- FreeDict should remain as a fallback path during the transition.

## Reverse Source Evaluation Decision

- For the `en-es` reverse-check dictionary, use the English-edition Kaikki dump as the canonical
  source for a dedicated `wiktionary-en-es.sqlite` artifact.
- Do not build the reverse dictionary by mechanically inverting `wiktionary-es-en.sqlite`.
- Do not use Spanish-edition Kaikki as the first canonical reverse source.

Reasoning:

- English-edition Kaikki exposes English headwords with Spanish entries in `translations[]`, plus
  English-side senses and translation tags. This is the cleanest fit for `English source candidate
  -> Spanish reverse targets`.
- Spanish-edition Kaikki does expose English translations from Spanish entries, but that would
  still force the runtime artifact to be derived from Spanish-headword records rather than native
  English-headword translation boxes.
- Spot evaluation showed English-edition records like `mother`, `until`, `hello`, and `table`
  carry usable Spanish translation rows with sense text and regional tags, while sampled
  Spanish-edition English records were primarily definition-oriented and often had empty
  `translations[]`.

Implementation consequence:

- The reverse-check path should get its own pair-specific pack id, `wiktionary-en-es`.
- The converter should emit the same normalized `entries` contract as the forward Kaikki artifact,
  while preserving reverse-specific translation metadata in auxiliary tables.

## Verification Decision

- Because this touches `en-es` rulegen resource behavior, the canonical benchmark -> quality gate -> triage loop remains required.
- Targeted tests are required for:
  - converter schema/output
  - loader compatibility
  - POS normalization
  - `en-es` regression coverage for known gaps such as `movimiento`

## Deferred Work

- synonym extraction/runtime wiring
- richer sense-risk ranking using Kaikki qualifiers/topics/register metadata
- generic multi-pair Kaikki pack generation and cataloging
