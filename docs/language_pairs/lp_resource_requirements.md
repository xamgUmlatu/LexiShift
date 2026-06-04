# LP Resource Requirements Matrix

Status: active mixed requirements matrix
Role: Mixed
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 language-pair authority note; LP requirement claims not fully re-audited
Source-of-truth: mixed LP requirements matrix; current implementation truth lives in LP capability/resource code, rulegen/SRS code, tests, and regenerated resource/POS audits.

Purpose:
- List all known LPs (Language Pairs).
- Separate resource classes (translation dictionary, synonym dictionary, frequency DB, stopwords).
- Mark what is required for each SRS stage.
- Distinguish `required by current code` vs `logically required for complete SRS E2E`.
- Distinguish `resource exists / is wired` from `resource is coverage-adequate for production publication`.

Related:
- `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/lp_capabilities.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/architecture/srs_lp_architecture.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/extension_lp_generalization_checklist.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/language_packs.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/lp_data_inventory_matrix.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/data_source_licensing_and_distribution.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/pos_source_and_pipeline_reference.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/kaikki_en_es_integration_plan.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/resource_integrity_audit.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/pos_inventory_audit.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/resource_recovery_playbook.md`

## 1) Resource Classes and What They Are For

- Translation dictionary:
  - Purpose: rule generation for cross-lingual LPs (build `source_phrase -> replacement` candidates).
  - Examples: JMDict, FreeDict, CC-CEDICT.
- Synonym dictionary:
  - Purpose: rule generation for monolingual LPs.
  - Examples: WordNet/Moby (EN), OdeNet/OpenThesaurus (DE), JP WordNet (JA).
- Frequency DB (SQLite):
  - Purpose: SRS initialize/refresh candidate pool (`top_n`, weighting, admission).
  - Examples: `freq-ja-bccwj.sqlite`, `freq-en-coca.sqlite`.
- Stopwords file (JSON array, optional):
  - Purpose: remove noisy high-frequency function words during candidate selection.
  - Examples: `stopwords-ja.json`, `stopwords-en.json`.
- SRS store/signal/status (JSON):
  - Purpose: scheduler state and events at runtime.
  - Not a dictionary/frequency source.

## 2) Stage-Level Requirement Rules

- `srs_initialize`:
  - Frequency DB: hard required by current code.
  - Dictionary validation gate: pair-specific (`require_jmdict` currently only true for `en-ja`).
- `srs_refresh`:
  - Frequency DB: hard required by current code.
  - Dictionary validation gate: same pair-specific rule as initialize.
- `rulegen publish` (`run_rulegen_for_pair`):
  - Requires pair adapter support.
  - Dictionary inputs are adapter-specific.
  - Current implemented adapters: `en-ja`, `en-de`, `en-es`, `es-en`.
- Scheduler/feedback/exposure:
  - No dictionary/frequency file requirement after items exist in `S`.

## 3) LP Matrix (Current Code vs Logical E2E)

Legend:
- `Hard (code)`: enforced by current helper/core code.
- `Logical E2E`: required to make that LP produce meaningful SRS rules end-to-end.
- `Optional`: beneficial but not required by current enforcement.
- `Coverage-adequate`: sufficient lexical coverage for the current SRS publish step, not just present/wired in code.

