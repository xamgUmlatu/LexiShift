# en-es Source Frame Gap Plan

- Status: `ready`
- Generated: `2026-04-28T21:08:16Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Alignment audit: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_source_row_alignment_audit_def_example_plus_llm_aligned_frame_gap_latest.json`
- Candidate source id: `llm_aligned_sentence_frame_rows`
- Prompt version: `aligned-sentence-frame-v2`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`
- Leakage policy: `prompts_use_sense_labels_and_glosses_only; do_not_include_sentence_veto_case_sentences`
- Sense slots: `38`
- Missing selector-ready slots: `1`
- Planned candidate requests: `5`
- Candidate diversity frames: `5`
- Estimated prompt tokens: `1996`

## Recommendation

Plan 5 no-spend candidate requests covering 1 missing active/shadow selector slots. Execute these only through the existing leakage audit and source-admission cycle, then rerun the context-conditioned matrix before any runtime claim.

## Gap Summary

| Target | Slots | Missing Slots | Candidate Requests |
| --- | ---: | ---: | ---: |
| active_example | 19 | 0 | 0 |
| shadow_example | 19 | 1 | 5 |

## Missing Slots By Family

| Family | Missing Active | Missing Shadows | Candidate Requests |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:board:tablero | 0 | 1 | 5 |

## Request Rows

| Request | Target | Family | Candidate Sense | Attempt | Diversity Frame | Prompt Tokens Est. |
| --- | --- | --- | --- | ---: | --- | ---: |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-01 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 1 | specific_role_action | 404 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-02 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 2 | place_time_observation | 398 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-03 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 3 | problem_resolution | 397 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-04 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 4 | instruction_or_plan | 395 |
| en-es:source-frame-gap:shadow_example:en-es-sentence-veto-board-tablero:en-es-sentence-veto-board-junta-shadow:candidate-05 | shadow_example | en-es:sentence-veto:board:tablero | en-es:sentence-veto:board:junta:shadow | 5 | contrastive_detail | 402 |
