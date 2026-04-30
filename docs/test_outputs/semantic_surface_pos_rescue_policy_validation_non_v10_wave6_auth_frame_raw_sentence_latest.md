# en-es Surface-POS Rescue Policy Validation

- Status: `ok`
- Decision: `scorer_backed_policy_pass`
- Generated: `2026-04-30T03:50:35Z`
- Policy: `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02`

## Summary

- Suites: `2`
- Cases: `54`
- Harmful replacements: `0` / max `0`
- False abstains: `0` / max `0`
- Active rescues applied: `3`
- Harmful cases: `none`
- False abstain cases: `none`

## Suites

| Suite | Pass | Cases | Harmful | False Abstain | Recall | Accuracy | Active Rescues | Source Validation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `active_shadow` | `true` | 38 | 0 | 0 | 100.0% | 100.0% | 3 | `ok` / `heldout_pass` |
| `phrase_no_winner` | `true` | 16 | 0 | 0 | 0.0% | 100.0% | 0 | `review` / `heldout_review` |

## Rescue Applications

| Suite | Case | Gold | Before | After | Active | Shadow | Phrase | Phrase Lead | Surface Signal | Trace |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `active_shadow` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:finish:001` | `replace` | `replace` | `replace` | 0.6238 | 0.6941 | 0.6867 | -0.0074 | `active_noun_frame` | rescue |
| `active_shadow` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:throw:001` | `replace` | `replace` | `replace` | 0.6168 | 0.5943 | 0.6842 | 0.0674 | `active_noun_frame` | rescue |
| `active_shadow` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:001` | `replace` | `replace` | `replace` | 0.6231 | 0.6946 | 0.7295 | 0.0349 | `active_noun_frame` | rescue |

## Failure Cases

No failure cases.

## Limitations

- `offline_scorer_backed_validation_not_runtime_policy`
- `policy_applied_after_fresh_harness_scoring`
- `bounded_wave6_active_and_phrase_suites_only`

## Next Steps

- keep the candidate research-only until broader semantic-class breadth is tested
- do not change runtime policy without implementation and runtime-path tests