| LP | Rulegen type | Dictionary source(s) | Frequency DB for SRS init/refresh | Stopwords | Required by current code | Logical E2E requirement |
| --- | --- | --- | --- | --- | --- | --- |
| `en-ja` | Cross-lingual translation | `jmdict-ja-en` (`JMdict_e`) | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | `JMdict_e`: Hard for seed + rulegen. Frequency DB: Hard. | Same as code. Implemented baseline path. |
| `de-en` | Cross-lingual translation | `freedict-en-de` (`eng-deu.tei`) for EN targets, DE sources | `freq-en-coca.sqlite` (current default) | `stopwords-en.json` for target-side seed filtering (optional); German source-side stopword filtering is pair-local rulegen behavior | Frequency DB: Hard. FreeDict EN->DE TEI: Hard for rulegen/publish. | Adapter implemented baseline path; benchmark seeding and pair-specific quality tuning still needed. |
| `en-de` | Cross-lingual translation | `freedict-de-en` (`deu-eng.tei`) for DE targets, EN sources; optional experimental `wiktionary-de-en` compatibility SQLite when manually supplied or app-built | `freq-de-default.sqlite` fallback path (placeholder, not bundled) | `stopwords-de.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). FreeDict DE->EN TEI: Hard for current baseline rulegen/publish. | Adapter implemented; Kaikki/Wiktionary DE->EN build path now exists, but the canonical lane still needs real German frequency DB and benchmark evidence before any source-family promotion. |
| `en-es` | Cross-lingual translation | `freedict-es-en` (`spa-eng.tei`) for ES targets, EN sources | `freq-es-cde.sqlite` | `stopwords-es.json` (optional, currently missing) | Frequency DB: Hard. FreeDict ES->EN TEI/SQLite: Hard for rulegen/publish. | Adapter implemented and wired, but current FreeDict ES->EN coverage is not adequate as the sole production SRS publication source; installed-resource journey still shows admitted/due words such as `movimiento` with no publishable rule. |
| `es-en` | Cross-lingual translation | `freedict-en-es` (`eng-spa.tei`) for EN targets, ES sources | `freq-en-coca.sqlite` | `stopwords-en.json` (optional) | Frequency DB: Hard. FreeDict EN->ES TEI/SQLite: Hard for rulegen/publish. | Adapter implemented baseline path. |
| `es-es` | Monolingual synonyms | Spanish monolingual source TBD (for example ES WordNet/OpenThesaurus-like source) | `freq-es-cde.sqlite` | `stopwords-es.json` (optional, currently missing) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual ES adapter + source selection. |
| `en-en` | Monolingual synonyms | `wordnet-en`, `moby-en` | `freq-en-coca.sqlite` | `stopwords-en.json` (optional) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual EN adapter using WordNet/Moby sources. |
| `de-de` | Monolingual synonyms | `odenet-de`, `openthesaurus-de` | `freq-de-default.sqlite` fallback path (placeholder) | `stopwords-de.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). Rulegen adapter missing. | Needs German frequency DB + monolingual DE adapter. |
| `ja-ja` | Monolingual synonyms | `jp-wordnet-sqlite` or `jp-wordnet` | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual JA adapter (JP WordNet source). |
| `en-zh` | Cross-lingual translation | `cc-cedict-zh-en` (`cedict_ts.u8`) | `freq-zh-default.sqlite` fallback path (placeholder) | `stopwords-zh.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). Rulegen adapter missing. | Needs Chinese frequency DB + `en-zh` adapter. |

## 4) FreeDict Direction Clarification (`en-de` / `de-en` / `en-es` / `es-en`)

- `freedict-de-en` (`deu-eng.tei`):
  - Headwords are German, translations are English.
  - Useful when targets are German and sources are English (LP `en-de` rule orientation).
- `freedict-en-de` (`eng-deu.tei`):
  - Headwords are English, translations are German.
  - Useful when targets are English and sources are German (LP `de-en` rule orientation).

Both files are TEI dictionaries; they support opposite directional rulegen needs.

- `freedict-es-en` (`spa-eng.tei`):
  - Headwords are Spanish, translations are English.
  - Useful when targets are Spanish and sources are English (LP `en-es` rule orientation).
- `freedict-en-es` (`eng-spa.tei`):
  - Headwords are English, translations are Spanish.
  - Useful when targets are English and sources are Spanish (LP `es-en` rule orientation).

## 5) Current Gaps Summary

- Hard blocker for several LPs: missing real target-language frequency DB (DE, ZH).
- Hard blocker for several LPs publish path: missing rulegen adapters (`es-es`, `en-en`, `de-de`, `ja-ja`, `en-zh`).
- Current dictionary hard requirements in code: `en-ja` (JMDict) and FreeDict-backed pairs (`en-de`, `en-es`, `es-en`).
- Important adequacy distinction:
  - `en-es` currently has a wired bilingual source (`freedict-es-en`), but that source is not coverage-adequate for production SRS publication on its own.
  - The current failure mode is not just ranking noise; some normal admitted lemmas have no usable ES->EN headword coverage in the installed FreeDict inventory.
  - Evidence: installed-resource SRS journey leaves `movimiento` due-but-unpublished in `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`.
- Future Spanish SRS-corpus expansion:
  - The current `freq-es-cde` pack is a sample-sized Spanish frequency resource; observed local metadata contains `2,000` rows and produces `1,984` unique Spanish SRS target lemmas after dedupe in the current semantic-veto bridge.
  - Treat that as a current installed-resource boundary, not as a final `en-es` product corpus cap.
  - Future research should identify a broader licensing-safe Spanish frequency source or pack strategy, verify POS/rank quality, and re-run SRS admission/rulegen/semantic-veto denominator reports before expanding paid evidence generation beyond the current corpus.
- Current replacement direction:
  - The active replacement plan for `en-es` is a Kaikki/Wiktionary-backed compatibility SQLite generated from Spanish entries in the English-edition Kaikki dump.
  - The active reverse-check replacement plan is a separate Kaikki/Wiktionary compatibility SQLite generated from English entries in the same English-edition dump.
  - See `docs/language_pairs/kaikki_en_es_integration_plan.md`.

## 6) German Frequency DB Build (Current Recommendation)

- Builder script: `/Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py`
- Target filename for current fallback wiring: `freq-de-default.sqlite`
- Input format expected by script: Leipzig words list (`id<TAB>surface<TAB>count`)
- Lemmatized build requires `simplemma` (`pip install simplemma`)
- Default filtering now includes:
  - hapax removal via `--min-lemma-count` (default `2`)
  - DE lexical whitelist from discovered language packs (`deu-eng.tei`, `odenet_oneline.xml`, `openthesaurus.txt`)
  - non-whitelist retention threshold via `--whitelist-min-count` (default `20`)
- Optional POS enrichment/filtering:
  - `--pos-lexicon` with delimiter controls and explicit lemma/POS column indexes
  - `--drop-proper-nouns` to exclude proper nouns when POS tags are present
  - supports raw `german-pos-dict` rows (`surface<TAB>lemma<TAB>tag [--comment]`) via `--pos-format german_pos_dict`
  - for repeat runs, use compact precompiled format (`lemma<TAB>tag1|tag2|...`) via `--pos-format generic_compact`

Example:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py \
  --input /Users/takeyayuki/Documents/deu_news_2023_1M/deu_news_2023_1M-words.txt \
  --output "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-de-default.sqlite" \
  --overwrite
```

