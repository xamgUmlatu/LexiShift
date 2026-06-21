# SRS Learner-Difficulty Model Shape Tenets

Status: design note; conceptual reference before the next modeling pass

Purpose: capture the current field-knowledge view of how en-ja learner
difficulty should be modeled now that the signal palette separates raw source
facts, flags, scores, knownness, and gated risks.

## Target Quantity

The target is not pure intrinsic word difficulty. The target is presentation
priority:

```text
presentation_level(word) in [0, 1]
```

Interpretation:

- `0.00`: first-lesson Japanese.
- `0.40-ish`: broad pedagogical/core learner vocabulary.
- `0.70-ish`: advanced but still useful/general vocabulary.
- `1.00`: obscure, recondite, unused, or effectively non-general vocabulary.

This matters because useful learner words can be early even when they have some
orthographic or lexical burden. Words like `難しい`, `働く`, `政治`, and `技術`
should not be pushed late merely because they contain kanji, have length, or
look structurally harder than first-week vocabulary.

## Signal Families

The cleaned palette is best understood as a set of source families with
different modeling roles:

```text
P = pedagogical anchors
    JLPT vocabulary, lesson vocabulary, beginner-core signals

F = exposure/commonness
    BCCWJ, TUBELEX, JMDict priority/commonness

O = orthographic/readability burden
    kanji grade, old JLPT kanji, stroke count, KanjiVG, nonstandard readings

L = lexical/dictionary complexity
    JMDict ambiguity, forms, senses, restrictions, readings

R = routing/admission/topic facts
    proper-name overlap, acronym, field, dialect, abbreviation, register

K = knownness/coverage
    source_known, source_coverage_count, source-specific coverage flags
```

The most important cleanup principle is that raw facts are not automatic
penalties. A source fact such as `jmdict_dialect_flag`,
`jmdict_abbreviation_flag`, `jmnedict_*_overlap`, or `wtype_proper_flag` can be
true for an item that still belongs early or mid ladder. These facts should only
create late-placement pressure through gates that account for ordinary
vocabulary protection, rarity, candidate state, topic-only status, or weak
general-vocabulary evidence.

## Core Tenets

1. The target is presentation priority, not pure difficulty.

   A single scalar remains useful for the app, but it should mean "when should
   this be shown to the learner?" rather than "how intrinsically difficult is
   the word?"

2. The early ladder is curriculum plus usefulness.

   In the beginner-to-intermediate range, pedagogical anchors and usefulness
   should dominate: JLPT vocabulary, lesson vocabulary, JMDict
   priority/commonness, BCCWJ/TUBELEX exposure, and beginner-core evidence.
   Orthographic burden may adjust nearby order, but it should not override
   strong evidence that the word is useful and expected early.

3. After learner sources thin out, native exposure becomes the main spine.

   Once a learner is around N1-and-beyond, the L2/L1 distinction should become
   much weaker. For a very advanced learner, presentation priority should look
   increasingly like educated native exposure, knownness, and usefulness rather
   than a separate artificial L2 curriculum.

4. Kanji, script, and reading complexity are mostly conditional.

   Kanji grade, stroke count, KanjiVG visual complexity, nonstandard readings,
   nanori counts, rare-wago signals, and written-form burden are valuable, but
   mostly as tie-breakers or tail shapers. They should matter most when
   exposure and pedagogical evidence are weak, missing, or otherwise comparable.

5. Raw routing flags are not penalties.

   Proper-name overlap, field/register/dialect flags, abbreviation flags, and
   source/form flags are facts. They are not direct difficulty. They become
   suppression or late-placement evidence only when gated by weak ordinary-vocab
   evidence, rarity, deprioritized candidate state, acronym/topic-only policy,
   or similar conditions.

6. Missingness is not zero evidence.

   Knownness signals are needed because "source absent" is different from
   "source says no." Unknown JLPT or lesson status should not mean "confirmed
   non-pedagogical"; it should mean that the pedagogical source cannot arbitrate
   that item.

## Candidate Model Shapes

### Shape 1: Flat Weighted Sum

```text
y = clamp(
  wP * P
+ wF * F
+ wO * O
+ wL * L
+ wR * R
+ b
)
```

