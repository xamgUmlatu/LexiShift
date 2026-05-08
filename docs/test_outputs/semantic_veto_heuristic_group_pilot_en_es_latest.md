# en-es Semantic Veto Heuristic Group Pilot

- Status: `ok`
- Decision: `heuristic_group_pilot_ready_for_manual_tests`
- Generated: `2026-05-05T01:45:57Z`
- Input fingerprint: `d823971d29c3e682612214cfb821ca223f0fb21cafe78b371089e7377c9c92c0`
- Candidate pool: `4112`
- Selected triggers: `29`
- Manual review rows: `29`
- Primary group selection: `pre_outcome_only_excludes_current_measured_triggers`
- Sentinel group selection: `outcome_informed_not_used_to_validate_heuristic`

## Methodology

Primary groups are selected before outcome review from cheap metadata only: English frequency rank, WordNet sense count, and WordNet POS count. Current measured triggers are excluded from those primary groups. The sentinel group is deliberately outcome-informed and must be used only as a regression anchor.

After this manifest is frozen, the manual step is to choose a Spanish target and write balanced test sentences for each trigger. The later scoring pass will compare group-level positive allow and negative abstain rates.

## Groups

### Core high-polysemy

- Group id: `core_high_polysemy`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Top-1000 English triggers with many WordNet senses across POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `man` | 95.0 | `1-500` | 12 | 2 | `noun:10, verb:2` |  |
| `work` | 115.0 | `1-500` | 34 | 2 | `noun:7, verb:27` |  |
| `call` | 125.0 | `1-500` | 41 | 2 | `noun:13, verb:28` |  |
| `help` | 155.0 | `1-500` | 12 | 2 | `noun:4, verb:8` |  |

### Core low-polysemy control

- Group id: `core_low_polysemy_control`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Top-1000 English triggers with few WordNet senses in one POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `yes` | 175.0 | `1-500` | 1 | 1 | `noun:1` |  |
| `money` | 215.0 | `1-500` | 3 | 1 | `noun:3` |  |
| `percent` | 265.0 | `1-500` | 1 | 1 | `noun:1` |  |
| `often` | 335.0 | `1-500` | 3 | 1 | `adverb:3` |  |

### Mid-rank high-polysemy

- Group id: `mid_high_polysemy`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Rank 1001-5000 English triggers with many senses across POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `green` | 1005.0 | `1001-2000` | 13 | 4 | `adjective:5, noun:6, adjective_satellite:1, verb:1` |  |
| `trade` | 1025.0 | `1001-2000` | 12 | 2 | `noun:7, verb:5` |  |
| `deep` | 1035.0 | `1001-2000` | 21 | 3 | `adjective:15, noun:3, adverb:3` |  |
| `particular` | 1045.0 | `1001-2000` | 9 | 2 | `adjective:6, noun:3` |  |

### Mid-rank low-polysemy control

- Group id: `mid_low_polysemy_control`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Rank 1001-5000 English triggers with few senses in one POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `therefore` | 1085.0 | `1001-2000` | 2 | 1 | `adverb:2` |  |
| `senate` | 1155.0 | `1001-2000` | 1 | 1 | `noun:1` |  |
| `participant` | 1185.0 | `1001-2000` | 2 | 1 | `noun:2` |  |
| `crisis` | 1295.0 | `1001-2000` | 2 | 1 | `noun:2` |  |

### Tail high-polysemy

- Group id: `tail_high_polysemy`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Rank >5000 English triggers with many senses across POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `upgrade` | 5005.0 | `>5000` | 11 | 2 | `noun:6, verb:5` |  |
| `yield` | 5025.0 | `>5000` | 17 | 2 | `noun:4, verb:13` |  |
| `hammer` | 5045.0 | `>5000` | 10 | 2 | `noun:8, verb:2` |  |
| `low` | 5135.0 | `>5000` | 15 | 4 | `adjective:10, noun:3, adverb:1, verb:1` |  |

### Tail low-polysemy control

- Group id: `tail_low_polysemy_control`
- Selection mode: `pre_outcome`
- Heuristic: `frequency_x_wordnet_polysemy`
- Description: Rank >5000 English triggers with few senses in one POS.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `unnecessary` | 5075.0 | `>5000` | 1 | 1 | `adjective:1` |  |
| `suitable` | 5085.0 | `>5000` | 2 | 1 | `adjective:2` |  |
| `purely` | 5105.0 | `>5000` | 1 | 1 | `adverb:1` |  |
| `prosecute` | 5125.0 | `>5000` | 3 | 1 | `verb:3` |  |

### Measured missing-rank high-failure sentinel

