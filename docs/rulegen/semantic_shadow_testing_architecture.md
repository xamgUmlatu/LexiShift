# Semantic Shadow Testing Architecture

Status: active workflow
Role: Runbook / operational
Purpose: keep semantic-shadow research testing repeatable, sweepable, and comparable as the workstream continues
Last updated: 2026-04-11
Last verified: 2026-04-11 targeted semantic-shadow scoring tests plus Campaign C matrix run, experiment-row compare, explicit forward-pack override replay against a rebuilt Kaikki forward artifact, and canonical en-es rulegen audit
Source-of-truth: current semantic-shadow testing workflow; implementation truth lives in the scripts and core scoring modules referenced below

## Why this exists

Semantic-shadow testing is no longer one question.

It now has several distinct questions:

- does the seed-admission path surface the blocker at all,
- does the mined candidate pool contain the right competitor,
- does promotion keep the blocker while dropping the junk,
- does the resulting blocker set actually improve veto behavior,
- and which node caused a miss when the answer is no.

Running those questions through one-off scripts is no longer sufficient.
The testing surface now needs to behave like infrastructure.

## Testing layers

Use these layers deliberately and keep them separate.

### 1. Deterministic scoring tests

Purpose:
- prove that scoring-node semantics are stable,
- prove that node-weight overrides do what the experiment says they do.

Primary files:
- `core/lexishift_core/rulegen/semantic_shadow_support.py`
- `core/lexishift_core/rulegen/semantic_shadow_trigger_support.py`
- `core/tests/rulegen/test_semantic_shadow_inventory.py`
- `core/tests/rulegen/test_semantic_shadow_evaluation.py`

### 2. Gold-proxy overlap tests

Purpose:
- measure direct overlap between mined/promoted shadows and the current lower-bound reviewed overlap gold.

Primary files:
- `scripts/testing/semantic_shadow_gold_proxy_en_es.py`
- `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`

Key metrics:
- candidate precision
- candidate recall
- gold-trigger hit rate
- overblocking rate

### 3. Veto-proxy tests

Purpose:
- measure whether a shadow source is sufficient to drive abstention on ambiguous rows.

Primary files:
- `scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py`
- `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`

Key metrics:
- overall accuracy
- abstain recall
- harmful allow rate
- overblocking rate
- harmful-allow miss classification (`seed_missing`, `candidate_missing`, `promotion_miss`)

### 4. Matrix experiments

Purpose:
- compare early-node and late-node combinations in one run,
- keep experiment definitions in data rather than in new scripts,
- make future ablations additive rather than bespoke.

Primary files:
- `scripts/testing/semantic_shadow_experiment_support.py`
- `scripts/testing/semantic_shadow_experiment_matrix_en_es.py`
- `docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json`

### 5. Promotion-gap diagnostics

Purpose:
- explain why good mined blockers still fail promotion under the current threshold
- separate `promotion_miss` from `candidate_missing` with score-aware evidence
- show whether the next frontier is new promotion evidence or new candidate generation

Primary files:
- `scripts/testing/semantic_shadow_promotion_gap_en_es.py`
- `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`

### 6. Row-to-row frontier compare

Purpose:
- quantify whether a promising candidate row is still buying real progress versus the current control
- show exact row-level fixes and regressions rather than relying on sampled rows
- expose where gains are concentrated so we can tell whether the frontier is broad or narrowing
- expose automatic feature-bucket risk regions so we can see which upstream case shapes still dominate `harmful_allow` or `false_abstain`

Primary files:
- `scripts/testing/semantic_shadow_experiment_compare_en_es.py`
- `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md`

### 7. Source-intake campaigns

Purpose:
- prepare broad source-heavy experiments without letting them sprawl directly into runtime policy
- keep approval state, source role, and provenance explicit before new families land in code
- make future source-family ablations first-class instead of one-off notes in commit messages

Primary files:
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
- `docs/test_inputs/semantic_shadow_source_registry.json`