This is the simplest sweep shape and resembles much of the older model-search
workstream.

Usefulness:

- Good baseline.
- Easy to sweep and debug.
- Can find broad scalar tradeoffs.

Limitations:

- Philosophically weak for this problem.
- Assumes the same signal has the same meaning everywhere.
- Lets raw flags or orthographic burden act too globally unless carefully
  bounded.

The tenets imply that a flat weighted sum should not be the final model shape
unless holdout and qualitative samples show surprisingly strong behavior.

### Shape 2: Bounded Correction Model

```text
base = exposure_or_pedagogical_spine(P, F)

correction = bounded(
  + orthographic_tail_adjustment(O)
  + lexical_complexity_adjustment(L)
  + gated_routing_adjustment(R)
)

y = clamp(base + correction)
```

This shape makes pedagogical/exposure evidence the spine and treats burden or
routing evidence as local adjustment.

Usefulness:

- Prevents kanji burden from throwing useful common words too late.
- Keeps raw facts from dominating the level.
- Easier to reason about than a fully flexible model.

Open design choices:

- How wide should the correction bound be?
- Should positive and negative corrections have different bounds?
- Should bounds vary by phase of the ladder?

### Shape 3: Phase-Gated Model

```text
early_weight  = g_early(P, F, K)
native_weight = g_native(P, F, K)
tail_weight   = g_tail(P, F, K)

y =
  early_weight  * y_early(P, F)
+ native_weight * y_native(F, P)
+ tail_weight   * y_tail(F, O, L, R)
```

Conceptual policy:

```text
if pedagogical evidence is strong:
    trust pedagogical/usefulness ordering
elif native exposure evidence is strong:
    trust native frequency/commonness
else:
    use tail burden, dictionary complexity, source gaps, and entity routing
```

Usefulness:

- Closely matches the tenets.
- Allows the same signal to have different power by ladder region.
- Lets kanji/reading burden be weak early and stronger in the tail.

Risks:

- Boundary errors can be expensive.
- More degrees of freedom can overfit calibration.
- Needs clear holdout validation and qualitative band samples.

### Shape 4: Source Arbitration Model

Instead of immediately combining components, build expert estimates:

```text
y_pedagogical = fP(P)
y_native      = fF(F)
y_burden      = fO(O, L)
y_admission   = fR(R, K)

confidence_pedagogical = cP(K, P)
confidence_native      = cF(K, F)
confidence_burden      = cO(K, O, L)

y = weighted_median_or_mean(
  y_pedagogical,
  y_native,
  y_burden,
  y_admission,
  weights = confidences
)
```

Usefulness:

- Makes knownness first-class.
- Handles disagreement between sources more explicitly.
- Avoids treating missing evidence as negative evidence.

Example:

- If JLPT/lesson evidence exists, the pedagogical expert gets high confidence.
- If those sources are absent but BCCWJ/TUBELEX/JMDict priority are strong, the
  native-exposure expert gets high confidence.
- If exposure is weak and orthographic/lexical burden is high, the burden expert
  can influence the upper tail.

Risk:

- Requires careful confidence functions.
- If confidence is wrong, the right expert may be ignored.

### Shape 5: Lexicographic / Priority-Bucket Model

Two-stage structure:

```text
1. Assign a coarse lane:
   beginner_core / learner_ladder / native_general / advanced_tail / non_ladder

2. Rank within the lane using a lane-specific formula.
```

Possible lanes:

- `beginner_core`: lesson/JLPT/commonness dominate.
- `learner_ladder`: JLPT, frequency, and usefulness dominate.
- `native_general`: BCCWJ/TUBELEX/JMDict priority dominate.
- `advanced_tail`: rarity, kanji/reading burden, and lexical complexity dominate.
- `non_ladder/topic`: gated entity, acronym, register, or topic policy dominates.

Usefulness:

- Very interpretable.
- Avoids pretending one formula works everywhere.
- Good for qualitative inspection.

Risk:

- Wrong lane assignment can be worse than a smoother model.
- Lane boundaries may be brittle.

### Shape 6: Monotonic GAM / Smooth Nonlinear Model

General form:

```text
y =
  fP(P)
+ fF(F)
+ fO(O)
+ fL(L)
+ fPF(P, F)
+ fFO(F, O)
+ fFR(F, R)
```

