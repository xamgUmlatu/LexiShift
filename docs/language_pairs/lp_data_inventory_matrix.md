# LP Data Inventory Matrix (Phase 0 Baseline)

Status: Drafted for POS normalization Phase 0
Last updated: 2026-03-22

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
- POS inventory audit script: `scripts/testing/pos_inventory_audit.py`
- POS handling reference: `docs/language_pairs/pos_source_and_pipeline_reference.md`
- Licensing/distribution register: `docs/language_pairs/data_source_licensing_and_distribution.md`

Operational note:

- This inventory distinguishes `data is available and wired` from `data is adequate for current production publication quality`.
- A resource can be present in the app catalog and active in code while still being insufficient as the sole lexical source for SRS publication.

## Resource Capability Contract (Current Runtime vs Source Potential)

Use the tables below when the question is not just "what file do we have?" but:

- what fields the source actually offers
- what fields survive into the local runtime artifact
- what fields current runtime reads today
- what the resource can currently do in LexiShift
- what the source could support later without changing upstream data

Legend:

- `Current runtime uses`: behavior implemented and wired today.
- `Additional source / preserved fields`: source data that exists now but is not yet a first-class runtime input.
- `Latent capabilities`: realistic future uses enabled by the preserved or upstream fields.

### Translation Resources

| Pack / source | Native source fields | Local runtime artifact | Current runtime-consumed fields | Additional source / preserved fields | Current runtime uses | Latent capabilities |
| --- | --- | --- | --- | --- | --- | --- |
| `jmdict-ja-en` | `k_ele/keb`, `r_ele/reb`, `sense/gloss`, `sense/pos` | XML `JMdict_e` | lemmas/readings, ordered English glosses, raw POS lists where loader path exposes them | richer per-sense metadata from JMDict XML | `en-ja` seed filtering and translation rulegen | better POS-aware ranking, richer morphology/script hints |
| FreeDict TEI / FreeDict compatibility SQLite (`freedict-de-en`, `freedict-en-de`, `freedict-es-en`, `freedict-en-es`) | TEI `form/orth`, `cit type=trans / quote`, `gramGrp/pos` | TEI or normalized SQLite `entries` + `meta` | `headword`, `translation`, ordering, raw `pos` | limited converter metadata in `meta.metadata` | translation rulegen for wired FreeDict-backed pairs; reverse-check when opposite-direction pack exists | better sense filtering only if extra source metadata is introduced elsewhere |
| Kaikki/Wiktionary compatibility SQLite (`wiktionary-de-en`, `wiktionary-es-en`, `wiktionary-en-es`) | forward path: `word`, `lang`, `lang_code`, `pos`, `pos_title`, `senses[].glosses`, `senses[].raw_glosses`, `senses[].tags/topics/categories`, `forms`, `sounds`, `synonyms`, `etymology_text`; reverse path: `word`, `lang`, `lang_code`, `pos`, `pos_title`, `translations[].word`, `translations[].sense`, `translations[].tags`, `translations[].lang_code`, `forms`, `sounds`, `synonyms`, `etymology_text` | normalized SQLite `entries`, `meta`, `entry_meta`, `sense_glosses`, optional `translation_meta` | `entries.headword`, `entries.translation`, ordering, `entries.pos` | `entry_meta.pos_title`, `forms_json`, `sounds_json`, `synonyms_json`, `tags_json`, `etymology_text`; `sense_glosses.raw_glosses_json`, `tags_json`, `topics_json`, `categories_json`, `form_of_json`, `alt_of_json`; reverse path may also preserve `translation_meta.sense_text`, `english_text`, `note_text`, `roman_text`, `tags_json` | `en-de` translation rulegen path once `wiktionary-de-en.sqlite` is manually supplied or app-built; `en-es` translation rulegen path once `wiktionary-es-en.sqlite` is present; `en-es` reverse-check path once `wiktionary-en-es.sqlite` is present | synonym extraction, pronunciation surfacing, morphology-aware filtering, sense-aware ranking, qualifier/topic demotions, reverse-check based on translation-box metadata |
| `cc-cedict-zh-en` | CEDICT text rows with script forms, pinyin, gloss list | plain text dictionary file | parser-level headword + gloss extraction where used | script/pinyin data from source line format | source registered; no active `en-zh` runtime path yet | Chinese translation rulegen, script-aware lookup, pinyin-aware ranking |

