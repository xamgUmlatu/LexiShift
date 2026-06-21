# SRS Learner Difficulty Model Workplan

Status: active design/workplan
Role: Planning authority for learner-difficulty and admission-target semantics
Last updated: 2026-06-18
Last verified: 2026-06-18 from en-ja profile-bootstrap samples, BCCWJ frequency rows, current SRS admission code paths, `scripts/testing/srs_learner_difficulty_audit_en_ja.py`, learner-difficulty signal sweeps, contender samples, experimental piecewise review artifacts, model-tree search artifacts, model-family search artifacts, model-family meta-search artifacts, smooth curve search artifacts, residual-gate audit artifacts, JLPT-curve/dampening sweep smoke tests, band-expert guard audits, and holdout evaluation artifacts.
Purpose: define how LexiShift should separate corpus frequency, admission suitability, and learner difficulty before tuning en-ja or future LP admission behavior.
Source-of-truth: design/workplan only. Current executable behavior lives in `core/lexishift_core/srs/`, tests, generated SRS artifacts, and installed helper resources.
Related source-lane audit: `docs/language_pairs/en_ja_learner_signal_source_matrix.md`.
Related acronym/code plan: `docs/srs/srs_en_ja_acronym_signal_plan.md`.

## Problem Statement

The current SRS admission path has enough machinery to admit words and respond to
profile preferences, but it still uses corpus commonness as the main proxy for
difficulty. That breaks down for Japanese and will also break down for future
LPs where frequency, pedagogical order, morphology, script knowledge, and
grammar category are not the same thing.

The concrete issues observed during en-ja sampling are:

- Some candidates should not be fixed by merely pushing them to higher
  difficulty. Particles, suffixes, counters, formulaic numerals, and highly
  compositional items may be bad standalone vocabulary cards even when they are
  common or useful.
- Frequency and learner difficulty are correlated but not equivalent. A rare
  but transparent compound can be easy, while a frequent function word or
  grammatical form can be hard to teach as a vocabulary card.
- The profile model currently mixes "the user can handle this" and "aim the
  next admission here." A high proficiency setting can still admit easier words
  because easy words remain acceptable under the current readiness model.
- Trivial numerals such as `一`, `二`, and `六` can appear across different
  proficiency previews (`0.00`, `0.25`, `0.50`) even though a learner model
  should treat them as the same beginner/pattern family.

The target is a real `learner_difficulty` model that is separate from frequency
and separate from admission suitability.

## Current Behavior

The current en-ja profile bootstrap path can be summarized as:

1. Build a candidate frontier from the target frequency pack.
2. Assign a source/commonness weight from frequency-derived seed fields.
3. Assign an admission/coverage weight that may include POS demotion.
4. Classify obvious candidate states and presentation modes with
   `candidate_classification_v3`, including source-backed en-ja acronym/code
   recommendations.
5. Estimate difficulty as `1 - source_commonness`.
6. Score candidates with selector weights, currently dominated by
   `base_freq = 0.55`; profile/user difficulty terms are smaller.
7. Apply readiness and `admission_suitability` multipliers.
8. Sample from the selected active pool, not from a sorted curriculum list.

The recent correction from `1 - admission_weight` to `1 - base_weight` was the
right direction: POS demotion should not automatically make a word "harder."
However, `1 - base_weight` is still only a corpus-frequency proxy, not a
pedagogical difficulty model.

Relevant current code paths:

- `core/lexishift_core/srs/profile_bootstrap.py`
  - `ProfileBootstrapPolicy.selector_config`
  - `ProfileBootstrapPolicy.difficulty_proxy`
  - `extract_profile_bootstrap_candidate_traits(...)`
- `core/lexishift_core/srs/profile_bootstrap_support.py`
  - `compute_proficiency_fit(...)`
  - `compute_challenge_fit(...)`
  - `compute_readiness_gate(...)`
- `core/lexishift_core/srs/admission_policy.py`
  - POS weighting used for admission suitability
- `core/lexishift_core/srs/admission_features.py`
  - serialized candidate/profile feature shapes
- `core/lexishift_core/srs/candidate_classification.py`
  - deterministic LP-aware candidate state and default suitability classifier
- `core/lexishift_core/srs/selector.py`
  - readiness and admission-suitability multipliers

## Current en-ja Sample Evidence

After the `1 - base_weight` correction, `candidate_classification_v3`, row-aware
candidate identity diagnostics, and the first `learner_difficulty_v1` exact
overlay, sampled rows are no longer polluted by obvious pattern, grammar,
suppressed, or deprioritized items in the product-default full-frontier audit.
The candidate frontier is unbounded by default, so high-proficiency sampling can
see the harder rows already present in the installed corpus.

| Profile proficiency | Observed average sampled difficulty | Interpretation |
| --- | ---: | --- |
| `0.00` | about `0.27` | Beginner samples are easy and normal-vocab only. |
| `0.25` | about `0.32` | Low bands separate better but remain compressed. |
| `0.50` | about `0.39` | Still mostly common/easy words under the frequency proxy. |
| `0.75` | about `0.59` | Mid-high samples move up meaningfully. |
| `1.00` | about `0.83` with full frontier | Normal-vocab only, now reaching the harder tail available in the installed corpus. |

Expanding the candidate frontier proved that the data already had harder
candidates available. The product default now uses all available seed rows for
bootstrap/admission sampling while still admitting only `initial_active_count`
items into active practice. That does not solve compositional words,
function-word suppression, or the difference between "rare" and "hard."

Current reproducible research artifacts:

```bash
python3 scripts/testing/srs_learner_difficulty_audit_en_ja.py

python3 scripts/testing/srs_learner_difficulty_audit_en_ja.py \
  --top-n 800 \
  --json-out docs/test_outputs/srs_learner_difficulty_audit_en_ja_top800_latest.json \
  --markdown-out docs/test_outputs/srs_learner_difficulty_audit_en_ja_top800_latest.md
```

The product-default audit uses all available seed rows and reports:

- `78,316` row-aware JMDict-filtered seed candidates;
- `6,565 / 78,316` seeds in non-normal or explicitly deprioritized classes;
- reviewed calibration alignment:
  - `66 / 66` candidate-state/presentation/problem-class labels match;
  - default-vocab decision accuracy is `1.0` with no false admits or false
    suppressions;
  - current learner-difficulty bucket accuracy is `45 / 45` (`1.0`);
- sample difficulty averages by proficiency:
  `0.271`, `0.318`, `0.373`, `0.586`, `0.827`;
- fixed-proficiency challenge-target active averages:
  `0.308`, `0.363`, `0.548`, `0.743`;
- all audited samples are `normal_vocab`, including `p=1.00`.

The old capped `top_n=800` comparison reports:

- `740` row-aware JMDict-filtered seed candidates;
- `170 / 740` seeds in non-normal or explicitly deprioritized classes
  (`deprioritized_vocab`, `pattern_item`, `grammar_item`, or
  `suppressed_default`);
- reviewed calibration alignment degrades because the capped frontier misses
  `23` of the `66` reviewed rows and has one candidate-state mismatch;
- sample difficulty averages by proficiency:
  `0.28`, `0.33`, `0.39`, `0.59`, `0.66`;
- all audited samples are `normal_vocab`; the highest-proficiency warning now
  reflects old capped-frontier difficulty, not non-vocab leakage.

This means the high-proficiency gap was partly a frontier-size issue, but the
classification issue also exists inside the old capped frontier.
The first implementation slices expose candidate state, row identity,
presentation mode, learner-difficulty source, readiness center, and
`admission_suitability` so the selector avoids ranking pattern, grammar,
suppressed, and deprioritized rows as ordinary high-priority vocabulary by
default.

## Current Holdout Gate Evidence

