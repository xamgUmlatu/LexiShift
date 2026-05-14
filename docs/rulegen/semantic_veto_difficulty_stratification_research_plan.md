# Semantic Veto Difficulty Stratification Research Plan

Status: active research plan
Role: Planning / WIP
Pair focus: `en-es` first, with the intended shape generalized later
Runtime policy change: none
Source evidence promotion: none

## Purpose

This plan defines how to research whether semantic-veto quality depends on word
difficulty, vocabulary rank, and ambiguity. It also connects that research to
the P1 SRS admission need: users should be able to prioritize words that are
useful, level-appropriate, and not unnecessarily chaotic in browser
replacement.

The central question is not only:

```text
Does the semantic veto work?
```

It is:

```text
For which kinds of words does the app experience feel good enough, and where
should we spend data-generation and source-coverage effort?
```

## Core Distinction

Do not collapse these into one score:

```text
learner_value
learner_difficulty
veto_decision_difficulty
```

They interact, but they answer different product questions.

## End-State Contract

The intended end state is a language-pair data-spend allocator, not a rule that
turns semantic veto on for a fixed set and off for everything else.

The main output should eventually be:

```text
top_N_llm_enrichment_queue(pair=en-es)
```

where each row is a source trigger plus target replacement family, with an
explicit next action:

```text
construct target/shadow family
score probe contexts
generate active/shadow/phrase rows
reserve locked evaluation rows
promote source evidence only after validation
```

The priority unit is not just an English word. It is:

```text
English source trigger + Spanish replacement target + semantic evidence family
```

However, the pipeline may start earlier with English-only ambiguous inventory
rows. Those rows are not ready for active/shadow/phrase LLM generation until
Spanish target and shadow families exist.

### Evidence Tiers

Semantic-veto coverage should fall into explicit tiers:

```text
Tier 1: LLM-enriched semantic veto
  expensive active/shadow/phrase examples exist and have passed admission plus
  locked validation.

Tier 2: cheap semantic veto
  enough dictionary, WordNet, Wiktextract, frequency, and local evidence exists
  for a lower-cost veto decision.

Tier 3: ordinary lexical replacement
  no expensive semantic-veto evidence exists, but the normal replacement rule is
  still allowed to function.

Tier 4: defer or review-only
  used only when rule quality, user policy, or known product risk says ordinary
  replacement is not acceptable.
```

Therefore, absence from the top-N LLM queue does not mean:

```text
always abstain
```

It usually means:

```text
use cheaper evidence or ordinary replacement until the word becomes worth
expensive enrichment.
```

### Stage Gates

Use these stages so research, source construction, LLM spend, and runtime policy
do not blur together:

```text
1. english_inventory_headword
2. translation_target_shadow_family_constructed
3. scored_context_probe_available
4. llm_active_shadow_phrase_rows_generated_and_admitted
5. locked_eval_validated_for_product_quality
6. runtime_semantic_inventory_available_if_promoted
```

Only stages 3 and later can produce active/shadow/phrase LLM packet
recommendations. Stage 1 can only recommend target/shadow family construction.

### Trusted Evaluation Lane Contract

The current full-family representative packet is a diagnostic queue, not a
trusted product-accuracy lane. It is valuable because it freezes families,
row shapes, scores, weaknesses, and review work. It is not valid as final
ground truth until the row-quality contract below is satisfied.

Keep these lanes separate:

```text
diagnostic draft lane
  agent-authored rows, WordNet-derived contexts, placeholder shadow targets,
  template no-winner rows, and pending review labels. Useful for finding
  failure classes and testing review tooling.

trusted-eval lane
  active source-target mapping reviewed, real shadow competitor target
  reviewed, independent context accepted, source trigger behavior confirmed,
  and row_quality_status trusted or explicitly scoped.

llm-discovery lane
  LLM-generated examples used to discover candidate source coverage,
  challenger evidence, and missing failure classes. Not gold by default.

llm-locked-eval lane
  pre-reserved rows generated or sampled under a frozen protocol and not used
  to choose thresholds, formulas, or scorer variants.
```

A row must not enter trusted product or budget claims unless it records:

```text
active_sense_status = aligned or accepted diagnostic exception
real Spanish active target and, for shadow rows, real Spanish shadow target
context_source independent from evidence_source or reviewed as acceptable
source_phrase appears in a runtime-triggerable form when trigger behavior is
  what the row is testing
human_review_status and row_quality_status set by review, not inference
```

When this work reaches the next accuracy or curve claim, the first task is to
build or refresh `trusted_eval_v1`, then rerun the score surfaces split by:

```text
all diagnostic rows
trusted/aligned rows
diagnostic-only controls
LLM discovery rows
locked-eval rows
```

If those splits do not exist, the result is a research signal only.

### Learner Value

Learner value asks whether a word is useful for a particular user.

Inputs can include:

- frequency and rank,
- user topic interests,
- user objectives,
- profile source preferences,
- current SRS inventory scarcity,
- user feedback history,
- pair-level policy.

Existing app direction already supports this shape through profile-context
signals such as interests, objectives, proficiency, difficulty preferences,
empirical trends, and source preferences. The research here should reuse that
conceptual split instead of inventing a separate semantic-veto-only notion of
importance.

### Learner Difficulty

Learner difficulty asks whether the replacement item is beginner,
intermediate, or advanced for the learner.

For `en-es`, this primarily concerns the Spanish replacement lemma, because
that is what enters SRS as the target vocabulary item. Useful features include:

- Spanish target frequency rank,
- Spanish `pmw` or other frequency value,
- CEFR when available,
- morphology and POS,
- cognate or transparency signals if later available,
- user-known lemmas,
- prior SRS feedback on the same or related target,
- profile challenge preference.

Frequency rank is not identical to difficulty. It is a starting proxy.

### Veto Decision Difficulty

Veto decision difficulty asks how risky the English source trigger is for
browser replacement.

For `en-es`, this mainly concerns the English trigger and its competing senses:

- English source frequency rank,
- number of WordNet senses,
- number of POS categories,
- number of Spanish translation candidates,
- active/shadow/phrase evidence counts,
- admitted shadow count,
- phrase-control count,
- active/shadow/phrase score margins,
- manual and LLM false-allow or false-abstain history,
- manual-vs-LLM distribution shift,
- source-coverage gaps.

A beginner source word can be difficult for the veto even when its Spanish
target is also beginner vocabulary. Examples include `change`, `check`,
`order`, `play`, `file`, `watch`, `bank`, and `plant`.

## Working Hypotheses

### H1: High-Frequency English Triggers Are Overrepresented In Veto Failures

Very common English words are likely more overloaded, more idiomatic, and more
syntactically flexible. They may create a disproportionate share of harmful
replacement decisions even if they are attractive SRS admissions.

Expected pattern:

```text
rank 1-500: high veto difficulty
rank 501-1000: still high
rank 1001-2000: mixed
rank 2001-5000: likely lower ambiguity, but watch source coverage
rank >5000: likely lower overload, but sparse evidence can dominate
```

### H2: Frequency Alone Will Not Explain Veto Difficulty

Polysemy and phrase density should explain failures better than frequency alone
for many rows. A high-frequency word with one dominant sense may be easier than
a less frequent word with several cross-POS senses.

### H3: Advanced Words Fail Differently

Advanced or domain-specific vocabulary may be less overloaded, but it can still
fail because source evidence is sparse. This is a different failure class from
beginner-word overload.

### H4: LLM Evaluation Rows Expose Broader Runtime-Like Ambiguity

The current LLM pilot suggests generated browser-ish rows leave the narrow
manual/source-evidence lane. A rank-stratified study should determine whether
that distribution shift is strongest in high-frequency triggers.

### H5: SRS Admission Should Penalize Veto Risk, Not Just Sort By Frequency

Some words are useful and level-appropriate but dangerous for automatic
browser replacement. They may still be admitted to SRS, but with a more
conservative replacement policy or a review-only presentation mode.

## Data Sources

Initial no-spend research should use existing local artifacts.

### Semantic-Veto Evaluation Rows

Use current manual, stress, and LLM artifacts:

```text
docs/test_outputs/semantic_veto_llm_pilot_scoring_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_failure_review_en_es_latest.json
docs/test_outputs/semantic_veto_llm_pilot_data_comparison_en_es_latest.json
docs/test_outputs/semantic_veto_llm_threshold_bakeoff_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_validation_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_candidate_selection_en_es_latest.json
docs/test_outputs/semantic_decision_rule_matrix_en_es_latest.json
```

### Frequency And Difficulty Metadata

Use installed or configured frequency packs where available. The repo already
models word-package frequency fields:

```text
core_rank
row_rank
pmw
frequency / freq / count fallback
```

For `en-es`, the research should try to resolve two ranks:

```text
source_trigger_rank_en
target_lemma_rank_es
```

The source English rank is most relevant to ambiguity and veto risk. The
Spanish target rank is most relevant to SRS learner difficulty.

### SRS Profile Signals

Treat profile settings as learner-value inputs, not as veto correctness labels.

Relevant signal families from the current SRS profile schema include:

```text
interests
objectives
proficiency
difficultyPreferences
empiricalTrends
sourcePreferences
```

Topic preference matters for admission priority. It should not be allowed to
hide a high veto-risk word from evaluation.

### Sense And Ambiguity Metadata

Use current source and evidence artifacts where available:

```text
WordNet sense count
WordNet POS count
translation candidate count
active evidence count
shadow evidence count
phrase-control evidence count
admitted shadow count
source coverage status
```

If an exact metadata source is missing in the first pass, emit `missing` and
keep the row in the report. Missing metadata is itself a useful coverage signal.

## Derived Scores

The first implementation should not train a model. It should compute transparent
heuristics that can later become model features.

### Learner Value Score

Purpose: rank how useful a candidate is for this user.

Suggested initial components:

```text
target_frequency_value
topic_interest_match
objective_match
profile_source_preference
inventory_scarcity
user_feedback_signal
```

This score should answer:

```text
Would this be worth learning soon?
```

### Learner Difficulty Score

Purpose: estimate beginner/intermediate/advanced level for SRS.

Suggested initial components:

```text
target_lemma_rank_es
target_lemma_pmw_es
CEFR if available
POS and morphology complexity
known-lemma proximity
prior feedback difficulty
```

Initial rank buckets:

```text
rank 1-500: beginner core
rank 501-1000: beginner plus / early intermediate
rank 1001-2000: intermediate
rank 2001-5000: upper intermediate / advanced
rank >5000: advanced or domain-specific
unranked: unknown
```

These labels are product heuristics, not linguistic truth.

### Veto Decision Difficulty Score

Purpose: estimate how risky a source trigger is for automatic browser
replacement.

Suggested initial components:

```text
source_trigger_rank_en
WordNet sense count
WordNet POS count
translation fan-out
shadow count
phrase-control count
active evidence count
shadow evidence count
phrase evidence count
active/shadow margin distribution
phrase margin distribution
manual false-allow rate
LLM false-allow rate
manual-vs-LLM disagreement
source coverage gaps
```

Initial heuristic:

```text
high veto difficulty =
  very frequent source trigger
  OR many senses / POS classes
  OR many target translations
  OR phrase-control cases exist
  OR low active-shadow margin
  OR sparse source evidence
  OR observed manual/LLM disagreement
```

Low veto difficulty:

```text
one dominant sense
stable POS
one major target translation
strong active evidence
few or no shadow/phrase competitors
large active-vs-shadow margin
consistent manual and LLM outcomes
```

## Research Reports To Build

### Report 1: Existing-Data Difficulty Stratification

No-spend first pass.

Status: implemented as a diagnostic research harness. Runtime policy remains
unchanged.

Script:

```text
scripts/testing/semantic_veto_difficulty_stratification_en_es.py
```

Outputs:

```text
docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.json
docs/test_outputs/semantic_veto_difficulty_stratification_en_es_latest.md
```

Inputs:

```text
LLM pilot scoring report
manual/stress validation reports
frequency packs or resolved frequency metadata
semantic source/evidence metadata
product quality policy
```

Minimum output sections:

```text
frequency-rank bin metrics
target-difficulty bin metrics
polysemy bin metrics
source-coverage bin metrics
phrase-density bin metrics
manual-vs-LLM delta by bin
top risky beginner triggers
top safe beginner candidates
top useful-but-dangerous SRS candidates
missing metadata summary
```

Do not use this report to promote runtime policy. Its job is to decide where
to spend evaluation and source-coverage effort.

Current first-pass read:

```text
case rows: 215
policy/product rows: 143
LLM pilot rows: 72
families: 35
triggers: 35
overall positive_allow_rate: 65.6%
overall negative_abstain_rate: 80.8%
English source-trigger rank coverage: 34.0%
Spanish target-rank coverage: 7.0%
known top-1000 English trigger failures: 6 / 25 rows
10+ WordNet-sense failures: 9 / 48 rows
```

The main result is methodological: we now have a repeatable stratification
surface, but the local frequency metadata is too sparse to prove the full
beginner-versus-advanced curve. Missing source and target rank is part of the
output, not a reason to remove rows from the denominator.

### Report 1b: Heuristic Group Pilot

This report freezes the small-group methodology before manual test writing.
It picks small word groups from cheap pre-outcome metadata, then emits a manual
review packet for balanced case authoring.

This lane is now classified as a stress/contrast lane, not representative
average evidence. Its original ordering favored prominent and polysemic words
inside each band, which is useful for finding hard examples but biased if the
question is "what is the mean veto difficulty for this heuristic band?"

Artifacts:

```text
scripts/testing/semantic_veto_heuristic_group_pilot_en_es.py
docs/test_outputs/semantic_veto_heuristic_group_pilot_en_es_latest.json
docs/test_outputs/semantic_veto_heuristic_group_pilot_en_es_latest.md
```

Current groups:

```text
core_high_polysemy: rank 1-1000, many WordNet senses, cross-POS
core_low_polysemy_control: rank 1-1000, few WordNet senses, one POS
mid_high_polysemy: rank 1001-5000, many WordNet senses, cross-POS
mid_low_polysemy_control: rank 1001-5000, few WordNet senses, one POS
tail_high_polysemy: rank >5000, many WordNet senses, cross-POS
tail_low_polysemy_control: rank >5000, few WordNet senses, one POS
measured_missing_rank_high_failure_sentinel: outcome-informed regression anchor
```

Methodology guardrail:

```text
The six primary groups are valid for stress/contrast comparisons because they
were selected before outcome scoring, but they are not representative
band-average samples. The sentinel group is outcome-informed and must be used
only as a regression anchor and metadata-gap warning.
```

Current first-pass output:

```text
candidate pool: 4112
selected triggers: 29
manual review rows: 29
case slots per trigger: 5
empty primary groups: 0
```

The manual-authoring step is now materialized as a separate research lane.

### Report 1b.2: Representative Heuristic-Band Sampler

This report corrects the sampling question raised after Report 1b. It freezes a
representative English-trigger sample within predeclared heuristic cells:

```text
source rank band x WordNet polysemy band x POS shape
```

Artifacts:

```text
scripts/testing/semantic_veto_representative_heuristic_band_sampler_en_es.py
docs/test_outputs/semantic_veto_representative_heuristic_band_sampler_en_es_latest.json
docs/test_outputs/semantic_veto_representative_heuristic_band_sampler_en_es_latest.md
```

Methodology:

```text
sample unit: English source trigger
rank bands: 1-500, 501-1000, 1001-2000, 2001-5000, 5001-10000, >10000
polysemy bands: 1-3, 4-9, 10+
POS shapes: single sense, same-POS polysemy, cross-POS polysemy
selection: deterministic seeded hash order inside each cell
default exclusion: previously measured triggers
```

Current freeze:

```text
candidate universe after measured-trigger exclusion: 4112
measured triggers excluded: 35
predeclared cells: 54
non-empty cells: 39
empty cells: 15
sampled triggers: 255
non-empty underfilled cells: 11
underfilled cells including empty cells: 26
sample per non-empty cell target: 8
```

This is still not semantic-veto accuracy evidence. It is a source-trigger
sampling frame. The next step is to construct Spanish target/shadow families
and fixed context packets over these frozen sampled triggers without
reselecting more interesting words after seeing outcomes.

Mean estimates must respect the sampling design:

```text
cell means:
  use sampled rows inside each cell

overall candidate-universe means:
  weight sampled rows by cell eligible count / sampled count

equal-cell means:
  allowed only when the question is "how hard is a typical predeclared cell?"
  not "how hard is a typical eligible source trigger?"
```

### Report 1b.3: Representative Target-Family Construction

This report applies the existing draft Spanish target/shadow family constructor
to every frozen representative sampled trigger. It does not replace blocked
rows with easier words, and it does not generate LLM rows.

Artifacts:

```text
scripts/testing/semantic_veto_representative_target_family_construction_en_es.py
docs/test_outputs/semantic_veto_representative_target_family_construction_en_es_latest.json
docs/test_outputs/semantic_veto_representative_target_family_construction_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_representative_target_family/en_es_representative_target_family_v1_dataset.json
docs/test_outputs/experiments/semantic_veto_representative_target_family/en_es_representative_target_family_v1_queue.json
```

