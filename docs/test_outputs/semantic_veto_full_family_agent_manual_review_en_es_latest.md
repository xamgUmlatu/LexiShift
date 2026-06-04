# en-es Semantic Veto Full-Family Agent Manual Review

- Status: `agent_review_complete_user_approval_required`
- Review authority: `codex_agent_recommendation_not_user_approval`
- Input packet: `docs/test_outputs/semantic_veto_full_family_human_review_packet_en_es_latest.json`
- Families reviewed: `10`
- Cases reviewed: `34`
- Trusted rows now: `0`

This review does not mark any row `approved_by_user`. It is an agent semantic
review of the current pilot packet so we do not forget which rows are plausible,
which are broken, and which must be rewritten before any product-quality claim.

## Summary

| Area | Finding |
| --- | --- |
| Families | 4 aligned mappings need independent context rewrites: `december -> diciembre`, `emotion -> emoción`, `dentist -> dentista`, `bouillon -> caldo`. |
| Families | 3 mappings are probably salvageable only after correcting the active sense: `break -> quebrar`, `bridle -> reprimir`, `control -> gobernar`. |
| Families | 3 mappings look questionable or wrong until the original rulegen evidence is audited: `bar -> cercar`, `offset -> distancia`, `demand -> deducción`. |
| Positive rows | 4 can be kept only after independent context rewrites; 8 should be rejected or relabeled. |
| Shadow rows | All 12 remain blocked by placeholder shadow targets. About 10 look like plausible abstain cases after real competitor targets are supplied; 2 are ambiguous or possibly active. |
| Phrase/no-winner rows | 2 look usable after review or minor rewrite; 3 are filename token-boundary diagnostics; 5 are questionable or should be relabeled. |

## Family Review

| Family | Active Sense Recommendation | Disposition | Rationale |
| --- | --- | --- | --- |
| `break -> quebrar` | `mismatched` | `salvage_with_corrected_active_sense` | `quebrar` can match break as fracture/shatter, but the packet active gloss and positive rows are interruption sense. |
| `bar -> cercar` | `mismatched` | `source_target_mapping_questionable` | `cercar` means surround/fence in/besiege; the active row is an alcohol bar. The family may only be salvageable through a block/enclose sense. |
| `offset -> distancia` | `mismatched` | `source_target_mapping_questionable` | `distancia` means distance; current active and positive rows are onset/outset sense. |
| `bridle -> reprimir` | `mismatched` | `salvage_with_corrected_active_sense` | `reprimir` maps to repress/restrain, but current active is horse headgear. |
| `december -> diciembre` | `aligned` | `aligned_but_contexts_need_rewrite` | Mapping is straightforward; positive row is definition-circular. |
| `emotion -> emoción` | `aligned` | `aligned_but_contexts_need_rewrite` | Mapping is aligned; positive row is definition-circular. |
| `dentist -> dentista` | `aligned` | `aligned_but_contexts_need_rewrite` | Mapping is aligned; positive row is definition-circular. |
| `bouillon -> caldo` | `aligned` | `aligned_but_contexts_need_rewrite` | Mapping is aligned; positive row is definition-circular. |
| `control -> gobernar` | `mismatched` | `salvage_with_corrected_active_sense` | `gobernar` can map to govern/rule/control as a verb; current active is noun power/control and the positive row is `under control`. |
| `demand -> deducción` | `mismatched` | `source_target_mapping_questionable` | `deducción` means deduction; demand/request/economic demand does not match without unexpected source evidence. |

## Case Review

