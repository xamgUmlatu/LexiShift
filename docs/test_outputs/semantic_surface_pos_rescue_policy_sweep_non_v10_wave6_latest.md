# en-es Surface-POS Rescue Policy Sweep

- Status: `review`
- Decision: `rescue_policy_review`
- Generated: `2026-04-29T03:48:19Z`
- Recommended policy: `none`
- Passing policies: `0`

## Recommendation

- Reason: `no_policy_passed`
- Next step: add a new rescue gate or source signal; current replayed gates did not pass

## Best Rows

| Suite | Policy | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.04` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.02` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.03` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.04` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.02` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.03` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.04` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.02` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.03` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `phrase_no_winner` | `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.04` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |

## Passing Policies

No passing policies.

## Blockers

| Policy | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| --- | --- | ---: | ---: | --- | --- |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.02` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.02` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.03` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.03` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.04` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.04` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.05` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=none` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.02` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.03` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.04` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.05` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.5;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=none` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.03` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.04` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.05` | `active_shadow` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=none` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.02` | `active_shadow` | 0 | 4 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.03` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.04` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.05` | `active_shadow` | 0 | 3 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` |
| `m=0;p=0.02;rescue_active=0.55;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=none` | `active_shadow` | 0 | 5 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=none` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.02` | `active_shadow` | 0 | 5 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.03` | `active_shadow` | 0 | 5 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.04` | `active_shadow` | 0 | 5 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.05` | `active_shadow` | 0 | 5 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:serve:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:upset:001` |
| `m=0;p=0.02;rescue_active=0.58;noun_lead=none;modifier_lead=0.05` | `phrase_no_winner` | 1 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001` | `none` |

## Limitations

- `replay_only_not_runtime_policy`
- `uses_fixed_score_traces_from_supplied_reports`
- `bounded_wave6_active_and_phrase_suites_only`