### Synonym Resources

| Pack / source | Native source fields | Local runtime artifact | Current runtime-consumed fields | Additional source / preserved fields | Current runtime uses | Latent capabilities |
| --- | --- | --- | --- | --- | --- | --- |
| `wordnet-en` | synset members, lexical relations, POS partitioned JSON files | extracted JSON directory | pack presence/selection only; no active monolingual adapter yet | synset graph and relation types | none in production runtime today | `en-en` synonym rulegen, relation-aware ranking, POS-filtered monolingual generation |
| `moby-en` | headword + comma-separated related terms | plain text file | pack presence/selection only | source is relation-poor and noisy | none in production runtime today | fallback `en-en` synonym expansion |
| `odenet-de` | OMW-LMF lexical entries, synsets, relations | XML file | pack presence/selection only | lexical relation structure and possible POS metadata | none in production runtime today | `de-de` synonym rulegen, relation-aware German monolingual generation |
| `openthesaurus-de` | semicolon-separated synonym groups | plain text file | pack presence/selection only | grouped synonym sets | none in production runtime today | lightweight `de-de` synonym generation |
| `jp-wordnet-sqlite` / `jp-wordnet` | word/sense/synset structures or tab synset export | SQLite or tab file | pack presence/selection only | synset relations and some category/POS structure | none in production runtime today | `ja-ja` synonym rulegen and Japanese relation-aware monolingual generation |

### Frequency Resources

| Pack / source | Native source fields | Local runtime artifact | Current runtime-consumed fields | Additional source / preserved fields | Current runtime uses | Latent capabilities |
| --- | --- | --- | --- | --- | --- | --- |
| `freq-en-coca` | lemma/rank/frequency plus compact POS tags | SQLite `frequency` + `meta` | lemma, rank/frequency, `pos` when available | converter inventory metadata in `meta.metadata` | SRS initialize/refresh candidate pool, admission weighting, POS-aware seeding for EN-target pairs | richer corpus diagnostics and POS audits |
| `freq-ja-bccwj` | lemma/rank/frequency plus BCCWJ POS and related columns | SQLite `frequency` + `meta` | lemma, rank/frequency, `pos` | `lform`, `wtype`, `sublemma`, POS inventories | SRS initialize/refresh for JA-target pairs, POS-aware admission | richer Japanese lexical/morphology-aware selection |
| `freq-es-cde` | lemma/rank/frequency plus compact POS tags | SQLite `frequency` + `meta` | lemma, rank/frequency, `pos` | converter inventory metadata | SRS initialize/refresh for ES-target pairs, POS-aware admission | richer Spanish diagnostics and candidate shaping |
| `freq-de-default` | frequency list plus compiled DE POS lexicon joins | SQLite `frequency` + `meta` | lemma, rank/frequency, `pos` | DE-specific POS inventory metadata | SRS initialize/refresh for DE-target pairs, POS-aware admission | richer German diagnostics and lexical filtering |

### Embeddings

| Pack / source | Native source fields | Local runtime artifact | Current runtime-consumed fields | Additional source / preserved fields | Current runtime uses | Latent capabilities |
| --- | --- | --- | --- | --- | --- | --- |
| `embed-en-cc`, `embed-de-cc`, `embed-es-cc`, `embed-ja-cc` | token + dense vector rows | raw `.vec(.gz)` plus optional SQLite | vector lookup when embedding path is activated | none beyond vector space itself | optional ranking/similarity support | better pair-specific semantic reranking |
| `embed-xling-en/de/es/ja` | aligned multilingual token + vector rows | raw aligned vector file plus optional SQLite | vector lookup when activated for pair | none beyond aligned vector space | optional cross-lingual similarity support | cross-lingual ranking experiments and semantic candidate filtering |

