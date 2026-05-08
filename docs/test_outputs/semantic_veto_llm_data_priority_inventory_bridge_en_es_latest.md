# en-es Semantic Veto LLM Data Priority Inventory Bridge

- Status: `ok`
- Decision: `llm_data_priority_inventory_bridge_established`
- Generated: `2026-05-05T19:33:26+00:00`
- Inventory candidates: `100`
- Target-family missing: `84`
- Already scored trigger rows: `16`

## End-State Contract

Build a language-pair data-spend allocator that can identify the top-N trigger/target families most worth expensive LLM enrichment while leaving lower-priority words on cheaper evidence or ordinary replacement fallbacks.

The top-N list decides who gets expensive enrichment first. It does not decide that every other word must abstain.

## Stage Counts

| Stage | Count |
| --- | ---: |
| `needs_translation_target_shadow_family` | 84 |
| `trigger_target_pair_scored` | 16 |

## Top Inventory Bridge Rows

| Rank | Trigger | Stage | Need | Matched scored pairs | Next action | Scored packet |
| ---: | --- | --- | ---: | ---: | --- | --- |
| 1 | `even` | `trigger_target_pair_scored` | 0.9250 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 2 | `firm` | `trigger_target_pair_scored` | 0.9250 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 3 | `stretch` | `trigger_target_pair_scored` | 0.9168 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 4 | `full` | `trigger_target_pair_scored` | 0.9156 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 0, locked 0 |
| 5 | `wrong` | `trigger_target_pair_scored` | 0.9156 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 4, phrase 12, locked 4 |
| 6 | `trim` | `trigger_target_pair_scored` | 0.9068 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 7 | `foul` | `trigger_target_pair_scored` | 0.9031 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 8 | `waste` | `trigger_target_pair_scored` | 0.9031 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 9 | `cast` | `trigger_target_pair_scored` | 0.8768 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 10 | `meet` | `trigger_target_pair_scored` | 0.8756 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 0, locked 0 |
| 11 | `crash` | `trigger_target_pair_scored` | 0.8703 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 12 | `fix` | `trigger_target_pair_scored` | 0.8703 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 13 | `score` | `trigger_target_pair_scored` | 0.8703 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 4, phrase 8, locked 2 |
| 14 | `squeeze` | `trigger_target_pair_scored` | 0.8668 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 15 | `like` | `trigger_target_pair_scored` | 0.8556 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 4, locked 0 |
| 16 | `gross` | `trigger_target_pair_scored` | 0.8450 | 1 | `use_scored_pair_llm_packet_or_refresh_contexts` | active 0, shadow 0, phrase 0, locked 0 |
| 17 | `flush` | `needs_translation_target_shadow_family` | 0.9503 | 0 | `construct_translation_target_shadow_family` | - |
| 18 | `rough` | `needs_translation_target_shadow_family` | 0.9503 | 0 | `construct_translation_target_shadow_family` | - |
| 19 | `home` | `needs_translation_target_shadow_family` | 0.9468 | 0 | `construct_translation_target_shadow_family` | - |
| 20 | `out` | `needs_translation_target_shadow_family` | 0.9468 | 0 | `construct_translation_target_shadow_family` | - |
| 21 | `true` | `needs_translation_target_shadow_family` | 0.9342 | 0 | `construct_translation_target_shadow_family` | - |
| 22 | `better` | `needs_translation_target_shadow_family` | 0.9156 | 0 | `construct_translation_target_shadow_family` | - |
| 23 | `flash` | `needs_translation_target_shadow_family` | 0.9136 | 0 | `construct_translation_target_shadow_family` | - |
| 24 | `level` | `needs_translation_target_shadow_family` | 0.9136 | 0 | `construct_translation_target_shadow_family` | - |
| 25 | `separate` | `needs_translation_target_shadow_family` | 0.9136 | 0 | `construct_translation_target_shadow_family` | - |
| 26 | `bound` | `needs_translation_target_shadow_family` | 0.9068 | 0 | `construct_translation_target_shadow_family` | - |
| 27 | `slack` | `needs_translation_target_shadow_family` | 0.9068 | 0 | `construct_translation_target_shadow_family` | - |
| 28 | `split` | `needs_translation_target_shadow_family` | 0.9068 | 0 | `construct_translation_target_shadow_family` | - |
| 29 | `white` | `needs_translation_target_shadow_family` | 0.9068 | 0 | `construct_translation_target_shadow_family` | - |
| 30 | `blue` | `needs_translation_target_shadow_family` | 0.9031 | 0 | `construct_translation_target_shadow_family` | - |
| 31 | `fit` | `needs_translation_target_shadow_family` | 0.9031 | 0 | `construct_translation_target_shadow_family` | - |
| 32 | `smash` | `needs_translation_target_shadow_family` | 0.9031 | 0 | `construct_translation_target_shadow_family` | - |
| 33 | `fine` | `needs_translation_target_shadow_family` | 0.8956 | 0 | `construct_translation_target_shadow_family` | - |
| 34 | `cross` | `needs_translation_target_shadow_family` | 0.8942 | 0 | `construct_translation_target_shadow_family` | - |
| 35 | `color` | `needs_translation_target_shadow_family` | 0.8850 | 0 | `construct_translation_target_shadow_family` | - |
| 36 | `side` | `needs_translation_target_shadow_family` | 0.8850 | 0 | `construct_translation_target_shadow_family` | - |
| 37 | `subject` | `needs_translation_target_shadow_family` | 0.8850 | 0 | `construct_translation_target_shadow_family` | - |
| 38 | `control` | `needs_translation_target_shadow_family` | 0.8768 | 0 | `construct_translation_target_shadow_family` | - |
| 39 | `rule` | `needs_translation_target_shadow_family` | 0.8768 | 0 | `construct_translation_target_shadow_family` | - |
| 40 | `strain` | `needs_translation_target_shadow_family` | 0.8768 | 0 | `construct_translation_target_shadow_family` | - |
| 41 | `spare` | `needs_translation_target_shadow_family` | 0.8756 | 0 | `construct_translation_target_shadow_family` | - |
| 42 | `burn` | `needs_translation_target_shadow_family` | 0.8736 | 0 | `construct_translation_target_shadow_family` | - |
| 43 | `spot` | `needs_translation_target_shadow_family` | 0.8736 | 0 | `construct_translation_target_shadow_family` | - |
| 44 | `strip` | `needs_translation_target_shadow_family` | 0.8736 | 0 | `construct_translation_target_shadow_family` | - |
| 45 | `bar` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |
| 46 | `figure` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |
| 47 | `force` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |
| 48 | `hang` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |
| 49 | `number` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |
| 50 | `position` | `needs_translation_target_shadow_family` | 0.8703 | 0 | `construct_translation_target_shadow_family` | - |

## Fallback Tiers

- `llm_enriched_semantic_veto`
- `cheap_existing_semantic_veto_or_source_evidence`
- `ordinary_lexical_replacement_without_expensive_veto`
- `defer_or_review_only_when_rule_quality_or_user_policy_requires_it`

## Guardrails

| Check | Value |
| --- | --- |
| `inventory_only_rows_have_no_llm_packet` | `True` |
| `scored_rows_link_to_priority_scan` | `True` |
| `forbidden_fields_absent_from_bridge_features` | `True` |
| `rows_sorted_by_stage_then_need` | `True` |

## Limitations

- `inventory_candidates_are_english_headwords_without_spanish_target_families`
- `source_frequency_rank_is_not_yet_joined_for_every_inventory_candidate`
- `inventory_source_need_ranks_family_construction_value_not_runtime_veto_quality`
- `scored_context_llm_packets_are_available_only_for_triggers_already_present_in_the_priority_scan`

## Next Steps

- Construct Spanish target/shadow families for the top inventory-only rows before LLM evidence generation.
- Rerun the LLM data priority scan after those trigger/target pairs have scored contexts.
- Keep fallback policy explicit: non-enriched words continue through ordinary replacement or existing cheaper semantic evidence, not automatic abstain.