Current construction read:

```text
attempted sampled triggers: 255
source-ready family drafts: 7
weak diagnostic family drafts: 87
blocked rows: 161
source-ready rate: 2.75%
constructed-family attempts: 94
missing noun/verb translation blockers: 161
```

Source-ready drafts:

```text
work
simple
look
return
soldier
stress
strike
```

Interpretation:

- the representative source-trigger sample is now actionable without changing
  the sample,
- current strict source-supported target/shadow construction covers only a
  small fraction of the representative sample,
- many weak rows have plausible target/shadow drafts but need better reverse or
  source support before scored probes,
- every currently blocked row is blocked by the constructor's
  `missing_noun_or_verb_translation` reason, so the next diagnosis should test
  whether the family constructor is too noun/verb-shaped, whether dictionary
  extraction is too sparse, or whether those rows are genuinely poor semantic
  veto candidates,
- blocked rows are part of the coverage estimate and must not be silently
  replaced by easier words,
- the next bottleneck is source/target-family coverage, not final YES/NO
  scoring.

Next work should use this as a coverage map:

```text
source-ready rows:
  review target/shadow family quality, then score fixed probe contexts

weak rows:
  improve reverse/source support or review whether diagnostic families are
  worth promoting to source-ready

blocked rows:
  analyze missing-shape reasons and decide whether the constructor is too
  narrow, the local dictionaries are insufficient, or the row should remain
  ordinary lexical replacement for now
```

### Report 1b.4: Sampling Methodology Comparison And Stability

This report compares the earlier heuristic-group pilot against the
representative sampler, then reruns source-sampling and target-family
construction stability checks across larger sample sizes and alternate seeds.

Artifacts:

```text
scripts/testing/semantic_veto_representative_sampling_methodology_comparison_en_es.py
docs/test_outputs/semantic_veto_representative_sampling_methodology_comparison_en_es_latest.json
docs/test_outputs/semantic_veto_representative_sampling_methodology_comparison_en_es_latest.md
```

Old versus new source-selection read:

```text
old heuristic-group pilot:
  24 primary triggers + 5 sentinel triggers
  6 coarse primary groups
  4 selected triggers per primary group
  selection was deterministic rank-first, not random
  represented fine cells: 10 / 39

representative sampler:
  255 sampled triggers
  39 / 39 non-empty fine cells represented
  10.625x more sampled triggers than old primary lane
  weighted rank/polysemy/POS distributions match the candidate universe for
  the cell-defining features
```

The old selection was biased toward the top of each group. For example:

```text
core_high_polysemy:
  selected rank mean: 122.5
  eligible rank mean: 495.7

mid_high_polysemy:
  selected rank mean: 1027.5
  eligible rank mean: 2531.2

tail_low_polysemy_control:
  selected rank mean: 5097.5
  eligible rank mean: 30300.4
```

Source-sampling stability:

```text
sample_per_cell=4:
  5 seeds, 140 sampled triggers, 39 / 39 cells, weighted rank TVD 0.0

sample_per_cell=8:
  5 seeds, 255 sampled triggers, 39 / 39 cells, weighted rank TVD 0.0

sample_per_cell=16:
  5 seeds, 444 sampled triggers, 39 / 39 cells, weighted rank TVD 0.0

sample_per_cell=32:
  5 seeds, 732 sampled triggers, 39 / 39 cells, weighted rank TVD 0.0
```

Target-family construction stability:

```text
sample_per_cell=4, 3 seeds:
  attempted rows: 140
  source-ready rate range: 3.57% - 5.00%

sample_per_cell=8, 3 seeds:
  attempted rows: 255
  source-ready rate range: 3.14% - 4.71%

sample_per_cell=16, 3 seeds:
  attempted rows: 444
  source-ready rate range: 2.93% - 4.28%
```

Interpretation:

- the seeded representative slice represents the predeclared source bands much
  better than the old pilot,
- this does not yet prove veto accuracy, because source sampling is upstream
  of target/shadow family quality and scored contexts,
- the low source-ready rate appears stable across seeds and sample sizes, so
  it is probably a real source/constructor coverage problem,
- the old heuristic difficulty surface, formula-shape bakeoff, formula-weight
  surface, and curve-guided expansion cannot be honestly rerun yet because
  they require representative scored case traces, not only source-trigger
  samples.

Required rerun order:

```text
1. representative source sample: done
2. target/shadow family construction over frozen sample: done
3. construction stability over alternate seeds/sizes: done
4. diagnose missing_noun_or_verb_translation and improve source readiness
5. author or generate fixed representative probe contexts
6. score representative case traces
7. rerun heuristic difficulty surface
8. rerun formula-shape bakeoff
9. rerun formula-weight surface
10. rerun curve-guided expansion from the representative surface
```

### Report 1c: Heuristic Group Case Authoring And Scoring

This report converts the frozen heuristic-group packet into a sentence-veto
dataset and records the first diagnostic scoring results.

Artifacts:

```text
scripts/testing/semantic_veto_heuristic_group_case_authoring_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json
docs/test_outputs/semantic_veto_heuristic_group_case_authoring_en_es_latest.json
docs/test_outputs/semantic_veto_heuristic_group_case_authoring_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_sentence_veto_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_sentence_veto_st_en_es_latest.md
docs/test_outputs/semantic_veto_heuristic_group_veto_only_validation_st_en_es_latest.md
scripts/testing/semantic_veto_heuristic_difficulty_surface_en_es.py
docs/test_outputs/semantic_veto_heuristic_difficulty_surface_en_es_latest.json
docs/test_outputs/semantic_veto_heuristic_difficulty_surface_en_es_latest.md
```

Authoring output:

```text
authored triggers: 29
dataset families: 29
dataset cases: 121
positive_active cases: 58
shadow_negative cases: 34
phrase_no_winner cases: 29
shadow contracts: full 16, limited 1, not_applicable 12
```

Methodology note:

```text
Low-polysemy controls are not forced to invent shadow-negative cases. When a
selected trigger has no honest alternate sense for the chosen replacement, the
dataset records a not_applicable shadow contract and uses active plus
mention/phrase no-winner cases. This makes the case mix uneven by design and
keeps the test honest.
```

First diagnostic scoring read:

```text
tfidf_cosine, masked_sentence/all_evidence_text:
  decision_accuracy: 69.4%
  positive recall: 39.7%
  harmful replace rate: 3.2%
  false abstain rate: 60.3%

sentence_transformer_cosine, masked_sentence/all_evidence_text:
  decision_accuracy: 77.7%
  positive recall: 89.7%
  harmful replace rate: 33.3%
  false abstain rate: 10.3%

frozen veto-only replay over the sentence-transformer row scores:
  positive allow: 100.0%
  negative abstain: 47.6%
  product target: fail on this draft lane
```

Interpretation:

- the heuristic lane is now scoreable end to end,
- sentence-transformer scoring gives the desired high positive allow rate, but
  no-winner/phrase cases still leak too often,
- TF-IDF remains useful as a conservative control but over-abstains,
- the low-polysemy controls exposed an important test-design issue: easy
  one-sense words may be positive-dominated rather than shadow-balanced,
- this lane is still `agent_draft_human_review_pending`; it is useful for
  research direction, not for promotion claims.

Difficulty-surface read:

```text
score rows: 242
primary rows: 192
sentinel rows: 50
overall weighted difficulty: 26.5%
primary-only weighted difficulty: 29.2%

sentence_transformer_cosine:
  positive_allow_difficulty: 10.3%
  shadow_negative_difficulty: 5.9%
  phrase_no_winner_difficulty: 65.5%

tfidf_cosine:
  positive_allow_difficulty: 60.3%
  shadow_negative_difficulty: 0.0%
  phrase_no_winner_difficulty: 6.9%
```

The current crude frequency/polysemy formula is not validated by this draft
surface. On the sentence-transformer lane, the baseline and richer formula
rank correlations are negative on the primary rank-known triggers, while the
dominant observed failure class is phrase/no-winner leakage. This means the
next heuristic should model phrase and mention risk separately instead of
expecting WordNet polysemy alone to predict veto difficulty.

Expansion planner output:

```text
P0/P1: expand phrase/no-winner cells, especially low-polysemy controls and
       mid-rank high-polysemy rows.
P1: add real shadow-negative rows only for full/limited shadow contracts.
P2: keep missing-rank sentinel triggers as regression anchors and metadata-gap
    prompts, not as primary heuristic proof.
```

### Report 1d: Formula-Shape And Data-Help Priority Bakeoff

The next plan update is not "add one better heuristic." It is a scientific
formula-composition bakeoff whose goal is to decide which data needs help.
That means the target is not only predicted word difficulty. The target is the
expected product value of authoring, buying, or generating more data for a
word/case cell.

Keep these objects separate:

```text
r = one scored row or one aggregated cell
s = English source trigger
t = Spanish replacement target
k = case type: positive_active, shadow_negative, phrase_no_winner
m = scorer lane: tfidf, sentence_transformer, veto-only replay, etc.
x(r) = observed features for r
phi(x) = normalized or bucketed feature vector
g(phi(x)) = formula that predicts failure risk or data-help priority
y(r) = observed outcome used for validation
```

Feature families:

```text
source features:
  source rank bucket, missing-rank flag, WordNet sense count, POS count,
  translation fan-out, source-coverage flags

target features:
  target-rank bucket, target-level proxy, target-lemma normalization coverage,
  replacement frequency or SRS priority when available

case-shape features:
  case type, shadow contract, phrase/no-winner density, mention-only pattern,
  order-sensitive phrase cues, local-window distance between source and cues

score-surface features:
  active score, strongest shadow score, phrase/no-winner score, active gap,
  phrase lead, shadow margin, score entropy, near-threshold flags

product features:
  estimated browsing exposure, user-topic value, learner value,
  learner difficulty, and product-quality utility weights
```

Normalization must be explicit. Examples:

```text
rank_score = 1 / log2(rank + 2)
sense_score = log1p(wordnet_sense_count)
missing_rank = 1 if no rank source covers s else 0
score_gap = active_score - max(shadow_score, phrase_score)
near_threshold = 1 if abs(score_gap - threshold) <= epsilon else 0
```

Missingness is a signal, not a value to silently impute. A missing rank gets a
separate bucket or indicator. The measured missing-rank sentinel group remains
excluded from primary validation because it is outcome-informed.

Observed difficulty should remain separated by failure class:

```text
positive_allow_difficulty =
  false_abstain_count / positive_active_count

shadow_negative_difficulty =
  negative_allow_count / shadow_negative_count

phrase_no_winner_difficulty =
  negative_allow_count / phrase_no_winner_count

overall_veto_difficulty =
  w_pos * positive_allow_difficulty
  + w_shadow * shadow_negative_difficulty
  + w_phrase * phrase_no_winner_difficulty
```

Use the existing product-quality utility weights for `w_pos`, `w_shadow`, and
`w_phrase`, and report the actual weights in every artifact. If a denominator
is zero, that class is not observed for the cell; do not treat it as easy or
hard.

The data-help priority function should estimate where more authored or
LLM-generated data is worth spending:

```text
data_help_priority(cell) =
  exposure_weight(cell)
  * product_impact_weight(cell)
  * uncertainty_weight(cell)
  * predicted_failure_risk(cell)
  * fixability_weight(cell)
  * coverage_gap_weight(cell)
```

Where:

```text
exposure_weight:
  how often this source/case shape is likely to appear in browsing

product_impact_weight:
  how much the failure class matters to product quality

uncertainty_weight:
  posterior or confidence-interval width from current observations

predicted_failure_risk:
  formula estimate for positive false abstain, shadow false allow,
  phrase/no-winner false allow, or the weighted blend

fixability_weight:
  high when misses are near-threshold, evidence-limited, or phrase-cue
  limited; lower when the target/source pair is fundamentally ambiguous

coverage_gap_weight:
  high when source evidence, target-level metadata, shadow examples, or
  phrase/no-winner rows are missing
```

For small cells, estimate uncertainty with a binomial posterior rather than a
raw percentage:

```text
posterior_failure_rate =
  (failures + 0.5) / (trials + 1.0)

uncertainty_width =
  beta_quantile(0.975, failures + 0.5, successes + 0.5)
  - beta_quantile(0.025, failures + 0.5, successes + 0.5)
```

If the implementation cannot depend on a beta quantile library, use an
explicit Wilson interval fallback and label it as an approximation.

Formula classes to compare:

```text
linear weighted sum:
  g = b + sum_j w_j * phi_j(x)

normalized dot product:
  g = dot(normalize(phi(x)), normalize(w))

multiplicative interaction:
  g = b + sum_j w_j * phi_j(x)
        + sum_{j,l} w_{j,l} * phi_j(x) * phi_l(x)

probabilistic product of risks:
  p = 1 - product_j (1 - clamp(w_j * phi_j(x), 0, 1))

max-risk rule:
  g = max_j risk_j(phi_j(x))

gated formula:
  if case_type == phrase_no_winner: use phrase-risk formula
  elif shadow_contract in {full, limited}: use shadow-risk formula
  else: use positive/mention-control formula

logistic model:
  p = sigmoid(b + sum_j w_j * phi_j(x))

small monotone tree or rule table:
  split first by case type or shadow contract, then by rank/polysemy/score gap

rank aggregation:
  combine per-formula ranks by median rank, Borda count, or robust top-k vote
```

Do not force structurally different formula classes to share one parameter
set. Shared bakeoff sweeps are fair only for structurally similar formulas.
For each class, compare a conservative default, a small grid, and a
locked-eval choice selected only from discovery data.

Validation metrics:

```text
rank agreement:
  Spearman/Kendall between predicted risk and observed difficulty by cell

calibration:
  Brier score and calibration buckets for predicted failure probability

top-k lift:
  how much observed failure mass appears in the top prioritized cells
  versus random or current baseline

budget curve:
  expected failure coverage or expected utility gain as generated rows increase

failure concentration:
  which feature families explain most misses for each failure class

stability:
  bootstrap intervals, family leave-one-out, and source-family dropout
```

Negative controls:

```text
random priority should not beat real formulas
shuffled outcomes should collapse rank agreement
single-feature controls should be reported but not over-promoted
target-lemma-only formulas should expose lexical leakage
sentinel rows must not influence primary heuristic validation
missing-rank rows must not be silently imputed into ordinary rank buckets
```

Interpretation rules:

- If formula classes using the same signals disagree strongly, the old
  composition was too naive.
- If all sane formula classes fail on locked evaluation, the bottleneck is
  probably signal coverage or case representation rather than formula shape.
- If phrase/no-winner remains the dominant miss class, model it as its own
  data-help target instead of averaging it away.
- If a formula predicts "hard" but no additional data would plausibly fix the
  row, it is not a high data-help priority.
- The output is a spending and understanding plan, not a runtime-policy
  promotion.

Implemented artifacts:

```text
docs/test_inputs/semantic_veto_formula_shape_bakeoff_en_es.json
scripts/testing/semantic_veto_formula_shape_bakeoff_en_es.py
docs/test_outputs/semantic_veto_formula_shape_bakeoff_en_es_latest.json
docs/test_outputs/semantic_veto_formula_shape_bakeoff_en_es_latest.md
```

The first implementation reuses the existing heuristic difficulty surface rows
and emits:

```text
per-formula metrics
per-cell predicted risk and priority
discovery versus internal locked-eval summaries
negative-control summaries
top data-help cells for manual rows
top data-help cells for LLM rows
cells that should not receive spend yet because the current evidence is too
thin, too outcome-informed, or not fixable by more examples
```

Current first-pass read:

```text
cells: 48
primary cells: 42
sentinel cells: 6
formula families: 9
parameter sweeps: 2
sampled sweep candidates: 205 linear + 161 gated
weight-surface report: implemented
primary all-scorer leader: monotone_rule_table
primary all-scorer Spearman: 0.3056
primary all-scorer top-k lift: 1.2632
best selected gated sweep Spearman: 0.2599
best selected gated sweep top-k lift: 1.5918
best selected gated sweep Brier: 0.0915
linear sampled maximum: sharp_sampled_peak
gated sampled maximum: sharp_sampled_peak
best gated feature curve: phrase_no_winner.underfilled_rate
best gated pairwise curve: phrase_no_winner rank_missing_rate vs underfilled_rate
negative controls: random, source-rank-only, target-lemma-length, shuffled
top data-help cells: mostly high-frequency phrase/no-winner or underfilled
                     limited-shadow cells
```

Interpretation:

- this is a meaningful harness milestone because formula shape is now testable
  separately from signal choice and runtime policy,
- the first result does not prove a robust model; correlations are modest and
  the internal locked split is advisory only,
- the monotone rule-table result suggests that coarse gates by case type,
  coverage, rank/polysemy, and near-threshold evidence are currently more
  useful than pretending one smooth linear score is already correct,
