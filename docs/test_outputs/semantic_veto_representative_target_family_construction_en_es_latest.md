# en-es Semantic Veto Representative Target-Family Construction

- Status: `ok`
- Decision: `representative_target_family_construction_queue_established`
- Generated: `2026-05-05T20:48:34+00:00`
- Attempted sampled triggers: `255`
- Source-ready family drafts: `7`
- Weak diagnostic family drafts: `87`
- Blocked rows: `161`

## Goal

Advance the frozen representative heuristic-band source-trigger sample toward en-es evaluation by constructing draft Spanish target/shadow families without changing the sampled trigger set.

This report does not generate LLM rows and does not change runtime policy. Blocked rows remain part of the representative result instead of being replaced.

## Stage Counts

| Stage | Count |
| --- | ---: |
| `construction_blocked` | 161 |
| `source_supported_family_draft_needs_review` | 7 |
| `weak_family_draft_needs_source_support` | 87 |

## Strategy Counts

| Strategy | Count |
| --- | ---: |
| `any_cross_pos_supported_source_linked` | 1 |
| `any_cross_pos_translation_only_diagnostic` | 53 |
| `any_cross_pos_wordnet_forward_only` | 34 |
| `noun_verb_supported_source_linked` | 6 |

## Reason Counts

| Reason | Count |
| --- | ---: |
| `constructed_family` | 94 |
| `missing_noun_or_verb_translation` | 161 |

## Cell Coverage

| Cell | Source-ready | Weak | Blocked |
| --- | ---: | ---: | ---: |
| `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 1 | 6 | 1 |
| `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 0 | 0 | 1 |
| `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 0 | 3 |
| `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 1 | 1 |
| `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 0 | 2 | 3 |
| `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 1 | 7 |
| `source_rank_band=1001-2000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 1 | 6 | 1 |
| `source_rank_band=1001-2000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 0 | 1 | 1 |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 1 | 6 | 1 |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |
| `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 0 | 5 |
| `source_rank_band=1001-2000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 1 | 5 | 2 |
| `source_rank_band=1001-2000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 1 | 7 |
| `source_rank_band=2001-5000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 0 | 7 | 1 |
| `source_rank_band=2001-5000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 0 | 0 | 3 |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 0 | 3 | 5 |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |
| `source_rank_band=2001-5000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 0 | 8 |
| `source_rank_band=2001-5000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 0 | 5 | 3 |
| `source_rank_band=2001-5000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 2 | 6 |
| `source_rank_band=5001-10000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 0 | 6 | 2 |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 0 | 2 | 6 |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 1 | 7 |
| `source_rank_band=5001-10000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 0 | 8 |
| `source_rank_band=5001-10000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 0 | 7 | 1 |
| `source_rank_band=5001-10000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |
| `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 2 | 5 | 1 |
| `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | 0 | 0 | 1 |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 0 | 0 | 2 |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 0 | 5 |
| `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 0 | 2 |
| `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 1 | 6 | 1 |
| `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |
| `source_rank_band=>10000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | 0 | 6 | 2 |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | 0 | 5 | 3 |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |
| `source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=single_sense` | 0 | 0 | 8 |
| `source_rank_band=>10000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | 0 | 3 | 5 |
| `source_rank_band=>10000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | 0 | 0 | 8 |

## Construction Attempts

