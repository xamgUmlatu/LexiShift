# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `fix_blocking_failure_classes`
- Generated: `2026-04-28T23:37:01Z`
- Promotion readiness: `blocked`
- Quality-gate distance: `semantic_risk_blockers`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest`
- Admission semantic contract: `16` / `16`
- Admission final rows: `51`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave5_portfolio_heldout_margin005_validation_latest`
- Held-out cases: `32` across `16` families
- Held-out harmful / false abstain: `1` / `0`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `heldout_harmful_replace` | `1` | `True` | `False` | `present` |
| `additional_heldout_1_harmful_replace` | `1` | `True` | `False` | `end` |
| `primary_phrase_contract_gap` | `16` | `False` | `True` | `answer, change, dry, end, fast, land, look, mean, offer, plain, present, quiet, rest, sign, train, use` |
| `comparator_sense_reject` | `8` | `False` | `True` | `competitor_sense_not_lower` |
| `comparator_phrase_contract_gap` | `8` | `False` | `True` | `answer, land, look, offer, rest, sign, train, use` |
| `margin_policy_blockers` | `17` | `False` | `True` | `end, present, rest` |

## Leverage And Overfit Boundary

- Source rows: `51`
- Source families: `16`
- Held-out cases per admitted row: `0.9412`
- Families needed before broad-confidence claim: `34`
- Cases needed before broad-confidence claim: `152`
- Source-mode false-abstain delta: `0`
- Source-mode sense-reject delta: `-8`

## Quality Gate Distance

- Blockers: `heldout_harmful_replace`
- Tracked residuals: `phrase_contract_gap`, `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave2_selected_latest` | `8` | `8` / `8` | `0` | `0` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave5_portfolio_phrase_margin005_validation_latest` | `non_v10_wave5_source_portfolio_phrase_no_winner` | `16` | `16` | `1` | `0` | `0.9375` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_non_v10_source_portfolio_wave5_anypos_latest` | `source_portfolio_materialized` | `16` | `51` | `0` | `0` |

## Margin Sweep

- Decision: `margin_review`
- Recommended margin: `None`
- Passing margins: `none`

## Next Steps

- resolve blocking semantic-risk classes before claiming source expansion
- rerun admission, held-out validation, margin sweep, and this mining harness
- only expand breadth after harmful replacements and semantic contract gaps are clean