- deterministic parameter sweeps are now in place for sliding continuous
  weights; the first selected gated sweep improves top-k lift and calibration
  but does not beat the fixed monotone rule table on primary all-scorer
  Spearman,
- a follow-up surface report now probes one-dimensional and pairwise curves
  around selected weights; both sampled maxima look sharp, which is best read
  as a curve-sensitivity map before expanding data rather than as a stable
  coefficient choice,
- the strongest curve signals are not generic "polysemy" signals; they are
  phrase/no-winner underfilled coverage, phrase rank/missing-rank interaction,
  shadow near-tie behavior, and positive-active low active score,
- the top spend cells are uncertainty-aware, so some underfilled cells can rank
  high even before they show many observed failures,
- the next data spend should still be reviewed by cell, not blindly generated
  from the score.

Surface-analysis artifacts:

```text
scripts/testing/semantic_veto_formula_weight_surface_en_es.py
docs/test_outputs/semantic_veto_formula_weight_surface_en_es_latest.json
docs/test_outputs/semantic_veto_formula_weight_surface_en_es_latest.md
scripts/testing/semantic_veto_curve_guided_expansion_plan_en_es.py
docs/test_outputs/semantic_veto_curve_guided_expansion_plan_en_es_latest.json
docs/test_outputs/semantic_veto_curve_guided_expansion_plan_en_es_latest.md
```

### Report 1d.2: Programmatic LLM Data Priority Scan

The formula-surface work can suggest what kinds of rows are valuable, but the
actual LLM generation budget needs a scanner that can be applied without manual
case labels. The first strict scanner now ranks trigger/target pairs with only
programmatic metadata and raw scorer surfaces.

Artifacts:

```text
scripts/testing/semantic_veto_llm_data_priority_scan_en_es.py
core/tests/dev/test_semantic_veto_llm_data_priority_scan_en_es.py
docs/test_outputs/semantic_veto_llm_data_priority_scan_en_es_latest.json
docs/test_outputs/semantic_veto_llm_data_priority_scan_en_es_latest.md
```

Ranking inputs are limited to programmatic fields:

```text
source rank and missing-rank indicator
target rank when available
WordNet sense and POS counts
translation candidate count
active, shadow, and phrase evidence counts
active score, shadow score, phrase-control score
near-tie, low-active, phrase-near-best, and phrase-surface rates
coverage gap and expected fixability
```

These fields are explicitly forbidden from the ranking feature vector:

```text
manual_case_type
gold_decision
gold_winner_type
predicted_decision
predicted_winner_type
product_outcome
error_type
veto_reason
```

The generated report may still include a `validation_shadow` block so we can
judge whether the frozen priority order correlates with observed misses, but
those labels do not enter the score. A focused unit test verifies that changing
only gold/product outcome labels does not change the priority score.

Current scan read:

```text
candidate trigger/target pairs: 35
declared programmatic features: 19
forbidden label/outcome fields: 8
top scored-context need: 0.2694
top static need: 0.4076
source-rank known rate by candidate pair: 31.4%
target-rank known rate by candidate pair: 14.3%
WordNet-sense known rate by candidate pair: 45.7%
translation-count known rate by candidate pair: 45.7%
```

Current top packet recommendations:

```text
wrong -> incorrecto: 0 active, 4 shadow, 12 phrase, 4 locked rows
watch -> reloj: 4 active, 4 shadow, 8 phrase, 4 locked rows
score -> tantos: 0 active, 4 shadow, 8 phrase, 2 locked rows
bank -> banco: 4 active, 0 shadow, 8 phrase, 2 locked rows
```

Interpretation:

- this is the first scanner that matches the actual LLM-cost question rather
  than only describing observed failures,
- phrase rows dominate the top-N packet budget because phrase evidence gaps and
  phrase-near-best score surfaces remain the clearest programmatic need signal,
- labels are now audit-only, which avoids overfitting the data-spend allocator
  to known failures,
- the current scan still covers measured/scored contexts, not the full general
  database; the next infrastructure step is to feed it a wider rule inventory
  with the same static metadata and, where possible, scored probe contexts.

### Report 1d.3: Inventory Bridge For Top-N Enrichment

The current broader inventory is English-headword based. It can identify
ambiguous source words, but many rows still lack Spanish target/shadow families.
The bridge report makes this prerequisite explicit instead of treating every
inventory row as ready for active/shadow/phrase LLM generation.

Artifacts:

```text
scripts/testing/semantic_veto_llm_data_priority_inventory_bridge_en_es.py
core/tests/dev/test_semantic_veto_llm_data_priority_inventory_bridge_en_es.py
docs/test_outputs/semantic_veto_llm_data_priority_inventory_bridge_en_es_latest.json
docs/test_outputs/semantic_veto_llm_data_priority_inventory_bridge_en_es_latest.md
```

Current bridge read:

```text
inventory candidates read: 100
already scored trigger rows: 16
target/shadow family missing: 84
top inventory-source need: 0.9503
top-N bridge size: 50
top-N target-family construction rows: 34
top-N scored-context packet rows: 16
```

The report's guardrails are:

```text
inventory-only rows receive no active/shadow/phrase LLM packet
scored rows must link back to the LLM data priority scan
forbidden label/outcome fields stay out of bridge features
rows are sorted by readiness stage and then source need
```

Interpretation:

- the current broad inventory is good enough to choose target-family
  construction work, not enough to spend LLM row budget directly,
- the 16 rows already present in the scored priority scan can reuse packet
  recommendations immediately,
- the remaining 84 rows need Spanish target/shadow family construction first,
- non-enriched rows remain on ordinary replacement or cheaper semantic evidence
  tiers; they are not automatically veto-disabled.

### Report 1d.4: Target-Family Construction Queue

The inventory bridge is not itself enough to spend LLM row budget. The next
stage attempts Spanish target/shadow construction for the bridge's top
inventory-only rows using the existing local non-v10 family constructor. It
keeps strict source-ready drafts separate from weak diagnostic drafts.

Artifacts:

```text
scripts/testing/semantic_veto_llm_data_priority_target_family_construction_en_es.py
core/tests/dev/test_semantic_veto_llm_data_priority_target_family_construction_en_es.py
docs/test_outputs/semantic_veto_llm_data_priority_target_family_construction_en_es_latest.json
docs/test_outputs/semantic_veto_llm_data_priority_target_family_construction_en_es_latest.md
docs/test_outputs/experiments/semantic_veto_llm_data_priority/en_es_target_family_construction_queue_v1_dataset.json
docs/test_outputs/experiments/semantic_veto_llm_data_priority/en_es_target_family_construction_queue_v1.json
```

Current construction read:

```text
top inventory-only rows attempted: 34
source-ready family drafts: 3
weak diagnostic family drafts: 25
blocked rows: 6

selected strategy counts:
  noun_verb_supported_source_linked: 1
  any_cross_pos_supported_source_linked: 2
  any_cross_pos_wordnet_forward_only: 13
  any_cross_pos_translation_only_diagnostic: 12
```

Interpretation:

- the broad inventory is useful for ranking where to try construction, but the
  current local source/translation support only makes a small fraction of the
  top rows immediately ready for scored probes,
- weak diagnostic drafts are still useful because they tell us whether the
  blocker is source support rather than total absence of plausible Spanish
  targets,
- only the 3 source-ready drafts enter the generated source-ready dataset,
- the weak and blocked rows should drive the next support-acquisition pass, not
  LLM active/shadow/phrase row generation,
- this result makes the next bottleneck more concrete: before large LLM spend,
  we need target-family review plus better reverse/source support for the top
  priority triggers.

The curve-guided expansion report converts those surface signals into the next
manual/LLM data queue. Its goal is not to extract a coefficient optimum from the
draft lane; its goal is to draw the difficulty surface clearly enough that the
next rows test the cells where the curve changes most.

Current curve-guided read:

```text
primary cells read: 42
sentinel cells excluded from queue selection: 6
curve signals read: 37
queued cells: 24
P0/P1/P2 cells: 5 / 16 / 3
first-wave row budget if the whole queue is pursued:
  manual discovery rows: 74
  LLM discovery rows: 258
  locked-eval rows: 129
largest case-type budget: phrase_no_winner
```

This queue is meant to be consumed in small waves. P0 manual rows come first;
LLM rows follow only after the manual rows confirm that the cell contract is
real; locked-eval rows stay separate from discovery rows.

### Report 1f: Scientific Sampling Expansion Design

The curve-guided queue is useful, but it is targeted by design. It must not be
the only expansion lane, because that would bias the suite toward the current
theory of failure. The next artifact therefore freezes a mixed sampling design:

```text
docs/test_inputs/semantic_veto_sampling_expansion_design_en_es.json
scripts/testing/semantic_veto_sampling_expansion_design_en_es.py
docs/test_outputs/semantic_veto_sampling_expansion_design_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_expansion_design_en_es_latest.md
```

Current design:

```text
lanes: 4
total planned rows: 440
locked-eval share: 50.0%
representative random product rows: 120 locked only
stratified difficulty-surface rows: 144
targeted curve-mechanism rows: 140, P0 only
negative/leakage control rows: 36
```

The methodology is:

```text
representative random lane:
  estimates product quality and remains locked-only

stratified surface lane:
  balances case type, rank bin, and polysemy before looking at failures

targeted curve lane:
  tests the current P0 mechanisms, but cannot estimate real-world frequency

control lane:
  catches label leakage, lexical leakage, and scorer-shaped generation
```

This is the anti-bias rule:

```text
random rows estimate product experience
stratified rows draw the surface
targeted rows test mechanisms
control rows test whether the experiment is contaminated
locked rows validate only after discovery choices are frozen
```

The first operational stage is not to generate all 440 rows. It is to freeze
the design, materialize the representative sampling frame, and author the P0
manual discovery rows. LLM generation starts only after those manual rows
confirm the cell contracts and prompts pass leakage review.

### Report 1g: Stage 1 Sampling Materialization

Stage 1 is now materialized without changing runtime policy, thresholds,
source evidence, or scorer selection:

```text
scripts/testing/semantic_veto_sampling_stage1_materialization_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json
docs/test_inputs/semantic_veto_representative_gap_rows_en_es.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_frame_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_materialization_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_materialization_en_es_latest.md
```

Current Stage 1 read:

```text
status: ok
decision: sampling_stage1_materialized
representative target locked rows: 120
available representative rows: 120
base v10 representative proxy rows: 95
corpus-like representative gap rows added: 25
remaining representative rows needed: 0
P0 curve cells materialized: 5
P0 manual draft cases: 20
P0 triggers: help, particular
manual review state: agent_draft_human_review_pending
```

The important methodological point is that the representative frame is not
backfilled with targeted rows. The existing v10 representative proxy supplies
95 selectable rows, and the remaining 25 are filled by a separate
corpus-like app-candidate proxy dataset with explicit provenance. This keeps
product-quality estimation separate from the P0 targeted mechanism lane.

The P0 manual packet is discovery-only. It exists to confirm that the queued
phrase/no-winner and positive-active cell contracts are linguistically real
before spending LLM budget. It must not be counted as representative browsing
evidence or locked evaluation.

The 25-row representative shortfall has been filled numerically, and the
separate gap plan now records that the active collection queue is closed:

```text
docs/test_inputs/semantic_veto_representative_gap_source_manifest_en_es.json
scripts/testing/semantic_veto_representative_gap_plan_en_es.py
docs/test_outputs/semantic_veto_representative_gap_plan_en_es_latest.json
docs/test_outputs/semantic_veto_representative_gap_plan_en_es_latest.md
```

Current representative-gap read:

```text
remaining representative rows needed: 0
open primary collection slots: 0
corpus-like app-candidate rows materialized: 25
observed runtime/context rows materialized: 0
existing LLM locked proxy rows available: 16
LLM proxy rows count toward primary target: false
```

This lets P0 LLM work proceed without hiding the product-lane gap. The rule is
strict: targeted P0 rows, stress rows, and generated discovery rows cannot fill
the representative product target. The current 25 gap rows are
agent-draft corpus-like proxy rows, not observed browser logs, so promotion
claims still need human review and later replacement or refresh with observed
runtime contexts when those logs are available.

### Report 1h: Stage 1 P0 Manual Discovery Scoring

The Stage 1 P0 manual packet has also been scored with the existing sentence
veto harness as a discovery read:

```text
docs/test_outputs/semantic_veto_sampling_stage1_p0_manual_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_p0_manual_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_sampling_stage1_p0_manual_st_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_p0_manual_st_en_es_latest.md
```

Configuration for both reports:

```text
context_view: masked_sentence
evidence_view: all_evidence_text
min_active_score: 0.05
min_margin: 0.0
phrase_control_mode: noun_family_frame_guard
active_rescue_mode: off
```

First read:

```text
tfidf_cosine:
  cases: 20
  decision_accuracy: 80.0%
  replace_recall: 0.0%
  harmful_replace_rate: 0.0%
  false_abstain_rate on positives: 100.0%
  phrase_preemption_precision: 100.0%

sentence_transformer_cosine:
  cases: 20
  decision_accuracy: 70.0%
  replace_recall: 50.0%
  harmful_replace_rate on negatives: 25.0%
  false_abstain_rate on positives: 50.0%
  phrase_preemption_precision: 100.0%
```

Interpretation:

- the P0 cells are real stressors, not just paperwork,
- TF-IDF is still too abstain-heavy for the positive-active `help` rows,
- sentence-transformer scoring recovers some positive `help` rows but leaks
  `help` interjection and `particular` phrase/no-winner rows,
- the phrase-control guard catches four phrase rows cleanly but does not cover
  the broader phrase/no-winner set,
- the next LLM/prompt work should focus on generating phrase/no-winner variants
  and positive `help` assistance rows without mixing them into representative
  product metrics.

### Report 1i: Filled Representative Scoring And Strict Veto-Only Check

The filled Stage 1 representative frame is now scoreable as an ordinary
sentence-veto dataset. This keeps row selection and scoring separate:

```text
scripts/testing/semantic_veto_sampling_stage1_representative_scoring_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_scoring_en_es_latest.json
docs/test_outputs/semantic_veto_sampling_stage1_representative_scoring_en_es_latest.md
```

Current current-policy score:

```text
cases: 120
positive cases: 53
negative cases: 67
positive_allow_rate: 24.5%
negative_abstain_rate: 100.0%
harmful replacements: 0
false abstains: 40
context sources: 95 existing v10 proxy, 25 corpus-like gap rows
```

The product-quality report now reads this filled representative score rather
than the old 95-row v10 report. That gives a more honest denominator, but it
also makes the old current policy's false-abstain problem sharper.

The veto-only validation report now also has a strict source-pass distinction.
When the filled representative score is combined with the wave7 stress reports,
some settings pass the aggregate product target, but none pass every source
lane:

```text
docs/test_outputs/semantic_veto_veto_only_validation_stage1_representative_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_validation_stage1_representative_en_es_latest.md
docs/test_outputs/semantic_veto_veto_only_candidate_selection_stage1_representative_en_es_latest.json
docs/test_outputs/semantic_veto_veto_only_candidate_selection_stage1_representative_en_es_latest.md

input case rows: 168
aggregate target-pass rows: 16
strict source-pass rows: 0
shared v10-plus-filled-representative candidate pass rows: 0
```

Interpretation:

- aggregate product passes can be misleading if one source lane fails badly,
- high-positive-allow veto-only settings leak too many filled-representative
  negatives,
- conservative settings protect representative negatives but miss too many
  positives,
- the next curve/data work should isolate which blocker signals separate
  representative negatives from positives, not only slide a global shadow
  threshold.

### Report 1j: Representative Band Performance

The filled representative-proxy score is now sliced separately by source-rank
band, gold winner type, context source, declared ambiguity, and metadata
availability:

```text
scripts/testing/semantic_veto_representative_band_performance_en_es.py
docs/test_outputs/semantic_veto_representative_band_performance_en_es_latest.json
docs/test_outputs/semantic_veto_representative_band_performance_en_es_latest.md
```

Current representative-proxy read:

```text
cases: 120
families/triggers: 19 / 19
positive_allow_rate: 24.5%
negative_abstain_rate: 100.0%
source-rank known rows: 33 / 120
source Zipf-known rows: 120 / 120
target-rank known rows: 0 / 120
WordNet-known rows: 0 / 120
```

Source-rank rows do not prove that beginner/intermediate/advanced bands have
the same veto performance. They show low positive allow across the current
representative-proxy lane, but most rows are missing source-rank metadata and
several rank cells have fewer than ten cases. The report therefore adds an
optional no-spend `wordfreq` Zipf-frequency fallback as a separate signal, not
as a replacement for corpus-rank or learner-level evidence.

The current Zipf slice is a useful clue:

```text
zipf_5_plus_very_common: 68 cases, 13.3% positive allow, 100.0% negative abstain
zipf_4_to_5_common: 52 cases, 39.1% positive allow, 100.0% negative abstain
```