Key discipline:
- source intake should widen the offline evidence warehouse, not the runtime contract
- each new source family should be evaluated separately for coverage gain vs discrimination gain
- external or silver sources should stay explicit until they survive ablation against the lexical control

## Current experiment contract

The matrix runner accepts one manifest row per experiment.
Each row is a fully specified configuration.

Current sweepable inputs:

- `seed_mode`
- `forward_seed_max_words` (manifest-global for the current runner)
- `trigger_support_score_min`
- `trigger_support_weights`
- `policy`
- `support_score_min`
- `support_score_max_promoted`
- `shadow_support_weights`
- `support_frequency_representative_bonus`
- `support_frequency_representative_top_k`
- `support_frequency_similarity_weight`
- `support_frequency_similarity_tau`
- `semantic_bridge_include_aux_text`
- `semantic_bridge_include_examples`
- `support_representative_pruning_mode`

The important design decision is that node weights are now first-class experiment inputs.
That means future testing can ablate or soften a node by configuration instead of code edits.

Current matrix outputs should expose the row-local evidence needed to explain a result:

- explicit trigger-support and shadow-support weight overrides
- sample harmful-allow rows for underblocking review
- sample false-abstain rows for overblocking review
- trigger-filter drop examples when a trigger threshold is active

## Node Map

Treat the algorithm as four separable layers.

### A. Seed-admission nodes

These determine whether a target/trigger pair enters the mining path at all.

Current sweepable seed-admission nodes:

- `seed_mode`
- `forward_seed_max_words`
- `trigger_support_score_min`
- `trigger_support_weights.rulegen_top3_source`
- `trigger_support_weights.rulegen_all_source`
- `trigger_support_weights.forward_gloss_fragment`
- `trigger_support_weights.multi_source_support`
- `trigger_support_weights.active_side_support`
- `trigger_support_weights.reverse_shadow_support`
- `trigger_support_weights.multi_word_penalty`

### B. Candidate-source nodes

These determine which shadow candidates are introduced upstream of promotion.

Current main candidate-source lanes:

- reverse lookup candidates
- forward-index supplement
- lexical semantic-bridge candidates
- neighbor-borrowed trigger seeds

These are not all weighted equally yet.
Some are still discrete lane choices rather than pure numeric knobs.

### C. Promotion / condensation nodes

These determine which mined candidates survive into the blocker set.

Current sweepable promotion nodes:

- `support_score_min`
- `support_score_max_promoted`
- `shadow_support_weights.reviewed_trigger_support`
- `shadow_support_weights.forward_trigger_support`
- `shadow_support_weights.benchmark_target_present`
- `shadow_support_weights.same_pos_as_active`
- `shadow_support_weights.active_side_support`
- `shadow_support_weights.active_profile_support`
- `shadow_support_weights.semantic_bridge_support`
- `shadow_support_weights.multi_source_candidate_support`
- `shadow_support_weights.cross_pos_mismatch_penalty`
- `support_frequency_representative_bonus`
- `support_frequency_representative_top_k`
- `support_frequency_similarity_weight`
- `support_frequency_similarity_tau`
- `support_representative_pruning_mode`

### D. Evaluation nodes

These do not change the mined blockers themselves.
They define how we judge movement.

Current evaluation surfaces:

- direct gold-proxy overlap
- veto proxy
- harmful-allow miss classification
- benchmark slice metadata

## Rigorous Sweep Program

Use the sweep program in stages.
Do not jump directly to large Cartesian matrices.

### Stage 0. Freeze controls

Before any campaign:

- freeze the benchmark dataset version for the campaign
- keep one manifest and one output lane for the campaign
- include the same controls in every run

Required controls:

- `reviewed_auto_control`
- `source_only_baseline`
- `source_only_borrowed`
- `no_shadows` in the veto comparison lane
- `curated_shadows` in the veto comparison lane

Comparability rule:

- if benchmark labels, slice metadata, or policy semantics change materially, start a new campaign instead of comparing across runs casually

