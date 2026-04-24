# Semantic Routing Weakness Triage Plan

Status: active planning
Role: Planning / WIP
Last updated: 2026-04-25
Last verified: 2026-04-25 desk audit plus filtered residual source generation, leakage admission, surface-POS prototype guard, and latest quality-gate artifacts
Purpose: define the many-turn triage program for deciding which semantic-routing weak points are real, which changes can and should be made, and what work is required before implementation or rollout
Source-of-truth: planning doc only; current implementation truth still lives in code, tests, generated evidence, and `docs/developer/feature_state_matrix.md`
Related docs:
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
- `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
- `docs/developer/feature_state_matrix.md`
Verification:
- `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
- `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`
- `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
- `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`

Routing note:

- use `docs/rulegen/semantic_routing_runtime_readiness.md` and `docs/rulegen/semantic_routing_publication_contract.md` for current shipped contract truth
- use `docs/rulegen/semantic_shadow_testing_architecture.md` for the current experiment and harness map
- use `docs/rulegen/semantic_routing_generalization_evaluation_plan.md` for the production-stabilization campaign shape
- use this document when the question is narrower and more operational:
  - what are the weak points
  - which of them should change
  - what exact work is needed
  - and what order should the many-turn triage follow

## Goal

Run semantic-routing triage as an explicit decision program rather than a loose sequence of observations.

For every suspected weak point, the process should answer five questions:

1. is the weakness real on current evidence
2. which layer owns it
3. can it be changed cleanly
4. should it be changed now
5. what exact experiment, implementation, validation, and rollout work would be required

## Standard Turn Loop

Most productive turns in this campaign follow the same loop.
Use this as the default mental model before improvising.

1. keep one runtime reference stack frozen
2. add one bounded held-out family or one bounded probe
3. rerun the fixed-shadow artifacts
4. classify the new residue by failure class
5. build one narrow follow-up probe for that specific residue
6. refresh the held-out corridor
7. update the canonical docs so the new interpretation becomes recoverable later

This loop is intentionally conservative.
It prevents three common mistakes:

- changing the reference row and the dataset at the same time
- mixing phrase-leak, weak-active-support, and upstream blocker misses into one bucket
- treating one nice point estimate as if it were a deploy-quality result

## Decision outputs

Every triage turn should end with one of these decisions:

- `do_now`
- `experiment_next`
- `instrument_first`
- `defer`
- `reject`

Those labels are intentionally narrower than general planning language.
The goal is to force each weak point into a concrete next state.

## Failure classes

Use these buckets consistently during triage:

- `seed_missing`
- `candidate_missing`
- `promotion_miss`
- `false_abstain`
- `harmful_allow`
- `harmful_replace`
- `winner_error`
- `phrase_leak`
- `coverage_gap`
- `doc_sprawl`

If a turn identifies a different failure mode, add it explicitly rather than silently overloading one of the existing labels.

## Work-scope taxonomy

Use these scope labels when estimating change cost:

- `docs_only`
- `offline_experiment_only`
- `bounded_code_change`
- `cross_contract_change`
- `new_data_or_source_work`
- `new_evaluation_work`
- `runtime_rollout_work`

## Frozen control stack

Before triaging any change, keep one explicit control stack frozen.
Do not compare a new idea against a moving mix of latest artifacts.

### Fixed-shadow runtime scorer control

Control artifact:

- `docs/test_outputs/semantic_routing_sentence_veto_latest.md`

Current frozen row:

- pair: `en-es`
- scorer: `tfidf_cosine`
- context view: `masked_sentence`
- evidence view: `all_evidence_text`
- phrase control mode: `noun_family_frame_guard`
- active rescue mode: `sense_label_near_tie_active_rescue`
- thresholds: `min_active=0.05`, `min_margin=0.0`

Current measured read:

- decision accuracy: `77.5%`
- replace precision / recall: `100.0%` / `43.8%`
- harmful replace / false abstain: `0.0%` / `56.2%`
- winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`

Interpretation:

- the current runtime gate has the desired abstain-first safety shape
- the current weakness is false-abstain pressure, not harmful replace

### Auto-shadow blocker-generation control ladder

Control artifact:

- `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`

Current frozen ladder:

| Row | Meaning | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: |
| `no_shadows` | no blocker generation | `81.1%` | `0.0%` | `100.0%` | `0.0%` |
| `auto_shadows` | best current source-only lexical lane | `87.4%` | `42.4%` | `57.6%` | `2.1%` |
| `borrowed_trigger_auto_shadows` | source-only plus borrowed-trigger seeds | `89.1%` | `51.5%` | `48.5%` | `2.1%` |
| `reviewed_auto_shadows` | reviewed-trigger automatic lane | `93.7%` | `66.7%` | `33.3%` | `0.0%` |
| `curated_shadows` | current lower-bound oracle ceiling | `100.0%` | `100.0%` | `0.0%` | `0.0%` |

Interpretation:

- blocker generation is materially better than no veto
- source-only blocker generation is still far from the curated ceiling
- the remaining gap is still dominated by blocker quality, not by runtime scorer choice

### Gold-proxy promotion control

Control artifact:

- `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`

Current frozen promotion read:

- current strict lexical policy family is still low-recall on the overlap proxy
- `support_score_v1` and `cross_checked_v1` both read at:
  - candidate precision: `14.1%`
  - candidate recall: `18.0%`
  - gold trigger hit rate: `27.3%`
  - gold trigger exact-match rate: `12.1%`
  - underblocking rows: `24`
  - overblocking rows: `33`

Interpretation:

- late-node promotion is still a real bottleneck
- the current strict promotion family is safer than broad lenient rows, but still underpowered

### Cluster-aware generalization corridor control

Control artifact:

- `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`

Current frozen corridor:

- best current source-only blocker lane: `borrowed_trigger_auto_shadows`
- source-only abstain-recall conservative floor: `31.8%`
- source-only harmful-allow conservative ceiling: `68.2%`
- fixed-shadow replace-recall conservative floor: `12.5%`
- fixed-shadow harmful-replace conservative ceiling: `0.0%`

Interpretation:

- current safety direction is good
- current confidence corridor is still too loose for broad production claims

## Decision rubric

For every item, record the following fields:

- `Evidence`
- `Failure class`
- `Layer`
- `Can change cleanly?`
- `Should change now?`
- `Work necessary`
- `Decision`

Use these meanings:

- `Evidence`: exact doc, artifact, code path, and metric lines supporting the claim
- `Failure class`: primary failure mode, not all possible related symptoms
- `Layer`: blocker generation, runtime scorer, phrase lane, calibration, evaluation, ops/publication, or docs
- `Can change cleanly?`: `yes`, `probably`, `unclear`, or `no`
- `Should change now?`: `yes`, `probably`, `unclear`, or `no`
- `Work necessary`: one or more scope labels from the taxonomy above
- `Decision`: one of the five required decision outputs

## Triage checklist per item

Run this checklist in order for every weak point:

1. state the problem in one sentence
2. cite the exact current evidence
3. separate structural weakness from dataset limitation
4. identify the dominant failure class
5. identify the narrowest owning layer and files
6. decide whether a clean offline experiment exists
7. decide whether the issue is mainly algorithm, data, evaluation, product policy, or docs
8. decide whether success must be judged on held-out families rather than same-family aggregate wins
9. estimate work as `low`, `medium`, `high`, or `very_high`
10. end with one decision label and the next concrete action

## Validation contract by change type

### Docs-only triage updates

- update the relevant planning docs
- run `git diff --check`
- run `python3 scripts/dev/check_doc_references.py` when canonical routing docs are touched

### Blocker-generation experiments

Required minimum:

- `python3 scripts/testing/semantic_shadow_gold_proxy_en_es.py`
- `python3 scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py`
- the targeted experiment runner for the changed lane
- the targeted compare or promotion-gap artifact if the result is supposed to be explanatory

Required before accepting a meaningful frontier move:

- `python3 scripts/testing/semantic_routing_generalization_bound_en_es.py`
- targeted tests for changed `semantic_shadow_*` modules

### Runtime scorer or policy changes

Required minimum:

- `python3 scripts/testing/semantic_routing_sentence_veto_harness.py`
- `python3 scripts/testing/semantic_routing_sentence_veto_sweep.py`
- targeted tests for `semantic_routing_runtime_policy.py` and `semantic_routing_runtime_scoring.py`

Required before accepting a meaningful frontier move:

- `python3 scripts/testing/semantic_routing_generalization_bound_en_es.py`

### Publication or runtime contract changes

Required minimum:

- targeted helper/publication/runtime tests
- keep `docs/developer/feature_state_matrix.md` aligned if default behavior or verified status changes
- run `npm --prefix scripts run check:state` if state claims or evidence paths change materially

## Master inventory

This table is the starting ledger for the many-turn process.
It is intentionally opinionated enough to drive the next turn, but still revisable.

| ID | Layer | Weak point | Current read | Can change cleanly? | Should change now? | Minimal next step |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-1` | docs | Weakness story is distributed across several docs and artifacts rather than one concise weakness map | architecture is legible, but weakness evidence is still scattered | `yes` | `yes` | centralize the weak-point ledger and keep it updated during triage |
| `BG-1` | blocker generation | Seed admission and trigger quality | still a live frontier, but some earlier trigger filtering ideas look saturated | `yes` | `probably` | review seed-lane misses and decide whether the next useful work is seed quality or not |
| `BG-2` | blocker generation | Candidate-source coverage | repeated `seed_missing` and `candidate_missing` rows remain in hard families | `probably` | `yes` | audit the remaining miss families by candidate-source lane |
| `BG-3` | blocker generation | Promotion evidence and thresholds | promotion is still a major bottleneck; strict lexical promotion is safe but narrow | `yes` | `yes` | triage late-node evidence and threshold frontier before adding more branches |
| `BG-4` | blocker generation | Family-specific hard gaps | `job`, `net_mesh_network`, `field_area_country`, and some phrase-sensitive rows still dominate misses | `probably` | `yes` | build a per-family gap table and classify each as seed, candidate, promotion, or phrase issue |
| `BG-5` | blocker generation | Semantic bridge and new source families | promising as recall probes, but not yet publishable improvements | `probably` | `unclear` | decide whether bridge/source work is an immediate frontier or a later secondary frontier |
| `RT-1` | runtime scorer | Context representation | several clear-active families still collapse to `margin=0.000` false abstains | `yes` | `yes` | triage weak context-view families and compare what is missing in the current representation |
| `RT-2` | runtime scorer | Evidence representation | current `all_evidence_text` is safe but likely too blunt for some families | `yes` | `probably` | classify which families look evidence-view-limited rather than context-view-limited |
| `RT-3` | runtime policy | Decision rule is too abstain-heavy | current runtime shape is safe but low-recall even on fixed-shadow data | `yes` | `probably` | decide whether richer scoring or calibration is needed before threshold tuning |
| `RT-4` | runtime policy | Active rescue and near-tie handling | current active rescue is present but effectively not buying much | `yes` | `probably` | inspect rescue activation and identify why it is mostly inert |
| `PH-1` | phrase lane | Phrase or idiom handling is too narrow and partly bolted on | phrase control exists, but the broader seam is still underdeveloped | `probably` | `yes` | separate phrase-sensitive failures from ordinary sense competition failures |
| `CAL-1` | calibration | No strong replace vs abstain vs soft-affordance calibration layer | current policy is threshold-driven and conservative, not strongly calibrated | `probably` | `unclear` | decide whether calibration should wait until blocker generation improves |
| `EVAL-1` | evaluation | Held-out confidence is still weak | corridor is honest, but still loose and family coverage is small | `yes` | `yes` | verify whether current held-out split and bound surface are enough for the next campaign |
| `EVAL-2` | evaluation | Dataset coverage is still small and uneven | fixed-shadow runtime set is still only `8` families / `40` rows | `yes` | `probably` | decide whether dataset growth should happen now or only after a narrower frontier is chosen |
| `OPS-1` | ops/publication | Publication/runtime plumbing is more mature than blocker quality | contract seams are real, but semantic quality is still the limiting factor | `yes` | `no` | keep runtime conservative unless a triaged quality frontier justifies change |
| `TECH-1` | cross-cutting | The current stack is not yet as technology-forward as it could be | retrieval, reranking, or calibrated second-opinion seams remain underused | `unclear` | `unclear` | first identify which failure classes could actually benefit from stronger semantic tech |

## Central weakness map

This section is the first deliverable of `DOC-1`.
Its job is to keep the weakness story in one place so later turns can stay narrow.

| ID | Weak seam | Primary evidence | Owning layer | Current best read |
| --- | --- | --- | --- | --- |
| `DOC-1` | weakness story is distributed across several docs and artifacts | this document plus `docs/rulegen/semantic_routing_implementation_roadmap.md` | docs | architecture is clear, but weakness discovery was too spread out before this ledger existed |
| `BG-1` | seed admission / trigger quality | `docs/test_outputs/semantic_shadow_seed_compare_en_es_latest.md`, `docs/test_outputs/semantic_shadow_forward_seed_sweep_en_es_latest.md`, `docs/test_outputs/semantic_shadow_trigger_support_sweep_en_es_latest.md` | blocker generation | trigger work still matters, but some earlier trigger-filter ideas now look close to saturated |
| `BG-2` | candidate-source coverage | `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`, `docs/test_outputs/semantic_shadow_coverage_gap_en_es_latest.md`, `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md` | blocker generation | remaining hard misses still include real `seed_missing` and `candidate_missing` rows |
| `BG-3` | promotion evidence and thresholds | `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`, `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`, `docs/test_outputs/semantic_shadow_campaign_b_en_es_latest.md`, `docs/test_outputs/semantic_shadow_campaign_c_en_es_latest.md` | blocker generation | promotion is still a major bottleneck and likely the main immediate frontier |
| `BG-4` | family-specific hard gaps | `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`, `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md` | blocker generation | `job`, `net_mesh_network`, `field_area_country`, and some phrase-sensitive families still dominate the miss profile |
| `BG-5` | semantic bridge and new source families | `docs/test_outputs/semantic_shadow_embedding_bridge_sweep_en_es_latest.md`, `docs/rulegen/semantic_shadow_source_intake_plan.md`, `docs/test_inputs/semantic_shadow_source_registry.json` | blocker generation | useful as research recall probes, not yet a publishable improvement |
| `RT-1` | context representation | `docs/test_outputs/semantic_routing_sentence_veto_latest.md`, `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.md` | runtime scorer | several clear-active rows still collapse to zero-margin abstains |
| `RT-2` | evidence representation | `docs/test_outputs/semantic_routing_sentence_veto_latest.md`, `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_latest.md`, `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py` | runtime scorer | current evidence views are safe but likely too blunt for some families |
| `RT-3` | decision rule is too abstain-heavy | `docs/test_outputs/semantic_routing_sentence_veto_latest.md`, `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md` | runtime policy | current gate is safe, but clear-active recall is still weak even on fixed-shadow data |
| `RT-4` | active rescue / near-tie handling | `docs/test_outputs/semantic_routing_sentence_veto_latest.md`, `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py` | runtime policy | rescue exists, but current evidence suggests it is not yet buying much |
| `PH-1` | phrase or idiom handling is too narrow | `docs/rulegen/semantic_routing_runtime_readiness.md`, `docs/test_outputs/semantic_routing_sentence_veto_phrase_guard_latest.md`, `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py` | phrase lane | phrase control helps, but the broader seam is still not fully separated from ordinary sense competition |
| `CAL-1` | no strong calibration layer for replace vs abstain vs soft affordance | `docs/rulegen/semantic_routing_runtime_readiness.md`, `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py` | calibration / product policy | current policy is mostly thresholds plus conservative fallback, not a richer calibrated decision layer |
| `EVAL-1` | held-out confidence is still weak | `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`, `docs/test_inputs/semantic_routing_generalization_splits_en_es.json` | evaluation | the corridor is honest but still too loose for broad confidence |
| `EVAL-2` | dataset coverage is still small and uneven | `docs/test_inputs/semantic_routing/README.md`, `docs/test_outputs/semantic_routing_sentence_veto_latest.md` | evaluation | the fixed-shadow runtime dataset remains small enough that family-level gaps dominate |
| `OPS-1` | publication/runtime plumbing is ahead of blocker quality | `docs/rulegen/semantic_routing_publication_contract.md`, `docs/rulegen/semantic_routing_runtime_readiness.md`, `docs/developer/feature_state_matrix.md` | ops / publication | the contracts are real, but quality remains the limiting factor |
| `TECH-1` | the current stack is not yet as technology-forward as it could be | `docs/rulegen/semantic_routing_runtime_readiness.md`, `core/lexishift_core/rulegen/semantic_shadow_embedding_bridge.py`, `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py` | cross-cutting | stronger semantic retrieval, reranking, or calibrated second-opinion seams are still underused |

## Evidence index

Use this section as the stable lookup table during later turns.
It deliberately names the smallest useful evidence surface for each item.

| ID | Primary artifact or doc | First file to read |
| --- | --- | --- |
| `DOC-1` | central weakness map and master inventory | `docs/rulegen/semantic_routing_weakness_triage_plan.md` |
| `BG-1` | seed and trigger sweep reports | `docs/test_outputs/semantic_shadow_trigger_support_sweep_en_es_latest.md` |
| `BG-2` | veto proxy and compare reports | `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md` |
| `BG-3` | promotion gap and campaign summaries | `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md` |
| `BG-4` | row-level compare and family-heavy miss lists | `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md` |
| `BG-5` | embedding bridge and source-intake plan | `docs/test_outputs/semantic_shadow_embedding_bridge_sweep_en_es_latest.md` |
| `RT-1` | sentence-veto summary | `docs/test_outputs/semantic_routing_sentence_veto_latest.md` |
| `RT-2` | sentence-veto sweep summaries and scoring module | `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.md` |
| `RT-3` | runtime summary plus corridor bound | `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md` |
| `RT-4` | runtime summary plus policy module | `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py` |
| `PH-1` | phrase guard artifact and readiness doc | `docs/test_outputs/semantic_routing_sentence_veto_phrase_guard_latest.md` |
| `CAL-1` | readiness doc plus policy module | `docs/rulegen/semantic_routing_runtime_readiness.md` |
| `EVAL-1` | generalization bound and split file | `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md` |
| `EVAL-2` | schema README and runtime dataset summary | `docs/test_inputs/semantic_routing/README.md` |
| `OPS-1` | publication and readiness docs | `docs/rulegen/semantic_routing_runtime_readiness.md` |
| `TECH-1` | readiness doc plus current bridge/policy modules | `docs/rulegen/semantic_routing_runtime_readiness.md` |

## Turn order

Run the many-turn process in this order:

1. `DOC-1`
2. `BG-1`
3. `BG-2`
4. `BG-3`
5. `BG-4`
6. `PH-1`
7. `BG-5`
8. `RT-1`
9. `RT-2`
10. `RT-3`
11. `RT-4`
12. `CAL-1`
13. `EVAL-1`
14. `EVAL-2`
15. `OPS-1`
16. `TECH-1`

Reasoning:

- docs and blocker-generation triage should come first because blocker quality is still the dominant current product risk
- runtime scorer and policy questions should be judged after blocker-generation ownership is clearer
- phrase and calibration questions should be evaluated separately so they do not get blurred into generic scorer discussion
- ops/publication should remain conservative until the quality triage says otherwise
- technology-forward alternatives should be discussed last, after the failure classes are pinned down well enough to avoid generic model-shopping

## Completed triage notes

### `DOC-1` weakness-map centralization

- Problem statement:
  - the weakness story was spread across roadmap, readiness, feature-state, and generated evidence artifacts
- Best read:
  - this was a real but low-risk process problem
  - centralizing the ledger was immediately useful and did not require algorithm changes
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `docs_only`
- Decision:
  - `do_now`

### `BG-1` seed admission and trigger quality

- Problem statement:
  - automatic trigger seeding still controls whether some blocker families appear at all, but it is no longer clear whether broad seed expansion is still a worthwhile frontier
- Primary evidence:
  - `docs/test_outputs/semantic_shadow_seed_compare_en_es_latest.md`
    - plain rulegen source seeding only reaches `70.0%` gold-trigger coverage and `50.0%` candidate recall
    - adding one-word forward-gloss seeds raises gold-trigger coverage to `90.0%` and candidate recall to `80.0%`
    - widening from `top3` to `all_sources` adds trigger volume without improving the gold-trigger or candidate-recall surfaces
    - the remaining underblocked rows are already a narrow set such as `cargo / job`, `trabajo / job`, `tabla / table`, and `sacar / remove`
  - `docs/test_outputs/semantic_shadow_forward_seed_sweep_en_es_latest.md`
    - `max_words=1` is already the best current forward-seed setting
    - wider forward-gloss phrase admission does not improve recall and only increases overblocking
  - `docs/test_outputs/semantic_shadow_trigger_support_sweep_en_es_latest.md`
    - a compact trigger-support filter can reduce noise on the `top3_plus_forward_gloss` slice, but stronger filtering quickly collapses recall
    - the same filter shape is not a robust frontier on the `all_plus_forward_gloss` slice
  - `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
    - borrowed-trigger seeding materially helps the source-only veto shape versus the plain auto lane
    - but some `seed_missing` rows still remain in hard families, especially inside the current `job` pocket
