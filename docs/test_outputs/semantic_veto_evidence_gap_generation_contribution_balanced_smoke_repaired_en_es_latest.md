# en-es Semantic Veto Evidence-Gap Generated Contribution

- Status: `ok`
- Decision: `generated_contribution_review_queue_ready`
- Generated: `2026-05-08T03:11:49Z`
- Admitted items: `15`
- Review-required items: `9`
- Possible active-role pollution: `2`
- Metadata active overlap: `2`
- New competitor target items: `4`

## Slot Summary

| Slot | Items | Review required | Possible active pollution |
| --- | ---: | ---: | ---: |
| `active_evidence_expansion` | 6 | 0 | 0 |
| `no_winner_context_probe` | 3 | 3 | 1 |
| `shadow_or_competitor_evidence_probe` | 6 | 6 | 1 |

## Review Queue

| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0508 | 0.0714 | The plan was entirely different from the one we discussed yesterday. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0471 | 0.0667 | Her decision was entirely her own, with no pressure from anyone else. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_before_shadow_or_no_winner_use` | 0.0964 | 0.125 | Search results for entirely. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0154 | 0.0417 | After years of study, the brother took his vows and lived in silence at the abbey. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0188 | 0.0526 | The brother copied manuscripts in the cloister and prayed before dawn. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_no_winner_context_before_rescoring` | 0.0357 | 0.0769 | Search results for brother |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0443 | 0.0588 | Her smile was warm and reassuring during the interview. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_before_shadow_or_no_winner_use` | 0.0597 | 0.125 | A quick smile crossed his face before he answered. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_no_winner_context_before_rescoring` | 0.0574 | 0.0769 | Page title: smile gallery overview |

## Next Steps

- Manually review possible active-role pollution before using generated shadow/no-winner items.
- Do not launch the full 72-request batch until role pollution is understood.

## Limitations

- `no runtime policy change`
- `no source evidence promotion`
- `active-pollution similarity flags use generated sentences, not explanatory metadata`
- `metadata-overlap counts are reported separately because notes may contain contrast language`
- `similarity scores are diagnostics, not final semantic judgments`
- `shadow and no-winner rows still need review or downstream score contribution checks`
