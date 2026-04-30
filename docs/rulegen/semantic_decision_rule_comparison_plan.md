# Semantic Decision Rule Comparison Plan

Status: active plan with first offline matrix implemented
Role: Testing design / decision-rule backlog
Purpose: compare the final semantic-veto YES/NO decision algorithms without confusing them with source-coverage work
Last updated: 2026-04-29
Source-of-truth: planning doc plus `scripts/testing/semantic_decision_rule_matrix_en_es.py` and generated `docs/test_outputs/semantic_decision_*_en_es_latest.*` artifacts
Related planning:
- `docs/rulegen/semantic_sentence_veto_algorithm.md`
- `docs/rulegen/semantic_source_admission_program.md`
- `docs/rulegen/semantic_en_es_expansion_opportunity_roadmap.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
Current executable manifests:
- `docs/test_inputs/semantic_decision_rule_matrix_en_es.json`
- `docs/test_inputs/semantic_decision_family_bakeoff_en_es.json`
- `docs/test_inputs/semantic_decision_suite_confirmation_en_es.json`
- `docs/test_inputs/semantic_active_score_surface_bakeoff_en_es.json`
- `docs/test_inputs/semantic_phrasing_order_surface_bakeoff_en_es.json`
- `docs/test_inputs/semantic_context_conditioned_evidence_bakeoff_en_es.json`
- `docs/test_inputs/semantic_source_scope_margin_bakeoff_en_es.json`
- `docs/test_inputs/semantic_sentence_transformer_row_level_bakeoff_en_es.json`
Current process ledger:
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- `docs/test_outputs/semantic_decision_research_lanes_latest.md`
Current system reconciliation ledger:
- `docs/rulegen/semantic_veto_reconciliation_workstream.md`
- `docs/test_inputs/semantic_veto_system_registry_en_es.json`
- `docs/test_outputs/semantic_veto_system_registry_latest.md`
Current source-row audits:
- `docs/test_outputs/semantic_source_row_alignment_audit_en_es_latest.md`
- `docs/test_outputs/semantic_source_row_alignment_audit_def_example_plus_llm_aligned_frame_gap_v2_latest.md`
Current source-portfolio admission artifacts:
- `docs/test_outputs/semantic_non_v10_source_portfolio_wave5_anypos_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest.md`
Current source-frame request plans:
- `docs/test_outputs/semantic_source_frame_gap_plan_en_es_latest.md`
- `docs/test_outputs/semantic_source_frame_gap_plan_def_example_plus_llm_aligned_v2_en_es_latest.md`
Current generation safety previews:
- `docs/test_outputs/semantic_source_frame_gap_generation_safety_latest.md`
- `docs/test_outputs/semantic_source_frame_gap_generation_safety_v2_latest.md`

## Goal

For a browser sentence containing an English trigger, decide whether the user
should see the Spanish replacement.

Example:

- browser trigger: `change`
- candidate replacement: `cambio`
- active gloss: `the process of becoming different`
- competing gloss: `to become something different`
- possible wrong source sense: money received in return, as in `change for a twenty`

The user-visible decision is binary:

- `YES`: show the replacement
- `NO`: show nothing

The internal decision can still use multiple senses, source rows, scorers,
thresholds, and phrase guards. This plan exists to test whether the current
decision algorithm is the best simple control, or whether another algorithm
should replace it.

## Terms

Use these terms consistently:

- **Context representation**: the text derived from the browser sentence.
  Example: raw sentence, masked sentence, local window, masked local window.
- **Sense representation**: the text or row set used to represent the active
  sense or a competing sense.
  Example: gloss only, WordNet definition row, Wiktionary example row, admitted
  source bundle.
- **Scoring function**: a function that assigns a number to a context and a
  sense representation.
  Example: token overlap, TF-IDF cosine, sentence-transformer cosine.
- **Aggregation rule**: the way multiple source rows become one active score or
  one competing-sense score.
  Example: max row score, mean score, top-k mean, source-weighted mean.
- **Decision rule**: the final binary classifier that outputs `YES` or `NO`.
  Example: active-minus-strongest-shadow margin.
- **Decision margin**: the numeric gap used by some decision rules.
  Example: `active_score - strongest_shadow_score`.
- **Negative control**: a deliberately weak or unsafe configuration used to make
  sure the harness can detect bad behavior.
  Example: active-only source, shuffled labels, wrong WordNet sense rows.

Avoid calling the whole algorithm a metric. In this work, `metric` should mean
an evaluation measure such as harmful replacement count, false abstain count,
replace recall, or decision accuracy.

## Current Control

The current semantic decision control can be written as:

```text
c = context(sentence, trigger)
a = representation(active_sense)
s_i = representation(competing_sense_i)

active_score = similarity(c, a)
shadow_score = max_i similarity(c, s_i)

YES if:
  active_score >= min_active_score
  and active_score - shadow_score >= min_margin
  and no phrase guard forces abstain

