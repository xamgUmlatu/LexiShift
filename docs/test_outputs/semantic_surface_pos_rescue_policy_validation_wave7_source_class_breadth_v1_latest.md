# en-es Surface-POS Rescue Policy Validation

- Status: `review`
- Decision: `scorer_backed_policy_review`
- Generated: `2026-04-30T19:20:25Z`
- Policy: `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02`

## Summary

- Suites: `2`
- Cases: `48`
- Harmful replacements: `8` / max `0`
- False abstains: `3` / max `0`
- Active rescues applied: `8`
- Harmful cases: `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001, en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001`
- False abstain cases: `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001, en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:even:001, en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001`

## Suites

| Suite | Pass | Cases | Harmful | False Abstain | Recall | Accuracy | Active Rescues | Source Validation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `active_shadow` | `false` | 32 | 1 | 3 | 81.2% | 87.5% | 4 | `review` / `heldout_review` |
| `phrase_no_winner` | `false` | 16 | 7 | 0 | 0.0% | 56.2% | 4 | `review` / `heldout_review` |

## Rescue Applications

| Suite | Case | Gold | Before | After | Active | Shadow | Phrase | Phrase Lead | Surface Signal | Trace |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `abstain` | `replace` | `replace` | 0.6767 | 0.6376 | 0.0 | -0.6767 | `active_modifier_frame` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:cast:001` | `replace` | `replace` | `replace` | 0.5639 | 0.5686 | 0.0 | -0.5686 | `active_noun_frame` | rescue |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `replace` | `abstain` | `abstain` | 0.626 | 0.7449 | 0.0 | -0.7449 | `shadow_verb_frame` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:full:001` | `replace` | `replace` | `replace` | 0.5873 | 0.6309 | 0.0 | -0.6309 | `active_modifier_frame` | rescue |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:even:001` | `replace` | `abstain` | `abstain` | 0.7265 | 0.5392 | 0.0 | -0.7265 | `` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `replace` | `abstain` | `abstain` | 0.5444 | 0.6926 | 0.0 | -0.6926 | `` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:score:001` | `replace` | `replace` | `replace` | 0.6984 | 0.7148 | 0.0 | -0.7148 | `active_noun_frame` | rescue |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:squeeze:001` | `replace` | `replace` | `replace` | 0.6188 | 0.6558 | 0.0 | -0.6558 | `active_noun_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `abstain` | `replace` | `replace` | 0.5626 | 0.6113 | 0.0 | -0.6113 | `active_noun_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001` | `abstain` | `replace` | `replace` | 0.5631 | 0.5314 | 0.0 | -0.5631 | `` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `abstain` | `replace` | `replace` | 0.679 | 0.6892 | 0.0 | -0.6892 | `active_modifier_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `abstain` | `replace` | `replace` | 0.7496 | 0.7342 | 0.0 | -0.7496 | `active_noun_frame` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `abstain` | `replace` | `replace` | 0.7298 | 0.7096 | 0.0 | -0.7298 | `active_noun_frame` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `abstain` | `replace` | `replace` | 0.683 | 0.734 | 0.0 | -0.734 | `active_noun_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `abstain` | `replace` | `replace` | 0.5938 | 0.6342 | 0.0 | -0.6342 | `active_noun_frame` | rescue |

## Failure Cases

| Suite | Case | Gold | Before | After | Active | Shadow | Phrase | Phrase Lead | Surface Signal | Trace |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `abstain` | `replace` | `replace` | 0.6767 | 0.6376 | 0.0 | -0.6767 | `active_modifier_frame` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `replace` | `abstain` | `abstain` | 0.626 | 0.7449 | 0.0 | -0.7449 | `shadow_verb_frame` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:even:001` | `replace` | `abstain` | `abstain` | 0.7265 | 0.5392 | 0.0 | -0.7265 | `` | none |
| `active_shadow` | `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `replace` | `abstain` | `abstain` | 0.5444 | 0.6926 | 0.0 | -0.6926 | `` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `abstain` | `replace` | `replace` | 0.5626 | 0.6113 | 0.0 | -0.6113 | `active_noun_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:full:001` | `abstain` | `replace` | `replace` | 0.5631 | 0.5314 | 0.0 | -0.5631 | `` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `abstain` | `replace` | `replace` | 0.679 | 0.6892 | 0.0 | -0.6892 | `active_modifier_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `abstain` | `replace` | `replace` | 0.7496 | 0.7342 | 0.0 | -0.7496 | `active_noun_frame` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `abstain` | `replace` | `replace` | 0.7298 | 0.7096 | 0.0 | -0.7298 | `active_noun_frame` | none |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `abstain` | `replace` | `replace` | 0.683 | 0.734 | 0.0 | -0.734 | `active_noun_frame` | rescue |
| `phrase_no_winner` | `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `abstain` | `replace` | `replace` | 0.5938 | 0.6342 | 0.0 | -0.6342 | `active_noun_frame` | rescue |

## Limitations

- `offline_scorer_backed_validation_not_runtime_policy`
- `policy_applied_after_fresh_harness_scoring`
- `bounded_wave6_active_and_phrase_suites_only`

## Next Steps

- inspect policy failure cases before changing gates
- rerun the fixed-trace sweep only after scorer-backed misses are understood
