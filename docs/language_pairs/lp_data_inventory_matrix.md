# LP Data Inventory Matrix (Phase 0 Baseline)

Status: Drafted for POS normalization Phase 0  
Last updated: 2026-02-22

## Purpose

Provide one inventory table set for all active LP data resources across languages:

- frequency databases
- translation dictionaries
- monolingual synonym dictionaries
- embeddings
- stopwords

This file is intentionally explicit about unknowns. If license/POS inventory data is not
recorded in-repo, it is marked as pending verification instead of guessed.

## Source of Truth

- Pack definitions: `apps/gui/src/language_packs.py`
- LP capability defaults: `core/lexishift_core/helper/lp_capabilities.py`
- Runtime path/link resolution: `core/lexishift_core/helper/pair_resources.py`
- Frequency integrity audit script: `scripts/testing/resource_integrity_audit.py`

## Runtime Status Probe (Downloaded / Linked / Validated)

Frequency DBs are machine-state dependent and must be probed from the local data root:

```bash
python3 scripts/testing/resource_integrity_audit.py
```

Optional JSON artifact:

```bash
python3 scripts/testing/resource_integrity_audit.py \
  --json-out docs/test_outputs/resource_integrity_audit/latest.json
```

`Downloaded` / `Linked` / `Validated` for frequency DBs should be read from that report.

Phase 0 POS baseline artifact (pair-level POS distributions and examples):

- `docs/test_outputs/phase0_pos_baseline/phase0_pos_probe_2026-02-22.json`

## 1) Frequency DB Inventory

| Target language / LPs | Resource type | Pack ID | Source URL | Local filename/path convention | License status | Schema/tables/required columns | POS fields / raw-tag inventory | Settings linkage key | Integration status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| English target (`en-en`, `de-en`, `es-en`) | Frequency DB (SQLite) | `freq-en-coca` | `https://www.wordfrequency.info/samples/lemmas_60k.txt` | `$DATA_ROOT/frequency_packs/freq-en-coca.sqlite` | Not recorded in-repo; verify upstream terms before redistribution | Required table: `frequency`. Required by code: case-insensitive `lemma` + one rank column (`core_rank`/`rank`/`id`/`index`) + one frequency column (`pmw`/`frequency`/`freq`/etc). | `pos` column present in observed DB. Raw tag inventory baseline not yet captured in Phase 0 report artifacts. | `synonyms.frequency_packs["freq-en-coca"]` (runtime also accepts filename key) | Active default for EN-target SRS LPs |
| Japanese target (`en-ja`, `ja-ja`) | Frequency DB (SQLite) | `freq-ja-bccwj` | `https://repository.ninjal.ac.jp/record/3234/files/BCCWJ_frequencylist_suw_ver1_0.zip` | `$DATA_ROOT/frequency_packs/freq-ja-bccwj.sqlite` | Not recorded in-repo; verify NINJAL terms | Required table: `frequency` with same minimum column contract above. Observed schema includes `core_rank`, `core_pmw`, `pos`, `lform`, `wtype`, `sublemma`. | `pos` present; raw tag inventory exists but mapping diagnostics are not yet captured in a committed Phase 0 artifact. | `synonyms.frequency_packs["freq-ja-bccwj"]` | Active default for JA-target SRS LPs |
| German target (`en-de`, `de-de`) | Frequency DB (SQLite) | `freq-de-default` | `https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz` | `$DATA_ROOT/frequency_packs/freq-de-default.sqlite` | Not recorded in-repo; verify Leipzig + LanguageTool licensing chain | Required table: `frequency` with same minimum column contract above. Current DE pipeline writes `lemma`, `core_rank`, `pmw`, `pos` (+ `meta` table). | `pos` present. Current DE pipeline ingestion uses LanguageTool Morfologik export path and now supports `german.dict` ingestion. Full raw-tag census still pending Phase 0 POS probe artifact. | `synonyms.frequency_packs["freq-de-default"]` | Active default for DE-target LPs (quality tuning in progress) |
| Spanish target (`en-es`, `es-es`) | Frequency DB (SQLite) | `freq-es-cde` | `https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt` | `$DATA_ROOT/frequency_packs/freq-es-cde.sqlite` | Not recorded in-repo; verify upstream terms | Required table: `frequency` with same minimum column contract above. Observed schema includes `id`, `freq`, `lemma`, `pos`. | `pos` present. ES raw tag mapping table is defined in POS workstream design; baseline unmapped-tag report still pending artifact capture. | `synonyms.frequency_packs["freq-es-cde"]` | Active default for ES-target LPs |
| Chinese target (`en-zh`) | Frequency DB (SQLite, planned placeholder) | `freq-zh-default` | TBD | `$DATA_ROOT/frequency_packs/freq-zh-default.sqlite` | TBD | Expected to follow same `frequency` table minimum contract. | POS source not selected yet. | `synonyms.frequency_packs["freq-zh-default"]` (convention) | Not active; LP not currently SRS-selectable |

