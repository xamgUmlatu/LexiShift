# en-ja to en-es Learner-Difficulty Transfer Audit

Status: design audit with first en-es formula and calibration-review sidecars implemented
Created: 2026-07-05
Runtime behavior changed: false
Manual corrections added: false

## Purpose

Critically inspect the mature `en-ja` learner-difficulty methodology and decide
which ideas should be transferred into the first `en-es` formula sweep.

The transfer principle is role-based, not name-based:

```text
Do not ask: "Can we port this en-ja signal?"
Ask:        "What modeling job did this en-ja signal do, and do we have an
             en-es source-backed signal that can do the same job?"
```

This matters because `en-ja` has learner-specific and script-specific sources
that `en-es` does not currently have. Porting those literally would create a
false sense of rigor. The goal is to preserve the useful model shape while
using only evidence that exists for Spanish.

## Current en-es Signal State

Current palette artifact:

- `docs/test_outputs/srs_learner_difficulty_signal_palette_en_es_latest.md`
- `docs/test_outputs/srs_learner_difficulty_signal_palette_en_es_latest.json`

Current formula-shape probe artifact:

- `docs/test_outputs/srs_learner_difficulty_formula_probe_en_es_latest.md`
- `docs/test_outputs/srs_learner_difficulty_formula_probe_en_es_latest.json`

Current calibration review-pack artifact:

- `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_latest.md`
- `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_latest.json`
- `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.md`
- `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.json`

Current promoted reviewed label inputs:

- `docs/test_inputs/srs_learner_difficulty_calibration_en_es.json`
- `docs/test_inputs/srs_learner_difficulty_holdout_en_es.json`

Current labeled formula-evaluation artifact:

- `docs/test_outputs/srs_learner_difficulty_formula_eval_en_es_latest.md`
- `docs/test_outputs/srs_learner_difficulty_formula_eval_en_es_latest.json`

Top-10k installed-pack coverage from the latest palette:

| Signal group | Coverage |
| --- | ---: |
| SPALEX rank/commonness | 100.0% |
| SPALEX Zipf | 100.0% |
| Effective POS via UD AnCora overlay | 77.9% |
| Dictionary entry metadata | 77.7% |
| Dictionary sense/gloss metadata | 77.7% |
| Dictionary topics | 12.2% |
| Dictionary marked-use cue | 3.8% |
| Spanish diacritic/form cue | 20.7% |

Interpretation:

- The strong spine is SPALEX exposure/commonness.
- The second strongest usable family is POS plus dictionary metadata.
- There is no JLPT-equivalent, lesson-order source, kanji curriculum source, or
  reading-specific variant source currently wired for Spanish.

## en-ja Roles And en-es Transfer Decisions

| en-ja role | en-ja implementation examples | en-es analogue | Transfer decision |
| --- | --- | --- | --- |
| Native exposure spine | BCCWJ `frequency`, JMDict priority, TUBELEX | SPALEX rank/pmw/freq/Zipf/prevalence/percent | Transfer directly. This should be the base of every first-pass model. |
| Frequency curve shape | `frequency_sqrt`, `frequency_power2`, `frequency_tail65`, `frequency_tail80`, piecewise bands | Same transforms over SPALEX-derived difficulty values | Transfer directly. This is language-independent and likely important. |
| Bounded correction | `max_shift_from_frequency` variants | Same cap around SPALEX base | Transfer directly. It limits damage from weak side signals. |
| Piecewise phase model | early/middle/tail sections anchored on frequency | early/core/native/tail sections anchored on SPALEX base | Transfer cautiously. Useful, but needs labels and sample review because Spanish lacks curriculum anchors. |
| Source arbitration | pedagogical/native/burden/admission experts with confidences | native/dictionary/form/admission experts with confidences | Transfer the shape, not the exact experts. There is no Spanish pedagogical expert yet. |
| Knownness / missingness | `*_known`, `source_coverage_count` | SPALEX known, POS known, dictionary known, marked/tag/topic known | Transfer directly. Missing dictionary/POS evidence is not the same as "easy" or "hard." |
| Pedagogical anchors | JLPT vocab, lesson vocab, old JLPT kanji | None currently | Do not transfer now. Add later only if CEFR/course/list source is audited and wired. |
| Orthographic burden | kanji grade, stroke, KanjiVG, script complexity | weak Spanish form features: length, diacritics, multiword, punctuation, suffix cues | Transfer only as weak/tiny capped probes. Spanish writing burden is not analogous to kanji burden. |
| Reading/variant pollution | rare readings, same-surface exact/family protection, kana-preferred rows | Kaikki `form_of`, `alt_of`, multiword/punctuation, maybe inflection/variant cues | Transfer conceptually. Use dictionary variant metadata, not Japanese reading logic. |
| Dictionary ambiguity | JMDict entry/POS/sense/gloss/form counts | Kaikki entry/sense/gloss/translation/POS counts | Transfer cautiously. Ambiguity can mean common polysemy, not necessarily difficulty. |
| Marked/register/domain risk | JMDict dialect, rare, archaic, abbreviation, field values | Kaikki tags/categories/topics: rare, obsolete, slang, regional, vulgar, formal, literary; dictionary topics | Transfer cautiously with frequency gates and caps. Raw topic/category facts are not direct penalties. |
| Non-ladder/admission guard | candidate state, proper/name/entity suppression | POS bucket, candidate classifier, proper-like dictionary tags/categories when available | Transfer as guard/admission pressure, not pure difficulty. Function words may be early but not always good SRS vocabulary. |
| Loanword / gairaigo origin ease | JMDict source-language + English source/gloss frequency | English-Spanish cognate/transparency from target surface and English translations/glosses | Strong new en-es candidate. Needs a source-backed translation/gloss text signal and false-friend caution. |
| Compound/standalone leakage | Japanese same-family compound-heavy guard | no direct analogue yet | Do not transfer now. Spanish would require morphology/corpus parsing beyond current signals. |

