# en-ja JLPT GitHub Source Audit

Status: source audit for learner-difficulty research, no runtime behavior changed
Recorded: 2026-06-22 JST

## Purpose

Audit GitHub-hosted JLPT/learner-list candidates for the simpler next path:
repair current JLPT coverage and exact mapping before adding a larger consensus
or fundamentally JLPT-primary model.

The main question is not whether another repository is "the official JLPT
list". Official vocabulary lists are not published for the current JLPT. The
question is whether a repository provides product-usable, reproducible evidence
that can improve our exact surface/reading/JMdict mapping or upper-bound useful
learner vocabulary.

## Repositories Inspected

Local audit clone root:

`/tmp/lexishift-jlpt-source-audit`

| Source | Repo | Commit audited | License observed | Provenance observed | Initial decision |
| --- | --- | --- | --- | --- | --- |
| Bluskyo JLPT Vocabulary | `https://github.com/Bluskyo/JLPT_Vocabulary` | `6c94c2c2835133e8d005202dee8e075470bea73c` | MIT repo; README says data from Tanos/Jonathan Waller is Creative Commons BY | Tanos-derived vocabulary and kanji CSV/JSON. Current product source lane already uses this family. | Keep as primary product-ingested JLPT vocab source. |
| stephenmk Yomitan JLPT vocab | `https://github.com/stephenmk/yomichan-jlpt-vocab` | `b062d4e38c4bdd0950ae1d4ec55f04b176182e03` | CC BY-SA 4.0 | Tanos-derived, with added JMdict sequence IDs and common-spelling normalization from JMdict inspection. | Best mapping-repair reference; do not silently ingest product data until CC BY-SA implications are accepted. |
| Open Anki JLPT decks | `https://github.com/jamsinclair/open-anki-jlpt-decks` | `1ad66734417aca9dbcca6b2d5ee440cb13ab3ba0` | MIT | Original deck data from `chyyran/jlpt-anki-decks`, based on Tanos; community-editable CSV decks. | Useful comparison/reference, not independent truth. |
| elzup JLPT word list | `https://github.com/elzup/jlpt-word-list` | `13aa3c54b27115be72d8a62cd4071077c68d2171` | MIT | Forked from Open Anki JLPT decks; original deck data ultimately Tanos-derived. | Low incremental value beyond Open Anki; useful only as normalized CSV comparison. |
| AnchorI JLPT kanji dictionary | `https://github.com/AnchorI/jlpt-kanji-dictionary` | `6dc7e6d3d4d5778b27f7f57a770cc5a350b7889c` | MIT | README claims JLPT kanji/vocabulary data, but source/provenance for data is not stated. Vocabulary dictionary has no per-word JLPT level. | Do not use for JLPT vocab upper bounds. Maybe reference-only for kanji-level comparison, but we already have KANJIDIC2 old JLPT kanji. |

## Data Shape And Counts

Counts are from local cloned files, parsed with Python CSV/JSON readers.

### Bluskyo

File:

`data/vocab/results/JLPT_vocab_ALL.csv`

Columns: `Kanji`, `Reading`, `Level`.

| Metric | Count |
| --- | ---: |
| Rows | 8,505 |
| Unique surface+reading pairs | 8,430 |
| Duplicate pairs | 74 |
| Multi-level pairs | 70 |

Level row counts:

| Level | Rows |
| --- | ---: |
| N1 | 3,475 |
| N2 | 1,846 |
| N3 | 1,835 |
| N4 | 649 |
| N5 | 700 |

This remains the cleanest product-ingested baseline: level plus reading, with
known Tanos/CC BY provenance and readable CSV/JSON.

### stephenmk Yomitan JLPT vocab

Files:

- `original_data/n1.csv` ... `original_data/n5.csv`
- `yomitan-jlpt-vocab/term_meta_bank_*.json`

Original CSV columns include `jmdict_seq`, `kana`, `kanji`,
`waller_definition`.

| Metric | Original CSV | Yomitan normalized |
| --- | ---: | ---: |
| Rows | 8,293 | 8,113 |
| Unique surface+reading pairs | 8,289 | 8,113 |
| Rows with non-empty JMdict sequence | 8,279 | n/a |
| Unique JMdict sequences | 7,747 | n/a |

Overlap with Bluskyo after using kana as surface for kana-only original rows:

| View | Overlap with Bluskyo | Only in stephenmk | Only in Bluskyo |
| --- | ---: | ---: | ---: |
| Original CSV | 8,175 | 114 | 255 |
| Yomitan normalized | 7,691 | 422 | 739 |

Interpretation:

- This is not an independent JLPT source. It is explicitly Tanos-derived.
- It is still the strongest option-1 source because it adds JMdict sequence IDs
  and intentionally repairs rare spellings such as Waller forms into more common
  JMdict spellings.
- CC BY-SA 4.0 makes direct product ingestion risky unless we accept
  share-alike obligations. Use first as a reference to improve our own
  JMDict-backed matching algorithm, not as a silent compiled dependency.

### Open Anki JLPT decks

Files:

`src/n1.csv` ... `src/n5.csv`

Columns: `expression`, `reading`, `meaning`, `tags`, `guid`.

| Metric | Count |
| --- | ---: |
| Rows | 8,131 |
| Unique surface+reading pairs | 8,034 |
| Multi-level pairs | 15 |

Level row counts:

| Level | Rows |
| --- | ---: |
| N1 | 2,951 |
| N2 | 3,567 |
| N3 | 402 |
| N4 | 675 |
| N5 | 536 |