NO otherwise
```

The library fallback constants in `semantic_routing_runtime_scoring.py` are:

```text
min_active_score = 0.35
min_margin = 0.05
```

Named runtime policies override those constants. The current `en-es` pair
default is documented in `docs/rulegen/semantic_sentence_veto_algorithm.md` and
currently resolves to `en_es_sentence_veto_v3`, while the no-spend research
matrices often use the lexical `v2`-style control because it is cheaper and more
reproducible for broad sweeps.

Several offline source-admission lanes have also tested `min_margin=0.0` and
the phrase-policy candidate margin `0.005`; this plan should not blur those
lanes. Each comparison row must record its policy and thresholds explicitly.

## Why The Current Control Is Plausible

The current control is a one-versus-nearest-competitor prototype classifier.
It is plausible because semantic veto is not only asking whether a sentence is
related to the active sense. It is asking whether the sentence is closer to the
active sense than to every known alternative sense.

For `change:cambio`, the useful question is not:

```text
Is the sentence similar to "cambio"?
```

The useful question is:

```text
Is the sentence closer to "the process of becoming different" than to
"to become something different", "money received in return", and other
non-target senses?
```

That structure makes an active-vs-strongest-competitor rule a reasonable
starting point.

## Why The Current Control Is Not Proven Best

The current control hides several assumptions:

- one context representation is enough
- one active representation is enough
- a single scalar similarity score is meaningful across families
- the strongest competing sense is the only competitor that matters
- a fixed active threshold and margin can work across different trigger shapes
- source rows have equal trust after admission
- phrase/no-winner cases can be handled by a separate guard rather than by the
  semantic scorer

The existing ablations support the current control as a usable baseline. They
do not prove that it is the best possible decision rule. This plan should turn
that open question into an explicit test program.

## Core Decomposition

Do not compare full algorithms before decomposing them. The hidden expression:

```text
active_score = similarity(c, a)
```

must be split into:

```text
active_score =
  aggregate_over_source_rows(
    score(
      context_representation(sentence),
      sense_representation(active_source_rows)
    )
  )
