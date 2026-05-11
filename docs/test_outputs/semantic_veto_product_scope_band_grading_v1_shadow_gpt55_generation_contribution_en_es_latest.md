# en-es Semantic Veto Evidence-Gap Generated Contribution

- Status: `ok`
- Decision: `generated_contribution_review_queue_ready`
- Generated: `2026-05-09T21:43:13Z`
- Admitted items: `12`
- Review-required items: `12`
- Possible active-role pollution: `0`
- Metadata active overlap: `2`
- New competitor target items: `0`

## Slot Summary

| Slot | Items | Review required | Possible active pollution |
| --- | ---: | ---: | ---: |
| `shadow_or_competitor_evidence_probe` | 12 | 12 | 0 |

## Review Queue

| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0297 | 0.05 | The officer will cite any driver who parks in the fire lane. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:cite:mencionar:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0289 | 0.05 | City inspectors may cite the restaurant if employees block the emergency exit. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0741 | 0.0625 | Her smile made the nervous child feel welcome. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0669 | 0.0588 | The photographer captured his smile just before the ceremony began. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0585 | 0.05 | We met at the bar after work to celebrate the promotion. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:bar:cercar:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.066 | 0.0909 | The old bar on the corner serves coffee in the morning and beer at night. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0309 | 0.0526 | Turn the dial to control the oven temperature before baking the bread. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:control:gobernar:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0331 | 0.0556 | Use the slider to control the screen brightness during the presentation. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0609 | 0.0556 | During the appeal, counsel will except to the judge's refusal to admit the exhibit. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:except:excepto:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0656 | 0.0588 | The defense attorneys except to the prosecutor's characterization of the witness testimony. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0594 | 0.0625 | The doctor examined the region around the patient's knee for swelling. |
| `semantic_veto_product_scope_band_grading_v1_allocation_en_es:en-es:full-family-repaired-full:region:comarca:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0571 | 0.0588 | The technician marked the overheated region on the circuit board with tape. |

## Next Steps

- Review non-active generated items for semantic role correctness.
- Then run the downstream score-contribution harness on reviewed generated items.

## Limitations

- `no runtime policy change`
- `no source evidence promotion`
- `active-pollution similarity flags use generated sentences, not explanatory metadata`
- `metadata-overlap counts are reported separately because notes may contain contrast language`
- `similarity scores are diagnostics, not final semantic judgments`
- `shadow and no-winner rows still need review or downstream score contribution checks`
