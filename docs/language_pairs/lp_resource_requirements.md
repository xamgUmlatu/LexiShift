# LP Resource Requirements Matrix

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
| `en-ja` | Cross-lingual translation | `jmdict-ja-en` (`JMdict_e`) seed/baseline source; `wiktionary-ja-en.sqlite` preferred helper/runtime rulegen source when present | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | `JMdict_e`: Hard for seed/bootstrap. `wiktionary-ja-en.sqlite`: Preferred helper/runtime translation dictionary when present; `JMdict_e` fallback if absent. Frequency DB: Hard. | Same as code. Implemented mixed rollout: JMDict seed/bootstrap plus Kaikki-preferred helper/runtime rulegen; current Kaikki `en-ja` quality depends on pair-specific reading-aware gloss normalization rather than a generalized Kaikki rulegen layer, and the newer discriminative `71`-case benchmark suite now exposes unresolved reading-sensitive gaps that were not visible on the older `53`-case suite. |
| `de-en` | Cross-lingual translation | `freedict-en-de` (`eng-deu.tei`) for EN targets, DE sources | `freq-en-coca.sqlite` (current default) | `stopwords-en.json` (optional) | Frequency DB: Hard. No dictionary hard-check today. Rulegen adapter missing. | Needs `de-en` adapter + FreeDict TEI wiring for publishable rules. |
| `en-de` | Cross-lingual translation | `freedict-de-en` (`deu-eng.tei`) for DE targets, EN sources | `freq-de-default.sqlite` fallback path (placeholder, not bundled) | `stopwords-de.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). FreeDict DE->EN TEI: Hard for rulegen/publish. | Adapter implemented; still needs real German frequency DB for practical initialize/refresh. |
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
- Hard blocker for several LPs publish path: missing rulegen adapters (`de-en`, `es-es`, `en-en`, `de-de`, `ja-ja`, `en-zh`).
- Current dictionary hard requirements in code: `en-ja` seed flows remain JMDict-based while helper/runtime rulegen now uses a generic translation-dictionary slot and prefers Kaikki when installed, and FreeDict-backed pairs (`en-de`, `en-es`, `es-en`) still require their direction-specific translation dictionaries.
- Important adequacy distinction:
  - `en-es` currently has a wired bilingual source (`freedict-es-en`), but that source is not coverage-adequate for production SRS publication on its own.
  - The current failure mode is not just ranking noise; some normal admitted lemmas have no usable ES->EN headword coverage in the installed FreeDict inventory.
  - Evidence: installed-resource SRS journey leaves `movimiento` due-but-unpublished in `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`.
- Current replacement direction:
  - The active replacement plan for `en-es` is a Kaikki/Wiktionary-backed compatibility SQLite generated from Spanish entries in the English-edition Kaikki dump.
  - The active reverse-check replacement plan is a separate Kaikki/Wiktionary compatibility SQLite generated from English entries in the same English-edition dump.
  - `en-ja` now also has a Kaikki/Wiktionary compatibility SQLite path (`wiktionary-ja-en.sqlite`) that helper/runtime rulegen prefers when present, while seed initialize/refresh remains JMDict-based.
  - Current `en-ja` Kaikki quality is benchmark-clean on the current `161`-case core lane plus a separate `2`-case rare-reading edge file: `Top1 100.00%`, `Top3 100.00%`, `ForbidAny 0.00%`, triage `0` on the core lane. The lift still comes from pair-specific reading-aware gloss-fragment handling and generalized family-level English-output cleanup in the `en-ja` adapter, not from a shared multilingual Kaikki methodology yet. The broader supported sweep still prefers the lean `md=1 / mr=1 / sd=1.0` family, but `168 / 864` configs are perfect and the canonical matrix still has a wide tied frontier, so the next useful work is more discriminative benchmark expansion rather than ordinary knob churn.
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
