# en-es Surface-POS Rescue Policy Sweep

- Status: `ok`
- Decision: `rescue_policy_candidate_found`
- Generated: `2026-04-30T03:42:53Z`
- Recommended policy: `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02`
- Passing policies: `12`

## Recommendation

- Reason: `passing_policy_found`
- Next step: run the recommended rescue policy through the scorer-backed held-out harness

## Best Rows

| Suite | Policy | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.04` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.05` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=none` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.02` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.03` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.04` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.05` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=none` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.02` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow` | `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.03` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |

## Passing Policies

| Policy | Min Margin | Phrase Margin | Rescue Active Floor | Noun Phrase Ceiling | Modifier Phrase Ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02` | 0.0 | 0.02 | 0.52 | none | 0.02 |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03` | 0.0 | 0.02 | 0.52 | none | 0.03 |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.04` | 0.0 | 0.02 | 0.52 | none | 0.04 |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.05` | 0.0 | 0.02 | 0.52 | none | 0.05 |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.02` | 0.0 | 0.02 | 0.55 | none | 0.02 |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.03` | 0.0 | 0.02 | 0.55 | none | 0.03 |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.04` | 0.0 | 0.02 | 0.55 | none | 0.04 |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.05` | 0.0 | 0.02 | 0.55 | none | 0.05 |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.02` | 0.0 | 0.02 | 0.58 | none | 0.02 |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.03` | 0.0 | 0.02 | 0.58 | none | 0.03 |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.04` | 0.0 | 0.02 | 0.58 | none | 0.04 |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.05` | 0.0 | 0.02 | 0.58 | none | 0.05 |

## Blockers

| Policy | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| --- | --- | ---: | ---: | --- | --- |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.02` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.03` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.04` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.02` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.03` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.04` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |

## Limitations

- `replay_only_not_runtime_policy`
- `uses_fixed_score_traces_from_supplied_reports`
- `bounded_wave6_active_and_phrase_suites_only`
