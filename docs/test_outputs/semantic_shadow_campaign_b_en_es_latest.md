# en-es Semantic Shadow Campaign B Conclusion

- Campaign scope: late-node promotion ablations on top of the borrowed-seed baseline
- Baseline row: `source_only_borrowed`
- Evidence artifacts:
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.json`
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.json`
  - `docs/test_outputs/semantic_shadow_promotion_gap_en_es_latest.md`

## Winning rows

- No late-node ablation row beat `source_only_borrowed`.
- The borrowed baseline remains the best current source-only operating point in this campaign.

Baseline metrics:

- gold candidate precision / recall: `84.0%` / `42.0%`
- veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `51.5%` / `48.5%` / `2.1%`
- harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`

## Harmful rows

- `promotion_min_4`
  - lowering the support threshold increases abstain recall slightly, but precision collapses and overblocking jumps to `21.1%`
  - this is not a viable trade

- `promotion_min_6`
  - raising the threshold collapses promotion entirely
  - abstain recall falls to `0.0%` and harmful allow rises to `100.0%`

- `promotion_same_pos_off`
  - removing the same-POS reward is catastrophic
  - it produces the same failure pattern as an overly strict threshold

- `promotion_active_profile_off`
  - this regresses the borrowed baseline back toward the weaker non-borrowed behavior
  - abstain recall falls to `42.4%`
  - harmful allow rises to `57.6%`

## Flat rows

- `promotion_top1`
- `promotion_top3`
- `promotion_forward_support_off`
- `promotion_forward_support_half`
- `promotion_forward_support_high`
- `promotion_same_pos_high`
- `promotion_active_profile_high`
- `promotion_semantic_bridge_off`
- `promotion_semantic_bridge_high`
- `promotion_cross_pos_penalty_off`
- `promotion_cross_pos_penalty_strong`

These rows are effectively flat on the main gold and veto surfaces.
They do not open a new late-node frontier point.

## Node conclusions

- `support_score_min=5` remains the current Pareto point.
- `same_pos_as_active` is required, not optional.
- `active_profile_support` matters when active evidence is sparse or missing.
- the current forward-support, semantic-bridge-support, and cross-POS-penalty weights are mostly inert on this benchmark slice
- `support_score_max_promoted` is mostly a gold-overlap knob here, not a veto-shaping knob

## Promotion-gap diagnostic

Under the borrowed baseline at `support_score_min=5` and `max_promoted=2`:

- `33` gold trigger rows total
- `16` rows hit a gold blocker
- `10` rows are `promotion_miss`
- `7` rows are `candidate_missing`

Promotion-miss best-gold scores cluster below threshold:

- score `4.0`: `1`
- score `3.5`: `4`
- score `3.0`: `4`
- score `1.5`: `1`

Dominant promotion-miss signatures:

- `forward_trigger_support + benchmark_target_present + same_pos_as_active + active_side_support`
- `benchmark_target_present + same_pos_as_active + active_side_support`
- `reviewed_trigger_support + benchmark_target_present + active_side_support`

Dominant promotion-miss families:

- `field_area_country`
- `net_mesh_network`

## Frontier decision

- the existing late-node knob frontier is close to saturated
- the next meaningful improvement is unlikely to come from resweeping the same weights
- the next step should be new discriminative promotion features that can raise good blockers from the `3.0-4.0` band without admitting the junk that caused the `promotion_min_4` overblocking spike
- candidate generation still matters, but it is now clearly the secondary frontier behind promotion-feature design
