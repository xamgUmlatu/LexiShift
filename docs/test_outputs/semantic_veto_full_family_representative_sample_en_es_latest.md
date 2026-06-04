# en-es Semantic Veto Full-Family Representative Sample

- Status: `ok`
- Decision: `full_family_representative_sample_frozen`
- Generated: `2026-05-06T01:44:23Z`
- Full source-target families: `570`
- Eligible families: `566`
- Non-empty cells: `30` / `80`
- Sampled families: `58`
- Planned manual cases: `254`

## Methodology

The sample is drawn from the full generated source-target family denominator, not from the 200-row SRS journey slice. Sampling is random by stable hash inside predeclared cells, so mid and rare source bands are represented even though they are smaller than common bands.

## Universe Versus Sample

### Source Zipf

| Band | Universe | Universe Share | Sample | Sample Share |
| --- | ---: | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 106 | 18.7% | 16 | 27.6% |
| `zipf_4_to_5_common` | 234 | 41.3% | 15 | 25.9% |
| `zipf_3_to_4_mid` | 152 | 26.9% | 14 | 24.1% |
| `zipf_below_3_rare` | 52 | 9.2% | 10 | 17.2% |
| `missing` | 22 | 3.9% | 3 | 5.2% |

### Target Zipf

| Band | Universe | Universe Share | Sample | Sample Share |
| --- | ---: | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 83 | 14.7% | 12 | 20.7% |
| `zipf_4_to_5_common` | 217 | 38.3% | 19 | 32.8% |
| `zipf_3_to_4_mid` | 205 | 36.2% | 23 | 39.7% |
| `zipf_below_3_rare` | 61 | 10.8% | 4 | 6.9% |

## Cell Summary

| Cell | Eligible | Sampled | Weight | Families |
| --- | ---: | ---: | ---: | --- |
| `source_zipf=zipf_5_plus_very_common::polysemy=low_1_to_3::pos_shape=single_sense` | 5 | 2 | 2.5 | `june->junio`, `december->diciembre` |
| `source_zipf=zipf_5_plus_very_common::polysemy=low_1_to_3::pos_shape=same_pos_polysemy` | 6 | 2 | 3.0 | `except->excepto`, `health->salud` |
| `source_zipf=zipf_5_plus_very_common::polysemy=low_1_to_3::pos_shape=cross_pos_polysemy` | 4 | 2 | 2.0 | `russian->ruso`, `tomorrow->mañana` |
| `source_zipf=zipf_5_plus_very_common::polysemy=medium_4_to_9::pos_shape=same_pos_polysemy` | 13 | 2 | 6.5 | `region->comarca`, `brother->hermano` |
| `source_zipf=zipf_5_plus_very_common::polysemy=medium_4_to_9::pos_shape=cross_pos_polysemy` | 24 | 2 | 12.0 | `american->americano`, `current->contemporáneo` |
| `source_zipf=zipf_5_plus_very_common::polysemy=high_10_plus::pos_shape=same_pos_polysemy` | 2 | 2 | 1.0 | `heart->corazón`, `continue->durar` |
| `source_zipf=zipf_5_plus_very_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy` | 50 | 2 | 25.0 | `control->gobernar`, `break->quebrar` |
| `source_zipf=zipf_5_plus_very_common::polysemy=missing::pos_shape=missing` | 2 | 2 | 1.0 | `among->entre`, `upon->sobre` |
| `source_zipf=zipf_4_to_5_common::polysemy=low_1_to_3::pos_shape=single_sense` | 12 | 2 | 6.0 | `pub->taberna`, `emotion->emoción` |
| `source_zipf=zipf_4_to_5_common::polysemy=low_1_to_3::pos_shape=same_pos_polysemy` | 37 | 2 | 18.5 | `entirely->enteramente`, `owe->deber` |
| `source_zipf=zipf_4_to_5_common::polysemy=low_1_to_3::pos_shape=cross_pos_polysemy` | 19 | 2 | 9.5 | `german->alemán`, `smile->sonreír` |
| `source_zipf=zipf_4_to_5_common::polysemy=medium_4_to_9::pos_shape=same_pos_polysemy` | 37 | 2 | 18.5 | `sale->deducción`, `acceptable->razonable` |
| `source_zipf=zipf_4_to_5_common::polysemy=medium_4_to_9::pos_shape=cross_pos_polysemy` | 74 | 2 | 37.0 | `shed->puesto`, `pair->par` |
| `source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=same_pos_polysemy` | 3 | 2 | 1.5 | `begin->comenzar`, `grow->acontecer` |
| `source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy` | 51 | 2 | 25.5 | `bar->cercar`, `demand->deducción` |
| `source_zipf=zipf_4_to_5_common::polysemy=missing::pos_shape=missing` | 1 | 1 | 1.0 | `recover->sanar` |
| `source_zipf=zipf_3_to_4_mid::polysemy=low_1_to_3::pos_shape=single_sense` | 30 | 2 | 15.0 | `dentist->dentista`, `salesman->vendedor` |
| `source_zipf=zipf_3_to_4_mid::polysemy=low_1_to_3::pos_shape=same_pos_polysemy` | 46 | 2 | 23.0 | `altitude->elevación`, `shortage->falta` |
| `source_zipf=zipf_3_to_4_mid::polysemy=low_1_to_3::pos_shape=cross_pos_polysemy` | 14 | 2 | 7.0 | `chic->elegante`, `parrot->loro` |
| `source_zipf=zipf_3_to_4_mid::polysemy=medium_4_to_9::pos_shape=same_pos_polysemy` | 26 | 2 | 13.0 | `govern->gobernar`, `endure->durar` |
| `source_zipf=zipf_3_to_4_mid::polysemy=medium_4_to_9::pos_shape=cross_pos_polysemy` | 31 | 2 | 15.5 | `cite->mencionar`, `rebate->descuento` |
| `source_zipf=zipf_3_to_4_mid::polysemy=high_10_plus::pos_shape=cross_pos_polysemy` | 2 | 2 | 1.0 | `stall->cuadra`, `offset->distancia` |
| `source_zipf=zipf_3_to_4_mid::polysemy=missing::pos_shape=missing` | 3 | 2 | 1.5 | `adjoining->vecino`, `adjoining->contiguo` |
| `source_zipf=zipf_below_3_rare::polysemy=low_1_to_3::pos_shape=single_sense` | 18 | 2 | 9.0 | `handiwork->artesanía`, `bouillon->caldo` |
| `source_zipf=zipf_below_3_rare::polysemy=low_1_to_3::pos_shape=same_pos_polysemy` | 20 | 2 | 10.0 | `aberration->equivocación`, `adder->víbora` |
| `source_zipf=zipf_below_3_rare::polysemy=low_1_to_3::pos_shape=cross_pos_polysemy` | 5 | 2 | 2.5 | `snore->roncar`, `rumanian->rumano` |
| `source_zipf=zipf_below_3_rare::polysemy=medium_4_to_9::pos_shape=cross_pos_polysemy` | 5 | 2 | 2.5 | `bridle->reprimir`, `billow->oleaje` |
| `source_zipf=zipf_below_3_rare::polysemy=missing::pos_shape=missing` | 4 | 2 | 2.0 | `turnon->poner`, `argentinean->argentino` |
| `source_zipf=missing::polysemy=low_1_to_3::pos_shape=single_sense` | 1 | 1 | 1.0 | `conversance->notoriedad` |
| `source_zipf=missing::polysemy=missing::pos_shape=missing` | 21 | 2 | 10.5 | `femalejournalist->periodista`, `mosaicwork->mosaico` |