- Best read:
  - seed admission is still a real weakness
  - the large seed-side gains are mostly already captured by:
    - one-word forward-gloss seeds
    - and the current borrowed-trigger lane
  - broad trigger widening now looks saturated or actively harmful
  - the remaining seed frontier is narrower and more family-local than it first appeared
- Can change cleanly:
  - `yes`
- Should change now:
  - `probably`, but only as a narrow audit rather than as another broad seed-expansion campaign
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - restate the remaining `seed_missing` rows under the current borrowed-trigger control
  - keep `forward_gloss max_words=1` frozen and do not reopen broad `all_sources` widening
  - separate pure trigger-coverage holes from rows that are now better explained by promotion, phrase, or bridge ownership
  - if seed work is reopened, test only one compact trigger-support intervention at a time and require family-level improvement rather than aggregate trigger-count growth
- Decision:
  - `instrument_first`

### `BG-2` candidate-source coverage

- Problem statement:
  - the current blocker generator still misses some gold blockers entirely, and those misses remain concentrated in a small set of families
- Primary evidence:
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`
    - `7` candidate-missing rows
  - `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md`
    - persistent harmful-allow rows still include `candidate_missing` and `seed_missing` families such as `empleo / employment`, `ocupación / employment`, `reja / mesh`, `rejilla / grille`, and `ruta / road`
  - `docs/test_outputs/semantic_shadow_coverage_gap_en_es_latest.md`
    - the remaining audited coverage gap is now narrow and explicitly classified as `semantic_bridge_needed` rather than a broad rulegen-source failure
- Best read:
  - candidate coverage is still a real weakness
  - it is not the main immediate frontier on the current evidence
  - broad source-gap claims look weaker than they did earlier; the remaining issues are now family-local and miss-class-specific
- Can change cleanly:
  - `probably`
- Should change now:
  - `probably`, but after promotion work is better scoped
- Work necessary:
  - `offline_experiment_only`
  - `new_data_or_source_work`
  - `new_evaluation_work`
- Required next work:
  - produce a per-family candidate-source audit for the remaining hard families
  - separate true `seed_missing` from true `candidate_missing`
  - isolate which misses are likely lexical-source fixes versus `semantic_bridge_needed`
- Decision:
  - `instrument_first`

### `BG-3` promotion evidence and thresholds

- Problem statement:
  - the current strict lexical promotion family is safe enough to study, but it still drops many plausible blockers that cluster just below threshold
- Primary evidence:
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`
    - promotion-miss rows cluster in the `3.0-4.0` support-score band
    - dominant families are `net_mesh_network`, `field_area_country`, `job`, and `table_board_chart`
  - `docs/test_outputs/semantic_shadow_campaign_b_en_es_latest.md`
    - no late-node ablation row beat the borrowed baseline
    - the current knob frontier is close to saturated
    - the next meaningful step should be new discriminative promotion features, not resweeping the same weights
  - `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md`
    - one candidate feature (`multi_source_candidate_support=1.5`) improves aggregate tune metrics, but the held-out read stays flat and false abstain ticks up
- Best read:
  - promotion is the main immediate frontier
  - simple threshold or weight resweeps are mostly exhausted
  - the next work should target new discriminative promotion features that lift good blockers from the `3.0-4.0` band without reproducing the `promotion_min_4` overblocking collapse
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - design a short list of new promotion features
  - test them against the frozen borrowed baseline
  - require held-out family improvement before accepting the feature as a real frontier move
- Decision:
  - `experiment_next`

#### Ranked `BG-3` promotion-feature queue

Use this queue to keep the next promotion experiments narrow.
The goal is to stop mixing proven controls, exhausted resweeps, and genuinely new feature ideas.

#### `BG-3` frozen invariants

- keep `support_score_min=5.0` as the control threshold until a new feature family changes the score distribution enough to justify re-opening the threshold frontier
- keep `same_pos_as_active` on; Campaign B shows that disabling it collapses both tune and held-out behavior
- keep `active_profile_support` on; Campaign B shows that turning it off regresses back toward the weaker non-borrowed lane
- keep `multi_source_candidate_support=1.5` as the current promoted control row; Campaign C shows that it is the best current late-feature addition even though held-out improvement remains incomplete
- judge every new feature on held-out families, not just tune-slice aggregate wins

| Rank | Feature family | Current status | Best read | Can change cleanly? | Should change now? | Decision | Required work |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | family-local discriminative lifters for the remaining `3.0-4.0` promotion-miss band | not yet implemented as an explicit feature family | this is the real immediate frontier; the remaining misses are clustered enough to target without reopening the broad threshold surface | `yes` | `yes` | `experiment_next` | inspect the `7` current promotion-miss rows, derive `1-3` bounded new features, add them behind zero-default weights, and rerun promotion-gap, veto-proxy, and held-out bound artifacts |
| `2` | dormant frequency representative and frequency-similarity bonuses | implemented in `core/lexishift_core/rulegen/semantic_shadow_support.py`, but not exercised in the current experiment matrix | plausible secondary frontier because the hooks already exist and may help the `3.0-4.0` band, but there is no current evidence yet that they move the right families | `yes` | `probably` | `instrument_first` | add a minimal frequency-only mini-matrix, inspect whether it lifts `field_area_country`, `net_mesh_network`, `table_board_chart`, or `job` without widening cross-POS junk, then decide whether it graduates into the main queue |
| `3` | source-convergence control via `multi_source_candidate_support` | already implemented and already the best current promoted row | keep it as the frozen control, not as the next new frontier | `yes` | `no` | `defer` | no immediate change; continue to compare new features against this row rather than the older borrowed baseline |
| `4` | `trigger_family_reentry` | implemented and already benchmarked in the current matrix | tune-slice gains exist, but held-out stays flat; this is not currently a convincing frontier move | `yes` | `no` | `defer` | revisit only if a later family-local feature needs it as a narrow tie-breaker rather than as a primary lifter |
| `5` | `forward_neighborhood_overlap` | implemented and already benchmarked in the current matrix | same shape as `trigger_family_reentry`: some tune movement, no held-out proof, and occasional accuracy regression | `yes` | `no` | `defer` | do not spend another turn on this alone unless a later feature depends on it compositionally |
| `6` | `semantic_bridge_support` weight changes or bridge-text widening inside promotion | implemented and already benchmarked in the current matrix | flat on the current promotion surfaces; bridge questions are real, but this knob is not the right immediate seam | `yes` | `no` | `reject` | stop spending promotion turns on bridge-weight resweeps; route bridge and new-source questions to `BG-5` instead |
| `7` | pure threshold or `max_promoted` resweeps | already heavily explored | exhausted as an immediate frontier; the `min=4` row widens the wrong surface and the stricter rows collapse promotion | `yes` | `no` | `reject` | do not reopen threshold tuning until a new feature family changes the score distribution materially |

#### `BG-3` queue conclusion

- The next actual promotion work should start with rank `1`, not with another resweep of existing weights.
- Rank `2` is the only credible secondary lane that is both already wired and still underexplored.
- Ranks `4` and `5` stay in reserve, but current evidence does not justify another dedicated turn on them.
- Ranks `6` and `7` are explicitly closed as immediate frontiers.

#### Minimal experiment package for rank `1`

1. Use `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md` to restate the `7` current promotion-miss rows and group them by reusable signature rather than by family name alone.
2. Design at most `3` new bounded features that specifically target the current `3.0-4.0` band while preserving the existing `same_pos_as_active` and `active_profile_support` safeguards.
3. Add the new features to `core/lexishift_core/rulegen/semantic_shadow_support.py` behind zero-default weights and add only a small number of experiment-matrix rows around the `multi_source_candidate_support=1.5` control.
4. Accept the feature only if it improves the promotion-gap artifact and the held-out generalization corridor without reproducing the `promotion_min_4` overblocking pattern.

### `BG-4` family-specific hard-gap map

- Problem statement:
  - the remaining blocker failures are no longer one undifferentiated pool; they cluster into a small set of families with different owning causes
