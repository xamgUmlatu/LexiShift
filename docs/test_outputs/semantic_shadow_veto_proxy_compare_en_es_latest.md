# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T22:19:10Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 93.7% | 66.7% | 33.3% | 92.8% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 87.4% | 42.4% | 57.6% | 88.0% | 2.1% |
| borrowed_trigger_auto_shadows | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 89.1% | 51.5% | 48.5% | 89.7% | 2.1% |
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
- Overall accuracy: `93.7%`
- Abstain recall on ambiguous rows: `66.7%`
- Harmful allow rate: `33.3%`
- Allow precision: `92.8%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-6.3%`
- Delta vs curated abstain recall: `-33.3%`
- Delta vs curated harmful allow: `33.3%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 93.3% | 66.7% | 33.3% | 0.0% |
| dimension:overlap_target_count:1 | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 142 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 140 | 93.6% | 64.0% | 36.0% | 0.0% |
| dimension:tier:smoke | 93 | 92.5% | 58.8% | 41.2% | 0.0% |
| dimension:tier:hard | 82 | 95.1% | 75.0% | 25.0% | 0.0% |
| dimension:pos:noun | 60 | 83.3% | 65.5% | 34.5% | 0.0% |
| dimension:reviewed_expectation:expected_only | 35 | 94.3% | 75.0% | 25.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 66.7% | 66.7% | 33.3% | n/a |
| dimension:overlap_target_count:2 | 20 | 45.0% | 45.0% | 55.0% | n/a |
| dimension:pos:verb | 15 | 93.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:job | 15 | 86.7% | 75.0% | 25.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 92.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 63.6% | 33.3% | 66.7% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 70.0% | 57.1% | 42.9% | 0.0% |
| dimension:semantic_family:path_route | 10 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 83.3% | 50.0% | 50.0% | 0.0% |
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
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=promotion_miss cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `quitar` / `remove` gold=['sacar'] promoted=[] miss=promotion_miss cases=['en-es:quitar'] tiers=['smoke'] tags=['family:remove_take_out', 'hazard:phrase_sensitive']
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss cases=['en-es:red'] tiers=['smoke'] tags=['family:net_mesh_network']
  - `reja` / `grille` gold=['rejilla'] promoted=[] miss=promotion_miss cases=['en-es:reja'] tiers=['hard'] tags=['family:net_mesh_network']
  - `rejilla` / `grille` gold=['reja'] promoted=[] miss=promotion_miss cases=['en-es:rejilla'] tiers=['hard'] tags=['family:net_mesh_network']

### auto_shadows
- Label: `Source-only auto shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Overall accuracy: `87.4%`
- Abstain recall on ambiguous rows: `42.4%`
- Harmful allow rate: `57.6%`
- Allow precision: `88.0%`
- Overblocking rate: `2.1%`
- Delta vs curated accuracy: `-12.6%`
- Delta vs curated abstain recall: `-57.6%`
- Delta vs curated harmful allow: `57.6%`
- Delta vs curated overblocking: `2.1%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 86.6% | 42.4% | 57.6% | 2.3% |
| dimension:overlap_target_count:1 | 142 | 97.9% | n/a | n/a | 2.1% |
| dimension:overlap_topology:singleton_trigger | 142 | 97.9% | n/a | n/a | 2.1% |
| dimension:reviewed_expectation:top1_expected | 140 | 88.6% | 48.0% | 52.0% | 2.6% |
| dimension:tier:smoke | 93 | 91.4% | 58.8% | 41.2% | 1.3% |
| dimension:tier:hard | 82 | 82.9% | 25.0% | 75.0% | 3.0% |
| dimension:pos:noun | 60 | 66.7% | 37.9% | 62.1% | 6.5% |
| dimension:reviewed_expectation:expected_only | 35 | 82.9% | 25.0% | 75.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 42.4% | 42.4% | 57.6% | n/a |
| dimension:overlap_target_count:2 | 20 | 35.0% | 35.0% | 65.0% | n/a |
| dimension:pos:verb | 15 | 93.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:job | 15 | 60.0% | 25.0% | 75.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 92.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 54.5% | 33.3% | 66.7% | 20.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 30.0% | 14.3% | 85.7% | 33.3% |
| dimension:semantic_family:path_route | 10 | 90.0% | 83.3% | 16.7% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 55.6% | 55.6% | 44.4% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 83.3% | 50.0% | 50.0% | 0.0% |
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
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss cases=['en-es:malla'] tiers=['hard'] tags=['family:net_mesh_network']
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] tiers=['hard']
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] tiers=['hard'] tags=['family:net_mesh_network']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] tiers=['smoke'] tags=['family:field_area_country']

### borrowed_trigger_auto_shadows
- Label: `Source-only borrowed-trigger shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Overall accuracy: `89.1%`
- Abstain recall on ambiguous rows: `51.5%`
- Harmful allow rate: `48.5%`
- Allow precision: `89.7%`
- Overblocking rate: `2.1%`
- Delta vs curated accuracy: `-10.9%`
- Delta vs curated abstain recall: `-48.5%`
- Delta vs curated harmful allow: `48.5%`
- Delta vs curated overblocking: `2.1%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 164 | 88.4% | 51.5% | 48.5% | 2.3% |
| dimension:overlap_target_count:1 | 142 | 97.9% | n/a | n/a | 2.1% |
| dimension:overlap_topology:singleton_trigger | 142 | 97.9% | n/a | n/a | 2.1% |
| dimension:reviewed_expectation:top1_expected | 140 | 89.3% | 52.0% | 48.0% | 2.6% |
| dimension:tier:smoke | 93 | 91.4% | 58.8% | 41.2% | 1.3% |
| dimension:tier:hard | 82 | 86.6% | 43.8% | 56.2% | 3.0% |
| dimension:pos:noun | 60 | 71.7% | 48.3% | 51.7% | 6.5% |
| dimension:reviewed_expectation:expected_only | 35 | 88.6% | 50.0% | 50.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 33 | 51.5% | 51.5% | 48.5% | n/a |
| dimension:overlap_target_count:2 | 20 | 40.0% | 40.0% | 60.0% | n/a |
| dimension:pos:verb | 15 | 93.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:job | 15 | 80.0% | 62.5% | 37.5% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 92.3% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:field_area_country | 11 | 54.5% | 33.3% | 66.7% | 20.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:net_mesh_network | 10 | 30.0% | 14.3% | 85.7% | 33.3% |
| dimension:semantic_family:path_route | 10 | 90.0% | 83.3% | 16.7% | 0.0% |
| dimension:overlap_target_count:3 | 9 | 55.6% | 55.6% | 44.4% | n/a |
| dimension:semantic_family:table_board_chart | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:remove_take_out | 6 | 83.3% | 50.0% | 50.0% | 0.0% |
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
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss cases=['en-es:malla'] tiers=['hard'] tags=['family:net_mesh_network']
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing cases=['en-es:ocupación'] tiers=['hard'] tags=['family:job']
  - `quitar` / `remove` gold=['sacar'] promoted=[] miss=promotion_miss cases=['en-es:quitar'] tiers=['smoke'] tags=['family:remove_take_out', 'hazard:phrase_sensitive']
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] tiers=['hard']
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] tiers=['hard'] tags=['family:net_mesh_network']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] tiers=['smoke'] tags=['family:field_area_country']

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
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[] miss=promotion_miss cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss cases=['en-es:carretera'] tiers=['smoke'] tags=['family:path_route']