## 2) Translation Dictionary Inventory

| LP direction(s) | Resource type | Pack ID | Source URL | Local filename/path convention | License status | Schema/required fields | POS fields / raw-tag inventory | Settings linkage key | Integration status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `en-ja` (JA source -> EN gloss) | Translation dictionary | `jmdict-ja-en` | `https://www.edrdg.org/pub/Nihongo/JMdict_e.gz` | `$DATA_ROOT/language_packs/JMdict_e` | Not recorded in-repo; verify EDRDG terms | XML entries; used for seed/rulegen filtering and gloss extraction. | POS-like category data exists in JMDict entries, but not yet normalized as canonical POS in current runtime. | `synonyms.language_packs["jmdict-ja-en"]` | Hard requirement for `en-ja` seed + rulegen |
| `en-de` target path | Translation dictionary | `freedict-de-en` | `https://download.freedict.org/dictionaries/deu-eng/1.9-fd1/freedict-deu-eng-1.9-fd1.src.tar.xz` | `$DATA_ROOT/language_packs/deu-eng.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; headword + translations parsed by converter/loader. | FreeDict TEI carries POS-like metadata in grammar fields, but default loaders currently prioritize gloss mapping; POS wiring remains partial. | `synonyms.language_packs["freedict-de-en"]` | Required for DE/ES FreeDict-backed rulegen paths depending on pair |
| `de-en` target path | Translation dictionary | `freedict-en-de` | `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz` | `$DATA_ROOT/language_packs/eng-deu.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; direction-specific loader usage by pair. | Same POS note as above. | `synonyms.language_packs["freedict-en-de"]` | Data available; dedicated `de-en` adapter remains pending |
| `en-es` target path | Translation dictionary | `freedict-es-en` | `https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz` | `$DATA_ROOT/language_packs/spa-eng.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; used by ES rulegen adapter. | Same POS note as above. | `synonyms.language_packs["freedict-es-en"]` | Active for `en-es` rulegen |
| `es-en` target path | Translation dictionary | `freedict-en-es` | `https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz` | `$DATA_ROOT/language_packs/eng-spa.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; used by EN-target ES-source rulegen adapter. | Same POS note as above. | `synonyms.language_packs["freedict-en-es"]` | Active for `es-en` rulegen |
| `en-zh` target path | Translation dictionary | `cc-cedict-zh-en` | `https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip` | `$DATA_ROOT/language_packs/cedict_ts.u8` | Not recorded in-repo; verify CC-CEDICT terms | Plain text dictionary entries; parser support exists, LP path not fully active. | No canonical POS mapping currently wired for this source. | `synonyms.language_packs["cc-cedict-zh-en"]` | Data source registered; `en-zh` pipeline not active |

## 3) Monolingual Synonym Dictionary Inventory

| Language | Resource type | Pack ID | Source URL | Local filename/path convention | License status | Schema/required fields | POS fields / raw-tag inventory | Settings linkage key | Integration status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| English | Synonym dictionary | `wordnet-en` | `https://en-word.net/static/english-wordnet-2025-json.zip` | `$DATA_ROOT/language_packs/english-wordnet-2025-json/` | Not recorded in-repo; verify WordNet terms | JSON synset files; validated by marker files in GUI validator. | POS is implicit in synset file families; no canonical POS normalization layer yet. | `synonyms.language_packs["wordnet-en"]` | Data available; monolingual `en-en` adapter path still pending |
| English | Synonym dictionary | `moby-en` | `https://dn790001.ca.archive.org/0/items/mobythesauruslis03202gut/mthesaur.txt` | `$DATA_ROOT/language_packs/mthesaur.txt` | Not recorded in-repo; verify source terms | Delimited text rows (`headword,synonym,...`). | No reliable POS structure in source. | `synonyms.language_packs["moby-en"]` | Data available; monolingual `en-en` adapter path still pending |
| German | Synonym dictionary | `odenet-de` | `https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/refs/heads/master/odenet_oneline.xml` | `$DATA_ROOT/language_packs/odenet_oneline.xml` | Not recorded in-repo; verify upstream terms | OMW-LMF XML parsing for lemma/synset relationships. | POS metadata may exist in source structures but is not currently part of normalized POS pipeline output. | `synonyms.language_packs["odenet-de"]` | Data available; monolingual `de-de` adapter path pending |
| German | Synonym dictionary | `openthesaurus-de` | `https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/openthesaurus.txt?inline=false` | `$DATA_ROOT/language_packs/openthesaurus.txt` | Not recorded in-repo; verify OpenThesaurus terms | Semicolon-separated synonym groups. | No canonical POS fields in current parse path. | `synonyms.language_packs["openthesaurus-de"]` | Optional DE source; adapter path pending |
| Japanese | Synonym dictionary | `jp-wordnet-sqlite` | `https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz` | `$DATA_ROOT/language_packs/wnjpn.db` | Not recorded in-repo; verify NTT/bond-lab terms | SQLite tables (`word`, `sense`, etc.) | POS/category information exists in source relations; no canonical POS normalization output yet. | `synonyms.language_packs["jp-wordnet-sqlite"]` | Data available; monolingual `ja-ja` adapter path pending |
| Japanese | Synonym dictionary | `jp-wordnet` | `https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz` | `$DATA_ROOT/language_packs/wnjpn-all.tab` | Not recorded in-repo; verify NTT/bond-lab terms | Tabular synset export. | POS handling is source-dependent and not normalized in current pipeline. | `synonyms.language_packs["jp-wordnet"]` | Legacy optional variant |