- Primary evidence:
  - `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
    - family-level veto read differs sharply by family
  - `docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md`
    - persistent harmful-allow rows already reveal the dominant miss class for the hardest families
  - `docs/test_outputs/semantic_shadow_campaign_c_en_es_latest.md`
    - the best current promotion feature still leaves a small stable set of promotion-miss families
  - `docs/test_outputs/semantic_shadow_coverage_gap_en_es_latest.md`
    - the remaining broad coverage gap is now narrow and explicitly classified
  - `docs/test_outputs/semantic_shadow_review_packet_en_es_latest.md`
    - some of the apparent blocker problems are really cross-POS or phrase/exception problems that should stay conservative
- Best read:
  - a family-level gap map is worth keeping explicitly
  - the hardest families do not all belong to the same frontier
  - the current family buckets are:
    - promotion-dominant
    - mixed source-plus-promotion
    - phrase or exception-dominant
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `docs_only`
  - `new_evaluation_work`
- Decision:
  - `do_now`

#### Current hard-gap family map

| Family | Borrowed baseline read | Reviewed-auto read | Dominant miss mix | Current interpretation | Primary owner | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| `field_area_country` | acc `54.5%`, abstain recall `33.3%`, harmful allow `66.7%`, overblocking `20.0%` | acc `63.6%`, abstain recall `33.3%`, harmful allow `66.7%`, overblocking `0.0%` | mostly `promotion_miss`, plus some false-abstain pressure | severe family, but mainly a promotion-quality problem rather than a broad source-gap problem; the new source-convergence feature already fixed part of `terreno`, while `campo / field` still persists | `BG-3` | treat as a primary promotion-feature validation family |
| `net_mesh_network` | acc `30.0%`, abstain recall `14.3%`, harmful allow `85.7%`, overblocking `33.3%` | acc `70.0%`, abstain recall `57.1%`, harmful allow `42.9%`, overblocking `0.0%` | mixed `seed_missing` plus `promotion_miss`, with clear false-abstain spillover | hardest current family; not one clean bug class | `BG-2` plus `BG-3` | split into separate source and promotion subqueues before new code |
| `job` | acc `80.0%`, abstain recall `62.5%`, harmful allow `37.5%`, overblocking `0.0%` | acc `86.7%`, abstain recall `75.0%`, harmful allow `25.0%`, overblocking `0.0%` | mixed `seed_missing` plus `candidate_missing`; one narrow `semantic_bridge_needed` row remains | real family weakness, but no longer a broad source-collapse story; it is now a smaller mixed source/bridge audit | `BG-2` plus `BG-5` | audit `cargo`, `empleo`, and `ocupación` as separate subcases before bridge work |
| `table_board_chart` | acc `85.7%`, abstain recall `50.0%`, harmful allow `50.0%`, overblocking `0.0%` | acc `85.7%`, abstain recall `50.0%`, harmful allow `50.0%`, overblocking `0.0%` | mainly `promotion_miss` | stable moderate weakness; good promotion test family, not the main source frontier | `BG-3` | keep as a secondary promotion-feature validation family |
| `path_route` | acc `90.0%`, abstain recall `83.3%`, harmful allow `16.7%`, overblocking `0.0%` | acc `100.0%`, abstain recall `100.0%`, harmful allow `0.0%`, overblocking `0.0%` | one residual `seed_missing` pocket | no longer a top-tier hard family; current weakness is narrow and should not dominate the frontier | `BG-2` | defer broad work; keep only a low-priority seed audit |
| `remove_take_out` | acc `83.3%`, abstain recall `50.0%`, harmful allow `50.0%`, overblocking `0.0%` | acc `83.3%`, abstain recall `50.0%`, harmful allow `50.0%`, overblocking `0.0%` | visible `promotion_miss`, but tagged `phrase_sensitive` | at least part of this family should not stay inside generic blocker triage; it wants phrase-lane handling | `PH-1` plus `BG-3` | hand off to phrase triage before widening blocker policy here |

#### Cross-family safety watchpoints

- `punto / period -> hora` is not a family-scale frontier, but it is a useful safety watchpoint:
  - the experiment compare shows it as the candidate row’s one introduced false abstain
  - the review packet and gap queue keep the row dropped because it is a cross-POS case without reviewed trigger support
- Use it as a cautionary row when testing new promotion features.
  A change that improves blocker recall by admitting more `punto -> hora` style rows is probably widening the wrong surface.

#### Family-routing conclusion

The family map changes the next-step order:

- `field_area_country` and `table_board_chart` should feed directly into promotion-feature design
- `net_mesh_network` and `job` should be decomposed further before deciding whether new source work or bridge work is justified
- `remove_take_out` should move into phrase-lane triage rather than staying in generic blocker-generation discussion
- `path_route` should not be allowed to dominate planning anymore

### `PH-1` phrase or exception handling

- Problem statement:
  - some unsafe or misleading applies are not ordinary sense-competition problems and should be blocked by a dedicated phrase or frame lane before generic semantic scoring
- Primary evidence:
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
    - phrase problems are explicitly called out as a separate seam, and the doc warns that if phrase preemption is not separated from semantic veto the runtime gate will stay muddy and harder to calibrate
  - `docs/test_outputs/semantic_routing_sentence_veto_phrase_guard_latest.md`
    - the best current phrase-guarded sentence-veto configuration reaches `95.0%` decision accuracy with `0.0%` harmful replace, `12.5%` false abstain, and `5` phrase preemption hits at `100.0%` precision
  - `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
    - the current phrase seam is narrow and heuristic:
      - noun-like families only
      - a few preceding-token frames (`modal`, `to`, `please`, sentence-initial object)
      - and a very small following-particle set (`into`, `on`)
  - `core/tests/rulegen/test_semantic_routing_runtime_scoring.py`
    - current tests cover the narrow `bank on` style noun-family guard and explicitly avoid blocking ordinary noun usage like `bank` or `ball into`
  - `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
    - phrase-sensitive hazard rows remain a distinct slice, and the family map now routes `remove_take_out` here instead of treating it as ordinary blocker tuning
- Best read:
  - the phrase lane is already real and high-leverage
  - the current implementation is still narrow, hand-shaped, and under-generalized
  - this is not a generic blocker-generation problem and should stay out of broad promotion tuning
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - define the current phrase-lane scope explicitly:
    - idioms
    - frozen collocations
    - cross-POS lexicalized expressions
    - frame-sensitive trigger uses
  - expand the phrase/exception dataset before broadening heuristics
  - test phrase-lane changes separately from ordinary blocker-generation changes
  - keep `punto / period -> hora` and `quitar / remove -> sacar` as safety watch rows
- Decision:
  - `experiment_next`

### `BG-5` semantic bridge and new source families

- Problem statement:
  - the remaining mixed families still tempt source-heavy or bridge-heavy work, but it is no longer clear whether that work is an immediate frontier or a secondary research lane
- Primary evidence:
  - `docs/test_outputs/semantic_shadow_coverage_gap_en_es_latest.md`
    - the current audited coverage gap has collapsed to `1` row
    - `semantic_bridge_needed=1`
    - `rulegen_source_gap=0`
    - the remaining explicit bridge-needed row is `trabajo / job -> cargo`
  - `docs/test_outputs/semantic_shadow_embedding_bridge_sweep_en_es_latest.md`
    - the embedding bridge is useful as a recall probe, but not as a current default frontier
    - on the publish-shaped lexical lane, the safe `support_min=5.0` rows are flat versus baseline, while lower-threshold rows widen overblocking sharply
  - `docs/rulegen/semantic_shadow_source_intake_plan.md`
    - source-heavy work is explicitly supposed to live in the offline research layer
    - broad ingest is allowed, but runtime should stay narrow and derived
    - the recommended operating model is still one small approved batch, not a broad new-source rollout
  - `docs/test_inputs/semantic_shadow_source_registry.json`
    - `wiktionary_sense_inventory_dump` and `example_sentence_bank` are approved but not integrated
    - `open_multilingual_wordnet`, `aligned_phrase_table`, `llm_shadow_proposals`, and `llm_anchor_cues` are still planned and pending
    - the current embedding bridge source remains marked `runtime_publishable=false`
- Best read:
  - semantic bridge and new-source work is real, but it is currently a secondary research lane rather than the next default-facing blocker frontier
  - the current product bottleneck is not a broad missing-source problem
  - it is a narrower mix of:
    - one audited `semantic_bridge_needed` case
    - a few family-local candidate gaps
    - and still-larger promotion-quality gaps
  - the current embedding bridge is good enough to justify future offline source experiments, but not good enough to justify widening the current default path
- Can change cleanly:
  - `probably`
- Should change now:
  - `no`
- Work necessary:
  - `offline_experiment_only`
  - `new_data_or_source_work`
  - `new_evaluation_work`
  - `runtime_rollout_work`
- Required next work:
  - do not expand the current default blocker lane with embedding bridge or broad new-source ingestion
  - keep source-heavy work on a dedicated experiment branch if it is reopened
  - if the queue returns here later, start with one coverage-heavy source and one discrimination-heavy source only
  - require the source ablation to show exactly which failure bucket moved before any publication-facing change is discussed
- Decision:
  - `defer`

### `RT-1` context representation

- Problem statement:
  - the current runtime context views are safe enough to use, but still collapse many clear-active rows into zero-margin abstains
- Primary evidence:
  - `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
    - current control row is `tfidf_cosine + masked_sentence + all_evidence_text`
    - decision accuracy is `77.5%`
    - harmful replace is `0.0%`
    - false abstain is still `56.2%`
    - the current false-abstain rows cluster in `ball`, `bank`, `plant`, and `spring`, often at margin `0.000`
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.json`
    - best safe row by context is:
      - `masked_sentence`: `77.5%` decision accuracy, `0.0%` harmful replace, `56.2%` false abstain
    - the next-best masked context is weaker:
      - `masked_window`: `75.0%` decision accuracy, `0.0%` harmful replace, `62.5%` false abstain
    - raw context buys some recall only by widening the wrong surface:
      - `raw_sentence`: `72.5%` decision accuracy, `4.2%` harmful replace, `62.5%` false abstain
      - `raw_window`: `75.0%` decision accuracy, `8.3%` harmful replace, `50.0%` false abstain
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_latest.json`
    - the same context pattern holds for the transformer lane:
      - safe best row remains `masked_sentence`
      - raw contexts improve winner ranking and even reach `85.0%` decision accuracy, but only with `8.3%` harmful replace
  - `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
    - the current context family is intentionally small:
      - `raw_sentence`
      - `masked_sentence`
      - `raw_window`
      - `masked_window`
    - the windowed views are only a fixed `4` tokens on each side
- Best read:
  - context representation is a real runtime frontier
  - `masked_sentence` is clearly the best current safety-shaped control and should stay frozen as the baseline
  - raw contexts are not the right default frontier because they recover some active recall by reintroducing harmful replace
  - narrow windows are also not enough; they lose too much of the useful sentence evidence
  - the remaining context problem is therefore not "pick raw instead of masked"
  - it is "design richer masked or multi-view context representations that keep safety while lifting the zero-margin active rows"
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - keep `masked_sentence` as the frozen runtime context control
  - do not reopen raw-context widening as the main frontier
  - design at most `1-2` richer context variants that preserve masking and full-sentence scope
  - require improvement specifically on the current `ball`, `bank`, `plant`, and `spring` false-abstain rows while preserving `0` harmful replaces
- Decision:
  - `experiment_next`

### `RT-2` evidence representation

- Problem statement:
  - the current runtime gate depends heavily on one broad concatenated evidence view, and it is still unclear whether the main problem is evidence sparsity, evidence bluntness, or incomplete evaluation of the supported evidence surface
- Primary evidence:
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.json`
    - best row by evidence view:
      - `all_evidence_text`: `77.5%` decision accuracy, `0.0%` harmful replace, `56.2%` false abstain, `75.0%` winner accuracy
      - `gloss_text`: `62.5%` decision accuracy, `0.0%` harmful replace, `93.8%` false abstain, `50.0%` winner accuracy
      - `sense_label`: `62.5%` decision accuracy, `0.0%` harmful replace, `93.8%` false abstain, `53.1%` winner accuracy
  - `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
    - the scorer supports more evidence views than the default sweep regularly exercises:
      - `sense_label`
      - `gloss_text`
      - `sense_gloss_bundle`
      - `qualifier_text`
      - `all_evidence_text`
  - `scripts/testing/semantic_routing_sentence_veto_sweep.py`
    - the default sweep currently only covers:
      - `sense_label`
      - `gloss_text`
      - `all_evidence_text`
  - `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
    - the dataset already carries `sense_gloss_bundle`, but not a populated `qualifier_text` lane
  - local one-turn probe on `2026-04-23` using `scripts/testing/semantic_routing_sentence_veto_sweep.py --evidence-views sense_gloss_bundle`
    - best `sense_gloss_bundle` row only reached:
      - `62.5%` decision accuracy
      - `0.0%` harmful replace
      - `93.8%` false abstain
      - `53.1%` winner accuracy
    - so the missing improvement is not hiding in the currently untested `sense_gloss_bundle` view
- Best read:
  - evidence representation is a real weakness
  - the current compact views are too thin to support a useful safe gate
  - the current winning view, `all_evidence_text`, is broad enough to work but likely too blunt and undifferentiated
  - the implemented evidence surface is still wider than the routinely exercised one, so this lane still needs instrumentation before default changes
- Can change cleanly:
  - `yes`
- Should change now:
  - `probably`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - extend the canonical sweep to include every currently supported evidence view
  - keep `all_evidence_text` as the frozen evidence control until a contender beats it on the `0` harmful-replace frontier
  - if this lane reopens after instrumentation, prefer structured or segmented evidence bundles over even broader plain concatenation
  - do not spend time on `sense_gloss_bundle` as a likely winner; the one-turn probe already shows that it behaves much closer to `sense_label` / `gloss_text` than to `all_evidence_text`
- Decision:
  - `instrument_first`

### `RT-3` decision rule is too abstain-heavy

- Problem statement:
  - the current runtime policy is safe, but it is still mostly a binary `replace` / `abstain` threshold rule and leaves too much potentially useful confidence structure unused
- Primary evidence:
  - `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
    - current best lexical control row is still:
      - `77.5%` decision accuracy
      - `100.0%` replace precision
      - `43.8%` replace recall
      - `0.0%` harmful replace
      - `56.2%` false abstain
    - this is a safe shape, but still clearly under-replacing
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.md`
    - the nearby threshold rows do not reveal a substantially better safe frontier
    - threshold movement mostly just trades false abstain against harmful replace or collapses back toward pure abstain
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_latest.md`
    - the transformer lane can reach:
      - `93.8%` winner accuracy
      - `100.0%` shadow-winner accuracy
    - but still does not beat the lexical control as a safe final gate
    - that means winner ranking signal and safe replace gating are already measurably different surfaces
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
    - the conceptual runtime ladder already distinguishes:
      - `replace`
      - `soft affordance`
      - `abstain`
    - but the shipped DOM path still only renders `replace`; `soft_affordance` currently behaves the same as `abstain` in visible product behavior
  - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
    - the current policy still reduces runtime admission mostly to:
      - `active_score >= min_active_score`
      - `margin >= min_margin`
      - plus phrase preemption and optional rescue
    - the reason-code ladder confirms the current shape:
      - `active_margin_clear`
      - `active_score_below_floor`
      - `active_margin_below_floor`
      - `shadow_winner`
  - `docs/test_outputs/semantic_routing_sentence_veto_ladder_latest.md`
    - the first bounded ladder sweep over the frozen `v3` default finds a real but tiny soft-affordance band
    - best zero-noise row is `soft:a=0.58:m=-0.03`
    - that row adds exactly one soft-affordance case, `plant:002`, with `0` soft false positives
    - replace-or-soft recall rises from `95.0%` to `100.0%`, but the gain is only one case and still product-blocked because visible `soft_affordance` rendering is not shipped
- Best read:
  - `RT-3` is a real frontier
  - simple threshold tuning is close to exhausted
  - the first offline ladder simulation is now landed and says the remaining three-way policy opportunity is narrow:
    - one clean soft true positive
    - no measured soft false positives on the fixed `v3` slice
  - some of the product value here is still blocked on the shipped path, because `soft_affordance` is still reserved rather than rendered
  - so the right next step is not live widening of replace criteria
  - it is held-out confidence work plus, if productized later, a bounded one-row-class soft-affordance experiment rather than a broad three-way rewrite
- Can change cleanly:
  - `probably`
- Should change now:
  - `probably`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `cross_contract_change`
- Required next work:
  - keep the current context and evidence controls frozen while evaluating richer policy variants
  - add offline policy comparisons that explicitly simulate:
    - binary `replace` / `abstain`
    - and three-way `replace` / `soft_affordance` / `abstain`
  - require any policy improvement to stay at `0` harmful replace on the current runtime set before discussing rollout changes
  - treat any real `soft_affordance` product use as a separate contract step, not as a hidden threshold tweak
- Decision:
  - `experiment_next`

### `RT-4` active rescue and near-tie handling

- Problem statement:
  - the runtime already has an active-side near-tie rescue path, but it appears to contribute little or nothing on the current frontier row
- Primary evidence:
  - `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
    - current control row reports:
      - `active rescue applied rate = 0.0%`
  - local one-turn probe on `2026-04-23` using `scripts/testing/semantic_routing_sentence_veto_harness.py` and `scripts/testing/semantic_routing_sentence_veto_sweep.py`
    - current frontier row is identical with rescue `off` and `sense_label_near_tie_active_rescue`:
      - `masked_sentence + all_evidence_text + noun_family_frame_guard + min_active=0.05 + min_margin=0.00`
      - `77.5%` decision accuracy
      - `0.0%` harmful replace
      - `56.2%` false abstain
      - `active_rescue_applied_count = 0`
    - rescue only fires in clearly weaker threshold regions, where the overall row drops to:
      - `62.5%` decision accuracy
      - `93.8%` false abstain
      - and just `1` rescue hit
  - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
    - rescue is intentionally narrow:
      - it only runs after a primary abstain
      - it is disabled on phrase-preempted rows
      - it only uses `sense_label` as the backup evidence view
      - and it still requires a positive backup margin floor
- Best read:
  - active rescue is real, but currently too narrow and too detached from the actual frontier to count as a live improvement lane
  - the current runtime weakness is upstream of rescue:
    - context
    - evidence
    - and the broader decision rule
  - rescue should therefore stay explicit, but not consume the next runtime turn
- Can change cleanly:
  - `yes`
- Should change now:
  - `no`
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - none on the mainline frontier
  - if this lane is revisited later, start with a case-level audit of the current near-tie abstains before changing rescue thresholds or backup evidence
- Decision:
  - `defer`

### `CAL-1` replace vs abstain vs soft-affordance calibration

- Problem statement:
  - the runtime now exposes scores, margins, reason codes, and even a reserved `soft_affordance` outcome, but there is still no strong calibrated layer that maps those signals into a trustworthy confidence policy
- Primary evidence:
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
    - the intended runtime ladder explicitly distinguishes:
      - `replace`
      - `soft affordance`
      - `abstain`
    - but the shipped DOM path still only visibly acts on `replace`
    - the doc also states that this should be an intentional product policy, not an accidental side effect of a benchmark threshold
  - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
    - current runtime behavior is still mostly threshold-led:
      - `min_active_score`
      - `min_margin`
      - phrase preemption
      - optional rescue
    - there is no stronger calibrated confidence layer on top of those signals
  - `docs/test_inputs/semantic_routing/semantic_admit_batch_response.schema.json`
    - contracts already reserve `soft_affordance`
  - `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
    - runtime can already carry `soft_affordance` decisions and diagnostics
  - `apps/chrome-extension/content/processing/replacements.js`
    - visible DOM behavior still only applies on `replace`
  - `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`
    - the current confidence corridor is still too loose for a true calibrated product layer:
      - fixed-shadow replace-recall conservative floor: `23.3%`
      - fixed-shadow false-abstain conservative ceiling: `76.7%`
      - source-only harmful-allow conservative ceiling: `96.8%`
  - `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
    - product confidence should come from campaign evidence, not anecdotal runtime sessions
