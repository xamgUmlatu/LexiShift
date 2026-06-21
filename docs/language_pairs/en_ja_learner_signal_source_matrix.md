# en-ja Learner Signal Source Matrix

Status: active source audit
Last updated: 2026-06-16
Purpose: track learner-difficulty and admission-suitability signal sources for
`en-ja` without mixing product-ready source lanes with unclear research inputs.

## Policy

Prioritize product lanes:

- `auto-download`: the LexiShift app may fetch the source directly, show source
  and license notices, and build user-local derived artifacts.
- `manual-local`: the app may guide the user to the upstream source and import a
  user-supplied local file.

Use `research-needed` only when a source looks useful but provenance,
redistribution, or transitive license obligations are not clear enough for
product ingestion. Do not use `research-needed` as a normal staging state for
sources that are already legal and technically ready to wire.

## Current Source Lanes

| Source | Product lane | Current use | Signal candidates | Notes |
| --- | --- | --- | --- | --- |
| Internal Japanese script analyzer | built-in | Deterministic learner-signal enrichment. | script shape, kanji/kana/digit/latin counts, mixed-script flag, script-complexity proxy | No external license surface; useful as a weak supporting signal, not a primary difficulty source. |
| JMDict | `auto-download` | Installed language pack for `en-ja` rulegen/seed filtering. | priority tags (`news`, `ichi`, `spec`, `gai`, `nfxx`), entry/form priority, POS/misc/field lexical cues, dialect labels, source-language labels, kanji/reading info labels, sense/reading restrictions, no-kanji flags, cross-reference/antonym counts, sense/gloss counts, gloss languages | Priority and lexical extraction are source signals; final difficulty formula is still open. Chinese/Sinitic source markers are separated from other loanword-source markers. |
| KANJIDIC2 | `auto-download` | Optional learner-signal enrichment. | kanji school grade, old JLPT kanji level, stroke count, kanji frequency rank, on/kun/nanori readings, English meaning count/sample, radical values/names, variant types, query-code types, dictionary-reference depth | Added as `kanjidic2-ja`; absence must not block `en-ja`. |
| JMnedict/ENAMDICT | `auto-download` | Optional proper-name signal enrichment. | name type groups, person/place/organization/product/work-name cues | Added as `jmnedict-ja`; useful for admission/name demotion and topic gating, not as a primary difficulty source. |
| KanjiVG | `auto-download` | Optional visual/component enrichment. | path count, group count, nesting depth, component count/sample, radical/position/part attributes, phonetic-component hints, variant count, visual-complexity proxy | Added as `kanjivg-ja`; useful for compositionality and visual-complexity experiments, not a primary difficulty source. |
| Tanos JLPT Vocabulary via Bluskyo CSV | `auto-download` | Optional learner-level enrichment. | JLPT vocabulary level, projected difficulty proxy, beginner-core proxy | Added as `jlpt-tanos-vocab-ja`; useful as an outside pedagogical signal, but not yet adopted in the production formula. |
| Step-by-Step Japanese 1 Pressbooks EPUB | `auto-download` | Optional beginner lesson-order enrichment. | earliest vocabulary lesson/module, lesson title, romanization, English gloss, projected low-band difficulty proxy, beginner-core proxy | Added as `sbsjapanese1-ja`; useful for beginner-core and low-band ordering experiments, but not yet adopted in the production formula. |
| BCCWJ SUW frequency list | `manual-local` | Quality-preferred `en-ja` frequency/POS source. | corpus rank, pmw, BCCWJ POS, lform, wtype, sublemma, compact profile over rank/pmw/frequency subcorpus columns, domain-rank spread/coverage, fixed-vs-variable rank delta | Keep manual/local unless policy review approves bundled/hosted converted artifacts. Raw subcorpus columns are reduced to compact metadata, not copied wholesale into seed caches. |
| UniDic CWJ | `auto-download candidate` | Not wired. | morphology, lemma identity, POS, conjugation/detail fields | License appears product-friendly via GPL/LGPL/New BSD triple-license posture, but parser and size policy are pending. |
| SudachiDict | `auto-download candidate` | Not wired. | morphology, normalized forms, named-entity cues | Apache-2.0 headline license, but transitive source notices should be verified before product wiring. |
| Tatoeba sentences | `auto-download candidate` | Not wired. | example/context QA, sentence evidence, not primary difficulty | Useful for tests and examples; weak direct learner-difficulty signal. |

