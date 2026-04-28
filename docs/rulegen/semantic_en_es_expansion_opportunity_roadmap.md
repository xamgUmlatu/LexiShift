# Semantic en-es Expansion Opportunity Roadmap

Status: active opportunity ledger
Role: Planning / backlog
Purpose: preserve every known direction opened by the reverse-aux plus WordNet plus Wiktextract semantic-source result
Last updated: 2026-04-29
Source-of-truth: planning doc only; executable truth lives in source-admission scripts and generated artifacts
Primary reference result:
- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json`
- `docs/test_outputs/semantic_source_reference_lane_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md`
- `docs/test_outputs/semantic_source_heldout_validation_v2_latest.md`
- `docs/test_outputs/semantic_source_phrase_heldout_validation_latest.md`
- `docs/test_outputs/semantic_source_phrase_heldout_v2_margin005_validation_latest.md`
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_challenge_cases_v1.json`
- `docs/test_outputs/semantic_source_phrase_challenge_v1_margin005_validation_latest.md`
- `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_stress_cases_v1.json`
- `docs/test_outputs/semantic_source_phrase_stress_v1_margin005_validation_latest.md`
- `docs/test_inputs/semantic_routing_cases/en_es_phrase_policy_signal_non_v10_v1.json`
- `docs/test_outputs/semantic_phrase_policy_signal_non_v10_latest.md`
- `docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_probe_v1.json`
- `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_margin_policy_sweep_latest.md`
- `docs/test_outputs/semantic_source_failure_class_mining_latest.md`
- `docs/test_outputs/semantic_non_v10_inventory_candidates_latest.md`
- `docs/test_outputs/semantic_non_v10_wave2_draft_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave16_latest.md`
- `docs/test_outputs/semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_heldout_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_phrase_margin005_validation_latest.md`
- `docs/test_outputs/semantic_source_non_v10_wave2_selected_margin_policy_sweep_latest.md`
- `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave2_selected_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.md`
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md`
- `docs/test_outputs/semantic_non_v10_source_support_conversion_wave4_anypos_supported_probe_latest.md`
- `docs/test_outputs/semantic_non_v10_source_support_conversion_wave3_anypos_latest.md`
- offline lane: `semantic_active_shadow`
- status: `ok` / `promotion_candidate`
- semantic source coverage: `19 / 19`
- phrase source coverage: `0 / 19`
- best full-`v10` ablation: `100.0%` accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains
- v2 held-out semantic validation: `100.0%` accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains over `38` active/shadow cases across all `19` v10 families
- phrase/no-winner held-out validation: v1 passes over `19` phrase cases after a general subject-trigger-object preemption fixed the verb-frame `match` miss; v2 broadens to `38` phrase cases and passes with a separate `min_margin=0.005` phrase-policy candidate lane after the zero-margin lane exposed one near-tie `on board` harmful replacement
- phrase challenge validation: a fresh independent `19`-case no-winner suite first exposed two harmful replacements, `ball:001` (`keep the ball rolling`) and `file:001` (`Customers file past...`); the current phrase-pattern repair passes that suite at `min_margin=0.005` with `0` harmful replacements and `0` false abstains
- phrase stress validation: a second fresh `19`-case no-winner stress suite, added after the phrase-pattern repair, also passes at `min_margin=0.005` with `0` harmful replacements and `0` false abstains
- non-v10 phrase signal validation: a signal-only audit over `16` non-v10 phrase/counterexample rows passes with `0` false positives and `0` false negatives; this screens phrase-pattern generalization before source evidence exists for those families
- non-v10 source-backed validation: the first WordNet definition-preferred probe covers `8 / 8` non-v10 active/shadow families, admits `18 / 18` rows after leakage and sense-discrimination gates, and passes a `16`-case held-out slice at `100.0%` decision accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains
- non-v10 failure-class mining: the current mining report is `review` / `seed_pass_expand_inventory` with `0` blocking semantic-promotion classes, but medium manual-overfit risk; it explicitly tracks the remaining seed-ablation false abstains (`rock`, `point`, `date`), phrase-contract gap, and breadth gap (`42` more families / `184` more cases at the current broad-confidence thresholds)
- non-v10 inventory candidates: the automatic WordNet-backed inventory report emits `75` ranked ambiguous headwords after excluding current v10 and seed non-v10 triggers; this is a candidate-selection surface only, because Spanish active/shadow target-family construction still has to happen before source admission
- non-v10 automatic wave control: the first source-supported Spanish active/shadow wave selects draft families from local Wiktionary, reverse Wiktionary, FreeDict, and WordNet link evidence. A fixed-eight sweep reaches `7 / 8` semantic-complete families, but the pool-first sweep is stronger: with a `16` requested pool and `8` family selection target, it finds `9` semantic-complete families and materializes an `8`-family admission-selected draft wave. The selected wave has active/shadow semantic coverage `8 / 8`, `30` final admitted rows, `0` leakage rejects, and clean selected-wave held-out validation: `16` active/shadow cases plus `8` phrase/no-winner cases both pass with `0` harmful replacements and `0` false abstains. It remains analysis-only because the automatic wave's seed cases are loader scaffolds excluded from promotion ablation, phrase source coverage is `0 / 8`, and the breadth proof is still only `8` families / `24` selected-wave held-out cases.
- non-v10 selected-wave failure-class mining: `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave2_selected_latest.md` reports `review` / `seed_pass_expand_inventory` with `0` blocking semantic-promotion classes. The tracked residuals are sense-filter rejects, phrase-contract gap, and breadth (`42` more families / `176` more cases at the current broad-confidence thresholds), so the next useful move is more automatic breadth rather than tuning this small slice.
- non-v10 wave32/wave64 supported breadth probe: `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_latest.md` broadens family construction from the original noun/verb shape to `any_cross_pos`; `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.md` confirms that asking for a larger supported pool still does not find additional constructor-supported families. With reverse Wiktionary or FreeDict support still required, the latest supported lane is `ok` / `semantic_complete_source_portfolio_found`: the best single source variant reaches `15 / 16`, while the source portfolio reaches `17` supported semantic-complete families and materializes a `16`-family portfolio-selected dataset/queue. This came from two general source-method changes, not family patches: weak WordNet links now retain the source sense-order prior, and source extraction can use a broader candidate slate than the conservative family-construction threshold.
- non-v10 source-support audits: `docs/test_outputs/semantic_non_v10_source_support_conversion_wave4_anypos_supported_probe_latest.md` verifies that the supported probe's selected `16` families have `36 / 36` translation-supported senses. `docs/test_outputs/semantic_non_v10_source_support_conversion_wave3_anypos_latest.md` verifies the forward-only upper-bound selected wave is not source-supported yet: only `3 / 16` selected families are fully supported, one unsupported row has a non-duplicate same-POS supported alternative, and `12 / 16` families still need reviewed or reverse-side source support.
- non-v10 wave32 source-support upper bound: `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md` allows forward-only translations to test whether source support is the bottleneck. It reaches `ok` / `semantic_complete_variant_found`, with `32` constructed families, `31 / 32` semantic-complete families, `111` final admitted rows, and a materialized `16`-family control dataset tagged `forward_only_upper_bound`. This is a design signal only, not promotion evidence, until those families gain reverse/reviewed source support plus held-out validation.
- margin sweep result: after adding phrase stress v1, `min_margin=0.005` remains the smallest currently passing margin across active/shadow v2, phrase v1, phrase v2, phrase challenge v1, phrase stress v1, and full-`v10`; this is a current-suite candidate, not independent proof that phrase policy is solved

## Why This Exists

The current result changes the question.

Before this result, the main uncertainty was whether source coverage could close the
semantic-veto quality gap at all. The current admitted composite shows that a
reproducible external-source path can close the full known `v10` semantic lane.

The new uncertainty is whether the pattern generalizes across en-es without
becoming benchmark-shaped, runtime-heavy, or phrase-policy-confused.

This document is an idea ledger, not a commitment list. It intentionally includes
aggressive and speculative directions so they are not lost.

## Current Result To Preserve

The current winning source shape is:

1. Reverse auxiliary text as the broad no-spend source floor.
2. Local English WordNet JSON for broad active/shadow example-frame coverage.
3. Raw Wiktextract examples for residual same-POS hard cases.
4. Active-side WordNet related-hyponym rows for same-POS living-plant breadth
   and deeper biology-cell coverage, with shadow-side related expansion kept
   out of the promoted lane after it over-weighted industrial-plant evidence.
5. Source-admission cycle:
   - leakage and duplicate audit before merge
   - final-composite sense admission after merge
   - split semantic vs phrase contract
   - downstream ablation before promotion status
6. Prototype-style active/shadow competition with surface-POS rescue/preemption,
   narrowed so modified noun frames like `comedy play opened` are not treated as
   verb-frame shadows.

The current non-runtime blockers are:

- runtime phrase-source policy
- runtime packaging feasibility for sentence-transformer plus evidence assets
- broader held-out breadth beyond the current active/shadow v2 validation
- broader non-v10 inventory breadth before treating the first source-backed seed wave as general en-es evidence
- decision-rule proof: the current active-minus-strongest-shadow rule is the
  control, but `docs/rulegen/semantic_decision_rule_comparison_plan.md` now
  tracks the need to test context representation, source representation,
  similarity scoring, aggregation, and final classification separately.

## Direction 1. Preserve And Lock The Win

Goal: make the current result hard to lose accidentally.

Ideas:

- Give the exact composite a stable lane name and artifact manifest.
- Add a compact regression fixture that asserts:
  - `0` leakage rejects
  - `0` final sense rejects
  - semantic coverage `19 / 19`
  - `0` harmful replacements
  - `0` false abstains
- Keep reverse-aux, WordNet, and Wiktextract component rows separable in reports.
- Add source leave-one-out regression reports so future work sees which source
  family is carrying which cases.
- Preserve rejected rows and rejection reasons as first-class regression data.
- Add a small source-admission summary command for this lane, similar to existing
  rulegen summary commands.
- Add a promotion-candidate manifest that records the exact source batch ids,
  source adapter versions, scorer ids, thresholds, and policy blockers.

First useful implementation:

- Landed: `scripts/testing/semantic_source_reference_lane_en_es.py` validates
  `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json`
  against the frozen source-cycle artifact, held-out artifact, and admitted
  evidence batch.
- Current report:
  `docs/test_outputs/semantic_source_reference_lane_latest.md` is `ok` /
  `reference_lane_frozen` with `59` passing checks and `0` failures, including
  the active/shadow lane and the separate phrase-policy candidate lane.
- Margin sweep:
  `docs/test_outputs/semantic_source_margin_policy_sweep_latest.md` is `ok` /
  `margin_candidate_found` after the phrase-pattern repair, recommends
  `min_margin=0.005`, and records `0.005` through `0.01` as the current
  passing window.

Next useful implementation:

- Keep the reference lane fixed while adding phrase-sensitive and non-v10
  held-out rows; do not treat the active/shadow v2 pass as runtime breadth.

## Direction 2. Prove Generalization

Goal: determine whether the source-admission pattern survives outside the known
full-`v10` suite.

Ideas:

- Build held-out en-es semantic-veto families that were not part of the source
  iteration loop.
- Add non-benchmark active/shadow sentences for existing families.
- Add adversarial same-POS families like living-plant vs industrial-plant.
- Add cross-POS families like noun/verb `check`, `play`, `watch`, and `report`.
- Add target-side ambiguity cases where Spanish replacements have competing
  target senses.
- Add phrase-sensitive held-out rows separately so phrase policy is not mixed
  into semantic-source validation.
- Add real-text smoke corpora:
  - short web/article snippets
  - dictionary-example snippets
  - user-like prose snippets
  - compact synthetic paragraphs with multiple ambiguous triggers
- Run source blindfold tests:
  - hold out a family while building source evidence
  - hold out one source family, such as Wiktextract, and see what breaks
  - hide known residual labels and let the adapter discover them
- Run time/version splits if external source dumps get versioned.
- Track confidence intervals by family cluster, POS shape, and source family.

First useful implementation:

- Landed: `scripts/testing/semantic_source_heldout_validation_en_es.py`
  consumes the admitted composite and now evaluates
  `docs/test_inputs/semantic_routing_cases/en_es_source_heldout_cases_v2.json`
  across all `19` v10 families. The v1 seed exposed surface-POS
  over-preemption and a plant active-source gap; v2 exposed an irregular
  `play won` noun-frame miss and a shallow `cell` source-depth miss. The current
  clean lane passes v2 at `100.0%` / `100.0%` / `0` / `0`.
- Landed: `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_heldout_cases_v1.json`
  adds a separate phrase/no-winner slice across the same `19` families without
  changing the active/shadow reference. Its first run exposed one harmful
  replacement, `match:001`; the accepted general subject-trigger-object phrase
  preemption now passes the phrase slice while leaving active/shadow v2 clean.
- Landed: `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_heldout_cases_v2.json`
  doubles the phrase/no-winner slice to `38` cases. The zero-margin lane exposed
  one harmful `on board` replacement where active beat shadow by only `0.0014`;
  the separate `min_margin=0.005` candidate lane passes phrase v2 while keeping
  active/shadow v2 and full-`v10` ablation clean.
- Landed: `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_challenge_cases_v1.json`
  adds a fresh independent no-winner phrase challenge across the same `19`
  families. Its first `min_margin=0.005` run caught two non-near-tie harmful
  replacements: `ball:001` (`keep the ball rolling`) and `file:001`
  (`Customers file past...`). The current phrase-pattern repair passes the
  suite with `0` harmful replacements and `0` false abstains, while preserving
  active/shadow v2 and full-`v10`.
- Landed: `docs/test_inputs/semantic_routing_cases/en_es_source_phrase_stress_cases_v1.json`
  adds a second fresh no-winner stress suite after the phrase-pattern repair.
  It passes at `min_margin=0.005` with `0` harmful replacements and `0` false
  abstains, giving the repair one independent post-fix stress read.
- Landed: `scripts/testing/semantic_phrase_policy_signal_audit_en_es.py`
  audits phrase-pattern signal firing without source evidence or semantic
  scoring. The first non-v10 suite,
  `docs/test_inputs/semantic_routing_cases/en_es_phrase_policy_signal_non_v10_v1.json`,
  passes `16 / 16` rows with `0` false positives and `0` false negatives.
- Landed: `docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_probe_v1.json`
  and `docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_heldout_cases_v1.json`
  move the first `8` non-v10 ambiguous heads from signal-only screening into
  source-backed active/shadow validation. Definition-preferred WordNet evidence
  admits all `18` active/shadow rows, and
  `docs/test_outputs/semantic_source_non_v10_heldout_v1_margin005_validation_latest.md`
  passes all `16` held-out decisions with `0` harmful replacements and `0`
  false abstains. The first held-out run caught one real mixed-shadow bug
  (`violin case` was over-rescued); the accepted fix blocks active-noun rescue
  when the strongest shadow is noun-like even if another verb shadow exists.
- Landed: `scripts/testing/semantic_source_margin_policy_sweep_en_es.py`
  sweeps candidate margins across active/shadow v2, phrase v1, phrase v2,
  phrase challenge v1, phrase stress v1, and the full-`v10` source ablation.
  The current run recommends `0.005`: lower margins keep the phrase v2
  `on board` harmful replacement, while `0.02+` creates active false abstains
  in held-out and full-`v10` rows.
- Landed: `scripts/testing/semantic_source_failure_class_mining_en_es.py`
  consumes the current non-v10 source admission, held-out validation,
  source-mode comparator, source extraction reports, and margin sweep without
  new spend. The current report has no blocking semantic-promotion failure
  class, but keeps the result at `review` / `seed_pass_expand_inventory`
  because the seed wave is small and the remaining residuals are now explicit:
  seed-ablation false abstains, phrase-contract absence, and inventory breadth.
- Landed: `scripts/testing/semantic_non_v10_wave_builder_en_es.py` creates the
  first automatic non-v10 family-construction path after the hand-seeded proof.
  The builder
  constructs draft Spanish active/shadow families from local Wiktionary,
  reverse Wiktionary, FreeDict, and WordNet-link evidence, and rejects
  same-visible-target active/shadow pairs so the UX remains binary.
- Landed: `scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py`
  runs the no-spend constructor/extraction/admission grid instead of trusting
  one hand-picked setting. The fixed-size control exposes a reusable gap
  (`end:fin`), while the pool-first run with `--wave-size 16 --selection-size 8`
  finds enough semantic-complete families to materialize an `8 / 8`
  admission-selected draft wave without hand-patching `end`.

Next useful implementation:

- Treat the `any_cross_pos` supported/upper-bound pair as the next control: the
  supported lane now has a `16`-family semantic source portfolio without using
  unsupported translations, while the forward-only upper-bound lane still shows
  the likely gain from better source support. The next generalization step is to
  materialize the supported portfolio evidence as one admitted batch, carry the
  active/shadow plus phrase held-out harness onto that broader selected wave,
  then convert upper-bound selected families into reverse-supported or reviewed
  source-backed rows.

## Direction 3. Scale Source Coverage Across en-es

Goal: move from `19` known families to a broad en-es ambiguous-headword inventory.

Ideas:

- Build an en-es ambiguity inventory from:
  - current rulegen candidate inventory
  - existing semantic-veto families
  - high-frequency English headwords
  - current replacement logs or local debug observations, if available
  - dictionary polysemy metadata
- Rank families by:
  - user-facing frequency
  - replacement risk
  - same-POS ambiguity
  - cross-POS ambiguity
  - phrase/idiom risk
  - source availability
  - observed false-abstain or harmful-replace risk
- Add per-family state:
  - not inventoried
  - no source
  - active-only source
  - shadow-only source
  - active/shadow complete
  - admitted
  - held-out passed
  - runtime-publishable
- Run no-spend source sweeps over the ranked inventory before any LLM generation.
- Promote by family wave rather than one giant en-es switch.

First useful implementation:

- Landed: `scripts/testing/semantic_non_v10_inventory_candidates_en_es.py`
  builds the first automatic no-spend candidate queue from local English
  WordNet, excluding the current v10 and non-v10 seed triggers. It ranks
  candidate headwords by cross-POS ambiguity, same-POS polysemy, and source
  availability, while explicitly stopping short of claiming Spanish
  active/shadow target construction.
- Next: add a source-coverage inventory command that reports active/shadow/phrase
  coverage for every selected en-es family candidate after target-family
  construction.

## Direction 4. Source Adapter Expansion

Goal: make the current external-source success reproducible at larger scale.

### Reverse Auxiliary Text

Ideas:

- Extend all-dataset reverse-aux extraction to broader en-es inventories.
- Improve reverse-aux role assignment when active and shadow text both exist.
- Use reverse-aux as the default source floor and residual router.
- Track which reverse-aux rows are sense-ambiguous and why.
- Compare reverse-aux labels, examples, glosses, and auxiliary forms separately.

### WordNet And Sense Graphs

Ideas:

- Keep entry sentence frames preferred over generic synset examples when they are
  more frame-like.
- Preserve WordNet sense order as a source prior for weak lexical links; do not
  let one generic overlap token outrank a high-priority sense by itself.
- Compare WordNet modes:
  - entry sentence preferred
  - example preferred
  - definition preferred
  - definition plus example
- Keep family-construction thresholds separate from extraction thresholds so a
  conservative family pool can still expose a broader source slate to admission.
- Use WordNet graph features:
  - synonyms
  - hypernyms
  - derivationally related forms
  - verb frames
  - similar-to pointers
- Add Open Multilingual WordNet or Spanish WordNet style target-side checks where
  local data exists.
- Use graph distance as a source-confidence feature, not as an automatic admit.

### Raw Wiktextract / Wiktionary / Kaikki

Ideas:

- Expand raw Wiktextract example mining beyond residual `plant`.
- Extract gloss examples, usage examples, labels, qualifiers, topics, and sense
  tags separately.
- Use Spanish-side Wiktionary/Wikcionario only as target-side corroboration until
  the linking quality is proven.
- Compare raw Wiktextract with converted Kaikki/Wiktionary SQLite packs to find
  conversion losses.
- Add early-stop and trigger-block indexing so broad scans are cheap.
- Add licensing/provenance summaries before anything becomes runtime-publishable.

### Bilingual Dictionaries And Translation Tables

Ideas:

- Use FreeDict sense notes, examples, and labels where available.
- Use Kaikki translation tables for target-side corroboration.
- Use aligned phrase or translation tables for phrase-sensitive families.
- Compare bilingual source rows against monolingual English examples to detect
  target-side mismatches.
- Keep dictionary examples separate from dictionary glosses in ablations.

### Corpus Retrieval

Ideas:

- Build local retrieval over licensed/example corpora.
- Retrieve real sentences by trigger and source-sense hints.
- Use retrieval only as provisional source rows until leakage and sense admission
  pass.
- Add hard-negative retrieval for same-POS shadow cases.
- Add source-document provenance and sentence offsets for auditability.
- Consider build-time retrieval first; runtime retrieval should be a later and
  separately gated design.

### LLM Source Generation

Ideas:

- Use generation as a coverage accelerator, not as direct truth.
- Generate multi-candidate active/shadow rows for missing slots.
- Generate adversarial hard negatives for same-POS shadows.
- Generate phrase-control rows only for containment or separately gated abstain
  evidence, not broad semantic competition.
- Require explicit request-count, cost, leakage, duplicate, and sense-admission
  gates for every live run.
- Prefer source-backed prompts that ask the model to transform or diversify
  admitted source examples instead of inventing benchmark-shaped sentences.
- Keep generated rows `runtime_publishable=false` until a separate publication
  policy exists.

## Direction 5. Admission Hardening

Goal: make source quality improve as scale increases instead of relying on manual
inspection.

Ideas:

- Keep candidate acceptance, leakage-kept, sense-admitted, and downstream-admitted
  counts separate.
- Add paraphrase-level leakage checks beyond token spans and canonical pronoun
  rewrites.
- Add benchmark-shape detection for generated examples.
- Add source-family duplicate detection across adapters.
- Add source confidence features:
  - source family
  - evidence kind
  - link score
  - overlap tokens
  - POS agreement
  - example-vs-definition provenance
  - graph distance
- Compare sense-admission scorers:
  - lexical overlap
  - TF-IDF
  - sentence-transformer
  - cross-encoder reranker, if later added
  - abstain-biased tiny reranker, if later added
- Add per-source rejection dashboards.
- Track admitted row age and source dump version.
- Promote row families only when source evidence survives ablation, not when
  structural coverage alone is complete.

## Direction 6. Algorithm And Scorer Variants

Goal: avoid assuming the current active/shadow prototype shape is the final best
algorithm.

Ideas:

- Keep active-vs-shadow prototype competition as the current best offline lane.
- Compare source text as:
  - prototypes
  - appended evidence
  - retrieved top-k examples
  - aggregated sense centroids
  - source-weighted evidence bundles
- Learn or tune source weights by source family and POS shape.
- Add hard-negative mining from admitted shadow rows.
- Add calibrated margins once held-out breadth is large enough.
- Add abstain-biased second opinion gates for borderline cases:
  - can add abstain
  - cannot authorize replacement
- Compare deterministic surface-POS guards with learned syntax features.
- Test whether phrase containment should be an independent pre-gate, a post-gate,
  or only a local containment pattern.
- Test a no-phrase semantic lane as the default offline promotion path while
  phrase remains runtime-policy gated.
- Keep lexical and TF-IDF lanes as negative controls so sentence-transformer gains
  are not accepted blindly.

## Direction 7. Phrase And Idiom Path

Goal: handle phrase risk without polluting ordinary semantic competition.

Ideas:

- Build phrase-control source adapters instead of broad phrase prototypes.
- Mine phrasal verbs and idioms from Wiktextract/Wiktionary examples.
- Use aligned phrase tables for multiword expression risk.
- Build phrase held-out suites:
  - phrasal verbs
  - idioms
  - support-verb constructions
  - lexicalized expressions
  - trigger words inside named entities
- Test containment-only phrase scoring at larger scale.
- Track false abstains caused by phrase overreach separately from semantic false
  abstains.
- Decide whether phrase coverage is required for runtime publication or only for
  phrase-risk families.
- Keep phrase rows out of broad active/shadow semantic competition unless an
  ablation explicitly proves they are safe.

## Direction 8. Runtime Capture

Goal: convert an offline source win into product behavior without importing the
entire research stack into runtime.

Ideas:

- Package admitted source rows into compact semantic evidence packs.
- Precompute embeddings for active/shadow prototypes.
- Keep runtime UX binary:
  - replace
  - abstain
- Add capability gates:
  - sentence-transformer available
  - evidence pack available
  - phrase policy available
  - fallback lane available
- Define fallback behavior when sentence-transformer assets are missing.
- Measure latency and memory with realistic page text.
- Decide whether source rows can ever become `runtime_publishable=true`, or
  whether runtime only receives distilled derived evidence.
- Keep debug output able to explain:
  - active score
  - shadow score
  - phrase preemption
  - source family that contributed the winning evidence
  - fallback reason
- Do not expose internal soft states in the UI unless product policy changes.

## Direction 9. No-Spend Sweep Harnesses

Goal: search broadly without paying for generation or changing runtime.

Ideas:

- Sweep source combinations:
  - reverse aux
  - WordNet
  - Wiktextract
  - Kaikki/Wiktionary
  - dictionary examples
  - corpus retrieval
  - composite source lanes
- Sweep admission thresholds by source family.
- Sweep scorer choices and decision shapes.
- Sweep source leave-one-out and source add-one-at-a-time.
- Automatically extract unexpected wins and regressions.
- Report by family, POS shape, source family, and failure class.
- Make the harness able to discover improvements that do not match current
  assumptions.

First useful implementation:

- Landed: `scripts/testing/semantic_source_failure_class_mining_en_es.py`
  is the first anti-handcrafting sweep surface. It does not generate new
  source rows; it makes the existing source/held-out/admission evidence
  falsifiable by classifying blockers, residuals, comparator deltas, and the
  manual-overfit boundary in one artifact.
- Landed: `scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py`
  is the first automatic-wave sweep surface. It changes source-construction
  assumptions and evidence modes at the wave level, then ranks them by admitted
  semantic contract coverage instead of by intuition or one-off family fixes.

## Direction 10. Test Suite Expansion

Goal: make quality scale with the risk of the new source path.

Ideas:

- Add unit tests for each source adapter:
  - missing local resource
  - fixture source rows
  - active/shadow linking
  - phrase absence
  - provenance fields
- Add integration tests for the source-admission cycle policy split.
- Add golden tests for the current promotion-candidate lane.
- Add held-out fixture tests separate from the known `v10` benchmark.
- Add mutation tests:
  - near-copy benchmark leakage
  - wrong-sense example
  - same-POS active/shadow ambiguity
  - phrase overreach
  - source duplicate across adapters
- Add artifact-schema tests so generated JSON remains stable.
- Add quality-summary tests so handoff commands do not drift from the canonical
  cycle.

## Direction 11. Governance, Docs, And Source Safety

Goal: keep the expanding source program auditable.

Ideas:

- Keep every source family in `docs/test_inputs/semantic_shadow_source_registry.json`.
- Add source-family lifecycle states:
  - proposed
  - implemented
  - admitted
  - promotion-candidate
  - held-out-passed
  - runtime-publishable
  - rejected
- Keep licensing/provenance notes close to source adapters.
- Update `docs/developer/feature_state_matrix.md` only when behavior or evidence
  state materially changes.
- Preserve known contradictions instead of silently marking docs as shipped.
- Keep generated artifacts in stable names for latest handoff plus immutable
  names for important runs.
- Branch broad source-ingestion churn separately once it becomes noisy.

## Direction 12. More Fundamental Product Options

Goal: remain open to changing assumptions if the source win exposes a better
architecture.

Ideas:

- Build a dedicated semantic-evidence pack generator instead of treating source
  adapters as testing-only utilities.
- Move semantic veto toward build-time retrieval and distilled runtime evidence.
- Keep runtime semantic routing conservative and let offline source admission do
  the heavy lifting.
- Introduce an abstain-only local reranker for risky borderline cases.
- Consider per-family strategy selection:
  - lexical enough
  - source prototypes required
  - phrase pre-gate required
  - runtime disabled until better evidence
- Use feedback loops to request new source evidence for observed runtime misses.
- Treat source coverage as an ongoing data product, not a one-time algorithm fix.

## Immediate Recommended Sequence

1. Keep the current promotion-candidate composite frozen as a named reference
   lane through `docs/test_inputs/semantic_routing/semantic_source_reference_lane_en_es_v1.json`.
2. Treat the new phrase-pattern repair as a candidate, not a settled policy:
   stress it on non-v10 rows without tuning the active/shadow reference lane.
3. Use `docs/test_outputs/semantic_source_failure_class_mining_latest.md` as
   the control surface for deciding whether new source work is broadening or
   handcrafting.
4. Expand held-out validation beyond the current active/shadow v2, phrase
   challenge, phrase stress, and first source-backed non-v10 slices without
   tuning on those slices; rerun the margin sweep after each expansion.
5. Add an en-es source-coverage inventory over broader ambiguous families.
6. Run no-spend source sweeps across reverse-aux, WordNet, Wiktextract, and any
   available Kaikki/Wiktionary source surfaces.
7. Expand tests around source-cycle policy, held-out validation, and
   failure-class mining.
8. Only after broader held-out breadth is convincing, audit runtime packaging and
   phrase-source policy for publication.

## Parking Lot

These ideas are deliberately not ordered yet:

- target-side Spanish sense graph corroboration
- cross-encoder sense-admission reranker
- local abstain-only tiny model
- runtime shadow logging for future source requests
- phrase-specific source adapter from phrasal verb inventories
- family-level source strategy selection
- source confidence dashboards
- build-time retrieval over local corpora
- automatic source residual planner
- source dump versioning and drift checks
- non-English target expansion after en-es proves the pattern