### Stopwords

| Resource | Native source fields | Local runtime artifact | Current runtime-consumed fields | Additional source / preserved fields | Current runtime uses | Latent capabilities |
| --- | --- | --- | --- | --- | --- | --- |
| `stopwords-*.json` | JSON array of strings | JSON file | exact stopword string set | none | optional noise filtering during candidate selection / rulegen preprocessing | language-specific function-word policies and pair tuning |

## Converter POS Mapping Matrix (Phase 5)

The table below defines the POS source contract per converter/build path so new LP onboarding can wire normalization in one place.

| Converter / build path | Output packs | Raw POS source field(s) | Expected raw tag family | Normalization provider/profile | Unknown-tag inventory output |
| --- | --- | --- | --- | --- | --- |
| `scripts/data/convert_freedict_tei_to_sqlite.py` | `freedict-en-es`, `freedict-es-en`, `freedict-en-de`, `freedict-de-en` (SQLite `entries`) | TEI `gramGrp/pos` | FreeDict free-text POS labels and abbreviations (`noun`, `verb`, etc.) | provider=`freedict`, profile=`freedict`, kind=`dictionary` | `meta.metadata` keys: `rows_with_pos`, `rows_without_pos`, `pos_inventory_top`, `unknown_pos_inventory_top` |
| `scripts/data/convert_kaikki_glosses_to_sqlite.py` | `wiktionary-de-en`, `wiktionary-es-en` (SQLite `entries` + auxiliary metadata tables) | record `pos`, optional `pos_title`; gloss extraction from `senses[].glosses` / `senses[].raw_glosses` | Wiktextract/Wiktionary POS tags (`noun`, `verb`, `adj`, `adjective`, etc.) | provider=`wiktionary-<src>-en`, profile=`wiktionary`, kind=`dictionary` | converter metadata currently written to `meta.metadata`; unknown-tag inventory is runtime-visible through the POS normalization profile rather than a dedicated committed audit artifact |
| `scripts/data/convert_kaikki_translations_to_sqlite.py` | `wiktionary-en-es` (SQLite `entries` + auxiliary metadata tables) | record `pos`, optional `pos_title`; translation extraction from `translations[].word` filtered by target `lang_code` plus `translations[].sense/tags` | Wiktextract/Wiktionary POS tags (`noun`, `verb`, `intj`, `prep`, etc.) | provider=`wiktionary-en-es`, profile=`wiktionary`, kind=`dictionary` | converter metadata currently written to `meta.metadata`; reverse-specific translation metadata is preserved in `translation_meta` |

## Translation Dictionary Field Contract (Normalized SQLite)

The normalized SQLite contract below is the runtime-facing shape consumed by the current
dictionary loader and FreeDict-backed rulegen paths. A source may have richer native metadata,
but if it emits this contract it can be used by the current translation rulegen path without a
new raw-data loader.

