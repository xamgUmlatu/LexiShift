# en-es Semantic Shadow Campaign C Conclusion

- Campaign scope: source-convergence promotion feature after Campaign B showed the old late-node knobs were saturated
- New implementation changes:
  - merge duplicate shadow candidates across source lanes instead of dropping later evidence
  - add candidate-level source-convergence support keyed to explicit `reverse_lookup + forward_index` agreement
- Evidence artifacts:
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.json`
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.json`
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`

## Best current row

- `promotion_multi_source_candidate_1_5`

Metrics versus current borrowed baseline:

- baseline `source_only_borrowed`
  - gold precision / recall: `78.6%` / `44.0%`
  - veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
  - harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`

- `promotion_multi_source_candidate_1_5`
  - gold precision / recall: `75.0%` / `48.0%`
  - veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
  - harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`

## What improved

- the new source-convergence feature is not inert
- it improves both direct overlap recall and veto-shaped behavior
- it cuts harmful allow by about six points
- it increases abstain recall by about six points
- it does so with a relatively small overblocking increase versus the borrowed baseline

## Why the stricter convergence definition matters

The first version treated any two source lanes as convergence.
That improved recall, but overblocking rose too much.

The refined version only rewards explicit `reverse_lookup + forward_index` agreement.
That keeps most of the gain while reducing the overblocking cost materially.

## Updated promotion-gap read

Under the refined `multi_source_candidate_support=1.5` row:

- `33` gold trigger rows total
- `19` rows hit a gold blocker
- `7` rows are `promotion_miss`
- `7` rows are `candidate_missing`

Remaining promotion-miss families:

- `net_mesh_network`
- `field_area_country`
- `job`
- `table_board_chart`

Promotion-miss score bands still cluster at:

- `4.0`
- `3.5`
- `3.0`
- one harder `1.5` case

## Frontier decision

- source-convergence support is a viable new late-feature family
- it is the best current promoted-feature row in this workstream
- the next likely promotion feature should target the remaining `3.0-4.0` misses in `net_mesh_network` and `field_area_country`
- candidate generation is still incomplete, but the immediate frontier remains promotion evidence rather than seed admission
