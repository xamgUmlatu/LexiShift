# en-es Semantic Veto Stage 1 Representative Scoring

- Status: `ok`
- Decision: `stage1_representative_current_policy_scored`
- Generated: `2026-05-05T18:21:56Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json`
- Source config: `docs/test_outputs/semantic_routing_sentence_veto_latest.json`

## Dataset Build

| Metric | Value |
| --- | ---: |
| dataset path | `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json` |
| base dataset | `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json` |
| representative frame | `docs/test_outputs/semantic_veto_sampling_stage1_representative_frame_en_es_latest.json` |
| source frame fingerprint | `476331df5bfc8dbb4d64a8d6d6b75867e677aa0d3111137662510eb246486c4f` |
| families | `19` |
| cases | `120` |
| issues | `none` |

## Current-Policy Score

| Metric | Value |
| --- | ---: |
| cases | `120` |
| gold replace | `53` |
| gold abstain | `67` |
| predicted replace | `13` |
| harmful replacements | `0` |
| false abstains | `40` |
| decision accuracy | `66.7%` |
| replace recall | `24.5%` |
| harmful replace rate | `0.0%` |
| false abstain rate | `75.5%` |

## Context Sources

| Key | Count |
| --- | ---: |
| `agent_curated_corpus_like_app_candidate_contexts` | `25` |
| `existing_sentence_veto_v10_representative_proxy` | `95` |

## Review States

| Key | Count |
| --- | ---: |
| `agent_draft_human_review_pending` | `25` |
| `reviewed_or_existing_source` | `95` |

## Gold Winner Types

| Type | Cases | Replace Recall | Harmful Replace Rate | False Abstain Rate |
| --- | ---: | ---: | ---: | ---: |
| `active` | `53` | `24.5%` | `n/a` | `75.5%` |
| `shadow` | `48` | `n/a` | `0.0%` | `n/a` |
| `none` | `19` | `n/a` | `0.0%` | `n/a` |

## Failure Samples

| Case | Trigger | Gold | Predicted | Context Source | Sentence |
| --- | --- | --- | --- | --- | --- |
| `en-es:representative-gap:v1:001` | `ball` | `replace` | `abstain` | `agent_curated_corpus_like_app_candidate_contexts` | A fan caught the foul ball in the second inning. |
| `en-es:sentence-veto:ball:001` | `ball` | `replace` | `abstain` | `existing_sentence_veto_v10_representative_proxy` | The goalkeeper punched the ball over the bar. |
| `en-es:sentence-veto:ball:002` | `ball` | `replace` | `abstain` | `existing_sentence_veto_v10_representative_proxy` | The child kicked the ball into the street. |
| `en-es:representative-gap:v1:003` | `bank` | `replace` | `abstain` | `agent_curated_corpus_like_app_candidate_contexts` | The bank froze the card after the suspicious charge. |
| `en-es:sentence-veto:bank:001` | `bank` | `replace` | `abstain` | `existing_sentence_veto_v10_representative_proxy` | She deposited the cash at the bank before lunch. |
| `en-es:sentence-veto:bank:002` | `bank` | `replace` | `abstain` | `existing_sentence_veto_v10_representative_proxy` | The bank approved our mortgage application. |
| `en-es:representative-gap:v1:015` | `board` | `replace` | `abstain` | `agent_curated_corpus_like_app_candidate_contexts` | The chess board was missing two squares. |
| `en-es:sentence-veto:board:001` | `board` | `replace` | `abstain` | `existing_sentence_veto_v10_representative_proxy` | He arranged the pieces on the board before the lesson began. |

## Limitations

- `stage1_frame_is_representative_proxy_not_final_browsing_distribution`
- `gap_rows_are_agent_draft_human_review_pending`
- `runtime_policy_change_none`

## Next Steps

- Use this filled-frame score as the representative-proxy lane in product-quality reporting.
- Human-review the 25 corpus-like gap rows before using the result for promotion claims.
- Prefer observed runtime/browser contexts for the next representative refresh.
