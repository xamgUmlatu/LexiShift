# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `fix_blocking_failure_classes`
- Generated: `2026-04-30T03:43:00Z`
- Promotion readiness: `blocked`
- Quality-gate distance: `semantic_risk_blockers`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest`
- Admission semantic contract: `16` / `16`
- Admission final rows: `284`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest`
- Held-out cases: `38` across `16` families
- Held-out harmful / false abstain: `0` / `0`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `additional_heldout_1_harmful_replace` | `2` | `True` | `False` | `bear, low` |

## Leverage And Overfit Boundary

- Source rows: `5`
- Source families: `0`
- Held-out cases per admitted row: `0.1901`
- Families needed before broad-confidence claim: `34`
- Cases needed before broad-confidence claim: `146`
- Source-mode false-abstain delta: `0`
- Source-mode sense-reject delta: `0`

## Quality Gate Distance

- Blockers: `heldout_harmful_replace`
- Tracked residuals: `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_alt_phrase_non_v10_wave6_wiktextract_supported_latest` | `0` | `16` / `16` | `0` | `0` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest` | `non_v10_wave6_wiktextract_supported_phrase_no_winner` | `16` | `16` | `2` | `0` | `0.8750` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest` | `authorization_frame_rows_ready` | `0` | `5` | `0` | `0` |

## Margin Sweep

- Decision: `rescue_policy_candidate_found`
- Recommended margin: `None`
- Passing margins: `none`

## Next Steps

- resolve blocking semantic-risk classes before claiming source expansion
- rerun admission, held-out validation, margin sweep, and this mining harness
- only expand breadth after harmful replacements and semantic contract gaps are clean