- Best read:
  - calibration is a real missing layer
  - but it is not yet ready to become a user-facing runtime behavior frontier
  - the main missing prerequisites are:
    - a tighter held-out confidence corridor
    - broader evaluation coverage
    - and a real rendered `soft_affordance` product path
  - the right near-term move is calibration instrumentation and reporting, not calibrated rollout behavior
- Can change cleanly:
  - `probably`
- Should change now:
  - `probably`, but only as instrumentation
- Work necessary:
  - `offline_experiment_only`
  - `new_evaluation_work`
  - `bounded_code_change`
  - `cross_contract_change`
- Required next work:
  - add one explicit per-pair calibration report over current semantic-routing outputs:
    - active score
    - shadow score
    - margin
    - reason-code bucket
    - and eventual `replace` / `soft_affordance` / `abstain` recommendation bucket
  - keep that report offline-only until the confidence corridor tightens materially
  - do not let calibration silently widen `replace`
  - treat visible `soft_affordance` behavior as a later product-contract step, not as a hidden threshold tweak
- Decision:
  - `instrument_first`

### `EVAL-1` held-out confidence is still weak

- Problem statement:
  - the repo now has an honest generalization corridor, but it is still too loose to support strong confidence claims about semantic veto quality
- Primary evidence:
  - `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`
    - fixed-shadow lexical control currently has:
      - replace-recall conservative floor: `23.3%`
      - false-abstain conservative ceiling: `76.7%`
    - fixed-shadow sentence-transformer default currently has:
      - replace-recall conservative floor: `76.7%`
      - harmful-replace conservative ceiling: `6.7%`
      - false-abstain conservative ceiling: `23.3%`
    - fixed-shadow active-sense overlay experiment currently has:
      - replace-recall conservative floor: `90.0%`
      - harmful-replace conservative ceiling: `0.0%`
      - false-abstain conservative ceiling: `10.0%`
    - fixed-shadow zero-noise soft ladder currently has:
      - replace-or-soft conservative floor: `83.3%`
      - soft-noise conservative ceiling: `0.0%`
    - interpretation:
      - the runtime-side held-out corridor is now materially tighter and more differentiated than before
      - but it is still only over `15` fixed-shadow families and a small soft lane
    - source-only blocker generation currently has:
      - abstain-recall conservative floor: `3.2%`
      - harmful-allow conservative ceiling: `96.8%`
  - `docs/test_inputs/semantic_routing_generalization_splits_en_es.json`
    - fixed-shadow runtime split is only:
      - `7` tune families
      - `8` held-out families
    - reviewed-overlap family split is only:
      - `6` tune families
      - `6` held-out families
  - `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
    - explicitly states that held-out family generalization is the minimum honest test
    - and that thresholds should never be chosen only by aggregate metrics on the same families used to design the feature
- Best read:
  - held-out confidence is a real current blocker for broad claims
  - the runtime-side corridor is now honest enough to distinguish three different postures:
    - the shipped hard reference is stronger than lexical control but still carries a small harmful ceiling
    - the zero-noise soft ladder remains narrow but real
    - the active-sense overlay experiment is now the cleanest current bounded runtime candidate
  - the repo already has the right evaluation philosophy
  - what is missing is not the concept of generalization testing
  - it is stronger held-out breadth, especially for blocker generation and for proving that the active-sense overlay remains clean beyond the current phrase-risk families
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `offline_experiment_only`
  - `new_evaluation_work`
- Required next work:
  - keep the current split file explicit and versioned
  - keep the current bounded default row and the current zero-noise soft row fixed as runtime references
  - expand held-out family coverage before accepting broad quality claims
  - refresh the cluster-aware bound artifact after each accepted frontier move rather than only after large campaigns
  - treat the conservative corridor as a release blocker, not as a reporting footnote
- Decision:
  - `experiment_next`

### `EVAL-2` dataset coverage is still small and uneven

- Problem statement:
  - the fixed-shadow runtime dataset is still small enough that a few family choices dominate both the frontier and the confidence story, even after the first targeted breadth expansion
- Primary evidence:
  - `docs/test_inputs/semantic_routing/README.md`
    - the current curated runtime-veto dataset is now:
      - `19` ambiguity families
      - `95` labeled sentences
    - `v10` adds:
      - `report` as a held-out noun-active / verb-shadow weak-active-support family
  - `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
    - the lexical control remains polarized, but the new family additions are informative rather than uniform:
      - `watch` still lands at `80.0%` decision accuracy / `50.0%` active recall
      - `check` lands at `60.0%` decision accuracy / `0.0%` active recall
      - `order`, `trip`, and `report` now also land at `60.0%` decision accuracy / `0.0%` active recall
  - `docs/test_outputs/semantic_routing_sentence_veto_ladder_latest.md`
    - the corrected zero-noise soft row is now:
      - `soft:a=0.60:m=0.00`
    - and it recovers no additional surfaced wins on the frozen `v10` hard row
  - `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`
    - the held-out runtime corridor is now more honest and more differentiated:
      - hard replace conservative floor `63.2%`
      - hard replace harmful ceiling `5.3%`
      - replace-or-soft conservative floor `63.2%`
      - active-sense overlay conservative floor `71.1%`
      - active-sense overlay harmful ceiling `0.0%`
- Best read:
  - the targeted family-growth approach was the right move
  - `v10` did exactly what the evaluation layer needed:
    - it added a held-out weak-active-support family without creating a new phrase-leak seam
    - while keeping the underlying hard-reference harmful row unchanged
  - the new weak-active probe sharpens the runtime read:
    - direct primary swaps still recover the weak-active rows
    - but they now add `4-8` harmful replaces on the same slice
    - and the widened rescue overlay is still not clean because `play:005` stays harmful
    - while `check:001`, `order:001`, and `trip:001` already land cleanly and `report:001` / `report:002` widen the held-out weak-active-support residue beyond `check:002`, `order:002`, and `trip:002`
  - the held-out corridor now sharpens that again:
    - both the runtime reference lane and the widened-rescue simulated lane still carry a `5.3%` harmful-replace ceiling
    - but the accepted active-sense overlay experiment now keeps a `71.1%` replace-recall conservative floor with a `0.0%` harmful-replace ceiling
  - dataset coverage is still small, so this remains an offline analysis result rather than rollout evidence
  - the next gap is now narrower than “add another held-out family right away”:
    - keep `play:005` as the live hard-reference harmful row
    - keep the active-sense overlay as the preferred bounded experimental comparator
    - preserve the genuine weak-active-support rescue wins on rows like `drink:001`, `drink:002`, and `park:001`
    - track `check:002`, `order:002`, `trip:002`, `report:001`, and `report:002` as the current held-out false-abstain residue
    - do not reopen generic context widening or broad soft-rollout claims
    - move the next evaluation turn to the queue-backed pre-prompt data path
- Can change cleanly:
  - `yes`
- Should change now:
  - `yes`
- Work necessary:
  - `new_evaluation_work`
- Required next work:
  - keep `v10` fixed as the active fixed-shadow evaluation slice
  - keep:
    - `drink` in tune
    - `play` in held-out
    - `watch` in held-out
    - `check` in held-out
    - `order` in held-out
    - `trip` in held-out
    - `report` in held-out
  - keep the new weak-active probe artifact current
  - keep the active-sense overlay bound lane current
  - treat `play:005` as the leading hard-reference phrase-leak target
  - treat `play:002`, `check:002`, `order:002`, `trip:002`, `report:001`, and `report:002` as the remaining held-out false-abstain targets
  - do not infer a broader soft rollout from the old `plant` / `drink` / `order` / `trip` lift story; the corrected `v10` zero-noise row adds no new surfaced wins
  - do not promote the direct `sense_label` or raw-context primaries into runtime-default candidates
  - keep the new family inventory, bakeoff queue, and prompt-slot manifest fixed against the same slice
  - keep the new `example_sentence_bank` feasibility pilot artifact current:
    - current installed packs expose `0 / 6` target families with example-bearing queued rows
    - all `6 / 6` target families do expose reverse-side auxiliary sense text
  - keep the new reverse-aux-text pilot artifact current:
    - `reverse_aux_plus_all_evidence` is now the best cheap non-LLM control on the frozen queue slice
    - it improves the queue-slice point read from `1` harmful / `8` false abstains to `1` harmful / `6` false abstains
    - the concrete recovered rows are `plant:002`, `drink:002`, and `order:002`
  - keep the new prompt-spec and smoke-preview bundle current:
    - proxy default `gpt-5.4-mini`
    - target default `gpt-5.4`
    - `6` concrete prompt requests across the `2` active cue slots on the frozen `v10` queue
  - do not treat that win as a new runtime-default candidate:
    - it is a pre-prompt control row, not a shipped runtime policy change
  - do not treat the smoke bundle as a completed proxy batch:
    - the execution runner now exists and is now guarded behind explicit `--execute-live`
    - the new no-spend preflight artifact should stay current before any real batch run
    - the new cost-estimate artifact should also stay current before any real batch run
    - the first live batch still requires the sourced-shell path plus usable quota on the machine that runs it
- Decision:
  - `do_now`

### `OPS-1` publication/runtime plumbing is ahead of blocker quality

- Problem statement:
  - the shipped publication and runtime seams are already more mature than the current blocker-quality frontier, so the main operational risk is widening product behavior before the semantic evidence actually justifies it
- Primary evidence:
  - `docs/rulegen/semantic_routing_publication_contract.md`
    - helper publication now has a real validated artifact family:
      - ruleset
      - snapshot
      - semantic inventory
      - publication manifest
    - ready pointers require semantic inventory publication and must resolve to trigger, sense, and competition-set records
    - `metadata.semantic_admission.status` remains the source of truth rather than sidecar presence alone
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
    - runtime only activates helper semantic scoring when:
      - the enabled SRS ruleset has computed capability `active`
      - nonzero `status=ready` coverage exists
      - semantic inventory resolves successfully
    - the shipped DOM path still only acts on `decision=replace`
    - `soft_affordance` and `abstain` both keep the original text
    - the doc explicitly says the current `en-es` ready-publication path is only a narrow helper-side broader-context `emitted_rule_siblings` PoC, not broad shadow-mined runtime readiness
  - `docs/developer/feature_state_matrix.md`
    - the shipped semantic runtime layer is documented as `implemented`, `default-on-when-capable`, and intentionally conservative
    - the `en-es` broader-context ready-publication seam is kept explicit as narrower than true shadow promotion
    - known gaps still include:
      - no LP default path emitting a fully mined competition/shadow set
      - no phrase-preemption inventory publication
      - and still-small runtime-veto evaluation coverage
- Best read:
  - the operational plumbing is real and already correctly conservative
  - `OPS-1` is not a call to broaden runtime behavior now
  - it is a call to preserve the current capability-gated, `replace`-only, narrow-ready-publication posture until blocker quality, phrase handling, and held-out confidence improve
  - the main risk in this lane is overclaiming readiness or widening publication semantics faster than the evaluation frontier supports
- Can change cleanly:
  - `yes`
- Should change now:
  - `no`
- Work necessary:
  - `docs_only`
  - `runtime_rollout_work`
  - `cross_contract_change`
- Required next work:
  - keep the current capability gating frozen:
    - `active`
    - `published_unready`
    - `unavailable`
    - `error`
  - do not broaden ready-publication defaults beyond the current emitted-sibling PoC until `BG-3`, `PH-1`, and `EVAL-1`/`EVAL-2` materially improve
  - keep visible DOM behavior conservative:
    - `replace` only
    - with `soft_affordance` remaining an explicit future contract step rather than a hidden runtime widening
  - if operational work reopens before quality work lands, limit it to:
    - diagnostics
    - checklist hardening
    - and explicit PoC-vs-ready documentation
- Decision:
  - `defer`

### `TECH-1` technology-forward alternatives are still underused

- Problem statement:
  - the current stack underuses stronger semantic retrieval, reranking, and second-opinion technology, but the repo still needs a failure-class-specific plan before any such technology is worth adding
- Primary evidence:
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
    - explicitly argues that embeddings alone are not the full answer and should sit inside a competition-based admission system rather than replace the pipeline
    - the first target-card embedding bridge can recover `trabajo / job -> cargo` only at a looser threshold where overblocking rises sharply
    - the current runtime ladder already distinguishes:
      - `replace`
      - `soft affordance`
      - `abstain`
    - and keeps phrase preemption as a separate conceptual seam
  - `docs/test_outputs/semantic_shadow_embedding_bridge_sweep_en_es_latest.md`
    - the embedding bridge can raise source-only recall from `80.0%` to `90.0%`
    - but the best bridge row falls to `11.8%` precision with `35.5%` overblocking
    - so the current bridge is a useful recall probe, not a publishable improvement
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_latest.md`
    - the transformer lane improves winner ranking and shadow-winner accuracy
    - but still does not beat the lexical control as a safe final gate
    - so stronger semantic ranking and safe replace gating are measurably different problems
  - `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
    - the remaining false-allow surface is already classified into concrete miss buckets rather than a generic “needs smarter model” story
  - `docs/developer/feature_state_matrix.md`
    - current stronger-tech seams stay explicitly research-only or non-default:
      - embedding bridge remains non-publishable
      - no fully mined default blocker path exists yet
      - `soft_affordance` is still reserved rather than productized
- Best read:
  - technology-forward work is real, but only in narrow, failure-bucket-specific, abstain-biased roles
  - the current evidence does not support replacing lexical/provenance mining with a broader embedding or LLM-first system
  - the only credible near-term lanes are:
    - bridge or backoff candidate filtering for the remaining `semantic_bridge_needed` or `candidate_missing` pockets
    - borderline promotion reranking around the current `3.0-4.0` support-score miss band
    - phrase-preemption classification for phrase-sensitive rows
    - veto-only runtime second opinion that can add abstains or future `soft_affordance`, but never authorize `replace`
- Can change cleanly:
  - `probably`
- Should change now:
  - `probably`, but only as bounded offline instrumentation rather than product-facing adoption
- Work necessary:
  - `offline_experiment_only`
  - `bounded_code_change`
  - `new_evaluation_work`
- Required next work:
  - define one explicit tech-forward micro-matrix keyed to failure class, not to model family hype
  - limit the first pass to at most four probes:
    - bridge candidate filtering
    - borderline promotion reranking
    - phrase classification
    - veto-only second opinion
  - require each probe to inherit the native safety metric of its owning lane:
    - `harmful_allow` and `overblocking` for blocker-generation work
    - `harmful_replace` and `false_abstain` for runtime-veto work
  - forbid first-pass tech-forward lanes from directly authorizing `replace`
  - reject broad “nearest-neighbor everything” or “LLM proposes blockers end to end” work as the current frontier
- Decision:
  - `instrument_first`

## First-pass priority stack

This is the post-triage order for actual work.
It is intentionally narrower than the original inventory.

### Tier 1: main next execution frontier

- `BG-3` rank `1` promotion-feature work
- `PH-1` phrase-lane scope and dataset expansion
- `EVAL-1` and `EVAL-2` targeted held-out and runtime-family growth

Why:

- blocker quality is still the main product limiter
- phrase-sensitive failures need to stop contaminating generic blocker tuning
- confidence breadth has to tighten alongside any accepted frontier move

### Tier 2: runtime improvements after the blocker/evaluation frontier sharpens

- `RT-1` richer masked-context variants
- `RT-3` offline decision-ladder comparisons
- `RT-2` full evidence-surface instrumentation

Why:

- runtime work is real, but it should be judged against a less fragile blocker and evaluation surface

### Tier 3: secondary audits and bounded exploratory seams

- `BG-1` family-local seed audit
- `BG-2` family-local candidate audit
- `CAL-1` offline calibration reporting
- `TECH-1` failure-bucket-specific stronger-tech micro-matrix

Why:

- these are real, but they are not the main current blocker to safe progress

### Tier 4: preserve-conservative or deferred seams

- `BG-5`
- `RT-4`
- `OPS-1`

Why:

- these lanes should either remain explicit secondary research or stay conservative until the main frontier moves

