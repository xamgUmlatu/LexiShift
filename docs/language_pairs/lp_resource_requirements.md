# LP Resource Requirements Matrix

Purpose:
- List all known LPs (Language Pairs).
- Separate resource classes (translation dictionary, synonym dictionary, frequency DB, stopwords).
- Mark what is required for each SRS stage.
- Distinguish `required by current code` vs `logically required for complete SRS E2E`.

Related:
- `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/lp_capabilities.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/architecture/srs_lp_architecture.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/extension_lp_generalization_checklist.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/language_packs.py`

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
  - Current implemented adapters: `en-ja`, `en-de`.
- Scheduler/feedback/exposure:
  - No dictionary/frequency file requirement after items exist in `S`.

## 3) LP Matrix (Current Code vs Logical E2E)

Legend:
- `Hard (code)`: enforced by current helper/core code.
- `Logical E2E`: required to make that LP produce meaningful SRS rules end-to-end.
- `Optional`: beneficial but not required by current enforcement.

| LP | Rulegen type | Dictionary source(s) | Frequency DB for SRS init/refresh | Stopwords | Required by current code | Logical E2E requirement |
| --- | --- | --- | --- | --- | --- | --- |
| `en-ja` | Cross-lingual translation | `jmdict-ja-en` (`JMdict_e`) | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | `JMdict_e`: Hard for seed + rulegen. Frequency DB: Hard. | Same as code. Implemented baseline path. |
| `de-en` | Cross-lingual translation | `freedict-en-de` (`eng-deu.tei`) for EN targets, DE sources | `freq-en-coca.sqlite` (current default) | `stopwords-en.json` (optional) | Frequency DB: Hard. No dictionary hard-check today. Rulegen adapter missing. | Needs `de-en` adapter + FreeDict TEI wiring for publishable rules. |
| `en-de` | Cross-lingual translation | `freedict-de-en` (`deu-eng.tei`) for DE targets, EN sources | `freq-de-default.sqlite` fallback path (placeholder, not bundled) | `stopwords-de.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). FreeDict DE->EN TEI: Hard for rulegen/publish. | Adapter implemented; still needs real German frequency DB for practical initialize/refresh. |
| `en-en` | Monolingual synonyms | `wordnet-en`, `moby-en` | `freq-en-coca.sqlite` | `stopwords-en.json` (optional) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual EN adapter using WordNet/Moby sources. |
| `de-de` | Monolingual synonyms | `odenet-de`, `openthesaurus-de` | `freq-de-default.sqlite` fallback path (placeholder) | `stopwords-de.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). Rulegen adapter missing. | Needs German frequency DB + monolingual DE adapter. |
| `ja-ja` | Monolingual synonyms | `jp-wordnet-sqlite` or `jp-wordnet` | `freq-ja-bccwj.sqlite` | `stopwords-ja.json` (optional) | Frequency DB: Hard. Rulegen adapter missing. | Needs monolingual JA adapter (JP WordNet source). |
| `en-zh` | Cross-lingual translation | `cc-cedict-zh-en` (`cedict_ts.u8`) | `freq-zh-default.sqlite` fallback path (placeholder) | `stopwords-zh.json` (optional, currently missing) | Frequency DB: Hard (will fail if missing). Rulegen adapter missing. | Needs Chinese frequency DB + `en-zh` adapter. |

## 4) FreeDict Direction Clarification (`en-de` vs `de-en`)

- `freedict-de-en` (`deu-eng.tei`):
  - Headwords are German, translations are English.
  - Useful when targets are German and sources are English (LP `en-de` rule orientation).
- `freedict-en-de` (`eng-deu.tei`):
  - Headwords are English, translations are German.
  - Useful when targets are English and sources are German (LP `de-en` rule orientation).

Both files are TEI dictionaries; they support opposite directional rulegen needs.

## 5) Current Gaps Summary

- Hard blocker for several LPs: missing real target-language frequency DB (DE, ZH).
- Hard blocker for several LPs publish path: missing rulegen adapters (`de-en`, `en-en`, `de-de`, `ja-ja`, `en-zh`).
- Current dictionary hard requirements in code: `en-ja` (JMDict), `en-de` (FreeDict DE->EN TEI).

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