- Group id: `measured_missing_rank_high_failure_sentinel`
- Selection mode: `outcome_informed_sentinel`
- Heuristic: `outcome_informed_metadata_gap`
- Description: Currently measured high-failure triggers missing local source rank. This is not used to validate the frequency/polysemy heuristic.

| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `check` |  | `missing` | 38 | 2 | `noun:13, verb:25` | 5 |
| `order` |  | `missing` | 23 | 2 | `noun:14, verb:9` | 5 |
| `plant` |  | `missing` | 10 | 2 | `noun:4, verb:6` | 5 |
| `report` |  | `missing` | 13 | 2 | `noun:7, verb:6` | 6 |
| `play` |  | `missing` | 52 | 2 | `noun:17, verb:35` | 4 |

## Manual Review Packet

| Group | Trigger | Rank bin | Senses | POS | Case slots |
| --- | --- | --- | ---: | ---: | ---: |
| `core_high_polysemy` | `man` | `1-500` | 12 | 2 | 5 |
| `core_high_polysemy` | `work` | `1-500` | 34 | 2 | 5 |
| `core_high_polysemy` | `call` | `1-500` | 41 | 2 | 5 |
| `core_high_polysemy` | `help` | `1-500` | 12 | 2 | 5 |
| `core_low_polysemy_control` | `yes` | `1-500` | 1 | 1 | 5 |
| `core_low_polysemy_control` | `money` | `1-500` | 3 | 1 | 5 |
| `core_low_polysemy_control` | `percent` | `1-500` | 1 | 1 | 5 |
| `core_low_polysemy_control` | `often` | `1-500` | 3 | 1 | 5 |
| `mid_high_polysemy` | `green` | `1001-2000` | 13 | 4 | 5 |
| `mid_high_polysemy` | `trade` | `1001-2000` | 12 | 2 | 5 |
| `mid_high_polysemy` | `deep` | `1001-2000` | 21 | 3 | 5 |
| `mid_high_polysemy` | `particular` | `1001-2000` | 9 | 2 | 5 |
| `mid_low_polysemy_control` | `therefore` | `1001-2000` | 2 | 1 | 5 |
| `mid_low_polysemy_control` | `senate` | `1001-2000` | 1 | 1 | 5 |
| `mid_low_polysemy_control` | `participant` | `1001-2000` | 2 | 1 | 5 |
| `mid_low_polysemy_control` | `crisis` | `1001-2000` | 2 | 1 | 5 |
| `tail_high_polysemy` | `upgrade` | `>5000` | 11 | 2 | 5 |
| `tail_high_polysemy` | `yield` | `>5000` | 17 | 2 | 5 |
| `tail_high_polysemy` | `hammer` | `>5000` | 10 | 2 | 5 |
| `tail_high_polysemy` | `low` | `>5000` | 15 | 4 | 5 |
| `tail_low_polysemy_control` | `unnecessary` | `>5000` | 1 | 1 | 5 |
| `tail_low_polysemy_control` | `suitable` | `>5000` | 2 | 1 | 5 |
| `tail_low_polysemy_control` | `purely` | `>5000` | 1 | 1 | 5 |
| `tail_low_polysemy_control` | `prosecute` | `>5000` | 3 | 1 | 5 |
| `measured_missing_rank_high_failure_sentinel` | `check` | `missing` | 38 | 2 | 5 |
| `measured_missing_rank_high_failure_sentinel` | `order` | `missing` | 23 | 2 | 5 |
| `measured_missing_rank_high_failure_sentinel` | `plant` | `missing` | 10 | 2 | 5 |
| `measured_missing_rank_high_failure_sentinel` | `report` | `missing` | 13 | 2 | 5 |
| `measured_missing_rank_high_failure_sentinel` | `play` | `missing` | 52 | 2 | 5 |

## Limitations

- `primary_groups_do_not_have_manual_cases_yet`
- `outcome_informed_sentinel_group_must_not_validate_frequency_polysemy_heuristic`
- `wordnet_polysemy_is_a_proxy_and_can_miss_browser_phrase_difficulty`
- `source_frequency_pack_is_local_and_sparser_than_a_full_corpus_rank_list`
- `spanish_target_selection_still_requires_manual_or_translation_family_review`

## Next Steps

- Freeze this group manifest before writing manual cases.
- For each trigger, choose one plausible Spanish replacement target and at least one shadow sense.
- Write two positive, two shadow-negative, and one phrase/no-winner sentence per trigger where possible.
- Score the filled manual packet with the frozen veto candidate and compare group-level positive allow plus negative abstain rates.
- Use only the pre-outcome groups to judge whether frequency and polysemy predict difficulty; use the sentinel group as a regression anchor.