## Deferred Or Research-Needed Inputs

| Source type | Current lane | Reason |
| --- | --- | --- |
| Community JLPT vocabulary lists | `research-needed` | Pedagogically useful, but common public lists often have unclear source provenance or redistribution rights. |
| Anki/Kaggle/GitHub vocabulary decks | `research-needed` | Dataset license may not cover the underlying word-list provenance. |
| Jisho/JPDB/WaniKani-style level tags | `research-needed` | Product terms/API/bulk-use rights need explicit verification. |
| Textbook vocabulary lists | `research-needed` | Likely high pedagogical value, but copyright/licensing varies by publisher/list. |

## Pedagogical Commonness Signal Gap

The residual-gate audit in
`docs/test_outputs/srs_learner_difficulty_residual_gate_audit_en_ja_latest.md`
shows that current source-backed gates are not precise enough to isolate the
remaining learner-difficulty failures. The clearest gaps are:

- easy or transparent learner words pushed too high by rarity or written form;
- common/ordinary kango that need a midrange floor without lifting already-high
  formal rows;
- rare or literary wago/readings that need upper-tail pressure without moving
  core native words.

Treat new sources in this area as a search for a word-level pedagogical
commonness or learner-order signal. Promising source categories are:

- cleanly redistributable JLPT vocabulary or learner-level lists;
- textbook, graded-reader, or learner-dictionary headword lists when
  provenance and product rights are explicit;
- manual-local lists if the upstream terms allow user-directed import but not
  redistribution;
- generated or human-reviewed labels for test coverage, with a separate policy
  decision before treating them as shipped product data.

Before wiring any new source into `learner_difficulty`, run the residual-gate
audit against its derived signal and require holdout evidence that it improves
cluster separability without regressing non-cluster rows.

## Initial Pedagogical Source Search, 2026-06-16

This search focuses on sources that may provide a word-level learner-order,
lesson-order, or pedagogical-commonness signal. "Reference-only" means we can
inspect it qualitatively or use it to design reviewed tests, but should not
scrape, bundle, or compile it into product artifacts without a separate policy
decision.

