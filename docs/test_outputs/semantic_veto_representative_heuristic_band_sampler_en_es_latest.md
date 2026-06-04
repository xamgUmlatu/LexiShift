# en-es Semantic Veto Representative Heuristic-Band Sampler

- Status: `ok`
- Decision: `representative_heuristic_band_sample_frozen`
- Generated: `2026-05-05T20:38:52+00:00`
- Candidate universe: `4112`
- Non-empty cells: `39` / `54`
- Empty cells: `15`
- Sampled triggers: `255`
- Underfilled non-empty cells: `11`
- Underfilled cells including empty cells: `26`

## Methodology

Estimate heuristic-band mean veto difficulty by sampling representative source triggers within predeclared cells, instead of choosing the most interesting or hardest-looking words.

Cells are sampled by frozen hash order inside each cell. This avoids the old hard-case bias where each band could be represented by its most difficult-looking words.

## Cell Summary

| Cell | Eligible | Sampled | Weight | Triggers |
| --- | ---: | ---: | ---: | --- |
| `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=single_sense` | 2 | 2 | 1.0 | `percent`, `yes` |
| `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 3 | 3 | 1.0 | `college`, `often`, `money` |
| `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 8 | 8 | 1.0 | `consider`, `security`, `door`, `however`, `process`, `news`, `able`, `event` |
| `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 5 | 5 | 1.0 | `off`, `five`, `buy`, `kid`, `today` |
| `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 1 | 1 | 1.0 | `heart` |
| `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 13 | 8 | 1.625 | `home`, `service`, `long`, `work`, `kill`, `help`, `case`, `action` |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 2 | 2 | 1.0 | `employee`, `nobody` |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 5 | 5 | 1.0 | `camera`, `road`, `finally`, `particularly`, `science` |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 2 | 2 | 1.0 | `district`, `hate` |
| `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 14 | 8 | 1.75 | `serious`, `agency`, `example`, `role`, `performance`, `clearly`, `degree`, `response` |
| `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 11 | 8 | 1.375 | `simple`, `paper`, `couple`, `public`, `oil`, `earth`, `blood`, `matter` |
| `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 1 | 1 | 1.0 | `hot` |
| `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 10 | 8 | 1.25 | `look`, `common`, `design`, `return`, `answer`, `union`, `present`, `throw` |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 5 | 5 | 1.0 | `definitely`, `senate`, `currently`, `mayor`, `beer` |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 13 | 8 | 1.625 | `ocean`, `basis`, `consequence`, `participant`, `encourage`, `therefore`, `temperature`, `crisis` |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 9 | 8 | 1.125 | `institute`, `cash`, `soldier`, `expert`, `content`, `african`, `chairman`, `fucking` |
| `source_rank_band=1001-2000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 20 | 8 | 2.5 | `possibility`, `variety`, `attend`, `organize`, `pleasure`, `supreme`, `path`, `facility` |
| `source_rank_band=1001-2000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 23 | 8 | 2.875 | `worth`, `survey`, `future`, `egg`, `particular`, `league`, `medicine`, `stress` |
| `source_rank_band=1001-2000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 2 | 2 | 1.0 | `maintain`, `lead` |
| `source_rank_band=1001-2000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 24 | 8 | 3.0 | `jump`, `down`, `complete`, `strike`, `average`, `reference`, `deep`, `trade` |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 38 | 8 | 4.75 | `stimulus`, `instructional`, `tumor`, `unexpected`, `oven`, `correctly`, `reportedly`, `minimal` |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 82 | 8 | 10.25 | `happily`, `eternal`, `uncover`, `hidden`, `biological`, `teaspoon`, `conscious`, `guideline` |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 15 | 8 | 1.875 | `narrative`, `junk`, `ruling`, `petition`, `sock`, `syrian`, `forty`, `nowhere` |
| `source_rank_band=2001-5000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 45 | 8 | 5.625 | `endure`, `juice`, `execution`, `essence`, `wisdom`, `backup`, `administer`, `leading` |
| `source_rank_band=2001-5000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 68 | 8 | 8.5 | `discount`, `outfit`, `crawl`, `graduate`, `whole`, `constitutional`, `irish`, `campaign` |
| `source_rank_band=2001-5000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 3 | 3 | 1.0 | `explode`, `relieve`, `submit` |
| `source_rank_band=2001-5000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 32 | 8 | 4.0 | `knock`, `short`, `round`, `pad`, `program`, `loose`, `exchange`, `extract` |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 117 | 8 | 14.625 | `psychiatrist`, `toddler`, `humidity`, `strategist`, `tortilla`, `prevailing`, `battlefield`, `exceptionally` |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 133 | 8 | 16.625 | `ambiguous`, `altitude`, `sovereignty`, `paralyze`, `outweigh`, `underneath`, `uphold`, `spider` |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 49 | 8 | 6.125 | `unemployed`, `bulldog`, `classified`, `greenhouse`, `thug`, `notable`, `methodist`, `chant` |
| `source_rank_band=5001-10000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 45 | 8 | 5.625 | `fearful`, `correspond`, `reconstruct`, `spine`, `clove`, `refined`, `variance`, `evacuate` |
| `source_rank_band=5001-10000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 100 | 8 | 12.5 | `tilt`, `console`, `crow`, `collective`, `cube`, `cuff`, `supplement`, `humble` |
| `source_rank_band=5001-10000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 29 | 8 | 3.625 | `mold`, `spike`, `radical`, `grind`, `clip`, `bond`, `screen`, `water` |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 1765 | 8 | 220.625 | `exorcize`, `highchair`, `juggernaut`, `hierarchic`, `intricacy`, `supercomputer`, `rediscover`, `concise` |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 744 | 8 | 93.0 | `avuncular`, `spasmodically`, `squalid`, `revived`, `darter`, `jaunty`, `flashing`, `expulsion` |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 294 | 8 | 36.75 | `conspecific`, `guyanese`, `rebuke`, `lutheran`, `aloof`, `rastafarian`, `rebroadcast`, `florentine` |
| `source_rank_band=>10000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 91 | 8 | 11.375 | `diffusion`, `retardation`, `skimming`, `stilt`, `entree`, `strident`, `subordination`, `showy` |
| `source_rank_band=>10000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 246 | 8 | 30.75 | `shuffle`, `mystic`, `snowball`, `vagabond`, `essay`, `feminine`, `scatter`, `norse` |
| `source_rank_band=>10000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 43 | 8 | 5.375 | `plaster`, `grand`, `rat`, `combine`, `paddle`, `flush`, `fold`, `superior` |

## Sample Rows

| Trigger | Rank | Freq | Senses | POS | Rank band | Polysemy | POS shape | Weight |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: |
| `percent` | 265.0 | 357515.0 | 1 | 1 | `1-500` | `low_1_to_3` | `single_sense` | 1.0 |
| `yes` | 175.0 | 537066.0 | 1 | 1 | `1-500` | `low_1_to_3` | `single_sense` | 1.0 |
| `college` | 435.0 | 224634.0 | 3 | 1 | `1-500` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `often` | 335.0 | 295709.0 | 3 | 1 | `1-500` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `money` | 215.0 | 437583.0 | 3 | 1 | `1-500` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `consider` | 395.0 | 244644.0 | 9 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `security` | 475.0 | 201542.0 | 9 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `door` | 385.0 | 252623.0 | 5 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `however` | 305.0 | 326015.0 | 4 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `process` | 415.0 | 235304.0 | 6 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `news` | 345.0 | 289175.0 | 5 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `able` | 355.0 | 279559.0 | 4 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `event` | 495.0 | 194748.0 | 4 | 1 | `1-500` | `medium_4_to_9` | `same_pos_polysemy` | 1.0 |
| `off` | 195.0 | 479459.0 | 9 | 3 | `1-500` | `medium_4_to_9` | `cross_pos_polysemy` | 1.0 |
| `five` | 365.0 | 270274.0 | 4 | 2 | `1-500` | `medium_4_to_9` | `cross_pos_polysemy` | 1.0 |
| `buy` | 375.0 | 260201.0 | 6 | 2 | `1-500` | `medium_4_to_9` | `cross_pos_polysemy` | 1.0 |
| `kid` | 275.0 | 351451.0 | 6 | 2 | `1-500` | `medium_4_to_9` | `cross_pos_polysemy` | 1.0 |
| `today` | 225.0 | 431562.0 | 4 | 2 | `1-500` | `medium_4_to_9` | `cross_pos_polysemy` | 1.0 |
| `heart` | 445.0 | 216345.0 | 10 | 1 | `1-500` | `high_10_plus` | `same_pos_polysemy` | 1.0 |
| `home` | 255.0 | 370758.0 | 17 | 4 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `service` | 295.0 | 332313.0 | 17 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `long` | 285.0 | 345005.0 | 12 | 3 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `work` | 115.0 | 854095.0 | 34 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `kill` | 325.0 | 307305.0 | 17 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `help` | 155.0 | 606887.0 | 12 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `case` | 205.0 | 458383.0 | 22 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `action` | 485.0 | 198530.0 | 13 | 2 | `1-500` | `high_10_plus` | `cross_pos_polysemy` | 1.625 |
| `employee` | 945.0 | 101818.0 | 1 | 1 | `501-1000` | `low_1_to_3` | `single_sense` | 1.0 |
| `nobody` | 975.0 | 99029.0 | 1 | 1 | `501-1000` | `low_1_to_3` | `single_sense` | 1.0 |
| `camera` | 965.0 | 99855.0 | 2 | 1 | `501-1000` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `road` | 555.0 | 173413.0 | 2 | 1 | `501-1000` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `finally` | 535.0 | 181233.0 | 3 | 1 | `501-1000` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `particularly` | 925.0 | 104018.0 | 3 | 1 | `501-1000` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `science` | 565.0 | 170488.0 | 2 | 1 | `501-1000` | `low_1_to_3` | `same_pos_polysemy` | 1.0 |
| `district` | 885.0 | 109941.0 | 2 | 2 | `501-1000` | `low_1_to_3` | `cross_pos_polysemy` | 1.0 |
| `hate` | 955.0 | 100757.0 | 3 | 2 | `501-1000` | `low_1_to_3` | `cross_pos_polysemy` | 1.0 |
| `serious` | 795.0 | 122251.0 | 6 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `agency` | 785.0 | 123524.0 | 5 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `example` | 775.0 | 125442.0 | 6 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `role` | 525.0 | 184483.0 | 4 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `performance` | 765.0 | 127318.0 | 5 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `clearly` | 905.0 | 105965.0 | 4 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `degree` | 855.0 | 113046.0 | 7 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `response` | 715.0 | 135942.0 | 7 | 1 | `501-1000` | `medium_4_to_9` | `same_pos_polysemy` | 1.75 |
| `simple` | 735.0 | 132004.0 | 9 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `paper` | 585.0 | 165070.0 | 9 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `couple` | 515.0 | 189272.0 | 9 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `public` | 995.0 | 97031.0 | 4 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `oil` | 645.0 | 150410.0 | 6 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `earth` | 725.0 | 134202.0 | 8 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `blood` | 705.0 | 137579.0 | 6 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `matter` | 575.0 | 167351.0 | 7 | 2 | `501-1000` | `medium_4_to_9` | `cross_pos_polysemy` | 1.375 |
| `hot` | 755.0 | 128310.0 | 21 | 1 | `501-1000` | `high_10_plus` | `same_pos_polysemy` | 1.0 |
| `look` | 605.0 | 160145.0 | 14 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `common` | 745.0 | 130294.0 | 10 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `design` | 875.0 | 111026.0 | 13 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `return` | 545.0 | 176787.0 | 29 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `answer` | 835.0 | 115956.0 | 15 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `union` | 935.0 | 102805.0 | 11 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `present` | 865.0 | 111731.0 | 18 | 3 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `throw` | 635.0 | 152388.0 | 20 | 2 | `501-1000` | `high_10_plus` | `cross_pos_polysemy` | 1.25 |
| `definitely` | 1345.0 | 70982.0 | 1 | 1 | `1001-2000` | `low_1_to_3` | `single_sense` | 1.0 |
| `senate` | 1155.0 | 83931.0 | 1 | 1 | `1001-2000` | `low_1_to_3` | `single_sense` | 1.0 |
| `currently` | 1455.0 | 66051.0 | 1 | 1 | `1001-2000` | `low_1_to_3` | `single_sense` | 1.0 |
| `mayor` | 1775.0 | 51481.0 | 1 | 1 | `1001-2000` | `low_1_to_3` | `single_sense` | 1.0 |
| `beer` | 1815.0 | 50024.0 | 1 | 1 | `1001-2000` | `low_1_to_3` | `single_sense` | 1.0 |
| `ocean` | 1885.0 | 47773.0 | 2 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `basis` | 1385.0 | 68758.0 | 3 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `consequence` | 1685.0 | 54883.0 | 3 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `participant` | 1185.0 | 81371.0 | 2 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `encourage` | 1305.0 | 73251.0 | 3 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `therefore` | 1085.0 | 89981.0 | 2 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `temperature` | 1585.0 | 59493.0 | 2 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `crisis` | 1295.0 | 73691.0 | 2 | 1 | `1001-2000` | `low_1_to_3` | `same_pos_polysemy` | 1.625 |
| `institute` | 1525.0 | 62451.0 | 3 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| `cash` | 1665.0 | 55856.0 | 3 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| `soldier` | 1235.0 | 78276.0 | 3 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| `expert` | 1105.0 | 88134.0 | 3 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| `content` | 1215.0 | 79496.0 | 3 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| `african` | 1635.0 | 57497.0 | 2 | 2 | `1001-2000` | `low_1_to_3` | `cross_pos_polysemy` | 1.125 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Guardrails

| Check | Value |
| --- | --- |
| `outcome_fields_absent_from_sample_rows` | `True` |
| `all_sampled_rows_have_cell_ids` | `True` |
| `all_nonempty_cells_have_samples` | `True` |
| `sample_counts_do_not_exceed_eligible_counts` | `True` |
| `empty_cells_are_preserved` | `True` |

## Limitations

- `english_source_trigger_sample_only_no_spanish_target_family_yet`
- `sample_is_representative_within_cells_not_a_natural_browser_token_distribution`
- `wordnet_polysemy_and_pos_shape_are_proxy_features_not_human_sense_labels`
- `measured_triggers_are_excluded_by_default_to_avoid_reusing_biased_prior_outcomes`
- `case_authoring_or_llm_generation_must_not_replace_this_frozen_sample_ad_hoc`

## Next Steps

- Run target/shadow family construction over the frozen sampled rows without reselecting triggers.
- For source-ready sampled words, generate or author a fixed small context packet per word.
- Estimate mean veto difficulty and confidence intervals by cell, then fit factor effects across rank, polysemy, and POS shape.
- Only after representative means are measured, run separate targeted oversampling for high-uncertainty or high-value cells.
