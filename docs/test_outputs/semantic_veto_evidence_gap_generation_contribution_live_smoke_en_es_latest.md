# en-es Semantic Veto Evidence-Gap Generated Contribution

- Status: `ok`
- Decision: `generated_contribution_review_queue_ready`
- Generated: `2026-05-08T01:41:47Z`
- Admitted items: `5`
- Review-required items: `3`
- Possible active-role pollution: `0`
- Metadata active overlap: `2`
- New competitor target items: `2`

## Slot Summary

| Slot | Items | Review required | Possible active pollution |
| --- | ---: | ---: | ---: |
| `active_evidence_expansion` | 2 | 0 | 0 |
| `no_winner_context_probe` | 1 | 1 | 0 |
| `shadow_or_competitor_evidence_probe` | 2 | 2 | 0 |

## Review Queue

| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe:item:001` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0152 | 0.0769 | The report included an adjoining appendix with the raw data. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:shadow_or_competitor_evidence_probe:item:002` | `shadow_or_competitor_evidence_probe` | `review_competitor_target_before_rescoring` | 0.0152 | 0.0714 | She signed the form and placed it in the adjoining envelope. |
| `semantic_veto_evidence_gap_control_pilot_en_es_v1:en-es:full-family-repaired-full:adjoining:vecino:no_winner_context_probe:item:001` | `no_winner_context_probe` | `review_no_winner_context_before_rescoring` | 0.0168 | 0.0769 | Search results for adjoining apartments in the city center. |

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
