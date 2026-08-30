# en-ja Acronym Admission And Difficulty Signal Plan

Status: implementation plan; signal extraction/audit and seed classification
bridge implemented, runtime scalar difficulty pending
Last updated: 2026-06-17
Owner area: SRS admission, learner difficulty, en-ja source-signal extraction
Related docs:
- `docs/srs/srs_learner_difficulty_model_workplan.md`
- `docs/language_pairs/en_ja_learner_signal_source_matrix.md`

## Purpose

Define a source-backed implementation path for acronym-like Japanese target
rows in en-ja SRS admission and learner-difficulty tuning.

The immediate trigger is the q15/q20 tail review. The aggressive q20 tail
candidate promoted many full-width Latin rows such as `ＶＲ`, `ＳＩ`, `ＷＡＶ`,
`ＴＯＥＩＣ`, `ＲＣ`, `ＰＶ`, `ＰＤＦ`, `ＭＲＩ`, `ＭＲＳＡ`, and `ＳＮＳ`.
Those rows are not all the same product case:

- some are exact or near-exact English carryovers with low SRS value;
- some are useful Japanese-context vocabulary;
- some are domain-specific abbreviations that should be topic-scoped;
- some are proper-name or organization rows;
- some are source artifacts or weak standalone cards.

The goal is not to make "acronym" mean "hard." It is to classify acronym-like
rows before scalar difficulty scoring so they do not pollute the upper tail.

## Implementation Update, 2026-06-17

The first two phases are implemented, and seed classification now consumes the
source-backed recommendation:

- `core/lexishift_core/resources/japanese_learner_signals.py` emits a structured
  `learner_signals["ja_acronym"]` payload when source-backed acronym/code
  evidence is present.
- `core/lexishift_core/srs/seed.py` passes BCCWJ reading/POS/word-type metadata
  and the compact `source_frequency_profile` into learner-signal extraction.
- `core/lexishift_core/srs/candidate_classification.py` applies
  `ja_acronym.recommended_candidate_state` to seed classification by default,
  with `SeedSelectionConfig.apply_learner_signal_classification` available as
  an experiment/off switch.
- `scripts/testing/srs_ja_acronym_signal_audit_en_ja.py` writes the current
  corpus audit to `docs/test_outputs/srs_ja_acronym_signal_audit_latest.json`
  and `docs/test_outputs/srs_ja_acronym_signal_audit_latest.md`.
- `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py` exposes
  acronym components for sweeps and future model comparisons.

Current audit snapshot:

| Metric | Value |
| --- | ---: |
| Seed candidates | `78,434` |
| Acronym/code signal rows | `548` |
| Signal rate | `0.006987` |
| `shared_exact_acronym` | `207` |
| `domain_acronym` | `184` |
| `proper_name_acronym` | `93` |
| `japanese_specific_acronym` | `4` |
| `unknown_acronym_like` | `60` |

The standalone audit still reports `runtime_behavior_changed: false` because it
only inspects signal extraction. Seed classification/admission state now changes
when the signal recommends `suppressed_default`, `topic_only`,
`deprioritized_vocab`, or `normal_vocab`; runtime scalar difficulty still does
not directly use acronym/classification fields.

The current audit also records source-evidence flags:

| Evidence flag | Count |
| --- | ---: |
| `has_exact_identity` | `435` |
| `has_initialism_expansion` | `389` |
| `has_jmdict_domain_field` | `208` |
| `has_proper_name_signal` | `93` |
| `domain_from_distribution_only` | `252` |

`expanded_gloss_confidence` now means a real English initialism expansion: the
acronym letters must match English gloss initials after stopword filtering.
`domain_from_distribution_only` is intentionally audit-only. BCCWJ distribution
skew can support sweeps and triage, but it does not by itself classify a row as
`domain_acronym`.

## Current Code Hooks

Current code already has the shape needed for this:

- `core/lexishift_core/srs/candidate_classification.py`
  - candidate states: `normal_vocab`, `deprioritized_vocab`, `pattern_item`,
    `grammar_item`, `topic_only`, `suppressed_default`;
  - problem classes for numerals, grammar, proper nouns, symbol-like rows, and
    acronym/code rows;
  - applies source-backed `ja_acronym` recommendations unless disabled in seed
    selection config.
