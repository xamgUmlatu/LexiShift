# en-es Semantic Shadow Experiment Matrix

- Status: `ok`
- Generated: `2026-04-11T03:02:50Z`
- Manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json`
- Data root: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift`
- Forward pack: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_shadow_temp/wiktionary-es-en-with-examples.sqlite` (wiktionary)
- Reverse pack: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-en-es.sqlite` (wiktionary)
- Forward seed max words: `1`
- Neighbor-borrow modes loaded: `True`
- Matrix meaning: each row is a full experiment configuration spanning seed admission, promotion scoring, and veto evaluation.
- Forward records with examples: `132 / 453` across `45` targets
- Reverse records with aux text: `3003 / 3003` across `371` triggers

## Summary
| Experiment | Seed Mode | Trigger Filter | Shadow Min | Max Promoted | Gold Prec | Gold Rec | Veto Acc | Abstain Rec | Harmful Allow |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reviewed_auto_control | benchmark_reviewed | 0.0 | 5.0 | 1 | 100.0% | 50.0% | 95.4% | 75.8% | 24.2% |
| source_only_baseline | rulegen_top3_plus_forward_gloss | 0.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| source_only_trigger_filtered | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| source_only_borrowed | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| source_only_borrowed_threshold_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 2.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| source_only_borrowed_threshold_3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| promotion_min_4 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 4.0 | 2 | 32.4% | 46.0% | 74.9% | 60.6% | 39.4% |
| promotion_min_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | 72.7% | 16.0% | 83.4% | 18.2% | 81.8% |
| promotion_top1 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 1 | 72.7% | 32.0% | 89.1% | 54.5% | 45.5% |
| promotion_top3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 3 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_forward_support_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_forward_support_half | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_forward_support_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_same_pos_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 72.7% | 16.0% | 83.4% | 18.2% | 81.8% |
| promotion_same_pos_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_active_profile_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| promotion_active_profile_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_semantic_bridge_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_semantic_bridge_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_semantic_bridge_aux_text_on | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_semantic_bridge_aux_text_examples_on | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 75.9% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_cross_pos_penalty_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_cross_pos_penalty_strong | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_multi_source_candidate_1 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_multi_source_candidate_1_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 75.0% | 48.0% | 89.7% | 60.6% | 39.4% |
| promotion_multi_source_candidate_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 75.0% | 48.0% | 89.7% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 75.0% | 48.0% | 89.7% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 73.5% | 50.0% | 89.1% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 80.0% | 48.0% | 90.3% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 80.0% | 48.0% | 90.3% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_multi_source_plus_trigger_family_reentry_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 78.6% | 44.0% | 89.1% | 54.5% | 45.5% |
| promotion_multi_source_plus_trigger_family_reentry_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 80.0% | 48.0% | 90.3% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 78.1% | 50.0% | 89.7% | 60.6% | 39.4% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 71.4% | 50.0% | 88.6% | 60.6% | 39.4% |
| source_only_forward_reward_off | rulegen_top3_plus_forward_gloss | 0.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_threshold_2 | rulegen_top3_plus_forward_gloss | 2.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_threshold_4 | rulegen_top3_plus_forward_gloss | 4.0 | 5.0 | 2 | 85.7% | 24.0% | 85.1% | 27.3% | 72.7% |
| admission_forward_gloss_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 86.7% | 26.0% | 85.7% | 30.3% | 69.7% |
| admission_forward_gloss_half | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 86.7% | 26.0% | 85.7% | 30.3% | 69.7% |
| admission_forward_gloss_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_multi_source_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_multi_source_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_reverse_shadow_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 86.7% | 26.0% | 85.7% | 30.3% | 69.7% |
| admission_reverse_shadow_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_multiword_penalty_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |
| admission_multiword_penalty_strong | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 73.9% | 34.0% | 87.4% | 45.5% | 54.5% |

## Details