## Candidate en-es Component Families For Sweep

The first en-es sweep should expose components by function. Names below are
suggested implementation names, not committed API.

### 1. Frequency Base And Shape

Required components:

```text
frequency = current SPALEX-derived difficulty proxy
spalex_rank_difficulty
spalex_zipf_difficulty
spalex_prevalence_difficulty
spalex_percent_difficulty
frequency_sqrt
frequency_power2
frequency_power3
frequency_tail50
frequency_tail65
frequency_tail80
frequency_tail90
```

Why:

- This is the only full-coverage source-backed ordering signal.
- en-ja improved materially when frequency was treated as a curve, not just a
  flat scalar.

Sweep treatment:

- Always include at least one frequency spine.
- Try bases separately and blends:

```text
base = weighted_mean(rank_difficulty, zipf_difficulty, prevalence_difficulty)
```

- Sweep transforms and tail ramps rather than assuming linearity.

### 2. POS And Candidate Suitability

Candidate components:

```text
pos_known
pos_function_risk        # determiner/adposition/conjunction/pronoun/interjection/numeral
pos_content_gate         # noun/verb/adjective/adverb
pos_other_risk
candidate_non_normal_risk
admission_suitability_risk = 1 - admission_suitability
```

Why:

- Spanish top frequency rows are heavily grammatical: `que`, `los`, `del`,
  `por`, `con`, `una`, `para`, etc.
- Some may be valid early learner items, but many are weak standalone SRS
  vocabulary compared with content words.

Sweep treatment:

- Keep this as bounded upward pressure or admission guard.
- Do not globally demote all function words until sample review confirms that
  this matches desired UX.

### 3. Dictionary Ambiguity And Polysemy

Candidate components:

```text
dict_entry_known
dict_entry_count_score
dict_sense_count_score
dict_gloss_count_score
dict_translation_count_score
dict_pos_count_score
dict_sense_ambiguity
dict_gloss_ambiguity
dict_translation_ambiguity
common_dict_ambiguity = frequency_ease * dict_ambiguity
tail_dict_ambiguity = frequency_tail65 * dict_ambiguity
```

Why:

- en-ja ambiguity signals helped identify rows that are common-looking but
  messy, overloaded, or not clean standalone vocabulary.
- In Spanish, polysemy is common in normal words (`por`, `como`, `medio`,
  `parte`, `cuenta`). This can be useful, but it is dangerous as a direct
  difficulty penalty.

Sweep treatment:

- Try both common-gated and tail-gated ambiguity.
- Keep caps small in first pass.

### 4. Dictionary Markedness / Domain / Variant Metadata

Candidate components:

```text
dict_marked_usage_risk       # rare/obsolete/archaic/dialectal/regional/slang/vulgar/etc.
dict_form_of_risk
dict_alt_of_risk
dict_variant_risk = max(form_of, alt_of)
dict_topic_known
dict_topic_domain_risk       # only through allowlisted topic groups, if used
dict_category_noise_risk     # only after precision review
```

Why:

- This is the closest Spanish analogue to JMDict marked/form/source flags.
- It may help keep dictionary artifacts, rare forms, and domain-only vocabulary
  from leaking too early.

Sweep treatment:

- Use as gated risk:

```text
risk_effective = risk * max(frequency_tail65, ordinary_vocab_residual)
```

