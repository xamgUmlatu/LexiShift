# en-es Semantic Source Failure-class Mining

- Status: `review`
- Decision: `fix_blocking_failure_classes`
- Generated: `2026-04-30T19:18:43Z`
- Promotion readiness: `blocked`
- Quality-gate distance: `semantic_risk_blockers`
- Manual overfit risk: `low`

## Primary Evidence

- Admission: `semantic_source_admission_cycle_wave7_source_class_breadth_v1_latest`
- Admission semantic contract: `16` / `16`
- Admission final rows: `151`
- Seed ablation harmful / false abstain: `0` / `0`
- Held-out: `semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest`
- Held-out cases: `32` across `16` families
- Held-out harmful / false abstain: `1` / `3`
- Additional held-out suites: `1`

## Failure Classes

| Class | Count | Blocks semantic promotion | Tracked residual | Families |
| --- | ---: | --- | --- | --- |
| `heldout_harmful_replace` | `1` | `True` | `False` | `gross` |
| `heldout_false_abstain` | `3` | `False` | `True` | `even, fix, meet` |
| `additional_heldout_1_harmful_replace` | `6` | `True` | `False` | `cast, foul, score, squeeze, stretch, wrong` |
| `primary_sense_reject` | `29` | `False` | `True` | `competitor_sense_not_lower` |
| `primary_phrase_contract_gap` | `16` | `False` | `True` | `cast, crash, even, firm, fix, foul, full, gross, like, meet, score, squeeze, stretch, trim, waste, wrong` |
| `comparator_sense_reject` | `4` | `False` | `True` | `competitor_sense_not_lower` |
| `comparator_semantic_contract_gap` | `4` | `False` | `True` | `case, date, point, rock` |
| `comparator_seed_false_abstain` | `7` | `False` | `True` | `case, date, point, rock` |
| `comparator_phrase_contract_gap` | `8` | `False` | `True` | `case, date, draft, line, point, ring, rock, scale` |
| `margin_policy_blockers` | `12` | `False` | `True` | `ball, bank, board, file, plant, seal, table` |

## Leverage And Overfit Boundary

- Source rows: `87`
- Source families: `16`
- Held-out cases per admitted row: `0.3179`
- Families needed before broad-confidence claim: `0`
- Cases needed before broad-confidence claim: `0`
- Source-mode false-abstain delta: `-7`
- Source-mode sense-reject delta: `25`

## Quality Gate Distance

- Blockers: `heldout_harmful_replace`
- Tracked residuals: `heldout_false_abstain`, `sense_filter_rejects`, `phrase_contract_gap`

## Comparator Admissions

| Label | Sense rejects | Semantic contract | Seed harmful | Seed false abstain |
| --- | ---: | ---: | ---: | ---: |
| `semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest` | `4` | `4` / `8` | `0` | `7` |

## Additional Held-out Suites

| Label | Scope | Cases | Families | Harmful | False abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest` | `non_v10_wave7_source_class_breadth_phrase_no_winner` | `16` | `16` | `6` | `0` | `0.6250` |

## Source Reports

| Label | Mode | Families | Rows | Active gaps | Shadow gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_wiktextract_translation_support_wave7_source_class_breadth_v1_latest` | `wiktextract_support_complete` | `0` | `0` | `0` | `0` |
| `semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest` | `source_class_frame_rows_ready` | `0` | `87` | `0` | `0` |
| `semantic_wordnet_def_ex_non_v10_wave7_source_class_breadth_v1_latest` | `definition_and_example` | `16` | `68` | `0` | `0` |
| `semantic_translation_sense_evidence_non_v10_wave7_source_class_breadth_v1_latest` | `candidate_batch_ready` | `16` | `37` | `0` | `0` |

## Margin Sweep

- Decision: `margin_candidate_found`
- Recommended margin: `0.005`
- Passing margins: `0.005, 0.01`

## Next Steps

- resolve blocking semantic-risk classes before claiming source expansion
- rerun admission, held-out validation, margin sweep, and this mining harness
- only expand breadth after harmful replacements and semantic contract gaps are clean
