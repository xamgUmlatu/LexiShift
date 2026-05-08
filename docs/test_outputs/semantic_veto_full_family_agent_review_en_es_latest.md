# en-es Semantic Veto Full-Family Agent Review

- Status: `ok`
- Decision: `full_family_agent_review_complete_user_approval_required`
- Review authority: `codex_agent_review_user_approval_required`
- Families reviewed: `58`
- Repair-pool families: `49`
- Excluded families: `9`

This is a full agent semantic review, not user-approved gold data. It tells us which of the 58 sampled source-target families are worth repairing before the next scorer or band-formula sweep.

## Summary

| Key | Value |
| --- | --- |
| `issues` | `[]` |
| `family_count` | `58` |
| `repair_pool_family_count` | `49` |
| `excluded_family_count` | `9` |
| `draft_case_count` | `206` |
| `draft_shadow_count` | `75` |
| `scoring_action_counts` | `{"exclude_from_trusted_eval": 9, "repair_pool": 49}` |
| `family_disposition_counts` | `{"aligned_mapping_rewrite_contexts": 18, "aligned_mapping_shadow_rows_not_competitors": 16, "questionable_mapping_rejected": 1, "salvage_with_corrected_active_sense": 15, "source_form_artifact_rejected": 3, "source_target_mapping_rejected": 5}` |
| `active_sense_status_counts` | `{"aligned": 34, "corrected_active_sense_required": 15, "questionable_mapping_rejected": 1, "source_form_artifact_rejected": 3, "source_target_mapping_rejected": 5}` |
| `source_band_counts` | `{"missing": 3, "zipf_3_to_4_mid": 14, "zipf_4_to_5_common": 15, "zipf_5_plus_very_common": 16, "zipf_below_3_rare": 10}` |
| `repair_pool_source_band_counts` | `{"zipf_3_to_4_mid": 14, "zipf_4_to_5_common": 11, "zipf_5_plus_very_common": 16, "zipf_below_3_rare": 8}` |

## Dispositions

