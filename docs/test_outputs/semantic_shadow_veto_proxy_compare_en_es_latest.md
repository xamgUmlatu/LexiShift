# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T21:51:19Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 93.9% | 80.0% | 20.0% | 98.5% | 5.1% |
| borrowed_trigger_auto_shadows | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 93.2% | 100.0% | 0.0% | 100.0% | 7.2% |
| no_shadows | rulegen_top3_plus_forward_gloss | 93.2% | 0.0% | 100.0% | 93.2% | 0.0% |

## Details

### curated_shadows
- Label: `Curated overlap oracle`
- Seed mode: `benchmark_reviewed`
- Policy: `gold_overlap_oracle`
- Overall accuracy: `100.0%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:overlap_target_count:1 | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:trigger_shape:unigram | 137 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:top1_expected | 121 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:smoke | 78 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 70 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 33 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 27 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_target_count:2 | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:overlap_topology:shared_trigger | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:job | 9 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 4 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:field_area_country | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |

### reviewed_auto_shadows
- Label: `Reviewed-trigger auto shadows`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Overall accuracy: `100.0%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `0.0%`
- Delta vs curated abstain recall: `0.0%`
- Delta vs curated harmful allow: `0.0%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:overlap_target_count:1 | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:trigger_shape:unigram | 137 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:top1_expected | 121 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:smoke | 78 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 70 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 33 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 27 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_target_count:2 | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:overlap_topology:shared_trigger | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:job | 9 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 4 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:field_area_country | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |

### auto_shadows
- Label: `Source-only auto shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Overall accuracy: `93.9%`
- Abstain recall on ambiguous rows: `80.0%`
- Harmful allow rate: `20.0%`
- Allow precision: `98.5%`
- Overblocking rate: `5.1%`
- Delta vs curated accuracy: `-6.1%`
- Delta vs curated abstain recall: `-20.0%`
- Delta vs curated harmful allow: `20.0%`
- Delta vs curated overblocking: `5.1%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:overlap_target_count:1 | 138 | 94.9% | n/a | n/a | 5.1% |
| dimension:overlap_topology:singleton_trigger | 138 | 94.9% | n/a | n/a | 5.1% |
| dimension:trigger_shape:unigram | 137 | 93.4% | 80.0% | 20.0% | 5.5% |
| dimension:reviewed_expectation:top1_expected | 121 | 93.4% | 88.9% | 11.1% | 6.2% |
| dimension:tier:smoke | 78 | 94.9% | 80.0% | 20.0% | 4.1% |
| dimension:tier:hard | 70 | 92.9% | 80.0% | 20.0% | 6.2% |
| dimension:pos:noun | 33 | 75.8% | 66.7% | 33.3% | 22.2% |
| dimension:reviewed_expectation:expected_only | 27 | 96.3% | 0.0% | 100.0% | 0.0% |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_target_count:2 | 10 | 80.0% | 80.0% | 20.0% | n/a |
| dimension:overlap_topology:shared_trigger | 10 | 80.0% | 80.0% | 20.0% | n/a |
| dimension:semantic_family:job | 9 | 66.7% | 0.0% | 100.0% | 14.3% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 4 | 75.0% | 100.0% | 0.0% | 50.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:field_area_country | 3 | 66.7% | n/a | n/a | 33.3% |
| dimension:semantic_family:path_route | 3 | 0.0% | n/a | n/a | 100.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `trabajo` / `job` gold=['cargo'] promoted=[] cases=['en-es:trabajo'] tiers=['smoke'] tags=['family:job']
- Sample false-abstain rows:
  - `camino` / `road` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `path` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `campo` / `field` promoted=['área'] cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `cargo` / `position` promoted=['plaza'] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']

### borrowed_trigger_auto_shadows
- Label: `Source-only borrowed-trigger shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Overall accuracy: `93.2%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `7.2%`
- Delta vs curated accuracy: `-6.8%`
- Delta vs curated abstain recall: `0.0%`
- Delta vs curated harmful allow: `0.0%`
- Delta vs curated overblocking: `7.2%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:overlap_target_count:1 | 138 | 92.8% | n/a | n/a | 7.2% |
| dimension:overlap_topology:singleton_trigger | 138 | 92.8% | n/a | n/a | 7.2% |
| dimension:trigger_shape:unigram | 137 | 92.7% | 100.0% | 0.0% | 7.9% |
| dimension:reviewed_expectation:top1_expected | 121 | 91.7% | 100.0% | 0.0% | 8.9% |
| dimension:tier:smoke | 78 | 93.6% | 100.0% | 0.0% | 6.8% |
| dimension:tier:hard | 70 | 92.9% | 100.0% | 0.0% | 7.7% |
| dimension:pos:noun | 33 | 75.8% | 100.0% | 0.0% | 29.6% |
| dimension:reviewed_expectation:expected_only | 27 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_target_count:2 | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:overlap_topology:shared_trigger | 10 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:job | 9 | 77.8% | 100.0% | 0.0% | 28.6% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 4 | 75.0% | 100.0% | 0.0% | 50.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:field_area_country | 3 | 66.7% | n/a | n/a | 33.3% |
| dimension:semantic_family:path_route | 3 | 0.0% | n/a | n/a | 100.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 50.0% | n/a | n/a | 50.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample false-abstain rows:
  - `banco` / `bank` promoted=['escuela'] cases=['en-es:banco'] tiers=['smoke'] tags=['family:bank_bench']
  - `camino` / `road` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `path` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `campo` / `field` promoted=['área'] cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']

### no_shadows
- Label: `No shadow veto`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `none`
- Overall accuracy: `93.2%`
- Abstain recall on ambiguous rows: `0.0%`
- Harmful allow rate: `100.0%`
- Allow precision: `93.2%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-6.8%`
- Delta vs curated abstain recall: `-100.0%`
- Delta vs curated harmful allow: `100.0%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:overlap_target_count:1 | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 138 | 100.0% | n/a | n/a | 0.0% |
| dimension:trigger_shape:unigram | 137 | 92.7% | 0.0% | 100.0% | 0.0% |
| dimension:reviewed_expectation:top1_expected | 121 | 92.6% | 0.0% | 100.0% | 0.0% |
| dimension:tier:smoke | 78 | 93.6% | 0.0% | 100.0% | 0.0% |
| dimension:tier:hard | 70 | 92.9% | 0.0% | 100.0% | 0.0% |
| dimension:pos:noun | 33 | 81.8% | 0.0% | 100.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 27 | 96.3% | 0.0% | 100.0% | 0.0% |
| dimension:pos:verb | 15 | 73.3% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 69.2% | 0.0% | 100.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_target_count:2 | 10 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:overlap_topology:shared_trigger | 10 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:semantic_family:job | 9 | 77.8% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 66.7% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 80.0% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 4 | 50.0% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:field_area_country | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `coger` / `take` gold=['llevar'] promoted=[] cases=['en-es:coger'] tiers=['hard'] tags=['family:take_carry', 'hazard:phrase_sensitive', 'hazard:slang_leakage']
  - `cuadro` / `table` gold=['tabla'] promoted=[] cases=['en-es:cuadro'] tiers=['hard'] tags=['family:table_board_chart']
  - `llevar` / `take` gold=['coger'] promoted=[] cases=['en-es:llevar'] tiers=['smoke'] tags=['family:take_carry', 'hazard:phrase_sensitive']
  - `malla` / `net` gold=['red'] promoted=[] cases=['en-es:malla'] tiers=['hard'] tags=['family:net_mesh_network']
