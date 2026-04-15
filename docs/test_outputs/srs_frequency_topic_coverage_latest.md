# SRS Frequency Topic Coverage

- status: WARN
- pass_count: 4
- warn_count: 1
- fail_count: 0
- topic_columns_requested: sense_topics, topics, topic, profile_topics
- frontier_limit: 800

## Findings
- WARN `TOPIC_COLUMNS_ABSENT` [C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-en-coca.sqlite]: No requested topic columns are present, so profile-topic matching would rely on lexical exact-match fallback only. (sense_topics, topics, topic, profile_topics)
- PASS `TOPIC_COLUMNS_PRESENT` [C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-es-cde.sqlite]: Topic columns are present with non-empty rows. (sense_topics)
- PASS `FRONTIER_TOPICS_PRESENT` [C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-es-cde.sqlite]: Bootstrap frontier contains candidates with canonical topic metadata. (rows=800, canonical_rows=126)
- PASS `TOPIC_COLUMNS_PRESENT` [C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-ja-bccwj.sqlite]: Topic columns are present with non-empty rows. (sense_topics)
- PASS `FRONTIER_TOPICS_PRESENT` [C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-ja-bccwj.sqlite]: Bootstrap frontier contains candidates with canonical topic metadata. (rows=800, canonical_rows=101)

## Per-DB audit

### C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-en-coca.sqlite
- exists: True
- table_name: frequency
- row_count: 6100
- topic_columns_present: none
- topic_columns_missing: sense_topics, topics, topic, profile_topics
- any_topic_rows: 0
- frontier_row_count: 0
- frontier_rank_column: rank
- frontier_topic_columns: none
- frontier_rows_with_raw_topics: 0
- frontier_rows_with_canonical_topics: 0
- frontier_canonical_topic_coverage_ratio: 0.0
- frontier_top_canonical_topics: none

### C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-es-cde.sqlite
- exists: True
- table_name: frequency
- row_count: 2000
- topic_columns_present: sense_topics
- topic_columns_missing: topics, topic, profile_topics
- any_topic_rows: 239
- frontier_row_count: 800
- frontier_rank_column: id
- frontier_topic_columns: sense_topics
- frontier_rows_with_raw_topics: 126
- frontier_rows_with_canonical_topics: 126
- frontier_canonical_topic_coverage_ratio: 0.1575
- frontier_top_canonical_topics: lifestyle=42, sciences=40, natural_sciences=30, hobbies=27, sports=23, medicine=18, physical_sciences=16, mathematics=15, entertainment=14, anatomy=14

### C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-ja-bccwj.sqlite
- exists: True
- table_name: frequency
- row_count: 185136
- topic_columns_present: sense_topics
- topic_columns_missing: topics, topic, profile_topics
- any_topic_rows: 5294
- frontier_row_count: 800
- frontier_rank_column: core_rank
- frontier_topic_columns: sense_topics
- frontier_rows_with_raw_topics: 101
- frontier_rows_with_canonical_topics: 101
- frontier_canonical_topic_coverage_ratio: 0.12625
- frontier_top_canonical_topics: sciences=37, lifestyle=32, mathematics=21, natural_sciences=20, human_sciences=18, games=17, religion=15, hobbies=13, buddhism=13, board_games=11
