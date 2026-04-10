# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T22:05:50Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 97.7% | 87.9% | 12.1% | 97.3% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 88.0% | 48.5% | 51.5% | 89.0% | 2.8% |
| borrowed_trigger_auto_shadows | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 88.0% | 57.6% | 42.4% | 90.6% | 4.9% |
| no_shadows | rulegen_top3_plus_forward_gloss | 81.1% | 0.0% | 100.0% | 81.1% | 0.0% |

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
| dimension:trigger_shape:unigram | 164 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:1 | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 140 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:smoke | 93 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 82 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 35 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:overlap_target_count:2 | 20 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:path_route | 10 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:4 | 4 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |

### reviewed_auto_shadows
- Label: `Reviewed-trigger auto shadows`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Overall accuracy: `97.7%`
- Abstain recall on ambiguous rows: `87.9%`
- Harmful allow rate: `12.1%`
- Allow precision: `97.3%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-2.3%`
- Delta vs curated abstain recall: `-12.1%`
- Delta vs curated harmful allow: `12.1%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 97.6% | 87.9% | 12.1% | 0.0% |
| dimension:overlap_target_count:1 | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 140 | 98.6% | 92.0% | 8.0% | 0.0% |
| dimension:tier:smoke | 93 | 95.7% | 76.5% | 23.5% | 0.0% |
| dimension:tier:hard | 82 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 60 | 93.3% | 86.2% | 13.8% | 0.0% |
| dimension:reviewed_expectation:expected_only | 35 | 94.3% | 75.0% | 25.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 87.9% | 87.9% | 12.1% | n/a |
| dimension:overlap_target_count:2 | 20 | 80.0% | 80.0% | 20.0% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 63.6% | 33.3% | 66.7% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:path_route | 10 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:4 | 4 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `terreno` / `land` gold=['tierra'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']
  - `terreno` / `ground` gold=['tierra'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']
  - `terreno` / `field` gold=['campo'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']
  - `tierra` / `ground` gold=['terreno'] promoted=[] cases=['en-es:tierra'] tiers=['smoke'] tags=['family:field_area_country']

### auto_shadows
- Label: `Source-only auto shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Overall accuracy: `88.0%`
- Abstain recall on ambiguous rows: `48.5%`
- Harmful allow rate: `51.5%`
- Allow precision: `89.0%`
- Overblocking rate: `2.8%`
- Delta vs curated accuracy: `-12.0%`
- Delta vs curated abstain recall: `-51.5%`
- Delta vs curated harmful allow: `51.5%`
- Delta vs curated overblocking: `2.8%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 87.2% | 48.5% | 51.5% | 3.1% |
| dimension:overlap_target_count:1 | 142 | 97.2% | n/a | n/a | 2.8% |
| dimension:overlap_topology:singleton_trigger | 142 | 97.2% | n/a | n/a | 2.8% |
| dimension:reviewed_expectation:top1_expected | 140 | 90.0% | 60.0% | 40.0% | 3.5% |
| dimension:tier:smoke | 93 | 89.2% | 52.9% | 47.1% | 2.6% |
| dimension:tier:hard | 82 | 86.6% | 43.8% | 56.2% | 3.0% |
| dimension:pos:noun | 60 | 66.7% | 41.4% | 58.6% | 9.7% |
| dimension:reviewed_expectation:expected_only | 35 | 80.0% | 12.5% | 87.5% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 48.5% | 48.5% | 51.5% | n/a |
| dimension:overlap_target_count:2 | 20 | 45.0% | 45.0% | 55.0% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 15 | 53.3% | 25.0% | 75.0% | 14.3% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 54.5% | 16.7% | 83.3% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 60.0% | 42.9% | 57.1% | 0.0% |
| dimension:semantic_family:path_route | 10 | 60.0% | 66.7% | 33.3% | 50.0% |
| dimension:overlap_target_count:3 | 9 | 55.6% | 55.6% | 44.4% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:4 | 4 | 50.0% | 50.0% | 50.0% | n/a |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] cases=['en-es:carretera'] tiers=['smoke'] tags=['family:path_route']
  - `empleo` / `employment` gold=['ocupación'] promoted=[] cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `empleo` / `work` gold=['trabajo'] promoted=[] cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `ocupación` / `job` gold=['cargo', 'empleo', 'trabajo'] promoted=[] cases=['en-es:ocupación'] tiers=['hard'] tags=['family:job']
- Sample false-abstain rows:
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `cargo` / `position` promoted=['plaza'] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] tiers=['hard']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] tiers=['smoke'] tags=['family:path_route']

### borrowed_trigger_auto_shadows
- Label: `Source-only borrowed-trigger shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Overall accuracy: `88.0%`
- Abstain recall on ambiguous rows: `57.6%`
- Harmful allow rate: `42.4%`
- Allow precision: `90.6%`
- Overblocking rate: `4.9%`
- Delta vs curated accuracy: `-12.0%`
- Delta vs curated abstain recall: `-42.4%`
- Delta vs curated harmful allow: `42.4%`
- Delta vs curated overblocking: `4.9%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 87.2% | 57.6% | 42.4% | 5.3% |
| dimension:overlap_target_count:1 | 142 | 95.1% | n/a | n/a | 4.9% |
| dimension:overlap_topology:singleton_trigger | 142 | 95.1% | n/a | n/a | 4.9% |
| dimension:reviewed_expectation:top1_expected | 140 | 88.6% | 64.0% | 36.0% | 6.1% |
| dimension:tier:smoke | 93 | 88.2% | 58.8% | 41.2% | 5.3% |
| dimension:tier:hard | 82 | 87.8% | 56.2% | 43.8% | 4.5% |
| dimension:pos:noun | 60 | 68.3% | 51.7% | 48.3% | 16.1% |
| dimension:reviewed_expectation:expected_only | 35 | 85.7% | 37.5% | 62.5% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 57.6% | 57.6% | 42.4% | n/a |
| dimension:overlap_target_count:2 | 20 | 55.0% | 55.0% | 45.0% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 15 | 66.7% | 62.5% | 37.5% | 28.6% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 54.5% | 16.7% | 83.3% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 60.0% | 42.9% | 57.1% | 0.0% |
| dimension:semantic_family:path_route | 10 | 60.0% | 66.7% | 33.3% | 50.0% |
| dimension:overlap_target_count:3 | 9 | 55.6% | 55.6% | 44.4% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:4 | 4 | 75.0% | 75.0% | 25.0% | n/a |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 50.0% | n/a | n/a | 50.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] cases=['en-es:carretera'] tiers=['smoke'] tags=['family:path_route']
  - `empleo` / `employment` gold=['ocupación'] promoted=[] cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `ocupación` / `job` gold=['cargo', 'empleo', 'trabajo'] promoted=[] cases=['en-es:ocupación'] tiers=['hard'] tags=['family:job']
  - `ocupación` / `employment` gold=['empleo'] promoted=[] cases=['en-es:ocupación'] tiers=['hard'] tags=['family:job']
  - `reja` / `grille` gold=['rejilla'] promoted=[] cases=['en-es:reja'] tiers=['hard'] tags=['family:net_mesh_network']
- Sample false-abstain rows:
  - `banco` / `bank` promoted=['escuela'] cases=['en-es:banco'] tiers=['smoke'] tags=['family:bank_bench']
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `cargo` / `position` promoted=['plaza'] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `cargo` / `post` promoted=['orden'] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `marco` / `frame` promoted=['tabla', 'cuadro'] cases=['en-es:marco'] tiers=['hard']

### no_shadows
- Label: `No shadow veto`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `none`
- Overall accuracy: `81.1%`
- Abstain recall on ambiguous rows: `0.0%`
- Harmful allow rate: `100.0%`
- Allow precision: `81.1%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-18.9%`
- Delta vs curated abstain recall: `-100.0%`
- Delta vs curated harmful allow: `100.0%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 79.9% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_target_count:1 | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 140 | 82.1% | 0.0% | 100.0% | 0.0% |
| dimension:tier:smoke | 93 | 81.7% | 0.0% | 100.0% | 0.0% |
| dimension:tier:hard | 82 | 80.5% | 0.0% | 100.0% | 0.0% |
| dimension:pos:noun | 60 | 51.7% | 0.0% | 100.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 35 | 77.1% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:overlap_target_count:2 | 20 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:pos:verb | 15 | 73.3% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:job | 15 | 46.7% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 69.2% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 45.5% | 0.0% | 100.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 30.0% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:path_route | 10 | 40.0% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 66.7% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 80.0% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_target_count:4 | 4 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `campo` / `field` gold=['terreno'] promoted=[] cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] cases=['en-es:carretera'] tiers=['smoke'] tags=['family:path_route']