The correct current claim remains:

```text
same-band-performance claim: not_supported
```

Interpretation:

- current browser-like behavior is conservative: it hides every negative row in
  this lane,
- the visible product issue is false abstention on good replacements, not
  harmful replacement leakage,
- frequency-band curves are still fragile because 87 / 120 representative rows
  lack source-rank metadata,
- the denser Zipf fallback suggests very common triggers may be especially
  abstain-heavy, which is a promising clue rather than a stable causal law,
- target-rank and WordNet/sense-count features are unavailable for this filled
  representative-proxy lane, so they cannot yet drive a top-N LLM data formula,
- the next data work should preserve the Zipf signal, improve target/WordNet
  coverage, and score representative rows with richer evidence before claiming
  that a frequency/polysemy formula identifies the true LLM spend frontier.

### Report 1k: Zipf Expansion Plan

The Zipf slice now has a separate expansion planner so the frequency signal can
be strengthened without accidentally overfitting to the current failures:

```text
scripts/testing/semantic_veto_zipf_expansion_plan_en_es.py
docs/test_outputs/semantic_veto_zipf_expansion_plan_en_es_latest.json
docs/test_outputs/semantic_veto_zipf_expansion_plan_en_es_latest.md
```

Current expansion read:

```text
represented Zipf bands: 2 / 4
P0 bands: 3
recommended manual/observed rows: 96
recommended LLM discovery rows: 84
recommended locked-eval rows: 42
```

The planner deliberately separates two needs:

- `zipf_5_plus_very_common` is P0 because it is represented and carries the
  largest false-abstain mass in the current representative proxy.
- `zipf_3_to_4_mid` and `zipf_below_3_rare` are P0 because the representative
  proxy has no rows there, so the current curve cannot say whether mid/rare
  source words are actually easier.
- `zipf_4_to_5_common` stays P1 as a control band because it is represented and
  currently performs better than the very-common band.

Interpretation:

- the random representative slice helped by moving us away from hand-picked
  worst-case words, but it still only covers very-common and common Zipf bands,
- the best current frequency claim is directional, not decisive: very-common
  source words look harder, especially for positive allows, but mid/rare
  controls are missing,
- the next expansion should add control rows before we make any top-N LLM spend
  formula dependent on Zipf,
- LLM rows should be split into discovery and locked-eval lanes, so the same
  generated examples do not both inspire a heuristic and prove it.

### Report 1l: SRS Zipf Bridge

The frequency/cost denominator now has a bridge report from the installed en-es
SRS journey to semantic-veto source-trigger planning:

```text
scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py
docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_latest.json
docs/test_outputs/semantic_veto_srs_zipf_bridge_en_es_latest.md
```

This report separates:

```text
Spanish SRS target lemma distribution
English rule source-trigger distribution
English-source + Spanish-target family matrix
```

Current installed en-es SRS and rulegen read:

```text
full SRS-admissible seed rows: 2000
full unique SRS-admissible targets: 1984
journey candidate-slice targets: 200
selected initial-active targets: 3
latest admitted targets: 7
journey source-target pairs: 10
full generated source-target pairs: 570
full generated source triggers: 536
full targets very-common/common: 404 / 1984 = 20.4%
journey candidate-slice targets very-common/common: 172 / 200 = 86.0%
source mapping status: source_target_pairs_available
full source mapping status: full_source_target_pairs_available
```

Current target-side distribution:

```text
full_srs_admissible_universe:
  zipf_5_plus_very_common: 73 / 1984 = 3.7%
  zipf_4_to_5_common: 331 / 1984 = 16.7%
  zipf_3_to_4_mid: 825 / 1984 = 41.6%
  zipf_below_3_rare: 743 / 1984 = 37.5%
  missing: 12 / 1984 = 0.6%

journey_srs_candidate_slice:
  zipf_5_plus_very_common: 62 / 200 = 31.0%
  zipf_4_to_5_common: 110 / 200 = 55.0%
  zipf_3_to_4_mid: 26 / 200 = 13.0%
  zipf_below_3_rare: 2 / 200 = 1.0%

latest_admitted_srs_items:
  zipf_5_plus_very_common: 6 / 7 = 85.7%
  zipf_4_to_5_common: 1 / 7 = 14.3%
```

Current source-side rule distribution over the journey union:

```text
zipf_5_plus_very_common English sources: 8 / 10 = 80.0%
zipf_3_to_4_mid English sources: 2 / 10 = 20.0%
```

Current source-side rule distribution over full generated source triggers:

```text
zipf_5_plus_very_common English sources: 101 / 536 = 18.8%
zipf_4_to_5_common English sources: 218 / 536 = 40.7%
zipf_3_to_4_mid English sources: 144 / 536 = 26.9%
zipf_below_3_rare English sources: 51 / 536 = 9.5%
missing English sources: 22 / 536 = 4.1%
```

Interpretation:

- the SRS target denominator is not the same as the semantic-veto source
  denominator,
- the full installed SRS-admissible Spanish target universe is mostly mid and
  rare by Zipf count, while the journey top-200 slice is mostly very-common and
  common,
- current published journey rule families mostly use very-common English source
  triggers, but the full generated source-trigger denominator is mostly common
  and mid English sources,
- LLM cost planning should join both axes: high-exposure SRS targets only need
  expensive semantic-veto evidence when their English source-trigger families
  are ambiguity-prone,
- this is still bounded by the currently installed 2000-row Spanish frequency
  pack and generated rule families, not by an unlimited all-user or all-profile
  SRS distribution.

### Report 1m: Zipf Boundary Sweep

The current `5.0 / 4.0 / 3.0` Zipf bands are now a tested control, not an
unstated assumption:

```text
scripts/testing/semantic_veto_zipf_boundary_sweep_en_es.py
docs/test_outputs/semantic_veto_zipf_boundary_sweep_en_es_latest.json
docs/test_outputs/semantic_veto_zipf_boundary_sweep_en_es_latest.md
```

The sweep reads:

```text
latest difficulty-stratification case traces
full SRS Zipf bridge source-target pairs
```

Current run:

```text
case rows: 120
full generated source-target pairs: 570
schemes swept: 240
current scheme: current_5_4_3
current scheme rank: 129 / 240
current objective: -0.0014
best scheme: zipf_5p4_4p4_3p4
best objective: 0.1023
```

Current `5 / 4 / 3` observed case rows:

```text
very-common: 68 cases, 38.2% failure, 86.7% positive-abstain rate
common: 52 cases, 26.9% failure, 60.9% positive-abstain rate
mid: 0 cases
rare: 0 cases
```

Current `5 / 4 / 3` full generated source-family denominator:

```text
very-common: 109 / 570 = 19.1%
common: 235 / 570 = 41.2%
mid: 152 / 570 = 26.7%
rare: 52 / 570 = 9.1%
missing: 22 / 570 = 3.9%
```

Interpretation:

- the fixed `5 / 4 / 3` bands are reasonable reporting bands, but they are not
  proven optimal for explaining veto difficulty,
- the best current shifted schemes mostly raise the very-common/common
  thresholds, suggesting that the hardest observed cases may be concentrated in
  the upper part of the old very-common/common split,
- the sweep cannot promote new bands yet because the representative lane still
  has no mid or rare observed cases,
- this strengthens the next expansion requirement: fill mid and rare
  representative rows before treating any Zipf boundary as a stable difficulty
  curve.

### Report 1n: Full-Family Representative Manual Sample

The next sample is now frozen from the full generated source-target family
denominator instead of from the old hand-picked or journey-slice lanes:

```text
scripts/testing/semantic_veto_full_family_representative_sample_en_es.py
docs/test_outputs/semantic_veto_full_family_representative_sample_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_representative_sample_en_es_latest.md
```

This report does not author manual sentences. It freezes the families and case
slots that manual authoring should fill.

Current run:

```text
full generated source-target families: 570
eligible families after measured-trigger exclusion: 566
measured triggers excluded: 35
cell dimensions:
  source Zipf band
  source WordNet polysemy band
  source WordNet POS shape
non-empty cells: 30 / 80
sampled families: 58
planned active-positive cases: 116
planned shadow-negative cases: 80
planned phrase/no-winner cases: 58
planned total manual case slots: 254
```

Sampled source-band coverage:

```text
very-common: 16 sampled families
common: 15 sampled families
mid: 14 sampled families
rare: 10 sampled families
missing source Zipf: 3 sampled families
```

Sampled target-band coverage:

```text
very-common Spanish targets: 12
common Spanish targets: 19
mid Spanish targets: 23
rare Spanish targets: 4
```

Sampled source-polysemy coverage:

```text
high 10+ WordNet senses: 10
medium 4-9 WordNet senses: 14
low 1-3 WordNet senses: 25
missing WordNet profile: 9
```

Manual packet contract:

```text
per sampled family:
  active_positive: 2 rows
  phrase_no_winner: 1 row
  shadow_negative: 2 rows only when the source looks polysemic

single-sense or missing-shadow rows:
  keep shadow_negative not_applicable instead of inventing fake shadows
```

Interpretation:

- this is the first sample that directly attacks the missing mid/rare evidence
  problem from the full current rule-family denominator,
- the queue is small enough for manual work but large enough to represent all
  non-empty source-Zipf/polysemy/POS-shape cells,
- the planned 254 manual case slots are an upper bound before weakness-aware
  authoring drops duplicate or unsupported generated rows; they are not 1,984
  target tests and not 570 exhaustive family tests,
- once authored and scored, this packet should let us estimate positive allow
  and negative abstain by source band and source ambiguity instead of guessing.

### Report 1o: Full-Family Draft Manual Packet And First Score

The frozen 58-family queue has now been materialized into a scoreable
sentence-veto dataset:

```text
scripts/testing/semantic_veto_full_family_manual_packet_authoring_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_representative_manual_v1.json
docs/test_outputs/semantic_veto_full_family_manual_packet_authoring_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_manual_packet_authoring_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_manual_sentence_veto_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_manual_sentence_veto_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_manual_sentence_veto_st_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_manual_sentence_veto_st_en_es_latest.md
```

Current authored dataset:

```text
families: 58
cases: 206
active-positive cases: 73
shadow-negative cases: 75
phrase/no-winner cases: 58
mid-source-band cases: 50
rare-source-band cases: 32
review state: agent_draft_human_review_pending
```

First diagnostic scores:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 206
  decision accuracy: 80.6%
  positive recall: 45.2%
  harmful replace rate: 0.0%
  false abstain rate: 54.8%
  harmful replacements: 0
  false abstains: 40

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 206
  decision accuracy: 72.8%
  positive recall: 83.6%
  harmful replace rate: 33.1%
  false abstain rate: 16.4%
  harmful replacements: 44
  false abstains: 12
```

Interpretation:

- this is the first scoreable packet with explicit mid and rare source-band
  coverage from the full current source-target family denominator,
- the weakness-aware authoring pass removed unsupported duplicate rows, varied
  phrase/no-winner templates, and stopped putting WordNet examples into the
  default all_evidence_text view,
- the large drop in TF-IDF positive recall is useful evidence: the earlier
  99% lane was inflated by evidence/context overlap,
- the sentence-transformer result is now the better positive-allow signal, but
  harmful replacement leakage remains visible, especially on phrase/no-winner
  rows,
- neither score is a promotion claim because the rows are still
  `agent_draft_human_review_pending`,
- the next meaningful pass is a row-quality review and replacement of weak
  auto-authored contexts before treating the band curve as product evidence.

### Report 1p: Full-Family Score Surface

The first full-family scores now have a row-level surface report:

```text
scripts/testing/semantic_veto_full_family_score_surface_en_es.py
docs/test_outputs/semantic_veto_full_family_score_surface_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_score_surface_en_es_latest.md
```

Purpose:

```text
Take the same 206 full-family draft cases and break their outcomes down by:
  scorer
  English source Zipf band
  Spanish target Zipf band
  WordNet polysemy band
  WordNet POS shape
  manual case type
  source band x case type
```

Current scorer-level result:

```text
TF-IDF:
  decision accuracy: 80.6%
  positive allow: 45.2%
  shadow-negative abstain: 100.0%
  phrase/no-winner abstain: 100.0%

Sentence-transformer:
  decision accuracy: 72.8%
  positive allow: 83.6%
  shadow-negative abstain: 94.7%
  phrase/no-winner abstain: 31.0%
```

Current source-band result:

```text
TF-IDF decision accuracy by English source band:
  very-common: 76.3%
  common: 76.3%
  mid: 78.0%
  rare: 96.9%

Sentence-transformer decision accuracy by English source band:
  very-common: 74.6%
  common: 71.2%
  mid: 76.0%
  rare: 71.9%
```

Interpretation:

- the random/full-family packet did improve band representation because mid
  and rare rows are now present in the same scored packet as very-common and
  common rows,
- it does not yet prove a monotonic frequency curve; the current draft packet
  shows case-shape and row-quality effects more clearly than a simple
  beginner-vs-advanced split,
- the cleanest current signal is that TF-IDF is conservative after evidence
  separation, while sentence-transformer still over-replaces phrase/no-winner
  rows,
- the rare-source TF-IDF result looks promising but is based on only 32 cases
  and remains draft evidence,
- the right next research move is user review of active target-sense alignment
  and replacement of remaining definition-fallback rows, then rerun this
  surface before formula and Zipf-boundary sweeps.

### Report 1q: Evaluation Validity Remediation Plan

Fresh-perspective review of Report 1o/1p found that the pipeline structure is
now useful, but the data validity is not strong enough for product accuracy or
LLM-budget claims. These issues must stay explicit until fixed.

The current valid claim is narrow:

```text
We have a frozen, reproducible, mid/rare-inclusive full-family diagnostic
packet, and the first scorer runs expose row-shape and scorer behavior.
```

The current invalid claims are:

```text
do not claim product-wide veto accuracy
do not claim TF-IDF is solved
do not claim source frequency has a proven monotonic difficulty curve
do not claim shadow negatives are solved outside this drafted WordNet packet
do not use the raw unweighted 206-case score as the browsing/SRS distribution
```

#### Validity Gap 1: Evidence-Context Circularity

Problem:

```text
The generated context sentences often come from the same WordNet definitions,
examples, and wording used as scorer evidence.
```

Why it matters:

```text
If active evidence says "the month following May and preceding July" and the
positive context repeats that definition, a lexical scorer can pass through
overlap rather than real contextual discrimination.
```

Current symptom:

```text
After removing example text from default scorer evidence, TF-IDF reports 80.6%
decision accuracy and only 45.2% positive allow on the draft full-family
packet. That confirms the earlier 99.2% result was not a trustworthy product
accuracy estimate.
```

Required fix:

```text
Build an independent-context lane where evidence remains dictionary/WordNet/
rulegen-backed, but evaluation sentences come from a different source:
  observed browser/helper contexts when available,
  corpus examples,
  subtitle/news/wiki snippets,
  or human-authored browser-like contexts.
```

Acceptance before trust:

```text
Each row records context_source and evidence_source.
Rows with context_source overlapping evidence_source stay diagnostic-only.
Product or budget claims use only independent or human-reviewed contexts.
```

#### Validity Gap 2: Active Target Sense Is Not Audited

Problem:

```text
The authoring harness often treats the first WordNet sense of the English
source as the active sense for source -> Spanish target.
```

Why it matters:

```text
Rulegen can create source-target pairs where the Spanish target corresponds to
a later English sense, a narrow dictionary gloss, or a questionable mapping.
If the active evidence is the wrong sense, the gold label is unstable.
```

Examples that require care:

```text
sale -> deducción
shed -> puesto
grow -> acontecer
bar -> cercar
demand -> deducción
```

Required fix:

```text
Add an active-sense audit before accuracy claims:
  inspect source -> target against the rulegen evidence,
  mark active_sense_status as aligned, uncertain, or mismatched,
  keep uncertain/mismatched rows out of locked-eval promotion summaries,
  preserve them as source-quality diagnostics.
```

Acceptance before trust:

```text
Band and scorer claims report aligned-only, uncertain-only, and all-row views.
No candidate is promoted from rows whose active target sense is uncertain.
```

#### Validity Gap 2b: Shadow Competitors Are Not Reviewed Targets

Problem:

```text
Some shadow-negative rows still point at generated placeholders such as
"source alternate sense 1" instead of a real Spanish competitor replacement.
```

Why it matters:

```text
The veto decision is not just "does the English context differ from the active
gloss?" It is "should this source be replaced by the active Spanish target, or
is another sense/no-winner explanation stronger?" If the shadow side is not a
reviewed competitor target, the abstain label may be testing a phantom
competitor rather than a product decision.
```

Required fix:

```text
For shadow-negative trusted eval, require:
  reviewed Spanish shadow target,
  reviewed English shadow sense,
  context that truly supports the shadow target over the active target,
  and a reviewer decision that the active replacement should abstain.
