# en-es Semantic Veto Veto-Only Candidate Selection

- Status: `review`
- Decision: `veto_only_shared_candidate_not_found`
- Generated: `2026-05-05T18:22:14Z`
- Probe: `docs/test_outputs/semantic_veto_veto_only_probe_en_es_latest.json`
- Validation: `docs/test_outputs/semantic_veto_veto_only_validation_stage1_representative_en_es_latest.json`
- Matched candidate rows: `297`
- Passing shared rows: `0`

## E2E Checks

| Check | Value |
| --- | --- |
| `probe_rows_considered` | `297` |
| `validation_rows_considered` | `540` |
| `matched_parameter_rows` | `297` |
| `passing_shared_rows` | `0` |

## Top Shared Candidates

| Candidate | Shared pass | Combined utility | Min pos allow | Min neg abstain | v10 pos/neg | validation pos/neg |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.0\|score=0.0 | false | 145.0 | 39.1% | 92.9% | 68.4% / 98.2% | 39.1% / 92.9% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.02\|score=0.0 | false | 142.2 | 81.6% | 53.5% | 81.6% / 94.7% | 88.4% / 53.5% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.02\|score=0.02 | false | 142.2 | 81.6% | 53.5% | 81.6% / 94.7% | 88.4% / 53.5% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase\|lead=0.0\|score=0.0 | false | 140.8 | 43.5% | 86.9% | 68.4% / 98.2% | 43.5% / 86.9% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase\|lead=0.02\|score=0.0 | false | 139.4 | 81.6% | 48.5% | 81.6% / 94.7% | 92.8% / 48.5% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase\|lead=0.02\|score=0.02 | false | 139.4 | 81.6% | 48.5% | 81.6% / 94.7% | 92.8% / 48.5% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.02\|score=0.05 | false | 136.6 | 81.6% | 49.5% | 81.6% / 94.7% | 88.4% / 49.5% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.0\|score=0.02 | false | 136.6 | 68.4% | 55.6% | 68.4% / 98.2% | 84.1% / 55.6% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase\|lead=-0.02\|score=0.0 | false | 136.6 | 33.3% | 93.9% | 60.5% / 98.2% | 33.3% / 93.9% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=-0.02\|score=0.0 | false | 135.2 | 27.5% | 97.0% | 60.5% / 98.2% | 27.5% / 97.0% |
| control_st_masked_all_margin_phrase_override\|shadow_or_phrase\|lead=0.02\|score=0.05 | false | 133.8 | 81.6% | 44.4% | 81.6% / 94.7% | 92.8% / 44.4% |
| control_st_masked_all_margin_phrase_override\|shadow_only\|lead=0.0\|score=0.0 | false | 133.8 | 44.9% | 84.9% | 68.4% / 91.2% | 44.9% / 84.9% |

## Passing Shared Candidates

_No candidate rows._

## Recommendation

- No shared veto-only candidate currently passes both measured inputs.
- Do not promote the v10 pass until a common parameter shape survives the configured validation report.