With monotonic or bounded functions.

Example interaction:

```text
orthographic_effect = O * ramp(F, lower=0.65, upper=0.95)
```

Usefulness:

- Can discover nonlinear curves without fully hardcoding phases.
- Allows field knowledge through monotonicity, bounds, and selected
  interactions.
- Good compromise between manual design and brute-force search.

Risk:

- Less interpretable than explicit phases.
- Can still overfit if interaction families are too broad.

### Shape 7: Pairwise Ranking Model

Optimize ordering directly:

```text
word_a should appear before word_b
score(word_a) < score(word_b)
```

Usefulness:

- Matches the app's practical need: ordering.
- Good validation objective for whether the model preserves human ordering.

Limitation:

- Pure ranking does not tell us calibrated proficiency bands.
- It can say `A < B < C` without telling us whether `B` is around `0.35` or
  `0.70`.

Recommended role:

- Use pairwise ranking as an evaluation objective and perhaps as a secondary
  training pressure, not as the only final output.

## Preferred Direction

The most promising family is a conditional source-arbitration / bounded
adjustment model:

```text
base = source_arbitrated_spine(P, F, K)

tail_gate = ramp(base or F, threshold_region)
burden_adjustment = bounded(tail_gate * f(O, L))

entity_gate = weak_ordinary_vocab_evidence(K, P, F) * raw_entity_overlap(R)
topic_gate  = field_register_acronym_evidence(R) gated by rarity/use_case

y = clamp(base + burden_adjustment + entity_adjustment + topic_adjustment)
```

In words:

1. Build the main ladder from pedagogical and exposure evidence.
2. Use knownness to decide which source should be trusted.
3. Apply kanji, reading, and dictionary complexity mostly as conditional tail
   pressure.
4. Apply entity, register, acronym, and topic pressure only through gates.
5. Keep adjustments bounded so one raw fact cannot dominate.

This shape is materially different from a larger flat sweep because it changes
where a signal is allowed to matter. The model is not just asking "what weight
does kanji burden get?" It is asking "under what conditions should kanji burden
matter at all?"

## Known Unknowns

Known open questions:

- Where the pedagogical-to-native transition actually happens. It may not be a
  fixed level like `0.40`; it may depend on source coverage and item type.
- How strongly JLPT should dominate frequency. Some N1 words are common, and
  some non-JLPT words are basic.
- Whether TUBELEX improves generality or mainly adds spoken/video-register bias.
- How much kanji burden should matter for words learners need early.
- Whether proper-name/entity suppression should be global or topic/user
  preference dependent.
- Whether calibration labels are internally consistent enough to distinguish
  close model shapes.
- Whether the holdout labels are large and diverse enough to detect real
  generalization.
- How missingness should interact with source confidence. Missing JLPT evidence,
  for example, may mean either "not in this source" or "not covered by this
  source's worldview."

## Unknown Unknowns

Potential hidden risks:

- Frequency sources may encode register or domain bias that is not obvious from
  aggregate rank.
- JMDict/JMnedict overlap may produce misleading cues because dictionary entries
  are broad and multi-sense.
- Difficulty may differ sharply by learner background, especially Chinese
  character knowledge, anime/media exposure, classroom path, and literacy goals.
- Recognition difficulty and production difficulty are different, but the app
  currently collapses them into one scalar.
- Some words are pedagogically late because they require grammar, topic context,
  or discourse use, not because the word itself is hard.
- Native-speaker knownness after N1 may not align cleanly with corpus frequency.
- Current labels may encode our own aesthetic judgment of Japanese vocabulary
  rather than true learner presentation value.

## Practical Implication

The next serious modeling pass should not be only a bigger flat sweep. It should
test a conditional source-arbitration / gated-adjustment family against:

- calibration labels,
- holdout labels,
- pairwise ordering,
- band samples,
- endpoint audits,
- and qualitative review of model disagreements.

The expected benefit is not merely a higher calibration score. The expected
benefit is a model whose ordering is more defensible: pedagogical evidence leads
the early ladder, native exposure leads the advanced/general ladder, orthographic
and lexical burden shape the tail, and raw entity/register flags only matter
when a gate makes them relevant.