### Stage 1. Single-node ablations

Goal:
- prove whether a node is helping, inert, or harmful before testing interactions

Method:

- hold everything else at the control baseline
- run one-node sweeps only
- prefer a small ladder over a giant grid

Recommended early-node ladder:

- threshold: `trigger_support_score_min in {0, 2, 3, 4}`
- positive weights: `{0.0, 0.5x, 1.0x, 1.5x}`
- penalties: `{0.0, baseline, stronger-than-baseline}`

Recommended late-node ladder:

- threshold: `support_score_min in {4, 5, 6}`
- `support_score_max_promoted in {1, 2, 3}`
- positive weights:
  - `reviewed_trigger_support in {1.0, 2.0, 3.0}`
  - `forward_trigger_support in {0.0, 0.25, 0.5, 0.75, 1.0}`
  - `benchmark_target_present in {0.0, 0.5, 1.0, 1.5}`
  - `same_pos_as_active in {0.0, 0.5, 1.0, 1.5}`
  - `active_side_support in {0.0, 0.5, 1.0, 1.5}`
  - `active_profile_support in {0.0, 0.5, 1.0, 1.5}`
  - `semantic_bridge_support in {0.0, 0.5, 1.0, 1.5}`
- penalty:
  - `cross_pos_mismatch_penalty in {-2.0, -1.0, 0.0}`

Interpretation rule:

- a node is `necessary` if zeroing it clearly hurts the targeted frontier
- a node is `harmful` if zeroing it improves the targeted frontier without causing obvious regression elsewhere
- a node is `inert` if the ladder is effectively flat on both gold and veto surfaces

### Stage 2. Ridge sweeps

Goal:
- find the viable numeric range after single-node ablations narrow the field

Method:

- keep only the nodes that moved the frontier in Stage 1
- sweep thresholds jointly with 2-4 relevant weights
- still avoid full Cartesian search

Examples:

- seed-admission ridge:
  - `trigger_support_score_min`
  - `forward_gloss_fragment`
  - `multi_source_support`
  - `reverse_shadow_support`
- promotion ridge:
  - `support_score_min`
  - `forward_trigger_support`
  - `benchmark_target_present`
  - `semantic_bridge_support`

### Stage 3. Interaction sweeps

Goal:
- test whether the best improvements depend on each other

Method:

- select the top 2-3 early nodes and top 2-4 late nodes from earlier stages
- run only pairwise or small interaction sweeps
- rank results by Pareto dominance, not by one scalar

Primary interaction questions:

- does loosening early admission require stricter later promotion
- does stronger `semantic_bridge_support` only help when `benchmark_target_present` is softened
- does neighbor-borrow help only when promotion keeps a slightly wider set

### Stage 4. Frontier campaigns

Run campaigns by miss type rather than by vague “quality”.

#### Frontier 1. Seed coverage

Question:
- how do we reduce `seed_missing`

Primary metrics:

- `harmful_allow_miss_counts.seed_missing`
- `gold_trigger_inventory_coverage_rate`
- `candidate_pool_trigger_recall`

Guardrails:

- `veto_overblocking_rate`
- `gold_candidate_precision`

Candidate levers:

- seed mode
- trigger-support threshold
- upstream trigger-support weights
- neighbor-borrow on/off

#### Frontier 2. Promotion quality

Question:
- how do we reduce `promotion_miss`

Primary metrics:

- `harmful_allow_miss_counts.promotion_miss`
- `veto_abstain_recall`
- `gold_candidate_precision`

Guardrails:

- `veto_overblocking_rate`
- `gold_candidate_recall`

Candidate levers:

- `support_score_min`
- `support_score_max_promoted`
- late support weights
- cross-POS penalty

#### Frontier 3. Candidate generation

Question:
- how do we reduce `candidate_missing`

Primary metrics:

- `harmful_allow_miss_counts.candidate_missing`
- `candidate_pool_trigger_recall`
- direct underblocked-row review