```

The comparison must isolate:

1. context representation
2. sense representation
3. scoring function
4. score aggregation
5. active-vs-shadow competition rule
6. phrase/no-winner handling
7. source confidence and source provenance
8. phrasing, token order, and syntactic frame

## Harness Preservation Rules

Keep the testing harness intact as durable research infrastructure.

- Do not use a generic `done` state for research lanes. Use explicit states:
  `idea_recorded`, `queued_next`, `harness_partial`,
  `harness_ready_unswept`, `swept_inconclusive`, `swept_negative`,
  `swept_promising_control`, `active_source_program`, or
  `parked_second_lane`.
- Keep `docs/test_inputs/semantic_decision_research_lanes_en_es.json` updated
  whenever a new idea, partial mechanism, sweep, or promotion candidate appears.
  Regenerate `docs/test_outputs/semantic_decision_research_lanes_latest.md`
  with `scripts/testing/semantic_decision_research_lanes_summary.py`.
- A lane is not swept unless it has a reproducible manifest or generated
  artifact. A lane is not promotable unless it beats the incumbent on frozen
  plus held-out suites and passes negative controls.
- Do not mark a mechanism as failed globally when only one form was tested. For
  example, the first phrasing/order sweep rejected synthetic frame labels over
  gloss text; it did not reject real source-aligned phrasing rows or dynamic
  evidence selection.
- Add new research lanes as sibling manifests or explicit harness extensions;
  do not overwrite older manifests just because a newer idea is more promising.
- Keep the final decision-rule bakeoff separate from `active_score` surface
  bakeoffs. A row that changes `c`, `a`, scorer, or aggregation is testing the
  score surface, not proving a new final YES/NO rule.
- Keep frozen input hashes and evaluation-suite fingerprints in every artifact
  so later source additions cannot silently move the comparison target.
- Keep full score traces available for broad/debug manifests, but allow compact
  JSON for large bakeoffs when Markdown keeps the human-facing findings.
- For multi-suite no-spend scorers such as TF-IDF, fit per evaluation suite
  unless a manifest explicitly declares a cross-suite fit. Adding held-out
  sentences must not alter frozen-suite scores.
- Dynamic definitions of `c` or `a` are allowed, but they must be implemented as
  named, reproducible surface rows before being compared. Examples include
  multi-context scoring, source-family agreement, context-conditioned evidence
  selection, and phrase-risk-specific context selection.
- Phrasing-level experiments are first-class `active_score` surface work. They
  should be labeled separately from ordinary context windows because they test
  whether order, syntactic role, and local phrase shape matter, not just which
  words are present.
- No production policy or runtime default changes from these harnesses until a
  candidate passes frozen, held-out active/shadow, and phrase/no-winner suites
  without adding harmful replacements.

## Current Wave6 Source/Guard Finding

This is a research-methodology finding, not a runtime-policy or promotion
claim. Generated reports below are supporting evidence; promotion authority
still requires the reconciliation registry, locked heldout breadth, and the
rulegen quality loop.

The 2026-04-29 wave6 evidence slice confirms that source coverage and guard
composition are still more important than the final scalar margin alone.

New source work:

- Wiktextract translation-sense evidence covers `38 / 38` selected wave6
  senses across `16 / 16` families and passes leakage/sense admission.
- WordNet alternate-sense phrase evidence adds phrase-control rows for
  `16 / 16` families. This is a real no-winner coverage improvement, not a
  production policy by itself.
- Authorization-frame evidence adds `5` deterministic English rows for
  source-backed permission/authorization senses. The adapter uses the selected
  sense's source gloss or translation-sense text to decide whether a generic
  class frame is allowed, and it excludes browser-sentence text, Spanish target
  lemmas, and the heldout-specific `manager` wording from emitted evidence.

Guard/margin results:

- Semantic phrase prototypes alone protect the 16-row phrase/no-winner suite at
  zero harm, but over-abstain active cases.
- An independent phrase-prototype dominance margin is useful but insufficient.
  The best zero-harm active/shadow point tested so far is active margin `0`,
  phrase margin `0.02`: `0` harmful, `7` false abstains, `56.2%` recall,
  `81.6%` accuracy.
- A hybrid semantic-phrase-prototype plus surface-POS guard is the strongest
  active/shadow signal so far: active margin `0`, phrase margin `0.02` gives
  `0` harmful, `2` false abstains, `87.5%` recall, `94.7%` accuracy.
- The hybrid is not promotable because the wave6 phrase/no-winner suite
  regresses to `2` harmful replacements: `low` rating and `bear` animal.
- A replay-only rescue-gating sweep tested general active-score and phrase-lead
  ceilings over the fixed hybrid score traces. It found no passing policy:
  phrase/no-winner can be restored to `0` harmful / `0` false abstains, but the
  best active/shadow rows still have `0` harmful / `2` false abstains.
- The surface-POS margin sweep now has a replay path, so scorer-backed traces
  are computed once and margin/phrase-margin policies are replayed cheaply. A
  context-view sweep over the same hybrid shape found a real context signal:
  `raw_sentence` and `raw_window` recover the dark `black` active row at margin
  `0`, phrase margin `0.02`; `masked_sentence` does not. Raw-sentence held-out
  validation reaches `0` harmful, `1` false abstain, `93.8%` recall, and
  `97.4%` accuracy on active/shadow.
- Adding the authorization-frame source rows to the raw-sentence hybrid lane
  closes the remaining `leave:001` active false abstain without adding active
  harmful replacements: active/shadow held-out validation is now `0` harmful,
  `0` false abstains, `100%` recall, and `100%` accuracy across `38` cases.
- The authorization-frame source rows do not themselves repair phrase/no-winner
  harm, which is expected because they target active source evidence. The
  paired rescue replay now finds `12` passing policies across active/shadow plus
  phrase/no-winner suites. The recommended replay policy is active margin `0`,
  phrase margin `0.02`, rescue active floor `0.52`, no noun phrase-lead rescue,
  and modifier phrase-lead ceiling `0.02`.

Current interpretation:

- Surface-POS rescue is useful. It recovers many active noun/adjective cases
  that semantic phrase prototypes over-block.
- Surface-POS rescue is too broad when it can override strong no-winner evidence.
  Rescue gates are therefore a candidate policy family only when evaluated
  jointly with active/shadow and phrase/no-winner suites.
- Dark `black` is no longer a blocker under raw sentence or raw window context,
  which suggests that trigger masking removed useful literal-darkness evidence
  for this class.
- `leave` permission-vs-absence is no longer a blocker under the
  source-backed authorization-frame adapter. The important distinction is that
  this is a class/source mechanism, not a hand row for the word `leave`.
- The phrase/no-winner rescue regressions remain `low` rating and `bear`
  animal in the unrescued validation artifact, but the replayed rescue gates can
  block them without reintroducing active false abstains under the auth-frame
  raw-sentence score surface.
- The next fair test is breadth: add more source-detectable semantic classes,
  expand locked heldout families, and verify that the same source-admission plus
  rescue-replay process keeps zero harmful replacements outside this wave.

Relevant artifacts:

- `docs/test_outputs/semantic_source_margin_policy_sweep_non_v10_wave6_alt_phrase_semantic_phrase_margin_grid_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_heldout_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_phrase_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_heldout_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_phrase_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_non_v10_wave6_alt_phrase_semantic_surface_pos_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_window_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_non_v10_wave6_alt_phrase_semantic_surface_pos_masked_window_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_raw_sentence_latest.md`
- `docs/test_outputs/semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md`
- `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md`
- `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.md`

## Context Representations To Compare

Each context representation must preserve the same input sentence and trigger.

Required candidates:

- `raw_sentence`
  - Example: `The company announced a major change in strategy.`
- `masked_sentence`
  - Example: `The company announced a major ___ in strategy.`
- `raw_window`
  - Fixed trigger-centered token window.
- `masked_window`
  - Fixed trigger-centered token window with the trigger replaced.
- `preceding_following_tokens`
  - Compact surface context such as previous token, next token, and local POS
    shape.
- `phrase_frame`
  - Surface pattern such as `the rest of`, `file past`, `keep the ball rolling`.
- `sentence_plus_neighbor`
  - Current sentence plus nearby sentence or paragraph context.
  - This is prospective and should be tested only after the sentence-only
    harness is stable.

Questions to answer:

- Does masking the trigger prevent trivial trigger-word matching?
- Does masking remove useful information for short sentences?
- Does a local window reduce noise or remove needed disambiguation?
- Do phrase frames catch no-winner cases that semantic similarity misses?
- Does paragraph context help enough to justify runtime complexity?

## Phrasing And Word-Order Surfaces To Compare

Bag-of-words scoring can make two sentences look similar even when word order,
syntactic role, or local construction changes the meaning. This is especially
relevant for phrases such as `change for`, `bank on`, `file past`, `play out`,
and for same-word active/shadow conflicts where the nearby words are shared but
their arrangement differs.

Required candidates:

- `ordered_ngram_context`
  - Preserve adjacent token order around the trigger. Example: `major ___ in`,
    `___ for a twenty`, `bank on`.
- `skipgram_context`
  - Preserve loose ordered pairs within a small trigger window so useful
    long-distance local cues survive short insertions.
- `before_after_slot_context`
  - Represent the left and right trigger context separately. Example:
    `left=major`, `right=in strategy`.
- `surface_frame_context`
  - Normalize the trigger slot inside a compact frame. Example: `VERB on OBJ`,
    `NOUN for MONEY`, `the NOUN of`.
- `pos_frame_context`
  - Use local POS or coarse syntactic shape around the trigger. Example:
    `DET ADJ TRIGGER PREP NOUN`.
- `dependency_role_context`
  - Capture whether the trigger is a subject, object, complement, phrasal-verb
    head, or prepositional object. The first no-spend lane uses a cheap local
    approximation; a real parser remains a second-lane candidate if this family
    shows promise.
- `negation_modal_context`
  - Preserve nearby negation, modality, and comparison markers when they affect
    sense or replacement safety.
- `ordered_evidence_phrase`
  - Keep source/example wording order instead of flattening it into unordered
    evidence text.
- `canonical_template_evidence`
  - Rephrase evidence rows into consistent templates such as `X means ...`,
    `X is used when ...`, or `X appears in contexts like ...`.
- `paraphrase_variant_evidence`
  - Compare multiple manually or generated paraphrases of the same sense to see
    whether active evidence is too brittle to one phrasing.

Negative controls:

- `shuffled_context_tokens`
  - Same words as the browser context, randomized order. An order-sensitive
    scorer should degrade.
- `reversed_context_tokens`
  - Browser context tokens reversed. Useful for detecting accidental bag-of-
    words equivalence.
- `shuffled_evidence_tokens`
  - Same evidence words, randomized order. A phrase-sensitive evidence scorer
    should degrade if order carries signal.
- `frame_only_without_lexical_content`
  - Keep only phrase/POS frame. This should not replace ordinary semantic
    evidence unless a phrase/no-winner lane explicitly proves it.
- `lexical_only_without_frame`
  - Keep cue words but remove their local order/frame, to test whether phrase
    wins are just lexical leakage.

Questions to answer:

- Are current TF-IDF wins mostly word-presence wins, or do we need order-aware
  context to separate active from shadow cases?
- Which failure classes require phrase frame rather than semantic evidence?
- Can simple ordered n-gram or before/after-slot features provide most of the
  gain without a parser?
- Does order-sensitive evidence help active cases, or only reduce harmful
  replacements?
- Should dynamic `c` select a phrase/frame representation for high-risk local
  patterns and a semantic sentence representation elsewhere?
- Should dynamic `a` select example rows whose phrasing matches the browser
  frame, rather than always scoring definitions and examples together?

## Sense Representations To Compare

Representations must be tested for both active and competing senses.

Required candidates:

- `gloss_only`
  - Example active text: `the process of becoming different`
- `sense_label`
  - Example: `change noun sense: the process of becoming different`
- `sense_gloss_bundle`
  - Example: `change noun sense: ... | the process of becoming different`
- `all_evidence_text`
  - Current broad evidence view.
- `definition_rows_separate`
  - Keep WordNet or source definitions as separate rows.
- `example_rows_separate`
  - Keep examples as separate rows.
- `definition_and_example_rows_separate`
  - Do not concatenate until aggregation time.
- `admitted_source_bundle`
  - All source rows that passed leakage, duplicate, and sense admission.
- `reviewed_only_bundle`
  - Reviewed rows only, where available.
- `external_only_bundle`
  - WordNet/Wiktionary/Wiktextract style rows only.
- `source_family_bundles`
  - Separate reverse-aux, WordNet, Wiktextract, Wiktionary, FreeDict, generated,
    and reviewed rows.

Questions to answer:

- Does gloss-only under-describe real browser usage?
- Do examples carry practical usage better than definitions?
- Does concatenating all evidence blur multiple sub-senses into one noisy text?
- Do multiple admitted rows outperform a single prototype string?
- Does source family matter after sense admission, or can admitted rows be
  treated equally?

## Scoring Functions To Compare

Required candidates:

- `token_jaccard`
  - Cheap lexical overlap control.
- `tfidf_cosine`
  - Cheap bag-of-words weighted control.
- `sentence_transformer_cosine`
  - Current strongest semantic embedding lane.
- `cross_encoder_similarity`
  - Prospective: score the sentence and sense text jointly rather than embedding
    them independently.
- `entailment_score`
  - Prospective: ask whether the sentence entails, supports, or contradicts the
    sense gloss.
- `definition_question_answering`
  - Prospective: ask which sense definition answers the sentence context.
- `small_supervised_classifier`
  - Prospective: train on held-out active/shadow/no-winner rows using features
    from scores, source metadata, POS shape, and phrase signals.
- `learned_reranker`
  - Prospective: rank active and shadow senses from all features, then apply an
    abstention rule.

Questions to answer:

- Does the current sentence-transformer lane win because it understands meaning,
  or because source rows were tuned to it?
- Does TF-IDF remain competitive when source rows are cleaner?
- Does a cross-encoder materially reduce same-POS ambiguity?
- Does entailment avoid false matches from semantically adjacent but wrong
  senses?
- Is any learned model stable under family-level holdout?

## Active And Shadow Score Aggregation

When each sense has multiple source rows, do not force a single text too early.

Required aggregation candidates:

- `single_concatenated_text`
  - Current simple representation for many lanes.
- `max_row_score`
  - A sense wins if any admitted row strongly matches.
- `mean_row_score`
  - A sense wins by broad average support.
- `top_k_mean`
  - Average the best `k` row scores to avoid one lucky row dominating.
- `source_weighted_mean`
  - Weight rows by source family or review status.
- `source_weighted_top_k`
  - Combine row selectivity with source confidence.
- `agreement_count`
  - Count how many independent rows exceed a threshold.
- `minimum_agreement_by_source_family`
  - Require at least two source families to agree before replacement.
- `definition_example_agreement`
  - Require both a definition-like row and example-like row to support active
    replacement.

Questions to answer:

- Does max scoring rescue legitimate sparse evidence, or does it overfit to one
  lucky row?
- Does averaging punish senses with diverse but valid evidence?
- Does source weighting reduce wrong WordNet sense effects?
- Does requiring agreement reduce harmful replacements too much?

## Decision Rules To Compare

Keep the current rule as the control.

Required decision candidates:

- `active_minus_strongest_shadow`
  - Current control.
  - `YES` when `active_score - max_shadow_score >= threshold`.
- `active_ratio_strongest_shadow`
  - `YES` when `active_score / max_shadow_score >= threshold`.
- `softmax_probability`
  - Convert active and shadow scores into a probability distribution.
  - `YES` when active probability exceeds threshold.
- `pairwise_active_beats_all_shadows`
  - Active must beat every shadow by a minimum gap.
- `pairwise_active_beats_most_shadows`
  - Active may lose to one weak or unreliable shadow but must beat most.
- `active_absolute_only`
  - Negative control: ignores shadows.
- `shadow_veto_only`
  - Negative control: abstains only when a shadow is strong.
- `abstention_first_agreement`
  - `YES` only when multiple independent active views agree and no shadow or
    phrase view objects.
- `calibrated_logistic_classifier`
  - Features include active score, strongest shadow score, margin, ratio,
    active row count, shadow row count, POS shape, source confidence, phrase
    signals, and context type.
- `family_calibrated_thresholds`
  - Different thresholds per trigger family or POS shape.
- `cluster_calibrated_thresholds`
  - Different thresholds for same-POS noun/noun, cross-POS noun/verb, phrase
    risk, short-context, and source-sparse clusters.

Questions to answer:

- Is nearest-shadow margin enough, or do multiple shadows jointly matter?
- Does ratio behave better when scores are globally high or low?
- Does softmax hide close absolute scores?
- Are family-specific thresholds real signal or overfitting?
- Can a learned classifier beat the simple rule under leave-family-out testing?

## Phrase And No-Winner Handling

Phrase/no-winner cases must stay separate from ordinary active/shadow semantic
competition unless an ablation proves otherwise.

Required candidates:

- `phrase_guard_off`
  - Negative control.
- `phrase_guard_patterns_only`
  - Current pattern/preemption style.
- `phrase_as_semantic_shadow`
  - Negative control unless it proves safe.
- `phrase_containment_only`
  - Phrase rows can force abstain but cannot compete as broad meanings.
- `phrase_classifier`
  - Prospective: separate classifier for no-winner cases.
- `phrase_then_semantic`
  - First detect phrase/no-winner; if no hit, run semantic active/shadow.
- `semantic_then_phrase`
  - First score semantic active/shadow; then allow phrase guard to override.

Questions to answer:

- Are phrase cases best handled outside the semantic scorer?
- Which phrase frames are general enough to preserve?
- Does phrase-as-shadow create false abstains?
- Does phrase-first reduce harmful replacements without hurting active recall?

## Source-Data Polysemy Checks

The system must solve polysemy twice:

1. source-data polysemy
   - Which WordNet/Wiktionary/source row actually represents the intended sense?
2. browser-sentence polysemy
   - Which sense does this page sentence express?

For `change:cambio`, the source-data failure mode is:

```text
intended active gloss:
  the process of becoming different