## Manual Authoring Queue

| Family | Source Band | Target Band | Senses | POS Shape | Manual Rows | Weight |
| --- | --- | --- | ---: | --- | ---: | ---: |
| `june` -> `junio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1 | `single_sense` | 3 | 2.5 |
| `december` -> `diciembre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1 | `single_sense` | 3 | 2.5 |
| `except` -> `excepto` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 2 | `same_pos_polysemy` | 5 | 3.0 |
| `health` -> `salud` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 2 | `same_pos_polysemy` | 5 | 3.0 |
| `russian` -> `ruso` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 3 | `cross_pos_polysemy` | 5 | 2.0 |
| `tomorrow` -> `mañana` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 3 | `cross_pos_polysemy` | 5 | 2.0 |
| `region` -> `comarca` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 5 | `same_pos_polysemy` | 5 | 6.5 |
| `brother` -> `hermano` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 4 | `same_pos_polysemy` | 5 | 6.5 |
| `american` -> `americano` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 5 | `cross_pos_polysemy` | 5 | 12.0 |
| `current` -> `contemporáneo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 4 | `cross_pos_polysemy` | 5 | 12.0 |
| `heart` -> `corazón` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 10 | `same_pos_polysemy` | 5 | 1.0 |
| `continue` -> `durar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 10 | `same_pos_polysemy` | 5 | 1.0 |
| `control` -> `gobernar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 20 | `cross_pos_polysemy` | 5 | 25.0 |
| `break` -> `quebrar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 75 | `cross_pos_polysemy` | 5 | 25.0 |
| `among` -> `entre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 0 | `missing` | 3 | 1.0 |
| `upon` -> `sobre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 0 | `missing` | 3 | 1.0 |
| `pub` -> `taberna` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 1 | `single_sense` | 3 | 6.0 |
| `emotion` -> `emoción` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 1 | `single_sense` | 3 | 6.0 |
| `entirely` -> `enteramente` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 2 | `same_pos_polysemy` | 5 | 18.5 |
| `owe` -> `deber` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 3 | `same_pos_polysemy` | 5 | 18.5 |
| `german` -> `alemán` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 3 | `cross_pos_polysemy` | 5 | 9.5 |
| `smile` -> `sonreír` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 3 | `cross_pos_polysemy` | 5 | 9.5 |
| `sale` -> `deducción` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 5 | `same_pos_polysemy` | 5 | 18.5 |
| `acceptable` -> `razonable` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 4 | `same_pos_polysemy` | 5 | 18.5 |
| `shed` -> `puesto` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 6 | `cross_pos_polysemy` | 5 | 37.0 |
| `pair` -> `par` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 9 | `cross_pos_polysemy` | 5 | 37.0 |
| `begin` -> `comenzar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 10 | `same_pos_polysemy` | 5 | 1.5 |
| `grow` -> `acontecer` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 10 | `same_pos_polysemy` | 5 | 1.5 |
| `bar` -> `cercar` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 18 | `cross_pos_polysemy` | 5 | 25.5 |
| `demand` -> `deducción` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 11 | `cross_pos_polysemy` | 5 | 25.5 |
| `recover` -> `sanar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0 | `missing` | 3 | 1.0 |
| `dentist` -> `dentista` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 1 | `single_sense` | 3 | 15.0 |
| `salesman` -> `vendedor` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 1 | `single_sense` | 3 | 15.0 |
| `altitude` -> `elevación` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 3 | `same_pos_polysemy` | 5 | 23.0 |
| `shortage` -> `falta` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 2 | `same_pos_polysemy` | 5 | 23.0 |
| `chic` -> `elegante` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 2 | `cross_pos_polysemy` | 5 | 7.0 |
| `parrot` -> `loro` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 3 | `cross_pos_polysemy` | 5 | 7.0 |
| `govern` -> `gobernar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 4 | `same_pos_polysemy` | 5 | 13.0 |
| `endure` -> `durar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 7 | `same_pos_polysemy` | 5 | 13.0 |
| `cite` -> `mencionar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 8 | `cross_pos_polysemy` | 5 | 15.5 |
| `rebate` -> `descuento` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 5 | `cross_pos_polysemy` | 5 | 15.5 |
| `stall` -> `cuadra` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 14 | `cross_pos_polysemy` | 5 | 1.0 |
| `offset` -> `distancia` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 11 | `cross_pos_polysemy` | 5 | 1.0 |
| `adjoining` -> `vecino` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0 | `missing` | 3 | 1.5 |
| `adjoining` -> `contiguo` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0 | `missing` | 3 | 1.5 |
| `handiwork` -> `artesanía` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 1 | `single_sense` | 3 | 9.0 |
| `bouillon` -> `caldo` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 1 | `single_sense` | 3 | 9.0 |
| `aberration` -> `equivocación` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 3 | `same_pos_polysemy` | 5 | 10.0 |
| `adder` -> `víbora` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 3 | `same_pos_polysemy` | 5 | 10.0 |
| `snore` -> `roncar` | `zipf_below_3_rare` | `zipf_below_3_rare` | 3 | `cross_pos_polysemy` | 5 | 2.5 |
| `rumanian` -> `rumano` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 3 | `cross_pos_polysemy` | 5 | 2.5 |
| `bridle` -> `reprimir` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 5 | `cross_pos_polysemy` | 5 | 2.5 |
| `billow` -> `oleaje` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 5 | `cross_pos_polysemy` | 5 | 2.5 |
| `turnon` -> `poner` | `zipf_below_3_rare` | `zipf_5_plus_very_common` | 0 | `missing` | 3 | 2.0 |
| `argentinean` -> `argentino` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0 | `missing` | 3 | 2.0 |
| `conversance` -> `notoriedad` | `missing` | `zipf_3_to_4_mid` | 1 | `single_sense` | 3 | 1.0 |
| `femalejournalist` -> `periodista` | `missing` | `zipf_4_to_5_common` | 0 | `missing` | 3 | 10.5 |
| `mosaicwork` -> `mosaico` | `missing` | `zipf_3_to_4_mid` | 0 | `missing` | 3 | 10.5 |

## Guardrails

| Check | Value |
| --- | --- |
| `full_source_target_pairs_available` | `True` |
| `outcome_fields_absent_from_sample_rows` | `True` |
| `all_sampled_rows_have_cell_ids` | `True` |
| `all_nonempty_cells_have_samples` | `True` |
| `sample_counts_do_not_exceed_eligible_counts` | `True` |
| `mid_source_band_represented` | `True` |
| `rare_source_band_represented` | `True` |
| `measured_triggers_excluded_when_requested` | `True` |
| `all_authoring_rows_have_manual_packet` | `True` |

## Limitations

- `manual_sentences_are_not_authored_by_this_report`
- `wordnet_polysemy_is_a_proxy_for_shadow_availability`
- `source_zipf_bands_are_reporting_cells_not_proven_difficulty_boundaries`
- `sample_is_representative_within_declared_cells_not_a_browser_token_distribution`
- `missing_wordnet_profiles_are_preserved_as_missing_cells`

## Next Steps

- Author fixed manual sentence packets for the frozen queue without reselecting families.
- Keep rows that lack honest shadow negatives as not_applicable rather than inventing fake shadows.
- Score the authored packet with the current veto algorithm.
- Estimate positive allow and negative abstain by source Zipf, polysemy, and POS-shape cell.
- Rerun formula-shape and formula-weight sweeps only after this representative packet is scored.