## 4) Embedding Inventory

| Pair scope | Resource type | Pack ID | Source URL | Local filename/path convention | License status | Schema/required fields | POS fields | Settings linkage key(s) | Integration status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EN monolingual similarity | Embedding | `embed-en-cc` | `https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.vec.gz` | raw: `$DATA_ROOT/embeddings/cc.en.300.vec.gz`, optimized: `.sqlite` sibling | Not recorded in-repo; verify fastText terms | Vector text converted to SQLite by `scripts/data/convert_embeddings.py` | N/A | `synonyms.embedding_packs["embed-en-cc"]`, pair activation via `embedding_pair_paths` | Optional ranking enhancement |
| DE monolingual similarity | Embedding | `embed-de-cc` | `https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.de.300.vec.gz` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model | Optional ranking enhancement |
| JA monolingual similarity | Embedding | `embed-ja-cc` | `https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.vec.gz` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model | Optional ranking enhancement |
| ES monolingual similarity | Embedding | `embed-es-cc` | `https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.es.300.vec.gz` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model | Optional ranking enhancement |
| EN aligned cross-lingual | Embedding | `embed-xling-en` | `https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.en.align.vec` | raw: `$DATA_ROOT/embeddings/wiki.en.align.vec`, optional optimized SQLite sibling | Not recorded in-repo; verify fastText terms | Same conversion path if optimized | N/A | Same linkage model + pair activation | Optional cross-lingual ranking |
| DE aligned cross-lingual | Embedding | `embed-xling-de` | `https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.de.align.vec` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model + pair activation | Optional cross-lingual ranking |
| JA aligned cross-lingual | Embedding | `embed-xling-ja` | `https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.ja.align.vec` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model + pair activation | Optional cross-lingual ranking |
| ES aligned cross-lingual | Embedding | `embed-xling-es` | `https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.es.align.vec` | Same convention | Not recorded in-repo; verify fastText terms | Same | N/A | Same linkage model + pair activation | Optional cross-lingual ranking |

## 5) Stopwords Inventory

| Target language | Resource type | Logical name | Source URL | Local filename/path convention | License status | Schema/required fields | POS/raw-tag status | Linkage model | Integration status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| German | Stopwords JSON | `stopwords-de.json` | Internal default seed (helper-generated) | Search order: `$DATA_ROOT/srs/stopwords-de.json`, `$DATA_ROOT/srs/stopwords/stopwords-de.json`, `$DATA_ROOT/stopwords/stopwords-de.json`, `$DATA_ROOT/language_packs/stopwords-de.json` | Project-local data | JSON array of non-empty strings | N/A | Resolved by path search (not settings-linked) | Default seeded by helper path bootstrap |
| English | Stopwords JSON | `stopwords-en.json` | TBD / user-provided | Same search order pattern | TBD | JSON array of non-empty strings | N/A | Path search | Optional; not seeded by default |
| Japanese | Stopwords JSON | `stopwords-ja.json` | TBD / user-provided | Same search order pattern | TBD | JSON array of non-empty strings | N/A | Path search | Optional; not seeded by default |
| Spanish | Stopwords JSON | `stopwords-es.json` | TBD / user-provided | Same search order pattern | TBD | JSON array of non-empty strings | N/A | Path search | Optional; currently usually missing |
| Chinese | Stopwords JSON | `stopwords-zh.json` | TBD / user-provided | Same search order pattern | TBD | JSON array of non-empty strings | N/A | Path search | Optional; LP not active |

## Phase 0 Coverage Notes

- Frequency integrity/linkage checks now have a reproducible CLI probe:
  `scripts/testing/resource_integrity_audit.py`.
- This inventory now centralizes data-resource metadata and integration ownership.
- Remaining Phase 0 work is POS distribution artifact generation and representative
  behavior snapshots (see `docs/rulegen/pos_normalization_workstream.md`).