| Artifact family | Primary runtime table(s) | Required fields | Optional / preserved fields | What current runtime can do with it | What is preserved for later use |
| --- | --- | --- | --- | --- | --- |
| FreeDict compatibility SQLite | `entries`, `meta` | `entries.headword`, `entries.headword_lc`, `entries.translation`, `entries.translation_lc`, `entries.rank`, `entries.pos`, `entries.entry_ord`, `entries.gloss_ord` | `meta.metadata` inventory and converter stats | ordered translation candidate lookup; raw POS passthrough into rulegen/POS normalization | converter inventory only; little extra lexical metadata survives today |
| Kaikki compatibility SQLite (`wiktionary-es-en`, `wiktionary-en-es`) | `entries`, `meta`, `entry_meta`, `sense_glosses`, optional `translation_meta` | same `entries.*` contract as FreeDict compatibility SQLite | `entry_meta.lang`, `entry_meta.lang_code`, `entry_meta.pos`, `entry_meta.pos_title`, `entry_meta.categories_json`, `entry_meta.forms_json`, `entry_meta.sounds_json`, `entry_meta.synonyms_json`, `entry_meta.tags_json`, `entry_meta.etymology_text`; `sense_glosses.raw_glosses_json`, `sense_glosses.tags_json`, `sense_glosses.topics_json`, `sense_glosses.categories_json`, `sense_glosses.form_of_json`, `sense_glosses.alt_of_json`; reverse path may also preserve `translation_meta.sense_text`, `english_text`, `note_text`, `roman_text`, `tags_json`, `lang_code` | same ordered translation candidate lookup and raw POS passthrough as FreeDict; current `en-es` rulegen can treat `wiktionary-es-en` as a drop-in forward dictionary and `wiktionary-en-es` as a reverse-check dictionary | forms, sounds, synonyms, sense tags/topics/categories, raw glosses, etymology, and reverse translation-box metadata are preserved for future synonym extraction and sense-aware ranking |

Operational note:

- For current `en-es` rulegen, Kaikki is intentionally exposed through the normalized `entries`
  contract first.
- Auxiliary Kaikki tables are not yet consumed by production rulegen, but they make the source’s
  additional capabilities explicit and durable.