- `core/lexishift_core/resources/japanese_learner_signals.py`
  - builds the en-ja learner-signal bundle from script shape, JMDict, JMnedict,
    KANJIDIC2, KanjiVG, JLPT vocab, and lesson vocabulary;
  - now emits `ja_acronym` from NFKC script shape, reading spell-out evidence,
    exact/expanded English-gloss evidence, domain fields, proper-name signals,
    and source-frequency profile metadata.
- `core/lexishift_core/srs/seed.py`
  - preserves learner signals and BCCWJ `source_frequency_profile`;
  - preserves BCCWJ `lemma`, `lform`, `pos`, `sublemma`, and `wtype` in seed
    rows and word packages;
  - passes learner signals into candidate classification by default.
- `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py`
  - consumes the learner-signal bundle and source-frequency profile;
  - now exposes acronym-specific components for research sweeps.

The current implementation path is:

1. Add an acronym/code detector and source-backed signal payload. Done.
2. Use that payload in candidate classification and admission suitability. Done.
3. Expose sweep components for research, but do not rely on the sweep alone to
   discover that exact carryover acronyms are weak SRS cards.
4. Add fixtures and review artifacts around known acronym categories. In
   progress.
5. Decide whether runtime learner-difficulty estimation should apply separate
   scalar adjustments for classification fields, or keep that behavior inside
   admission state/topic gating.

## Source Analysis

### Internal Script Shape

Available now, no external license surface:

- Unicode normalization can convert full-width Latin/digit forms to ASCII for
  analysis while preserving display surface.
- Current script signal already counts Latin, digit, kana, kanji, and other
  characters.
- Missing signal: acronym/code confidence after NFKC normalization.

Proposed derived fields:

- `normalized_ascii_surface`: NFKC-normalized ASCII-like surface, for metadata
  only;
- `latin_upper_ratio`: share of Latin letters that are uppercase;
- `latin_or_digit_ratio`: share of surface made from Latin/digit chars;
- `acronym_surface_confidence`: high for 2-8 uppercase Latin letters, optionally
  mixed with digits or hyphen separators;
- `mixed_code_confidence`: high for forms such as `3D`, `B型`, `X線`,
  `CD-ROM`, where acronym handling may need separate policy;
- `all_latin_surface`: true when the normalized surface is only Latin letters
  plus allowed separators;
- `fullwidth_source_surface`: true when original surface used full-width ASCII.

Important counter-case: full-width Latin is common in Japanese corpora and does
not by itself mean junk. It means "route through acronym/code policy."

### Reading Spell-Out Signal

Available from BCCWJ `lform`, seed `reading`, and JMDict/JMnedict readings.

A robust detector should compare the reading against Japanese letter-name
sequences. Examples:

| Surface | Reading | Interpretation |
| --- | --- | --- |
| `ＰＤＦ` | `ピーディーエフ` | English-letter spell-out. |
| `ＶＲ` | `ブイアール` | English-letter spell-out. |
| `ＳＮＳ` | `エスエヌエス` | English-letter spell-out, but common Japanese term. |
| `ＴＯＥＩＣ` | `トーイック` | Acronym-like but lexicalized, not pure letter spell-out. |
| `ＮＧ` | `エヌジー` | English-letter spell-out, Japanese-specific usage. |

Proposed fields:

- `reading_spellout_confidence`: exact or near-exact match to letter-name
  sequence;
- `lexicalized_acronym_reading`: true when the reading is not a simple letter
  sequence, for example `ＴＯＥＩＣ` as `トーイック`;
- `reading_source`: `bccwj_lform`, `jmdict_reb`, `jmnedict_reb`, or seed
  fallback.

This is a high-value guard against treating alphabetic surfaces as ordinary
loanwords.

### JMDict

Primary reference: EDRDG JMdict DTD (`https://www.edrdg.org/jmdict/jmdict_dtd_h.html`).

