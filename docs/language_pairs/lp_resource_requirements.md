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
| `en-ja` | Cross-lingual translation | `jmdict-ja-en` (`JMdict_e`) | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | `JMdict_e`: Hard for seed + rulegen. Frequency DB: Hard. | Same as code. JMDict is the auto-download rulegen/semantic locator source; BCCWJ is the quality-preferred target-frequency source but remains manual-supply/review-required for bundled or hosted derivatives. |
| `de-en` | Cross-lingual translation | `freedict-en-de` (`eng-deu.tei`) for EN targets, DE sources | `freq-en-leipzig-default` managed SQLite first; legacy/manual `freq-en-coca.sqlite` fallback | `stopwords-en.json` for target-side seed filtering (optional); German source-side stopword filtering is pair-local rulegen behavior | Frequency DB: Hard. FreeDict EN->DE TEI: Hard for rulegen/publish. | Adapter implemented baseline path; benchmark seeding and pair-specific quality tuning still needed. |
| `en-de` | Cross-lingual translation | `freedict-de-en` (`deu-eng.tei` / managed `freedict-de-en/main.sqlite`) for DE targets, EN sources; reverse `freedict-en-de` for reverse-check experiments; optional experimental `wiktionary-de-en` compatibility SQLite when manually supplied or app-built | `freq-de-default` managed SQLite (`frequency_packs/freq-de-default/main.sqlite`) plus legacy flat `freq-de-default.sqlite` fallback | `stopwords-de.json` (optional fallback seeded by helper path bootstrap) | Frequency DB: Hard. FreeDict DE->EN: Hard for current baseline rulegen/publish. Reverse FreeDict is needed only for reverse-check lanes. | Runtime/SRS beta implemented and installed smoke passed; source stack is wired. Rulegen quality remains advisory/failing against the old top1 floor, so source-family promotion/hard-gated parity remains pending. |
| `en-es` | Cross-lingual translation | `wiktionary-es-en` primary; `freedict-es-en` (`spa-eng.tei`) fallback for ES targets, EN sources | `freq-es-spalex-v1.sqlite` / managed `freq-es-spalex-v1/main.sqlite` | `stopwords-es.json` (optional, currently missing) | Frequency DB: Hard. Wiktionary ES->EN SQLite: Hard for current production rulegen/publish path; FreeDict fallback remains useful but not sufficient alone. | SPALEX is the product/default admission source. `freq-es-cde` is retired from runtime fallback and should be kept only as a historical/manual benchmark artifact. |
| `es-en` | Cross-lingual translation | `freedict-en-es` (`eng-spa.tei`) for EN targets, ES sources | `freq-en-leipzig-default` managed SQLite first; legacy/manual `freq-en-coca.sqlite` fallback | `stopwords-en.json` (optional) | Frequency DB: Hard. FreeDict EN->ES TEI/SQLite: Hard for rulegen/publish. | Adapter implemented baseline path. |
| `es-es` | Monolingual synonyms | Spanish monolingual source TBD (for example ES WordNet/OpenThesaurus-like source) | `freq-es-spalex-v1.sqlite` / managed `freq-es-spalex-v1/main.sqlite` | `stopwords-es.json` (optional, currently missing) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual ES adapter + source selection. |
| `en-en` | Monolingual synonyms | `wordnet-en`, `moby-en` | `freq-en-leipzig-default` managed SQLite first; legacy/manual `freq-en-coca.sqlite` fallback | `stopwords-en.json` (optional) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual EN adapter using WordNet/Moby sources. |
| `de-de` | Monolingual synonyms | `odenet-de`, `openthesaurus-de` | `freq-de-default` managed SQLite plus legacy flat fallback | `stopwords-de.json` (optional fallback seeded by helper path bootstrap) | Frequency DB: Hard. Rulegen adapter missing. | German frequency is no longer the main blocker in the current source-stack model; this pair still needs a monolingual DE adapter, source ranking policy, and quality evidence. |
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

- Hard blocker for several LPs: missing real target-language frequency DB still
  applies to ZH. DE target frequency is now represented by `freq-de-default`;
  remaining German-target blockers are pair-specific quality/adapters rather
  than basic frequency availability.
- Hard blocker for several LPs publish path: missing rulegen adapters (`es-es`, `en-en`, `de-de`, `ja-ja`, `en-zh`).
- Current dictionary hard requirements in code: `en-ja` (JMDict) and FreeDict-backed pairs (`de-en`, `en-de`, `en-es`, `es-en`).
- Important adequacy distinction:
  - `en-es` currently has a wired bilingual source (`freedict-es-en`), but that source is not coverage-adequate for production SRS publication on its own.
  - The current failure mode is not just ranking noise; some normal admitted lemmas have no usable ES->EN headword coverage in the installed FreeDict inventory.
  - Evidence: installed-resource SRS journey leaves `movimiento` due-but-unpublished in `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`.
- Future Spanish SRS-corpus expansion:
  - `freq-es-spalex-v1` is the current product/default Spanish frequency source and is built in `spalex_only` mode.
  - `freq-es-cde` is no longer a runtime fallback. Treat it as a frozen historical/manual benchmark only.
  - Future research should verify POS/rank quality on SPALEX plus license-safe overlays and re-run SRS admission/rulegen/semantic-veto denominator reports before expanding paid evidence generation beyond the current corpus.
- Current replacement direction:
  - The active replacement plan for `en-es` is a Kaikki/Wiktionary-backed compatibility SQLite generated from Spanish entries in the English-edition Kaikki dump.
  - The active reverse-check replacement plan is a separate Kaikki/Wiktionary compatibility SQLite generated from English entries in the same English-edition dump.
  - See `docs/language_pairs/kaikki_en_es_integration_plan.md`.

## 6) German Frequency DB Build (Current Recommendation)

- Managed pipeline: `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/frequency/de/pipeline.py`
- CLI compatibility wrapper: `/Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_pipeline.py`
- Legacy one-shot builder: `/Users/takeyayuki/Documents/projects/LexiShift/scripts/build/de_frequency_sqlite.py`
- Managed target artifact: `$DATA_ROOT/frequency_packs/freq-de-default/main.sqlite`
- Legacy fallback filename still accepted by helper/runtime:
  `$DATA_ROOT/frequency_packs/freq-de-default.sqlite`
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
- Frequency DB: managed `freq-es-spalex-v1/main.sqlite` or legacy-flat `freq-es-spalex-v1.sqlite`
- Translation DBs: `wiktionary-es-en.sqlite` / `wiktionary-en-es.sqlite` primary, with `freedict-es-en.sqlite` / `freedict-en-es.sqlite` fallback

Build SPALEX Spanish frequency SQLite:

```bash
python3 /Users/takeyayuki/Documents/projects/LexiShift/scripts/data/build_spalex_frequency_pack_en_es.py \
  --spalex-csv /path/to/word_info.csv \
  --pack-root "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-spalex-v1" \
  --overwrite \
  --write-sidecars
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