The holdout gate now evaluates the current retained trace sweep directly,
instead of only older model-family/meta artifacts. It uses the current
`news_entity_refine_new_s005_r010` trace, component matrix, and calibration
matrix by default:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_trace_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_component_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_calibration_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_holdout_eval_en_ja_latest.md`

The latest holdout run evaluated `400` current trace candidates, `200` family
candidates, and `120` meta candidates. The current calibration winner is still:

- `grid_s20_cnone_000661__jlptn5_06_n4_28_n3_50_n2_72_n1_94__kd050`
- calibration balanced `0.923025`, MAE `0.107987`, pairwise `0.900000`
- holdout balanced `0.699736`, MAE `0.176761`, pairwise `0.794725`

That gap is real evidence of calibration overfit or holdout-label distribution
mismatch. The best current trace candidate on holdout reached about `0.749751`
balanced, while the best all-source holdout result was the older
`boost__grid_s10_cnone_008869__rare_wago_tail_risk_t35_s28` family/meta path at
about `0.823692` balanced. Do not promote the calibration winner as the product
learner-difficulty default without resolving this calibration/holdout split.

The guard/stitch path was also corrected so missing guarded experts cannot
silently fall back to unguarded behavior, and high-tail/default-decision scores
are part of the guard. With those fixes, the stitched candidates did not beat
the base calibration candidate, so band-expert stitching remains research-only.

## Why `一`, `二`, And `六` Split Across Bands

The BCCWJ rows show these are all extremely common numeral entries:

| Lemma | Main BCCWJ form | POS | Rank | Core rank |
| --- | --- | --- | ---: | ---: |
| `一` | `イチ` | `名詞-数詞` | `23` | `21` |
| `二` | `ニ` | `名詞-数詞` | `28` | `24` |
| `六` | `ロク` | `名詞-数詞` | `65` | `51` |

They split across samples because the current preview is a weighted draw from an
active candidate pool. It is not a deterministic difficulty-bucket curriculum.
The final sample is affected by:

- the candidate frontier;
- source/commonness score;
- admission/coverage score;
- POS handling for numeral-like `other` buckets;
- readiness gating;
- random sample seed and pool membership;
- the fact that low and mid difficulty estimates are compressed under the
  frequency proxy.

That means the split is not evidence that `一`, `二`, and `六` have genuinely
different learner difficulty. It is evidence that the current model lacks a
clean learner-difficulty overlay. Simple numerals may remain pattern-lane
material, but transparent compound numerals should be suppressed from the
current vocab-first SRS flow rather than quizzed as standalone vocabulary.

Related BCCWJ rows also show why frequency alone misleads:

| Lemma | Main BCCWJ form | POS | Rank | Core rank | Learner interpretation |
| --- | --- | --- | ---: | ---: | --- |
| `七百` | `ナナヒャク` | `名詞-数詞` | `579` | `691` | Less frequent as a surface, but compositionally simple after `七` + `百`. |
| `三千` | `サンゼン` | `名詞-数詞` | `675` | `696` | Same issue: rare surface, easy pattern once components are known. |
| `三` | `サン` | `名詞-数詞` | `32` | `27` | Easy simple numeral. |

## Candidate States

Not every candidate should be represented as "normal vocab with higher or lower
difficulty." The admission layer should support candidate states:

| State | Meaning | Examples |
| --- | --- | --- |
| `normal_vocab` | Good default standalone SRS vocabulary card. | nouns, verbs, adjectives, common adverbs with stable meanings |
| `deprioritized_vocab` | Valid vocabulary, but lower default priority unless profile/topic evidence lifts it. | political organizations, less central named entities, topic-colored proper nouns |
| `pattern_item` | Useful learner material, but better taught through a pattern lane than as a standalone replacement word. | simple numerals, simple counters |
| `grammar_item` | Important but not suitable for normal vocab admission without a grammar-aware card. | particles, auxiliary-like forms, suffixes/prefixes |
| `topic_only` | Admit only when a user's topic/domain preference or current-page signal justifies it. | sports team names, medical terms, domain-specific proper nouns |
| `suppressed_default` | Do not admit by default. Allow only explicit override or future specialized lane. | compound numerals, junk rows, punctuation-like forms, malformed rows, source artifacts |

Current en-ja classification uses `deprioritized_vocab` for proper nouns that
are valid vocabulary but weaker default targets. Core country/place names such
as `日本`, `中国`, `アメリカ`, and `フランス` are treated as normal vocabulary
despite proper-noun POS because they are central learner words.

This matters because pushing an unsuitable item toward higher difficulty can be
wrong. `七百` is not advanced vocabulary just because the exact surface is less
frequent, and it is not a good current SRS vocabulary card just because it can
be parsed as a pattern. A suffix is not a better advanced target because POS
demotion lowered its admission score. These need type-aware routing, not
scalar-only tuning.

Current identity posture: seed rows and admission diagnostics now carry a
row-aware candidate identity, so audits and previews can distinguish readings/POS
for the same surface, for example `的` as suffix-like `てき` and noun `まと`.
Persisted SRS item IDs still use `pair:lemma`; a full persisted item-ID
migration remains separate and should be planned deliberately because it touches
runtime rules, feedback, existing stores, and diagnostics.

## Proposed Model

Separate these dimensions:

| Dimension | Question answered | Should affect |
| --- | --- | --- |
| `corpus_commonness` | How common is this form in the source corpus? | coverage gain, source priority |
| `learner_difficulty` | How hard is this item for a learner at this stage? | proficiency/challenge targeting |
| `admission_suitability` | Is this a good standalone SRS admission candidate? | default inclusion, demotion, suppression |
| `presentation_mode` | How should the learner encounter this item? | vocab card vs pattern/grammar/composition lane |
| `topic_relevance` | Does this match user interests or page/context needs? | topic lift and topic-only admission |
| `rulegen_runtime_value` | Can this produce useful replacement rules? | browser replacement value and publication priority |

For the next implementation slice, add explicit feature fields rather than
overloading `difficulty_estimate`:

```json
{
  "corpus_commonness": 0.79,
  "coverage_gain": 0.32,
  "learner_difficulty": 0.08,
  "admission_suitability": 0.02,
  "presentation_mode": "pattern",
  "candidate_state": "pattern_item",
  "difficulty_sources": ["frequency_proxy", "ja_numeral_parser"],
  "suitability_reasons": ["numeral_compositional"]
}
```

`difficulty_estimate` can remain as a compatibility field during migration, but
new scoring should read `learner_difficulty` when present.

## en-ja Signal Plan

Start with deterministic, local, license-safe signals before considering LLM
expansion:

1. `ja_number_expression`
   - Detect simple kanji numerals, Arabic numerals, and transparent compounds.
   - Route simple numerals to `pattern_item`.
   - Suppress transparent compound numerals from current default vocab
     admission.
2. `ja_pos_suitability`
   - Use BCCWJ POS to route particles, prefixes, suffixes, and counters away
     from default standalone vocabulary admission.
   - Keep POS as suitability, not difficulty.
3. `ja_script_complexity`
   - Track script form, kanji count, kana-only status, and mixed-script shape.
   - This is a weak difficulty signal on its own, but useful when combined with
     learner-level or kanji-grade data.
4. `ja_dictionary_level_overlay`
   - Evaluate redistributable JLPT, school-grade kanji, or learner-list data.
   - Keep source/license provenance explicit before using this in shipped packs.
   - Current product-lane signals are internal Japanese script-shape facts,
     JMDict priority plus POS/misc lexical cues, KANJIDIC2 kanji
     grade/stroke/old-JLPT/frequency facts, JMnedict proper-name type cues, and
     KanjiVG visual/component facts; community JLPT vocabulary lists remain
     research-needed until provenance is clean.
5. `empirical_feedback`
   - Use user review history later to personalize difficulty and demotion.
   - Smooth changes over time; do not jump difficulty based on one failure.

## Aim-Here vs Can-Handle

Keep both concepts. They answer different questions:

- `proficiency_estimate`: what the learner can probably handle.
- `challenge_target`: where new admissions should aim.

Current behavior effectively treats proficiency mostly as a ceiling/readiness
signal. If `difficulty <= proficiency`, `compute_proficiency_fit(...)` returns
full fit, so a `1.00` proficiency user does not automatically prefer advanced
items. This explains why high-proficiency samples can still look too easy.

Target behavior:

- The UI can keep a single proficiency control if that is simpler, but the
  backend should derive a default `challenge_target` from it.
- Advanced users should see samples centered near their challenge target, not
  merely any words below their ceiling.
- If the user chooses an explicit challenge preference, it should override the
  derived default target.
- The selector should report both values in diagnostics so the product can
  explain why a candidate was admitted.

Suggested default target curve for investigation:

| Proficiency | Derived default challenge target | Intent |
| --- | ---: | --- |
| `0.00` | `0.10` | very easy starter material |
| `0.25` | `0.25` | beginner-plus |
| `0.50` | `0.50` | mid-level material |
| `0.75` | `0.72` | upper-mid material |
| `1.00` | `0.88` | advanced but not only obscure tail items |

This curve should be calibrated with actual sample audits and user feedback, not
treated as final.

## Acceptance Criteria

A learner-difficulty slice is acceptable when these are true for en-ja:

1. Per-proficiency sampled average `learner_difficulty` is monotonic enough for
   normal product use.
2. `p=1.00` high-challenge samples can reach genuinely advanced material without
   being dominated by obscure proper nouns, source artifacts, or compositional
   numerals.
3. Simple numerals (`一`, `二`, `三`, `六`, etc.) no longer drift across ordinary
   vocab difficulty bands as independent advanced/easy candidates.
4. Transparent compound numerals (`七百`, `三千`, etc.) are suppressed from
   default standalone vocab.
5. POS-demoted categories are not interpreted as harder merely because they are
   less suitable as standalone cards.
6. Default samples are not dominated by particles, suffixes, counters, proper
   nouns, or rare named entities unless the profile/topic explicitly requests
   them.
7. Diagnostics expose `corpus_commonness`, `learner_difficulty`,
   `admission_suitability`, and `presentation_mode` separately.

## Experiment Plan

### 1. Add A Labeled Calibration Set

Implemented as `docs/test_inputs/srs_learner_difficulty_calibration_en_ja.json`.
It is intentionally small enough to review and now includes `66` labels:

- beginner normal vocab;
- intermediate normal vocab;
- advanced normal vocab;
- pattern/compositional items;
- grammar/function items;
- proper nouns and topic-only items;
- known problematic numerals and suffixes.

The first target is not comprehensive coverage. It prevents obvious model
regressions and makes the review conversation concrete.
The current reviewed set is sufficient for first-pass classifier and default
admission regression checks. It is not yet large enough to claim broad Japanese
learner-difficulty accuracy.

### 2. Add A Learner-Difficulty Audit

`scripts/testing/srs_learner_difficulty_audit_en_ja.py` now emits:

- per-proficiency samples;
- average/min/max current learner difficulty;
- `candidate_state` distribution;
- `presentation_mode` distribution;
- row-aware candidate identity for ambiguous same-surface diagnostics;
- reviewed calibration precision/recall for candidate state, presentation mode,
  and problem class;
- default-vocab false-admit / false-suppress counts;
- learner-difficulty bucket accuracy against reviewed normal
  vocabulary labels;
- fixed-proficiency challenge-target spread checks;
- top reasons for demotion/suppression;
- examples of items admitted despite low suitability.

The audit should compare at least:

- current product-default learner-difficulty behavior;
- expanded `top_n=10000` frontier behavior;
- derived `challenge_target` behavior;
- learner-difficulty overlay behavior.

The product-default full-frontier behavior, capped comparison, challenge-target
spread, and first exact learner-difficulty overlay are implemented. Future
comparisons should add richer learner-level sources when chosen.

### 3. Implement en-ja Feature Overlay

Partially implemented through `candidate_classification_v2`,
`candidate_identity_v1`, and `learner_difficulty_v1`:

- simple kanji/Arabic/full-width numeral detection;
- compound numeral suppression for the current vocab-first flow;
- POS category routing for particles, suffixes, prefixes, counters, numerals;
- common country/place names as normal vocab;
- non-core proper-noun routing to `deprioritized_vocab` for blended topic lift;
- row-aware candidate identity in seeds, caches, previews, and audits;
- exact beginner-staple learner-difficulty overlay for a small reviewed en-ja
  set;
- compatibility serialization into admission diagnostics.

Still pending:

- a real compositional parser beyond obvious numeral strings;
- persisted reading/POS-aware SRS item identity for ambiguous same-surface rows;
- script complexity fields;
- learner-level/JLPT/kanji-grade overlays.

### 4. Wire Selector Semantics

Partially implemented. Profile-bootstrap scoring now:

- keeps frequency/commonness as coverage gain;
- applies `admission_suitability` as a selector multiplier;
- reads `learner_difficulty` when an overlay exists and falls back to
  `1 - base_weight`;
- demotes pattern/grammar/topic-only items from ordinary vocabulary samples;
- lets topic-only rows recover suitability when they match explicit topics.
- centers readiness on explicit `challenge_target` when present and uses
  proficiency as the fallback center.

### 5. Product Diagnostics

Update Options/admission sample output so it can show enough detail for
debugging without overwhelming normal users. The important internal fields are:

- `learner_difficulty`;
- `candidate_state`;
- `presentation_mode`;
- `difficulty_sources`;
- `suitability_reasons`;
- `challenge_target` and whether it was explicit or derived.

## Research Methodology Checkpoint, 2026-06-13

The first global sweeps and experimental piecewise contenders produced a useful
methodology finding: direct piecewise formulas inside the sweep are good as a
prototype, but they are not the best primary research loop.

Observed evidence:

- The old local-best target-curve formula still has the highest reviewed
  balanced score, but it is dominated by `old_jlpt_kanji` and has visible
  blotches in ordinary sample review.
- The full all-signal `0.10` frequency-forced sweep produced healthier linear
  formulas, but the best balanced contender did not beat the old local-best
  score and still had weak upper-tail behavior.
- The first smooth piecewise prototype improved numeric MAE strongly
  (`piecewise_pedagogy_mid_visual_tail_v1`, MAE `0.119444`) but did not beat
  the old local-best balanced score and weakened beginner-core alignment.
- Per-sample diagnostics are now necessary. A scalar score alone hides whether
  a placement came from frequency, old-JLPT/kanji signals, visual complexity,
  name/proper-noun risk, or a piecewise section boundary.

Current artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_contender_samples_en_ja_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_piecewise_presets_en_ja_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_piecewise_review_en_ja_latest.md`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_latest.{csv,md}`

### Improved Research Loop

For serious piecewise research, prefer an offline score-matrix optimizer:

1. Sweep ordinary linear formulas first.
2. Persist a score matrix:
   - rows: deduped vocabulary candidates plus reviewed calibration rows;
   - columns: raw formula scores for each retained formula/expert;
   - metadata: lemma, reading, POS, candidate state, problem class, core rank,
     frequency proxy, component signal values, and source/provenance fields.
3. Search piecewise combinations after the sweep:
   - split points;
   - hard versus smooth transitions;
   - formula/expert choice per segment;
   - objective weights for beginner, middle, upper-tail, pairwise, MAE, bucket,
     and sample-quality metrics.
4. Recompute the combined raw score for each proposed piecewise model.
5. Re-run global target-curve normalization on the combined raw score.
6. Score the normalized result against calibration metrics.
7. Generate band-strict samples with diagnostics for the best few contenders.

This is better than putting every piecewise option directly into the huge sweep
because split search and formula selection can be explored cheaply after the
expensive source scoring is done. It also makes the research more transparent:
each segment can say which formula/expert it selected and why.

### Planned Huge-Sweep Artifact Contract

The next huge sweep should use the compact-plus-matrix trace rather than only
the human summary artifact. This avoids losing piecewise research options while
keeping storage controlled:

- Main report JSON/Markdown: leaderboards and retained detailed contenders for
  human review.
- Trace JSON: all evaluated variant definitions, weights, aggregate scores, and
  calibration metric summaries.
- Calibration prediction matrix NPZ: every evaluated variant's observed
  difficulty for every calibration label.
- Component matrix NPZ: the reusable deduped normalization-population signal
  matrix, with component names, row identities, lemmas, readings, candidate
  states, problem classes, current values, frequency values, and target-curve
  positions.

Use this command for the next full `0.10` all-signal run:

```bash
python3 scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py \
  --variant-mode grid \
  --grid-step 0.10 \
  --grid-signals frequency,jmdict_priority,kanji_grade,old_jlpt_kanji,stroke_count,kanjivg_visual_complexity,script_complexity,jmdict_non_vocab_risk,jmnedict_name_risk,kanji_frequency_rank \
  --grid-min-weights frequency=0.20 \
  --calibration-only \
  --json-out docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_latest.json \
  --markdown-out docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_latest.md \
  --trace-json-out docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_trace_latest.json \
  --trace-calibration-matrix-out docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_calibration_matrix_latest.npz \
  --component-matrix-out docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_component_matrix_latest.npz