## Full investigation map

This section is the compact "do not forget anything" view.
Use it when deciding what to work on next across many turns.

Rules:

- every still-relevant path should appear in exactly one bucket below
- completed or ruled-out work should stay listed with a re-entry condition instead of silently disappearing
- if a turn materially changes a lane, update the bucket assignment here before relying on chat memory

### Bucket A: active execution now

These are the paths we actively expect to keep pushing in the current campaign.

| Path | Owning IDs | Why it is still open | Next concrete work | Success signal | Do not forget |
| --- | --- | --- | --- | --- | --- |
| bounded active-sense noun phrase-guard experiment | `PH-1`, `RT-3` | the acceptability review is now sharper: on `v10`, the active-sense hard lane still removes harmful replace without improving the conservative hard corridor, while the active-sense overlay removes harmful replace without giving back the current overlay floor | keep the active-sense overlay as the preferred bounded experiment while monitoring the hard variant as a secondary lane | the overlay stays clean while future cue-data work or new held-out families do not reopen phrase leakage beyond `play:005` | do not promote the active-sense hard lane to the main reference unless it materially improves weak-active-support residue too |
| weak-active-support diagnosis on every new family | `RT-2`, `RT-3` | current `drink`, `trip`, and `report` evidence says new families can split into backup-rescue cases vs cue-data residue vs mixed phrase-leak cases; we still need to keep the buckets explicit | for each new family, compare current default, direct primary swaps, bounded overlay behavior, and phrase-sensitive failure rows, then register the result in the family inventory | new misses separate into safe backup-rescue cases vs phrase-leak or cue-data residue | do not promote `sense_label` or raw-context primaries based on diagnostic wins alone |
| runtime held-out corridor tightening | `EVAL-1`, `EVAL-2` | the corridor is more honest now, but the hard reference and plain widened-rescue overlay still carry a non-zero harmful ceiling on `v10`; the accepted active-sense overlay is the clean comparator | keep the bound artifact authoritative and refresh it after each accepted runtime-eval move or cue-data pilot | the phrase-leak failure class is isolated cleanly enough that the held-out corridor tightens again | avoid reading one point estimate as a deploy KPI |
| pre-prompt family queue freeze and review | `EVAL-2`, `CAL-1` | the first real family inventory and bakeoff queue now exist, but they still need to remain the canonical frozen slice for pre-prompt work | keep the `v10` inventory, queue, slot manifest, and queue-review note fixed while new cue-data work is judged against them | prompt work starts from a stable family slice rather than drifting with each new runtime artifact | do not start prompt smoke work on a moving queue |

### Bucket B: queued next once the current runtime-eval slice is sharper

These are real paths, but they should not jump ahead of the current rescue-gating / held-out-growth frontier.

| Path | Owning IDs | Why it is queued rather than active-now | Next concrete work | Re-entry trigger |
| --- | --- | --- | --- | --- |
| another held-out rescue-gating / phrase-leak family-growth wave | `RT-3`, `PH-1`, `EVAL-2` | `v10` already served the current conservative pre-prompt goal: `report` widened cue-data residue without reopening phrase leakage, so another family wave should not jump ahead of queue-backed cue-data pilots | resume held-out growth only after the `v10` queue and the first non-LLM cue pilot are stable | the current queue-backed cue pilot fails to explain the residue or a new phrase seam appears |
| promotion-feature redesign from current live miss signatures | `BG-3` | blocker generation is still the main product limiter overall, but the first new triplet feature pack was flat and should not be blindly replaced by another guess | reopen the promotion queue only after the next held-out/runtime additions clarify the live miss signatures again | a refreshed promotion-gap read produces a bounded feature idea tied to current misses rather than stale signatures |
| family-local seed audit | `BG-1` | seed work still matters, but it is now a smaller residual lane rather than the current main frontier | audit remaining hard families for `seed_missing` patterns only after the current runtime-eval step is stable | clear family-local seed misses remain after the current runtime frontier is mapped |
| family-local candidate-source audit | `BG-2` | candidate coverage is still real, but not the next bottleneck to resolve in the current turn order | classify remaining hard misses by candidate-source lane after the next runtime-eval additions land | live hard misses still show real `candidate_missing` rows after current runtime work |
| richer masked-context variants | `RT-1` | current evidence says not to reopen generic raw-context widening; context work should only resume if rescue-gating is not enough | design masked-context variants only for residue that stays unresolved after the new held-out rescue-gating families are added | new held-out families produce misses that the backup-evidence path does not explain |
| offline calibration reporting | `CAL-1` | calibration is a real missing layer, but current product behavior is still dominated by evidence and coverage questions | add reporting-only calibration views after the held-out runtime slice is less fragile | we have a larger held-out slice and multiple plausible runtime candidate lanes to compare |
| failure-bucket-specific stronger-tech probes | `TECH-1` | stronger semantic tech should be studied only once the failure buckets are sharper, not as generic model-shopping | run a small abstain-biased micro-matrix against a clearly defined failure bucket | a specific bucket remains unresolved after current rescue-gating and held-out-growth work |

### Bucket C: monitor, preserve, or reopen only with new evidence

These paths are intentionally not the default next move, but they should stay visible.

| Path | Owning IDs | Current stance | Reopen only if | What we already learned |
| --- | --- | --- | --- | --- |
| semantic bridge and new source-family work | `BG-5` | deferred research lane | blocker-generation recall remains capped after the nearer lexical/promotion lanes are rechecked | bridge/source work is interesting, but not the next default-facing blocker frontier |
| explicit rescue-mode implementation change | `RT-4` | preserve-conservative | the widened-rescue signal survives broader held-out growth and still looks like the best clean path | current rescue exists, but earlier direct rescue tuning was mostly inert on the frontier row |
| visible soft-affordance product behavior | `CAL-1`, `RT-3` | preserve-conservative | the soft lane grows beyond the one-row `plant:002` class and survives held-out evaluation | the zero-noise soft ladder is real but still tiny and not the main current frontier |
| publication/runtime widening | `OPS-1` | preserve-conservative | semantic quality improves enough that runtime behavior expansion is actually justified | the contracts are ahead of semantic quality; widening too early is the main risk |

### Bucket D: explicitly closed until a real re-entry condition appears

These are the main anti-forgetting rows.
They are not gone; they are closed because current evidence says "do not spend the next turn here."

| Closed lane | Prior owner | Why it is closed | Reopen only if |
| --- | --- | --- | --- |
| first triplet promotion-feature pack | `T1-A`, `BG-3` | `promotion_triplet_core_bonus`, `promotion_triplet_forward_bonus`, and `promotion_triplet_bridge_guard_bonus` were flat against the current control row | a fresh promotion-gap read shows a genuinely different miss-signature frontier |
| direct `sense_label` primary runtime candidate | `RT-2`, `RT-3` | it does recover `park:001`, but introduces harmful replaces on the same fixed slice | a future held-out slice shows the harmful rows were slice-specific and a bounded version can stay clean |
| direct raw-context primary runtime candidate | `RT-1`, `RT-3` | raw sentence / raw window recover recall only by widening harmful replaces | a future failure bucket clearly requires broader context and does not recreate the current harmful rows |
| broad threshold loosening | `RT-3` | negative-margin hard-threshold widening becomes harmful before it solves the current frontier cleanly | a future policy experiment shows a new safeguarded threshold shape, not just looser hard replace rules |

### Carry-forward checklist

Before ending any future turn, check these questions against this section:

1. did we move an active path forward
2. did we change any queued path's re-entry condition
3. did we accidentally reopen a closed lane without new evidence
4. did a preserve-conservative lane become active, and if so, why
5. did we add a new path that needs a row here

## Tier 1 execution matrix

Use the next phase as three bounded packages.
Do not mix code changes, acceptance decisions, or frontier claims across them.

### Tier 1 package rules

- keep `BG-3` and `PH-1` in separate patches
- keep the current split manifest authoritative unless a turn explicitly edits it
- do not tune on a family and then claim it as held-out evidence in the same turn
- rerun the cluster-aware bound after any candidate package that looks good enough to keep
- if a candidate win is only tune-slice movement, record it as `instrument_first` or `defer`, not as a frontier move

### `T1-A` promotion-feature package (`BG-3` rank `1`)

Goal:

- test whether `1-3` bounded new support features can lift the current `3.0-4.0` promotion-miss band without reopening the broad threshold surface

Current frozen inputs:

- seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- policy: `support_score_v1`
- threshold / max promoted: `5.0` / `2`
- current promoted control row: `promotion_multi_source_candidate_1_5`
- current promotion-miss rows: `7`
- current miss families:
  - `field_area_country`
  - `job`
  - `table_board_chart`
  - `net_mesh_network`

Design boundary:

- derive features from the current miss signatures, not from family names alone
- use the current reviewed-overlap split as written:
  - tune families include `job`, `field_area_country`, and `table_board_chart`
  - `net_mesh_network` stays a held-out watch family unless the split manifest is explicitly revised first
- keep `same_pos_as_active`, `active_profile_support`, `support_score_min=5.0`, and `max_promoted=2` frozen unless a new feature changes the score distribution enough to justify a later threshold re-open

Current signature queue to target:

- `forward_trigger_support + benchmark_target_present + same_pos_as_active + active_side_support`
- `benchmark_target_present + same_pos_as_active + active_side_support`
- `benchmark_target_present + same_pos_as_active + active_side_support + semantic_bridge_support`

First concrete hypothesis pack:

| Planned experiment id | Hypothesis | Why it is first-pass safe |
| --- | --- | --- |
| `promotion_triplet_core_bonus` | add one higher-order feature for `benchmark_target_present + same_pos_as_active + active_side_support` | this is the narrowest reusable interaction that explains `6` of the current `7` promotion-miss rows while staying inside the existing lexical/provenance lane |
| `promotion_triplet_forward_bonus` | add a second interaction feature for `forward_trigger_support + benchmark_target_present + same_pos_as_active + active_side_support` | this isolates the stronger near-threshold signature already present on rows like `tabla -> cuadro`, `trabajo -> empleo`, and `red -> malla` instead of just increasing the global `forward_trigger_support` weight again |
| `promotion_triplet_bridge_guard_bonus` | add a small guarded interaction for `semantic_bridge_support` only when the triplet-core signature is already present | this targets the lone `reja -> rejilla` style bridge-confirmed miss without reopening the failed broad bridge-weight lane |

Implementation note:

- these are interaction-feature hypotheses, not a request to raise the current base weights globally
- if `promotion_triplet_core_bonus` widens the surface too much on its own, keep it as the main lesson and move the next pass to a stricter guarded variant rather than reopening threshold tuning

Allowed code surface:

- `core/lexishift_core/rulegen/semantic_shadow_support.py`
- `docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json`
- `core/tests/rulegen/test_semantic_shadow_scoring.py`
- `core/tests/rulegen/test_semantic_shadow_evaluation.py`

Required command pack:

```bash
python3 scripts/testing/semantic_shadow_experiment_matrix_en_es.py \
  --manifest docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json \
  --json-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md

python3 scripts/testing/semantic_shadow_experiment_compare_en_es.py \
  --control-experiment-id promotion_multi_source_candidate_1_5 \
  --candidate-experiment-id <new_experiment_id> \
  --json-out docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_experiment_compare_en_es_latest.md

python3 scripts/testing/semantic_shadow_promotion_gap_en_es.py \
  --seed-mode rulegen_top3_plus_forward_gloss_plus_neighbor_borrow \
  --include-neighbor-borrow-seed-modes \
  --policy support_score_v1 \
  --support-score-min 5.0 \
  --support-score-max-promoted 2 \
  --support-score-weights-json '<candidate_weight_json>' \
  --json-out docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md

python3 scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py \
  --json-out docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md

python3 scripts/testing/semantic_routing_generalization_bound_en_es.py \
  --json-out docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md

PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/rulegen/test_semantic_shadow_scoring.py \
  core/tests/rulegen/test_semantic_shadow_evaluation.py
```

Accept only if:

- the candidate closes at least `1` of the current `7` promotion-miss rows
- the compare report shows more ambiguity fixes than new false-abstain regressions
- the held-out read does not worsen into a new `promotion_min_4`-style overblocking surface
- the refreshed generalization bound does not worsen the current blocker-generation corridor

Reject or defer if:

- the win is tune-only
- the new row depends mainly on `net_mesh_network` without an explicit split update
- the new row improves recall only by broadening cross-POS or phrase-sensitive junk

First execution result (`2026-04-23`):

- implemented the three zero-default interaction features in:
  - `core/lexishift_core/rulegen/semantic_shadow_support.py`
- added manifest rows:
  - `promotion_triplet_core_bonus`
  - `promotion_triplet_forward_bonus`
  - `promotion_triplet_bridge_guard_bonus`
- targeted tests passed:
  - `core/tests/rulegen/test_semantic_shadow_inventory.py`
  - `core/tests/rulegen/test_semantic_shadow_scoring.py`
  - `core/tests/rulegen/test_semantic_shadow_evaluation.py`
- current matrix read is flat versus `promotion_multi_source_candidate_1_5`:
  - gold precision / recall stay `88.2%` / `30.0%`
  - veto accuracy / abstain recall / harmful allow stay `86.9%` / `36.4%` / `63.6%`
- current compare artifact reads:
  - `flat_no_row_level_change`
  - `improved=0`
  - `regressed=0`
  - `fixed_harmful_allow=0`
  - `introduced_false_abstain=0`
- refreshed live control promotion-gap evidence now shows why the triplet features stayed inert:
  - the current misses are no longer dominated by the earlier `same_pos_as_active + active_side_support` shape
  - the live miss signatures are now more often:
    - `reviewed_trigger_support + benchmark_target_present + active_side_support + trigger_family_reentry`
    - `benchmark_target_present + active_side_support + trigger_family_reentry`
    - `benchmark_target_present + semantic_bridge_support`
  - the live `promotion_miss` family set is currently:
    - `field_area_country`
    - `path_route`
    - `take_carry`
    - `remove_take_out`
    - `net_mesh_network`
- decision:
  - do not widen `T1-A` immediately with another guessed feature family
  - treat this first hypothesis pack as executed and flat
  - move directly to `T1-B` Phase `1` before reopening promotion design

### `T1-B` phrase-lane package (`PH-1`)

Goal:

- separate phrase-lane scope from ordinary sense competition, then test any heuristic broadening only after the phrase slice itself is better specified

Phase split:

1. dataset and scope first
2. heuristic changes second

Phase 1 outputs:

- explicit phrase-lane scope note covering:
  - idioms
  - frozen collocations
  - cross-POS lexicalized expressions
  - frame-sensitive trigger uses
- a small runtime-veto dataset expansion for phrase work

Minimum dataset package:

- create `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json`
- add exactly `2` new families / `10` rows in the first pass:
  - `1` phrase-dominant noun family
  - `1` cross-POS or lexicalized-expression family
- update `docs/test_inputs/semantic_routing/README.md`
- update `docs/test_inputs/semantic_routing_generalization_splits_en_es.json` in the same patch

Frozen first-pass family choices:

- tune family:
  - `board`
  - active target `tablero`
  - shadow target `junta`
  - phrase-control row centered on idiomatic `on board`
- held-out family:
  - `table`
  - active target `mesa`
  - shadow target `tabla`
  - phrase-control row centered on lexicalized verb use `will table`

Why these two:

- `board` adds a noun-family idiom slice that is clearly phrase-shaped rather than generic sense competition
- `table` adds a cross-POS lexicalized-expression slice that should stay separate from ordinary noun-family blocker tuning
- both stay close to the current phrase-lane discussion without duplicating an existing `v2` family

Allowed code surface for Phase 1:

- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json`
- `docs/test_inputs/semantic_routing/README.md`
- `docs/test_inputs/semantic_routing_generalization_splits_en_es.json`
- this planning doc

Allowed code surface for Phase 2:

- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `core/tests/rulegen/test_semantic_routing_runtime_scoring.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`

Required command pack for Phase 2:

```bash
python3 scripts/testing/semantic_routing_sentence_veto_harness.py \
  --dataset docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json \
  --scorer tfidf_cosine \
  --context-view masked_sentence \
  --evidence-view all_evidence_text \
  --min-active-score 0.05 \
  --min-margin 0.00 \
  --phrase-control-mode noun_family_frame_guard \
  --active-rescue-mode sense_label_near_tie_active_rescue \
  --json-out docs/test_outputs/semantic_routing_sentence_veto_latest.json \
  --markdown-out docs/test_outputs/semantic_routing_sentence_veto_latest.md

