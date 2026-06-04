# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `fix_blocking_failure_classes`
- Generated: `2026-04-29T01:49:48Z`
- Promotion readiness: `blocked`
- Quality-gate distance: `semantic_risk_blockers`
- Manual overfit risk: `medium`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_wordnet_def_ex_non_v10_wave6_wiktextract_supported_latest`
- Admission semantic contract: `16` / `16`
- Admission final rows: `61`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave6_wiktextract_supported_heldout_margin005_validation_latest`
- Held-out cases: `38` across `16` families
- Held-out harmful / false abstain: `2` / `1`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `heldout_harmful_replace` | `2` | `True` | `False` | `leave, piece` |
| `heldout_false_abstain` | `1` | `False` | `True` | `leave` |
| `additional_heldout_1_harmful_replace` | `2` | `True` | `False` | `bear, fair` |
| `primary_sense_reject` | `11` | `False` | `True` | `competitor_sense_not_lower` |
| `primary_phrase_contract_gap` | `16` | `False` | `True` | `advance, bear, black, fair, feel, finish, leave, low, part, piece, rank, serve, show, still, throw, upset` |
| `comparator_sense_reject` | `4` | `False` | `True` | `competitor_sense_not_lower` |
| `comparator_semantic_contract_gap` | `4` | `False` | `True` | `case, date, point, rock` |
| `comparator_seed_false_abstain` | `7` | `False` | `True` | `case, date, point, rock` |
| `comparator_phrase_contract_gap` | `8` | `False` | `True` | `case, date, draft, line, point, ring, rock, scale` |
| `margin_policy_blockers` | `29` | `False` | `True` | `bear, black, fair, leave, low, piece` |

## Leverage And Overfit Boundary

- Source rows: `72`
- Source families: `16`
- Held-out cases per admitted row: `0.8852`
- Families needed before broad-confidence claim: `34`
- Cases needed before broad-confidence claim: `146`
- Source-mode false-abstain delta: `-7`
- Source-mode sense-reject delta: `7`

## Quality Gate Distance

- Blockers: `heldout_harmful_replace`
- Tracked residuals: `heldout_false_abstain`, `sense_filter_rejects`, `phrase_contract_gap`, `insufficient_family_breadth`, `insufficient_case_breadth`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest` | `4` | `4` / `8` | `0` | `7` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave6_wiktextract_supported_phrase_margin005_validation_latest` | `non_v10_wave6_wiktextract_supported_phrase_no_winner` | `16` | `16` | `2` | `0` | `0.8750` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_wordnet_def_ex_non_v10_wave6_wiktextract_supported_latest` | `definition_and_example` | `16` | `72` | `0` | `0` |

## Margin Sweep

- Decision: `margin_review`
- Recommended margin: `None`
- Passing margins: `none`

## Next Steps

- resolve blocking semantic-risk classes before claiming source expansion
- rerun admission, held-out validation, margin sweep, and this mining harness
- only expand breadth after harmful replacements and semantic contract gaps are clean
