# en-es Semantic Veto Representative Band Performance

- Status: `ok`
- Decision: `representative_band_performance_established`
- Generated: `2026-05-05T21:46:44Z`
- Representative cases: `120`
- Families / triggers: `19` / `19`
- Source-rank known rows: `33`
- Source Zipf-known rows: `120`
- Target-rank known rows: `0`
- WordNet-known rows: `0`

## Answer To The Band Question

- Same-band-performance claim: `not_supported`
- Main read: The representative-proxy lane does not prove that bands perform the same. It shows low positive allow across most source-rank bands, while the denser Zipf fallback suggests very common triggers may be especially abstain-heavy. That is a promising clue, not yet a stable curve.
- Product read: Current browser-like behavior is conservative: negative rows are all abstained, while positive allow is 24.5%. That is safer than over-replacing, but it misses many good replacements.
- LLM-data read: The immediate LLM-data need is not proven to be one rank band. The stronger finding is that we should add denser, programmatic frequency metadata and then test whether very-common trigger abstention persists before using a top-N difficulty formula confidently.

## Overall Representative Proxy

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `overall` | `120` | `53` | `67` | `24.5%` | `100.0%` | `40` | `0` | `50.6` | `fail` |

## Source Trigger Rank

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `1-500` | `6` | `3` | `3` | `33.3%` | `100.0%` | `2` | `0` | `2.6` | `fail` |
| `501-1000` | `6` | `3` | `3` | `0.0%` | `100.0%` | `3` | `0` | `1.2` | `fail` |
| `2001-5000` | `14` | `6` | `8` | `50.0%` | `100.0%` | `3` | `0` | `8.2` | `fail` |
| `>5000` | `7` | `3` | `4` | `33.3%` | `100.0%` | `2` | `0` | `3.4` | `fail` |
| `missing` | `87` | `38` | `49` | `21.1%` | `100.0%` | `30` | `0` | `35.2` | `fail` |

## Source Zipf Frequency

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | `68` | `30` | `38` | `13.3%` | `100.0%` | `26` | `0` | `24.0` | `fail` |
| `zipf_4_to_5_common` | `52` | `23` | `29` | `39.1%` | `100.0%` | `14` | `0` | `26.6` | `fail` |

## Source Rank By Gold Winner Type

