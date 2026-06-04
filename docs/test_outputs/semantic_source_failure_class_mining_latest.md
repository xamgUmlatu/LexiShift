# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `seed_pass_expand_inventory`
- Generated: `2026-04-27T21:54:27Z`
- Promotion readiness: `ready_for_broader_breadth`
- Quality-gate distance: `breadth_and_residual_tracking`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest`
- Admission semantic contract: `8` / `8`
- Admission final rows: `18`
- Seed ablation harmful / false abstain: `0` / `4`
- Held-out: `semantic_source_non_v10_heldout_v1_margin005_validation_latest`
- Held-out cases: `16` across `8` families
- Held-out harmful / false abstain: `0` / `0`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `primary_seed_false_abstain` | `4` | `False` | `True` | `date, point, rock` |
| `primary_phrase_contract_gap` | `8` | `False` | `True` | `case, date, draft, line, point, ring, rock, scale` |
| `comparator_sense_reject` | `4` | `False` | `True` | `competitor_sense_not_lower` |
| `comparator_semantic_contract_gap` | `4` | `False` | `True` | `case, date, point, rock` |
| `comparator_seed_false_abstain` | `7` | `False` | `True` | `case, date, point, rock` |
| `comparator_phrase_contract_gap` | `8` | `False` | `True` | `case, date, draft, line, point, ring, rock, scale` |
| `margin_policy_blockers` | `12` | `False` | `True` | `ball, bank, board, file, plant, seal, table` |

## Leverage And Overfit Boundary

- Source rows: `18`
- Source families: `8`
- Held-out cases per admitted row: `0.8889`
- Families needed before broad-confidence claim: `42`
- Cases needed before broad-confidence claim: `184`
- Source-mode false-abstain delta: `-3`
- Source-mode sense-reject delta: `-4`

## Quality Gate Distance

- Blockers: `none`
- Tracked residuals: `seed_ablation_false_abstain`, `phrase_contract_gap`, `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest` | `4` | `4` / `8` | `0` | `7` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_wordnet_def_source_non_v10_probe_v1_latest` | `definition_preferred` | `8` | `18` | `0` | `0` |
| `semantic_wordnet_source_non_v10_probe_v1_latest` | `example_preferred` | `8` | `18` | `0` | `0` |

## Margin Sweep

- Decision: `margin_candidate_found`
- Recommended margin: `0.005`
- Passing margins: `0.005, 0.01`

## Next Steps

- build automatic non-v10 inventory candidate generation instead of tuning this small slice further
- run WordNet definition-preferred extraction across the expanded inventory and rerun admission
- use this mining report to separate reusable failure clusters from one-off manual cases
- keep phrase containment as a tracked residual lane until source data or policy exists for it