Relevant fields already parsed in
`core/lexishift_core/resources/japanese_learner_signals.py`:

- `k_ele/keb`, including exceptional letters from other alphabets;
- `r_ele/reb`, `re_inf`, `re_pri`;
- `ke_pri` / `re_pri`, including `spec`, `gai`, and `nf` priority tags;
- `sense/pos`, `sense/field`, `sense/misc`, `sense/lsource`,
  `sense/gloss`, `sense/xref`, `sense/s_inf`;
- `stagk` / `stagr` and reading restrictions.

Local examples confirm useful distinctions:

- `ＣＭ` has JMDict `spec1` priority and glosses around radio/TV commercials.
  It is useful Japanese vocabulary, but not upper-tail difficulty.
- `ＳＮＳ` has an `internet` field and glosses "social networking service",
  "SNS", and "social media." It is a Japanese-context tech term, not junk.
- `ＮＧ` has colloquial misc metadata and glosses such as "no good" and
  "not allowed." It is not an exact English identity card.
- `ＰＤＦ`, `ＵＳＢ`, `ＭＲＩ`, and `ＡＩ` have exact acronym glosses, which
  strongly indicates English carryover/domain handling rather than normal
  vocabulary difficulty.

Proposed derived fields:

- `jmdict_abbreviation_misc`: true when JMDict misc contains abbreviation;
- `jmdict_field_values`: already preserved; use for domain/topic mapping;
- `jmdict_exact_acronym_gloss`: true when a gloss exactly equals the normalized
  acronym surface, case-insensitive;
- `jmdict_expanded_english_gloss`: true when a gloss is a phrase expansion;
- `jmdict_japanese_specific_gloss`: heuristic for glosses such as "office
  lady", "commercial message", "no good", or social-service terms whose
  Japanese usage is not a simple source-word identity;
- `jmdict_priority_commonness`: reuse existing priority score, but treat it as
  commonness/value, not hardness.

JMDict alone should not decide suppression. It can prove that a term is real,
common, domain-tagged, or exact-carryover-like.

### BCCWJ

Primary reference: NINJAL BCCWJ word-list page
(`https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html`).

The installed `freq-ja-bccwj` SQLite pack currently preserves:

- `lemma`, `lform`, `pos`, `sublemma`, `wtype`;
- global `rank`, `frequency`, `pmw`;
- `core_rank`, `core_frequency`, `core_pmw`;
- domain/subcorpus rank, frequency, and PMW columns;
- fixed/variable sample split columns.

Local rows show useful evidence:

| Lemma | POS | wType | Rank | Signal implication |
| --- | --- | --- | ---: | --- |
| `ＣＭ` | `名詞-普通名詞-一般` | `記号` | `3265` | Common real Japanese acronym; should not be hard just because it is Latin. |
| `ＤＶＤ` | `名詞-普通名詞-一般` | `記号` | `1944` | Common exact/shared acronym; low learning value as a replacement target. |
| `ＮＧ` | `名詞-普通名詞-一般` | `記号` | `10307` | Japanese-specific usage; valid, moderate learner target. |
| `ＮＨＫ` | `名詞-固有名詞-一般` | `固` | `2899` | Proper organization acronym; usually deprioritize or topic-scope. |
| `ＭＲＳＡ` | `名詞-普通名詞-一般` | `記号` | `26948` | Domain/medical acronym; topic-only or heavily deprioritized by default. |
| `ＳＮＳ` | `名詞-普通名詞-一般` | `記号` | `43114` | Useful Japanese-context tech term despite low BCCWJ rank. |

Proposed derived fields:

- `bccwj_symbol_wtype`: true for `wtype=記号`;
- `bccwj_proper_wtype`: true for `wtype=固`;
- `bccwj_global_commonness`: from rank/PMW;
- `bccwj_core_commonness`: from core rank/PMW;
- `bccwj_domain_concentration`: high when domain ranks exist only in a narrow
  subset or rank spread is large;
- `bccwj_fixed_variable_skew`: reuse fixed/variable delta as weak
  formal/context signal;