python3 scripts/testing/semantic_routing_sentence_veto_sweep.py \
  --dataset docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json \
  --scorers tfidf_cosine,sentence_transformer_cosine \
  --context-views masked_sentence \
  --evidence-views all_evidence_text \
  --min-active-grid 0.00,0.05,0.10,0.15 \
  --min-margin-grid 0.00,0.05,0.10 \
  --phrase-control-modes off,noun_family_frame_guard \
  --active-rescue-modes off,sense_label_near_tie_active_rescue \
  --json-out docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.json \
  --markdown-out docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.md

python3 scripts/testing/semantic_routing_generalization_bound_en_es.py \
  --sentence-dataset docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json \
  --family-splits-manifest docs/test_inputs/semantic_routing_generalization_splits_en_es.json \
  --json-out docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.json \
  --markdown-out docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md

PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/rulegen/test_semantic_routing_runtime_scoring.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py
```

Accept Phase 1 if:

- the new dataset expansion is still small, explicit, and tagged by failure bucket
- each new family is assigned to tune or held-out in the split manifest on purpose

Phase 1 execution result (`2026-04-23`):

- added `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json`
- kept the first-pass family choices frozen:
  - `board` in tune
  - `table` in held-out
- tagged the new phrase rows by failure bucket instead of leaving them as generic family rows:
  - `board` phrase row is idiom + frame-sensitive pressure
  - `table` phrase row is cross-POS + lexicalized-expression pressure
- updated the runtime-dataset README so `v3` is current and `v2` remains frozen for before/after comparison
- updated the fixed-shadow sentence-veto split manifest in the same patch
- decision:
  - treat `T1-B` Phase `1` as landed
  - reopen phrase work only through `T1-B` Phase `2`
  - keep `T1-A` closed until the new runtime slice actually changes the blocker story

Accept Phase 2 only if:

- harmful replace stays at `0`
- phrase-preemption precision does not regress on the current phrase slice
- non-phrase clear-active rows do not regress into a broader false-abstain surface

Phase 2 baseline read on `v3` (`2026-04-23`):

- refreshed conservative control harness on `v3`:
  - config:
    - `tfidf_cosine`
    - `masked_sentence`
    - `all_evidence_text`
    - `noun_family_frame_guard`
    - `sense_label_near_tie_active_rescue`
    - `min_active=0.05`
    - `min_margin=0.00`
  - current control read:
    - decision accuracy `78.0%`
    - replace recall `45.0%`
    - harmful replace `0.0%`
    - false abstain `55.0%`
    - phrase slice remains fully safe:
      - phrase-control decision accuracy `100.0%`
      - phrase-preemption precision `100.0%`
    - new families are not special breakpoints on the control row:
      - `board` is `80.0%` / `50.0%` active recall
      - `table` is `80.0%` / `50.0%` active recall
- refreshed `v3` sweep:
  - best row is:
    - `sentence_transformer_cosine`
    - `masked_sentence`
    - `all_evidence_text`
    - `noun_family_frame_guard`
    - `sense_label_near_tie_active_rescue`
    - `min_active=0.00`
    - `min_margin=0.00`
  - best-row read:
    - decision accuracy `98.0%`
    - replace recall `95.0%`
    - harmful replace `0.0%`
    - false abstain `5.0%`
    - phrase-preemption precision `100.0%`
    - active-rescue precision `100.0%`
- dedicated best-row harness confirms the remaining failure is now only:
  - `en-es:sentence-veto:plant:002`
  - false abstain on `The plant needs more sunlight in the afternoon.`
- scorer/policy/bound alignment is now landed:
  - the bound control row now matches the current conservative runtime control:
    - replace-recall conservative floor `20.0%`
    - harmful-replace conservative ceiling `0.0%`
  - the bound reference row now matches the actual winning `v3` candidate lane:
    - label `Sentence-transformer phrase-guard candidate`
    - replace-recall conservative floor `85.0%`
    - harmful-replace conservative ceiling `0.0%`
    - false-abstain conservative ceiling `15.0%`
- decision:
  - do not add phrase-specific runtime heuristics yet
  - the phrase slice is already effectively solved on the strong safe runtime lane
  - the next runtime turn should decide whether the aligned sentence-transformer candidate lane remains advisory only or becomes the subject of an explicit runtime-policy/default experiment

Reject or defer if:

- the change only improves phrase rows by widening generic abstain behavior
- the change relies on unreviewed phrase categories that are not yet represented in the dataset

### `T1-C` minimum evaluation package (`EVAL-1` + `EVAL-2` rider)

Goal:

- keep `T1-A` and `T1-B` honest with the smallest evaluation changes that materially improve confidence

Package rules:

- do not add new reviewed-overlap blocker families just to support `T1-A`; use the current split first
- if `T1-A` produces a promising candidate that is clearly net-mesh-specific, revise the reviewed-overlap split in a separate patch before accepting the feature
- treat the new sentence-veto `v3` dataset as the only required runtime-family expansion for Tier 1
- rerun the bound after every candidate package that looks keepable

Minimum output set:

- current split manifest stays explicit and versioned
- `v2` remains frozen for before/after comparison
- `v3` becomes the only new runtime dataset admitted in Tier 1
- each accepted `T1-A` or `T1-B` move refreshes:
  - the relevant package artifact
  - the compare or sweep artifact
  - the cluster-aware bound artifact

Tier 1 stop rule:

- do not start Tier 2 runtime-context or runtime-policy work until at least one Tier 1 package produces a real accepted frontier move or the Tier 1 matrix is explicitly judged exhausted

## Immediate next-turn checklist

Use the next execution turn in this exact order:

1. keep `T1-A` closed as executed-and-flat; do not add another promotion feature guess yet
2. treat `T1-B` Phase `1` as landed and keep the first-pass family choices frozen:
   - `board` in tune
   - `table` in held-out
3. if phrase work continues, start with `T1-B` Phase `2` only:
   - treat the existing `v3` baseline as the control
   - do not add phrase heuristics unless a new failure appears beyond the current `plant:002` residue
4. next runtime work should decide whether the strong safe sentence-transformer lane can and should become a first-class evaluated reference
5. only after scorer/policy/bound alignment is explicit should `T1-A` reopen or phrase heuristics widen again

## Initial execution status

Current status after this document was created:

- Stage 0 control stack: frozen in this document
- Stage 1 ledger skeleton: seeded in the master inventory above
- `DOC-1`: completed for the first pass by adding the central weakness map and evidence index
- `BG-1`: triaged to `instrument_first`; the seed frontier is now narrowed to a smaller family-local audit instead of a broad trigger-expansion campaign
- `BG-2`: triaged to `instrument_first`
- `BG-3`: triaged to `experiment_next`, with the ranked promotion-feature queue now added and the exhausted resweep lanes explicitly closed
- `BG-4`: triaged to `do_now` by adding the family hard-gap map and routing the hardest families to their likely owners
- `PH-1`: triaged to `experiment_next`
- `BG-5`: triaged to `defer`; the source-heavy and semantic-bridge lane is now explicitly separated from the current default blocker frontier
- `RT-1`: triaged to `experiment_next`; masked full-sentence context is the best current safe control, but the zero-margin active failures remain concentrated in a small family set
- `RT-2`: triaged to `instrument_first`; evidence work is real, but the missing win is not hiding in `sense_gloss_bundle`, and the supported evidence surface is still only partly exercised in the canonical sweep
- `RT-3`: triaged to `experiment_next`; the current policy is safe but too binary, and the next meaningful policy work is richer offline decision-ladder simulation rather than more threshold nudging
- `RT-4`: triaged to `defer`; active rescue exists, but is currently inert on the frontier row
- `CAL-1`: triaged to `instrument_first`; calibration is a real missing layer, but current product behavior and confidence bounds are still too immature for a user-facing calibrated policy
- `EVAL-1`: triaged to `experiment_next`; the held-out corridor is honest but still too loose for broad confidence
- `EVAL-2`: triaged to `experiment_next`; dataset growth is justified now, but only in a targeted family-driven way
- `OPS-1`: triaged to `defer`; the current capability-gated publication/runtime conservatism is the correct posture and should remain explicit until blocker quality improves
- `TECH-1`: triaged to `instrument_first`; stronger semantic tech is still worth studying, but only in narrow abstain-biased failure-bucket probes
- Current recommended next turn:
  - keep `PH-1` narrow, but treat the candidate decision as landed through the current held-out phrase and weak-active families:
    - the phrase-leak probe now spans `play`, `watch`, `check`, `order`, `trip`, and `report`
    - active-sense noun phrase guarding is no longer an abstract candidate
    - the hard lane is safer but does not improve the conservative hard corridor
    - the overlay lane remains the preferred bounded experiment
  - keep the bounded runtime-default decision fixed while follow-on work catches up:
    - keep `en_es_sentence_veto_v10.json` as the active fixed-shadow evaluation slice
    - keep:
      - `drink` in tune
      - `play` in held-out
      - `watch` in held-out
      - `check` in held-out
      - `order` in held-out
      - `trip` in held-out
      - `report` in held-out
    - keep `en_es_sentence_veto_v3` as the shipped bounded default
    - keep `en_es_sentence_veto_v2` as the explicit conservative lexical control
    - treat the current bound as authoritative for that frozen default/control split:
      - control floor `15.8%` replace recall
      - candidate floor `63.2%` replace recall
      - candidate harmful-replace ceiling `5.3%`
      - active-sense hard experimental floor `63.2%` replace recall with `0.0%` harmful replace ceiling
      - active-sense overlay experimental floor `71.1%` replace recall with `0.0%` harmful replace ceiling
  - keep the first `RT-3` ladder baseline fixed:
    - best zero-noise soft row is now `soft:a=0.60:m=0.00`
    - it recovers no additional surfaced wins on `v10`
    - do not treat soft-affordance as a live frontier again unless a later slice re-establishes clean lift
  - the held-out confidence baseline is now landed for the runtime lane:
    - default runtime reference floor is `63.2%` replace recall with `5.3%` harmful replace ceiling
    - zero-noise soft ladder floor is `63.2%` replace-or-soft recall with `0.0%` soft-noise ceiling
    - widened-rescue simulated floor is `71.1%` replace recall with `5.3%` harmful replace ceiling
    - active-sense hard experimental floor is `63.2%` replace recall with `0.0%` harmful replace ceiling
    - active-sense overlay experimental floor is `71.1%` replace recall with `0.0%` harmful replace ceiling
  - next runtime work should now shift from more held-out growth to the pre-prompt data path:
    - keep `T1-A` closed as flat until new blocker evidence justifies reopening it
    - keep the fixed `v10` hard row, the fixed zero-noise soft row, and the accepted active-sense overlay experiment as frozen references
    - keep the new family inventory, bakeoff queue, and prompt-slot manifest frozen with the same slice
    - keep the new `example_sentence_bank` feasibility pilot current
    - if we want more non-LLM pre-prompt coverage, run a reverse-aux-text cue pilot before any paid prompt smoke pass

Reasoning:

- `DOC-1` was the cheapest high-leverage cleanup and is now good enough to stop re-discovering the same weak points every turn
- `BG-1` is still real, but it is now clearly a smaller residual lane rather than the dominant current blocker frontier
- `BG-2` is still real, but current evidence says it is not the main immediate frontier
- `BG-3` is the current main technical frontier
- `BG-4` was necessary because the remaining hard families no longer belong to one single queue
- `PH-1` should come before `BG-5` because the family map now shows that some apparent blocker failures are actually phrase/exception failures, and keeping them inside generic blocker triage will muddy the next promotion experiments
- the `BG-3` promotion-feature queue is now specific enough to stop wasting turns on flat bridge-weight or threshold resweeps
- `BG-5` is now separated as a deferred research lane rather than an immediate blocker-quality frontier
- the blocker-generation side is now mapped well enough to move to runtime-scorer triage without losing track of which failures are still upstream
- `RT-1` now makes the runtime context frontier explicit: `masked_sentence` is the right control, but current safe context views are still too weak on several clear-active families
- `RT-2` now makes the evidence frontier explicit: `all_evidence_text` is the only currently viable evidence control, and the missing improvement is not sitting in the already-supported `sense_gloss_bundle`
- `RT-3` now makes the policy frontier explicit: better safe ranking does not automatically become a better replace gate, and the current binary threshold ladder is close to saturated
- `RT-4` is real but not worth a frontier turn yet, because it does not change the current best row
- `CAL-1` is now separated as instrumentation-first rather than rollout-first, which keeps calibration from being treated as a magical fix for weak evidence or weak generalization
- `EVAL-1` and `EVAL-2` now make the confidence gap concrete: the main issue is not lack of evaluation philosophy, but lack of enough held-out breadth and targeted runtime-family coverage
- `OPS-1` is now closed as a preserve-conservative lane, not an active implementation frontier
- `TECH-1` is now closed as instrumentation-first, which keeps “more advanced technology” tied to specific failure buckets instead of generic model-shopping
- the triage program now has a first-pass execution order:
  - Tier 1 for mainline improvement
  - Tier 2 for runtime follow-on work
  - Tier 3 for secondary audits and bounded exploratory probes
  - Tier 4 for deferred or preserve-conservative seams
- Tier 1 is now also concrete enough to execute without another planning-only pass:
  - `T1-A` has now been executed once and came back flat
  - `T1-B` phrase dataset/scope is now the immediate next package
  - `T1-C` evaluation rules riding alongside both

## Decision log

Use this section to record the result of each completed triage turn.

| Date | ID | Decision | Why | Follow-up |
| --- | --- | --- | --- | --- |
| `2026-04-23` | `DOC-1` | `do_now` | the weakness story was too distributed across docs and artifacts, and centralizing it had low risk with immediate payoff for later turns | keep this ledger current; next triage slice is `BG-2` plus `BG-3` |
| `2026-04-23` | `BG-1` | `instrument_first` | seed admission still matters, but the big seed-side gains are already captured by one-word forward-gloss seeds and the borrowed-trigger lane; the remaining seed frontier is now smaller and family-local | next turn should move to `RT-1`; if blocker-generation work resumes first, start with a narrow `seed_missing` audit rather than broad trigger expansion |
| `2026-04-23` | `BG-2` | `instrument_first` | candidate coverage is still a real weakness, but current evidence says it is now a smaller, family-local frontier rather than the main broad bottleneck | next turn should classify the remaining hard families by exact miss class and source lane |
| `2026-04-23` | `BG-3` | `experiment_next` | promotion remains the main immediate frontier, and the current knob frontier appears saturated enough that new discriminative features are more promising than more resweeps | next turn should build a short ranked queue of promotion-feature ideas tied to the `3.0-4.0` miss band |
| `2026-04-23` | `BG-4` | `do_now` | the remaining hard families no longer belonged to one queue, and centralizing the family map immediately clarified which issues are promotion-dominant, mixed, or phrase-dominant | next turn should triage `PH-1`, then return to promotion-feature design with the family routing fixed |
| `2026-04-23` | `PH-1` | `experiment_next` | the phrase lane is already high-leverage and clearly separable, but the current implementation is still too narrow and heuristic to count as solved | next turn should return to `BG-3` and design promotion features without using phrase-sensitive rows as a generic blocker proxy |
| `2026-04-23` | `BG-3 queue` | `do_now` | the promotion frontier needed a ranked queue before more experiments; current evidence now clearly separates the control row, the secondary underexplored frequency lane, and the already-exhausted resweep lanes | next turn should move to `BG-5`, then return to rank `1` and rank `2` promotion work only |
| `2026-04-23` | `BG-5` | `defer` | source-heavy and bridge-heavy work is still real, but current evidence says it is a secondary offline research lane rather than the next default-facing blocker frontier; the audited gap has collapsed to one bridge-needed row and the current embedding bridge is still either flat or too noisy | next turn should close the blocker-generation map by triaging `BG-1`, then move on to runtime-scorer weaknesses |
| `2026-04-23` | `RT-1` | `experiment_next` | runtime context is a real frontier, but the current evidence says the answer is not raw-context widening; `masked_sentence` is the best current safe control and the remaining problem is richer masked context for the zero-margin active rows | next turn should triage `RT-2` and `RT-4`, then return to `RT-3` once the runtime surfaces are separated |
| `2026-04-23` | `RT-2` | `instrument_first` | evidence representation is still underpowered and only partly exercised; `all_evidence_text` is the only current winner, while `sense_label`, `gloss_text`, and the one-turn `sense_gloss_bundle` probe all collapse into near-total abstain behavior | next turn should move to `RT-3`; if evidence work resumes before that, extend the canonical sweep before changing defaults |
| `2026-04-23` | `RT-3` | `experiment_next` | the current policy is safe but mostly binary, and threshold tuning is close to exhausted; the next meaningful work is offline comparison of richer decision ladders, not more tiny threshold changes | next turn should move to `CAL-1`, keeping `soft_affordance` as an explicit product-contract question rather than hiding it inside replace tuning |
| `2026-04-23` | `RT-4` | `defer` | active rescue exists, but the one-turn probe shows that it is inert on the current frontier row and only fires in clearly worse threshold regions | next turn should move to `CAL-1`, not rescue tuning |
| `2026-04-23` | `CAL-1` | `instrument_first` | calibration is real, but current confidence bounds, dataset size, and product behavior are still too immature for a true calibrated runtime layer; the right immediate move is calibration reporting, not calibrated rollout behavior | next turn should move to `EVAL-1` and `EVAL-2`, then only revisit calibration once the confidence corridor tightens |
| `2026-04-23` | `EVAL-1` | `experiment_next` | the repo already has the right held-out evaluation concept, but the corridor is still too loose for strong claims; more held-out breadth is now a real blocker for confidence | next turn should move to `EVAL-2`, then `OPS-1` |
| `2026-04-23` | `EVAL-2` | `experiment_next` | dataset growth is now justified, but it should stay targeted and family-driven rather than expanding into one large undifferentiated benchmark bucket | next turn should move to `OPS-1` with the evaluation gaps now explicit |
| `2026-04-23` | `OPS-1` | `defer` | the publication/runtime seam is already correctly conservative and more mature than the current blocker-quality frontier; the main risk is widening it too early, not failing to add more plumbing right now | next turn should move to `TECH-1`, then convert the finished first-pass triage into an execution-priority matrix |
| `2026-04-23` | `TECH-1` | `instrument_first` | stronger semantic tech is still real, but only in bounded abstain-biased roles tied to concrete failure buckets; the repo should study it through a narrow micro-matrix, not through generic model substitution | next turn should convert Tier `1` into a concrete execution package, starting with `BG-3` rank `1`, `PH-1`, and targeted `EVAL-2` growth |
| `2026-04-23` | `T1-B Phase 1` | `do_now` | the smallest phrase-lane dataset patch is now landed with frozen tune/held-out family choices, explicit failure-bucket tags, and no scorer-surface drift | next turn should run `T1-B` Phase `2` on `v3` before any phrase-heuristic claim is accepted |
| `2026-04-23` | `T1-B Phase 2 baseline` | `instrument_first` | the `v3` sweep shows the phrase slice is already effectively solved on the strong safe sentence-transformer lane, while the current bound/reporting surfaces still measure older control/reference rows; new phrase heuristics are not the next justified move | next turn should align scorer, policy, and bound surfaces around the real winning row before any runtime-default or phrase-heuristic claim is accepted |
| `2026-04-23` | `Runtime reference alignment` | `do_now` | the bound/reporting surface now measures the actual conservative runtime control and the actual winning sentence-transformer candidate lane, so runtime-policy discussion can stop relying on mismatched artifacts | next turn should decide whether the candidate lane remains advisory-only or moves into a bounded runtime-policy/default experiment |
| `2026-04-23` | `Runtime default decision` | `do_now` | the aligned `v3` candidate lane now materially outperforms the lexical control on the fixed-shadow slice while preserving a `0.0%` harmful-replace ceiling, and the helper environment already supports the sentence-transformer runtime path | next turn should keep `v3` fixed as the bounded default, keep `v2` as the explicit lexical control, and return to `RT-3` decision-ladder work plus held-out monitoring |
| `2026-04-23` | `RT-3 ladder baseline` | `do_now` | the first bounded three-way probe over the frozen `v3` default shows only one clean soft-affordance candidate, `plant:002`, at `soft:a=0.58:m=-0.03`; there is no evidence yet for a broader soft lane on the fixed-shadow slice | next turn should keep visible `soft_affordance` product work deferred, and move to held-out confidence work using the fixed default and fixed zero-noise soft row as references |
| `2026-04-23` | `EVAL-1 runtime held-out baseline` | `do_now` | the cluster-aware bound now carries both the fixed sentence-transformer default and the fixed zero-noise soft ladder across tune and held-out families; runtime-side confidence is materially tighter, while blocker-generation confidence remains loose | next turn should move to `EVAL-2` targeted family growth rather than another corridor-only pass |
| `2026-04-23` | `EVAL-2 targeted family growth` | `do_now` | the `v4` fixed-shadow slice is now landed with `branch` as a clean breadth family and `park` as a held-out weak-active-support cross-POS family; the result is more honest held-out coverage rather than a prettier headline, because the hard row now misses both `plant:002` and `park:001` while the zero-noise soft row still only recovers `plant:002` | next turn should keep `v4` fixed and move to a narrow runtime probe for park-like weak-active-support cross-POS misses rather than broader soft-rollout or dataset-growth work |
| `2026-04-23` | `RT-3 weak-active probe` | `do_now` | the direct primary-surface alternatives (`sense_label`, `raw_sentence`, `raw_window`) do recover `park:001`, but each introduces `2-3` harmful replaces on the same frozen slice; the first clean runtime signal is a bounded rescue-overlay simulation that widens the trigger floor to `-0.05` while keeping a `sense_label` backup, recovering `ball:002`, `plant:002`, and `park:001` with `0` harmful replaces on `v4` | next turn should keep this result in the offline-analysis lane, treat weak-active-support misses as an evidence-routing / rescue-gating frontier, and verify that the signal survives more held-out breadth before any runtime-policy change |
| `2026-04-23` | `RT-3 widened-rescue bound` | `do_now` | the generalization-bound surface now carries an explicit widened-rescue simulated lane projected over the current sentence-transformer default; on the current fixed-shadow `v4` tune/held-out split it remains perfect with `100.0%` replace-recall conservative floors and `0.0%` harmful-replace / false-abstain ceilings, so the rescue-gating hypothesis now survives the current corridor as well as the point-estimate probe | next turn should keep this lane explicitly simulated, avoid changing runtime policy yet, and move to targeted held-out rescue-gating family growth before any rollout decision |
| `2026-04-23` | `EVAL-2 targeted family growth v5` | `do_now` | the `v5` fixed-shadow slice adds `drink` on the tune side and `play` on the held-out side; `drink` widens the weak-active-support slice cleanly, but `play:005` becomes the first harmful replace on both the strong sentence-transformer reference row and the widened-rescue overlay, while `play:002` remains a false abstain | next turn should stop defaulting to more family growth, keep `v5` fixed, and move to a narrow `PH-1` / `RT-3` phrase-leak probe |
| `2026-04-23` | `PH-1 reopened by v5` | `experiment_next` | `v5` invalidates the earlier “phrase slice is effectively safe on the strong runtime lane” posture on the active fixed-shadow slice; the new frontier is a cross-POS lexicalized-expression leak, not generic weak-active-support residue | next turn should test phrase-leak containment against `play:005` without losing the genuine rescue wins on `drink`, `park`, and `play:001` |
| `2026-04-23` | `PH-1 / RT-3 phrase-leak probe` | `do_now` | the new phrase-leak probe shows that the current family-wide POS gate is the direct cause of the `play:005` leak on mixed noun/verb families; anchoring phrase control to the active noun POS removes `play:005` on both the hard row and the widened overlay while preserving the current rescue wins, but it also broadens phrase-preemption hits across mixed noun/verb shadow rows like `play:004`, `drink:003`, and `park:003` | next turn should decide whether that broader mixed noun/verb phrase-preemption semantics is acceptable enough for a bounded runtime-reference experiment before adding more held-out families |
| `2026-04-23` | `PH-1 / RT-3 bounded candidate review` | `do_now` | the held-out bound now resolves the acceptability question more precisely: the active-sense hard lane removes the `7.1%` harmful-replace ceiling but softens the conservative hard corridor from `75.0%` to `71.4%` replace recall and from `25.0%` to `28.6%` false-abstain, while the active-sense overlay keeps the `89.3%` replace-recall floor and `10.7%` false-abstain ceiling while dropping the harmful-replace ceiling from `7.1%` to `0.0%` | next turn should keep the hard reference fixed, keep the active-sense overlay as the preferred bounded experiment, and resume held-out family growth plus corridor tightening |
| `2026-04-23` | `EVAL-2 targeted family growth v6` | `do_now` | the `v6` fixed-shadow slice adds `watch` as a second held-out mixed noun/verb phrase-risk family; it does not change the hard-reference failure class or the narrow zero-noise soft lane, but it shows the active-sense overlay still removes the harmful ceiling while preserving a `90.0%` replace-recall conservative floor and `10.0%` false-abstain ceiling on the current corridor | next turn should keep `v6` fixed, keep the hard reference and active-sense overlay frozen, and resume targeted held-out family growth rather than more phrase-leak-only diagnosis |
| `2026-04-23` | `EVAL-2 targeted family growth v7` | `do_now` | the `v7` fixed-shadow slice adds `check` as a held-out weak-active-support noun/verb family; it does not create a new phrase-leak harmful row, but it does add `check:002` as a new held-out false-abstain residue while keeping `play:005` as the only harmful replace on the plain hard and widened-rescue lanes | next turn should keep `v7` fixed, keep the hard reference and accepted active-sense overlay frozen, and continue held-out family growth plus corridor tightening with `check:002` tracked as weak-active-support residue rather than reopening generic phrase-leak diagnosis |
| `2026-04-23` | `EVAL-2 targeted family growth v8` | `do_now` | the `v8` fixed-shadow slice adds `order` as a held-out weak-active-support noun/verb family; it does not create a new phrase-leak harmful row, but it does add `order:002` as another held-out false-abstain residue while keeping `play:005` as the only harmful replace on the plain hard and widened-rescue lanes, and it is the first new held-out residue that cleanly joins the zero-noise soft ladder | next turn should keep `v8` fixed, keep the hard reference, zero-noise soft row, and accepted active-sense overlay frozen, and continue held-out family growth plus corridor tightening with `check:002` and `order:002` tracked as weak-active-support residue rather than reopening generic phrase-leak diagnosis |
| `2026-04-23` | `EVAL-2 targeted family growth v9` | `do_now` | the `v9` fixed-shadow slice adds `trip` as a held-out weak-active-support noun/verb family; it does not create a new phrase-leak harmful row, but it does add `trip:002` as another held-out false-abstain residue while keeping `play:005` as the only harmful replace on the plain hard and widened-rescue lanes, and it is the second new held-out residue that cleanly joins the zero-noise soft ladder | next turn should keep `v9` fixed, keep the hard reference, zero-noise soft row, and accepted active-sense overlay frozen, and continue held-out family growth plus corridor tightening with `check:002`, `order:002`, and `trip:002` tracked as weak-active-support residue rather than reopening generic phrase-leak diagnosis |
| `2026-04-24` | `EVAL-2 targeted family growth v10` | `do_now` | the `v10` fixed-shadow slice adds `report` as a held-out weak-active-support noun/verb family; it does not create a new phrase-leak harmful row, but it does add `report:001` and `report:002` as new held-out false-abstain residue while keeping `play:005` as the only harmful replace on the plain hard and widened-rescue lanes, and it collapses the current zero-noise soft ladder back to a pure monitoring control | next turn should keep `v10` fixed, stop defaulting to more family growth, and move to the queue-backed pre-prompt data path |
| `2026-04-24` | `Pre-prompt family inventory and queue freeze` | `do_now` | the repo now has the first concrete family inventory, sampled queue review, frozen bakeoff queue, and frozen prompt-slot manifest for the active `v10` runtime slice; current first-tranche targets are cue-heavy (`check`, `order`, `trip`, `report`) with `play` and `watch` held as guardrail families | next turn should run a tiny `example_sentence_bank` cue-data pilot on that frozen queue before any paid prompt smoke pass |
| `2026-04-24` | `Pre-prompt example_sentence_bank feasibility pilot` | `do_now` | the new pilot shows that the current installed packs expose `0 / 6` target families with queued-family example rows on the frozen `v10` queue, while all `6 / 6` target families do expose reverse-side auxiliary sense text; so a true example-backed control is not currently available on this machine without dedicated source ingestion | next turn should either run a reverse-aux-text cue pilot as the last non-LLM control before prompt spend or explicitly accept prompt bakeoff without a live example-source control |
| `2026-04-24` | `Pre-prompt reverse-aux-text queue pilot` | `do_now` | the new reverse-aux-text pilot shows that `reverse_aux_plus_all_evidence` is a real cheap control on the frozen `v10` prompt slice: it improves the point read from `77.5%` accuracy / `50.0%` replace recall / `1` harmful / `8` false abstains to `82.5%` / `62.5%` / `1` / `6`, fixing `plant:002`, `drink:002`, and `order:002` while leaving `play:005` as the live harmful row | next turn should keep that row frozen as the last non-LLM control and move into the actual prompt bakeoff |
| `2026-04-24` | `Pre-prompt prompt smoke bundle` | `do_now` | the repo now has the first concrete prompt wording bundle for the frozen `v10` queue: `semantic_prompt_bakeoff_v1` with proxy `gpt-5.4-mini`, target `gpt-5.4`, and `6` rendered request rows across the `2` active cue slots, so prompt work is now an execution surface rather than a plan-only seam | next turn should run the actual cheap proxy batch on a configured API surface rather than reopen queue design or add more local prompt variants first |
| `2026-04-24` | `Pre-prompt prompt runner implementation` | `do_now` | the repo now has the real prompt execution runner in `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`; it preserves immutable raw response bundles plus raw and normalized batch artifacts for each run while keeping a stable `latest` summary, so paid prompt test data no longer disappears into terminal output | next turn should review the runner, then run the first proxy batch once the configured account exposes usable quota |
| `2026-04-24` | `Pre-prompt prompt preflight, spend guard, and cost estimate` | `do_now` | the repo now has a no-spend preflight surface in `scripts/testing/semantic_llm_prompt_preflight_en_es.py`, a no-spend cost-estimate surface in `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py`, and the live runner now requires explicit `--execute-live`; the current preflight artifact resolves to `sourced-shell-ready` rather than direct-shell-ready, and the current proxy cost-estimate artifact keeps the token-volume review explicit before any live call | next turn should review the preflight and cost artifacts first, then only run a live proxy batch from a sourced-shell/account path that is both env-ready and quota-ready |
| `2026-04-24` | `Pre-prompt prompt replay rehearsal` | `do_now` | the same bakeoff runner now has a strict replay path backed by `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`, and the replay rehearsal in `docs/test_outputs/semantic_llm_prompt_replay_latest.md` proved the preserved-batch plumbing end to end: one accepted request normalized cleanly, one malformed row was rejected while staying raw-only, and one forced API failure was counted separately without corrupting the batch | next turn can move to real prompt execution once quota is available, because the remaining unknown is live model/account behavior rather than local preservation plumbing |
| `2026-04-24` | `Pre-prompt live spend hard-stop guards` | `do_now` | the live bakeoff runner now fails closed unless the operator declares the exact selected request count, explicit pricing inputs, and an explicit estimated cost ceiling; preflight now prints a spend-capped command template instead of an uncapped live command, so a queue/filter drift cannot silently widen a paid run | next turn can run the one-request plumbing smoke and the six-request proxy run with explicit caps once the account path is quota-ready |
| `2026-04-24` | `Pre-prompt resume-safe journaling` | `do_now` | the live bakeoff runner now also uses an append-only per-request journal keyed by explicit `--run-id`, can reuse completed outcomes under `--resume`, and intentionally refuses resume when a request was started without a recorded outcome so interruption handling stays fail-closed against duplicate spend | next turn can use the one-request smoke and six-request proxy run with explicit `--run-id`, and any interrupted run should be resumed only through the recorded journal path |
| `2026-04-24` | `Live proxy rerun on simplified prompt contract` | `do_now` | `semantic_prompt_bakeoff_v2` now has a real live proxy result on the frozen `v10` queue: `6 / 6` accepted and normalized again, but with materially lower token usage (`3414 -> 2545` input, `1137 -> 222` output) and visibly better cross-POS framing cues on `check`, `order`, `trip`, and `report`; the simpler contract therefore looks strictly better than the verbose `v1` proxy contract | next turn should move to target confirmation on the simplified contract rather than reopening the verbose output shape |
| `2026-04-24` | `Live target confirmation on simplified prompt contract` | `do_now` | `semantic_prompt_bakeoff_v2` now also has a real live `gpt-5.4` target result on the same frozen `v10` queue: `6 / 6` accepted and normalized, token usage stayed close to proxy (`2545` input, `231` output), and the cross-POS cues remained frame-sensitive instead of regressing to broad noun-gloss summaries; so prompt confirmation is no longer the main open question | next turn should move to the downstream bakeoff on the fixed-shadow runtime slice rather than more prompt-shape iteration |
| `2026-04-24` | `Downstream bakeoff on accepted target cue tranche` | `do_now` | the downstream comparison now shows that the accepted `gpt-5.4` cue tranche is not yet promotion-ready on the frozen `v10` queue slice: the intended safe additive lane (`llm_cue_plus_all_evidence`) stays flat on both the hard row and the active-sense overlay, fixing `drink:002` but introducing `drink:001`, while the stronger LLM cue insertions (`llm_cue_plus_sense_label`, `llm_cue_plus_gloss`) only improve recall by widening harmful replace from `1` to `3`; `reverse_aux_plus_all_evidence` remains the better queue-slice control on both reference lanes | next turn should keep the queue fixed, hold the current accepted cue tranche in analysis-only status, and redesign the next cue prompt around stronger overlap-bearing discriminators before any larger cue-generation spend |
| `2026-04-24` | `Overlap-bearing prompt challenger matrix prep` | `do_now` | the redesign is now concretized as `semantic_prompt_bakeoff_v3` on the same frozen `v10` queue: `4` active proxy slots and `12` requests, with the current `v2` incumbent slots (`cue_contrastive_general_v1`, `cue_cross_pos_frame_v1`) paired against overlap-bearing challengers (`cue_contrastive_overlap_v1`, `cue_cross_pos_overlap_v1`) that explicitly ask for short collocates and frame fragments instead of smoother prose cues | next turn should run the cheap proxy challenger comparison, keep `reverse_aux_plus_all_evidence` as the external control, and only advance slots that clearly beat the incumbents before another target-model pass |
| `2026-04-24` | `Live proxy challenger comparison on overlap matrix` | `do_now` | the first cheap live run on `semantic_prompt_bakeoff_v3` completed cleanly (`12 / 12` accepted and normalized; `5370` input tokens, `414` output tokens) and the overlap challengers are the first prompt variants that visibly shift away from meta-language toward literal anchor fragments such as `soil, water, leaves, roots, sunlight`, `your online order for delivery`, and `annual report with findings, results, and recommendations`; that makes them better-aligned proxy candidates than the incumbent `v2` slot wording, which still leans on `preceded by a determiner`-style phrasing | next turn should run target confirmation on the overlap challenger slots only, then return to the downstream acceptance gate rather than reopening a broader prompt matrix |
| `2026-04-25` | `Live target confirmation on overlap challenger slots` | `do_now` | the narrowed `semantic_prompt_bakeoff_v3` target pass carried forward only `cue_contrastive_overlap_v1` and `cue_cross_pos_overlap_v1`; it completed cleanly on `gpt-5.4` with `6 / 6` requests accepted and normalized, `2825` input tokens, and `179` output tokens, and target outputs preserved the intended literal-overlap shape such as `green leaves, roots in soil`, `write a check to pay the rent`, and `the final report on findings and results` | next turn should judge the accepted overlap tranche only through the downstream acceptance harness, not by proxy/target output aesthetics |
| `2026-04-25` | `Downstream bakeoff on overlap challenger tranche` | `defer` | the refreshed downstream comparison rejects the overlap tranche for promotion: `llm_cue_plus_all_evidence` regresses the hard row to `72.5%` accuracy / `50.0%` replace recall / `3` harmful / `8` false abstains, stays flat on the active-sense overlay at `80.0%` / `50.0%` / `0` / `8`, and only fixes `order:002` while introducing `drink:001`; stronger LLM diagnostic lanes improve recall only by widening harmful replace to `5`, while `reverse_aux_plus_all_evidence` remains the better control at `82.5%` / `62.5%` / `1` / `6` hard and `85.0%` / `62.5%` / `0` / `6` overlay | next turn should stop prompt-only iteration, keep both target cue tranches analysis-only, and reopen paid generation only after a downstream insertion, source-data, or evaluation-lane change gives a concrete path past the reverse-aux control |
| `2026-04-25` | `Prompt failure diagnostic and insertion/source reroute` | `do_now` | the new no-spend diagnostic in `docs/test_outputs/semantic_llm_prompt_failure_diagnostic_latest.md` explains why the prompt-only loop is exhausted: reverse-aux remains the current control (`82.5%` / `62.5%` / `1` / `6`), active-only reverse-aux is weaker (`80.0%` / `56.2%` / `1` / `7`), LLM cue plus all evidence is unsafe/flat (`72.5%` / `50.0%` / `3` / `8`), reverse-aux plus LLM cue is identical to reverse-aux alone, and LLM rescue-only probes do not beat reverse-aux | next turn should treat `scripts/testing/semantic_llm_prompt_failure_diagnostic_en_es.py` as the no-spend gate, then test competition-symmetric source/insertion hypotheses before any more paid prompt generation |
| `2026-04-25` | `Source/insertion symmetry probe` | `do_now` | the new no-spend source/insertion probe in `docs/test_outputs/semantic_llm_source_insertion_probe_latest.md` shows the next source shape more directly: full symmetric reverse-aux remains the only winning no-spend lane (`82.5%` / `62.5%` / `1` / `6`), active-only reverse is weaker (`80.0%` / `56.2%` / `1` / `7`), shadow-only reverse is weaker and less safe (`77.5%` / `56.2%` / `2` / `7`), and active LLM cues plus reverse-shadow calibration are still unsafe/weak (`72.5%` / `56.2%` / `4` / `7`) | next turn should only reopen paid generation for a competition-symmetric source hypothesis that can be rerun through both the failure diagnostic and source/insertion probe before target-model spend |
| `2026-04-25` | `Reviewed example-frame source upper bound` | `do_now` | the source/insertion probe now includes the first concrete competition-symmetric example/frame candidate: hard reviewed example frames remove all false abstains but reopen phrase leaks (`92.5%` / `100.0%` / `3` / `0`), while the same reviewed frames with active-sense phrase guarding reach `100.0%` / `100.0%` / `0` / `0` as an internal non-runtime oracle | next turn should target external or generated active/shadow example-frame evidence with equivalent phrase-leak containment; do not treat reviewed sentence-veto examples as publishable runtime data |
| `2026-04-25` | `Prototype admission and expanded-family guardrail` | `do_now` | the new no-spend prototype-admission probe in `docs/test_outputs/semantic_llm_prototype_admission_probe_latest.md` keeps the UX binary while changing the internal scorer shape: context competes against active/shadow reviewed example prototypes, then emits only `replace` or `abstain`; it clears the frozen queue (`100.0%` / `100.0%` / `0` / `0`), but the expanded full-`v10` run in `docs/test_outputs/semantic_llm_prototype_admission_probe_expanded_latest.md` still has `2` harmful phrase-control leaks (`ball:005`, `match:005`) at `97.9%` / `100.0%` / `2` / `0` | next turn should treat prototype admission as the right internal direction, but expand phrase containment beyond the active-only frame guard before claiming full-suite readiness |
| `2026-04-25` | `Phrase-control prototype guard` | `do_now` | the prototype-admission probe now adds phrase-control reviewed examples as abstain prototypes, so the internal competition is active vs shadow vs phrase-control while the UX still sees only replacement or no replacement; this clears both the frozen queue and the expanded `95`-case `v10` oracle read at `100.0%` / `100.0%` / `0` / `0` | next turn should translate this oracle shape into source requirements for real ingest/generation: active, shadow, and phrase-control examples must be acquired together before any paid prompt source batch is promotion-relevant |
| `2026-04-25` | `Phrase-control source contract` | `do_now` | the canonical semantic intake/evidence schemas and normalizer now accept `relation_type=phrase_control_example` and the `phrase_containment` role, preserving the prototype-admission source requirement in machine-checkable batch rows rather than only prose docs | next turn can design the first no-spend or paid example-frame batch around this source contract; keep rows `runtime_publishable=false` until a separate runtime publication path exists |
| `2026-04-25` | `Example-frame source-contract gate` | `do_now` | the new no-spend gate in `docs/test_outputs/semantic_llm_example_frame_contract_latest.md` checks raw intake or normalized evidence batches for active, shadow, and phrase-control rows per family; the current overlap target batch is intentionally `review`, with `0 / 6` complete families because it only contains active cue rows | next turn should make this contract gate the precondition for any reopened example-frame generation spend, then build the first contract-complete batch fixture or live source run |
| `2026-04-25` | `Reviewed example-frame batch fixture` | `do_now` | the new no-spend batch builder emits reviewed sentence-veto examples as raw intake plus normalized evidence under `docs/test_outputs/experiments/semantic_llm_example_frame_batches/`; the frozen fixture is contract-complete (`8 / 8` families), the full-`v10` fixture is contract-complete (`19 / 19` families), and the prototype-admission probe now consumes those normalized batches directly while preserving the `100.0%` / `100.0%` / `0` / `0` oracle read | next turn should use this fixture shape as the exact target for generated evidence, not as runtime data; the remaining implementation work is generating external/LLM rows that satisfy the same contract without reviewed-case leakage |
| `2026-04-25` | `Required-family source-contract gate` | `do_now` | the example-frame contract gate now accepts `--required-family-json`, so a batch can be judged against the frozen queue or dataset family set rather than only against families present in the batch; the reviewed frozen fixture still passes with `8 / 8` required families in `docs/test_outputs/semantic_llm_example_frame_contract_required_latest.md` | next turn should use required-family mode for all promotion-relevant example-frame batches so a cherry-picked complete subset cannot pass as a complete source |
| `2026-04-25` | `Reverse-aux external example-frame batch` | `experiment_next` | `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py` now emits a real non-LLM source batch from installed reverse auxiliary sense text; it produces `13` rows and covers active reverse-aux text for all `6 / 6` target families and shadow reverse-aux text for `4 / 6`, but the required-family contract read is still `review` with `0 / 8` complete families because `plant` and `check` lack shadow rows and all families lack phrase-control examples | next turn should route exactly the missing shadow and phrase-control rows to dedicated source ingestion or a narrow example-frame LLM generator before any runtime publication claim |
| `2026-04-25` | `Missing-row example-frame generation plan` | `do_now` | `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py` now turns the reverse-aux required-family contract gap into a no-spend generation plan with exactly `11` requests: `1` active row for `play`, `2` shadow rows for `plant`/`check`, and `8` phrase-control rows; prompt input excludes reviewed case sentences and translation targets | next turn should execute those requests only under explicit live/replay guards, normalize accepted rows, merge them with the reverse-aux batch, and rerun the required-family contract plus prototype-admission/source-insertion gates |
| `2026-04-25` | `Live missing-row generation quality gate` | `defer` | the live missing-row run accepted and normalized `11 / 11` rows and the merged reverse-aux plus generated batch is structurally complete (`8 / 8` required families, `24` rows), but `docs/test_outputs/semantic_llm_example_frame_generation_quality_gate_latest.md` rejects it as analysis-only: best prototype config is only `67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains, with broad phrase-control prototypes adding `2` false abstains beyond the active-guard baseline | next turn should stop missing-row-only generation and change the source shape: generate balanced active/shadow exemplar sets and keep phrase-control examples out of broad semantic prototype competition unless they are converted into containment patterns or separately gated abstain evidence |
| `2026-04-25` | `Phrase containment ablation for generated rows` | `do_now` | `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py` now includes a containment-only phrase-control config and keeps the broad phrase-prototype config as a negative control; on the merged generated batch, broad phrase scoring puts phrase-overreach pressure on `12` active false-abstain rows and directly adds `2` incremental false abstains, while containment-pattern scoring adds `0` incremental false-abstains and gets `2` correct containment hits, so `docs/test_outputs/semantic_llm_example_frame_generation_quality_gate_latest.md` now chooses `prototype_reviewed_examples_phrase_containment_guard` as the best analysis-only config at `67.5%` / `31.2%` / `2` / `11` | next turn should treat the phrase branch as structurally solved for this batch and work on the real blocker: balanced active/shadow source exemplars for the false-abstain families and the harmful `report` shadow cases |
| `2026-04-25` | `Residual source remediation plan` | `do_now` | `scripts/testing/semantic_llm_example_frame_remediation_plan_en_es.py` converts the containment-aware residuals into a no-spend request set in `docs/test_outputs/semantic_llm_example_frame_remediation_plan_latest.md`: `8` requests across `7` families, with `7` active examples for the `11` false-abstain cases and `1` shadow example for the `2` harmful `report` cases; prompts include residual case ids and slice tags but not benchmark sentence text | next turn can either run this narrow source plan under explicit live guards or first add a replay fixture/merge gate for remediation batches so generated rows are evaluated before any promotion claim |
| `2026-04-25` | `Generated-row leakage admission` | `do_now` | `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py` now audits generated example-frame batches against sentence-veto benchmark cases before merge, including full token-sequence containment and shared contiguous benchmark spans; the first residual run accepted `8 / 8` rows but filtered one `plant` near-copy, and the second rekeyed/replayed run accepted `6 / 6` rows but filtered one shared-span `plant` row | next turn should keep leakage admission mandatory for generated example-frame rows and avoid treating accepted LLM output count as admitted source count |
| `2026-04-25` | `Surface-POS prototype guard` | `do_now` | `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py` now includes `prototype_reviewed_examples_surface_pos_rescue_guard`, which keeps the UX binary, keeps phrase-control rows as local containment patterns, and uses surface syntax to rescue noun-frame active cases while preempting verb-frame shadow cases; `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_quality_gate_latest.md` now passes at `95.0%` accuracy / `87.5%` recall / `0` harmful / `2` false abstains with `8 / 8` required families complete | next turn should treat this as a promotion-candidate offline source/scorer configuration, then validate generalization before any runtime default or publication claim; remaining misses are the same-POS `plant` rows |
| `2026-04-25` | `Surface-POS generalization and planner correction` | `do_now` | `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_generalization_probe_latest.md` validates the surface-POS guard across the full `95`-case `v10` dataset with `0` harmful replacements and `5` correct active rescues, while making clear that all-family recall is source-coverage-limited; `scripts/testing/semantic_llm_example_frame_remediation_plan_en_es.py` now auto-selects the best remediation-eligible prototype config instead of the stale phrase-containment config, so `docs/test_outputs/semantic_llm_example_frame_plant_remediation_plan_latest.md` narrows the next source plan to `1` active `plant` request | next turn should keep this auto-selected planner path and avoid spending on residual rows already solved by the surface-POS guard |
| `2026-04-25` | `Canonical generated-row leakage admission` | `do_now` | `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py` now canonicalizes person and determiner substitutions before containment checks, catching `I/my` rewrites of reviewed examples that exact token-span checks missed; the existing plant remediation audit now rejects the previously accepted `I watered the plant on my windowsill every morning` row | next turn should treat canonical leakage as the source-admission floor for any generated example-frame row before merge or prototype scoring |
| `2026-04-25` | `Plant-only source retry` | `defer` | two bounded live plant remediation attempts were executed under explicit request-count and spend guards in `docs/test_outputs/semantic_llm_example_frame_plant_remediation_run_latest.md` and `docs/test_outputs/semantic_llm_example_frame_plant_remediation_v2_run_latest.md`; both normalized one active row, but `docs/test_outputs/semantic_llm_example_frame_plant_remediation_leakage_audit_latest.md` and `docs/test_outputs/semantic_llm_example_frame_plant_remediation_v2_leakage_audit_latest.md` filtered both as canonical benchmark-near-copies, leaving `0` admitted plant rows and no improvement over the prior `95.0%` / `87.5%` / `0` / `2` quality gate | next source attempt should not be another single generic plant prompt; it needs split multi-example generation with pre-merge non-overlap validation, a different source family, or a deliberately source-backed same-POS discrimination strategy |