```

Acceptance before trust:

```text
Rows with placeholder shadow targets stay blocking or diagnostic-only.
Score reports split real-shadow-competitor rows from placeholder-shadow rows.
```

#### Validity Gap 3: Phrase/No-Winner Rows Are Too Artificial

Problem:

```text
The current no-winner row is usually a repeated template:
The page listed "source" as a vocabulary term, not as a sentence meaning.
```

Why it matters:

```text
This is useful as a diagnostic sentinel, but it is not a realistic browsing
distribution. It may make some scorers look weak or strong for the wrong
reason, especially when measuring phrase/no-winner leakage.
```

Current symptom:

```text
Sentence-transformer phrase/no-winner abstain is only 31.0%, while
shadow-negative abstain is 94.7%. That tells us phrase/no-winner behavior is
still the clearest leakage axis, but it does not tell us the real browser rate.
```

Required fix:

```text
Split phrase/no-winner rows into explicit subtypes:
  mention_only: word appears as a listed term or label,
  metalinguistic: sentence talks about the word itself,
  named_entity_or_title: source appears in names/titles,
  phrase_collision: source is part of a longer phrase that should block,
  nonsemantic_fragment: surrounding text is too short or malformed,
  realistic_negative_context: source appears in natural text but no replacement
    should occur.
```

Acceptance before trust:

```text
The score surface reports phrase/no-winner by subtype.
Template-only no-winner rows are diagnostic controls, not product evidence.
```

#### Validity Gap 4: Stratified Sample Needs Weighted Estimates

Problem:

```text
The 58-family sample intentionally samples up to two families per non-empty
source-Zipf/polysemy/POS-shape cell. That gives coverage, not a product
frequency distribution.
```

Why it matters:

```text
Raw 206-case accuracy overrepresents small rare or underfilled cells and
underrepresents large cells like common/cross-POS/polysemic families.
```

Current available correction signal:

```text
Each sampled family already records cell_eligible_count, cell_sample_count, and
cell_sampling_weight.
```

Required fix:

```text
Every score surface should report:
  unweighted diagnostic metrics,
  cell-weighted source-family metrics,
  SRS-target-exposure-weighted metrics when target exposure is available,
  and eventually browsing-observation-weighted metrics when runtime logs exist.
```

Acceptance before trust:

```text
Any claim about "overall" quality states which weighting scheme it uses.
Raw unweighted scores are called diagnostic scores only.
```

#### Validity Gap 5: Single Seed Cannot Estimate Sampling Variance

Problem:

```text
The current representative packet uses one frozen stable-hash seed.
```

Why it matters:

```text
One seed is reproducible, but it cannot tell whether source-band results are
stable or dependent on the particular two words selected per cell.
```

Required fix:

```text
Add a no-spend multi-seed sampler over the same full denominator:
  keep the same cell definitions,
  generate several alternate sampled family queues,
  score only automatically available rows first,
  report variance by band and by cell,
  keep the current seed as the canonical hand-review packet.
```

Acceptance before trust:

```text
A source-band trend is treated as stable only if it persists across seeds or is
confirmed by reviewed/independent contexts.
```

#### Validity Gap 6: Data Quality And Scorer Quality Are Entangled

Problem:

```text
A failure row can mean several different things:
  bad scorer,
  bad threshold,
  wrong active sense,
  weak generated context,
  impossible or questionable rulegen mapping,
  artificial no-winner template,
  missing shadow evidence,
  or real semantic ambiguity.
```

Why it matters:

```text
Without row-quality labels, scorer bakeoffs can optimize against flawed rows or
discard useful scorer ideas because the data lane was contaminated.
```

Required fix:

```text
Add row_quality_status and failure_review_status:
  row_quality_status: trusted, needs_review, weak_context,
    active_sense_uncertain, active_sense_mismatch, no_winner_template_control,
    source_mapping_questionable
  failure_review_status: unreviewed, scorer_error, data_error, ambiguous,
    expected_under_current_policy
```

Acceptance before trust:

```text
Score reports split failures by row_quality_status and failure_review_status.
Promotion summaries use trusted/aligned rows; diagnostics can still include all
rows, but must label them.
```

#### Recommended Execution Order

Do not jump straight back to scorer tuning. The next work should repair
evaluation validity in this order:

```text
1. Add row-quality and active-sense-status fields to the full-family packet.
2. Review the 58 sampled source-target families for active target-sense
   alignment.
3. Replace placeholder shadow targets with reviewed Spanish competitor targets
   before using shadow-negative rows as trusted abstain evidence.
4. Replace or subtype phrase/no-winner rows, starting with the 58 current
   template rows.
5. Add independent-context rows for a small slice of the same frozen families.
6. Rerun TF-IDF and sentence-transformer score surfaces with:
     all rows,
     trusted/aligned rows,
     diagnostic template-control rows,
     and independent-context rows.
7. Add weighted estimates using existing cell_sampling_weight.
8. Run multi-seed sampling to measure whether band trends survive different
   sampled families.
9. Only then rerun formula, threshold, and Zipf-boundary sweeps for promotion
   or LLM-budget planning.
```

#### Planned Artifacts

Likely artifact lane:

```text
docs/test_inputs/semantic_routing_cases/en_es_full_family_representative_manual_v1.json
scripts/testing/semantic_veto_full_family_human_review_packet_en_es.py
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_evaluation_validity_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_evaluation_validity_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_score_surface_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_score_surface_en_es_latest.md
```

The first validity report should answer:

```text
How many rows are trusted versus diagnostic-only?
How many active source-target families have aligned, uncertain, or mismatched
active target senses?
How many no-winner rows are artificial templates versus realistic negatives?
How different are all-row scores from trusted-row scores?
How different are raw unweighted scores from cell-weighted scores?
```

### Report 1r: Full-Family Human Review Pilot Packet

The first user-review packet has been generated:

```text
scripts/testing/semantic_veto_full_family_human_review_packet_en_es.py
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.md
```

Scope:

```text
dataset families: 58
pilot review families: 10
pilot review cases: 34
trusted families: 0
trusted cases: 0
```

Pilot selection:

```text
Round-robin across non-missing English source Zipf bands first, preferring
shadow-bearing, high-polysemy, cross-POS, and natural-example-backed families
before easier or metadata-missing rows. Missing source-band rows are fallback
coverage only.
```

Current pilot family mix:

```text
very-common source band: 3 families
common source band: 3 families
mid source band: 2 families
rare source band: 2 families
missing source band: 0 families
```

Current pilot case mix:

```text
positive_active: 12
shadow_negative: 12
phrase_no_winner: 10
```

Review rule:

```text
Every family and case is pending_user_review.
No row is trusted.
No score surface may treat this packet as reviewed evidence until the user
fills or approves the review decisions.
```

Fields exposed for review:

```text
family-level:
  human_review_status
  active_sense_status
  active_sense_notes
  corrected_active_evidence
  family_disposition

case-level:
  human_review_status
  gold_decision
  row_quality_status
  no_winner_subtype
  corrected_sentence
  notes
```

Interpretation:

- this packet is the first concrete bridge from agent-draft rows to
  user-reviewed semantic ground truth,
- it intentionally includes high-polysemy/cross-POS families, shadow-negative
  rows, and phrase/no-winner rows so the review format tests the important
  failure surfaces,
- it is still a review packet, not a scored evidence lane,
- after user review, a separate reviewed-decision artifact should be created
  instead of overwriting the original agent-draft packet silently.

#### Report 1r-Weaknesses: Test Weakness Taxonomy

The review packet now carries a named weakness taxonomy:

```text
docs/test_inputs/semantic_veto_test_weakness_taxonomy_en_es.json
```

Purpose:

```text
Make test-quality problems explicit before rows are trusted, so the project can
separate "the scorer failed" from "the evaluation row was weak, circular, or
unaudited."
```

Current weakness classes:

```text
family-level:
  active_target_sense_not_audited
  source_target_mapping_questionable
  source_form_artifact_risk

case-level:
  active_context_template_circular
  evidence_context_overlap_risk
  shadow_negative_synthetic_definition_context
  shadow_competitor_target_not_reviewed
  shadow_negative_may_still_match_target
  duplicate_case_sentence
  phrase_no_winner_template_control_only
  no_winner_token_boundary_artifact

packet-level:
  review_markdown_missing_case_fields
  pilot_not_hard_case_representative
```

Current pilot pre-triage summary:

```text
review-required weakness instances: 13
blocking weakness instances: 12
diagnostic-only weakness instances: 26
packet weaknesses: none
```

Interpretation:

```text
The packet is cleaner as a review artifact, but the stricter taxonomy now
correctly blocks trusted shadow-negative use until real Spanish competitor
targets are reviewed. This is intentional: the packet should prevent us from
forgetting that placeholder shadows are not product ground truth.
```

Change from the first taxonomy pass:

```text
before weakness-aware authoring/selection:
  review cases: 40
  review-required weaknesses: 12
  blocking weaknesses: 6
  diagnostic-only weaknesses: 66
  packet weakness: pilot_not_hard_case_representative

after weakness-aware authoring/selection:
  review cases: 34
  review-required weaknesses before stricter shadow/token checks: 10
  diagnostic-only weaknesses: 26
  packet weaknesses: none

after stricter trust-boundary checks:
  review-required weaknesses: 13
  blocking weaknesses: 12
  diagnostic-only weaknesses: 26
  newly visible blocking class: shadow_competitor_target_not_reviewed
  newly visible review class: no_winner_token_boundary_artifact
```

Interpretation:

- weakness labels are not runtime veto decisions,
- weakness labels are not proof that a row is useless,
- blocking labels mean the row should not count as an independent trusted
  evaluation case until repaired or explicitly excluded,
- diagnostic-only labels can still be useful controls, but must not be mixed
  into trusted product-accuracy claims,
- review-required labels mean the user must decide whether the source-target
  family or row is semantically valid.

The practical review rule is:

```text
Before a row becomes trusted, remove or explicitly approve every blocking and
review-required weakness. Keep diagnostic-only rows in a separate control lane
unless the row is rewritten into independent, browser-like context.
```

### Report 1s: Agent Manual Review Of The Pilot Packet

The first direct semantic review of the 10-family pilot packet has been
recorded separately from the generated packet:

```text
docs/test_outputs/semantic_veto_full_family_agent_manual_review_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_agent_manual_review_en_es_latest.md
```

Authority boundary:

```text
This is codex_agent_recommendation_not_user_approval.
It does not mark any row approved_by_user.
It is a triage artifact for deciding what to rewrite, audit, or discard.
```

Reviewed scope:

```text
families reviewed: 10
cases reviewed: 34
trusted families now: 0
trusted cases now: 0
```

Main finding:

```text
The pilot packet is useful precisely because it exposed a larger data-quality
problem: 6 of 10 active source-target families are not currently usable as
trusted positive rows. They either point at the wrong WordNet active sense or
need a source-target mapping audit before any scorer claim.
```

Family-level triage:

```text
aligned mapping, contexts need independent rewrites:
  december -> diciembre
  emotion -> emoción
  dentist -> dentista
  bouillon -> caldo

active sense mismatched, but family may be salvageable after correction:
  break -> quebrar
  bridle -> reprimir
  control -> gobernar

source-target mapping questionable or likely wrong until rulegen evidence is
audited:
  bar -> cercar
  offset -> distancia
  demand -> deducción
```

Case-level triage:

```text
positive_active:
  4 keep only after independent context rewrite
  8 reject or relabel

shadow_negative:
  12 blocked by placeholder shadow targets
  10 likely abstain after real Spanish shadow target
  2 ambiguous or possible active after active-sense correction

phrase_no_winner:
  2 usable after review or minor rewrite
  3 diagnostic token-boundary controls only
  5 questionable or relabel
```

Practical consequence:

```text
The next trusted-eval construction should not try to perfect all 10 pilot
families at once. Start with the 4 aligned families to prove the review-to-
trusted-eval workflow, then correct salvageable active senses, then audit or
drop questionable source-target mappings.
```

### Report 1t: Repaired Pilot Candidate

The first repair pass has been implemented as a separate reproducible candidate
lane rather than by overwriting the generated draft packet:

```text
scripts/testing/semantic_veto_full_family_repair_pilot_en_es.py
core/tests/dev/test_semantic_veto_full_family_repair_pilot_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_pilot_v1.json
docs/test_outputs/semantic_veto_full_family_repair_pilot_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_repair_pilot_en_es_latest.md
```

Authority boundary:

```text
manual_review_state: agent_repaired_user_review_pending
trusted families now: 0
trusted cases now: 0
```

Repair policy:

```text
keep aligned or salvageable pilot families
correct active senses where the source-target mapping is salvageable
defer questionable source-target mappings instead of forcing them into tests
use real Spanish shadow targets, not placeholder alternate-sense labels
replace definition fallbacks with independent contexts
require standalone source tokens in every row
```

Repaired scope:

```text
repaired families: 7
repaired cases: 27
positive_active: 14
shadow_negative: 6
phrase_no_winner: 7
deferred families: 3
```

Repaired families:

```text
active sense corrected:
  break -> quebrar
  bridle -> reprimir
  control -> gobernar

aligned mapping, contexts rewritten:
  december -> diciembre
  emotion -> emoción
  dentist -> dentista
  bouillon -> caldo
```

Deferred until source-target mapping audit:

```text
bar -> cercar
offset -> distancia
demand -> deducción
```

The repaired candidate passes these mechanical checks:

```text
has active, shadow, and no-winner cases
all rows are pending user review
no placeholder shadow targets
all cases contain the source as a standalone token
no definition-fallback templates
no trusted rows claimed
```

Diagnostic scoring artifacts:

```text
docs/test_outputs/semantic_veto_full_family_repaired_pilot_sentence_veto_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_repaired_pilot_sentence_veto_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_repaired_pilot_sentence_veto_st_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_repaired_pilot_sentence_veto_st_en_es_latest.md
```

Current diagnostic scores:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 27
  decision accuracy: 55.6%
  replace recall: 14.3%
  harmful replacements: 0
  false abstains: 12

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 27
  decision accuracy: 70.4%
  replace recall: 78.6%
  harmful replacements: 5
  false abstains: 3
```

Interpretation:

```text
The repaired data lane is materially cleaner than the draft pilot, but it is
not a promotion result. The score pattern still shows the familiar tradeoff:
TF-IDF is conservative and avoids harmful replacements, while the
sentence-transformer recovers more positives but leaks on abstain rows.
```

Next rule:

```text
Do not tune thresholds from this repaired candidate until the user reviews the
rows or the lane is split into discovery and locked-eval slices.
```

### Report 1u: Trusted Eval Seed From User-Approved Repaired Pilot

The repaired pilot has crossed the user-review gate and has been copied into a
separate trusted seed dataset:

```text
scripts/testing/semantic_veto_full_family_trusted_eval_seed_en_es.py
core/tests/dev/test_semantic_veto_full_family_trusted_eval_seed_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v1.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_en_es_latest.md
```

Approval boundary:

```text
approval_id: user_step7_repaired_pilot_approval_2026_05_07
manual_review_state: approved_by_user
row_quality_status: trusted
trusted families: 7
trusted cases: 27
excluded families: 3
```

Important scope limit:

```text
This approval applies to the repaired 7-family pilot only.
It does not approve the deferred source-target mappings:
  bar -> cercar
  offset -> distancia
  demand -> deducción
```

The trusted seed is still not a discovery/locked split:

```text
It can establish the post-approval baseline.
It must not be used for threshold tuning and then cited as locked-eval
performance.
```

Trusted seed diagnostic scoring artifacts:

```text
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_sentence_veto_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_sentence_veto_tfidf_en_es_latest.md
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_sentence_veto_st_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_sentence_veto_st_en_es_latest.md
```

Current trusted-seed diagnostic scores:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 27
  decision accuracy: 55.6%
  replace recall: 14.3%
  harmful replacements: 0
  false abstains: 12

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 27
  decision accuracy: 70.4%
  replace recall: 78.6%
  harmful replacements: 5
  false abstains: 3
```

Step status after approval:

```text
Step 7 user review of repaired lane: done for the 7 repaired families.
Step 8 deferred mapping audit: done for 3 excluded families.
Step 9 discovery/locked split: still open.
Step 10 scorer/bakeoff on trusted rows: baseline diagnostics done; tuning is
not allowed until Step 9 creates the split.
```

### Report 1v: Deferred Source-Target Mapping Audit

The three excluded pilot mappings have now been audited against the SRS
source-target bridge and local installed en-es dictionary/sense packs:

```text
scripts/testing/semantic_veto_deferred_mapping_audit_en_es.py
core/tests/dev/test_semantic_veto_deferred_mapping_audit_en_es.py
docs/test_outputs/semantic_veto_deferred_mapping_audit_en_es_latest.json
docs/test_outputs/semantic_veto_deferred_mapping_audit_en_es_latest.md
```

Authority boundary:

```text
runtime policy change: none
trusted seed change: none
new trusted rows: 0
purpose: decide whether deferred mappings are repairable or should be replaced
```

Audit result:

```text
bar -> cercar:
  status: salvageable_with_corrected_active_sense
  evidence: reverse dictionary has cercar -> bar; source-side evidence supports
    bar as obstruct/lock/bolt; target-side evidence supports cercar as
    corral/fence/fence off
  rule: do not revive alcohol-bar rows; author fresh verb/blockage rows only