- `bccwj_real_usage_confidence`: high when global/core rank and PMW are strong.

BCCWJ can answer "does this actually occur in contemporary written Japanese?"
and "is usage narrow?" It cannot answer "is this worth teaching?" by itself.

### JMnedict

Current parser preserves:

- surfaces/readings;
- name types;
- grouped name type classes;
- name signal score.

Local example:

- `ＮＨＫ` appears as an organization name in JMnedict.

Proposed derived fields:

- `jmnedict_acronym_name_type`: person/place/company/organization/product/work;
- `acronym_proper_name_risk`: high for organization/product/work acronyms;
- `cultural_infrastructure_exception`: possible review lane for terms such as
  `ＪＲ` and `ＮＨＫ`, which are proper names but useful in Japan context.

JMnedict should demote or topic-scope proper acronyms. It should not suppress
all organization acronyms blindly, because a learner may want common cultural
infrastructure terms.

### Source-Side Rule Context

Target-only SRS seed rows cannot always determine whether a target acronym is
an exact identity replacement from English. For example:

- `PDF -> ＰＤＦ` is likely low SRS value because the user already knows the
  source surface.
- `commercial -> ＣＭ` is a Japanese lexicalization and can be useful.
- `no good -> ＮＧ` is Japanese-specific shorthand and can be useful.

Therefore exact-identity suppression should use one of:

1. rulegen candidate source/replacement pairs when available;
2. JMDict exact acronym gloss as a proxy;
3. a curated small allow/block policy for high-confidence shared acronyms.

Do not make target-only acronym surface an unconditional suppress signal.

## Proposed Classification Fields

Add a structured payload, likely under `learner_signals["ja_acronym"]`:

```json
{
  "acronym_signal_version": "ja_acronym_signal_v1",
  "normalized_ascii_surface": "PDF",
  "surface_confidence": 1.0,
  "reading_spellout_confidence": 1.0,
  "lexicalized_reading": false,
  "identity_gloss_confidence": 1.0,
  "expanded_gloss_confidence": 0.0,
  "japanese_specific_usage_confidence": 0.0,
  "domain_concentration": 0.6,
  "proper_name_risk": 0.0,
  "real_usage_confidence": 0.7,
  "recommended_acronym_class": "shared_exact_acronym",
  "recommended_candidate_state": "suppressed_default",
  "recommended_admission_suitability": 0.0,
  "reasons": [
    "fullwidth_latin_surface",
    "letter_name_reading",
    "exact_acronym_gloss"
  ]
}
```

Recommended classes:

- `shared_exact_acronym`
- `japanese_specific_acronym`
- `domain_acronym`
- `proper_name_acronym`
- `mixed_code_term`
- `unknown_acronym_like`
- `not_acronym`

Recommended new problem class:

- `acronym_or_code`

Candidate-state mapping:

| Class | Default state | Admission suitability | Difficulty treatment |
| --- | --- | ---: | --- |
| `shared_exact_acronym` | `suppressed_default` | `0.0` to `0.05` | Do not score as normal vocab. |
| `japanese_specific_acronym` | `normal_vocab` or `deprioritized_vocab` | `0.45` to `0.85` | Cap or moderate; do not force tail. |
| `domain_acronym` | `topic_only` or `deprioritized_vocab` | `0.10` to `0.40` default | Let active topic lift it. |
| `proper_name_acronym` | `deprioritized_vocab` or `topic_only` | `0.15` to `0.50` | Use name/topic handling, not raw tail. |
| `mixed_code_term` | review/default deprioritized | `0.15` to `0.60` | Needs fixtures before broad policy. |
| `unknown_acronym_like` | `deprioritized_vocab` | `0.20` to `0.45` | Prefer safe demotion over suppression. |

## Policy Principles

1. Acronymness is not a difficulty-increase signal.
2. Exact shared acronyms are usually poor default SRS cards because the
   source-side learner already recognizes the surface.
3. Japanese-specific acronyms can be real vocabulary and should be admitted
   when common enough.
4. Domain acronyms should be topic-scoped or deprioritized unless the user's
   active topics or current context justify them.