### reviewed_auto_control
- Label: `Reviewed-trigger automatic control`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `1`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`175 / 175`)
- Gold candidate precision / recall / F1: `100.0%` / `50.0%` / `66.7%`
- Gold trigger hit / top1 hit / exact-pool match: `75.8%` / `75.8%` / `12.1%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `95.4%` / `75.8%` / `24.2%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=8`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=0`, `candidate_missing=0`, `promotion_miss=8`
- Sample harmful-allow rows:
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=promotion_miss
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
  - `tabla` / `table` gold=['cuadro'] promoted=[] miss=promotion_miss
  - `terreno` / `land` gold=['tierra'] promoted=[] miss=promotion_miss
  - `terreno` / `ground` gold=['tierra'] promoted=[] miss=promotion_miss

### source_only_baseline
- Label: `Source-only lexical baseline`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`398 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### source_only_trigger_filtered
- Label: `Source-only with upstream trigger filter`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### source_only_borrowed
- Label: `Source-only with borrowed triggers`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### source_only_borrowed_threshold_2
- Label: `Borrowed triggers with threshold 2`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `2.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `94.8%` (`398 / 420`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Trigger-filter examples dropped:
  - `acabar` / `quit` score=`1.0` features=['reverse_shadow_support']
  - `camino` / `track` score=`1.0` features=['reverse_shadow_support']
  - `campo` / `ground` score=`1.0` features=['reverse_shadow_support']
  - `cargo` / `job` score=`1.0` features=['reverse_shadow_support']
  - `casa` / `track` score=`1.0` features=['reverse_shadow_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### source_only_borrowed_threshold_3
- Label: `Borrowed triggers with threshold 3`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `46.9%` (`197 / 420`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `quit` score=`1.0` features=['reverse_shadow_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_min_4
- Label: `Borrowed baseline with support min 4`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `4.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `32.4%` / `46.0%` / `38.0%`
- Gold trigger hit / top1 hit / exact-pool match: `54.5%` / `51.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `74.9%` / `60.6%` / `39.4%` / `21.8%`
- Veto counts: `false_abstain=31`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `reja` / `mesh` gold=['malla', 'rejilla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `acabar` / `finish` promoted=['salir'] cases=['en-es:acabar'] slices=['family:finish_end', 'hazard:slang_leakage']
  - `acabar` / `end` promoted=['salir'] cases=['en-es:acabar'] slices=['family:finish_end', 'hazard:slang_leakage']
  - `camino` / `way` promoted=['canal', 'sendero'] cases=['en-es:camino'] slices=['family:path_route']
  - `canal` / `canal` promoted=['camino'] cases=['en-es:canal'] slices=[]
  - `canal` / `channel` promoted=['camino'] cases=['en-es:canal'] slices=[]

### promotion_min_6
- Label: `Borrowed baseline with support min 6`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `72.7%` / `16.0%` / `26.2%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `83.4%` / `18.2%` / `81.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=27`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=0`, `candidate_missing=1`, `promotion_miss=11`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']

### promotion_top1
- Label: `Borrowed baseline with top1 promotion`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `1`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `72.7%` / `32.0%` / `44.4%`
- Gold trigger hit / top1 hit / exact-pool match: `48.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_top3
- Label: `Borrowed baseline with top3 promotion`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `3`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_forward_support_off
- Label: `Borrowed baseline with forward support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"forward_trigger_support": 0.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_forward_support_half
- Label: `Borrowed baseline with forward support half`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"forward_trigger_support": 0.25}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_forward_support_high
- Label: `Borrowed baseline with forward support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"forward_trigger_support": 1.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_same_pos_off
- Label: `Borrowed baseline with same-POS reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `72.7%` / `16.0%` / `26.2%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `83.4%` / `18.2%` / `81.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=27`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=0`, `candidate_missing=1`, `promotion_miss=11`
- Shadow support weights: `{"same_pos_as_active": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']

### promotion_same_pos_high
- Label: `Borrowed baseline with same-POS reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"same_pos_as_active": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_active_profile_off
- Label: `Borrowed baseline with active-profile support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=4`, `candidate_missing=1`, `promotion_miss=7`
- Shadow support weights: `{"active_profile_support": 0.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=promotion_miss
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_active_profile_high
- Label: `Borrowed baseline with active-profile support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"active_profile_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_semantic_bridge_off
- Label: `Borrowed baseline with semantic-bridge support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"semantic_bridge_support": 0.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_semantic_bridge_high
- Label: `Borrowed baseline with semantic-bridge support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"semantic_bridge_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_semantic_bridge_aux_text_on
- Label: `Borrowed baseline with semantic-bridge aux text on`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `True` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_semantic_bridge_aux_text_examples_on
- Label: `Borrowed baseline with semantic-bridge aux text and examples on`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `True` / `True`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `75.9%` / `44.0%` / `55.7%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `45.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `53`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_cross_pos_penalty_off
- Label: `Borrowed baseline with cross-POS penalty off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"cross_pos_mismatch_penalty": 0.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_cross_pos_penalty_strong
- Label: `Borrowed baseline with cross-POS penalty strong`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"cross_pos_mismatch_penalty": -2.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_candidate_1
- Label: `Borrowed baseline with multi-source candidate support 1.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `48.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"multi_source_candidate_support": 1.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_candidate_1_5
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_candidate_2
- Label: `Borrowed baseline with multi-source candidate support 2.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"multi_source_candidate_support": 2.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_2
- Label: `Borrowed baseline with multi-source 1.5 plus neighborhood overlap 2.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_3
- Label: `Borrowed baseline with multi-source 1.5 plus neighborhood overlap 3.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `73.5%` / `50.0%` / `59.5%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `60.6%` / `39.4%` / `4.2%`
- Veto counts: `false_abstain=6`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `camino` / `way` promoted=['ruta'] cases=['en-es:camino'] slices=['family:path_route']
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']

### promotion_multi_source_plus_forward_neighborhood_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `80.0%` / `48.0%` / `60.0%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `90.3%` / `60.6%` / `39.4%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `80.0%` / `48.0%` / `60.0%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `90.3%` / `60.6%` / `39.4%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_2_threshold_6
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 2.0, threshold 6.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `51.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_3_threshold_6
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, threshold 6.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `51.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_trigger_family_reentry_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, trigger-family reentry 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Gold trigger hit / top1 hit / exact-pool match: `51.5%` / `51.5%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "trigger_family_reentry": 2.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_trigger_family_reentry_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, trigger-family reentry 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `80.0%` / `48.0%` / `60.0%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `90.3%` / `60.6%` / `39.4%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "trigger_family_reentry": 3.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, trigger-family reentry 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `78.1%` / `50.0%` / `61.0%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5, "trigger_family_reentry": 2.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `camino` / `way` promoted=['ruta'] cases=['en-es:camino'] slices=['family:path_route']
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, trigger-family reentry 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`420 / 420`)
- Gold candidate precision / recall / F1: `71.4%` / `50.0%` / `58.8%`
- Gold trigger hit / top1 hit / exact-pool match: `57.6%` / `57.6%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `88.6%` / `60.6%` / `39.4%` / `4.9%`
- Veto counts: `false_abstain=7`, `harmful_allow=13`
- Automatic feature slices tracked: `52`
- Harmful-allow miss counts: `seed_missing=6`, `candidate_missing=1`, `promotion_miss=5`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5, "trigger_family_reentry": 3.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
  - `ocupación` / `employment` gold=['empleo'] promoted=[] miss=seed_missing
  - `red` / `net` gold=['malla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `camino` / `way` promoted=['ruta', 'sendero'] cases=['en-es:camino'] slices=['family:path_route']
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']

### source_only_forward_reward_off
- Label: `Source-only with forward support ablated`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`398 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Shadow support weights: `{"forward_trigger_support": 0.0}`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_threshold_2
- Label: `Admission threshold 2`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `2.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`398 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_threshold_4
- Label: `Admission threshold 4`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `4.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `9.8%` (`39 / 398`)
- Gold candidate precision / recall / F1: `85.7%` / `24.0%` / `37.5%`
- Gold trigger hit / top1 hit / exact-pool match: `27.3%` / `27.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `27.3%` / `72.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=24`
- Automatic feature slices tracked: `47`
- Harmful-allow miss counts: `seed_missing=9`, `candidate_missing=0`, `promotion_miss=3`
- Trigger-filter examples dropped:
  - `acabar` / `finish` score=`3.0` features=['rulegen_top3_source', 'active_side_support']
  - `acabar` / `cum` score=`3.0` features=['rulegen_top3_source', 'active_side_support']
  - `acabar` / `exhaust` score=`3.0` features=['rulegen_top3_source', 'active_side_support']
  - `acabar` / `end` score=`3.0` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=seed_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']

### admission_forward_gloss_off
- Label: `Admission forward-gloss reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `42.7%` (`170 / 398`)
- Gold candidate precision / recall / F1: `86.7%` / `26.0%` / `40.0%`
- Gold trigger hit / top1 hit / exact-pool match: `30.3%` / `30.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `30.3%` / `69.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=23`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Trigger support weights: `{"forward_gloss_fragment": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `end` score=`2.0` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
  - `acabar` / `just` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']

### admission_forward_gloss_half
- Label: `Admission forward-gloss reward half`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `42.7%` (`170 / 398`)
- Gold candidate precision / recall / F1: `86.7%` / `26.0%` / `40.0%`
- Gold trigger hit / top1 hit / exact-pool match: `30.3%` / `30.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `30.3%` / `69.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=23`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Trigger support weights: `{"forward_gloss_fragment": 0.5}`
- Trigger-filter examples dropped:
  - `acabar` / `end` score=`2.5` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
  - `acabar` / `just` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']

### admission_forward_gloss_high
- Label: `Admission forward-gloss reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"forward_gloss_fragment": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_multi_source_off
- Label: `Admission multi-source reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"multi_source_support": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_multi_source_high
- Label: `Admission multi-source reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"multi_source_support": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_reverse_shadow_off
- Label: `Admission reverse-shadow reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `42.7%` (`170 / 398`)
- Gold candidate precision / recall / F1: `86.7%` / `26.0%` / `40.0%`
- Gold trigger hit / top1 hit / exact-pool match: `30.3%` / `30.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `30.3%` / `69.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=23`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=7`, `candidate_missing=1`, `promotion_miss=4`
- Trigger support weights: `{"reverse_shadow_support": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `end` score=`2.0` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']

### admission_reverse_shadow_high
- Label: `Admission reverse-shadow reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"reverse_shadow_support": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_multiword_penalty_off
- Label: `Admission multiword penalty off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `50.0%` (`199 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"multi_word_penalty": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']

### admission_multiword_penalty_strong
- Label: `Admission multiword penalty strong`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `49.5%` (`197 / 398`)
- Gold candidate precision / recall / F1: `73.9%` / `34.0%` / `46.6%`
- Gold trigger hit / top1 hit / exact-pool match: `42.4%` / `39.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `87.4%` / `45.5%` / `54.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=18`
- Automatic feature slices tracked: `51`
- Harmful-allow miss counts: `seed_missing=8`, `candidate_missing=1`, `promotion_miss=3`
- Trigger support weights: `{"multi_word_penalty": -2.0}`
- Trigger-filter examples dropped:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `urine` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `pop` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `empleo` / `work` gold=['trabajo'] promoted=[] miss=seed_missing
  - `malla` / `mesh` gold=['reja', 'rejilla'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `marco` / `frame` promoted=['cuadro'] cases=['en-es:marco'] slices=[]
  - `reja` / `grating` promoted=['rejilla'] cases=['en-es:reja'] slices=['family:net_mesh_network']
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
  - `tierra` / `earth` promoted=['terreno'] cases=['en-es:tierra'] slices=['family:field_area_country']