offset -> distancia:
  status: salvageable_with_corrected_active_sense
  evidence: reverse dictionary has distancia -> offset; source-side evidence
    supports offset as distance/out-of-alignment; target-side evidence supports
    distancia as distance
  rule: author fresh technical/spatial rows only if the broad target
    distancia is acceptable; otherwise prefer a more specific Spanish target

demand -> deducción:
  status: reject_mapping_source_target_mismatch
  evidence: reverse dictionary has deducción -> demand, but source-side demand
    senses are request/claim/economic demand and target-side deducción is
    deduction
  rule: keep excluded unless independent source evidence proves a valid sense;
    replace this sampled slot from the same representative cell
```

Important methodological lesson:

```text
The bad draft rows were not just weak contexts. They exposed a source-data
boundary: a reverse dictionary pair can enter the source-target denominator
without enough sense evidence to choose the active English sense. The fix is
not to manually force the first WordNet sense; it is to audit the mapping,
author fresh pending-review rows only when the mapping is coherent, and keep
bad pairs out of trusted eval.
```

### Report 1w: Deferred Mapping Manual Review Fix

The deferred mapping audit has now been followed by an agent manual repair
packet. This is a fixed review candidate, not trusted evaluation data:

```text
scripts/testing/semantic_veto_deferred_mapping_review_fix_en_es.py
core/tests/dev/test_semantic_veto_deferred_mapping_review_fix_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_deferred_mapping_review_fix_v1.json
docs/test_outputs/semantic_veto_deferred_mapping_review_fix_en_es_latest.json
docs/test_outputs/semantic_veto_deferred_mapping_review_fix_en_es_latest.md
```

Manual review and fix result:

```text
fixed families: 3
fixed cases: 15
positive-active rows: 6
shadow-negative rows: 6
phrase/no-winner rows: 3
trusted rows: 0
manual review state: agent_reviewed_user_review_pending
```

What changed:

```text
bar -> cercar:
  repaired as the verb/blockage sense only
  rejected draft alcohol-bar active rows
  real Spanish shadow competitors: taberna, barra

offset -> distancia:
  repaired as the spatial/technical distance sense only
  rejected draft outset/compensation active rows
  real Spanish shadow competitors: compensar, compensación
  note: broad target adequacy for distancia still needs user review

demand -> deducción:
  rejected as a source-target mismatch
  replaced by crack -> grieta in the same source Zipf/polysemy/POS-shape cell
  real Spanish shadow competitors: broma, chasquido
```

Mechanical quality checks all pass:

```text
salvageable audit rows repaired: yes
rejected mapping not repaired as same pair: yes
replacement family same source cell: yes
active, shadow, and no-winner cases present: yes
all rows pending user review: yes
placeholder shadow targets: 0
definition fallback templates: 0
non-standalone source tokens: 0
trusted rows claimed: 0
```

Sentence-veto smoke diagnostics on the fixed packet:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 15
  decision accuracy: 66.7%
  replace recall: 33.3%
  harmful replacements: 1
  false abstains: 4
  winner accuracy: 41.7%
  shadow winner accuracy: 0.0%

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 15
  decision accuracy: 66.7%
  replace recall: 66.7%
  harmful replacements: 3
  false abstains: 2
  winner accuracy: 75.0%
  shadow winner accuracy: 83.3%
```

Interpretation:

```text
The packet now tests real source-target decisions instead of first-sense
fallbacks or placeholder shadows. The diagnostic scores are not promotion
claims: TF-IDF is still conservative and sentence-transformer still leaks
metalinguistic no-winner rows. That is useful signal because the fixed packet
now exposes scorer behavior on real competitor cases.
```

Authority boundary:

```text
runtime policy change: none
trusted seed change: none
new trusted rows: 0
next step: user review before trusted addendum or seed rerun
```

### Report 1x: Trusted Eval Seed v2 From Approved Deferred Fix

The user approved the GPT-5.5-reviewed deferred mapping repair rows for the
purpose of moving the testing workstream forward. A second trusted seed now
keeps the old v1 seed intact and adds the 15 approved deferred-fix rows:

```text
scripts/testing/semantic_veto_full_family_trusted_eval_seed_v2_en_es.py
core/tests/dev/test_semantic_veto_full_family_trusted_eval_seed_v2_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v2.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_v2_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_v2_en_es_latest.md
```

v2 trusted data shape:

```text
trusted families: 10
trusted cases: 42
carried-forward v1 families: 7
newly approved deferred-fix families: 3
newly approved deferred-fix cases: 15
case mix: 20 positive-active, 12 shadow-negative, 10 phrase/no-winner
approval ids:
  user_step7_repaired_pilot_approval_2026_05_07: 27 rows
  user_step8_deferred_mapping_review_fix_approval_2026_05_07: 15 rows
rejected mappings still excluded: demand -> deducción
```

Authority boundary:

```text
runtime policy change: none
production scorer promotion: none
trusted data status: approved seed for near-term diagnostics
locked-eval status: not an untouched locked split
```

v2 sentence-veto diagnostics:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 42
  decision accuracy: 59.5%
  replace precision: 100.0%
  replace recall: 15.0%
  harmful replacements: 0
  false abstains: 17
  winner accuracy: 56.2%
  shadow winner accuracy: 8.3%

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 42
  decision accuracy: 69.0%
  replace precision: 65.2%
  replace recall: 75.0%
  harmful replacements: 8
  false abstains: 5
  winner accuracy: 81.2%
  shadow winner accuracy: 91.7%
```

Interpretation:

```text
The approved v2 seed is now good enough to run near-term scorer bakeoffs and
data-quality tests without mixing pending-review rows into the denominator.
It still cannot support promotion claims by itself. Its first diagnostic result
shows a real scorer tradeoff: TF-IDF is safe but under-allows positives, while
sentence-transformer recovers positives and shadow winners but leaks
phrase/no-winner negatives.
```

### Report 1y: Trusted Seed v2 Band Performance

The band test has now been rerun on the approved trusted v2 denominator rather
than the older agent-draft full-family packet:

```text
scripts/testing/semantic_veto_trusted_seed_v2_band_performance_en_es.py
core/tests/dev/test_semantic_veto_trusted_seed_v2_band_performance_en_es.py
docs/test_outputs/semantic_veto_trusted_seed_v2_band_performance_en_es_latest.json
docs/test_outputs/semantic_veto_trusted_seed_v2_band_performance_en_es_latest.md
```

Input scorer reports:

```text
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_v2_sentence_veto_tfidf_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_trusted_eval_seed_v2_sentence_veto_st_en_es_latest.json
```

Band data shape:

```text
unique trusted cases: 42
unique trusted families: 10
case mix: 20 positive-active, 12 shadow-negative, 10 phrase/no-winner
source Zipf bands:
  zipf_5_plus_very_common: 13 cases
  zipf_4_to_5_common: 13 cases
  zipf_3_to_4_mid: 8 cases
  zipf_below_3_rare: 8 cases
```

Overall scorer behavior on the trusted v2 denominator:

```text
TF-IDF:
  decision accuracy: 59.5%
  positive allow: 15.0%
  shadow-negative abstain: 100.0%
  phrase/no-winner abstain: 100.0%
  harmful replacements: 0
  false abstains: 17

Sentence-transformer:
  decision accuracy: 69.0%
  positive allow: 75.0%
  shadow-negative abstain: 100.0%
  phrase/no-winner abstain: 20.0%
  harmful replacements: 8
  false abstains: 5
```

Band-level directional result:

```text
claim strength: directional_underpowered

The bands are now trusted, but they are still small. The clearest signal is
not yet a stable frequency curve; it is the case-type/scorer interaction.

TF-IDF is safe in every source band but under-allows positives:
  very-common: 16.7% positive allow
  common: 33.3% positive allow
  mid: 0.0% positive allow
  rare: 0.0% positive allow

Sentence-transformer allows positives much more often but leaks
phrase/no-winner negatives:
  very-common: 83.3% positive allow, 33.3% phrase/no-winner abstain
  common: 66.7% positive allow, 0.0% phrase/no-winner abstain
  mid: 100.0% positive allow, 0.0% phrase/no-winner abstain
  rare: 50.0% positive allow, 50.0% phrase/no-winner abstain
```

Comparison to the older 206-row draft full-family surface:

```text
TF-IDF on trusted v2 is safer but much less permissive than the draft surface:
  positive allow delta: -30.2 points
  harmful replacement delta: no change at 0

Sentence-transformer on trusted v2 has fewer harmful replacements in absolute
count because the denominator is much smaller, and it remains the only scorer
with strong positive-active recovery:
  positive allow delta: -8.6 points
  shadow-negative abstain delta: +5.3 points
  phrase/no-winner abstain delta: -11.0 points
```

Current interpretation:

```text
This answers where we are on the roadmap: we have resumed band testing on
reviewed data, but the current band report is still underpowered. It is strong
enough to guide next diagnostics, not strong enough to claim that frequency
alone predicts veto difficulty. The next useful tests should focus on
separating phrase/no-winner handling from ordinary active-vs-shadow scoring and
then expanding the tiny source-band x case-type cells.
```

### Report 1z: Full 58-Family Agent Review Before Band Sweeps

The full-family review packet has been expanded from the original 10-family
pilot surface to all 58 frozen representative-sample families:

```text
scripts/testing/semantic_veto_full_family_human_review_packet_en_es.py
core/tests/dev/test_semantic_veto_full_family_human_review_packet_en_es.py
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.md
```

Full packet shape:

```text
families: 58
cases: 206
case mix:
  positive-active: 73
  shadow-negative: 75
  phrase/no-winner: 58
source Zipf families:
  zipf_5_plus_very_common: 16
  zipf_4_to_5_common: 15
  zipf_3_to_4_mid: 14
  zipf_below_3_rare: 10
  missing: 3
trusted rows: 0
```

A full agent semantic review now records which sampled families should be
repaired or excluded before any new formula or band-boundary sweep is treated
as meaningful:

```text
scripts/testing/semantic_veto_full_family_agent_review_en_es.py
core/tests/dev/test_semantic_veto_full_family_agent_review_en_es.py
docs/test_outputs/semantic_veto_full_family_agent_review_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_agent_review_en_es_latest.md
```

Agent-review result:

```text
reviewed families: 58
repair-pool families: 49
excluded families: 9
draft rows inspected through packet: 206
draft shadow rows: 75

family dispositions:
  aligned_mapping_rewrite_contexts: 18
  aligned_mapping_shadow_rows_not_competitors: 16
  salvage_with_corrected_active_sense: 15
  source_target_mapping_rejected: 5
  source_form_artifact_rejected: 3
  questionable_mapping_rejected: 1

repair-pool source bands:
  zipf_5_plus_very_common: 16
  zipf_4_to_5_common: 11
  zipf_3_to_4_mid: 14
  zipf_below_3_rare: 8
```

Interpretation:

```text
This changes the immediate path. The best next denominator is not the old
10-family trusted seed and not the unreviewed 206-row draft packet. It is the
49-family repair pool after rows are reauthored from the full review.

This is still not user-approved gold data. It is an agent review that decides
which families deserve repair effort. The next step is to materialize repaired
case rows from the 49-family pool, drop same-target POS shadows that are not
real competitors, and exclude rejected/artifact mappings before rerunning
scoring or band-formula sweeps.
```

### Report 1aa: Full 49-Family Repair Pool

The full 58-family agent review has been materialized into a repaired
pending-user-review candidate:

```text
scripts/testing/semantic_veto_full_family_repair_pool_en_es.py
core/tests/dev/test_semantic_veto_full_family_repair_pool_en_es.py
docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json
docs/test_outputs/semantic_veto_full_family_repair_pool_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_repair_pool_en_es_latest.md
```

Repair-pool shape:

```text
reviewed families: 58
repaired families: 49
excluded families: 9
repaired cases: 189
case mix:
  positive-active: 98
  shadow-negative: 42
  phrase/no-winner: 49
trusted rows: 0

source-band case counts:
  zipf_5_plus_very_common: 60
  zipf_4_to_5_common: 42
  zipf_3_to_4_mid: 57
  zipf_below_3_rare: 30
```

Mechanical checks:

```text
all 49 expected repair-pool families materialized
every family has positive-active and phrase/no-winner rows
shadow-negative rows use real Spanish competitor targets
placeholder shadow targets removed
definition-fallback templates removed
all cases keep standalone source tokens
rejected families excluded
no trusted rows claimed
```

Diagnostic sentence-veto scoring over the repaired-full candidate:

```text
TF-IDF, masked_sentence/all_evidence_text:
  cases: 189
  decision accuracy: 50.3%
  replace precision: 83.3%
  replace recall: 5.1%
  harmful replacements: 1
  false abstains: 93
  shadow winner accuracy: 23.8%

Sentence-transformer, masked_sentence/all_evidence_text:
  cases: 189
  decision accuracy: 73.0%
  replace precision: 68.8%
  replace recall: 87.8%
  harmful replacements: 39
  false abstains: 12
  shadow winner accuracy: 81.0%
```

Interpretation:

```text
This completes the full repair pass, but not the approval pass. The repaired
denominator is now large enough to make the next band/formula sweeps much less
toy-like than trusted seed v2, while still preserving the row-authority boundary:
all rows are agent_repaired_full_user_review_pending.

The diagnostic scores are intentionally not promotion claims. They show a
stronger and more realistic scorer tradeoff on the repaired denominator:
TF-IDF is safe but barely allows positives; sentence-transformer recovers
positives but leaks many harmful replacements. That makes the next useful work
band/formula and phrase/no-winner analysis over this repaired-full lane, after
any user approval or locked split we choose to apply.
```

### Report 2: LLM Data Budget Planner

This report should run after Report 1.

Likely script:

```text
scripts/testing/semantic_veto_llm_budget_plan_en_es.py
```

Purpose:

```text
Given rank-bin risk, estimate how many generated evaluation rows are needed per
bucket and which model quality tier should be used.
```

Possible policies:

```text
top 500 triggers: high-quality model, dense active/shadow/phrase coverage
501-1000: high-quality model if risk score is high, otherwise medium sample
1001-5000: stratified sample
>5000: sparse sentinel sample plus source-coverage checks
unranked: sample if admitted by profile/topic relevance
```

### Report 3: SRS Admission Difficulty Surface

This should connect semantic-veto difficulty to admission planning.

Likely script:

```text
scripts/testing/srs_semantic_difficulty_surface_en_es.py
```

Purpose:

```text
Combine learner value, learner difficulty, and veto difficulty into an
operator-readable admission surface.
```

Output examples:

```text
high value / low learner difficulty / low veto risk
high value / low learner difficulty / high veto risk
high value / advanced / low veto risk
topic-relevant but source-poor
admit with conservative replacement
admit review-only
defer until source coverage improves
```

## Metrics

For every bin, report:

```text
case_count
family_count
positive_allow_rate
negative_abstain_rate
phrase_no_winner_abstain_rate
shadow_negative_abstain_rate
positive_abstain_count
negative_allow_count
utility_score
manual_vs_llm_delta
source_coverage_rate
metadata_missing_rate
```

For words/triggers, report:

```text
trigger
target_lemma
source_trigger_rank_en
target_lemma_rank_es
learner_value_score
learner_difficulty_score
veto_decision_difficulty_score
observed_failure_classes
recommended_research_action
recommended_srs_action
```

Recommended SRS actions:

```text
admit_normal
admit_conservative_replacement
admit_review_only
defer_for_source_coverage
defer_for_level
sample_for_llm_eval
```

## Methodology Guardrails

### Keep Evaluation Lanes Separate

Do not blend:

```text
manual v10
manual/stress wave7
LLM discovery
LLM locked-eval
future representative browsing lanes
```

Each can answer a different question. The report can compare them, but it must
not hide their distribution differences.

### Do Not Tune On Locked Eval

If a threshold or scorer change is proposed from difficulty stratification, use:

```text
discovery for candidate selection
locked-eval for post-selection check
manual/stress for robustness check
future representative browsing data for promotion claims
```

### Separate User Relevance From Correctness

Topic preference can increase admission priority. It cannot make a risky veto
decision correct.

### Treat Missing Metadata As A Finding

If rank, sense count, or coverage cannot be resolved, the row remains in the
denominator and gets a missing-metadata flag.

### Avoid The Beginner-Word Trap

Do not conclude:

```text
beginner words are bad admissions
```

The correct conclusion may be:

```text
beginner words are high-value admissions that need safer replacement policy or
better source coverage.
```

## How This Can Reduce LLM Spend

If failure mass clusters in high-frequency source triggers, then expensive LLM
generation should be concentrated there.

Possible spend strategy:

```text
1. run no-spend stratification over current artifacts,
2. identify top-risk rank bins and individual triggers,
3. generate dense high-quality rows only for top-risk high-exposure triggers,
4. use cheaper or sparse sampling for lower-risk bins,
5. reserve locked-eval rows before using discovery rows for threshold or source
   decisions.