| Source | Observed license/posture | Candidate lane | Signal value | Current recommendation |
| --- | --- | --- | --- | --- |
| Jonathan Waller / Tanos JLPT Resources (`https://www.tanos.co.uk/jlpt/`) | Explicit "Use my data" page says non-sold site data is Creative Commons BY with attribution. | `auto-download candidate` | JLPT-style N5-N1 learner-level tags for vocabulary and kanji. | Highest-value first prototype. Ingest directly from upstream where possible, preserve attribution, and treat levels as unofficial/old but useful. |
| Bluskyo `JLPT_Vocabulary` (`https://github.com/Bluskyo/JLPT_Vocabulary`) | Repository is MIT; README says data comes from Tanos under CC BY. | `auto-download candidate` or tooling reference | Structured JSON/CSV conversion of Tanos JLPT vocab/kanji. | Useful implementation shortcut or parser reference. Product notices should still cite Tanos/CC BY as the data source. |
| `stephenmk/yomitan-jlpt-vocab` (`https://github.com/stephenmk/yomitan-jlpt-vocab`) | Repository license is CC BY-SA 4.0; README says JLPT data comes from Tanos and adds JMdict entry mapping/common spelling normalization. | `reference` / `manual-local candidate` | JLPT tags mapped to JMdict entries and normalized spellings. | Valuable comparison source and mapping reference. Avoid silent ingestion until CC BY-SA/share-alike implications are accepted for this derived dictionary. |
| Wiktionary JLPT appendices and Japanese basic-word appendices (`https://en.wiktionary.org/wiki/Appendix:JLPT`, `https://en.wiktionary.org/wiki/Appendix:1000_Japanese_basic_words`) | Wiktionary text is CC BY-SA 4.0 unless otherwise noted. | `reference` / possible `auto-download candidate` if share-alike accepted | Cross-check JLPT tags, basic-core vocabulary, and category-based beginner staples. | Good consensus/reference source. Use first for validation and calibration; product ingestion needs CC BY-SA policy clarity. |
| Step-by-Step Japanese 1 (`https://utsa.pressbooks.pub/sbsjapanese1/`) | Pressbooks footer says CC BY 4.0 except where otherwise noted. | `auto-download candidate` | Lesson/module-ordered beginner vocabulary; gives clear first-course ordering. | Strong product-compatible beginner-core source. Prototype as a low-band pedagogical signal after checking all chapters for exceptions. |
| Beginning Japanese for Professionals (`https://pdx.pressbooks.pub/beginningjapanese1/`) | CC BY-NC 4.0 except where otherwise noted. | `reference-only` unless product is clearly noncommercial | Beginner work/life vocabulary by lesson/dialogue. | Useful qualitative/reference source for beginner professional/living vocabulary. Do not ingest into commercial product artifacts without permission. |
| Japanese I + II Workbook (`https://utexas.pressbooks.pub/japaneseiworkbook/`) | CC BY-NC 4.0 except where otherwise noted. | `reference-only` unless product is clearly noncommercial | Beginner topic/lesson vocabulary and kanji order. | Useful for test design and sanity checks. Avoid product ingestion under current commercial-uncertain posture. |
| Irodori: Japanese for Life in Japan (`https://www.irodori.jpf.go.jp/en/`) | Official site offers downloadable word lists, but footer says all rights reserved. | `reference-only` / permission-needed | Practical A1-A2/B1 life-in-Japan vocabulary and lesson order. | High pedagogical value, but do not ingest or redistribute without explicit permission. |
| Kaishi 1.5k (`https://github.com/donkuri/Kaishi`) | No repository license found; README says it was built from Core/Tango decks plus other sources. | `reference-only` | Community-vetted beginner ordering, especially first 1500 words. | Useful qualitative sanity check only. Do not ingest or compile because license/provenance is unclear. |
| Kanshudo/Routledge/iKnow/JapanesePod101-style lists | Proprietary or unclear for bulk/product reuse in the initial search. | `reference-only` / reject for product ingestion | Usefulness, frequency, or course-order signals. | Do not ingest. Can inform human discussion if viewed manually, but should not drive generated product data. |

Near-term priority:

1. Prototype Tanos/JLPT level tags as the first outside pedagogical source.
2. Add Step-by-Step Japanese lesson-order extraction as a clean CC BY
   beginner-core signal.
3. Use Wiktionary and `yomitan-jlpt-vocab` as consensus/reference checks before
   deciding whether CC BY-SA-derived data belongs in the product source stack.
4. Keep Irodori, Kaishi, and commercial learner platforms out of compiled
   product artifacts unless permission or license posture changes.

## Sweep Readiness

The first formula-sweep-ready signal set should use only already-wired product
lanes:

1. BCCWJ frequency/POS fields.
2. Internal Japanese script-shape fields.
3. JMDict priority tags plus POS/misc/field/source/restriction/form lexical groups.
4. KANJIDIC2 kanji-level, radical, variant, reading, and reference aggregate fields.
5. JMnedict proper-name signal fields.
6. KanjiVG visual/component/position/radical/phonetic aggregate fields.
7. Tanos/JLPT vocabulary-level aggregate fields.
8. Step-by-Step Japanese 1 lesson-order/gloss/romanization aggregate fields.
9. Existing reviewed exact learner-difficulty overlay.
10. Existing candidate-state/admission-suitability classifier.

