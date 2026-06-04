# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `seed_pass_expand_inventory`
- Generated: `2026-04-29T00:16:20Z`
- Promotion readiness: `ready_for_broader_breadth`
- Quality-gate distance: `breadth_and_residual_tracking`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_non_v10_wave5_phrase_probe_latest`
- Admission semantic contract: `16` / `16`
- Admission final rows: `58`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave5_portfolio_heldout_margin005_validation_latest`
- Held-out cases: `32` across `16` families
- Held-out harmful / false abstain: `0` / `0`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `primary_phrase_contract_gap` | `9` | `False` | `True` | `dry, look, mean, offer, plain, present, quiet, sign, train` |
| `comparator_phrase_contract_gap` | `16` | `False` | `True` | `answer, change, dry, end, fast, land, look, mean, offer, plain, present, quiet, rest, sign, train, use` |
| `margin_policy_blockers` | `5` | `False` | `True` | `present, rest` |

## Leverage And Overfit Boundary

- Source rows: `51`
- Source families: `16`
- Held-out cases per admitted row: `0.8276`
- Families needed before broad-confidence claim: `34`
- Cases needed before broad-confidence claim: `152`
- Source-mode false-abstain delta: `0`
- Source-mode sense-reject delta: `0`

## Quality Gate Distance

- Blockers: `none`
- Tracked residuals: `phrase_contract_gap`, `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest` | `0` | `16` / `16` | `0` | `0` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave5_portfolio_phrase_margin005_validation_latest` | `non_v10_wave5_source_portfolio_phrase_no_winner` | `16` | `16` | `0` | `0` | `1.0000` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_non_v10_source_portfolio_wave5_anypos_latest` | `source_portfolio_materialized` | `16` | `51` | `0` | `0` |
| `semantic_wordnet_phrase_control_non_v10_wave5_portfolio_latest` | `phrase_control_rows_mined` | `7` | `7` | `0` | `0` |

## Margin Sweep

- Decision: `margin_candidate_found`
- Recommended margin: `0.0`
- Passing margins: `0.0, 0.001, 0.005, 0.01, 0.02`

## Next Steps

- build automatic non-v10 inventory candidate generation instead of tuning this small slice further
- run WordNet definition-preferred extraction across the expanded inventory and rerun admission
- use this mining report to separate reusable failure clusters from one-off manual cases
- keep phrase containment as a tracked residual lane until source data or policy exists for it