| Source Rank | Winner Type | Cases | Pos allow | Neg abstain | Pos abstain | Neg allow |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1-500` | `active` | `3` | `33.3%` | `n/a` | `2` | `0` |
| `1-500` | `shadow` | `2` | `n/a` | `100.0%` | `0` | `0` |
| `1-500` | `none` | `1` | `n/a` | `100.0%` | `0` | `0` |
| `501-1000` | `active` | `3` | `0.0%` | `n/a` | `3` | `0` |
| `501-1000` | `shadow` | `2` | `n/a` | `100.0%` | `0` | `0` |
| `501-1000` | `none` | `1` | `n/a` | `100.0%` | `0` | `0` |
| `2001-5000` | `active` | `6` | `50.0%` | `n/a` | `3` | `0` |
| `2001-5000` | `shadow` | `6` | `n/a` | `100.0%` | `0` | `0` |
| `2001-5000` | `none` | `2` | `n/a` | `100.0%` | `0` | `0` |
| `>5000` | `active` | `3` | `33.3%` | `n/a` | `2` | `0` |
| `>5000` | `shadow` | `3` | `n/a` | `100.0%` | `0` | `0` |
| `>5000` | `none` | `1` | `n/a` | `100.0%` | `0` | `0` |
| `missing` | `active` | `38` | `21.1%` | `n/a` | `30` | `0` |
| `missing` | `shadow` | `35` | `n/a` | `100.0%` | `0` | `0` |
| `missing` | `none` | `14` | `n/a` | `100.0%` | `0` | `0` |

## Declared Ambiguity

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `medium` | `11` | `5` | `6` | `40.0%` | `100.0%` | `3` | `0` | `5.6` | `fail` |
| `high` | `63` | `28` | `35` | `21.4%` | `100.0%` | `22` | `0` | `25.2` | `fail` |
| `missing` | `46` | `20` | `26` | `25.0%` | `100.0%` | `15` | `0` | `19.8` | `fail` |

## Context Source

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `agent_curated_corpus_like_app_candidate_contexts` | `25` | `15` | `10` | `13.3%` | `100.0%` | `13` | `0` | `4.8` | `fail` |
| `existing_sentence_veto_v10_representative_proxy` | `95` | `38` | `57` | `28.9%` | `100.0%` | `27` | `0` | `45.8` | `fail` |

## Metadata Profile

| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `source_rank_known` | `33` | `15` | `18` | `33.3%` | `100.0%` | `10` | `0` | `15.4` | `fail` |
| `source_rank_missing` | `87` | `38` | `49` | `21.1%` | `100.0%` | `30` | `0` | `35.2` | `fail` |
| `target_rank_missing` | `120` | `53` | `67` | `24.5%` | `100.0%` | `40` | `0` | `50.6` | `fail` |
| `wordnet_missing` | `120` | `53` | `67` | `24.5%` | `100.0%` | `40` | `0` | `50.6` | `fail` |

## Trigger Risk Summary

| Trigger | Cases | Failures | Source Rank | Zipf Band | Ambiguity | Pos allow | Neg abstain |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| `ball` | `7` | `3` | `missing` | `zipf_5_plus_very_common` | `missing` | `0.0%` | `100.0%` |
| `park` | `7` | `3` | `missing` | `zipf_5_plus_very_common` | `missing` | `0.0%` | `100.0%` |
| `plant` | `7` | `3` | `missing` | `zipf_4_to_5_common` | `high` | `0.0%` | `100.0%` |
| `bank` | `6` | `3` | `501-1000` | `zipf_5_plus_very_common` | `high` | `0.0%` | `100.0%` |
| `drink` | `6` | `3` | `missing` | `zipf_4_to_5_common` | `missing` | `0.0%` | `100.0%` |
| `play` | `6` | `3` | `missing` | `zipf_5_plus_very_common` | `high` | `0.0%` | `100.0%` |
| `board` | `7` | `2` | `>5000` | `zipf_5_plus_very_common` | `high` | `33.3%` | `100.0%` |
| `branch` | `7` | `2` | `missing` | `zipf_4_to_5_common` | `high` | `33.3%` | `100.0%` |
| `match` | `7` | `2` | `2001-5000` | `zipf_5_plus_very_common` | `high` | `33.3%` | `100.0%` |
| `spring` | `7` | `2` | `missing` | `zipf_4_to_5_common` | `missing` | `33.3%` | `100.0%` |
| `table` | `7` | `2` | `missing` | `zipf_5_plus_very_common` | `missing` | `33.3%` | `100.0%` |
| `watch` | `6` | `2` | `1-500` | `zipf_5_plus_very_common` | `high` | `33.3%` | `100.0%` |
| `check` | `5` | `2` | `missing` | `zipf_5_plus_very_common` | `high` | `0.0%` | `100.0%` |
| `order` | `5` | `2` | `missing` | `zipf_5_plus_very_common` | `high` | `0.0%` | `100.0%` |
| `report` | `5` | `2` | `missing` | `zipf_5_plus_very_common` | `medium` | `0.0%` | `100.0%` |

## Sample Warnings

- `source_rank_mostly_missing`: 87 of 120 representative rows lack source-rank metadata, so frequency-band curves are still fragile.
- `source_rank_small_cells`: Some source_rank cells have fewer than 10 cases: 1-500, 501-1000, >5000. Treat their rates as directional only.

## Limitations

- `representative_proxy_is_not_final_browser_distribution`
- `source_rank_known_rows_are_sparse`
- `wordfreq_zipf_is_a_frequency_proxy_not_a_corpus_rank_or_cefr_level`
- `wordnet_and_target_rank_are_missing_for_the_current_representative_proxy`
- `agent_curated_gap_rows_need_human_review_before_promotion_claims`
- `current_policy_is_so_conservative_that_negative_bands_saturate_at_abstain`

## Next Steps

- Use this report to separate real product behavior from old authored stress-lane behavior.
- Improve metadata coverage for the representative lane before claiming a beginner/intermediate/advanced curve.
- Rerun formula and threshold bakeoffs on representative case traces, but keep source-rank-known and source-rank-missing rows separate.
- Add observed browser contexts or reviewed LLM rows where representative bands are sparse or metadata-missing.
