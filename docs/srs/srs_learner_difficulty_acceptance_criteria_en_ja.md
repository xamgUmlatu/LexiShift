# en-ja Learner Difficulty Acceptance Criteria

Status: working acceptance note for the sidecar learner-difficulty workstream

Purpose: define what "good enough to promote" means for the en-ja learner
difficulty scalar and what improvement size is realistic from the current
signals.

## Target

The scalar is a presentation-priority level:

```text
presentation_level(word) in [0, 1]
```

It is not pure rarity, pure intrinsic difficulty, pure JLPT level, or pure
kanji burden. It should answer:

```text
At approximately what learner proficiency should this item become reasonable to
show by default?
```

The app will likely expose one simple user proficiency setting, so the scalar
must remain usable as a single ordering spine even if the underlying model uses
lanes, gates, or source arbitration.

## Current Baseline

Current latest sidecar evidence:

- Calibration winner: `v1`, balanced `0.787825`, MAE `0.191308`.
- Holdout winner: `stitch`, balanced `0.889983`, MAE `0.089053`.
- Fresh stitch-validation winner: `ordinary_cap`, balanced `0.862096`, MAE
  `0.11965`.
- Cleaned JMDict-exact lane does not change the winner on calibration, holdout,
  or stitch-validation.

Interpretation:

- The current models are already close on ranking metrics.
- No current model is globally dominant across all splits.
- Source-pair cleanup is a hygiene improvement, not a scalar accuracy cure.
- The main scalar weakness is not "bad source rows"; it is the middle and
  conditional meaning of signals.

## Difficulty Bands

Use these as qualitative acceptance expectations, not hard model constants.

| Band | Expected behavior | Current risk |
| --- | --- | --- |
| `0.00-0.20` | First-lesson and early-core words. Pedagogical and frequency evidence dominate. | Mostly stable, but variant readings can still be odd. |
| `0.20-0.40` | Useful lower-intermediate words, common forms, ordinary learner ladder words. | High routing risk: many items look too easy by frequency or too hard by form. |
| `0.40-0.60` | Broad middle: ordinary but not beginner, productive forms, general kango, common domain/loanwords. | Weakest band; this is where "difficulty" and "presentation priority" diverge most. |
| `0.60-0.80` | Advanced but usable words, formal/domain terms, uncommon readings, technical or literary vocabulary. | Better than the middle, but topic/loanword/reading-specific errors remain. |
| `0.80-1.00` | Rare, obscure, recondite, native-tail, or effectively non-general vocabulary. | Relatively plausible, but distinguishing "advanced normal" from "truly obscure" remains hard. |

## Failure Centers

Current structured failures cluster around:

- Middle-band placement, especially `0.20-0.60`.
- Domain-specific or rare loanwords.
- Kango and formal written burden.
- Rare or nonstandard readings.
- Transparent rare wago and rare compounds that are easier than their frequency
  suggests.
- Source/admission rows that should be review/topic/grammar lanes rather than
  scalar normal vocabulary.

The distribution mismatch is material: calibration, holdout, and
stitch-validation contain very different shares of frequency-tail,
domain/loanword, written-burden, curriculum-core, and entity/acronym rows. This
is why broad calibration-fitted corrections can look promising and then fail
holdout or validation.

## Realistic Improvement Envelope

Without new labels or new high-quality signals, expected safe improvement is
small.

Observed evidence:

- One-group bounded corrections fit on calibration did not improve both holdout
  and stitch-validation balanced score.
- Calibration-fold stable bounded hybrids showed holdout gains around
  `+0.003` to `+0.007` for selected policies, depending on selector scope.
- Holdout-oracle narrow policies reached roughly `+0.015` on the tested
  ordering objective, but that is an oracle upper bound, not a promotable
  expectation.
- Source-pair cleaning improved reviewability but did not change the scalar
  winner.

Practical expectation:

```text
safe short-term gain:     about +0.003 to +0.010 on cross-split score
optimistic oracle signal: about +0.015 on the tested ordering objective
large gain without new data/signals: unlikely
```

So the next work should not be judged by whether it finds a dramatic score
jump. It should be judged by whether it makes a small improvement that is
stable, explainable, and qualitatively better in the known weak bands.

## Promotion Criteria

A candidate should not be promoted into runtime ordering unless it satisfies all
of the following.

1. Cross-split stability

   The candidate must not be selected only because it wins calibration. It must
   preserve or improve holdout and fresh validation behavior against the current
   anchor.

   Minimum bar:

   - no meaningful regression on holdout balanced score;
   - no meaningful regression on stitch-validation balanced score;
   - no hidden trade where MAE improves but pairwise ordering degrades enough
     to make presentation order worse.

2. Hygiene gate

   Normal-vocab scalar evaluation should be separated from source-pair,
   grammar, topic-only, name/entity, and source-fix rows.

   Minimum bar:

   - exact JMDict lemma/reading rows remain eligible for normal scalar review;
   - non-exact pairs are retained as review or special-lane rows, not silently
     treated as normal scalar evidence;
   - topic-only and grammar rows are excluded from scalar difficulty metrics.

3. Band behavior

   The candidate must improve or preserve qualitative behavior in the weak
   middle bands.

   Minimum bar:

   - no obvious degradation in `0.00-0.20`;
   - review samples for `0.20-0.60` look at least as coherent as the current
     anchor;
   - upper-tail samples still reserve `0.90-1.00` for genuinely rare or
     obscure items;
   - loanword, acronym, and domain rows do not flood ordinary middle bands
     without source-backed justification.

4. Interpretability

   A promoted model should have a defensible story:

   ```text
   pedagogical/exposure evidence builds the spine;
   source confidence chooses which evidence to trust;
   kanji/reading/dictionary burden applies conditionally;
   topic/entity/acronym facts route or adjust only through gates.
   ```

   A black-box shape can be tested as a sidecar, but it should not be promoted
   unless it can be explained in this language and passes qualitative review.

5. Review pack pass

   Before promotion, generate a compact current-model band review pack with:

   - representative samples per band;
   - largest errors by model;
   - cases where candidate and anchor strongly disagree;
   - source-lane exclusions;
   - qualitative accept/reject notes.

## Current Recommendation

Treat `ordinary_cap` as the current fresh-validation anchor, with `stitch` as
the holdout-strength comparator and `v1` as an important calibration/rowwise
fallback signal.

Do not promote a new scalar correction yet. The current best next step is a
compact qualitative band review of the current anchor versus the strongest
contenders. If that review identifies a narrow, source-computable failure group,
test only a bounded correction for that group and require it to pass both
holdout and stitch-validation.

## Decision State

Current state:

```text
source hygiene: useful and nearly promotable as a review/lane guardrail
scalar model: useful, but not yet improved enough to promote over the current anchor
expected near-term gains: small but potentially worthwhile
main acceptance blocker: weak middle-band qualitative coherence and split stability
```
