# en-es Semantic Veto Product-Scope Selected Candidate Surface

- Status: `ok`
- Decision: `product_scope_selected_candidate_surface_established`
- Generated: `2026-05-09T04:53:18Z`
- Candidates: `5`
- Row results: `700`

## Candidates

| Candidate | Reason | Base scorer | Phrase | Rescue | Pos allow | Neg abstain | Harmful | False abstain |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `best_product_rank_sentence_transformer_a0000_mneg0025` | `best_product_rank` | `sentence_transformer_cosine` | `noun_family_frame_guard` | `off` | 92.9% | 88.1% | 5 | 7 |
| `safest_80pct_positive_sentence_transformer_a0000_m0015` | `safest_80pct_positive` | `sentence_transformer_cosine` | `noun_family_frame_guard` | `off` | 83.7% | 97.6% | 1 | 16 |
| `high_recall_soft_assist_tfidf_a0000_mneg0050` | `high_recall_soft_assist` | `tfidf_cosine` | `off` | `off` | 99.0% | 11.9% | 37 | 1 |
| `current_v3_like_sentence_transformer_a0000_m0000` | `current_v3_like` | `sentence_transformer_cosine` | `noun_family_frame_guard` | `sense_label_near_tie_active_rescue` | 85.7% | 92.9% | 3 | 14 |
| `tfidf_best_by_scorer_tfidf_a0000_mneg0005` | `tfidf_best_by_scorer` | `tfidf_cosine` | `noun_family_frame_guard` | `off` | 91.8% | 50.0% | 21 | 8 |

## Limitations

- `candidate_set_is_selected_from_discovery_bakeoff`
- `filtered_repaired_full_is_not_final_browsing_distribution`
- `candidate_id_is_encoded_as_scorer_id_for_downstream_sweep_compatibility`

## Next Steps

- Run repaired-full band/formula sweep with this report as score-surface input.
- Compare whether heuristic signals still rank hard families under the corrected candidate rows.
