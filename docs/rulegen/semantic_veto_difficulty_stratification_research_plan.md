# Semantic Veto Difficulty Stratification Research Plan

Status: active research plan
Role: semantic-veto plus SRS-admission planning reference
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

Likely script:

```text
scripts/testing/semantic_veto_difficulty_stratification_en_es.py
```

Likely outputs:

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