Overlap with Bluskyo:

| Metric | Count |
| --- | ---: |
| Overlap | 7,124 |
| Only in Open Anki | 910 |
| Only in Bluskyo | 1,306 |

Interpretation:

- MIT repo, but the README says original deck data came from another JLPT Anki
  deck based on Tanos.
- Useful for finding community edits/missing rows, but not a clean independent
  learner signal.
- Some rows are deck-oriented strings rather than clean dictionary entries,
  such as parenthetical patterns and semicolon-separated alternatives; do not
  ingest without normalization.

### elzup JLPT word list

Files:

- `out/all.csv`
- `out/all.min.csv`
- `src/n1.csv` ... `src/n5.csv`

Columns in `out/all.csv`: `expression`, `reading`, `meaning`, `tags`.

| Metric | Count |
| --- | ---: |
| Rows | 7,972 |
| Unique surface+reading pairs | 7,972 |
| Multi-level pairs | 0 |

Level row counts:

| Level | Rows |
| --- | ---: |
| N1 | 2,951 |
| N2 | 3,409 |
| N3 | 401 |
| N4 | 675 |
| N5 | 536 |

Overlap with Bluskyo:

| Metric | Count |
| --- | ---: |
| Overlap | 7,094 |
| Only in elzup | 878 |
| Only in Bluskyo | 1,336 |

Interpretation:

- MIT repo, but README states it is forked from Open Anki and ultimately
  Tanos-derived.
- It is mostly a normalized/downstream Open Anki view.
- Lower value than Open Anki for source repair because it does not add JMdict
  IDs or clearly stronger normalization.

### AnchorI JLPT Kanji Dictionary

Files:

- `jlpt-kanji.json`
- `dictionary_part_1.json` ... `dictionary_part_4.json`

Kanji counts:

| JLPT | Kanji rows |
| --- | ---: |
| N1 | 1,135 |
| N2 | 380 |
| N3 | 370 |
| N4 | 170 |
| N5 | 80 |
| Missing | 1 |

Vocabulary dictionary counts:

| Metric | Count |
| --- | ---: |
| Vocab rows | 220,885 |
| Unique surface+reading pairs | 220,016 |
| Per-word JLPT level present | no |

Interpretation:

- MIT repo, but data provenance is not stated clearly enough for product source
  ingestion.
- The vocabulary dictionary is not a JLPT vocabulary-level source; it has
  `kanji`, `reading`, `pos`, glosses, and `sequence`, but no JLPT word level.
- Not useful for the current "easyish word upper bound" goal. It may overlap
  with existing kanji-level signals, but KANJIDIC2 already provides better
  provenance for old JLPT kanji-level information.

## Relation To Current LexiShift Matrix

Current regenerated source-arbitration component matrix:

`docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz`

Observed JLPT coverage in that matrix:

| Signal | Present / nonzero rows |
| --- | ---: |
| `jlpt_vocab_known` | 7,527 |
| `jlpt_vocab_surface_known` | 7,527 |
| `jlpt_vocab_reading_known` | 7,154 |
| `jlpt_vocab_exact_known` | 6,788 |
| `jlpt_vocab_difficulty` | 7,527 |
| `jlpt_vocab_exact_difficulty` | 6,788 |

Default curve counts in matrix:

| Level | Broad rows | Exact rows |
| --- | ---: | ---: |
| N5 | 615 | 474 |
| N4 | 562 | 487 |
| N3 | 1,725 | 1,525 |
| N2 | 1,536 | 1,428 |
| N1 | 3,089 | 2,874 |

This means the product problem is not only source availability. We already have
thousands of JLPT-like rows. The more immediate problem is exact mapping:

- broad JLPT evidence exists for 7,527 rows;
- exact surface+reading evidence exists for 6,788 rows;
- broad-minus-exact gap is 739 rows;
- exact matching is precisely where rare reading and same-surface pollution can
  distort rankings.

## Recommendation

Prefer option 1: coverage and mapping repair.

Do not start by adding every GitHub list as a consensus score. Most audited
vocabulary sources are Tanos-derived and therefore not independent. Instead:

1. Keep Bluskyo/Tanos as the primary product-ingested JLPT source.
2. Use stephenmk as a reference source for JMdict sequence mapping and spelling
   normalization.
3. Compare our Bluskyo importer against stephenmk original CSV sequence IDs and
   normalized Yomitan rows.
4. Repair our own exact JLPT matching by using already-approved JMDict data and
   explicit surface+reading logic.
5. Rebuild the component matrix and measure:
   - `jlpt_vocab_exact_known` gain;
   - broad-minus-exact shrinkage;
   - changes in same-surface rare-reading samples;
   - first-60 acceptance pack texture.

Only after that should we consider adding a second product-ingested source. Open
Anki and elzup are useful comparison sets, but they do not add enough
independent evidence to justify a more complex consensus model yet.

## Practical Model Implication

The safest source-driven model improvement is an exact learner-source upper
bound:

```text
if exact surface+reading learner source exists:
  use the level as a strong upper-bound anchor

if only surface-family learner source exists:
  use it weakly, or only when rare-reading/same-surface pollution risk is low

if no learner source exists:
  do not punish; fall back to current source-arbitration ranking
```

This directly supports the app goal: known learner-stage vocabulary should not
drift into the tail just because frequency, kanji burden, or domain labels are
noisy. It also avoids the dangerous inverse assumption that absence from a JLPT
list means the word is hard.