- Avoid raw category penalties until topic/category precision is reviewed.

### 5. Spanish Form / Orthographic Features

Candidate components:

```text
char_length_difficulty
multiword_risk
hyphen_or_punctuation_risk
digit_risk
diacritic_burden_light
spanish_specific_letter_light
suffix_mente_flag
verb_infinitive_like
participle_like
gerund_like
```

Why:

- This is not equivalent to kanji burden.
- It can still help identify phrases, artifacts, and some visually harder or
  morphologically marked rows.

Sweep treatment:

- Tiny bounded probes only.
- `diacritic` should not be treated as strong difficulty; Spanish learners must
  learn accents early.
- `verb_infinitive_like` may be an ease/clean-lemma cue rather than a risk.

### 6. English-Spanish Transparency / Cognate Ease

Candidate components:

```text
english_translation_similarity_ease
english_translation_similarity_risk = 1 - ease
english_translation_frequency_ease
cognate_rescue = similarity_ease * english_translation_frequency_ease
rare_cognate_tail_rescue = frequency_tail50 * cognate_rescue
false_friend_caution = high_similarity * high_dictionary_ambiguity
```

Why:

- This is the main en-es-specific opportunity that en-ja did not have in the
  same form.
- For an English-speaking learner, Spanish words that resemble common English
  translations are often easier than Spanish frequency alone predicts:
  `animal`, `hospital`, `doctor`, `normal`, `central`, `música`, `familia`.

Source support:

- Kaikki/Wiktionary `sense_glosses.translation_lc` already exists locally.
- The first formula probe reads bounded translation text directly from the
  Kaikki/Wiktionary SQLite and combines it with local English frequency.

Required hook before sweep:

- Implemented in `scripts/testing/srs_learner_difficulty_formula_probe_en_es.py`
  as a sweep-local extraction. Cognate rescue is POS-compatible so a noun sense
  cannot lower a verb-form row solely because the spellings match.

Sweep treatment:

- Use as downward/ease pressure, capped.
- Require high confidence: target surface similar to at least one English
  translation/gloss token.
- Penalize or suppress the rescue when dictionary ambiguity is very high.

## First Sweep Shape Recommendation

Start with a bounded-correction model:

```text
base = frequency_spine(SPALEX)

upward_risk =
    w_pos      * pos_function_or_other_risk
  + w_variant  * dict_variant_risk
  + w_marked   * gated_dict_marked_usage_risk
  + w_ambiguity* gated_dict_ambiguity
  + w_form     * weak_form_risk

downward_ease =
    w_cognate * cognate_rescue
  + w_content * pos_content_gate_small

score = clamp(base + cap_up(upward_risk) - cap_down(downward_ease))
```

Initial cap grid:

```text
up_cap   in {0.00, 0.04, 0.08, 0.12, 0.18}
down_cap in {0.00, 0.03, 0.06, 0.10}
```

Then add a piecewise variant only after the bounded model has a baseline:

```text
early/core section:
    frequency spine + tiny content/POS guard + cognate rescue

middle section:
    frequency spine + dictionary ambiguity + cognate rescue

tail section:
    frequency tail + marked/domain/variant/form risks
```

## What Not To Do Yet

Do not port these en-ja mechanisms literally:

- JLPT/lesson curves.
- Kanji grade, old JLPT kanji, stroke count, KanjiVG.
- Japanese rare-reading or same-kanji reading checks.
- Wago/kango/gairaigo lanes.
- Compound-leak guard.
- A manual correction overlay.

Each may have an eventual Spanish analogue, but none has enough current
source support to be part of the first honest en-es formula sweep.

## Immediate Implementation Plan

1. Generate qualitative samples from the formula probe and review whether the
   bounded guards/rescues match product intuition.
2. Create a small reviewed calibration set for
   `en-es`; until then, use qualitative band samples and component diagnostics.
3. After labels exist, turn the same component families into a scored grid:
   - frequency-only baselines;
   - bounded correction variants;
   - optional piecewise variants;
   - optional cognate-rescue variants.
4. Only after formula behavior is stable, add a sparse manual correction layer
   for first-page/first-200 product polish.

## Current Recommendation

The most promising transferred ideas are:

1. Frequency curve/base-shape sweep over SPALEX fields.
2. Bounded correction around frequency.
3. POS/function-word admission guard.
4. Dictionary markedness and variant risk, frequency-gated.
5. Dictionary ambiguity, frequency-gated and capped.
6. English-Spanish cognate/transparency ease, capped and ambiguity-aware.

The least transferable en-ja ideas are kanji/script burden and JLPT-style
pedagogical anchoring. Those should stay out until we have actual Spanish
sources that support them.