5. Proper-name acronyms should use the proper-name path, with a small exception
   lane for high-value cultural infrastructure.
6. Ambiguous acronym-like rows should be demoted, not hard-suppressed, until
   fixtures prove a stronger rule.

## Candidate Examples

| Example | Likely class | Rationale |
| --- | --- | --- |
| `ＡＩ` | `shared_exact_acronym` or `domain_acronym` | Exact English acronym gloss; common, but low replacement-learning value. |
| `ＵＳＢ` | `shared_exact_acronym` | Exact acronym gloss and common carryover. |
| `ＰＤＦ` | `shared_exact_acronym` | Exact acronym gloss; q20 overpromotes it. |
| `ＤＶＤ` | `shared_exact_acronym` | Very common, but likely not useful as a default SRS replacement. |
| `ＣＭ` | `japanese_specific_acronym` | Common Japanese usage for commercials; JMDict priority and BCCWJ frequency. |
| `ＮＧ` | `japanese_specific_acronym` | Colloquial Japanese-specific "not allowed/no good" usage. |
| `ＯＬ` | `japanese_specific_acronym` | "office lady"; culturally specific and real, but may be dated/register-marked. |
| `ＳＮＳ` | `japanese_specific_acronym` / `domain_acronym` | Internet field; useful in Japanese, even if source acronym is recognizable. |
| `ＴＯＥＩＣ` | `proper_name_acronym` or `domain_acronym` | Exam/product-like entity, lexicalized reading, useful in education/work contexts. |
| `ＭＲＩ` | `domain_acronym` | Medical/technical; exact acronym gloss. |
| `ＭＲＳＡ` | `domain_acronym` | Medical acronym; should not be a default tail target. |
| `ＮＨＫ` | `proper_name_acronym` | JMnedict organization; useful but not ordinary vocabulary. |
| `ＪＲ` | `proper_name_acronym` | Infrastructure organization; possibly useful exception. |
| `ＶＲ` | `domain_acronym` / `shared_exact_acronym` | Exact tech acronym; topic or context should drive admission. |

## Implementation Phases

### Phase 1: Detector And Fixture Coverage

Implement pure helpers, with unit tests:

- NFKC acronym/code normalization;
- all-Latin/full-width/mixed-code surface detection;
- Japanese letter-name reading matcher;
- JMDict exact-acronym gloss detector;
- Japanese-specific gloss cue detector;
- domain-field extraction from JMDict fields;
- BCCWJ usage/domain profile summarizer;
- JMnedict proper-name acronym risk.

Suggested test module:

- `core/tests/resources/test_japanese_acronym_signals.py`

Fixture rows should include at least:

- shared exact: `ＡＩ`, `ＵＳＢ`, `ＰＤＦ`, `ＤＶＤ`;
- Japanese-specific: `ＣＭ`, `ＮＧ`, `ＯＬ`, `ＳＮＳ`;
- domain: `ＭＲＩ`, `ＭＲＳＡ`, `ＶＲ`;
- proper-name: `ＮＨＫ`, `ＪＲ`, `ＴＯＥＩＣ`;
- mixed-code counterexamples: `Ｘ線`, `３Ｄ`, `Ｂ型`, `Ｎ１`, `ＣＤ－ＲＯＭ`.

### Phase 2: Learner Signal Bundle

Add `ja_acronym` to `build_japanese_learner_signal_bundle(...)`.

Do not change default admission behavior in this phase. First regenerate or
audit seed rows and inspect coverage:

- total acronym-like rows;
- rows by recommended class;
- JMDict/BCCWJ/JMnedict coverage by class;
- false positives in non-acronym mixed-script rows.

Suggested output:

- `docs/test_outputs/srs_ja_acronym_signal_audit_latest.json`
- `docs/test_outputs/srs_ja_acronym_signal_audit_latest.md`

### Phase 3: Classification Policy

Extend `candidate_classification.py`:

- add `PROBLEM_CLASS_ACRONYM_OR_CODE`;
- accept optional learner-signal metadata or a precomputed acronym signal in
  `classify_srs_candidate(...)`;