| `scripts/data/convert_bccwj_frequency_to_sqlite.py` | `freq-ja-bccwj` | `pos` column from BCCWJ SUW TSV (`wtype` preserved separately but not used for POS mapping) | BCCWJ tags (`名詞-*`, `動詞-*`, etc.) | provider=`freq-ja-bccwj`, profile=`bccwj`, kind=`frequency` | `meta.metadata` keys: `rows_with_pos`, `rows_without_pos`, `pos_inventory_top`, `unknown_pos_inventory_top` |
| `scripts/data/convert_cde_frequency_to_sqlite.py` | `freq-es-cde` | `pos` column from CDE sample list | compact one-letter/Penn-like tags (`n`, `j`, `v`, `r`, etc.) | provider=`freq-es-cde`, profile=`freq-es-cde`, kind=`frequency` | `meta.metadata` keys: `rows_with_pos`, `rows_without_pos`, `pos_inventory_top`, `unknown_pos_inventory_top` |
| `scripts/data/convert_frequency_to_sqlite.py` + `apps/gui/src/language_packs.py` | generic frequency packs (for example `freq-en-coca`) | CLI-configurable via `--pos-column` (default `pos,wtype` when enabled); GUI path uses pack-id defaults | source-defined (compact, Penn-like, or custom) | CLI-configurable via `--pos-provider` and `--pos-profile`; GUI path maps known packs to provider/profile defaults | `meta.metadata` keys: `rows_with_pos`, `rows_without_pos`, `pos_inventory_top`, `unknown_pos_inventory_top` when POS inventory is enabled |
| `core/lexishift_core/frequency/de/build.py` | `freq-de-default` SQLite writer | DE POS lexicon tag payload attached to lemma (`pos`) | LanguageTool/Morfologik-derived tags (`SUB:*`, `VV*`, etc.) | provider=`freq-de-default`, profile=`freq-de-default`, kind=`frequency` | `meta.metadata.pos_inventory` keys: `rows_with_pos`, `rows_without_pos`, `pos_inventory_top`, `unknown_pos_inventory_top` |
| `core/lexishift_core/frequency/de/pipeline.py` | `freq-de-default` end-to-end pipeline | Delegates to `de/build.py` after POS lexicon compilation | same as above (depends on selected source: `german.dict` or `EIG+sonstige`) | same as above | prints summary counters and persists `meta.metadata.pos_inventory` |

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
| `en-de` target path (optional Kaikki experiment) | Translation dictionary | `wiktionary-de-en` | `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` | `$DATA_ROOT/language_packs/wiktionary-de-en.sqlite` | See licensing/distribution register; current policy posture remains review-required/manual-supply | Kaikki-derived compatibility SQLite. Runtime contract: `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`. Preserved auxiliary metadata: `entry_meta` and `sense_glosses` tables with forms, sounds, synonyms, sense tags/topics/categories, raw glosses, and etymology. | Raw POS from Kaikki record `pos` normalized under provider/profile `wiktionary` in current runtime. | `synonyms.language_packs["wiktionary-de-en"]` | Managed app build/download path now exists; benchmark/rulegen can consume it when manually selected or overridden, but it is not yet the default `en-de` source lane. |
| `de-en` target path | Translation dictionary | `freedict-en-de` | `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz` | `$DATA_ROOT/language_packs/eng-deu.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; direction-specific loader usage by pair. | Same POS note as above. | `synonyms.language_packs["freedict-en-de"]` | Data available; dedicated `de-en` adapter remains pending |
| `en-es` target path | Translation dictionary | `freedict-es-en` | `https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz` | `$DATA_ROOT/language_packs/spa-eng.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; used by ES rulegen adapter. | Same POS note as above. | `synonyms.language_packs["freedict-es-en"]` | Active for `en-es` rulegen, but not currently adequate as the sole production SRS publication source; installed-resource journey still leaves some admitted/due lemmas unpublished (for example `movimiento`). |
| `es-en` target path | Translation dictionary | `freedict-en-es` | `https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz` | `$DATA_ROOT/language_packs/eng-spa.tei` (or converted SQLite) | Not recorded in-repo; verify FreeDict terms | TEI XML; used by EN-target ES-source rulegen adapter. | Same POS note as above. | `synonyms.language_packs["freedict-en-es"]` | Active for `es-en` rulegen and current `en-es` reverse-check fallback; production adequacy for ES publication should not be inferred from this row alone. |
| `en-es` target path (preferred when present) | Translation dictionary | `wiktionary-es-en` | `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` | `$DATA_ROOT/language_packs/wiktionary-es-en.sqlite` | See licensing/distribution register; current policy posture remains review-required/manual-supply | Kaikki-derived compatibility SQLite. Runtime contract: `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`. Preserved auxiliary metadata: `entry_meta` and `sense_glosses` tables with forms, sounds, synonyms, sense tags/topics/categories, raw glosses, and etymology. | Raw POS from Kaikki record `pos` normalized under provider/profile `wiktionary` in current runtime. | `synonyms.language_packs["wiktionary-es-en"]` | Implemented app/runtime pipeline for `en-es`; intended to replace FreeDict fallback once a real converted artifact is generated and benchmarked in-workspace. |
| `en-es` reverse-check path (preferred when present) | Translation dictionary | `wiktionary-en-es` | `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` | `$DATA_ROOT/language_packs/wiktionary-en-es.sqlite` | See licensing/distribution register; current policy posture remains review-required/manual-supply | Kaikki-derived compatibility SQLite from English-edition translation boxes. Runtime contract stays `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`. Preserved auxiliary metadata: `entry_meta`, `sense_glosses`, and reverse-specific `translation_meta`. | Raw POS from Kaikki record `pos` normalized under provider/profile `wiktionary` in current runtime. | `synonyms.language_packs["wiktionary-en-es"]` | Implemented converter/catalog path; preferred for `en-es` reverse-check when present, but not yet promoted to the default `es-en` forward dictionary path. |
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
- Current Spanish publication caveat:
  - `freq-es-cde` is adequate for admission candidate selection.
  - `freedict-es-en` is wired for `en-es` rulegen/publication, but current installed coverage is not sufficient to guarantee that admitted/due lemmas are publishable.
  - This is a source-adequacy problem, not merely a morphology or fuzzy-lookup problem.
- Current Kaikki capability note:
  - `wiktionary-es-en` preserves fields that make future synonym and sense-aware ranking work possible, but the current production runtime only consumes its normalized `entries` contract.