bad source row:
  money received in return for its equivalent in a larger denomination

why it fooled the old linker:
  weak overlap on a generic word such as different
```

Required source-polysemy tests:

- wrong WordNet first-sense row
- wrong high-overlap WordNet row
- right low-overlap WordNet row
- example row that matches active but not the exact gloss
- definition row that matches active but looks close to a shadow
- same-POS active/shadow source rows
- cross-POS active/shadow source rows
- target-side duplicate or same-visible-replacement rows
- source row admitted by lexical scoring but rejected by semantic scoring
- source row admitted by semantic scoring but suspicious under source-rank or
  source-family checks

Questions to answer:

- Should source sense rank influence scoring after admission?
- Should weak lexical links require a second source family?
- Should WordNet definitions and examples have different trust weights?
- Should source selection be optimized jointly with runtime decision accuracy,
  or kept as a separate admission problem?

## Evaluation Data To Freeze

Before comparing decision rules, freeze the same inputs for every row.

Required suites:

- full `v10` synthetic sentence-veto suite
- v2 active/shadow held-out suite
- phrase/no-winner v1
- phrase/no-winner v2
- independent phrase challenge v1
- phrase stress v1
- non-v10 phrase signal rows
- first non-v10 source-backed held-out suite
- selected-wave non-v10 held-out active/shadow rows
- selected-wave non-v10 phrase rows
- supported wave64 portfolio-selected `16`-family active/shadow rows once added
- supported wave64 portfolio-selected phrase/no-winner rows once added

Required future splits:

- family holdout
- POS-shape holdout
- source-family holdout
- same-POS ambiguity holdout
- cross-POS ambiguity holdout
- short-context holdout
- phrase-risk holdout
- trigger-frequency band holdout

## Evaluation Measures

Do not rank by one headline number.

Primary measures:

- harmful replacement count
- false abstain count
- replace recall
- replace precision
- decision accuracy
- family-level pass count
- phrase/no-winner harmful replacement count
- active/shadow harmful replacement count

Secondary measures:

- winner accuracy
- active score distribution
- strongest shadow score distribution
- margin distribution
- source family contribution
- row-count sensitivity
- runtime cost
- model/package size
- deterministic reproducibility

Hard gates:

- any increase in harmful replacements must be treated as blocking unless the
  lane is explicitly exploratory
- phrase/no-winner regressions must be reported separately
- family-level regressions must not be hidden by aggregate improvement
- no generated or external row may count as source evidence unless it passed
  leakage, duplicate, and sense-discrimination admission

## Negative Controls

Run these to prove the harness catches bad logic:

- active-only source
- shadow-only source
- no-shadow competition
- shuffled active/shadow labels
- wrong WordNet sense rows
- source rows before admission filtering
- phrase rows used as broad semantic prototypes
- trigger-only context
- target-lemma-only active representation
- random source row assignment
- source rows from another family
- over-large margin
- zero-margin with phrase guard off

Expected behavior:

- active-only should over-replace
- shadow-only should over-abstain
- shuffled labels should fail badly
- wrong WordNet rows should expose source-polysemy brittleness
- phrase-as-semantic should either fail or prove a surprising real gain

## Comparison Matrix

Every comparison row should record:

- source lane id
- source admission artifact
- held-out suite ids
- context representation
- evidence representation
- scoring function
- aggregation rule
- decision rule
- thresholds
- phrase/no-winner mode
- source-family weights, if any
- runtime cost estimate
- harmful replacement count
- false abstain count
- replace recall
- phrase harmful count
- active/shadow harmful count
- family-level failures
- failure-class summary

Minimum first matrix:

| Context | Evidence | Scorer | Aggregation | Decision | Phrase Mode |
| --- | --- | --- | --- | --- | --- |
| `masked_sentence` | `all_evidence_text` | `sentence_transformer_cosine` | `single_concatenated_text` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `max_row_score` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `top_k_mean` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `active_ratio_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `softmax_probability` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `pairwise_active_beats_all_shadows` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `tfidf_cosine` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |
| `raw_sentence` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_window` | `definition_and_example_rows_separate` | `sentence_transformer_cosine` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |

Prospective second matrix:

| Context | Evidence | Scorer | Aggregation | Decision | Phrase Mode |
| --- | --- | --- | --- | --- | --- |
| `masked_sentence` | `definition_and_example_rows_separate` | `cross_encoder_similarity` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | `definition_and_example_rows_separate` | `entailment_score` | `source_weighted_top_k` | `active_minus_strongest_shadow` | `patterns_only` |
| `masked_sentence` | feature bundle | score features | feature vector | `calibrated_logistic_classifier` | `patterns_only` |
| `masked_sentence` | feature bundle | score features | feature vector | `learned_reranker` | `phrase_then_semantic` |

## Implementation Checklist

1. Freeze the evaluation inputs.
   - Record exact dataset paths and source batch ids.
   - Keep source evidence fixed while testing decision rules.
2. Extend or add a comparison harness.
   - Prefer a new script if existing ablation code would become unclear.
   - The harness should produce JSON and Markdown.
3. Add context-representation variants.
   - Start with existing raw/masked sentence and window views.
4. Add evidence-representation variants.
   - Add separate-row active/shadow scoring before any learned model.
5. Add aggregation variants.
   - Implement max, mean, top-k mean, and source-weighted top-k first.
6. Add decision-rule variants.
   - Implement margin, ratio, softmax, and pairwise before classifier lanes.
7. Add negative controls.
   - Do this before interpreting a better score.
8. Run the first no-spend matrix.
   - Compare current control against cheap variants first.
9. Add failure-class mining for matrix rows.
   - Report family tokens and failure reasons.
10. Only then consider higher-cost models.
    - Cross-encoder, entailment, classifier, and learned reranker require a
      stronger train/validation split.
11. Document every finding in this file or a generated findings artifact.
    - Record wins, losses, regressions, and inconclusive rows.
12. Promote only with strict evidence.
    - A more complex rule must beat the control on held-out data without adding
      harmful replacements or hiding family regressions.

## Findings Ledger

Current known findings:

- The active-minus-strongest-shadow margin rule is the current control, not a
  proven optimum.
- Sentence-transformer scoring has outperformed lexical controls on the strongest
  source-admission lanes, but source quality has often mattered more than scorer
  choice.
- Phrase/no-winner cases should remain separate from broad semantic competition
  unless an ablation proves otherwise.
- The `change:cambio` WordNet issue showed that source-data polysemy can corrupt
  active evidence before runtime scoring starts.
- Weak WordNet lexical links now use source sense rank as a prior, and broader
  extraction slates let admission reject bad source rows.
- The supported wave64 source portfolio reached a `16`-family semantic source
  control without unsupported translations, but it still needs held-out active
  / shadow and phrase validation before any quality claim.
- The first decision-rule matrix harness is implemented at
  `scripts/testing/semantic_decision_rule_matrix_en_es.py`. It records frozen
  input hashes, score traces, negative controls, threshold/dropout diagnostics,
  family winners, decision-signature clusters, tied-headline groups, and
  discovery-selection versus locked-eval summaries.
- The structurally similar family bakeoff in
  `docs/test_inputs/semantic_decision_family_bakeoff_en_es.json` shows that many
  final decision rules tie at the same headline metric because they make the
  exact same replace/no-replace choices. The tie is therefore real at the final
  classifier level, but the score surfaces are not identical: ROC AUC and
  average precision separate margin/softmax from pairwise and ratio variants.
- Lower active thresholds can recover false abstains, but the current fixed
  source/evidence surface turns that gain into harmful replacements. In the
  family bakeoff, the clearest tradeoff rows fix many false abstains only by
  introducing dozens of harmful replacements, so they are exploratory and not
  promotable.
- The suite-confirmation manifest
  `docs/test_inputs/semantic_decision_suite_confirmation_en_es.json` now runs
  selected decision families across frozen v10, active/shadow held-out v2,
  phrase held-out v2, and phrase challenge v1. It fits TF-IDF per evaluation
  suite so adding held-out sentences cannot change frozen-v10 scores.
- The current suite-confirmation result preserves phrase/no-winner behavior on
  the phrase suites, but active/shadow held-out v2 remains the bottleneck under
  this fixed source surface: the selected candidates share the same final
  decisions, including one harmful replacement and eighteen false abstains on
  `source_heldout_v2`.
- The first active-score surface bakeoff in
  `docs/test_inputs/semantic_active_score_surface_bakeoff_en_es.json` keeps the
  final decision rule fixed and varies `c`, `a`, scorer, and aggregation across
  the same frozen plus held-out suites.
- That active-score bakeoff found a small real no-spend improvement signal:
  separate evidence rows with `max_row_score` or `top_k_mean` produced `0`
  harmful replacements and `45` false abstains overall, versus the fixed
  current TF-IDF masked/all-evidence control at `1` harmful replacement and
  `46` false abstains. The improvement is concentrated in preserving phrase
  suites while removing the active/shadow held-out harmful replacement.
- The same bakeoff also showed why threshold-only relaxation is dangerous:
  more permissive variants can recover false abstains but quickly introduce
  harmful replacements, and target-lemma-only failed as expected with heavy
  lexical leakage.
- Phrasing and word-order surfaces are now an explicit next research axis.
  Current TF-IDF rows are mostly word-presence controls; they do not prove that
  ordered local cues, before/after slots, phrase frames, POS frames, or ordered
  evidence wording are unnecessary.
- The first phrasing/order bakeoff in
  `docs/test_inputs/semantic_phrasing_order_surface_bakeoff_en_es.json`
  implements ordered n-gram, skip-gram, before/after slot, surface-frame,
  POS-frame, heuristic dependency-role, negation/modal, ordered-evidence,
  canonical-template, paraphrase, shuffled-context, reversed-context, and
  shuffled-evidence surfaces.
- That phrasing bakeoff did not beat the prior separate-row evidence control.
  The best row remains `definition_and_example_rows_separate` with
  `max_row_score` at `0` harmful replacements and `45` false abstains. The best
  pure phrasing/frame candidates stayed safe but over-abstained at `55+` false
  abstains; the first dependency-role approximation also landed in this group
  at `0` harmful replacements and `55` false abstains.
- The phrasing negative probes were informative: shuffled/reversed context and
  shuffled evidence can leak heavy harmful replacements under permissive
  thresholds. Word order and frame surfaces therefore need aligned source
  examples or a model that understands paired context/evidence phrasing; simple
  synthetic frame labels over gloss text are not enough.
- The first context-conditioned evidence bakeoff in
  `docs/test_inputs/semantic_context_conditioned_evidence_bakeoff_en_es.json`
  loads the admitted WordNet definition/example source batch, attaches `87/87`
  source rows, and tests whether the browser context should select a different
  active/shadow evidence row before the final active-vs-shadow margin rule.
- That context-conditioned bakeoff did not beat the simpler row-level control.
  The best safe selector families were source-plus-definition rows selected by
  before/after or surface-frame context at `0` harmful replacements and `53`
  false abstains; pure source-row selectors landed at `0` harmful replacements
  and `55` false abstains. The prior separate-row max control remains better at
  `0` harmful replacements and `45` false abstains.
- The bounded sentence-transformer source-row subset in the same bakeoff was
  diagnostically useful but unsafe: it improved winner-ranking metrics and
  reduced false abstains, but every tested source-row sentence-transformer
  variant introduced harmful replacements. It is not promotable under the
  current zero-harm safety rule.
- The source-row alignment audit in
  `docs/test_outputs/semantic_source_row_alignment_audit_en_es_latest.md`
  explains why the first context-conditioned selector did not get a fair chance
  to win as a phrasing mechanism: only `16/87` audited rows contain the trigger,
  only `7` have a two-sided trigger frame, and only `5` families have both
  active and shadow selector-ready rows.
- The source-frame gap plan in
  `docs/test_outputs/semantic_source_frame_gap_plan_en_es_latest.md` turns that
  alignment failure into an executable no-spend queue: `38` active/shadow sense
  slots, `23` missing selector-ready slots, and `97` planned candidate requests.
  The request rows now include the `expected_row_preview`, model, roles, and
  prompt-slot metadata expected by the existing generation runner. Prompts use
  sense labels and glosses only; they do not include reviewed evaluation
  sentences.
- The first live aligned-frame run
  `docs/test_outputs/semantic_source_frame_gap_generation_run_latest.md`
  generated `97` rows. Admission was intentionally strict: leakage/duplicate
  filtering kept `37`, sense admission rejected `1`, and `36` candidate rows
  survived. Merged with the `87`-row source control, the source-admission
  ablation improved to `0` harmful replacements and `1` false abstain on frozen
  v10, but active/shadow held-out v2 still had `1` false abstain. This is a real
  source-quality improvement, not a promotion.
- The first live run also exposed a prompt-process problem: many repeated
  candidate requests produced near-duplicate sentence frames. The frame-gap
  planner now emits `aligned-sentence-frame-v2` prompts with per-attempt
  diversity frames. After auditing the v1 composite, only one selector-ready
  gap remained, so the v2 plan requested `5` board-shadow rows rather than
  regenerating the whole original queue.
- The v2 micro-run
  `docs/test_outputs/semantic_source_frame_gap_generation_run_v2_latest.md`
  generated `5` rows; admission kept `3`. The resulting v2 composite has
  `126` admitted rows and all `19` families are selector-ready for active/shadow
  dynamic selection. It still does not pass the active/shadow held-out threshold
  because `en-es:source-heldout:v2:cell:001` remains a false abstain.
- The v2 context-conditioned bakeoff in
  `docs/test_outputs/semantic_context_conditioned_evidence_llm_aligned_v2_bakeoff_en_es_latest.md`
  improves the best source-plus-definition selector to `0` harmful replacements
  and `47` false abstains, versus `53` in the first source-row selector pass.
  The separate definition/example row control still leads at `0` harmful and
  `45` false abstains, so dynamic source selection remains promising
  infrastructure rather than a promotable decision policy.
- A focused cell/source-scope trace then separated the remaining held-out
  failure from the final decision rule. The LLM-v2 source lane still abstained
  on `en-es:source-heldout:v2:cell:001` because it lacked red-blood/oxygen
  active evidence. The existing WordNet active-related reference lane already
  contained blood-cell evidence and fixed that case, but broad reference rows
  could barely over-replace `holding cell` unless margin/source scope was
  controlled.
- The source-scope margin bakeoff in
  `docs/test_outputs/semantic_source_scope_margin_bakeoff_en_es_latest.md`
  added per-row source evidence scopes and tested source rows as both partial
  replacements and true supplements to the row-level control. The important
  result is the additive surface:
  `definition_example_plus_source_rows_separate` with combined LLM-v2 plus
  WordNet-reference rows produced `0` harmful replacements and `37` false
  abstains across frozen v10, source-heldout v2, phrase-heldout v2, and phrase
  challenge. The prior no-source row control was `0` harmful and `44` false
  abstains. Source-heldout v2 improved from `0/17` to `0/12`, while phrase
  suites stayed clean.
- This changes the current best no-spend interpretation. Source rows should be
  tested as additive evidence over the incumbent definition/example rows, not
  as a replacement for those rows. The earlier source-plus-definition surface
  omitted the incumbent auxiliary/example rows and therefore understated the
  value of source coverage.
- The dedicated sentence-transformer row-level bakeoff in
  `docs/test_outputs/semantic_sentence_transformer_row_level_bakeoff_en_es_latest.md`
  tested the same additive source surface with a semantic scorer and its own
  thresholds. It is not promotable: the best additive-source top-k row tied the
  sentence-transformer definition/example control at `1` harmful replacement
  and `31` false abstains, with the harmful case isolated to source-heldout v2.
  The negative controls all failed as expected, so the result is a real
  negative/inconclusive scorer finding rather than a harness failure.

Findings to fill after broader representation/source matrices:

- best context representation:
  first active-score surface bakeoff favors `raw_window` among simple context
  alternatives, but row-level evidence aggregation beat context-only changes.
- best phrasing / word-order representation:
  first pass tested ordered n-grams, skip-grams, before/after slots, phrase
  frames, POS frames, heuristic dependency roles, and shuffled/reversed
  controls. None beat separate-row evidence yet. The first context-conditioned
  source-row pass also failed to beat separate-row evidence. The v1/v2 aligned
  source-frame runs improved the source selector from `0/53` false abstains to
  `0/47`, but not past the `0/45` row-level control. Next phrasing work should
  focus on the remaining held-out false-abstain class and on stronger
  source-family/row-agreement signals before considering promotion.
- best active/shadow representation:
  additive `definition_example_plus_source_rows_separate` with combined LLM-v2
  and WordNet-reference rows is the current best no-spend research candidate:
  `0` harmful replacements and `37` false abstains across the four-suite
  source-scope margin bakeoff. The older no-source row control remains the
  runtime-safe incumbent until this additive surface passes the companion
  negative-control and broader held-out promotion checks.
- best scoring function:
  TF-IDF remains the most useful no-spend control for surface iteration;
  sentence-transformer fixed and source-row probes ranked active cases better
  but introduced harmful replacements under the tested thresholds. The
  dedicated row-level sentence-transformer bakeoff did not beat its own
  no-source control and is not a promotion candidate in the tested form.
- best aggregation rule:
  `max_row_score` currently leads the additive source-evidence surface. Earlier
  fixed-source controls also favored `max_row_score` or `top_k_mean`; source
  agreement and calibrated row weighting remain unswept.
- best decision rule:
  current fixed-surface evidence favors the existing margin-shaped control; no
  tested final decision family is promotable yet.
- best phrase/no-winner handling:
  phrase override remains the control; current suite confirmation did not expose
  phrase held-out regressions for selected candidates.
- strongest negative-control failure:
  companion broad matrix keeps active-only, shadow-only, no-shadow, shuffled,
  and target-lemma-only controls visible.
- strongest family-level regression:
  lower active-threshold margin rows recover some replacements but introduce
  harmful replacements, including phrase-held-out leakage in suite confirmation.
- runtime feasibility notes:
  no production runtime policy change is justified from this matrix alone.
- recommendation:
  treat the final decision rule as provisionally adequate; continue the next
  major test effort on source/evidence representation, especially separate-row
  and dynamic `c`/`a` candidates, while keeping this matrix as the promotion
  gate for any future scorer or source-lane change.

## Promotion Standard

A challenger decision algorithm can replace the current control only if it:

- uses the same frozen source evidence or clearly records source changes
- passes active/shadow held-out suites
- passes phrase/no-winner suites
- does not increase harmful replacements
- reduces false abstains or improves family breadth
- survives family-level and POS-shape analysis
- has a clear runtime feasibility path
- has a simpler explanation than its gain justifies, or a measured gain large
  enough to justify the extra complexity

Until then, the active-minus-strongest-shadow rule remains the control.