Example with POS lexicon:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py \
  --input /Users/takeyayuki/Documents/deu_news_2023_1M/deu_news_2023_1M-words.txt \
  --output "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-de-default.sqlite" \
  --pos-lexicon /path/to/german-pos-dict.tsv \
  --pos-delimiter tab \
  --pos-lemma-col 0 \
  --pos-tag-col 1 \
  --drop-proper-nouns \
  --overwrite
```

Example with your german-pos-dict path (raw):

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py \
  --input /Users/takeyayuki/Documents/deu_news_2023_1M/deu_news_2023_1M-words.txt \
  --output "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-de-default.sqlite" \
  --pos-lexicon /Users/takeyayuki/Documents/projects/german-pos-dict/german-pos-dict.txt \
  --pos-format german_pos_dict \
  --drop-proper-nouns \
  --overwrite
```

Optional precompile for faster future runs:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_pos_lexicon.py \
  --input /Users/takeyayuki/Documents/projects/german-pos-dict/german-pos-dict.txt \
  --output "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/de-pos-compact.tsv" \
  --overwrite
```

Then use:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py \
  --input /Users/takeyayuki/Documents/deu_news_2023_1M/deu_news_2023_1M-words.txt \
  --output "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-de-default.sqlite" \
  --pos-lexicon "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/de-pos-compact.tsv" \
  --pos-format generic_compact \
  --drop-proper-nouns \
  --overwrite
```

Single-command pipeline (recommended for app button wiring):

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_pipeline.py \
  --input /Users/takeyayuki/Documents/deu_news_2023_1M/deu_news_2023_1M-words.txt \
  --pos-raw /Users/takeyayuki/Documents/projects/german-pos-dict/german-pos-dict.txt \
  --drop-proper-nouns \
  --overwrite
```

## 7) Spanish Resource Conversion Quickstart

Expected outputs:
- Frequency DB: `freq-es-cde.sqlite`
- Translation DBs: `freedict-es-en.sqlite`, `freedict-en-es.sqlite`

Convert Corpus del Espanol sample frequency text to SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/convert_cde_frequency_to_sqlite.py \
  /path/to/spanish_lemmas20k.txt \
  "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-cde.sqlite" \
  --overwrite
```

Convert FreeDict ES->EN archive/tei to SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/convert_freedict_spa_eng_to_sqlite.py \
  /path/to/freedict-spa-eng-0.3.1.src.tar.xz \
  "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/freedict-es-en.sqlite" \
  --overwrite
```

Convert FreeDict EN->ES archive/tei to SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/convert_freedict_eng_spa_to_sqlite.py \
  /path/to/freedict-eng-spa-2025.11.23.src.tar.xz \
  "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/freedict-en-es.sqlite" \
  --overwrite
```

Convert Kaikki English-edition raw dump to the `en-es` compatibility SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/convert_kaikki_es_en_to_sqlite.py \
  /path/to/raw-wiktextract-data.jsonl.gz \
  "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-es-en.sqlite" \
  --overwrite
```

Convert Kaikki English-edition raw dump to the `en-es` reverse-check compatibility SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/convert_kaikki_en_es_to_sqlite.py \
  /path/to/raw-wiktextract-data.jsonl.gz \
  "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-en-es.sqlite" \
  --overwrite
```
