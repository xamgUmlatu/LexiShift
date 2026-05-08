# en-es Semantic Veto Sampling Expansion Design

- Status: `ok`
- Decision: `sampling_expansion_design_established`
- Generated: `2026-05-05T06:13:35Z`
- Lanes: `4`
- Curve queue rows read: `24`
- Planned total rows: `440`
- Locked-eval share: `0.5000`

## Lane Budgets

| Lane | Type | Claim | Manual discovery | LLM discovery | Locked eval | Representative? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `representative_random_product_lane` | `representative_random` | `product_quality_estimate` | 0 | 0 | 120 | `yes` |
| `stratified_difficulty_surface_lane` | `stratified_balanced` | `curve_shape_estimation` | 48 | 48 | 48 | `no` |
| `targeted_curve_mechanism_lane` | `targeted_curve_expansion` | `mechanism_validation` | 20 | 80 | 40 | `no` |
| `negative_and_leakage_control_lane` | `negative_control` | `sanity_check` | 12 | 12 | 12 | `no` |

## Stratified Grid

| Case type | Rank bin | Polysemy | Manual | LLM | Locked |
| --- | --- | --- | ---: | ---: | ---: |
| `positive_active` | `1-500` | `low_1_to_3` | 2 | 2 | 2 |
| `positive_active` | `1-500` | `high_4_plus` | 2 | 2 | 2 |
| `positive_active` | `501-1000` | `low_1_to_3` | 2 | 2 | 2 |
| `positive_active` | `501-1000` | `high_4_plus` | 2 | 2 | 2 |
| `positive_active` | `1001-5000` | `low_1_to_3` | 2 | 2 | 2 |
| `positive_active` | `1001-5000` | `high_4_plus` | 2 | 2 | 2 |
| `positive_active` | `missing_or_tail` | `low_1_to_3` | 2 | 2 | 2 |
| `positive_active` | `missing_or_tail` | `high_4_plus` | 2 | 2 | 2 |
| `shadow_negative` | `1-500` | `low_1_to_3` | 2 | 2 | 2 |
| `shadow_negative` | `1-500` | `high_4_plus` | 2 | 2 | 2 |
| `shadow_negative` | `501-1000` | `low_1_to_3` | 2 | 2 | 2 |
| `shadow_negative` | `501-1000` | `high_4_plus` | 2 | 2 | 2 |
| `shadow_negative` | `1001-5000` | `low_1_to_3` | 2 | 2 | 2 |
| `shadow_negative` | `1001-5000` | `high_4_plus` | 2 | 2 | 2 |
| `shadow_negative` | `missing_or_tail` | `low_1_to_3` | 2 | 2 | 2 |
| `shadow_negative` | `missing_or_tail` | `high_4_plus` | 2 | 2 | 2 |
| `phrase_no_winner` | `1-500` | `low_1_to_3` | 2 | 2 | 2 |
| `phrase_no_winner` | `1-500` | `high_4_plus` | 2 | 2 | 2 |
| `phrase_no_winner` | `501-1000` | `low_1_to_3` | 2 | 2 | 2 |
| `phrase_no_winner` | `501-1000` | `high_4_plus` | 2 | 2 | 2 |
| `phrase_no_winner` | `1001-5000` | `low_1_to_3` | 2 | 2 | 2 |
| `phrase_no_winner` | `1001-5000` | `high_4_plus` | 2 | 2 | 2 |
| `phrase_no_winner` | `missing_or_tail` | `low_1_to_3` | 2 | 2 | 2 |
| `phrase_no_winner` | `missing_or_tail` | `high_4_plus` | 2 | 2 | 2 |

## Targeted Curve Cells

| Priority | Case type | Group | Scorer | Score | Manual | LLM | Locked |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `P0` | `phrase_no_winner` | `core_high_polysemy` | `tfidf_cosine` | 0.9087 | 4 | 16 | 8 |
| `P0` | `positive_active` | `core_high_polysemy` | `tfidf_cosine` | 0.7916 | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `mid_high_polysemy` | `tfidf_cosine` | 0.7687 | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.7599 | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.7521 | 4 | 16 | 8 |

## Bias Controls

- `all_rows_locked_for_promotion_estimation`
- `balanced_quota_not_failure_weighted`
- `case_contract_blinded_to_current_scorer`
- `control_failures_block_promotion_claims`
- `controls_expected_to_fail_or_degrade_when_the_pipeline_leaks_labels`
- `do_not_condition_on_current_failure_status`
- `locked_eval_rows_reserved_before_discovery_results`
- `manual_rows_confirm_cell_contract_before_llm_rows`
- `report_controls_separately_from_product_accuracy`
- `report_empty_and_underfilled_cells`
- `report_sampling_weights_and_missing_context_source`
- `rerun_curve_surface_before_expanding_P1`
- `source_trigger_and_context_sampled_before_scoring`
- `stratified_results_not_representative_without_reweighting`
- `targeted_rows_cannot_estimate_real_world_frequency`

## Methodology

- Core principle: Representative rows estimate product quality, stratified rows draw the difficulty surface, targeted rows test mechanisms, controls detect leakage, and locked rows validate after selection.
- Random seed: `semantic_veto_sampling_expansion_en_es_v1_2026_05_05`
- Pre-register sampling lanes, quotas, split policy, and promotion claims before authoring or generating rows.
- Keep representative, stratified, targeted, control, discovery, and locked-eval rows separate in every output.
- Do not tune thresholds, formula weights, source evidence, or prompt templates on locked-eval rows.
- Do not ask LLMs to create rows that fool or repair the current scorer; prompts may name only the linguistic case contract.
- Treat missing metadata and underfilled strata as findings, not as permission to substitute known failure rows.
- Use stable random seeds and deterministic row IDs so later agents can reproduce the sample plan.

## Stage Plan

- `stage_0_design_freeze`: entry `Current curve-guided report and product-quality policy are present.`; exit `Sampling design report is generated, reviewed, and committed; no rows authored yet.`
- `stage_1_p0_manual_and_frame_sample`: entry `Design freeze passed.`; exit `P0 manual rows and representative sampling-frame candidate list are materialized; no threshold or scorer changes.`
- `stage_2_llm_discovery_generation`: entry `Manual rows confirm each P0 cell contract and prompts pass leakage review.`; exit `LLM discovery rows are admitted and scored separately from manual rows.`
- `stage_3_locked_eval_and_curve_rerun`: entry `Discovery candidate choices are frozen.`; exit `Locked-eval rows are scored once, and curve reports are rerun without changing the locked lane.`

## Acceptance Link

- `positive_allow_rate_min`: 0.8
- `negative_abstain_rate_min`: 0.5
- `representative_lane_required_for_promotion`: True
- `promotion_claim_rule`: Only the representative locked lane can estimate product quality; stratified and targeted lanes can explain or improve it.

## Next Steps

- Freeze this sampling design before authoring additional rows.
- Materialize the representative sampling frame and P0 manual rows first.
- Run leakage/control prompts before any LLM generation spend.
- After P0 discovery rows are scored, rerun the difficulty surface and decide whether P1 expansion is still justified.