```

This strategy is only justified if Report 1 shows rank or veto-difficulty
features actually predict failure concentration.

## Product Interpretation

The end state should support statements like:

```text
The app is conservative enough for beginner high-risk words.
Intermediate words show better replacement accuracy.
Advanced words need source-coverage checks but are not uniformly risky.
Top-1000 English triggers deserve denser LLM evaluation.
SRS admission can admit useful risky words while using safer replacement
behavior.
```

If the data does not support those statements, the report should say so.

## Implementation Checklist

### Phase 0: Inventory Existing Metadata

- Locate installed/configured English and Spanish frequency packs.
- Confirm how to resolve source-trigger rank and target-lemma rank.
- Confirm whether CEFR exists anywhere locally; if not, mark it future input.
- Confirm available WordNet sense-count and POS-count sources.
- Confirm available translation fan-out sources.
- Confirm profile-context topic/preference fields available to offline tests.

### Phase 1: Build Feature Join

- Join each semantic-veto case row to trigger and target metadata.
- Preserve lane identity.
- Preserve source evidence counts and score margins.
- Emit missing-metadata diagnostics.
- Add tests for rank-bin assignment, missing metadata, and lane preservation.

### Phase 2: Emit Stratified Metrics

- Bin by English source-trigger rank.
- Bin by Spanish target-lemma rank.
- Bin by polysemy count.
- Bin by phrase-control count.
- Bin by source evidence coverage.
- Emit top risky/safe word tables.

### Phase 3: Budget Planner

- Use observed failure concentration to propose LLM generation density.
- Keep discovery and locked-eval quotas separate.
- Recommend model quality tier by risk bucket.
- Emit expected row counts and estimated coverage.

### Phase 4: SRS Admission Surface

- Combine learner value, learner difficulty, and veto difficulty.
- Generate admission recommendations.
- Keep the output advisory until product policy accepts it.

### Phase 5: Policy Integration

Only after reports are validated:

- decide whether SRS admission should penalize veto risk,
- decide whether high-risk words should be admitted with conservative runtime
  behavior,
- decide whether topic-relevant but high-risk words need explicit user-facing
  mode,
- update helper/UI contracts if new signals become executable.

## Open Questions To Ask

Useful next questions:

```text
Are false allows concentrated in the first 500 or 1000 English triggers?
Does source-trigger frequency predict failures after controlling for polysemy?
Does WordNet sense count predict failures better than frequency rank?
Does Spanish target rank predict learner value independently of veto risk?
Which beginner words are safe enough for normal admission and replacement?
Which beginner words should be admitted only with conservative replacement?
How much LLM data do we need for the top 1000 triggers?
Should SRS admission use veto risk as a penalty, a mode switch, or only a
diagnostic?
Do profile topics increase value enough to override higher difficulty, but not
override veto risk?
```

## First Recommended Work Slice

Implement `semantic_veto_difficulty_stratification_en_es.py` as a no-spend
report over current artifacts.

Minimum acceptance for the first slice:

```text
reads LLM pilot scoring rows
reads manual/stress validation rows
preserves lane identity
attempts English source-trigger rank lookup
attempts Spanish target-lemma rank lookup
emits rank-bin metrics
emits missing-metadata summary
emits top risky beginner trigger table
does not change runtime policy
does not promote source evidence
```

Validation commands should include:

```bash
PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_difficulty_stratification_en_es.py

python3 scripts/dev/check_doc_references.py
git diff --check
```

## 2026-05-08: Approved Repaired-Full Sweep Lane

The full repaired dataset is now approved by the user for exploratory sweeps:

```text
dataset: docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json
families: 49
cases: 189
positive-active: 98
shadow-negative: 42
phrase/no-winner: 49
manual_review_state: approved_by_user
row_quality_status: trusted
approval_id: user_approved_full_repaired_dataset_2026_05_08
```

This approval changes the data-authority state for the repaired-full lane. It
does not make the lane a final locked evaluation set and it does not change
runtime policy.

### Repaired-Full Scorer Surface

Current scorer diagnostics over the approved repaired-full lane:

```text
TF-IDF:
  decision accuracy: 50.3%
  positive allow: 5.1%
  shadow-negative abstain: 97.6%
  phrase/no-winner abstain: 100.0%
  harmful replacements: 1 / 91 gold-abstain cases
  false abstains: 93 / 98 gold-replace cases

Sentence-transformer:
  decision accuracy: 73.0%
  positive allow: 87.8%
  shadow-negative abstain: 90.5%
  phrase/no-winner abstain: 28.6%
  harmful replacements: 39 / 91 gold-abstain cases
  false abstains: 12 / 98 gold-replace cases
```

Interpretation:

- TF-IDF is safe but unusably conservative for positive replacements.
- Sentence-transformer is close to the product positive-allow goal but leaks
  badly on phrase/no-winner rows.
- The main current product gap is not ordinary active-vs-shadow selection; it
  is identifying contexts where no replacement should happen at all.

Artifacts:

```text
scripts/testing/semantic_veto_full_family_score_surface_en_es.py
docs/test_outputs/semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json
docs/test_outputs/semantic_veto_full_family_repaired_full_score_surface_en_es_latest.md
```

### Repaired-Full Band/Formula Sweep

A new family-level sweep tests formulas for ranking the source-target families
most likely to need LLM-generated semantic evidence:

```text
script: scripts/testing/semantic_veto_repaired_full_band_formula_sweep_en_es.py
test: core/tests/dev/test_semantic_veto_repaired_full_band_formula_sweep_en_es.py
json: docs/test_outputs/semantic_veto_repaired_full_band_formula_sweep_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_repaired_full_band_formula_sweep_en_es_latest.md
```

The formula inputs are programmatic family-level signals:

```text
source_zipf_risk
target_zipf_risk
polysemy_risk
pos_shape_risk
shadow_coverage_risk
```

The sweep deliberately excludes gold labels, predicted decisions, error type,
and manual case type from formula features. Gold and prediction labels are used
only to evaluate whether a formula successfully ranks families with observed
failure concentration.

Current sweep shape:

```text
families: 49
scorer-family observations: 98
fixed formulas: 10
linear weight-sweep formulas: 3124
internal split: stable family hash, 70 discovery observations / 28 locked-proxy observations
```

Current finding:

```text
Sentence-transformer best discovery formula:
  formula: sweep_linear_0040
  weights: 75% POS-shape risk, 25% polysemy risk
  discovery Spearman: 0.1558
  internal locked-proxy Spearman: -0.6103
  top-k lift: 0.7656

TF-IDF best formula:
  formula: source_zipf_only
  discovery Spearman: 0.1915
  internal locked-proxy Spearman: -0.1225
  top-k lift: 0.9630
```

Interpretation:

- This is not a ranking win yet.
- The current coarse family signals do not reliably identify the highest
  observed-failure families on the internal locked proxy.
- This result is still useful because it blocks premature LLM budget allocation
  from a weak heuristic.

### Immediate Consequence

The next LLM generation pilot should not blindly use the current band/formula
winner as the top-N allocator.

Instead, the next research slice should either:

1. add stronger pre-outcome features that are available for the full inventory,
   especially exact source frequency/rank, translation fan-out, source evidence
   coverage, target evidence coverage, and phrase/no-winner risk proxies; or
2. run a deliberately falsifiable pilot with top-ranked, middle-ranked, and
   low-ranked controls, then judge whether LLM evidence helps enough even when
   the ranker is weak.

The current evidence says the heuristic problem is harder than simple Zipf or
polysemy banding. It does not say the veto project is blocked; it says the top-N
data-spend allocator needs better features or an explicit control-bearing pilot.

## 2026-05-08: SRS Case-Mix Prior Reweighting

The repaired-full evaluation suite has a deliberately balanced case mix. That
is useful for conditional testing, but it is not the real SRS/browser exposure
distribution. To estimate product-facing band success, we need:

```text
P(case_type | source_band, real SRS/browser exposure)
```

The first programmatic prior report estimates those proportions from static SRS
source-target metadata:

```text
script: scripts/testing/semantic_veto_srs_case_mix_prior_en_es.py
test: core/tests/dev/test_semantic_veto_srs_case_mix_prior_en_es.py
json: docs/test_outputs/semantic_veto_srs_case_mix_prior_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_srs_case_mix_prior_en_es_latest.md
```

Inputs:

```text
full SRS source-target pairs: 570
unique source triggers: 536
WordNet-profile known source-target pairs: 540
conditional veto performance: approved repaired-full score surface
```

The report uses only programmatic features:

```text
source_zipf_band_en
target_zipf_band_es
source_zipf_frequency_en
target_zipf_frequency_es
source_translation_fanout
wordnet_sense_count
wordnet_pos_count
source_form_risk
```

It does not claim true case labels. It estimates priors, then computes:

```text
band_success =
  p_active * positive_allow_rate
+ p_shadow * shadow_abstain_rate
+ p_no_winner * phrase_no_winner_abstain_rate
```

Base prior by source band:

```text
very common:
  SRS pair share: 19.1%
  active prior: 65.1%
  shadow prior: 19.6%
  no-winner prior: 15.3%

common:
  SRS pair share: 41.2%
  active prior: 72.1%
  shadow prior: 16.1%
  no-winner prior: 11.8%

mid:
  SRS pair share: 26.7%
  active prior: 79.4%
  shadow prior: 11.7%
  no-winner prior: 8.8%

rare:
  SRS pair share: 9.1%
  active prior: 82.8%
  shadow prior: 10.3%
  no-winner prior: 6.9%
```

Estimated sentence-transformer SRS-weighted success under the base prior:

```text
very common: 77.3%
common: 85.2%
mid: 83.8%
rare: 75.8%
overall: 82.3%
```

No-winner sensitivity for sentence-transformer:

```text
low no-winner prior: 85.7% overall
base no-winner prior: 82.3% overall
high no-winner prior: 77.1% overall
```

Interpretation:

- This makes the sentence-transformer lane look more product-plausible than the
  balanced repaired-full aggregate, because real SRS exposure is unlikely to be
  25% no-winner in every band.
- The estimate is still not promotion evidence, because no-winner proportion is
  inferred from static features rather than observed browser/corpus contexts.
- The biggest remaining unknown is the true no-winner rate for high-frequency
  SRS source triggers.

Next required improvement:

```text
Sample real or corpus-like SRS-trigger contexts by source band, weak-label them
as active/shadow/no-winner, review a calibration slice, and replace this static
prior with observed case-type proportions.
```

## 2026-05-08: Translation-Ambiguity Heuristic Bakeoff

The first stronger-heuristic lane tests the hypothesis that frequency bands are
not the right primary difficulty signal. It compares inventory-available
pre-outcome signals against observed repaired-full veto failures:

```text
script: scripts/testing/semantic_veto_translation_ambiguity_heuristic_en_es.py
test: core/tests/dev/test_semantic_veto_translation_ambiguity_heuristic_en_es.py
json: docs/test_outputs/semantic_veto_translation_ambiguity_heuristic_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_translation_ambiguity_heuristic_en_es_latest.md
```

Inputs:

```text
approved repaired-full families: 49
scorer-family observations: 98
inventory source profiles: 536
fixed formulas: 15
sweep formulas: 16,383
internal split: 70 discovery-proxy observations, 28 locked-proxy observations
```

Tested feature families:

```text
source_exposure_risk
translation_fanout_risk
translation_entropy_risk
target_diversity_risk
wordnet_sense_risk
wordnet_pos_risk
evidence_overlap_risk
evidence_gap_risk
shadow_competition_risk
source_surface_risk
```

Current result:

```text
best stable formula: evidence_gap_only
best stable scorer: tfidf_cosine
discovery Spearman: 0.5934
locked-proxy Spearman: 0.8084
top-k lift: 1.1840
strong allocator found: false
```

The important negative result is that translation fanout, translation entropy,
WordNet sense count, and WordNet POS count did not immediately produce a stable
sentence-transformer allocator on this 49-family denominator. That does not
prove those signals are useless. It means the current inventory representation
is too weak to treat them as the top-N LLM budget formula.

The useful positive result is that evidence coverage/gap is now a real
diagnostic signal for the TF-IDF lane, and a weaker stable signal for
sentence-transformer. This is plausible: TF-IDF especially fails when active
evidence is short, lexically sparse, or does not overlap useful context tokens.
That signal is closer to "what data needs better evidence" than raw frequency
or raw polysemy.

Interpretation:

- Do not drop frequency entirely. Move it to the exposure/value side of the
  formula rather than treating it as direct difficulty.
- Do not use raw polysemy alone as the next allocator; current evidence remains
  weak or negative.
- Prioritize evidence-gap and separability features, but require a
  control-bearing LLM or context pilot before using them as a budget allocator.
- Keep top-ranked, middle-ranked, and low-ranked controls in the next pilot so
  the heuristic can be falsified.

## 2026-05-08: Evidence-Gap Control Pilot Plan

The next no-spend step freezes a control-bearing pilot manifest from the
evidence-gap heuristic. This is not generation and not runtime promotion. It is
the experimental design needed before we can claim that the heuristic predicts
which words benefit from better evidence.

```text
script: scripts/testing/semantic_veto_evidence_gap_control_pilot_plan_en_es.py
test: core/tests/dev/test_semantic_veto_evidence_gap_control_pilot_plan_en_es.py
manifest: docs/test_inputs/semantic_veto_evidence_gap_control_pilot_plan_en_es.json
json: docs/test_outputs/semantic_veto_evidence_gap_control_pilot_plan_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_evidence_gap_control_pilot_plan_en_es_latest.md
```

Selection rule:

```text
selection scorer: tfidf_cosine
selection formula: evidence_gap_only
selection uses observed outcomes: false
```

The manifest selects three equal arms from the 49 approved repaired-full
families:

```text
high_need: 8 highest predicted evidence-gap families
middle_control: 8 families closest to median predicted need
low_control: 8 lowest predicted evidence-gap families
```

Each selected family gets the same three planned slots:

```text
active_evidence_expansion
shadow_or_competitor_evidence_probe
no_winner_context_probe
```

Latest pilot shape:

```text
selected families: 24
planned generation slots: 72

high_need mean predicted need: 0.8359
middle_control mean predicted need: 0.7266
low_control mean predicted need: 0.5371

high_need historical TF-IDF failure: 62.5%
middle_control historical TF-IDF failure: 61.3%
low_control historical TF-IDF failure: 37.5%

high_need historical sentence-transformer failure: 33.3%
middle_control historical sentence-transformer failure: 38.8%
low_control historical sentence-transformer failure: 22.5%
```

Interpretation:

- This is a fairer next step than selecting only the top-ranked words.
- The high and middle arms are historically similar, so the future pilot must
  measure improvement after new evidence, not merely pre-existing failure rate.
- A useful heuristic claim requires high-need families to improve more than
  middle and low controls under the same generation and scoring contract.
- If all arms improve similarly, evidence generation may still be useful, but
  evidence-gap ranking is not proven as a top-N budget allocator.

## 2026-05-08: Evidence-Gap Generation Request Packet

The pilot plan now has a no-spend request packet. It renders one request per
planned slot, not one request per final row, so the fair 24-family x 3-slot
control design stays visible.

```text
script: scripts/testing/semantic_veto_evidence_gap_generation_requests_en_es.py
test: core/tests/dev/test_semantic_veto_evidence_gap_generation_requests_en_es.py
json: docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.md
```

Request packet shape:

```text
families: 24
requests: 72
expected generated items: 120
expected output-token budget: 16,800

high_need: 24 requests, 40 expected items
middle_control: 24 requests, 40 expected items
low_control: 24 requests, 40 expected items