| # | Family | Source Band | Disposition | Action | Corrected Active | Notes |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `break -> quebrar` | `zipf_5_plus_very_common` | `salvage_with_corrected_active_sense` | `repair_pool` | become separated into pieces or crack under force | Draft active sense is interruption; target requires fracture/breaking. |
| 2 | `bar -> cercar` | `zipf_4_to_5_common` | `salvage_with_corrected_active_sense` | `repair_pool` | block, bar, fence in, or prevent passage with a barrier | Alcohol-bar row is wrong; only a barrier/enclosure verb sense is salvageable. |
| 3 | `offset -> distancia` | `zipf_3_to_4_mid` | `salvage_with_corrected_active_sense` | `repair_pool` | a measured displacement or distance from a reference point | Draft onset/outset sense is wrong; spatial or technical offset is the usable lane. |
| 4 | `bridle -> reprimir` | `zipf_below_3_rare` | `salvage_with_corrected_active_sense` | `repair_pool` | restrain, repress, or hold back an action or reaction | Horse-headgear active evidence is wrong; restrain/repress sense is salvageable. |
| 5 | `december -> diciembre` | `zipf_5_plus_very_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | the twelfth month of the year | Mapping is straightforward; draft positive row is definition-circular. |
| 6 | `emotion -> emoción` | `zipf_4_to_5_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a strong feeling or affective state | Mapping is aligned; draft positive row needs independent context. |
| 7 | `dentist -> dentista` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a person qualified to practice dentistry | Mapping is aligned; draft positive row needs independent context. |
| 8 | `bouillon -> caldo` | `zipf_below_3_rare` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a clear seasoned broth | Mapping is aligned; draft positive row needs independent context. |
| 9 | `control -> gobernar` | `zipf_5_plus_very_common` | `salvage_with_corrected_active_sense` | `repair_pool` | exercise authority over a place, organization, or group | Noun control/power row is not enough; governing-authority verb sense is salvageable. |
| 10 | `demand -> deducción` | `zipf_4_to_5_common` | `source_target_mapping_rejected` | `exclude_from_trusted_eval` |  | Demand/request/economic demand does not match deducción. |
| 11 | `stall -> cuadra` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a compartment in a stable where an animal is kept | Stable-stall sense is usable; draft rows still need independent contexts and real shadows. |
| 12 | `rumanian -> rumano` | `zipf_below_3_rare` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | Romanian as a nationality, language, or country adjective | Target can cover adjective, person, and language; draft POS shadows are not true competitors. |
| 13 | `june -> junio` | `zipf_5_plus_very_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | the month following May and preceding July | Mapping is straightforward; filename no-winner should be rewritten or trigger-checked. |
| 14 | `pub -> taberna` | `zipf_4_to_5_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a tavern or public house serving drinks and often light meals | Mapping is aligned; draft positive row needs independent context. |
| 15 | `salesman -> vendedor` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a person whose job is selling goods or services | Mapping is aligned despite gender/generalization looseness. |
| 16 | `handiwork -> artesanía` | `zipf_below_3_rare` | `aligned_mapping_rewrite_contexts` | `repair_pool` | work or craft produced by hand | Mapping is aligned; draft positive row needs independent context. |
| 17 | `continue -> durar` | `zipf_5_plus_very_common` | `salvage_with_corrected_active_sense` | `repair_pool` | last or continue for a period of time | Draft continue-working sense is too close to seguir; durar needs duration/lasting contexts. |
| 18 | `begin -> comenzar` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | start or come into being | Mapping is aligned, but several draft shadows also allow comenzar and are not true negatives. |
| 19 | `chic -> elegante` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | elegant and stylish | Adjective target is aligned; noun chic/elegance can be a real contrast. |
| 20 | `billow -> oleaje` | `zipf_below_3_rare` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a large sea wave or swell | Noun wave sense is aligned; verb billow rows need real Spanish competitor targets. |
| 21 | `among -> entre` | `zipf_5_plus_very_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | in the midst of or included within a group | Mapping is aligned but lacks WordNet-backed sense evidence in the draft packet. |
| 22 | `recover -> sanar` | `zipf_4_to_5_common` | `salvage_with_corrected_active_sense` | `repair_pool` | recover from illness, injury, or shock; heal | Draft regain/find-back sense is wrong for sanar. |
| 23 | `adjoining -> contiguo` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | next to or sharing a boundary with something | Mapping is aligned; draft evidence is placeholder-only. |
| 24 | `argentinean -> argentino` | `zipf_below_3_rare` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | Argentine as a nationality or country adjective | Mapping is aligned; noun/adjective contrasts usually share the same Spanish target. |
| 25 | `heart -> corazón` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | heart as emotional center or physical organ | Most major senses still allow corazón, so draft shadows are weak competitors. |
| 26 | `grow -> acontecer` | `zipf_4_to_5_common` | `source_target_mapping_rejected` | `exclude_from_trusted_eval` |  | Grow does not naturally map to acontecer, which means happen/occur. |
| 27 | `cite -> mencionar` | `zipf_3_to_4_mid` | `salvage_with_corrected_active_sense` | `repair_pool` | mention or refer to a source, person, or fact | Draft noun citation sense is wrong; verb mention/reference sense is salvageable. |
| 28 | `snore -> roncar` | `zipf_below_3_rare` | `salvage_with_corrected_active_sense` | `repair_pool` | breathe noisily while sleeping | Target is verb roncar; draft noun snore/ronquido sense must be corrected. |
| 29 | `upon -> sobre` | `zipf_5_plus_very_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | on, onto, or regarding, depending on context | Mapping is broad but usable; draft lacks real sense evidence. |
| 30 | `adjoining -> vecino` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | neighboring or adjacent | Mapping is usable for neighboring/adjoining; distinguish from contiguo duplicate lane later. |
| 31 | `turnon -> poner` | `zipf_below_3_rare` | `source_form_artifact_rejected` | `exclude_from_trusted_eval` |  | Unspaced trigger turnon is not a normal browser-facing source token for this target. |
| 32 | `current -> contemporáneo` | `zipf_5_plus_very_common` | `aligned_mapping_rewrite_contexts` | `repair_pool` | belonging to the present time; contemporary | Adjective current sense is aligned; electrical/water-current shadows are real competitors. |
| 33 | `shed -> puesto` | `zipf_4_to_5_common` | `source_target_mapping_rejected` | `exclude_from_trusted_eval` |  | Draft caducous, outbuilding, and remove senses do not justify puesto as a trusted target. |
| 34 | `parrot -> loro` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a parrot bird | Bird sense is aligned; repeat/copycat shadows are real competitors after target repair. |
| 35 | `aberration -> equivocación` | `zipf_below_3_rare` | `questionable_mapping_rejected` | `exclude_from_trusted_eval` |  | Aberration as deviation/disorder/optical flaw is not reliably equivocación. |
| 36 | `american -> americano` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | American as a nationality or regional adjective | The Spanish target covers several noun/adjective senses; draft shadows are not clean negatives. |
| 37 | `german -> alemán` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | German as nationality, language, or country adjective | Person/language/adjective distinctions usually share alemán, so draft shadows are weak. |
| 38 | `rebate -> descuento` | `zipf_3_to_4_mid` | `aligned_mapping_rewrite_contexts` | `repair_pool` | a refund, reduction, or discount on an amount paid | Price-reduction sense is aligned; woodworking-groove shadows are useful competitors. |
| 39 | `adder -> víbora` | `zipf_below_3_rare` | `salvage_with_corrected_active_sense` | `repair_pool` | a small viper snake | Draft arithmetic-person active sense is wrong; viper sense is salvageable. |
| 40 | `tomorrow -> mañana` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | the day after today, the next day, or the near future | Noun/adverb/future senses mostly map to mañana, so draft shadows are not true negatives. |
| 41 | `pair -> par` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | a pair or set of two things | Noun pair senses map to par; verb shadows need different competitors or should be dropped. |
| 42 | `endure -> durar` | `zipf_3_to_4_mid` | `salvage_with_corrected_active_sense` | `repair_pool` | continue to exist or last over time | Draft tolerate/suffer sense is not durar; lasting/perdure sense is salvageable. |
| 43 | `russian -> ruso` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | Russian as nationality, language, or country adjective | Person/language/adjective distinctions usually share ruso. |
| 44 | `smile -> sonreír` | `zipf_4_to_5_common` | `salvage_with_corrected_active_sense` | `repair_pool` | smile as a verb, changing one's facial expression | Draft noun smile is sonrisa; target sonreír requires verb contexts. |
| 45 | `govern -> gobernar` | `zipf_3_to_4_mid` | `salvage_with_corrected_active_sense` | `repair_pool` | exercise governing authority over a country, place, or organization | Regulate/conformity sense is too broad; authority sense should be active. |
| 46 | `brother -> hermano` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | a male sibling, fellow member, or fraternal address | Most draft alternate senses still allow hermano, so shadows are not clean competitors. |
| 47 | `acceptable -> razonable` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | acceptable or reasonable in degree or quality | Mapping is broad but usable; several draft shadows may still be reasonable/acceptable. |
| 48 | `altitude -> elevación` | `zipf_3_to_4_mid` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | height or elevation above a reference level | Mapping is aligned; geometric/angular altitude can also be elevation-like. |
| 49 | `health -> salud` | `zipf_5_plus_very_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | health as wellbeing or bodily/mental condition | Both WordNet senses map to salud, so draft shadow is not a competitor. |
| 50 | `sale -> deducción` | `zipf_4_to_5_common` | `source_target_mapping_rejected` | `exclude_from_trusted_eval` |  | Sale/selling/discount event does not reliably map to deducción. |
| 51 | `shortage -> falta` | `zipf_3_to_4_mid` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | a lack, deficit, or insufficient amount | Both draft senses map to falta, so shadow contrast is weak. |
| 52 | `except -> excepto` | `zipf_5_plus_very_common` | `salvage_with_corrected_active_sense` | `repair_pool` | except/excluding as a preposition or conjunction | WordNet verb object-to sense is wrong; common browser preposition sense is salvageable. |
| 53 | `entirely -> enteramente` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | completely, wholly, or entirely | Both draft adverb senses can map to enteramente; shadows are weak competitors. |
| 54 | `region -> comarca` | `zipf_5_plus_very_common` | `salvage_with_corrected_active_sense` | `repair_pool` | a local district, territory, or comarca-like region | Generic region is too broad; local/district region sense is the usable target lane. |
| 55 | `owe -> deber` | `zipf_4_to_5_common` | `aligned_mapping_shadow_rows_not_competitors` | `repair_pool` | owe, be obliged to pay, or be indebted | Monetary and abstract owe senses both map to deber, so shadows are not clean competitors. |
| 56 | `conversance -> notoriedad` | `missing` | `source_target_mapping_rejected` | `exclude_from_trusted_eval` |  | Conversance means familiarity/knowledge, not notoriety/fame. |
| 57 | `femalejournalist -> periodista` | `missing` | `source_form_artifact_rejected` | `exclude_from_trusted_eval` |  | Unspaced source form is an artifact; use journalist/female journalist only in a separate source-form lane. |
| 58 | `mosaicwork -> mosaico` | `missing` | `source_form_artifact_rejected` | `exclude_from_trusted_eval` |  | Unspaced source form is an artifact, even though mosaic work can map to mosaico. |

## Issues

- `none`

## Next Steps

- Build a repaired full-family candidate only from repair_pool families.
- Drop rejected source-target mappings from trusted evaluation denominators.
- For shadow-weak families, keep positives but avoid counting same-target POS shadows as true competitors.
- Rerun scoring and band-formula sweeps only after repaired rows are materialized.
