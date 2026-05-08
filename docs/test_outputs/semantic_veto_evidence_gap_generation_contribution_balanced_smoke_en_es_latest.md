# en-es Semantic Veto Evidence-Gap Generated Contribution

- Status: `ok`
- Decision: `generated_contribution_review_queue_ready`
- Generated: `2026-05-08T19:36:03Z`
- Admitted items: `13`
- Review-required items: `7`
- Possible active-role pollution: `2`
- Metadata active overlap: `2`
- New competitor target items: `2`

## Slot Summary

| Slot | Items | Review required | Possible active pollution |
| --- | ---: | ---: | ---: |
| `active_evidence_expansion` | 6 | 0 | 0 |
| `no_winner_context_probe` | 3 | 3 | 1 |
| `shadow_or_competitor_evidence_probe` | 4 | 4 | 1 |

## Review Queue

| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:entirely:enteramente:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_before_shadow_or_no_winner_use` | 0.1278 | 0.125 | Search results for entirely |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0165 | 0.0526 | The old brother spent the morning copying manuscripts in the monastery library. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0167 | 0.0476 | Each brother rose before dawn for prayer and silence in the abbey. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:brother:hermano:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_no_winner_context_before_rescoring` | 0.0345 | 0.0769 | Search results for brother |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.043 | 0.0625 | Her smile lit up the room during the ceremony. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_before_shadow_or_no_winner_use` | 0.0645 | 0.125 | He gave a quick smile before answering the question. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:smile:sonre-r:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_no_winner_context_before_rescoring` | 0.0505 | 0.0714 | Page title: smile — customer feedback dashboard |

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