active_evidence_expansion: 24 requests, 48 expected items
shadow_or_competitor_evidence_probe: 24 requests, 48 expected items
no_winner_context_probe: 24 requests, 24 expected items
```

Guardrails:

```text
no LLM call is made
runtime policy change: none
request ids are unique
slot ids are unique
slot counts are equal per arm
selection uses observed outcomes: false
```

This packet is ready for human review before any spend. The next work after
review is admission, not scoring: generated outputs must be checked against
request_id, family_id, slot_id, slot_type, source phrase presence, Spanish
target absence, duplicate rows, and label leakage before they are allowed into
any downstream rescoring artifact.

## 2026-05-08: Evidence-Gap Generated-Response Admission Gate

The pilot now has the pre-scoring admission gate that generated responses must
pass after the LLM batch is run. This still makes no LLM call and changes no
runtime policy. Its purpose is to prevent malformed, leaky, or misaligned
generated outputs from becoming either evaluation rows or candidate evidence.

```text
script: scripts/testing/semantic_veto_evidence_gap_generation_admission_en_es.py
test: core/tests/dev/test_semantic_veto_evidence_gap_generation_admission_en_es.py
json: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_en_es_latest.md
```

Current pre-generation status:

```text
status: ok
decision: ready_for_generated_response_admission
expected requests: 72
expected generated items: 120
admitted items: 0
rejected items: 0
```

Admission checks:

```text
request_id must exist in the frozen request packet
family_id, slot_id, slot_type, source_phrase, and target_lemma must align
items must be present and non-empty
each generated sentence must contain a runtime-like standalone source phrase
Spanish active, slot, proposed competitor, and known shadow target lemmas are blocked
label leakage is rejected
duplicate generated sentences are rejected
shadow probe responses must name or propose a competitor target lemma
shadow probe responses must include response-level competitor_sense_label and active_sense_contrast
shadow probe items must include active_mismatch_note
no-winner responses must keep target_lemma blank
no-winner items must include no_winner_context_class and runtime_trigger_note
no-winner context classes must visibly match a non-translation context such as UI label or search query
overproduced items beyond requested_items are rejected
```

The harness supports selected request subsets for smoke batches through
`selected_request_ids`, but full pilot comparison still requires complete
coverage across the 72 frozen requests. Its current output is a readiness
artifact, not evidence that generated rows are good. The next real decision
comes only after generated response objects are admitted and then rescored under
the unchanged high/middle/low control design.

## 2026-05-08: Evidence-Gap Generation Runner And No-Spend Smoke

The evidence-gap packet now has a sibling generation runner rather than reusing
the older LLM pilot row runner. The older runner expects one final benchmark row
per request. This pilot expects one slot response with one or more generated
items, so using the older row-shaped runner would blur the contract.

```text
script: scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py
test: core/tests/dev/test_semantic_veto_evidence_gap_generation_run_en_es.py
smoke json: docs/test_outputs/semantic_veto_evidence_gap_generation_run_smoke_replay_en_es_latest.json
smoke markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_run_smoke_replay_en_es_latest.md
smoke generated responses: docs/test_outputs/semantic_veto_evidence_gap_generated_responses_smoke_replay_en_es_latest.json
smoke admission: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_smoke_replay_en_es_latest.md
```

The runner supports:

```text
replay mode for no-spend rehearsals
live mode only with explicit run id, request count, and cost ceilings
append-only live journals for safe resume
selected request ids or max request count for smoke batches
raw response bundles
generated response payloads
immediate admission preview against the frozen request packet
```

No-spend smoke result:

```text
prompt id: semantic_veto_evidence_gap_generation_v4
selected requests: 3
accepted responses: 3
accepted generated items: 5
admission status: ok
admitted items: 5
rejected items: 0
coverage shortfall: 0
possible active-role pollution: 0
```

This smoke used replay fixtures, not an API call. It verifies the mechanics:
request selection, JSON parsing, generated-response payload writing, admission
preview, and selected-subset coverage all line up. It does not prove LLM output
quality. The next spend-bearing step should be a tiny live batch with the same
three-slot shape, then admission review, then only a full 72-request batch if
the live smoke produces usable response objects.

## 2026-05-08: Evidence-Gap Tiny Live Smoke

The live smoke uses the same three selected requests from the first family in
the frozen packet. It ran through the local project virtualenv because the
system Python environment lacked the `openai` package.

```text
command shape: scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py --execute-live --max-requests 3 --require-selected-request-count 3
latest run id: semantic-veto-evidence-gap-live-smoke-20260508-005
prompt id: semantic_veto_evidence_gap_generation_v4
generation json: docs/test_outputs/semantic_veto_evidence_gap_generation_run_live_smoke_en_es_latest.json
generation markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_run_live_smoke_en_es_latest.md
generated responses: docs/test_outputs/semantic_veto_evidence_gap_generated_responses_live_smoke_en_es_latest.json
admission markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_live_smoke_en_es_latest.md
contribution markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_contribution_live_smoke_en_es_latest.md
```

Live smoke result:

```text
selected requests: 3
accepted responses: 3
accepted generated items: 5
input tokens: 1721
output tokens: 697
admission status: ok
admitted items: 5
rejected items: 0
coverage shortfall: 0
contribution review-required items: 3
possible active-role pollution: 0
metadata active overlap: 2
```

Important interpretation:

- The current live generation runner accepted all three response objects under
  the repaired v4 prompt.
- The admission gate admitted exactly the expected five items: two active, two
  shadow/competitor, and one no-winner. It rejected no items and recorded no
  coverage shortfall.
- The no-winner lane no longer relies on underscore filenames or ordinary active
  sentences. The admitted no-winner item is a `search_query` context with a
  standalone source token.
- The contribution diagnostic now separates sentence-only active-role pollution
  from metadata overlap. Sentence-level pollution is `0`; shadow notes still
  show metadata overlap because explanatory notes contain contrast language, so
  those notes must be reviewed before promotion.
- This repairs the generation/admission mechanics enough to move to the next
  research step, but it is not source promotion. Non-active generated items still
  require semantic role review and downstream score-contribution measurement.

Prompt corrections from the smoke loop:

```text
v2: require honest no-competitor marker instead of forcing fake shadow coverage
v3: require no_winner_context_class, runtime_trigger_note, and exact item counts
v4: include an explicit top-level JSON skeleton so source_phrase is not omitted
shadow/competitor prompt explicitly permits:
unable_to_find_distinct_competitor: true
items: []
no_distinct_competitor_reason: ...
```

This is intentional. Forcing the model to invent a competitor can manufacture
bad shadow evidence. An honest no-competitor marker is more useful than fake
coverage.

## 2026-05-09: Evidence-Gap Balanced Live Smoke

The next live step expanded the tiny smoke into a balanced 9-request subset:
one high-need family, one middle-control family, one low-control family, and
the same three slot types for each family. This still does not run the full
72-request pilot. It is a bounded check that the generation/admission contract
survives more than one arm before any larger spend.

```text
run id: semantic-veto-evidence-gap-balanced-smoke-20260509-001
prompt id: semantic_veto_evidence_gap_generation_v4
families: entirely -> enteramente, brother -> hermano, smile -> sonreir
selected requests: 9
generation json: docs/test_outputs/semantic_veto_evidence_gap_generation_run_balanced_smoke_en_es_latest.json
generation markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_run_balanced_smoke_en_es_latest.md
generated responses: docs/test_outputs/semantic_veto_evidence_gap_generated_responses_balanced_smoke_en_es_latest.json
admission markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_balanced_smoke_en_es_latest.md
contribution markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_contribution_balanced_smoke_en_es_latest.md
```

Balanced smoke result:

```text
accepted responses: 9
accepted generated items: 13
input tokens: 5436
output tokens: 1960
admission status: ok
admitted items: 13
rejected items: 0
coverage shortfall: 0
coverage waived items: 2
semantic review required items: 7
possible active-role pollution: 2
metadata active overlap: 2
```

The two waived items are intentional, not missing coverage. The high-need
`entirely -> enteramente` shadow request returned an honest
`unable_to_find_distinct_competitor` marker because the model did not find a
clearly distinct English sense that would compete with the active translation.
The admission gate now counts that as waived shadow coverage instead of a
shortfall. This preserves the anti-fabrication rule: a truthful no-competitor
answer is better than invented shadow evidence.

Important interpretation:

- The balanced smoke proves the live runner, response journal, structural
  admission, honest no-competitor waiver, and contribution diagnostics work
  across all three control arms.
- Active evidence generation is structurally clean in this smoke: 6 active
  evidence items were admitted with no active-role pollution.
- Shadow and no-winner slots still need semantic review before promotion: 7
  non-active items were review-required, with 2 possible active-role pollution
  flags and 2 metadata active-overlap flags.
- This is enough to run offline score-contribution measurement, but not enough
  to launch the full 72-request pilot blindly. The next question is how
  generated evidence should be applied, not whether the generator can emit JSON.

## 2026-05-09: Evidence-Gap Score-Contribution Probe

The score-contribution probe measures whether admitted generated items actually
move frozen manual sentence-veto decisions. It does not tune thresholds, change
runtime policy, or promote generated source evidence. It builds selected base
and augmented datasets from the approved repaired-full manual packet, then
compares several application modes under the same TF-IDF sentence-veto scorer.

```text
script: scripts/testing/semantic_veto_evidence_gap_generation_score_contribution_en_es.py
test: core/tests/dev/test_semantic_veto_evidence_gap_generation_score_contribution_en_es.py
json: docs/test_outputs/semantic_veto_evidence_gap_generation_score_contribution_balanced_smoke_en_es_latest.json
markdown: docs/test_outputs/semantic_veto_evidence_gap_generation_score_contribution_balanced_smoke_en_es_latest.md
base dataset: docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json
admission input: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_balanced_smoke_en_es_latest.json
```

Application modes:

```text
base
generated_active_only
generated_shadow_existing_only
generated_shadow_synthetic_only
generated_existing_shadows
generated_synthetic_shadows
```

Balanced smoke score-contribution result:

```text
selected families: 3
selected frozen manual cases: 11

base:
  decision accuracy: 0.4545
  replace recall: 0.0000
  harmful replaces: 0
  false abstains: 6
  winner accuracy: 0.7500

generated_active_only:
  decision accuracy: 0.6364
  replace recall: 0.6667
  harmful replaces: 2
  false abstains: 2
  winner accuracy: 0.7500

generated_existing_shadows:
  decision accuracy: 0.6364
  replace recall: 0.6667
  harmful replaces: 2
  false abstains: 2
  winner accuracy: 0.7500

generated_synthetic_shadows:
  decision accuracy: 0.7273
  replace recall: 0.8333
  harmful replaces: 2
  false abstains: 1
  winner accuracy: 0.6250
```

The main result is real but mixed. Generated active evidence is strong enough to
rescue false abstains: it reduces false abstains from 6 to 2 in the active-only
mode. It is also blunt enough to create harmful replacements: the same mode
introduces 2 harmful replaces, both around `smile`, where generated active
evidence makes a noun/shadow case and a no-winner project-code case look too
active.

Shadow-only application did not improve decision accuracy in this probe. It
reduced winner attribution quality, especially when synthetic shadows were used.
The generated synthetic-shadow mode had the highest decision accuracy, but it
also retained the 2 harmful replaces and lowered winner accuracy, so it is not a
promotable policy by itself.

Policy-sweep update:

The same harness now runs a no-spend policy sweep over the fixed balanced-smoke
generated evidence. This changes only the scorer policy used for measurement,
not the generated data:

```text
policy sweep rows: 240
min_active_score: 0.05, 0.075, 0.1, 0.125
min_margin: 0.0, 0.02, 0.05
phrase_control_mode: off, noun_family_frame_guard
active_rescue_mode: off, sense_label_near_tie_active_rescue
application modes: five generated-evidence modes
```

Best rows by harmful-replace budget:

```text
budget 0 harmful replaces:
  mode: generated_shadow_existing_only
  decision accuracy: 0.4545
  replace recall: 0.0000
  false abstains: 6

budget 1 harmful replace:
  mode: generated_active_only
  min_active_score: 0.05
  min_margin: 0.05
  phrase_control_mode: off
  active_rescue_mode: off
  decision accuracy: 0.7273
  replace recall: 0.6667
  false abstains: 2
  harmful replaces: 1

budget 2 harmful replaces:
  mode: generated_synthetic_shadows
  min_active_score: 0.05
  min_margin: 0.00
  phrase_control_mode: off
  active_rescue_mode: off
  decision accuracy: 0.7273
  replace recall: 0.8333
  false abstains: 1
  harmful replaces: 2
```

Interpretation:

- Do not run the full 72-request generation batch under naive evidence append.
- Keep the balanced smoke outputs as the current control for evidence
  application research.
- The first application-policy bakeoff is now in place. It shows that simple
  threshold/margin changes can reduce but not eliminate the harmful-replace
  regression from generated active evidence on this tiny slice.
- The zero-harmful budget still collapses back to no useful generated-active
  lift, so the next no-spend research should inspect the remaining harmful
  replace and test source/application representations that separate active verb
  evidence from noun/shadow and no-winner contexts.
- Treat harmful-replace behavior as the gating metric for this lane. Generated
  evidence is useful only if it raises positive allows without making obvious
  no-winner or wrong-sense contexts look active.

## 2026-05-09: PoC Exit Decision

The active product goal is now a proof-of-concept semantic assist, not a
near-perfect veto algorithm. This changes how to interpret the latest results.
Some harmful replacements are acceptable if the feature gives low-to-moderate
visible benefit and avoids a meaningful share of clearly wrong replacements.

Current expected value:

```text
feature role: soft semantic quality filter
expected benefit: low-to-moderate product lift
expected failure mode: some wrong-sense or no-winner replacements still pass
runtime promise: better than lexical-only for enriched/high-risk families, not
  semantic correctness across en-es
```

Operationally, this means:

- Do not keep optimizing this lane toward zero harmful replacements unless a
  later product decision raises the bar again.
- Preserve the harnesses and reports as reusable research infrastructure.
- Treat `generated_active_only` with a modest positive margin as the current
  practical direction if a PoC policy is promoted later.
- Keep generated shadow and synthetic-shadow evidence diagnostic until reviewed.
- Do not run the full 72-request batch unless the next workstream specifically
  needs a larger PoC evidence sample.

Recommended handoff state:

```text
semantic veto status: PoC-ready research lane, not production-promoted
default runtime policy change: none
next semantic-veto action: pause unless packaging a PoC or generating a bounded
  enrichment batch for a specific product demo
best next project action: checkpoint/commit, then move attention back to the
  broader SRS/admission/product workflow
```

## 2026-05-09: Active-Only PoC Follow-Through Batch

The follow-through batch freezes the smallest meaningful generation set that can
support the soft-assist PoC: active evidence only, all 24 families from the
existing high/middle/low evidence-gap pilot, two active examples per family.
This deliberately does not generate shadow or no-winner rows.

```text
freeze script: scripts/testing/semantic_veto_evidence_gap_active_only_poc_requests_en_es.py
frozen request packet: docs/test_inputs/semantic_veto_evidence_gap_active_only_poc_requests_en_es.json
freeze report: docs/test_outputs/semantic_veto_evidence_gap_active_only_poc_requests_en_es_latest.md
prompt id: semantic_veto_evidence_gap_generation_v5
requests: 24
families: 24
arms: 8 high_need, 8 middle_control, 8 low_control
expected active examples: 48
runtime policy change: none
```

Live generation:

```text
run id: semantic-veto-evidence-gap-active-only-poc-20260509-001
run report: docs/test_outputs/semantic_veto_evidence_gap_generation_run_active_only_poc_en_es_latest.md
generated responses: docs/test_outputs/semantic_veto_evidence_gap_generated_responses_active_only_poc_en_es_latest.json
selected requests: 24
accepted responses: 24
accepted generated items: 48
input tokens: 11421
output tokens: 4177
api errors: 0
invalid outputs: 0
```

Admission and contribution:

```text
admission report: docs/test_outputs/semantic_veto_evidence_gap_generation_admission_active_only_poc_en_es_latest.md
contribution report: docs/test_outputs/semantic_veto_evidence_gap_generation_contribution_active_only_poc_en_es_latest.md
admitted items: 48
rejected items: 0
coverage shortfall: 0
coverage waived items: 0
semantic review required: 0
possible active-role pollution: 0
candidate active evidence for rescoring: 48
```

Score-contribution result:

```text
score report: docs/test_outputs/semantic_veto_evidence_gap_generation_score_contribution_active_only_poc_en_es_latest.md
selected families: 24
frozen manual cases: 91

base:
  decision accuracy: 0.5055
  replace recall: 0.0833
  harmful replaces: 1
  false abstains: 44
  winner accuracy: 0.7015

generated_active_only:
  decision accuracy: 0.7363
  replace recall: 0.5208
  harmful replaces: 1
  false abstains: 23
  winner accuracy: 0.8060

delta:
  decision accuracy: +0.2308
  replace recall: +0.4375
  harmful replaces: +0
  false abstains: -21
  winner accuracy: +0.1045
```

Policy-sweep reading:

```text
policy sweep rows: 240
best 0-harmful budget: no useful active-evidence lift; 44 false abstains remain
best 1-harmful budget: generated_active_only, min_active_score 0.05,
  min_margin 0.0, phrase guard off, active rescue off
```

The remaining harmful replacement is:

```text
family: smile -> sonreir
case: Her smile returned after the good news.
gold: abstain
candidate: replace
```

Interpretation:

- The active-only PoC follow-through succeeded under the relaxed product goal.
- It produced a real soft-assist shape: many fewer false abstains, much higher
  replace recall, no net increase in harmful replacement count versus the base
  selected-family scorer.
- The result does not prove general en-es quality and does not promote runtime
  policy by itself.
- This is the stop point for the current veto research loop. The next veto work,
  if any, should be packaging a bounded PoC configuration, not continuing the
  same research cycle.
