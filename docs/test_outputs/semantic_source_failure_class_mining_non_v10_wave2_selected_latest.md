# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `seed_pass_expand_inventory`
- Generated: `2026-04-27T22:53:48Z`
- Promotion readiness: `ready_for_broader_breadth`
- Quality-gate distance: `breadth_and_residual_tracking`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest`
- Admission semantic contract: `8` / `8`
- Admission final rows: `30`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave2_selected_heldout_margin005_validation_latest`
- Held-out cases: `16` across `8` families
- Held-out harmful / false abstain: `0` / `0`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `primary_sense_reject` | `8` | `False` | `True` | `competitor_sense_not_lower` |
| `primary_phrase_contract_gap` | `8` | `False` | `True` | `answer, land, look, offer, rest, sign, train, use` |
| `comparator_sense_reject` | `7` | `False` | `True` | `competitor_sense_not_lower` |
| `comparator_semantic_contract_gap` | `1` | `False` | `True` | `end` |
| `comparator_phrase_contract_gap` | `8` | `False` | `True` | `end, land, look, offer, quiet, sign, train, use` |

## Leverage And Overfit Boundary

- Source rows: `38`
- Source families: `8`
- Held-out cases per admitted row: `0.8000`
- Families needed before broad-confidence claim: `42`
- Cases needed before broad-confidence claim: `176`
- Source-mode false-abstain delta: `0`
- Source-mode sense-reject delta: `1`

## Quality Gate Distance

- Blockers: `none`
- Tracked residuals: `sense_filter_rejects`, `phrase_contract_gap`, `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_draft_latest` | `7` | `7` / `8` | `0` | `0` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave2_selected_phrase_margin005_validation_latest` | `non_v10_wave2_admission_selected_phrase_no_winner` | `8` | `8` | `0` | `0` | `1.0000` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_wordnet_def_ex_non_v10_wave2_selected_latest` | `definition_and_example` | `8` | `38` | `0` | `0` |
| `semantic_wordnet_def_ex_non_v10_wave2_draft_latest` | `definition_and_example` | `8` | `34` | `0` | `0` |

## Margin Sweep

- Decision: `margin_candidate_found`
- Recommended margin: `0.0`
- Passing margins: `0.0, 0.001, 0.005, 0.01, 0.02, 0.05`

## Next Steps

- build automatic non-v10 inventory candidate generation instead of tuning this small slice further
- run WordNet definition-preferred extraction across the expanded inventory and rerun admission
- use this mining report to separate reusable failure clusters from one-off manual cases
- keep phrase containment as a tracked residual lane until source data or policy exists for it