```

The full per-variant-by-corpus score matrix remains optional. The component
matrix can recompute linear and piecewise candidates without preserving every
variant's 74k-row score vector. If offline recomputation becomes the bottleneck,
add a separate one-off full-matrix flag rather than making the default huge
sweep artifact tens of GiB.

### Piecewise Search Result, 2026-06-13

The first post-sweep piecewise search is implemented in
`scripts/testing/srs_learner_difficulty_piecewise_search_en_ja.py` and writes:

- `docs/test_outputs/srs_learner_difficulty_piecewise_search_en_ja_latest.json`
- `docs/test_outputs/srs_learner_difficulty_piecewise_search_en_ja_latest.md`

The search uses a compact two-stage strategy:

1. Select a diverse expert pool from the huge-sweep trace leaderboards.
2. Preselect hard frequency-anchored two- and three-segment combinations using
   calibration-matrix predictions.
3. Recompute the retained candidates exactly from raw component signals over
   the full 74,128-row normalization population.
4. Apply global target-curve normalization and score against the calibration
   rubric.

Earlier best exact candidate before lexical-origin/POS gates:

- Candidate:
  `pw3_b45_85__grid_s10_cnone_015229__grid_s10_cnone_015229__grid_s10_c080_056563`
- Boundaries: `0.45`, `0.85`
- Early/middle expert:
  `grid_s10_cnone_015229`
  (`frequency=0.3, kanji_grade=0.1, kanjivg_visual_complexity=0.1,
  old_jlpt_kanji=0.1, script_complexity=0.3, stroke_count=0.1`)
- Upper-tail expert:
  `grid_s10_c080_056563`
  (`frequency=0.2, jmdict_priority=0.1, jmnedict_name_risk=0.1,
  kanji_frequency_rank=0.3, old_jlpt_kanji=0.3`, cap `0.08`)
- Balanced score: `0.831752`
- MAE: `0.201906`
- Bucket accuracy: `0.689024`
- Pairwise accuracy: `0.872411`
- Beginner core pass rate: `0.979592`
- High-tail pass rate: `0.363636`

This improves the scalar balanced score over the best single formula from the
same full sweep (`0.815733`) and improves pairwise ordering materially. It does
not solve all sample-quality concerns: top candidate mismatches still include
too-low intermediate items such as `的/まと`, `自民/じみん`, `憲法/けんぽう`,
`避難/ひなん`, `過疎/かそ`, and `宿る/やどる`; top-tail samples also surface
many katakana/domain words, so sample review and candidate-classification work
remain necessary before treating this as product-ready.

Important guardrail: target-curve normalization is global and rank-based. Do
not combine already-normalized formula outputs and treat that as a valid
piecewise difficulty result. The correct sequence is:

```text
raw formula columns -> piecewise raw score -> global target-curve normalization -> calibration/sample scoring
```

### Model-Tree Search Result, 2026-06-13

The next research step is implemented in
`scripts/testing/srs_learner_difficulty_model_tree_search_en_ja.py` and writes:

- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_latest.md`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_latest.csv`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_latest.md`

This search generalizes the frequency-only piecewise idea into a shallow hard
gated model tree:

```text
leaf = split(existing component signals)
raw_score(row) = expert_formula_for_leaf(row)
final_difficulty = global_target_curve_normalize(raw_score)
```

Current successful research setting:

- Expert pool: `24` formulas selected from the huge-sweep trace.
- Split specs: `60`, including quantile splits plus explicit frequency
  boundaries `0.25`, `0.35`, `0.45`, `0.55`, `0.65`, `0.75`, `0.80`, `0.85`.
- Leaf experts: top `4` local specialists plus top `4` global experts. The
  global fallback is important: the strong `grid_s10_cnone_015229` expert was
  not locally top-ranked in tiny frequency leaves, so narrower pruning missed
  known-good candidates.
- Approximate retain limit: `1000`.
- Exact evaluation limit: `1000`.
- Detailed calibration-row output: top `20` exact candidates by default.
- Runtime behavior changed: `false`; this is still research output only.

The generated JSON attaches full per-calibration-label diagnostics to the top
detailed candidates. The flat CSV is the preferred artifact for sorting and
filtering reviewed labels because each row includes candidate rank, expected
and observed difficulty, bucket status, direction, leaf/expert assignment,
candidate state, problem class, core rank, frequency, and component signal
values. The Markdown calibration-rows artifact shows a compact candidate
summary, mismatch tables, largest numeric errors, and the full best-candidate
calibration table.

Current best exact candidate:

- Candidate:
  `tree2__root_kanjivg_visual_complexity<=0.3854:ml__right_kanji_grade<=0.2600:ml__grid_s10_cnone_015229__grid_s10_c150_108026__grid_s10_cnone_005593`
- Root split: `kanjivg_visual_complexity <= 0.3854`, missing values left.
- Right-child split: `kanji_grade <= 0.2600`, missing values left.
- Leaf experts:
  - leaf `0`: `grid_s10_cnone_015229`, `37,107` rows;
  - leaf `1`: `grid_s10_c150_108026`, `7,082` rows;
  - leaf `2`: `grid_s10_cnone_005593`, `29,939` rows.
- Balanced score: `0.871507`.
- MAE: `0.133817`.
- Bucket accuracy: `0.810976`.
- Pairwise accuracy: `0.857577`.
- Beginner core pass rate: `0.897959`.
- High-tail pass rate: `0.636364`.

This is a material improvement over both the best single formula from the same
sweep (`0.815733`) and the first frequency-piecewise candidate (`0.831752`).
It also produces less katakana-dominated top-tail samples than the first
frequency-piecewise result.

Caveats:

- It is still calibrated against a relatively small reviewed set, so the
  `0.871507` score should be treated as a research lead, not product acceptance.
- The best tree still misplaces several visible beginner/intermediate anchors:
  `猫`, `胸`, and `傘` are too high; `自民`, `人民`, `山中`, and some policy/news
  words are too low.
- The model-tree result suggests the existing signals contain useful structure,
  especially visual complexity plus kanji grade, but it does not replace
  candidate-state/suitability work.
- Future sweeps should add holdout or cross-validation once the calibration set
  grows enough. Until then, sample review remains part of the acceptance loop.
- The current default exact run is still expensive because it recomputes and
  target-curve-normalizes full 74,128-row vectors for up to 1,000 candidates.
  The detail rows are report-only and are attached after ranking; they are not
  the main runtime cost.

### Lexical-Origin/POS Gate Result, 2026-06-13

The next experiment exposed BCCWJ lexical-origin (`wtype`) and POS-derived
components to the learner-difficulty research matrix. This directly addresses
the `猫`/`胸`/`傘` problem: kanji-character difficulty is much less reliable for
native Japanese words (`和`) than for Sino-Japanese compounds (`漢`).

Implementation/research changes:

- `scripts/testing/srs_learner_difficulty_audit_en_ja.py` now preserves BCCWJ
  `wtype` from the normalized word package.
- `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py` now exposes
  research components including `wtype_kango_risk`, `wtype_wago_ease`,
  `wtype_non_wago_risk`, `wtype_gairaigo_risk`, POS gates, and kango/wago
  interactions with old-JLPT, kanji-grade, and visual-complexity signals.
- The target-curve/component matrix now retains split-only components that are
  present in the normalization population, even when a formula does not weight
  them. This lets model-tree gates use `wtype`/POS without forcing them into
  linear formulas.
- `scripts/testing/srs_learner_difficulty_model_tree_search_en_ja.py` now
  supports `--expert-exclude-signals` for research runs that keep a signal
  available for gates while excluding formulas that directly weight it.
- Exact model-tree evaluation now ranks candidates before attaching expensive
  full-corpus leaf summaries and band samples, avoiding duplicate detail work.

New artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_wtype_component_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_wtype_manual_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_wtype_manual_latest.{csv,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_wtype_manual_no_visual_expert_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_kango_interaction_s020_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_kango_interaction_s020_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_combined_old_kango_latest.{json,md}`

Current best research candidate:

- Candidate:
  `tree2__root_wtype_kango_risk<=0.5000:ml__right_frequency<=0.8500:mr__grid_s10_cnone_015229__grid_s10_cnone_005618__grid_s10_c080_056563`
- Root split: `wtype_kango_risk <= 0.5000`, missing values left.
- Right-child split: `frequency <= 0.8500`, missing values right.
- Leaf experts:
  - leaf `0`: `grid_s10_cnone_015229`;
  - leaf `1`: `grid_s10_cnone_005618`;
  - leaf `2`: `grid_s10_c080_056563`.
- Balanced score: `0.905333`.
- MAE: `0.110845`.
- Bucket accuracy: `0.841463`.
- Pairwise accuracy: `0.881887`.
- Beginner core pass rate: `0.979592`.
- High-tail pass rate: `0.818182`.

Compared with the earlier visual/grade tree, this is a material improvement:
balanced score `0.905333` vs `0.871507`, bucket accuracy `0.841463` vs
`0.810976`, pairwise accuracy `0.881887` vs `0.857577`, beginner-core pass rate
`0.979592` vs `0.897959`, and high-tail pass rate `0.818182` vs `0.636364`.
It also moves the reviewed `猫`, `胸`, `傘`, and `部屋` rows out of the obvious
too-hard failure pattern.

Interpretation:

- `wtype_kango_risk` is a real signal. The winning tree selects it as the root
  gate, which supports the hypothesis that kanji-level difficulty should be
  interpreted differently for `漢` words versus `和`/non-kango words.
- A blunt wtype/POS-only focused search helps beginner anchors but over-demotes
  several harder rows. The better result comes from using lexical origin as a
  gate while keeping strong old formula experts available.
- Excluding visual/stroke from leaf experts is not yet a win. The no-visual
  expert run keeps the beginner fixes but drops bucket accuracy sharply, which
  means those components are still doing useful work or need a better
  replacement formula family.
- A coarse kango-interaction formula sweep confirms the interaction signal is
  useful, especially for `猫`/`人民`/`山中`-style rows, but the coarse
  interaction-only and combined expert-pool runs do not beat the wtype-gated
  old-expert tree yet.

Remaining research gaps:

- Add a finer local kango-interaction search around the coarse winners instead
  of a full `0.10` grid; the naive full `0.10` interaction grid is too slow
  because target-curve scoring sorts the 74,128-row population for every
  variant.
- Add or review calibration labels for the current remaining mismatch families:
  `人民`/`山中` too low, `我が` too low, and advanced wago/literary rows such as
  `侘び` too low under the best wtype gate.
- Consider expert-pool combination/search improvements. The combined old+kango
  run did not beat the old-expert wtype tree, partly because expert selection
  and approximate pruning are still shallow.
- Treat this as research output only until sample review and SRS quality gates
  confirm product behavior.

### Conditional-Origin Signal Result, 2026-06-13

The next pass kept the lexical-origin finding but made the interpretation more
conditional. Instead of treating `和` and `漢` as direct hard/easy signals, the
new components ask narrower questions:

- how much kanji burden appears in kango rows;
- whether a kango row is also low-priority/uncommon;
- whether a wago row is rare and has a written-form burden;
- whether written-form burden should matter independently of lexical origin.

This pass also added the reviewed rows from the current discussion to the
calibration set so future sweeps keep them visible: `一揆`, `後年`, `猯`,
`防止`, `保証`, `真理`, `凶悪`, and the non-numeric tracking row `ザ`.

New artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_conditional_origin_s020_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_conditional_origin_s020_tight_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_conditional_origin_s020_tight_latest.{csv,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_conditional_origin_local_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_conditional_origin_local_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_conditional_origin_local_s010_latest.{csv,md}`

Comparison guardrail:

- The previous `wtype` best scored `0.905333` balanced on the older
  206-label calibration set.
- The conditional-origin experiments use the expanded 214-label calibration
  set. Their scores should be compared against each other directly, but not
  directly against the old 206-label score.
- On the expanded 214-label set before the `的/まと` retarget, the first
  conditional-origin tree scored `0.899691` balanced and the refined local
  `0.10` tree scored `0.902968` balanced.
- After reviewing `的/まと` as acceptable near `0.37` and retargeting it to
  `0.40` beginner, the same conditional-origin local family scored `0.903683`
  balanced.

Current updated-label best research candidate:

- Candidate:
  `tree2__root_kango_common_priority_risk<=0.4500:mr__left_frequency<=0.7500:mr__grid_s10_cnone_000315__grid_s10_cnone_000343__grid_s10_cnone_000199`
- Root split: `kango_common_priority_risk <= 0.4500`, missing values right.
- Left-child split: `frequency <= 0.7500`, missing values right.
- Leaf experts:
  - leaf `0`: `grid_s10_cnone_000315`;
  - leaf `1`: `grid_s10_cnone_000343`;
  - leaf `2`: `grid_s10_cnone_000199`.
- Balanced score: `0.903683`.
- MAE: `0.119520`.
- Bucket accuracy: `0.824561`.
- Pairwise accuracy: `0.888423`.
- Beginner core pass rate: `0.979592`.
- High-tail pass rate: `0.727273`.

Tracked-row behavior for the current updated-label best:

| Row | Expected | Observed | Status |
| --- | ---: | ---: | --- |
| `一揆/いっき` | `0.58` | `0.552930` | match |
| `後年/こうねん` | `0.56` | `0.604928` | match |
| `猯/まみ` | `0.88` | `0.544493` | mismatch, too low |
| `防止/ぼうし` | `0.42` | `0.240409` | match, still numerically low |
| `保証/ほしょう` | `0.50` | `0.541207` | match |
| `真理/しんり` | `0.46` | `0.414699` | match |
| `凶悪/きょうあく` | `0.62` | `0.673260` | match |
| `的/まと` | `0.40` | `0.245468` | match |
| `ザ/ざ` | tracking only | `0.195758` | not scored |

Interpretation:

- The conditional-origin family is a real improvement over the first
  conditional tree on the expanded labels, especially for the discussed common
  kango rows (`防止`, `保証`, `真理`, `凶悪`) and intuitive/formal kango rows
  (`一揆`, `後年`).
- The earlier `猫`/`胸` failure remains fixed: `猫/ねこ` is `0.107799` and
  `胸/むね` is `0.097720` under the retargeted updated-label best.
- `的/まと` is no longer considered a failure at the lower reviewed target. The
  main remaining weakness has shifted toward advanced/literary wago or uncommon
  reading rows: `猯` and `侘び` are still too low. This suggests the next signal
  work should focus on rare wago/literary evidence, not on bluntly increasing
  all kanji burden.
- Some topic/proper-name rows (`自民`, `国連`, `北朝鮮`, `ＮＨＫ`) remain too low
  under scalar learner difficulty. That may need a topic-aware admission lane
  or candidate-state treatment rather than another global scalar formula.

### Rare Written-Wago Probe, 2026-06-13

The next probe exposed narrower rare-written-wago components:

- `max_kanji_burden` and `max_written_form_burden`;
- separate JMDict lexical gates for `marked_usage`, `kana_preferred`, and
  register marking;
- `rare_wago_max_kanji_burden`, `rare_wago_max_written_burden`,
  `rare_wago_marked_usage_risk`, and `rare_wago_obscure_written_risk`.

The first implementation treated `marked_usage` too broadly: `的/まと` also has
marked/register metadata, so a direct marked-usage interaction pushed in the
wrong direction. The final probe dampens marked-usage risk by JMDict priority
rarity so common/high-priority marked rows do not look like rare obscure rows.

Artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_rare_written_wago_s020_refined_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_rare_written_wago_s020_refined_focused_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_rare_written_wago_s020_refined_focused_latest.{csv,md}`
- Control rerun:
  `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_conditional_origin_local_s010_retargeted_latest.{json,md}`

Result:

- Retargeted conditional-origin control: balanced `0.903683`, MAE `0.119520`,
  bucket `0.824561`, pairwise `0.888423`.
- Refined rare-written-wago focused tree: balanced `0.900096`, MAE `0.142824`,
  bucket `0.789474`, pairwise `0.885481`.
- The rare-written-wago probe improves the specific rare-wago rows only
  modestly: `侘び/わび` moves from `0.566446` to `0.645851`, and `猯/まみ`
  moves from `0.544493` to `0.635651`. It still does not reach the reviewed
  target neighborhood for `猯` (`>=0.90` intuition, calibration currently
  `0.88`).

Conclusion:

- Keep the new components available for future research; they are source-backed
  and have clear semantics.
- Do not promote the rare-written-wago probe as the preferred candidate. It is a
  sidegrade/regression overall despite slightly improving `猯` and `侘び`.
- The remaining `猯`/`侘び` gap likely needs a stronger external pedagogical or
  register/literary rarity signal, or an explicit treatment of uncommon written
  forms beyond the current BCCWJ/JMDict/KANJIDIC2/KanjiVG components.

### Missing-Curriculum Rare-Wago Probe, 2026-06-14

Follow-up review showed that `max_kanji_burden` was not a pure visual-complexity
signal. It mixed old JLPT, school-grade, KanjiVG visual complexity, and stroke
count using `max(...)`. That made covered kanji such as `的` receive a higher
`max_kanji_burden` than `猯`, even though `猯` is visually and pedagogically more
obscure. The actionable distinction was not visual shape alone; it was that
`猯` and `侘び` have KANJIDIC/KanjiVG shape evidence but no grade, no old JLPT
level, and no KANJIDIC frequency rank.

New source-backed components:

- `kanji_curriculum_burden`: grade/JLPT/kanji-frequency burden where present.
- `kanji_shape_burden` and `max_kanji_shape_burden`: visual/stroke burden
  separated from curriculum metadata.
- `kanji_curriculum_missing_risk`: fires when kanji shape evidence exists but
  curriculum/frequency metadata is absent.
- `rare_wago_missing_curriculum_risk`: rare native word plus missing kanji
  curriculum evidence.
- `rare_wago_missing_curriculum_shape_risk`: the same signal gated by shape
  burden.

Implementation notes:

- Japanese learner signal bundles now expose `grade_known_count`,
  `freq_known_count`, `old_jlpt_known_count`, and
  `curriculum_signal_known_count`.
- `JAPANESE_LEARNER_SIGNALS_VERSION` moved to `v6` so regenerated seed/sweep
  rows do not silently reuse the old bundle shape.
- `scripts/testing/srs_learner_difficulty_model_tree_search_en_ja.py` now
  supports `--tree-depth linear|stump|depth2` and `--max-split-specs` for
  progressive searches. The previous depth-2 enumeration was too expensive for
  interactive iteration when broad split spaces were used.

Artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_curriculum_missing_probe_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_curriculum_missing_local_s005_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_curriculum_kango_local_s005_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_curriculum_kango_stump_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_curriculum_kango_stump_latest.{csv,md}`
- constrained depth-2 control:
  `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_curriculum_kango_depth2_tiny_latest.{json,md}`

Best current candidate from this lane:

- Candidate:
  `stump__frequency<=0.8879:mr__grid_s20_cnone_000588__grid_s20_cnone_000224`
- Root split: `frequency <= 0.8879`, missing values right.
- Left/low-frequency-side expert: `grid_s20_cnone_000588`.
- Right/high-frequency-side expert: `grid_s20_cnone_000224`.
- Balanced score: `0.904509`.
- MAE: `0.110187`.
- Bucket accuracy: `0.824561`.
- Pairwise accuracy: `0.879707`.
- Beginner core pass rate: `0.959184`.
- High-tail pass rate: `0.727273`.

Tracked-row behavior versus the previous retargeted best:

| Row | Expected | Previous best | New stump | Status |
| --- | ---: | ---: | ---: | --- |
| `猫/ねこ` | `0.08` | `0.107799` | `0.124` | preserved, slightly high |
| `犬/いぬ` | `0.08` | `0.086233` | `0.052` | preserved, slightly low |
| `胸/むね` | `0.20` | `0.097720` | `0.116` | preserved, still low |
| `傘/かさ` | `0.20` | `0.254920` | `0.235` | preserved |
| `的/まと` | `0.40` | `0.245468` | `0.245` | unchanged, still low |
| `侘び/わび` | `0.82` | `0.566446` | `0.889` | gap closed |
| `猯/まみ` | `0.88` | `0.544493` | `0.882` | gap closed |
| `編纂/へんさん` | `0.84` | `0.770644` | `0.791` | slight improvement |
| `詭弁/きべん` | `0.90` | `0.756315` | `0.684` | regression |
| `防止/ぼうし` | `0.42` | `0.240409` | `0.277` | slight improvement, still low |
| `保証/ほしょう` | `0.50` | `0.541207` | `0.560` | acceptable high |
| `凶悪/きょうあく` | `0.62` | `0.673260` | `0.657` | preserved |

Interpretation:

- The missing-curriculum signal is real and product-relevant. It fixes the
  specific `猯`/`侘び` pattern without dragging common covered kanji like `猫`,
  `胸`, and `的` into the upper tail.
- The best shape found so far is still simple: a one-split model tree over
  frequency, with a different expert for the high-rarity side. This suggests
  the current polynomial/grid plus shallow decision-tree mechanism is
  sufficient for this stage.
- A constrained depth-2 control did not beat the stump candidate. It improved
  some numeric MAE/bucket behavior but overraised beginner rows and scored only
  `0.864169` balanced, so depth-2 should stay a later optimization lane.
- Remaining gaps are now narrower: `詭弁` regressed under the stump and
  `的`/`胸` remain numerically low. These look like calibration/model-family
  tradeoffs rather than evidence that we need a fully opaque nonlinear model.

### Piecewise Search Guardrails

- Use an independent split anchor first, probably `frequency_difficulty_proxy`.
  Avoid splitting by the final piecewise output because that is circular.
- Keep suitability/classification separate from scalar difficulty. Piecewise
  scoring may reduce some blotches, but it will not reliably solve bad
  standalone SRS candidates such as acronyms, source artifacts, grammar items,
  transparent numerals, or low-value named entities.
- Penalize excessive complexity:
  - too many segments;
  - sharp discontinuities at split boundaries;
  - tiny segments with unstable calibration evidence;
  - improvements that only raise one metric while visibly harming samples.
- Report per-segment metrics, not just global balanced score. A useful model
  should improve the section it claims to own.
- Keep an explicit holdout or review-only set once calibration grows large
  enough. The current reviewed set is still small, so sample review remains
  part of the acceptance loop.

### Research Questions To Discuss Before More Sweeps

- What should be the first split anchor: raw frequency, a pedagogical baseline,
  or an anchor blending frequency with old-JLPT/kanji grade?
- How much should early bands favor pedagogical/JLPT-style signals versus raw
  commonness?
- Should the upper tail be optimized for "hard but valuable vocabulary" rather
  than "rarest/densest dictionary rows"?
- Which blotches belong to candidate classification instead of difficulty
  scoring?
- Should objective weights differ from product acceptance priorities, for
  example prioritizing top-3 bucket placement or visible sample quality over
  exact numeric MAE?

## Full-Frontier Latency Plan

Removing the default `bootstrap_top_n=800` cap is the correct product behavior:
admission should see the full installed source frontier, then admit only the
requested active count. The cost is that en-ja currently rebuilds and scores
about `78,316` row-aware JMDict-filtered seed candidates for a normal
profile-bootstrap sample.
That is acceptable for backend research, but too slow for a polished Options
flow if it happens synchronously on every sample request.

The latency work should preserve the current selection behavior first, then
optimize the boundary around it:

1. Documented contract:
   - omitted/null `bootstrap_top_n` means all available source rows;
   - finite `bootstrap_top_n` remains a debug/research override;
   - cache hits must produce the same seed candidates as the uncached path for
     the same frequency DB, dictionary, POS overlay, stopwords, and seed config;
   - cache misses or invalid cache files fall back to the current uncached path,
     never to a smaller frontier.
2. First implementation slice:
   - add a local seed-frontier cache at the `build_seed_candidates(...)`
     boundary;
   - cache only normalized seed rows, not profile-specific scores;
   - include source freshness in the cache key/fingerprint;
   - write cache files atomically and ignore corrupt cache files.
3. Validation slice:
   - test cache miss, cache hit, invalidation, and corrupt-cache fallback;
   - run the SRS quality harness;
   - run the en-ja learner-difficulty audit to confirm the full-frontier
     metrics stay stable.
4. Second implementation slice, only if repeat latency remains visible:
   - build the seed-frontier cache automatically after source download/import;
   - surface cache preparation status in the GUI resource flow;
   - reuse the ready cache for Options sampling and helper initialization.
5. Third implementation slice, only if full scoring remains too slow:
   - add difficulty/topic indexes over the cached frontier;
   - score a focused subset for a specific profile/challenge request;
   - keep a fallback full-frontier scoring path for audits and correctness
     comparisons.

The first cache should deliberately avoid profile-dependent state. Profile
signals, topic boosts, readiness, active count, and sampling seed stay in
`profile_bootstrap` and selector code. The cache owns only the expensive,
repeatable source normalization:

- frequency row extraction and rank/frequency normalization;
- JMDict lemma filtering;
- stopword filtering;
- bootstrap surface normalization;
- POS normalization and POS overlay lookup;
- `word_package` construction;
- deterministic candidate classification;
- source topic column extraction.

Cache freshness inputs:

- cache schema version;
- seed classifier version;
- language pair;
- frequency DB path, size, and `mtime_ns`;
- effective seed config columns and sort mode;
- JMDict path, size, and `mtime_ns` when required;
- stopwords path, size, and `mtime_ns`, plus explicit stopword list hash when
  supplied directly;
- POS overlay path, size, and `mtime_ns`;
- source label and topic columns.

Non-goals for the first slice:

- no behavior change to admission results;
- no UI progress state yet;
- no precomputed profile scores;
- no new learner-difficulty source;
- no topic/difficulty narrowing index.

Implementation checkpoint, 2026-06-11:

- First slice implemented in `core/lexishift_core/srs/seed.py`.
- Cache filesystem, lock, status, and cleanup mechanics live in
  `core/lexishift_core/srs/seed_cache.py`.
- Helper-driven initialize, preview, refresh, rebalance, and rulegen-job flows
  pass `srs/cache/seed_frontiers/` as the cache directory.
- Focused cache coverage verifies cache hits, source invalidation,
  corrupt-cache fallback, and zero-suitability round-trips.
- Local installed en-ja timing probe with an isolated cache:
  first full-frontier build `10.379s`, repeat cache hit `2.497s`, raw
  normalized seed rows stable at `78,316`.
- Local installed en-ja profile-bootstrap timing with the same isolated cache:
  first profile-bootstrap initialization `17.201s`, repeat cached
  profile-bootstrap initialization `8.326s`, selected unique count stable at
  `72,758` persisted surface-lemma IDs.
- Logic-independent second slice implemented:
  - seed-frontier cache status, explicit prepare, stale-cache cleanup, and
    single-flight lock behavior live at the seed-cache boundary;
  - helper CLI/native-host can report or prepare the cache without running an
    admission sample;
  - the desktop resource flow starts a background seed-cache warmup after
    relevant language, frequency, or POS-overlay pack download/link/import;
  - blocked warmups such as `en-ja` frequency present but JMDict missing are
    reported as blocked, not treated as admission failures.
- Remaining latency work is now logic-dependent: faster profile scoring,
  difficulty/topic indexes, lazy package materialization, or staged scoring
  should wait until the learner-difficulty/admission-quality model is settled.

## Kanji-Go Qualitative Calibration Checkpoint, 2026-06-14

The 漢字でGO AtWiki list is useful as a qualitative external sanity check, but
should not be copied into repository fixtures or shipped data without explicit
license clearance. Current safe usage is:

- compare existing LexiShift calibration rows against the public list;
- use exact `テキスト` plus same-reading hits as strongest evidence;
- treat reading-only or same-kanji/different-reading hits as weak evidence;
- promote only independently reviewed LexiShift labels and rationales.

The first scratch lookup covered the visible level navigation from Lv.1 through
Lv.8. Lv.4-Lv.8 page coverage looked structurally complete; Lv.1-Lv.3 exposed
less parseable `テキスト` HTML than their page titles imply, so early-level
overlap is useful but not exhaustive.

Calibration labels adjusted from that review:

- `研究/けんきゅう`: `0.54 -> 0.36` after same-reading Lv.1 overlap.
- `情報/じょうほう`: kept at `0.36`, now explicitly documented as the low
  end of its range after same-reading Lv.1 overlap.
- `矛盾/むじゅん`: `0.66 -> 0.58` after same-reading Lv.2 overlap.
- `躊躇う/ためらう`: `0.72 -> 0.68`.
- `脆弱/ぜいじゃく`: `0.82 -> 0.74`.
- `編纂/へんさん`: `0.84 -> 0.80`.
- `攪拌/かくはん`: `0.86 -> 0.82`.
- `邂逅/かいこう`: `0.88 -> 0.84`.
- `饕餮/とうてつ`: `0.99 -> 0.95`, keeping the true ceiling open for
  material difficult even relative to this class.
- `猯/まみ`: `0.88 -> 0.92`, because the row combines extreme rarity,
  obscure written form, and a non-standard-feeling reading.

Implementation notes:

- KANJIDIC2 learner signals now carry per-character `ja_on`/`ja_kun` readings.
- The sweep layer exposes `non_standard_reading_risk`,
  `rare_non_standard_reading_risk`, and
  `rare_wago_non_standard_reading_risk`.
- The rarity-gated reading risk is intentionally zero below frequency-side
  difficulty `0.60`; this avoids over-penalizing common irregulars such as
  `今日/きょう`.
- The signal is not sufficient for all hard readings: `猯/まみ` is listed by
  KANJIDIC2, so the new mismatch signal does not fire there. Existing
  rare-wago/obscure-written and missing-curriculum signals remain the stronger
  path for that case.

Reading-probe artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_probe_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_probe_trace_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_probe_calibration_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_probe_component_matrix_latest.npz`

## Reading-Wago Sweep Checkpoint, 2026-06-14

The refreshed sweep after the 漢字でGO calibration changes used the enriched
kango/wago/rare-written signal set plus the new reading-risk signals. A broad
`0.10` grid over all enriched signals was interrupted after it remained
CPU-bound for more than ten minutes without writing artifacts. A local `0.05`
grid around the first coarse winners showed the same bottleneck. Both traces
were interrupted inside per-variant pairwise calibration scoring, so future
wide sweeps should add a cheaper first-pass metric mode or progress/checkpoint
output before expanding the grid again.

Completed coarse artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_wago_s020_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_wago_s020_trace_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_wago_s020_calibration_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_reading_wago_s020_component_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_reading_wago_stump_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_reading_wago_stump_latest.{csv,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_reading_wago_depth2_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_reading_wago_depth2_latest.{csv,md}`

Best completed flat formula:

- `grid_s05_cnone_000918`
- Balanced `0.896549`, MAE `0.129339`, bucket `0.826590`,
  pairwise `0.878619`, beginner core `0.960000`, high tail `0.727273`.
- Weights:
  `frequency=0.4, kango_common_priority_risk=0.2,
  kango_kanji_burden=0.2, max_written_form_burden=0.2`.

Best completed tree candidate after the `宿る`/`侘び` calibration review:

- `tree2__root_frequency<=0.8500:mr__right_kango_common_priority_risk<=0.2500:mr__grid_s05_cnone_000918__grid_s05_cnone_000847__grid_s05_cnone_000837`
- Balanced `0.909201`, MAE `0.126677`, bucket `0.842105`,
  pairwise `0.887563`, beginner core `0.979592`, high tail `0.727273`.
- Shape:
  - root split `frequency <= 0.8500`, missing right;
  - high-rarity side then splits on `kango_common_priority_risk <= 0.2500`;
  - leaf experts keep frequency, kango burden, max written burden, and a
    small written-form/rare-marked usage neighborhood.

Calibration changes in this rerun:

- `宿る/やどる` moved from an advanced/intermediate-style target to target
  `0.50`. It is a normal verb that should stay below clearly harder rows such
  as `躊躇う`, `侘び`, and formal/technical advanced vocabulary.
- `侘び/わび` moved from target `0.82` to `0.80`; it remains an advanced row,
  but the exact distinction inside the advanced band is intentionally not
  over-weighted.

Watchlist interpretation for the best depth-2 candidate:

- Preserved or improved: `猫/ねこ` `0.120278`, `胸/むね` `0.152388`,
  `的/まと` `0.267060`, `一揆/いっき` `0.632967`,
  `後年/こうねん` `0.577441`, `今日/きょう` `0.021847`,
  `編纂/へんさん` `0.844783`, `猯/まみ` `0.840931`,
  `宿る/やどる` `0.378474` versus target `0.50`.
- Still low: `侘び/わび` `0.570788` versus target `0.80`,
  `詭弁/きべん` `0.768789` versus target `0.90`,
  `埋め立て/うめたて` `0.282971` versus target `0.76`,
  `我が/わが` `0.070524` versus target `0.58`.
- The new reading signal is active where expected but did not dominate the
  winning formulas. It helps rows such as `一揆` and `侘び` expose risk, but
  the current best still chooses other aggregate tradeoffs. `猯/まみ` remains
  a rare-wago/obscure-written case rather than a KANJIDIC2 reading-mismatch
  case.

Current interpretation:

- The shallow tree mechanism is still worthwhile: the best depth-2 tree beats
  the best flat formula and the new-label stump result.
- The remaining hard cases look less like a missing broad signal and more like
  metric/model tradeoffs around literary wago, formal-common compounds, and
  topic/proper-name rows.
- `宿る` should no longer drive an advanced-word fix. It is now mostly useful as
  a regression guard against over-raising normal verbs while fixing rarer wago.
- Before another wide sweep, optimize the research harness: cache component
  scoring, split cheap aggregate metrics from expensive pairwise metrics, or
  add resumable/progress output.

Remaining failure signal read, after the `宿る` relabel:

- Literary/rare wago is partially exposed by current signals. `侘び/わび`
  remains too low (`0.570788` vs `0.80`) despite very high `frequency`
  difficulty (`0.975940`), `jmdict_priority` risk (`1.0`),
  `rare_non_standard_reading_risk` (`0.939850`),
  `rare_wago_non_standard_reading_risk` (`0.939850`), and
  `rare_wago_obscure_written_risk` (`0.975940`). This is the clearest case
  where a nonlinear rare-wago upper-tail term could help without moving
  `猫`, `胸`, or `的` much.
- `躊躇う/ためらう` is low but closer (`0.519103` vs `0.68`). Its strongest
  distinctive signal is written-form burden (`max_written_form_burden=0.95`,
  `written_form_burden=0.746528`) rather than reading rarity. A separate
  written-form/wago interaction may help, but `宿る` now guards against making
  every written wago verb advanced.
- `埋め立て/うめたて` and `我が/わが` are still too low, but they are weaker
  signal cases. `埋め立て` has only moderate rarity/written burden; `我が`
  has high old-JLPT and kanji-frequency proxies but no marked/register signal.
  These should not dominate the next model until we either add a better
  register/lexicalized-expression signal or mark them as lower-confidence
  calibration rows.
- Common/formal kango rows such as `技術`, `政治`, `公開`, `雇用`, `財政`,
  and `改善` remain too low. A pure additive kango or kanji burden boost is
  risky because `影響` and `特徴` are already slightly too high. The safer
  shape is a bounded midrange floor for common kango, not an upper-tail boost.
- Proper/topic names such as `自民`, `国連`, `北朝鮮`, and `ＮＨＫ` are scalar
  mismatches, but they may belong in topic-aware admission rather than the
  global difficulty curve. Keep them visible in reports, but avoid optimizing
  the whole scalar model around them until topic lanes are part of the metric.

Mathematical model ideas to try next:

- Rare-wago nonlinear upper-tail term:
  `rare_wago_tail = wago * sigmoid(frequency - 0.90) *
  max(rare_wago_obscure_written_risk, rare_non_standard_reading_risk,
  rare_wago_non_standard_reading_risk)`.
  This targets `侘び`/`猯`-style rows and should barely affect core words whose
  rarity and reading-risk terms are low.
- Written-wago burden term:
  `written_wago_tail = wago * sigmoid(frequency - 0.70) *
  sqrt(max_written_form_burden * written_form_burden)`.
  This targets `躊躇う`-style rows and needs a cap or threshold so normal verbs
  like `宿る` are not over-raised.
- Common-kango midrange floor:
  `score = max(score, bounded_floor(common_kango_signal))`, where the floor
  tops out around the intermediate band instead of adding directly to the
  scalar. This can lift `技術`/`政治`/`公開` without forcing `影響` and
  `特徴` further upward.
- Weighted objective lane:
  keep the current balanced metric, but add a focused reviewed-failure metric
  that up-weights high-confidence human-reviewed rows and reports topic/proper
  rows separately. This makes the sweep less likely to reject a model that
  fixes `侘び` because it makes a noisy name row slightly worse.

## Prototype Component Sweep: 2026-06-14

After review, `影響/えいきょう` was retargeted from `0.54` to `0.46`.
It is a common abstract suru noun and should stay on the lower side of
early-intermediate difficulty despite its written-form burden.

The next controlled experiment added three derived components:

- `rare_wago_tail_risk`: rare native-word upper-tail pressure gated by
  frequency difficulty and rare/obscure reading or written-form risks.
- `written_wago_tail_risk`: rare written native-word pressure using
  `sqrt(max_written_form_burden * written_form_burden)`.
- `kango_mid_signal`: a scalar common-kango midrange signal using frequency,
  kango kanji burden, and uncommon-kanji burden.

The controlled prototype sweep wrote:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_trace_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_calibration_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_component_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_prototype_depth2_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_model_tree_calibration_rows_en_ja_prototype_depth2_latest.{csv,md}`

The prototype should not be promoted as the current winner. Its approximate
model-tree score looked slightly better, but exact evaluation did not beat the
refreshed reading/wago baseline:

| Candidate | Balanced | MAE Score | Bucket | Pairwise | Beginner Core | High Tail | Upper Tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Refreshed reading/wago depth-2 tree | `0.908729` | `0.872530` | `0.842105` | `0.886082` | `0.979592` | `0.727273` | `0.947368` |
| Prototype weighted-component depth-2/stump tree | `0.907466` | `0.867825` | `0.859649` | `0.886672` | `1.000000` | `0.727273` | `0.894737` |

The refreshed baseline remains:

`tree2__root_frequency<=0.8879:mr__right_kango_common_priority_risk<=0.2500:mr__grid_s05_cnone_000918__grid_s05_cnone_000847__grid_s05_cnone_000837`

The prototype is still useful diagnostically:

- `rare_wago_tail_risk` moves `侘び` in the right direction, but weighted
  averaging still leaves it too low.
- A linear `kango_mid_signal` improves some common/formal kango rows, but also
  over-raises already-sensitive rows such as `影響` and `特徴`.
- `技術`, `政治`, and `公開` remain too low even when the linear kango-mid
  signal is available, which suggests that the problem is not just missing a
  scalar component.

The next model-family experiment should therefore test nonlinear post-processing
or bounded floors, not simply another weighted-average signal:

- bounded common-kango floor that lifts only into the midrange and stops before
  pushing `影響`/`特徴` higher;
- nonlinear rare-wago tail transform that can lift `侘び`/`猯` without moving
  core wago rows;
- optional objective variants that report the current balanced metric alongside
  a high-confidence reviewed-failure metric.

## Model-Family Search: 2026-06-14

The next research pass added an exact full-corpus model-family search:

- Script:
  `scripts/testing/srs_learner_difficulty_model_family_search_en_ja.py`
- Outputs:
  `docs/test_outputs/srs_learner_difficulty_model_family_search_en_ja_latest.{json,md}`
- Calibration rows:
  `docs/test_outputs/srs_learner_difficulty_model_family_calibration_rows_en_ja_latest.{csv,md}`

The search reuses the cached prototype trace/component matrices and evaluates
each candidate over the full `74128`-row normalization population before applying
the global target curve. This keeps the experiment exact without requiring a new
source-data rebuild.

Model families covered in the first run:

- linear expert baselines from the existing grid trace;
- bounded floors;
- hinge/ramp boosts;
- combined floors;
- soft mixtures of experts.

Run shape:

- trace variants available: `64350`;
- expert pool: `36`;
- evaluated candidates: `5000`;
- calibration labels: `214`;
- reviewed-focus labels: `15` human-reviewed failure/guard rows.

Best aggregate candidate:

`boost__grid_s10_cnone_010023__written_wago_tail_risk_t20_s10`

| Candidate | Balanced | MAE | Bucket | Pairwise | Focus | Beginner Core | High Tail | Upper Tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Refreshed reading/wago baseline | `0.908729` | `0.127470` | `0.842105` | `0.886082` | not recorded | `0.979592` | `0.727273` | `0.947368` |
| Best model-family aggregate | `0.911676` | `0.113554` | `0.865497` | `0.882180` | `0.786491` | `0.979592` | `0.727273` | `0.947368` |

This is a real aggregate improvement over the refreshed baseline: lower MAE and
better bucket accuracy. It is not a clean promotion yet because pairwise order
regresses slightly, and the reviewed-focus failures remain weak.

Best reviewed-focus candidate:

`floors__grid_s10_cnone_003480__kango_mid_m35_f35_65__rare_wago_m50_f80_98__written_wago_m30_f60_85`

| Candidate | Balanced | MAE | Bucket | Pairwise | Focus | Beginner Core | High Tail | Upper Tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Best reviewed-focus candidate | `0.801613` | `0.116305` | `0.748538` | `0.877320` | `0.876075` | `0.979592` | `0.000000` | `0.578947` |

This candidate proves the mechanism can work on the rows we were worried about:

- `侘び/わび`: `0.846658` vs target `0.80`;
- `猯/まみ`: `0.937879` vs target `0.92`;
- `技術/ぎじゅつ`: `0.574802` vs target `0.58`;
- `政治/せいじ`: `0.580223` vs target `0.56`;
- `公開/こうかい`: `0.579212` vs target `0.58`;
- `躊躇う/ためらう`: `0.740186` vs target `0.68`.

But it is too aggressive globally: high-tail and upper-tail segment scores
collapse, and the aggregate balanced score falls far below the baseline. Do not
promote this candidate. Treat it as evidence that bounded floors are expressive
enough, but the search needs constraints or a multi-objective selection step.

Best pairwise-order candidate:

`boost__grid_s10_cnone_008869__written_wago_tail_risk_t20_s28`

- Pairwise order: `0.894772`, better than the baseline `0.886082`.
- Balanced score: `0.866345`, too low for default promotion.

Conclusion:

- The model-family suite found useful model shapes.
- Simple balanced ranking prefers a mild written-wago boost.
- Reviewed-focus ranking prefers combined floors that fix the targeted failures
  but damage global segment quality.
- Pairwise ranking prefers a different high-ordering candidate that is not good
  enough on bucket/segment balance.

The next search should not simply add more unconstrained candidates. It should
perform a constrained or Pareto selection:

- require baseline-or-better beginner/high-tail/upper-tail guardrails;
- require pairwise no worse than a small tolerance from baseline;
- then maximize balanced score and reviewed-focus score;
- report the Pareto frontier rather than one raw winner.

## Model-Family Meta Search: 2026-06-15

The constrained/Pareto follow-up is implemented as a research harness:

- Script:
  `scripts/testing/srs_learner_difficulty_model_family_meta_search_en_ja.py`
- Outputs:
  `docs/test_outputs/srs_learner_difficulty_model_family_meta_search_en_ja_latest.{json,md}`
- Calibration rows:
  `docs/test_outputs/srs_learner_difficulty_model_family_meta_calibration_rows_en_ja_latest.{csv,md}`

The harness selects model-family candidates from the exact leaderboards, tries
linear, stump, and depth-2 hard signal-gated blends, then recomputes the exact
full-corpus raw score before applying the global target curve. The exact stage
always keeps standalone family candidates as anchors, so a hard-gated blend only
wins if it actually improves on the known global contenders.

Run shape:

- selected family candidates: `48`;
- split specs: `32`;
- approximate retained: `1500`;
- exact evaluated: `240`;
- normalization population: `74128`;
- calibration labels: `214`.

Best constrained result:

`linear__boost__grid_s10_cnone_010023__written_wago_tail_risk_t20_s10`

| Candidate | Balanced | MAE | Bucket | Pairwise | Focus | Beginner Core | High Tail | Upper Tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Refreshed reading/wago baseline | `0.908729` | `0.127470` | `0.842105` | `0.886082` | not recorded | `0.979592` | `0.727273` | `0.947368` |
| Best constrained meta result | `0.911676` | `0.113554` | `0.865497` | `0.882180` | `0.786491` | `0.979592` | `0.727273` | `0.947368` |

This is the same mild written-wago boost found by the model-family aggregate
search. It passes the current baseline guardrails and improves balanced score,
MAE, and bucket accuracy. It is still not a complete solution for the focused
failure rows:

- `侘び/わび`: target `0.80`, observed `0.542132`;
- `猯/まみ`: target `0.92`, observed `0.510575`;
- `影響/えいきょう`: target `0.46`, observed `0.622062`;
- `埋め立て/うめたて`: target `0.76`, observed `0.268930`;
- `我が/わが`: target `0.58`, observed `0.075084`.

The focused candidates that fix `侘び` and `猯` still exist, for example the
combined-floor family around ranks `233+`, but they are globally too expensive:
they repair rare wago rows while over-moving common learner words and damaging
bucket/segment balance. The hard-gated stump/depth-2 meta search did not find a
clean way to isolate those benefits. That suggests the next mechanism should be
softer and more localized than the current hard tree, or should use stronger
input signals rather than reusing the same signals with more gates.

Current interpretation:

- A mild global written-wago boost is the best safe candidate so far.
- Hard-gated meta blending is useful as a falsification/comparison tool, but it
  did not produce a better segmented winner in this pass.
- The remaining `侘び`/`猯`/`我が`/`埋め立て` issues look like signal/model gaps,
  not just optimizer-search gaps.
- Before default promotion, inspect sample bands for the constrained winner and
  decide whether the small pairwise regression is acceptable for product use.

## Residual-Gate Research Options: 2026-06-16

The latest residual-gate audit makes the next research choice clearer:

- Script:
  `scripts/testing/srs_learner_difficulty_residual_gate_audit_en_ja.py`
- Outputs:
  `docs/test_outputs/srs_learner_difficulty_residual_gate_audit_en_ja_latest.{json,md}`
- Related curve search:
  `docs/test_outputs/srs_learner_difficulty_curve_search_en_ja_latest.{json,md}`

The mathematical shape we want is still simple:

```text
f_new(x) = f_base(x) + c(x)
```

`c(x)` should apply a bounded correction to a systematic failure region and
stay near zero elsewhere. This is only valid if the failure region can be
identified from observable product-time features. It is not enough to define
the region as "rows the current model got wrong," because that would not be a
runtime signal and would overfit reviewed labels.

Current evidence:

- Broader smooth-curve, RBF, soft-gated, piecewise, model-tree, model-family,
  and meta-search forms have explored a substantial amount of model space with
  the current source-backed signals.
- Perfect cluster detection would be valuable. The audit's holdout-oracle
  probes reduce cluster MAE by about `0.14` to `0.35` and total MAE by about
  `0.011` to `0.036`, depending on the cluster and base candidate.
- The current observable gates are not precise enough. The best average
  calibration-fit bounded corrections all worsened holdout MAE, including
  `wago_written_or_rare_moderate` (`+0.001877`), `wago_written_or_rare_any`
  (`+0.005007`), `non_standard_reading_any` (`+0.006035`), `kango_priority`
  (`+0.008374`), and `kango_commonish_mid` (`+0.028779`).
- The main remaining holdout clusters are:
  - `common_kango_too_high`: mean count `10.0`;
  - `written_wago_too_high`: mean count `5.5`;
  - `beginner_easy_too_high`: mean count `3.75`.
- Obscure-reading and upper-tail too-low clusters are smaller in this audit,
  but still matter because rows such as `猯`, `侘び`, and non-standard readings
  are visible product-quality failures when they occur.

The next options should therefore be evaluated as signal-identification work
first, and model-correction work second.

### Option 1: Outside Pedagogical Source

Goal: add a word-level learner-order or pedagogical-commonness signal that the
current source stack does not provide cleanly.

Candidate source types:

- redistributable JLPT vocabulary or learner-level lists;
- textbook or graded-reader headword/order lists, if license/provenance allows;
- learner-dictionary level tags;
- school/learner core vocabulary lists;
- other public pedagogical lists with clean redistribution or manual-local
  import terms.

Expected value:

- Highest likely value if a source is clean, because it directly addresses the
  difference between "rare in corpus" and "late for learners."
- Could separate easy learner staples such as `猫`, `胸`, `紅茶`, `卵焼き`,
  and ordinary compounds from genuinely obscure or literary words.
- Could provide the missing signal needed to lower common/transparent items
  without damaging upper-tail rows.

Risks and requirements:

- License and provenance are the main blocker. Product use must be classified
  as `auto-download`, `manual-local`, or rejected before wiring.
- Many community lists may be derived from copyrighted or unclear sources.
- A level tag is not automatically a scalar difficulty. The formula still needs
  normalization and guardrails.

Success criteria:

- Improves gate precision/lift for `beginner_easy_too_high` and
  `common_kango_too_high` without over-moving non-cluster rows.
- Improves holdout and cross-validation metrics, not just calibration labels.
- Can be used in product without redistributing unclear third-party data.

Current implementation hook:

- `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py` can now sweep
  explicit word-level JLPT difficulty mappings with `--jlpt-vocab-curve-grid`.
  The old fixed interpretation remains the default when the flag is omitted:
  `N5=0.08`, `N4=0.22`, `N3=0.42`, `N2=0.65`, `N1=0.85`.
- The same script can sweep `--jlpt-kanji-dampening-strengths`. This is a
  targeted guard against cases where a direct JLPT vocabulary anchor says a
  word is easier than its kanji-burden components imply. For each dampened
  kanji/written-form component `c`, JLPT anchor `a`, and strength `s`, the
  transformed value is:

  ```text
  c' = c - s * max(0, c - a)
  ```

  This only pulls an over-high kanji component down toward the direct word-level
  anchor. It does not push low kanji components upward, so it is intended to
  address `影響`-like "JLPT says lower than kanji burden" cases without making
  obscure words easier merely because their kanji look simple.
- Reports and compact traces include the active JLPT curve and dampening
  strength so retained candidates can be audited after large sweeps.
- The other installed pedagogical source currently exposes direct components:
  `lesson_vocab_difficulty` and `lesson_vocab_beginner_core`. It does not yet
  have a sweepable mapping layer because the source semantics need a separate
  calibration decision before we treat lesson/order tags as a scalar curve.

### Option 2: Derived Signal From Existing Data

Goal: derive a better discriminator from data we already have or already plan
to install, without adding a new legal surface.

Candidate derived signals:

- transparent compound/common constituent score from JMDict, KANJIDIC2, BCCWJ,
  and script analysis;
- ordinary-kango/common-kango signal that distinguishes high-utility compounds
  from formal or recondite compounds;
- written-wago tail signal that separates common written native words from
  literary, rare, or obscure readings;
- reading-specific rarity using reading, form, POS, and priority evidence;
- lexicalized-expression or register markers from dictionary metadata, only
  when the gate is precise enough.

Expected value:

- Product-friendly because it reuses already-approved source lanes.
- Good for interpretable incremental improvements.
- May be enough for common-kango and transparent compound issues if the right
  feature interaction is present.

Risks and requirements:

- Existing residual-gate probes suggest current gates are too broad. A derived
  signal must prove better separability before becoming another model knob.
- Weak derived gates can make global metrics worse even when they fix a few
  memorable examples.
- This lane may not solve learner-order gaps if the missing fact is genuinely
  external pedagogy rather than morphology.

Success criteria:

- Gate precision/recall/lift beats current gates on holdout.
- Bounded correction probes improve holdout MAE or improve a constrained
  Pareto objective without regressing beginner, high-tail, and pairwise guards.
- Reports preserve examples that motivated the signal, especially `侘び`,
  `猯`, `胸`, `猫`, common kango, and transparent/easy compounds.

### Option 3: More Reviewed Calibration And Holdout Data

Goal: make the evaluation less noisy and reduce overfitting risk.

Needed label coverage:

- beginner staples and beginner compounds;
- ordinary common kango;
- formal/common kango;
- rare or literary wago;
- non-standard readings;
- transparent compounds and compositional items;
- proper/topic/name rows kept separate from global difficulty;
- normal controls around every contested band.

Expected value:

- Improves confidence in sweeps and makes failures easier to classify.
- Allows cross-validation and holdout metrics to represent the product problem
  more honestly.
- Helps decide whether rows such as `詭弁`, `猯`, `侘び`, `宿る`, `影響`, and
  `中国` are true failures or reviewer-specific intuition.

Risks and requirements:

- More labels do not create a new runtime signal by themselves.
- Human labels can be inconsistent unless the target scale is explicit:
  `0.00` should mean first-lesson/simple core, and `1.00` should mean hard even
  for highly proficient learners or native speakers.
- Topic/proper rows should not silently distort the global scalar difficulty
  model if they actually belong in topic-aware admission.

Success criteria:

- Calibration and holdout contain enough type-balanced rows that a candidate
  can no longer win by overfitting a narrow set.
- The reports show separate metrics for numeric distance, bucket agreement,
  pairwise order, beginner core, high tail, and focused failure rows.

### Option 4: Human Or LLM Pedagogical Labels

Goal: expand reviewed evidence faster than manual row-by-row annotation.

Best use now:

- generate review candidates or preliminary target labels;
- create multiple independent label proposals for human reconciliation;
- add qualitative rationales that help identify missing signal families;
- expand test coverage, not product runtime data, until policy is settled.

Potential product use:

- A generated learner-difficulty overlay might eventually be product data, but
  that requires a separate policy and provenance decision. Treat generated
  per-word labels as a product artifact, not just code, if they are shipped.

Risks and requirements:

- LLM labels can be plausible but inconsistent, especially in middle bands.
- If prompts include source lists with restrictive licenses, generated outputs
  need review before redistribution.
- Model labels are not the source of truth. They should be audited against
  human-reviewed calibration and product sample quality.

Success criteria:

- Human review confirms that generated labels materially improve coverage.
- Adding the labels changes model selection in a way that improves holdout or
  independent review, not just the generated-label fit.
- Any shipped generated data has clean provenance and a documented policy.

### Recommended Research Sequence

1. Audit product-compatible outside pedagogical sources first. Classify each
   candidate as `auto-download`, `manual-local`, or rejected.
2. In parallel, prototype one or two derived signals from existing data, but
   require residual-gate evidence before using them in a broad sweep.
3. Expand reviewed calibration/holdout rows around known failure clusters and
   keep topic/proper-name rows marked separately.
4. Run residual-gate audits for each new signal:
   - precision, recall, F1, and lift by cluster;
   - calibration-fit bounded correction on holdout;
   - non-cluster MAE/regression cost;
   - sample-band review for the best candidates.
5. Only after a signal proves separability, add it to the formula/model-family
   sweep and re-run constrained/Pareto selection.
6. Use LLM or human batch labeling as an evaluation accelerator, not as a
   replacement for source-signal work.

Promotion guardrails:

- A candidate must improve the targeted weak clusters without reducing
  beginner-core, high-tail, upper-tail, default-decision, or pairwise metrics
  beyond an explicit tolerance.
- Reports must keep calibration, holdout, cross-validation, and sample-band
  evidence separate.
- Runtime/default promotion remains blocked until source licensing, product
  data flow, and SRS quality gates are all clean.

## Review-Batch and Holdout Extension

Before the next sweep, generate review-only candidate rows rather than adding
untested labels directly into the accepted calibration set:

```bash
python3 scripts/testing/srs_learner_difficulty_review_batch_en_ja.py \
  --json-out docs/test_outputs/srs_learner_difficulty_review_batch_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_learner_difficulty_review_batch_en_ja_latest.md \
  --holdout-review-markdown-out docs/test_outputs/srs_learner_difficulty_holdout_review_en_ja.md \
  --active-review-markdown-out docs/test_outputs/srs_learner_difficulty_active_review_en_ja.md
```

This script is intentionally not a sweep. It reads the latest component matrix,
current calibration labels, and latest meta/model-family outputs, then writes
two same-sized candidate sets:

- `active_review_candidates`: rows likely to teach us something about current
  failure modes or uncertain areas, including model disagreement, rare wago
  tails, common-kango floors, beginner kanji guards, non-standard readings,
  proper/topic boundaries, gairaigo tails, signal conflict, and band edges.
- `fresh_holdout_candidates`: an independent buffer against overfitting. By
  default it uses the current numeric vocab calibration-label count as the
  target size and selects rows whose kanji do not overlap the accepted
  calibration labels or the active-review candidate set.

Both sets remain review candidates only. Promote reviewed rows into accepted
calibration, pairwise, or holdout inputs only after human review assigns the
intended target difficulty/admission treatment.

The `review_batch` artifact intentionally keeps diagnostic columns such as
signal values and model disagreement. Human labeling should happen in the
barebones review files instead:

- `docs/test_outputs/srs_learner_difficulty_holdout_review_en_ja.md`
- `docs/test_outputs/srs_learner_difficulty_active_review_en_ja.md`

## Expanded-Signal Sweep Update

The first expanded-signal calibration sweep used the newer JMDict, KANJIDIC2,
KanjiVG, Step-by-Step, and compact BCCWJ profile components without changing
runtime behavior.

Primary artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_expanded_signals_s025_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_expanded_signals_s025_stump_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_tree_search_en_ja_expanded_signals_s025_focused_depth2_default_thresholds_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_search_en_ja_expanded_signals_s025_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_meta_search_en_ja_expanded_signals_s025_latest.json`

The coarse single-formula sweep evaluated `24,225` variants over `78,316` seed
rows and a `74,128` row normalization population. Its best global linear formula
scored `0.867769` balanced, with nonzero weights on `jmdict_priority`,
`kanjivg_variant_structure`, and `wtype_kango_risk`. This is useful as signal
coverage evidence, but it is below the best gated results.

The best current expanded-signal candidate remains a shallow stump, not a
deeper tree:

- Candidate:
  `stump__kango_common_priority_risk<=0.9668:mr__grid_s04_c150_022123__grid_s04_c150_023187`
- Balanced score: `0.904678`
- Bucket score: `0.795322`
- Pairwise score: `0.885825`
- Numeric MAE score: `0.868488`
- High-tail score: `0.727273`
- Upper-tail score: `0.947368`

The next-best stump uses the newly exposed compact BCCWJ domain coverage signal:

- Candidate:
  `stump__bccwj_domain_rank_coverage<=0.5833:mr__grid_s04_c150_020734__grid_s04_c150_022123`
- Balanced score: `0.904056`
- High-tail score: `0.818182`
- Upper-tail score: `0.894737`

That confirms the newly exposed source-profile fields are real signals, but the
current balanced objective still prefers the older `kango_common_priority_risk`
split by a small margin.

Model-family and meta searches produced useful but lower balanced scores:

- Best family/meta candidate:
  `softmix__grid_s04_cnone_004499__grid_s04_c150_023187__kango_mid_signal_t25_s50`
- Balanced score: `0.896797`
- Bucket score: `0.830409`
- Pairwise score: `0.895950`

This family improves bucket/pairwise behavior, but loses enough high-tail and
beginner stability that it is not the current balanced winner.

Focused depth-2 search was run twice. The first narrow-threshold pass excluded
the older winning `0.9668` kango-priority threshold, so it was not a valid
replacement comparison. The corrected pass restored the default threshold
quantiles and evaluated `650` exact candidates from `900` approximate retained
candidates. Its best result was still a stump:

- Best corrected focused depth-2 result:
  `stump__kango_mid_signal<=0.5099:ml__grid_s04_cnone_004501__grid_s04_cnone_003687`
- Balanced score: `0.898595`
- Bucket score: `0.807018`
- Pairwise score: `0.887224`
- High-tail score: `0.818182`
- Upper-tail score: `0.789474`

The best true depth-2 candidates improved numeric MAE, bucket score, or pairwise
score in places, but they did not beat the broad stump on the balanced objective
because high-tail handling degraded. The current lesson is that "deeper tree" is
not automatically the next win under the current signal and objective setup.

Remaining clean failure clusters in the current best stump:

- Proper/topic names are often scored too early despite being deprioritized
  vocabulary: `自民`, `北朝鮮`, `ＮＨＫ`, `国連`, `イラク`, and `トヨタ`.
- Formal or written wago still need stronger upper-tail pressure without
  regressing core native words: `我が`, `埋め立て`, `躊躇う`, `侘び`, and `猯`.
- Midrange kango remains compressed low: `技術`, `政治`, `財政`, `批判`,
  `憲法`, `承認`, `資源`, `改善`, and `減少`.
- A few kango are too high under some smoother/family candidates:
  `真理`, `特徴`, `影響`, `絶妙`, and `過疎`.

Near-term research posture:

1. Do not promote the expanded-signal learner-difficulty candidate to runtime
   yet.
2. Treat the broad expanded-signal stump as the current reference candidate for
   comparison.
3. Add a small residual-gate report that compares current-best failures against
   signal values for the three clusters above.
4. Keep model-family and depth-2 search artifacts because they reveal useful
   metric tradeoffs, especially bucket/pairwise improvements, but do not treat
   them as production-ready winners.
5. Investigate whether proper/topic names need a separate admission-priority
   model instead of being forced into the same learner-difficulty scalar.
6. Investigate stronger formal/written-wago and midrange-kango signals before
   spending more time on larger generic depth-2 searches.

## Refined Local Search Update

Follow-up searches tested whether the remaining obvious search space could beat
the expanded-signal stump without adding new runtime behavior.

Primary artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_refined_kango_coverage_s010_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_search_en_ja_refined_kango_coverage_s010_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_meta_search_en_ja_refined_kango_coverage_s010_vs_old_stump_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_tail_focus_s010_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_refined_kango_coverage_local_s005_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_search_en_ja_refined_kango_coverage_local_s005_latest.json`
- `docs/test_outputs/srs_learner_difficulty_model_family_meta_search_en_ja_refined_kango_coverage_local_s005_vs_old_stump_latest.json`

The refined `0.10` base sweep over the strongest kango/coverage signals
evaluated `16,016` variants. Its best base formula improved over the earlier
expanded-signal linear formula:

- Candidate: `grid_s10_cnone_006918`
- Balanced score: `0.895460`
- Bucket score: `0.855491`
- Pairwise score: `0.886383`
- Numeric MAE score: `0.901965`
- High-tail score: `0.636364`
- Upper-tail score: `0.842105`

Running model-family search over that refined pool produced a small new global
winner over the older expanded-signal stump:

- Candidate:
  `softmix__grid_s10_cnone_006909__grid_s10_cnone_006216__kango_mid_signal_t25_s50`
- Balanced score: `0.905528`
- Bucket score: `0.847953`
- Pairwise score: `0.889065`
- Numeric MAE score: `0.899213`
- High-tail score: `0.727273`
- Upper-tail score: `0.842105`

This candidate improves balanced score, bucket accuracy, pairwise order, and MAE
relative to the previous `0.904678` stump, but it loses the previous stump's
upper-tail score (`0.947368` -> `0.842105`). The meta search against the old
stump guardrails did not find a constrained candidate; no selected refined
family candidate preserved the old upper-tail guardrail.

A targeted rare/written-wago tail base sweep was also run to test whether the
`侘び`/`猯`/`埋め立て` class could be fixed by simply weighting tail signals more
heavily. It did not look promising as a standalone direction:

- Best tail-focused base balanced score: `0.863072`
- Best high-tail score among balanced leaders: `0.545455`

This suggests that the rare-wago signals are useful diagnostics, but not a clean
global scalar by themselves.

A local `0.05` search centered between the best refined experts evaluated
`31,780` variants. It showed that finer weights do matter, but only within the
same failure envelope:

- Best local base candidate: `grid_s20_cnone_008318`
- Balanced score: `0.902655`
- Bucket score: `0.867052`
- Pairwise score: `0.884552`
- High-tail score: `0.727273`

Running the model-family search over that local pool produced the current best
research candidate:

- Candidate: `boost__grid_s20_cnone_008318__kango_mid_signal_t35_s05`
- Balanced score: `0.907828`
- Bucket score: `0.871345`
- Pairwise score: `0.890611`
- Numeric MAE score: `0.893555`
- High-tail score: `0.727273`
- Upper-tail score: `0.842105`

The candidate is a material global improvement over both previous references,
but it still does not recover the old upper-tail score. The local-family meta
search against the old stump guardrails again found no constrained candidate,
so the current evidence says further generic grid or meta expansion is unlikely
to solve the remaining tail failures by itself.

Updated research posture:

1. Treat
   `boost__grid_s20_cnone_008318__kango_mid_signal_t35_s05` as the current best
   research candidate for review, not yet a runtime default.
2. Keep the older stump as the upper-tail reference because it still preserves
   the most advanced reviewed labels better.
3. Stop broad "more of the same" grid expansion for now. The valuable remaining
   work is residual modeling: better objective weighting, better upper-tail
   labels, stronger proper/topic-priority handling, or new pedagogical/source
   signals.
4. If another search is run before new signals are added, make it explicitly
   residual-aware: optimize the known misses (`侘び`, `猯`, `我が`,
   `埋め立て`, `自民`, `北朝鮮`, etc.) under non-regression constraints, rather
   than adding more unconstrained variants.

## Tail-Specialist Partition Search: 2026-06-16

The next search tests the hypothesis that the old upper-tail stump was not a
globally good difficulty model, but was a useful latent selector for the
hardest part of the corpus. This is implemented in
`scripts/testing/srs_learner_difficulty_tail_partition_search_en_ja.py` and
writes:

- `docs/test_outputs/srs_learner_difficulty_tail_partition_search_en_ja_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_tail_partition_calibration_rows_en_ja_latest.{csv,md}`

Definitions:

- Base model: the current best global research candidate,
  `boost__grid_s20_cnone_008318__kango_mid_signal_t35_s05`.
- Tail model: the old upper-tail reference,
  `stump__kango_common_priority_risk<=0.9668:mr__grid_s04_c150_022123__grid_s04_c150_023187`.
- Tail selector: the top `q` fraction of the full normalization population by
  the tail model's raw score. The default search uses `q` in
  `0.05, 0.08, 0.10, 0.12, 0.15, 0.20`.
- Hard partition: tail-selected rows receive the top `q` target-curve positions
  ordered by the tail model; all other rows receive the remaining target-curve
  positions ordered by the base model. This prevents duplicates and missing
  rows because every corpus row receives exactly one normalized position.
- Raw replace: tail-selected rows use the tail raw score and non-tail rows use
  the base raw score, then a single global target-curve normalization is
  applied.
- Soft blend: tail-selected rows use
  `(1 - strength) * base_raw + strength * tail_raw`, then a single global
  target-curve normalization is applied.
- Upper-tail labels: reviewed calibration rows with expected difficulty
  `>= 0.88`.
- High-tail labels: reviewed calibration rows with expected difficulty
  `>= 0.94`.
- False-tail rows: selected calibration rows with expected difficulty below
  `0.80`.

The search optimizes the same calibration metrics as the prior searches, but it
also reports tail-selection diagnostics:

- upper-tail precision and recall;
- high-tail precision and recall;
- false-tail count and rate;
- selected calibration examples, so the human review can inspect whether the
  selector is catching genuinely hard words or just rare-looking mid words.

Current reference metrics:

| Candidate | Balanced | MAE | Bucket | Pairwise | High tail | Upper tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base reference | `0.907828` | `0.106445` | `0.871345` | `0.890611` | `0.727273` | `0.842105` |
| Tail reference | `0.904678` | `0.131512` | `0.795322` | `0.885825` | `0.727273` | `0.947368` |

Current best tail-partition candidates:

| Candidate | Mode | q | Strength | Balanced | MAE | Bucket | Pairwise | High tail | Upper tail | Upper precision | False-tail rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw_replace_q20` | raw replace | `0.20` | - | `0.920372` | `0.104467` | `0.883041` | `0.892010` | `0.727273` | `0.947368` | `0.692308` | `0.115385` |
| `soft_blend_q20_s100` | soft blend | `0.20` | `1.00` | `0.920372` | `0.104467` | `0.883041` | `0.892010` | `0.727273` | `0.947368` | `0.692308` | `0.115385` |
| `hard_partition_q20` | hard partition | `0.20` | - | `0.919652` | `0.104532` | `0.877193` | `0.891973` | `0.727273` | `0.947368` | `0.692308` | `0.115385` |
| `soft_blend_q15_s75` | soft blend | `0.15` | `0.75` | `0.915866` | `0.104561` | `0.888889` | `0.892305` | `0.727273` | `0.894737` | `0.739130` | `0.043478` |
| `hard_partition_q05` | hard partition | `0.05` | - | `0.913599` | `0.105322` | `0.871345` | `0.891237` | `0.818182` | `0.842105` | `1.000000` | `0.000000` |

Interpretation:

- The user's tail-freezing intuition is statistically useful. The best q20
  candidates improve balanced score, MAE, bucket score, pairwise score, and
  upper-tail score versus the base reference.
- The main concern is selector precision. q20 recovers `18 / 19` upper-tail
  labels, but it also selects three calibration labels below `0.80`: `過疎`,
  `絶妙`, and `膨張`. That may be acceptable if qualitative band samples look
  better, but it is not a free win.
- q15 is the conservative alternative. It keeps most of the global gain,
  reduces false-tail rows to one (`膨張`), and has higher upper-tail precision,
  but gives back some upper-tail recall.
- q05 is very precise and improves high-tail score, but it misses too many
  upper-tail reviewed labels to be the obvious default.

False-tail risk sensitivity:

- The report now computes
  `false_tail_adjusted = balanced_score - penalty * false_tail_under_0_80_rate`
  for penalties `0.05`, `0.075`, `0.10`, and `0.15`.
- An unguarded false-tail penalty can select q05 because q05 has zero reviewed
  false-tail rows, but q05 also gives up the upper-tail lift that motivated this
  search. That is a useful warning that "avoid false tails" is not a complete
  objective by itself.
- The guarded sensitivity view therefore keeps only candidates with upper-tail
  score `>= 0.89`, preserving a meaningful upper-tail improvement before
  applying the false-tail penalty.
- Under that guard, `raw_replace_q20` wins only when the false-tail penalty is
  below about `0.062664`. At penalties `0.075`, `0.10`, and `0.15`,
  `soft_blend_q15_s75` is the top candidate.

Current candidate decision:

1. Treat `soft_blend_q15_s75` as the safer current research candidate for
   product-like qualitative testing.
2. Keep `raw_replace_q20` as the aggressive high-recall tail candidate and the
   best raw-objective candidate.
3. Do not promote q05 despite its false-tail precision, because it does not
   materially improve the upper-tail problem over the base model.
4. Before runtime/default promotion, compare larger upper-band samples against
   actual user experience. The research candidate choice is not yet product
   enablement.

### q15 Review Pack

The focused q15 review pack is generated by:

```bash
python3 scripts/testing/srs_learner_difficulty_q15_review_pack_en_ja.py
```

Outputs:

- `docs/test_outputs/srs_learner_difficulty_q15_review_pack_en_ja_latest.json`
- `docs/test_outputs/srs_learner_difficulty_q15_review_pack_en_ja_latest.md`

This artifact is intentionally not a runtime smoke. It samples rows by q15
difficulty windows and compares q15 against the base and q20 candidates:

- target-window proxy samples for `0.00`, `0.25`, `0.50`, `0.75`, and `1.00`;
- q15 upper-band samples from `0.65` through `1.00`;
- divergence examples for q20-over-q15, q15-over-base, and base-over-q15.

Initial read from the generated review pack:

- Low and mid windows are unchanged by the tail-specialist model, confirming
  that the q15/q20 decision is almost entirely about the upper tail.
- q20's largest promotions over q15 are dominated by acronym-like rows such as
  `ＶＲ`, `ＳＩ`, `ＷＡＶ`, `ＴＯＥＩＣ`, `ＰＤＦ`, and `ＭＲＩ`. This supports
  keeping q20 as the aggressive research ablation rather than the safer
  product-like candidate.
- q15 keeps many of those acronym rows high, but generally in the `0.85`
  neighborhood rather than forcing them into the extreme `0.99` tail.
- q15 also demotes several base-extreme rows, for example `噴霧`, `瘋癲`,
  `淵源`, `創成`, and `騰落`, into high-but-not-max territory. Those examples
  should be reviewed because some may actually deserve the base model's harder
  placement.
- The q15 review pack is good enough for focused qualitative review, but it
  still exposes unresolved upper-band taste questions. Runtime/default
  promotion should wait until those examples are accepted or a small follow-up
  calibration adjustment is made.

## Open Decisions

- Which non-numeric classes should be `pattern_item` versus
  `suppressed_default` for the first beta? Compound numerals are currently
  suppressed from default vocab admission.
- Should Options expose a separate challenge slider, or should challenge remain
  derived from proficiency unless advanced controls are open?
- Which redistributable learner-level sources are good enough for Japanese
  difficulty overlays?
- Which residual-gap path should be prioritized first: outside pedagogical
  source, derived existing-data signal, more reviewed labels, or generated label
  assistance?
- How should non-Japanese LPs express equivalent morphology/pattern categories?
- Should pattern items become their own future practice mode, or should they
  only be filtered out of default vocab admission for now?

## Recommended Next Slice

The smallest useful suitability and measurement slices are implemented. Next
work should focus on:

1. Review the best constrained meta result's sample bands and decide whether the
   mild pairwise regression is acceptable for default promotion.
2. Try softer/localized model forms for common-kango floors and rare-wago tails;
   the hard-gated meta search did not isolate the focused failure fixes cleanly.
3. Investigate product-compatible outside pedagogical sources and stronger
   derived residual gates before spending more time on broad model-form search
   with the same weak gates.
4. Keep the current balanced metric as the main gate, but continue reporting the
   side-by-side reviewed-failure metric before selecting a new default candidate.
5. Calibrate derived `challenge_target` so high-proficiency users aim higher
   without requiring manual advanced controls. Explicit challenge-target
   readiness centering is implemented; derived defaults still need product
   tuning.
6. Plan persisted reading/POS-aware SRS item IDs separately from admission
   diagnostics, including migration behavior for existing stores.
7. Choose and wire any richer redistributable learner-level source behind the
   existing `learner_difficulty` hook only after the current signal/model-space
   experiments stop yielding clear gains.