Guardrails:

- `gold_candidate_precision`
- `veto_harmful_allow_rate`

Candidate levers:

- lexical semantic bridge
- neighbor-borrow seed lane
- future explicit bridge lanes

Important note:

- `candidate_missing` can be sparse in sampled veto rows
- use direct gold-proxy underblocked rows and candidate-pool recall alongside the sampled miss counts

### Stage 5. Frontier freeze and benchmark expansion

Only expand benchmark scope after a frontier saturates.

A frontier is saturated when:

- the top rows become stable across repeated runs,
- single-node ablations stop producing clear positive movement,
- and remaining errors cluster into one narrower miss type

At that point:

- freeze the best config as the next control
- expand benchmark coverage in the weak families
- start a new campaign instead of continuing to optimize against the old denominator

## Initial Campaign Sequence

Run the first serious sweep as four explicit campaigns.
Each campaign should produce one saved matrix output and one short written conclusion.

### Campaign A. Early-node admission ablations

Goal:
- determine which upstream nodes are actually responsible for seed coverage movement

Baseline row:
- `source_only_baseline`

Add these rows first:

- `admission_threshold_0`
- `admission_threshold_2`
- `admission_threshold_3`
- `admission_threshold_4`
- `admission_forward_gloss_off`
- `admission_forward_gloss_half`
- `admission_forward_gloss_high`
- `admission_multi_source_off`
- `admission_multi_source_high`
- `admission_reverse_shadow_off`
- `admission_reverse_shadow_high`
- `admission_multiword_penalty_off`
- `admission_multiword_penalty_strong`
- `admission_neighbor_borrow_on`

Readout focus:

- `seed_missing`
- `gold_trigger_inventory_coverage_rate`
- `candidate_pool_trigger_recall`
- overblocking guardrails

Expected outcome:

- identify whether the frontier is still mostly upstream or whether upstream is already near saturation

### Campaign B. Late-node promotion ablations

Goal:
- determine whether misses are mostly caused by condensation rather than seed discovery

Baseline row:
- best row from Campaign A that does not regress guardrails materially

Add these rows first:

- `promotion_min_4`
- `promotion_min_5`
- `promotion_min_6`
- `promotion_top1`
- `promotion_top2`
- `promotion_top3`
- `promotion_forward_support_off`
- `promotion_forward_support_half`
- `promotion_forward_support_high`
- `promotion_same_pos_off`
- `promotion_same_pos_high`
- `promotion_active_profile_off`
- `promotion_active_profile_high`
- `promotion_semantic_bridge_off`
- `promotion_semantic_bridge_high`
- `promotion_cross_pos_penalty_off`
- `promotion_cross_pos_penalty_strong`

Readout focus:

- `promotion_miss`
- `veto_abstain_recall`
- `gold_candidate_precision`
- overblocking and recall guardrails

Expected outcome:

- identify which late nodes are real condensation signals and which are inert

### Campaign C. Ridge sweeps over winning nodes

Goal:
- map the viable numeric ranges instead of picking one arbitrary good point

Inputs:
- top 2-3 early nodes from Campaign A
- top 2-4 late nodes from Campaign B

Recommended ridge families:

- `ridge_seed_threshold_x_promotion_min`
- `ridge_seed_threshold_x_forward_support`
- `ridge_neighbor_borrow_x_promotion_topk`
- `ridge_same_pos_x_cross_pos_penalty`

Rule:

- keep each ridge to one threshold plus at most two weights at a time

Readout focus:

- Pareto-stable rows rather than one headline winner

Expected outcome:

- a short list of robust operating regions

### Campaign D. Interaction confirmation

Goal:
- confirm whether the best early and late improvements depend on each other

Add only pairwise confirmations:

- `interaction_borrow_x_forward_support`
- `interaction_borrow_x_cross_pos_penalty`
- `interaction_seed_threshold_x_promotion_min`
- `interaction_seed_threshold_x_same_pos`
- `interaction_semantic_bridge_x_benchmark_target`