| Rank | Trigger | Cell | Stage | Strategy | Active | Shadows | Reason |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `percent` | `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 2 | `yes` | `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=single_sense` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `sí (noun)` | `a favor (noun), aceptar (verb)` | `constructed_family` |
| 3 | `college` | `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 4 | `often` | `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 5 | `money` | `source_rank_band=1-500::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 6 | `consider` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 7 | `security` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 8 | `door` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 9 | `however` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 10 | `process` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `proceso (noun)` | `apéndice (noun), procesar (verb)` | `constructed_family` |
| 11 | `news` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 12 | `able` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 13 | `event` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 14 | `off` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 15 | `five` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 16 | `buy` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 17 | `kid` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `chino (noun)` | `chico (noun), tomar el pelo (verb)` | `constructed_family` |
| 18 | `today` | `source_rank_band=1-500::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `hodierno (adjective)` | `hoy (noun)` | `constructed_family` |
| 19 | `heart` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 20 | `home` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `hogar (noun)` | `patria (noun), en casa (adverb)` | `constructed_family` |
| 21 | `service` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `servicio (noun)` | `saque (noun), servir (verb)` | `constructed_family` |
| 22 | `long` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `lejos (adverb)` | `luengo (adjective)` | `constructed_family` |
| 23 | `work` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `source_supported_family_draft_needs_review` | `noun_verb_supported_source_linked` | `trabajo (noun)` | `trabajar (verb)` | `constructed_family` |
| 24 | `kill` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `matanza (noun)` | `matar (verb)` | `constructed_family` |
| 25 | `help` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `ayuda (noun)` | `mucamo (noun), ayudar (verb)` | `constructed_family` |
| 26 | `case` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `caso (noun)` | `caja (noun), empaquetar (verb)` | `constructed_family` |
| 27 | `action` | `source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 28 | `employee` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 29 | `nobody` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 30 | `camera` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 31 | `road` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 32 | `finally` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 33 | `particularly` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 34 | `science` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 35 | `district` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 36 | `hate` | `source_rank_band=501-1000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 37 | `serious` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 38 | `agency` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 39 | `example` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 40 | `role` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 41 | `performance` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 42 | `clearly` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 43 | `degree` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 44 | `response` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 45 | `simple` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `source_supported_family_draft_needs_review` | `any_cross_pos_supported_source_linked` | `sencillo (adjective)` | `simple (noun)` | `constructed_family` |
| 46 | `paper` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `papelero (adjective)` | `papel (noun)` | `constructed_family` |
| 47 | `couple` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `pareja (noun)` | `par (noun), acoplar (verb)` | `constructed_family` |
| 48 | `public` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 49 | `oil` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `aceite (noun)` | `aceite vegetal (noun), aceitar (verb)` | `constructed_family` |
| 50 | `earth` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `terreno (noun)` | `aterrar (verb)` | `constructed_family` |
| 51 | `blood` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `sangre (noun)` | `lazo de sangre (noun), ensangrentar (verb)` | `constructed_family` |
| 52 | `matter` | `source_rank_band=501-1000::polysemy_band=medium_4_to_9::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `materia (noun)` | `asunto (noun), importar (verb)` | `constructed_family` |
| 53 | `hot` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 54 | `look` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `source_supported_family_draft_needs_review` | `noun_verb_supported_source_linked` | `aspecto (noun)` | `parecer (verb)` | `constructed_family` |
| 55 | `common` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `común (adjective)` | `ejido (noun)` | `constructed_family` |
| 56 | `design` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `diseño (noun)` | `intención (noun), diseñar (verb)` | `constructed_family` |
| 57 | `return` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `source_supported_family_draft_needs_review` | `noun_verb_supported_source_linked` | `regreso (noun)` | `devolución (noun), devolver (verb)` | `constructed_family` |
| 58 | `answer` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `respuesta (noun)` | `contestación (noun), servir (verb)` | `constructed_family` |
| 59 | `union` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 60 | `present` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `presente (noun)` | `exponer (verb)` | `constructed_family` |
| 61 | `throw` | `source_rank_band=501-1000::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `lanzamiento (noun)` | `lanzar (verb)` | `constructed_family` |
| 62 | `definitely` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 63 | `senate` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 64 | `currently` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 65 | `mayor` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 66 | `beer` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 67 | `ocean` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 68 | `basis` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 69 | `consequence` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 70 | `participant` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 71 | `encourage` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 72 | `therefore` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 73 | `temperature` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 74 | `crisis` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=same_pos_polysemy` | `construction_blocked` | `-` | `-` | `-` | `missing_noun_or_verb_translation` |
| 75 | `institute` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `instituto (noun)` | `instituir (verb)` | `constructed_family` |
| 76 | `cash` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `cash (noun)` | `cobrar (verb)` | `constructed_family` |
| 77 | `soldier` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `source_supported_family_draft_needs_review` | `noun_verb_supported_source_linked` | `soldado (noun)` | `militar (verb)` | `constructed_family` |
| 78 | `expert` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `experto (adjective)` | `perito (noun)` | `constructed_family` |
| 79 | `content` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_translation_only_diagnostic` | `contenido (noun)` | `materia (noun), contentar (verb)` | `constructed_family` |
| 80 | `african` | `source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=cross_pos_polysemy` | `weak_family_draft_needs_source_support` | `any_cross_pos_wordnet_forward_only` | `africano (adjective)` | `africana (noun)` | `constructed_family` |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Guardrails

| Check | Value |
| --- | --- |
| `attempts_match_loaded_sample_rows` | `True` |
| `all_attempts_have_cell_ids` | `True` |
| `sample_rows_have_no_outcome_fields` | `True` |
| `no_llm_packets_emitted` | `True` |
| `source_ready_rows_have_source_supported_strategy` | `True` |
| `weak_rows_not_marked_source_ready` | `True` |
| `source_ready_families_have_distinct_visible_targets` | `True` |

## Limitations

- `target_families_are_drafts_and_need_review_before_scored_probe_claims`
- `source_ready_here_means_ready_for_probe_not_runtime_promotion`
- `english_trigger_sampling_is_representative_within_cells_not_browser_token_weighted`
- `blocked_rows_remain_part_of_the_representative_result_and_must_not_be_replaced`
- `no_active_shadow_phrase_llm_rows_are_generated_by_this_harness`

## Next Steps

- Review source-ready family drafts for visible-target and sense quality.
- Score fixed probe contexts for reviewed source-ready families.
- Keep blocked and weak rows in denominator when estimating source-coverage difficulty by cell.
- Use the blocked-cell map to decide whether to improve source packs or spend LLM budget.