| Case | Current Type | Recommendation | Recommended Decision | Notes |
| --- | --- | --- | --- | --- |
| `break:001` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | Telephone interruption sense, not `quebrar`. |
| `break:002` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | Break in the action is interruption sense, not fracture/shatter. |
| `break:003` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | End a lucky streak, not `quebrar`; placeholder shadow target blocks trust. |
| `break:004` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Big break means opportunity; placeholder shadow target blocks trust. |
| `break:005` | `phrase_no_winner` | `diagnostic_only_or_rewrite` | `abstain_if_trigger_behavior_confirmed` | Filename token-boundary artifact. |
| `bar:001` | `positive_active` | `reject_or_relabel` | `abstain` | Alcohol bar is not `cercar`. |
| `bar:002` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Prevent entry is not the alcohol-bar active sense and is probably not `cercar`; synthetic context plus placeholder target. |
| `bar:003` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Food/drink counter is not `cercar`; placeholder target. |
| `bar:004` | `phrase_no_winner` | `diagnostic_only_or_rewrite` | `abstain_if_trigger_behavior_confirmed` | Filename token-boundary artifact. |
| `offset:001` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | Unnatural adaptation of early start, not `distancia`. |
| `offset:002` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | From the offset means from the outset, not distance. |
| `offset:003` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Counterbalance sense; placeholder target. |
| `offset:004` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Compensating equivalent; synthetic context plus placeholder target. |
| `offset:005` | `phrase_no_winner` | `usable_after_review_or_minor_rewrite` | `abstain` | Saved-search query is a reasonable metalinguistic no-winner row. |
| `bridle:001` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | Horse headgear is not `reprimir`; context is circular. |
| `bridle:002` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Took offense, not `reprimir`; synthetic context plus placeholder target. |
| `bridle:003` | `shadow_negative` | `ambiguous_or_possible_active` | `review_required` | A bridle to temper means restraint and may be close to `reprimir`. |
| `bridle:004` | `phrase_no_winner` | `usable_after_review_or_minor_rewrite` | `abstain` | Saved-search query is a reasonable metalinguistic no-winner row. |
| `december:001` | `positive_active` | `keep_only_after_independent_context_rewrite` | `replace` | Correct sense, but definition-circular. |
| `december:002` | `phrase_no_winner` | `questionable_or_relabel` | `review_required` | A column titled December may still be valid replacement text. |
| `emotion:001` | `positive_active` | `keep_only_after_independent_context_rewrite` | `replace` | Correct sense, but definition-circular. |
| `emotion:002` | `phrase_no_winner` | `questionable_or_relabel` | `review_required` | A column titled emotion may still be valid replacement text. |
| `dentist:001` | `positive_active` | `keep_only_after_independent_context_rewrite` | `replace` | Correct sense, but definition-circular. |
| `dentist:002` | `phrase_no_winner` | `questionable_or_relabel` | `review_required` | A tab labeled dentist may still be valid replacement text. |
| `bouillon:001` | `positive_active` | `keep_only_after_independent_context_rewrite` | `replace` | Correct sense, but definition-circular. |
| `bouillon:002` | `phrase_no_winner` | `diagnostic_only_or_rewrite` | `abstain_if_trigger_behavior_confirmed` | Filename token-boundary artifact. |
| `control:001` | `positive_active` | `reject_or_relabel` | `abstain_or_rewrite` | Under control is not `gobernar`. |
| `control:002` | `shadow_negative` | `ambiguous_or_possible_active` | `review_required` | Control the budget may be close to active if the family is corrected to an authoritative-control verb sense. |
| `control:003` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Disease control is management/regulation, not `gobernar`; placeholder target. |
| `control:004` | `phrase_no_winner` | `questionable_or_relabel` | `shadow_negative_or_no_winner_after_review` | A column titled control may be a control-condition sense, not clean no-winner. |
| `demand:001` | `positive_active` | `reject_or_relabel` | `abstain_or_remove_family` | Urgent request is not `deducción`. |
| `demand:002` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Request/insist sense, not `deducción`; family mapping questionable and target placeholder. |
| `demand:003` | `shadow_negative` | `blocked_but_likely_abstain` | `abstain_after_real_shadow_target` | Economic demand, not `deducción`; family mapping questionable and target placeholder. |
| `demand:004` | `phrase_no_winner` | `questionable_or_relabel` | `shadow_negative_or_remove_family_after_review` | Column likely points to economic-demand sense, not clean no-winner. |

## Next Steps

1. Do not use this packet for product accuracy or scorer promotion.
2. Build the first trusted-eval candidate lane from the 4 aligned families, but rewrite positive contexts independently and replace questionable no-winner rows.
3. For `break`, `bridle`, and `control`, correct the active sense before authoring trusted rows.
4. For `bar`, `offset`, and `demand`, audit the original rulegen source-target mapping before spending review or LLM effort.
5. Replace placeholder shadow targets with real Spanish competitor targets before trusting shadow-negative rows.
