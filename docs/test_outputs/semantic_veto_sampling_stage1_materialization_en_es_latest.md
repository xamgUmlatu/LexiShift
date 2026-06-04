# en-es Semantic Veto Sampling Stage 1 Materialization

- Status: `ok`
- Decision: `sampling_stage1_materialized`
- Generated: `2026-05-05T18:21:44Z`
- Representative frame: `docs/test_outputs/semantic_veto_sampling_stage1_representative_frame_en_es_latest.json`
- P0 dataset: `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json`

## Summary

| Metric | Value |
| --- | ---: |
| representative target locked rows | `120` |
| representative available rows | `120` |
| representative selected locked rows | `120` |
| representative remaining rows needed | `0` |
| P0 curve cells | `5` |
| P0 manual cases | `20` |
| P0 triggers | `2` |

## Representative Frame

| Rank | Trigger | Target | Gold | Source case |
| ---: | --- | --- | --- | --- |
| 1 | `ball` | `pelota` | `replace` | `en-es:sentence-veto:ball:001` |
| 2 | `check` | `cheque` | `abstain` | `en-es:sentence-veto:check:005` |
| 3 | `branch` | `sucursal` | `abstain` | `en-es:sentence-veto:branch:004` |
| 4 | `bank` | `banco` | `abstain` | `en-es:sentence-veto:bank:005` |
| 5 | `park` | `parque` | `abstain` | `en-es:sentence-veto:park:004` |
| 6 | `play` | `obra` | `replace` | `en-es:sentence-veto:play:001` |
| 7 | `board` | `tablero` | `replace` | `en-es:sentence-veto:board:002` |
| 8 | `spring` | `primavera` | `abstain` | `en-es:sentence-veto:spring:003` |
| 9 | `bank` | `banco` | `replace` | `en-es:representative-gap:v1:003` |
| 10 | `report` | `informe` | `replace` | `en-es:sentence-veto:report:002` |
| 11 | `seal` | `sello` | `abstain` | `en-es:representative-gap:v1:011` |
| 12 | `order` | `pedido` | `abstain` | `en-es:sentence-veto:order:005` |

## P0 Manual Rows

| Case | Type | Scorer | Trigger | Decision | Sentence |
| --- | --- | --- | --- | --- | --- |
| `en-es:sampling-stage1-p0:help:01:001` | `phrase_no_winner` | `tfidf_cosine` | `help` | `abstain` | I cannot help noticing how quiet the room became. |
| `en-es:sampling-stage1-p0:help:01:002` | `phrase_no_winner` | `tfidf_cosine` | `help` | `abstain` | She could not help but smile at the news. |
| `en-es:sampling-stage1-p0:help:01:003` | `phrase_no_winner` | `tfidf_cosine` | `help` | `abstain` | Help, the elevator is stuck between floors! |
| `en-es:sampling-stage1-p0:help:01:004` | `phrase_no_winner` | `tfidf_cosine` | `help` | `abstain` | So help me, I will finish this tonight. |
| `en-es:sampling-stage1-p0:help:02:001` | `positive_active` | `tfidf_cosine` | `help` | `replace` | Her help made the move much easier. |
| `en-es:sampling-stage1-p0:help:02:002` | `positive_active` | `tfidf_cosine` | `help` | `replace` | The guide offers help with password resets. |
| `en-es:sampling-stage1-p0:help:02:003` | `positive_active` | `tfidf_cosine` | `help` | `replace` | We need help carrying these boxes upstairs. |
| `en-es:sampling-stage1-p0:help:02:004` | `positive_active` | `tfidf_cosine` | `help` | `replace` | Thank you for the help you gave my sister. |
| `en-es:sampling-stage1-p0:particular:03:001` | `phrase_no_winner` | `tfidf_cosine` | `particular` | `abstain` | In particular, the last paragraph needs work. |
| `en-es:sampling-stage1-p0:particular:03:002` | `phrase_no_winner` | `tfidf_cosine` | `particular` | `abstain` | Nothing in particular caught my eye. |
| `en-es:sampling-stage1-p0:particular:03:003` | `phrase_no_winner` | `tfidf_cosine` | `particular` | `abstain` | He was not angry with anyone in particular. |
| `en-es:sampling-stage1-p0:particular:03:004` | `phrase_no_winner` | `tfidf_cosine` | `particular` | `abstain` | One example in particular changed my mind. |
| `en-es:sampling-stage1-p0:help:04:001` | `phrase_no_winner` | `sentence_transformer_cosine` | `help` | `abstain` | No one can help being nervous before the final. |
| `en-es:sampling-stage1-p0:help:04:002` | `phrase_no_winner` | `sentence_transformer_cosine` | `help` | `abstain` | The child shouted help from the locked bathroom. |
| `en-es:sampling-stage1-p0:help:04:003` | `phrase_no_winner` | `sentence_transformer_cosine` | `help` | `abstain` | I can't help thinking we missed a step. |
| `en-es:sampling-stage1-p0:help:04:004` | `phrase_no_winner` | `sentence_transformer_cosine` | `help` | `abstain` | Help yourself to some coffee before the meeting. |
| `en-es:sampling-stage1-p0:particular:05:001` | `phrase_no_winner` | `sentence_transformer_cosine` | `particular` | `abstain` | She likes tea in particular after dinner. |
| `en-es:sampling-stage1-p0:particular:05:002` | `phrase_no_winner` | `sentence_transformer_cosine` | `particular` | `abstain` | No rule in particular explains that result. |
| `en-es:sampling-stage1-p0:particular:05:003` | `phrase_no_winner` | `sentence_transformer_cosine` | `particular` | `abstain` | This season in particular has been unpredictable. |
| `en-es:sampling-stage1-p0:particular:05:004` | `phrase_no_winner` | `sentence_transformer_cosine` | `particular` | `abstain` | I remember that hallway in particular. |

## Bias Controls

- `representative_selection_does_not_use_scores_or_outcomes`
- `representative_shortfall_is_reported_not_backfilled_with_targeted_rows`
- `representative_gap_rows_are_corpus_like_primary_proxy_not_targeted_p0`
- `p0_rows_are_discovery_only`
- `p0_rows_are_not_representative_frequency_evidence`
- `llm_generation_waits_for_manual_contract_review`

## Limitations

- `representative_frame_uses_existing_v10_proxy_and_corpus_like_gap_proxy_not_final_browsing_distribution`
- `representative_gap_rows_are_agent_draft_human_review_pending`
- `p0_manual_rows_are_agent_draft_human_review_pending`
- `duplicate_trigger_p0_cells_are_preserved_because_current_curve_queue_is_scorer_cell_based`

## Next Steps

- Human-review the P0 manual rows before LLM expansion.
- Human-review the 25 representative gap rows before using them for promotion claims.
- Prefer observed browser/runtime contexts for the next representative refresh when logs are available.
- Run leakage/control prompt checks before generating LLM discovery rows.
- Score the P0 manual packet as a discovery lane, then rerun the curve and sampling reports before expanding P1.