Readout focus:

- whether a good node still helps when paired with the current best surrounding settings

Expected outcome:

- a control-quality config that is more defensible than any single lucky row

## Campaign Deliverables

Every completed campaign should leave behind:

- one matrix JSON artifact
- one matrix Markdown artifact
- one short conclusion note summarizing:
  - winning rows
  - losing rows
  - which nodes moved `seed_missing`
  - which nodes moved `promotion_miss`
  - whether the frontier appears viable or saturated

If a campaign does not change the frontier meaningfully, record that explicitly.
Flat results are information, not failure.

## Current Frontier Status

Current read after the first `en-es` Campaign A, Campaign B, and Campaign C runs:

- upstream expansion is still viable
- upstream pruning is not currently a productive frontier
- neighbor-borrowed triggers are the only clear early-node improvement so far
- trigger filtering tends to erase recall and remove the benefit created by borrowed seeds
- forward-gloss and reverse-shadow trigger support act mainly as permissive admission signals, not as strong positive selectors
- multi-source reward and multiword penalty are currently inert on the main gold and veto surfaces
- `support_score_min=5` remains the current Pareto point for late promotion
- `same_pos_as_active` is required, and `active_profile_support` matters as a backstop when active evidence is thin
- most current late-node weight sweeps are flat, which means the existing late-knob frontier is close to saturated
- current promotion misses cluster at support scores `3.0-4.0`, especially in `field_area_country` and `net_mesh_network`
- explicit `reverse_lookup + forward_index` source convergence is a viable new promotion feature family
- the current best promoted-feature row is the refined `multi_source_candidate_support=1.5` setting
- candidate generation is still incomplete, but the next primary frontier remains new discriminative promotion evidence rather than more resweeping of the current weights

Evidence:

- `docs/test_outputs/semantic_shadow_campaign_a_en_es_latest.md`
- `docs/test_outputs/semantic_shadow_campaign_b_en_es_latest.md`
- `docs/test_outputs/semantic_shadow_campaign_c_en_es_latest.md`
- `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md`
- `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`

Operational consequence:

- keep `source_only_borrowed` as the working source-only control for the next campaign
- stop spending mainline research effort on stricter trigger filtering until later evidence justifies reopening it
- stop resweeping the old late weights as if they are an open frontier
- use `promotion_multi_source_candidate_1_5` as the current promoted-feature control when designing the next late-feature pass
- use the promotion-gap diagnostics to design new late promotion features that specifically lift the remaining `3.0-4.0` blockers from `net_mesh_network` and `field_area_country`

Open question carried forward:

- which next late promotion feature can lift the remaining good blockers without recreating the `promotion_min_4` overblocking spike
- which candidate-missing families should be targeted once the next late-feature pass is exhausted

## Ranking Results

Do not rank experiment rows by a single headline metric.

Use a frontier-specific ordering.

### For seed-coverage campaigns

Rank by:

1. lower `seed_missing`
2. higher `gold_trigger_inventory_coverage_rate`
3. lower `veto_harmful_allow_rate`
4. lower `veto_overblocking_rate`

### For promotion campaigns

Rank by:

1. lower `promotion_miss`
2. higher `veto_abstain_recall`
3. higher `gold_candidate_precision`
4. lower `veto_overblocking_rate`

### For candidate-generation campaigns

Rank by:

1. lower `candidate_missing`
2. higher `candidate_pool_trigger_recall`
3. lower `veto_harmful_allow_rate`
4. lower `gold_candidate_precision` loss versus control

## Negative-control lanes

Some lanes should stay in the sweep program mostly as sanity checks.

Current likely low-yield or already weak frontiers:

- multiword forward-gloss seeds
- raw frequency bonuses
- active-vs-shadow frequency similarity bonuses
- representative pruning as a primary lever
- unconstrained embedding-bridge injection

These should still be re-run occasionally.
But they should not dominate the main frontier search unless new evidence changes.