Formula sweeps should report both correctness and behavior metrics:

- calibration label accuracy for reviewed rows;
- monotonicity of sampled average learner difficulty across proficiency bands;
- high-proficiency hard-tail reach without non-vocab leakage;
- beginner-core retention for reviewed beginner staples;
- false admit/false suppress counts for `normal_vocab` decisions;
- signal coverage rates for script-shape, BCCWJ subcorpus profile, JMDict priority/lexical, KANJIDIC2, JMnedict, KanjiVG, JLPT vocabulary, and lesson-vocabulary fields.

## Implementation Update, 2026-06-16

The first two outside pedagogical sources are now wired as optional product
signals:

- `jlpt-tanos-vocab-ja` downloads the Bluskyo structured CSV derived from
  Jonathan Waller/Tanos JLPT vocabulary data and exposes
  `jlpt_vocabulary` metadata in seed candidates.
- `sbsjapanese1-ja` downloads the Step-by-Step Japanese 1 Pressbooks EPUB as
  `sbsjapanese1.zip`, extracts it through the existing ZIP path, and exposes
  `lesson_vocabulary` metadata in seed candidates.

Both are declared in the en-ja source stack, GUI catalog, third-party notices,
and seed-cache invalidation path. They remain opt-in research signals for
formula sweeps; no production learner-difficulty formula has been changed to
consume them yet.

## Signal Expansion Update, 2026-06-16

The installed-source audit found useful fields already present in the current
product lanes, so the signal bundle now exposes them without changing the
accepted production scorer:

- JMDict lexical records now capture dialect, source-language, kanji-form,
  reading-form, sense-restriction, reading-restriction, no-kanji-reading,
  cross-reference, sense-count, gloss-count, and compact English gloss-value
  signals. Chinese/Sinitic source labels are separated from other
  loanword-source labels because common kango words can carry Chinese etymology
  without behaving like modern loanwords.
- KANJIDIC2 aggregates now include nanori count, meaning count, radical
  values/names, variant types, query-code types, and dictionary-reference type
  depth.
- KanjiVG aggregates now include radical/position/part attributes, phonetic
  component hints, and variant count alongside the existing visual-complexity
  proxy.
- Step-by-Step Japanese 1 lesson records now preserve romanization, English
  gloss, and lesson title in addition to lesson order.
- BCCWJ seed rows now preserve a compact `source_frequency_profile` over
  subcorpus rank/pmw/frequency columns. This exposes rank coverage, spread, and
  fixed-vs-variable deltas for sweeps while avoiding raw-column cache bloat.
- Acronym/code rows now expose `ja_acronym` metadata derived from NFKC script
  shape, BCCWJ/JMDict/JMnedict reading evidence, exact/expanded JMDict English
  gloss evidence, JMDict domain fields, JMnedict proper-name signals, and the
  BCCWJ source-frequency profile. The first audit found 548 acronym/code signal
  rows in 78,434 en-ja seed candidates: 207 `shared_exact_acronym`, 184
  `domain_acronym`, 93 `proper_name_acronym`, 4 `japanese_specific_acronym`,
  and 60 `unknown_acronym_like` rows. `domain_acronym` now requires JMDict
  domain-field evidence; BCCWJ distribution skew remains a supporting audit and
  sweep signal, not a standalone semantic-domain label.

These fields are available to `srs_learner_difficulty_signal_sweep_en_ja.py`,
tree search, and model-family/meta searches as opt-in components. They are
research inputs until calibration/holdout evidence justifies consuming any of
them in the production learner-difficulty formula. The acronym audit is
behavior-neutral; it does not yet change candidate classification or runtime
admission behavior.
