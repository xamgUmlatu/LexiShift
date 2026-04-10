# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T21:54:36Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 99.4% | 95.5% | 4.5% | 99.3% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 93.9% | 72.7% | 27.3% | 95.8% | 2.8% |
| borrowed_trigger_auto_shadows | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 93.9% | 86.4% | 13.6% | 97.8% | 5.0% |
| no_shadows | rulegen_top3_plus_forward_gloss | 86.5% | 0.0% | 100.0% | 86.5% | 0.0% |

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
| dimension:trigger_shape:unigram | 152 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:1 | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 132 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:smoke | 87 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 76 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 48 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 31 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 22 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:overlap_target_count:2 | 16 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 12 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 8 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 6 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
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
- Overall accuracy: `99.4%`
- Abstain recall on ambiguous rows: `95.5%`
- Harmful allow rate: `4.5%`
- Allow precision: `99.3%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-0.6%`
- Delta vs curated abstain recall: `-4.5%`
- Delta vs curated harmful allow: `4.5%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 152 | 99.3% | 95.5% | 4.5% | 0.0% |
| dimension:overlap_target_count:1 | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 132 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:smoke | 87 | 98.9% | 91.7% | 8.3% | 0.0% |
| dimension:tier:hard | 76 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:pos:noun | 48 | 97.9% | 94.4% | 5.6% | 0.0% |
| dimension:reviewed_expectation:expected_only | 31 | 96.8% | 80.0% | 20.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 22 | 95.5% | 95.5% | 4.5% | n/a |
| dimension:overlap_target_count:2 | 16 | 93.8% | 93.8% | 6.2% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 12 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 8 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:field_area_country | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 6 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `terreno` / `field` gold=['campo'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']

### auto_shadows
- Label: `Source-only auto shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Overall accuracy: `93.9%`
- Abstain recall on ambiguous rows: `72.7%`
- Harmful allow rate: `27.3%`
- Allow precision: `95.8%`
- Overblocking rate: `2.8%`
- Delta vs curated accuracy: `-6.1%`
- Delta vs curated abstain recall: `-27.3%`
- Delta vs curated harmful allow: `27.3%`
- Delta vs curated overblocking: `2.8%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 152 | 93.4% | 72.7% | 27.3% | 3.1% |
| dimension:overlap_target_count:1 | 141 | 97.2% | n/a | n/a | 2.8% |
| dimension:overlap_topology:singleton_trigger | 141 | 97.2% | n/a | n/a | 2.8% |
| dimension:reviewed_expectation:top1_expected | 132 | 95.5% | 88.2% | 11.8% | 3.5% |
| dimension:tier:smoke | 87 | 94.3% | 75.0% | 25.0% | 2.7% |
| dimension:tier:hard | 76 | 93.4% | 70.0% | 30.0% | 3.0% |
| dimension:pos:noun | 48 | 81.2% | 66.7% | 33.3% | 10.0% |
| dimension:reviewed_expectation:expected_only | 31 | 87.1% | 20.0% | 80.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 22 | 72.7% | 72.7% | 27.3% | n/a |
| dimension:overlap_target_count:2 | 16 | 68.8% | 68.8% | 31.2% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 12 | 66.7% | 40.0% | 60.0% | 14.3% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 8 | 62.5% | 80.0% | 20.0% | 66.7% |
| dimension:semantic_family:field_area_country | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 7 | 85.7% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 6 | 83.3% | 83.3% | 16.7% | n/a |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['empleo', 'trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `empleo` / `work` gold=['trabajo'] promoted=[] cases=['en-es:empleo'] tiers=['hard'] tags=['family:job']
  - `rejilla` / `mesh` gold=['malla'] promoted=[] cases=['en-es:rejilla'] tiers=['hard'] tags=['family:net_mesh_network']
  - `ruta` / `road` gold=['camino'] promoted=[] cases=['en-es:ruta'] tiers=['smoke'] tags=['family:path_route']
  - `terreno` / `field` gold=['campo'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']
- Sample false-abstain rows:
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `cargo` / `position` promoted=['plaza'] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] tiers=['hard']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] tiers=['smoke'] tags=['family:path_route']

### borrowed_trigger_auto_shadows
- Label: `Source-only borrowed-trigger shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Overall accuracy: `93.9%`
- Abstain recall on ambiguous rows: `86.4%`
- Harmful allow rate: `13.6%`
- Allow precision: `97.8%`
- Overblocking rate: `5.0%`
- Delta vs curated accuracy: `-6.1%`
- Delta vs curated abstain recall: `-13.6%`
- Delta vs curated harmful allow: `13.6%`
- Delta vs curated overblocking: `5.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 152 | 93.4% | 86.4% | 13.6% | 5.4% |
| dimension:overlap_target_count:1 | 141 | 95.0% | n/a | n/a | 5.0% |
| dimension:overlap_topology:singleton_trigger | 141 | 95.0% | n/a | n/a | 5.0% |
| dimension:reviewed_expectation:top1_expected | 132 | 93.9% | 94.1% | 5.9% | 6.1% |
| dimension:tier:smoke | 87 | 93.1% | 83.3% | 16.7% | 5.3% |
| dimension:tier:hard | 76 | 94.7% | 90.0% | 10.0% | 4.5% |
| dimension:pos:noun | 48 | 83.3% | 83.3% | 16.7% | 16.7% |
| dimension:reviewed_expectation:expected_only | 31 | 93.5% | 60.0% | 40.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 22 | 86.4% | 86.4% | 13.6% | n/a |
| dimension:overlap_target_count:2 | 16 | 81.2% | 81.2% | 18.8% | n/a |
| dimension:pos:verb | 15 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:job | 12 | 83.3% | 100.0% | 0.0% | 28.6% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 8 | 62.5% | 80.0% | 20.0% | 66.7% |
| dimension:semantic_family:field_area_country | 7 | 85.7% | 50.0% | 50.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 7 | 85.7% | 75.0% | 25.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:overlap_target_count:3 | 6 | 100.0% | 100.0% | 0.0% | n/a |
| dimension:semantic_family:remove_take_out | 6 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 50.0% | n/a | n/a | 50.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `rejilla` / `mesh` gold=['malla'] promoted=[] cases=['en-es:rejilla'] tiers=['hard'] tags=['family:net_mesh_network']
  - `ruta` / `road` gold=['camino'] promoted=[] cases=['en-es:ruta'] tiers=['smoke'] tags=['family:path_route']
  - `terreno` / `field` gold=['campo'] promoted=[] cases=['en-es:terreno'] tiers=['smoke'] tags=['family:field_area_country']
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
- Overall accuracy: `86.5%`
- Abstain recall on ambiguous rows: `0.0%`
- Harmful allow rate: `100.0%`
- Allow precision: `86.5%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-13.5%`
- Delta vs curated abstain recall: `-100.0%`
- Delta vs curated harmful allow: `100.0%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:trigger_shape:unigram | 152 | 85.5% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_target_count:1 | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:overlap_topology:singleton_trigger | 141 | 100.0% | n/a | n/a | 0.0% |
| dimension:reviewed_expectation:top1_expected | 132 | 87.1% | 0.0% | 100.0% | 0.0% |
| dimension:tier:smoke | 87 | 86.2% | 0.0% | 100.0% | 0.0% |
| dimension:tier:hard | 76 | 86.8% | 0.0% | 100.0% | 0.0% |
| dimension:pos:noun | 48 | 62.5% | 0.0% | 100.0% | 0.0% |
| dimension:reviewed_expectation:expected_only | 31 | 83.9% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_topology:shared_trigger | 22 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:overlap_target_count:2 | 16 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:pos:verb | 15 | 73.3% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:phrase_sensitive | 13 | 69.2% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:job | 12 | 58.3% | 0.0% | 100.0% | 0.0% |
| dimension:trigger_shape:multiword | 11 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:path_route | 8 | 37.5% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:field_area_country | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:net_mesh_network | 7 | 42.9% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:table_board_chart | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:semantic_family:take_carry | 7 | 71.4% | 0.0% | 100.0% | 0.0% |
| dimension:overlap_target_count:3 | 6 | 0.0% | 0.0% | 100.0% | n/a |
| dimension:semantic_family:remove_take_out | 6 | 66.7% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:domain_competition | 5 | 100.0% | n/a | n/a | 0.0% |
| dimension:hazard:slang_leakage | 5 | 80.0% | 0.0% | 100.0% | 0.0% |
| dimension:hazard:mixed_pos | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:pos:mixed | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:account_bill | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:right_law_straight | 3 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:bank_bench | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:battery_music | 2 | 100.0% | n/a | n/a | 0.0% |
| dimension:semantic_family:finish_end | 2 | 100.0% | n/a | n/a | 0.0% |
- Sample harmful-allow rows:
  - `camino` / `road` gold=['ruta'] promoted=[] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[] cases=['en-es:camino'] tiers=['smoke'] tags=['family:path_route']
  - `campo` / `field` gold=['terreno'] promoted=[] cases=['en-es:campo'] tiers=['hard'] tags=['family:field_area_country']
  - `cargo` / `job` gold=['empleo', 'trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard'] tags=['family:job']
  - `coger` / `take` gold=['llevar'] promoted=[] cases=['en-es:coger'] tiers=['hard'] tags=['family:take_carry', 'hazard:phrase_sensitive', 'hazard:slang_leakage']