## Viable vs Prospective Frontiers

Current likely viable frontiers:

- better upstream seed coverage through bounded borrowing and trigger-support weighting
- better late promotion through explicit support-weight tuning
- clearer separation of `seed_missing` vs `promotion_miss`

Current prospective but not yet primary frontiers:

- stronger semantic-bridge generation for real `candidate_missing` cases
- sentence-level veto evaluation replacing the lower-bound proxy as the main runtime-shaped target
- LP-portable semantic-shadow mining beyond `en-es`

## Recommended workflow

1. Pick the frontier you are trying to move.

Examples:
- reduce `seed_missing`
- reduce `promotion_miss`
- improve veto abstain recall without increasing overblocking

2. Add experiment rows to `docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json`.

3. Run the matrix runner.

```bash
python3 scripts/testing/semantic_shadow_experiment_matrix_en_es.py \
  --manifest docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json \
  --json-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md
```

Optional source-audit replay:

```bash
python3 scripts/testing/semantic_shadow_experiment_matrix_en_es.py \
  --manifest docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json \
  --translation-dict /absolute/path/to/forward.sqlite \
  --reverse-translation-dict /absolute/path/to/reverse.sqlite \
  --json-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_candidate_pack.json \
  --markdown-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_candidate_pack.md
```

Use explicit pack overrides when you are testing rebuilt or temporary source artifacts.
Do not overwrite installed dictionaries just to answer a source-quality question.

4. Read both direct and veto metrics.

Do not accept a row based only on one surface.

- gold-proxy metrics answer set quality
- veto-proxy metrics answer runtime-shaped usefulness

5. Inspect harmful-allow miss counts before changing more nodes.

Interpretation:

- `seed_missing`: broaden or improve seed admission
- `candidate_missing`: improve mining/bridge generation
- `promotion_miss`: retune later promotion or support weights

6. When one candidate row looks promising, run the row-compare script against the current control.

```bash
python3 scripts/testing/semantic_shadow_experiment_compare_en_es.py \
  --control-experiment-id source_only_borrowed \
  --candidate-experiment-id promotion_multi_source_candidate_1_5 \
  --json-out docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md
```

The compare runner now accepts the same optional `--translation-dict` and
`--reverse-translation-dict` overrides when the candidate evidence depends on a rebuilt pack.

Use that report to answer:

- how many ambiguous rows were actually fixed
- how many clear rows regressed into false abstain
- which semantic families improved
- whether the frontier is still materially open or mostly trading errors

## Policy for future experiments

When testing continues for a long time, the failure mode is usually not lack of ideas.
It is loss of comparability.

To prevent that:

- keep one manifest-backed matrix as the main experiment lane
- keep new knobs additive inside the manifest schema where possible
- prefer numeric control surfaces over more named branch policies
- keep generated reports in `docs/test_outputs/` as evidence, not architecture truth
- avoid introducing a new script when the matrix can express the experiment

## What should still stay separate

The matrix runner is not a replacement for everything.

Keep these as separate lanes:

- benchmark expansion and hand-reviewed case updates
- review packets for human adjudication
- sentence-level runtime veto benchmarks when they arrive
- LP generalization work once non-`en-es` semantic-shadow mining exists

## Current limitations

- the current matrix runner is pair-specific to `en-es`
- `forward_seed_max_words` is global per run, not per row
- neighbor-borrow trigger scoring is observable in the matrix, but not yet a dedicated weighted trigger-support feature
- inventory-level `promoted_shadow_candidates` are emitted with inventory defaults (`support min=3`, `max promoted=3`), so they are not experiment-truth when a matrix row overrides promotion settings; use matrix outputs or the promotion-gap harness for row-specific conclusions
- existing one-off sweep scripts still exist and remain useful as focused diagnostics

That is acceptable for now.
The important shift is that semantic-shadow testing now has a stable reusable harness layer and a manifest-driven experiment lane.