- map high-confidence acronym classes to candidate states and admission
  suitability.

Avoid using only surface regex in classification. The classifier should require
supporting evidence unless the row is a very high-confidence exact shared
acronym.

### Phase 4: Sweep Components

Expose new components in
`scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py`:

- `acronym_surface_confidence`;
- `acronym_spellout_reading`;
- `acronym_identity_gloss`;
- `acronym_japanese_specific_usage`;
- `acronym_domain_concentration`;
- `acronym_proper_name_risk`;
- `acronym_real_usage_confidence`;
- `acronym_default_suppress_risk`;
- `acronym_topic_only_risk`.

Use these as model features only after the classifier has decided whether the
row remains normal vocabulary. This prevents the formula from learning "Latin
rows are hard" as a shortcut.

### Phase 5: Review And Acceptance

Add an acronym-focused review artifact:

- compare current q15, q20, and new acronym-aware candidate;
- list all q20-over-q15 acronym promotions with new class/state;
- show before/after upper-tail samples;
- show Japanese-specific acronym examples that remain admitted.

Acceptance criteria:

- `ＰＤＦ`, `ＵＳＢ`, `ＤＶＤ`, and similar exact carryovers do not appear as
  ordinary high-difficulty default vocab;
- `ＣＭ`, `ＮＧ`, `ＯＬ`, and `ＳＮＳ` are not blindly suppressed;
- `ＭＲＩ`, `ＭＲＳＡ`, and similar domain acronyms become topic-scoped or
  deprioritized by default;
- `ＮＨＫ` and `ＪＲ` follow proper-name policy, with explicit exceptions if
  desired;
- q15/q20 upper-tail acronym pollution is reduced without regressing reviewed
  beginner, intermediate, and rare-kanji/wago calibration cases;
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
  remains passing after production policy changes.

## Open Decisions

1. Exact shared-acronym suppression threshold:
   - strict: suppress only when exact acronym gloss and spell-out reading agree;
   - broader: suppress all high-confidence all-Latin rows unless Japanese-specific
     usage is detected.
   - Recommendation: start strict.
2. Japanese-specific acronym allowlist:
   - source-only signals catch many cases, but `ＣＭ`, `ＮＧ`, `ＯＬ`, `ＳＮＳ`,
     `ＪＲ`, and `ＮＨＫ` are important enough to use as calibration fixtures.
   - Recommendation: allow calibration fixtures without creating a large
     hardcoded production allowlist.
3. Topic mapping:
   - JMDict fields such as `internet`, `medicine`, `computer`, `business`,
     `finance`, and `sports` should map into existing topic preferences.
   - Recommendation: reuse the topic-normalization pipeline rather than define a
     separate acronym topic map.
4. Rulegen source-pair identity:
   - target-only SRS seed cannot fully know if `ＰＤＦ` is being taught from
     English `PDF`;
   - rulegen publication can know source/replacement identity.
   - Recommendation: keep target-side suppression conservative, then add a
     rulegen-side low-value identity guard for exact source-target acronym pairs.
5. Mixed-code terms:
   - `Ｘ線`, `３Ｄ`, `Ｂ型`, and `Ｎ１` are not the same as all-letter acronyms.
   - Recommendation: classify separately and only demote until fixtures are
     reviewed.

## Work Sequence

Recommended next implementation order:

1. Done: add pure acronym-signal extraction helpers and fixture tests.
2. Done: add a no-behavior-change audit script to measure corpus coverage and
   class distribution.
3. Done: add `ja_acronym` to learner-signal metadata.
4. Done: add sweep components so q15/q20/model-family review artifacts can show
   acronym diagnostics.
5. Pending: rerun q15/q20 review packs with acronym diagnostics included.
6. Pending: add candidate-classification policy behind tests.
7. Pending: run focused acronym-aware comparisons against current best
   difficulty/admission candidates.
8. Pending: promote the safest policy only after qualitative review confirms
   that exact
   carryovers are gone while Japanese-specific acronyms remain available.

This order keeps correctness first: source analysis and audit before production
classification, and classification before formula tuning.
